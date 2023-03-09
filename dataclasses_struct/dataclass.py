from collections.abc import Callable
# import dataclasses  # TODO
import inspect
from typing import Annotated, Any, get_args, get_origin

from .field import primitive_fields, Field

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
            raise TypeError('type not supported: {f}')
        type_ = f

    if not isinstance(field, Field):
        raise TypeError(f'invalid field annotation: {field}')

    if not issubclass(type_, field.type_):
        raise TypeError(f'type {type_} not supported for field: {field}')

    if field.native_only and not allow_native:
        raise TypeError(f'field {field} only supported for native alignment')

    if hasattr(cls, name):
        field.validate(getattr(cls, name))

    return field.format()


def _make_class(cls, allow_native: bool) -> type:
    cls_annotations = inspect.get_annotations(cls)
    struct_format = ''.join(
        _validate_and_parse_field(cls, name, field, allow_native)
        for name, field in cls_annotations.items()
    )
    names = list(cls_annotations.keys())

    # TODO: configure dataclass
    setattr(cls, "__dataclass_struct_format__", struct_format)
    setattr(cls, "__dataclass_struct_fieldnames__", names)

    # return dataclasses.dataclass(cls)
    return cls


def dataclass(endian: str = NATIVE_ENDIAN_ALIGNED) -> Callable[[type], type]:
    if endian not in _allowed_endians:
        raise ValueError(
            'invalid endianness: {endian}. '
            '(Did you forget to add parentheses: @dataclass()?)'
        )

    allow_native = endian in (NATIVE_ENDIAN, NATIVE_ENDIAN_ALIGNED)

    def decorator(cls) -> type:
        return _make_class(cls, allow_native)

    return decorator
