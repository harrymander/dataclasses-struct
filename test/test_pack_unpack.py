import itertools
import struct
from typing import Annotated

import pytest
from conftest import (
    bool_fields,
    char_fields,
    float_fields,
    native_byteorders,
    native_only_int_fields,
    parametrize_all_sizes_and_byteorders,
    parametrize_fields,
    std_byteorders,
    std_only_int_fields,
)

import dataclasses_struct as dcs
from dataclasses_struct.dataclass import dataclass_struct


@pytest.mark.parametrize(
    "size,byteorder,field_type",
    [
        *(
            ("native", byteorder, field_type[0])
            for byteorder, field_type in itertools.product(
                native_byteorders, native_only_int_fields
            )
        ),
        *(
            ("std", byteorder, field_type[0])
            for byteorder, field_type in itertools.product(
                std_byteorders, std_only_int_fields
            )
        ),
    ],
)
def test_pack_unpack_int(size, byteorder, field_type) -> None:
    @dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: field_type

    t = T(1)
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert type(unpacked.x) is int
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
@parametrize_fields(float_fields, "field_type")
@pytest.mark.parametrize("value", (1.5, 2.0, 2))
def test_pack_unpack_floats(size, byteorder, field_type, value) -> None:
    @dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: field_type

    t = T(value)
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert type(unpacked.x) is float
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
@parametrize_fields(char_fields, "field_type")
def test_pack_unpack_char(size, byteorder, field_type) -> None:
    @dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: field_type

    t = T(b"x")
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert type(unpacked.x) is bytes
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
@parametrize_fields(bool_fields, "field_type")
@pytest.mark.parametrize("value", (True, False))
def test_pack_unpack_bool(size, byteorder, field_type, value) -> None:
    @dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: field_type

    t = T(value)
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert type(unpacked.x) is bool
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
def test_pack_unpack_bytes_exact_length(size, byteorder) -> None:
    @dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: Annotated[bytes, 3]

    t = T(b"123")
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert type(unpacked.x) is bytes
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
def test_packed_bytes_longer_than_length_is_truncated(size, byteorder) -> None:
    @dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: Annotated[bytes, 3]

    t = T(b"12345")
    packed = t.pack()
    assert len(packed) == 3
    unpacked = T.from_packed(packed)
    assert unpacked.x == b"123"


@parametrize_all_sizes_and_byteorders()
def test_packed_bytes_shorter_than_length_is_zero_padded(
    size, byteorder
) -> None:
    @dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: Annotated[bytes, 5]

    t = T(b"123")
    packed = t.pack()
    assert len(packed) == 5
    unpacked = T.from_packed(packed)
    assert unpacked.x == b"123\0\0"


@parametrize_all_sizes_and_byteorders()
def test_pack_unpack_nested(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Nested:
        x: float
        y: Annotated[bytes, 3]

    assert dcs.get_struct_size(Nested) == struct.calcsize("@ d3b")

    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Container:
        x: dcs.F32
        item1: Annotated[Nested, dcs.PadBefore(10)]
        item2: Annotated[Nested, dcs.PadAfter(12)]
        y: bool

    c = Container(1, Nested(2, b"123"), Nested(5, b"456"), False)
    unpacked = Container.from_packed(c.pack())
    assert type(unpacked.item1) is Nested
    assert type(unpacked.item2) is Nested
    assert c == unpacked


@parametrize_all_sizes_and_byteorders()
def test_pack_unpack_double_nested(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Nested1:
        x: float
        y: Annotated[bytes, 3]

    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Nested2:
        nested1: Annotated[Nested1, dcs.PadBefore(12)]
        nested2: Annotated[Nested1, dcs.PadBefore(12)]

    @dcs.dataclass_struct(size=size, byteorder=byteorder)
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
    assert type(unpacked.item1) is Nested2
    assert type(unpacked.item1.nested1) is Nested1
    assert type(unpacked.item1.nested2) is Nested1
    assert type(unpacked.item2) is Nested2
    assert type(unpacked.item2.nested1) is Nested1
    assert type(unpacked.item2.nested2) is Nested1
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
