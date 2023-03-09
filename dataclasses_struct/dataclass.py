from collections.abc import Callable
import dataclasses
import inspect
from typing import Any, get_args, get_origin


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


def _parse_field(cls: type, name: str, f: type[Any]) -> tuple[type, str]:
    return int, ''


def _make_class(cls) -> type:
    cls_annotations = inspect.get_annotations(cls)
    fields = {
        name: _parse_field(cls, name, field)
        for name, field in cls_annotations.items()
    }

    return dataclasses.dataclass(cls)


def dataclass(endian: str = NATIVE_ENDIAN_ALIGNED) -> Callable[[type], type]:
    if endian not in _allowed_endians:
        raise ValueError(
            'invalid endianness: {endian}. '
            '(Did you forget to add parentheses: @dataclass()?)'
        )

    def decorator(cls) -> type:
        return _make_class(cls)

    return decorator
