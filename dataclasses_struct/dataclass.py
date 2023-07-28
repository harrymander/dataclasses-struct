import dataclasses
import struct
from typing import Any, Callable, Dict, List, Protocol, Type, Union, overload
from typing_extensions import (
    Annotated,
    TypeGuard,
    dataclass_transform,
    get_args,
    get_origin,
    get_type_hints,
)

from .field import primitive_fields, Field, BytesField
from .types import PadBefore, PadAfter


NATIVE_ENDIAN_ALIGNED = '@'
NATIVE_ENDIAN = '='
LITTLE_ENDIAN = '<'
BIG_ENDIAN = '>'
NETWORK_ENDIAN = '!'


ENDIANS = frozenset((
    NATIVE_ENDIAN_ALIGNED,
    NATIVE_ENDIAN,
    LITTLE_ENDIAN,
    BIG_ENDIAN,
    NETWORK_ENDIAN,
))


def _get_padding_and_field(fields):
    pad_before = pad_after = 0
    field = None
    for f in fields:
        if isinstance(f, PadBefore):
            pad_before += f.size
        elif isinstance(f, PadAfter):
            pad_after += f.size
        elif field is not None:
            raise TypeError(f'too many annotations: {f}')
        else:
            field = f

    return pad_before, pad_after, field


class _DataclassStructInternal:
    struct: struct.Struct
    cls: type

    @property
    def format(self) -> str:
        return self.struct.format

    @property
    def size(self) -> int:
        return self.struct.size

    @property
    def endianness(self) -> str:
        return self.format[0]

    def __init__(self, fmt: str, cls: type):
        self.struct = struct.Struct(fmt)
        self.cls = cls

    def pack(self, *args) -> bytes:
        return self.struct.pack(*args)

    def unpack(self, data: bytes) -> Any:
        return self.struct.unpack(data)


class DataclassStructProtocol(Protocol):
    __dataclass_struct__: _DataclassStructInternal


@overload
def is_dataclass_struct(obj: type) -> TypeGuard[type[DataclassStructProtocol]]:
    ...


@overload
def is_dataclass_struct(obj: Any) -> TypeGuard[DataclassStructProtocol]:
    ...


def is_dataclass_struct(obj: Union[type, Any]) -> Union[
    TypeGuard[DataclassStructProtocol],
    TypeGuard[type[DataclassStructProtocol]]
]:
    """
    Returns True if obj is a class that has been decorated with
    dataclasses_struct.dataclass or an instance of one.
    """
    return (
        dataclasses.is_dataclass(obj)
        and hasattr(obj, '__dataclass_struct__')
        and isinstance(obj.__dataclass_struct__, _DataclassStructInternal)
    )


def _validate_and_parse_field(
    cls: type,
    name: str,
    f: Type[Any],
    allow_native: bool,
    validate: bool,
) -> str:
    if get_origin(f) == Annotated:
        type_, *fields = get_args(f)
        pad_before, pad_after, field = _get_padding_and_field(fields)
    else:
        pad_before = pad_after = 0
        type_ = f
        field = None

    if field is None:
        field = primitive_fields.get(type_)
        if field is None:
            raise TypeError(f'type not supported: {f}')

    if issubclass(type_, bytes) and isinstance(field, int):
        field = BytesField(field)
    elif not isinstance(field, Field):
        raise TypeError(f'invalid field annotation: {field}')

    if not issubclass(type_, field.type_):
        raise TypeError(f'type {type_} not supported for field: {field}')

    if field.native_only and not allow_native:
        raise TypeError(f'field {field} only supported for native alignment')

    if validate and hasattr(cls, name):
        val = getattr(cls, name)
        if not isinstance(val, field.type_):
            raise TypeError(
                'invalid type for field: expected '
                f'{field.type_} got {type(val)}'
            )
        field.validate(val)

    return ''.join((
        (f'{pad_before}x' if pad_before else ''),
        field.format(),
        (f'{pad_after}x' if pad_after else ''),
    ))


def _make_pack_method(fieldnames: List[str]) -> Callable:
    func = f"""
def pack(self) -> bytes:
    '''Pack to bytes using struct.pack.'''
    return self.__dataclass_struct__.pack(
    {','.join(f'self.{name}' for name in fieldnames)}
    )
"""

    scope: Dict[str, Any] = {}
    exec(func, {}, scope)
    return scope['pack']


def _make_unpack_method(cls: type) -> classmethod:
    func = """
def from_packed(cls, data: bytes) -> cls_type:
    '''Unpack from bytes.'''
    return cls(*cls.__dataclass_struct__.unpack(data))
"""

    scope: Dict[str, Any] = {'cls_type': cls}
    exec(func, {}, scope)
    return classmethod(scope['from_packed'])


def _make_class(
    cls: type, endian: str, allow_native: bool, validate: bool
) -> type:
    cls_annotations = get_type_hints(cls, include_extras=True)
    struct_format = [endian]
    struct_format.extend(
        _validate_and_parse_field(cls, name, field, allow_native, validate)
        for name, field in cls_annotations.items()
    )

    setattr(
        cls,
        '__dataclass_struct__',
        _DataclassStructInternal(''.join(struct_format), cls)
    )
    setattr(cls, 'pack', _make_pack_method(list(cls_annotations.keys())))
    setattr(cls, 'from_packed', _make_unpack_method(cls))

    return dataclasses.dataclass(cls)


@dataclass_transform()
def dataclass(
    endian: str = NATIVE_ENDIAN_ALIGNED,
    validate: bool = True,
) -> Callable[[type], type]:
    if endian not in ENDIANS:
        raise ValueError(
            f'invalid endianness: {endian}. '
            '(Did you forget to add parentheses: @dataclass()?)'
        )

    def decorator(cls: type) -> type:
        return _make_class(
            cls,
            endian,
            endian == NATIVE_ENDIAN_ALIGNED,
            validate
        )

    return decorator
