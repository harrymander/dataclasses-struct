from collections.abc import Callable
from typing import TypeAlias

import pytest

STD_BYTEORDERS = ('native', 'big', 'little', 'network')
NATIVE_BYTEORDERS = ('native',)

ALL_VALID_SIZE_BYTEORDER_PAIRS = (
    *(('native', e) for e in NATIVE_BYTEORDERS),
    *(('std', e) for e in STD_BYTEORDERS)
)


ParametrizeDecorator: TypeAlias = Callable[[Callable], pytest.MarkDecorator]


def parametrize_std_byteorders(
    argname: str = 'byteorder'
) -> ParametrizeDecorator:
    def mark(f) -> pytest.MarkDecorator:
        return pytest.mark.parametrize(argname, STD_BYTEORDERS)(f)

    return mark


def parametrize_all_sizes_and_byteorders(
    size_argname: str = 'size', byteorder_argname: str = 'byteorder'
) -> ParametrizeDecorator:
    def mark(f) -> pytest.MarkDecorator:
        return pytest.mark.parametrize(
            ','.join((size_argname, byteorder_argname)),
            ALL_VALID_SIZE_BYTEORDER_PAIRS
        )(f)

    return mark
