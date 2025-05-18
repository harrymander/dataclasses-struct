import struct

import pytest
from conftest import parametrize_all_sizes_and_byteorders

import dataclasses_struct as dcs
from dataclasses_struct import Annotated


def test_pack_unpack_nested() -> None:
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


def test_pack_unpack_double_nested() -> None:
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


def assert_true_has_correct_padding(
    packed: bytes,
    expected_num_before: int,
    exected_num_after: int,
) -> None:
    __tracebackhide__ = True
    expected = (
        (expected_num_before * b"\x00")
        + b"\x01"
        + (exected_num_after * b"\x00")
    )
    assert packed == expected


@pytest.mark.parametrize("padding", (dcs.PadBefore, dcs.PadAfter))
@parametrize_all_sizes_and_byteorders()
def test_pack_padding_zero(size, byteorder, padding: type) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: Annotated[bool, padding(0)]

    assert T(True).pack() == b"\x01"


@parametrize_all_sizes_and_byteorders()
def test_pack_padding_before(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadBefore(5)]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 5, 0)


@parametrize_all_sizes_and_byteorders()
def test_pack_padding_after(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadAfter(5)]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 0, 5)


@parametrize_all_sizes_and_byteorders()
def test_pack_padding_before_and_after(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadBefore(10), dcs.PadAfter(5)]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 10, 5)


@parametrize_all_sizes_and_byteorders()
def test_pack_padding_before_and_after_with_after_before_before(
    size, byteorder
) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadAfter(5), dcs.PadBefore(10)]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 10, 5)


@parametrize_all_sizes_and_byteorders()
def test_pack_padding_multiple(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[
            bool,
            dcs.PadBefore(4),
            dcs.PadAfter(5),
            dcs.PadBefore(0),
            dcs.PadAfter(3),
            dcs.PadBefore(10),
        ]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 14, 8)


@parametrize_all_sizes_and_byteorders()
def test_pack_padding_with_bytes(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        a: Annotated[bytes, dcs.PadBefore(2), 4, dcs.PadAfter(3)]

    t = Test(b"1234")
    assert t.pack() == b"\x00\x001234\x00\x00\x00"


@parametrize_all_sizes_and_byteorders()
def test_unpack_padding(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadAfter(2)]
        y: Annotated[bool, dcs.PadBefore(2), dcs.PadAfter(7)]

    unpacked = Test.from_packed(
        b"\x00" + (b"\x00" * 4) + b"\x01" + (b"\x00" * 7)
    )
    assert unpacked == Test(False, True)
