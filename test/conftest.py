from collections.abc import Callable
from typing import TypeAlias

import pytest

STD_ENDIANS = ('native', 'big', 'little', 'network')
NATIVE_ENDIANS = ('native',)

ALL_VALID_SIZE_ENDIAN_PAIRS = (
    *(('native', e) for e in NATIVE_ENDIANS),
    *(('std', e) for e in STD_ENDIANS)
)


ParametrizeDecorator: TypeAlias = Callable[[Callable], pytest.MarkDecorator]


def parametrize_std_endians(argname: str = 'endian') -> ParametrizeDecorator:
    def mark(f) -> pytest.MarkDecorator:
        return pytest.mark.parametrize(argname, STD_ENDIANS)(f)

    return mark


def parametrize_all_sizes_and_endians(
    size_argname: str = 'size', endian_argname: str = 'endian'
) -> ParametrizeDecorator:
    def mark(f) -> pytest.MarkDecorator:
        return pytest.mark.parametrize(
            ','.join((size_argname, endian_argname)),
            ALL_VALID_SIZE_ENDIAN_PAIRS
        )(f)

    return mark
