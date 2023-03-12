from collections.abc import Callable
import dataclasses
import inspect
import struct
from typing import Annotated, Any, get_args, get_origin
from typing_extensions import dataclass_transform

from .field import primitive_fields, Field, BytesField

NATIVE_ENDIAN_ALIGNED = '@'
NATIVE_ENDIAN = '='
LITTLE_ENDIAN = '<'
BIG_ENDIAN = '>'
NETWORK_ENDIAN = '!'


_allowed_endians = frozenset((
    NATIVE_ENDIAN_ALIGNED,
    NATIVE_ENDIAN,
    LITTLE_ENDIAN,
    BIG_ENDIAN,
    NETWORK_ENDIAN,
))


def _validate_and_parse_field(
    cls: type,
    name: str,
    f: type[Any],
    allow_native: bool
) -> str:
    if get_origin(f) == Annotated:
        type_, field = get_args(f)
    else:
        field = primitive_fields.get(f)
        if field is None:
            raise TypeError(f'type not supported: {f}')
        type_ = f

    if issubclass(type_, bytes) and isinstance(field, int):
        field = BytesField(field)
    elif not isinstance(field, Field):
        raise TypeError(f'invalid field annotation: {field}')

    if not issubclass(type_, field.type_):
        raise TypeError(f'type {type_} not supported for field: {field}')

    if field.native_only and not allow_native:
        raise TypeError(f'field {field} only supported for native alignment')

    if hasattr(cls, name):
        val = getattr(cls, name)
        if not isinstance(val, field.type_):
            raise TypeError(
                'invalid type for field: expected '
                f'{field.type_} got {type(val)}'
            )
        field.validate(val)

    return field.format()


def _make_pack_method(fieldnames: list[str]) -> Callable:
    func = f"""
def pack(self) -> bytes:
    '''Pack to bytes using struct.pack.'''
    return self.__dataclass_struct__.pack(
    {','.join(f'self.{name}' for name in fieldnames)}
    )
"""

    scope: dict[str, Any] = {}
    exec(func, {}, scope)
    return scope['pack']


def _make_unpack_method(cls: type) -> classmethod:
    func = """
def from_packed(cls, data: bytes) -> cls_type:
    '''Unpack from bytes.'''
    return cls(*cls.__dataclass_struct__.unpack(data))
"""

    scope: dict[str, Any] = {'cls_type': cls}
    exec(func, {}, scope)
    return classmethod(scope['from_packed'])


def _make_class(
    cls: type, endian: str, allow_native: bool
) -> type:
    cls_annotations = inspect.get_annotations(cls)
    struct_format = ''.join(
        _validate_and_parse_field(cls, name, field, allow_native)
        for name, field in cls_annotations.items()
    )
    names = list(cls_annotations.keys())

    setattr(cls, '__dataclass_struct__', struct.Struct(endian + struct_format))
    setattr(cls, 'pack', _make_pack_method(names))
    setattr(cls, 'from_packed', _make_unpack_method(cls))

    return dataclasses.dataclass(cls)


@dataclass_transform()
def dataclass(endian: str = NATIVE_ENDIAN_ALIGNED) -> Callable[[type], type]:
    if endian not in _allowed_endians:
        raise ValueError(
            f'invalid endianness: {endian}. '
            '(Did you forget to add parentheses: @dataclass()?)'
        )

    def decorator(cls: type) -> type:
        return _make_class(cls, endian, endian == NATIVE_ENDIAN_ALIGNED)

    return decorator
