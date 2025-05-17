import itertools
import struct
from re import escape

import pytest
from conftest import ALL_VALID_SIZE_BYTEORDER_PAIRS

import dataclasses_struct as dcs
from dataclasses_struct import Annotated


def test_nested() -> None:
    @dcs.dataclass_struct()
    class Nested:
        x: float
        y: Annotated[bytes, 3]

    assert dcs.get_struct_size(Nested) == struct.calcsize("@ d3b")

    @dcs.dataclass_struct()
    class Container:
        x: dcs.F32
        item1: Annotated[Nested, dcs.PadBefore(10)]
        item2: Annotated[Nested, dcs.PadAfter(12)]
        y: bool

    fmt = "@ f 10xq3b q3b12x ?"
    assert dcs.get_struct_size(Container) == struct.calcsize(fmt)

    c = Container(1, Nested(2, b"123"), Nested(5, b"456"), False)
    unpacked = Container.from_packed(c.pack())
    assert c == unpacked


def test_double_nested() -> None:
    @dcs.dataclass_struct()
    class Nested1:
        x: float
        y: Annotated[bytes, 3]

    @dcs.dataclass_struct()
    class Nested2:
        nested1: Annotated[Nested1, dcs.PadBefore(12)]
        nested2: Annotated[Nested1, dcs.PadBefore(12)]

    @dcs.dataclass_struct()
    class Container:
        x: bool
        item1: Nested2
        item2: Nested2
        y: float

    c = Container(
        True,
        Nested2(Nested1(2, b"abc"), Nested1(7, b"123")),
        Nested2(Nested1(12, b"def"), Nested1(-1, b"456")),
        2,
    )
    unpacked = Container.from_packed(c.pack())
    assert c == unpacked


@pytest.mark.parametrize(
    "nested_size_byteorder,container_size_byteorder",
    itertools.combinations(ALL_VALID_SIZE_BYTEORDER_PAIRS, 2),
)
def test_mismatch_byteorder_fails(
    nested_size_byteorder, container_size_byteorder
) -> None:
    nested_size, nested_byteorder = nested_size_byteorder
    container_size, container_byteorder = container_size_byteorder
    exp_msg = f"byteorder and size of nested dataclass-struct does not \
match that of container (expected '{container_size}' size and \
'{container_byteorder}' byteorder, got '{nested_size}' size and \
'{nested_byteorder}' byteorder)"

    with pytest.raises(TypeError, match=f"^{escape(exp_msg)}$"):

        @dcs.dataclass_struct(size=nested_size, byteorder=nested_byteorder)
        class Nested:
            pass

        @dcs.dataclass_struct(
            size=container_size,
            byteorder=container_byteorder,
        )
        class _:
            y: Nested
