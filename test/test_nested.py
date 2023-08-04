import itertools
import struct
from re import escape

import pytest
from typing_extensions import Annotated

import dataclasses_struct as dcs


def test_nested() -> None:
    @dcs.dataclass()
    class Nested:
        x: dcs.I64
        y: Annotated[bytes, 3]

    assert dcs.get_struct_size(Nested) == struct.calcsize('@ q3b')

    @dcs.dataclass()
    class Container:
        x: dcs.I32
        item1: Annotated[Nested, dcs.PadBefore(10)]
        item2: Annotated[Nested, dcs.PadAfter(12)]
        y: dcs.I32

    fmt = '@ i 10xq3b q3b12x i'
    assert dcs.get_struct_size(Container) == struct.calcsize(fmt)

    c = Container(1, Nested(2, b'123'), Nested(5, b'456'), 12)
    unpacked = Container.from_packed(c.pack())
    assert c == unpacked


def test_double_nested() -> None:
    @dcs.dataclass()
    class Nested1:
        x: dcs.I64
        y: Annotated[bytes, 3]

    @dcs.dataclass()
    class Nested2:
        nested1: Annotated[Nested1, dcs.PadBefore(12)]
        nested2: Annotated[Nested1, dcs.PadBefore(12)]

    @dcs.dataclass()
    class Container:
        x: dcs.I32
        item1: Nested2
        item2: Nested2
        y: dcs.U32

    c = Container(
        1,
        Nested2(Nested1(2, b'abc'), Nested1(7, b'123')),
        Nested2(Nested1(12, b'def'), Nested1(-1, b'456')),
        2
    )
    unpacked = Container.from_packed(c.pack())
    assert c == unpacked


@pytest.mark.parametrize('e1,e2', itertools.combinations(dcs.ENDIANS, 2))
def test_mismatch_endian_fails(e1: str, e2: str) -> None:
    exp_msg = (
        'endianness of contained dataclass-struct does '
        'not match that of container '
        f'(expected {e2}, got {e1})'
    )
    with pytest.raises(TypeError, match=f'^{escape(exp_msg)}$'):
        @dcs.dataclass(e1)
        class Nested:
            x: dcs.I64

        @dcs.dataclass(e2)
        class Container:
            y: Nested
