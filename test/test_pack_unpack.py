import dataclasses
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
    parametrize_all_list_types,
    parametrize_all_sizes_and_byteorders,
    parametrize_fields,
    parametrize_std_byteorders,
    skipif_kw_only_not_supported,
    std_byteorders,
    std_only_int_fields,
)

import dataclasses_struct as dcs


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
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
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
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
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
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
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
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: field_type

    t = T(value)
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert type(unpacked.x) is bool
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
def test_pack_unpack_bytes_exact_length(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: Annotated[bytes, 3]

    t = T(b"123")
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert type(unpacked.x) is bytes
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
def test_packed_bytes_longer_than_length_is_truncated(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
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
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
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


@parametrize_std_byteorders()
@parametrize_all_list_types()
@parametrize_fields(std_only_int_fields, "int_type")
def test_pack_unpack_array_of_std_int_types(
    byteorder, list_type, int_type
) -> None:
    @dcs.dataclass_struct(size="std", byteorder=byteorder)
    class T:
        x: Annotated[list_type[int_type], 5]

    t = T([1, 2, 3, 4, 5])
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert isinstance(unpacked.x, list)
    assert t == unpacked


@parametrize_all_list_types()
@parametrize_fields(native_only_int_fields, "int_type")
def test_pack_unpack_array_of_native_int_types(list_type, int_type) -> None:
    @dcs.dataclass_struct()
    class T:
        x: Annotated[list_type[int_type], 5]

    t = T([1, 2, 3, 4, 5])
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert isinstance(unpacked.x, list)
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
@parametrize_all_list_types()
@parametrize_fields(float_fields, "float_type")
def test_pack_unpack_array_of_float_types(
    size, byteorder, list_type, float_type
) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: Annotated[list_type[float_type], 5]

    t = T([1.0, 2.0, 3.0, 4.0, 5.0])
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert isinstance(unpacked.x, list)
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
@parametrize_all_list_types()
def test_pack_unpack_array_of_dataclass_struct(
    size, byteorder, list_type
) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Nested:
        x: float
        y: float

    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: Annotated[list_type[Nested], 2]

    t = T([Nested(1.0, 2.0), Nested(3.0, 4.0)])
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert isinstance(unpacked.x, list)
    assert t == unpacked


@parametrize_all_list_types()
def test_pack_unpack_2d_array_of_primitives(list_type) -> None:
    @dcs.dataclass_struct()
    class T:
        x: Annotated[list_type[Annotated[list_type[int], 3]], 2]

    t = T([[1, 2, 3], [4, 5, 6]])
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert isinstance(unpacked.x, list)
    assert t == unpacked


@parametrize_all_sizes_and_byteorders()
@parametrize_all_list_types()
def test_pack_unpack_2d_array_of_dataclass_struct(
    size, byteorder, list_type
) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Nested:
        x: float
        y: float

    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: Annotated[list_type[Annotated[list_type[Nested], 3]], 2]

    t = T(
        [
            [Nested(1.0, 2.0), Nested(3.0, 4.0), Nested(5.0, 6.0)],
            [Nested(7.0, 8.0), Nested(9.0, 10.0), Nested(11.0, 12.0)],
        ]
    )
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert isinstance(unpacked.x, list)
    assert t == unpacked


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
@parametrize_all_list_types()
def test_pack_unpack_with_padding_around_fixed_size_array(
    size, byteorder, list_type
) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        a: Annotated[list_type[bool], dcs.PadBefore(2), 4, dcs.PadAfter(3)]

    t = Test([True, True, False, True])
    packed = t.pack()
    assert packed == b"\x00\x00\x01\x01\x00\x01\x00\x00\x00"
    assert Test.from_packed(packed) == t


@parametrize_all_sizes_and_byteorders()
@parametrize_all_list_types()
def test_pack_unpack_fixed_size_array_with_padding(
    size, byteorder, list_type
) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        a: Annotated[
            list_type[Annotated[bytes, dcs.PadBefore(2), dcs.PadAfter(3)]], 4
        ]

    items = [b"1", b"2", b"3", b"4"]
    t = Test(items)
    packed = t.pack()

    exp_packed_bytes: list[int] = []
    for i in items:
        exp_packed_bytes.extend(0 for _ in range(2))
        exp_packed_bytes.append(i[0])
        exp_packed_bytes.extend(0 for _ in range(3))

    exp_packed = bytes(exp_packed_bytes)
    assert packed == exp_packed
    assert Test.from_packed(packed) == t


@parametrize_all_sizes_and_byteorders()
@parametrize_all_list_types()
def test_pack_unpack_list_of_byte_arrays(size, byteorder, list_type) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class T:
        x: Annotated[list_type[Annotated[bytes, 5]], 4]

    t = T([b"", b"1234", b"123456", b"12345"])
    packed = t.pack()
    unpacked = T.from_packed(packed)
    assert isinstance(unpacked.x, list)
    assert unpacked == T([b"\0" * 5, b"1234\0", b"12345", b"12345"])


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


@skipif_kw_only_not_supported
def test_pack_unpack_with_kw_only() -> None:
    @dcs.dataclass_struct(kw_only=True)  # type: ignore
    class KwOnly:
        x: int
        y: bool
        z: float

    kw_only = KwOnly(z=-5.0, x=12, y=True)
    packed = kw_only.pack()
    unpacked = KwOnly.from_packed(packed)
    assert unpacked == kw_only


@skipif_kw_only_not_supported
def test_pack_unpack_with_nested_kw_only() -> None:
    @dcs.dataclass_struct(kw_only=True)  # type: ignore
    class KwOnly:
        x: int
        y: bool
        z: float

    @dcs.dataclass_struct()
    class Container:
        a: KwOnly
        b: KwOnly

    c = Container(KwOnly(y=True, z=-5.0, x=12), KwOnly(z=0.25, x=100, y=False))
    packed = c.pack()
    unpacked = Container.from_packed(packed)
    assert unpacked == c


def test_pack_unpack_with_no_init_args_initialised_with_defaults() -> None:
    @dcs.dataclass_struct(init=False)
    class T:
        x: int = 1
        y: int = 2

    t = T()
    assert t.x == 1
    assert t.y == 2

    t.x = 3
    t.y = 4
    unpacked = T.from_packed(t.pack())
    assert unpacked.x == 3
    assert unpacked.y == 4


def test_pack_unpack_with_no_init_args_initialised_in_user_init() -> None:
    @dcs.dataclass_struct(init=False)
    class T:
        x: int
        y: int

        def __init__(self) -> None:
            self.x = 1
            self.y = 2

    t = T()
    assert t.x == 1
    assert t.y == 2

    t.x = 3
    t.y = 4
    unpacked = T.from_packed(t.pack())
    assert unpacked.x == 3
    assert unpacked.y == 4


def test_pack_unpack_with_specific_field_no_init() -> None:
    @dcs.dataclass_struct()
    class T:
        x: int = dataclasses.field(default=-100)
        y: int = dataclasses.field(default=200, init=False)

    t = T(x=100)
    assert t.x == 100
    assert t.y == 200

    t.y = -200
    unpacked = T.from_packed(t.pack())
    assert unpacked.x == 100
    assert unpacked.y == -200


def test_pack_unpack_with_no_init_in_decorator_overriding_fields_init() -> (
    None
):
    @dcs.dataclass_struct(init=False)
    class T:
        x: int = dataclasses.field(init=True, default=100)
        y: int = dataclasses.field(init=True, default=200)

    t = T()
    assert t.x == 100
    assert t.y == 200

    t.x = -100
    t.y = -200
    unpacked = T.from_packed(t.pack())
    assert unpacked.x == -100
    assert unpacked.y == -200


def test_pack_unpack_no_init_fields_with_validate_defaults_false() -> None:
    @dcs.dataclass_struct(validate_defaults=False)
    class T:
        x: int = dataclasses.field(init=False, default=1)

    t = T()
    assert t.x == 1

    t.x = -1
    unpacked = T.from_packed(t.pack())
    assert unpacked.x == -1
