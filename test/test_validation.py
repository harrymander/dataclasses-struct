import ctypes
from contextlib import contextmanager
from dataclasses import field
from typing import Annotated

import pytest
from conftest import (
    bool_fields,
    char_fields,
    float_fields,
    native_only_int_fields,
    parametrize_all_list_types,
    parametrize_all_sizes_and_byteorders,
    parametrize_fields,
    parametrize_std_byteorders,
    raises_default_value_invalid_type_error,
    raises_default_value_out_of_range_error,
    std_only_int_fields,
)

import dataclasses_struct as dcs


def int_min_max(nbits: int, signed: bool) -> tuple[int, int]:
    if signed:
        exp = 2 ** (nbits - 1)
        return -exp, exp - 1
    else:
        return 0, 2**nbits - 1


std_int_out_of_range_vals = []
std_int_boundary_vals = []
for field_type, nbits, signed in (
    (dcs.I8, 8, True),
    (dcs.U8, 8, False),
    (dcs.I16, 16, True),
    (dcs.U16, 16, False),
    (dcs.I32, 32, True),
    (dcs.U32, 32, False),
    (dcs.I64, 64, True),
    (dcs.U64, 64, False),
):
    min_, max_ = int_min_max(nbits, signed)
    std_int_out_of_range_vals.append((field_type, min_ - 1))
    std_int_out_of_range_vals.append((field_type, max_ + 1))
    std_int_boundary_vals.append((field_type, min_))
    std_int_boundary_vals.append((field_type, max_))


@pytest.mark.parametrize("field_type,default", std_int_boundary_vals)
@parametrize_std_byteorders()
def test_std_int_default(field_type, default, byteorder) -> None:
    @dcs.dataclass_struct(size="std", byteorder=byteorder)
    class Class:
        field: field_type = default

    assert Class().field == default


@pytest.mark.parametrize("field_type,default", std_int_out_of_range_vals)
@parametrize_std_byteorders()
def test_std_int_default_out_of_range_fails(
    field_type, default, byteorder
) -> None:
    with raises_default_value_out_of_range_error():

        @dcs.dataclass_struct(size="std", byteorder=byteorder)
        class _:
            x: field_type = default


@pytest.mark.parametrize("field_type,default", std_int_out_of_range_vals)
@parametrize_std_byteorders()
def test_std_int_default_out_of_range_with_unvalidated_does_not_fail(
    field_type, default, byteorder
) -> None:
    @dcs.dataclass_struct(
        size="std",
        byteorder=byteorder,
        validate_defaults=False,
    )
    class Class:
        x: field_type = default

    assert Class().x == default


native_int_out_of_range_vals = []
native_int_boundary_vals = []
for field_type, ctype_type, signed in (
    (dcs.SignedChar, ctypes.c_byte, True),
    (dcs.UnsignedChar, ctypes.c_ubyte, False),
    (dcs.Short, ctypes.c_short, True),
    (dcs.UnsignedShort, ctypes.c_ushort, False),
    (int, ctypes.c_int, True),
    (dcs.Int, ctypes.c_int, True),
    (dcs.UnsignedInt, ctypes.c_uint, False),
    (dcs.Long, ctypes.c_long, True),
    (dcs.UnsignedLong, ctypes.c_ulong, False),
    (dcs.LongLong, ctypes.c_longlong, True),
    (dcs.UnsignedLongLong, ctypes.c_ulonglong, False),
    (dcs.SignedSize, ctypes.c_ssize_t, True),
    (dcs.UnsignedSize, ctypes.c_size_t, False),
    (dcs.Pointer, ctypes.c_void_p, False),
):
    min_, max_ = int_min_max(ctypes.sizeof(ctype_type) * 8, signed)
    native_int_out_of_range_vals.append((field_type, min_ - 1))
    native_int_out_of_range_vals.append((field_type, max_ + 1))
    native_int_boundary_vals.append((field_type, min_))
    native_int_boundary_vals.append((field_type, max_))


@pytest.mark.parametrize("field_type,default", native_int_boundary_vals)
def test_native_int_default(field_type, default) -> None:
    @dcs.dataclass_struct(size="native", byteorder="native")
    class Class:
        field: field_type = default

    assert Class().field == default


@pytest.mark.parametrize("field_type,default", native_int_out_of_range_vals)
def test_native_int_default_out_of_range_fails(field_type, default) -> None:
    with raises_default_value_out_of_range_error():

        @dcs.dataclass_struct(size="native", byteorder="native")
        class _:
            x: field_type = default


@pytest.mark.parametrize("field_type,default", native_int_out_of_range_vals)
def test_native_int_default_out_of_range_with_unvalidated_does_not_fail(
    field_type, default
) -> None:
    @dcs.dataclass_struct(
        size="native",
        byteorder="native",
        validate_defaults=False,
    )
    class Class:
        x: field_type = default

    assert Class().x == default


def parametrize_invalid_int_defaults(f):
    return pytest.mark.parametrize(
        "default",
        (
            "wrong",
            1.5,
            "1",
            None,
        ),
    )(f)


@parametrize_fields(std_only_int_fields, "int_type")
@parametrize_std_byteorders()
@parametrize_invalid_int_defaults
def test_std_int_default_wrong_type_fails(
    int_type, byteorder, default
) -> None:
    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct(size="std", byteorder=byteorder)
        class _:
            x: int_type = default


@parametrize_fields(native_only_int_fields, "int_type")
@parametrize_invalid_int_defaults
def test_native_int_default_wrong_type_fails(int_type, default) -> None:
    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct(size="native", byteorder="native")
        class _:
            x: int_type = default


@parametrize_all_sizes_and_byteorders()
@parametrize_fields(char_fields, "char_field")
def test_char_default(byteorder, size, char_field) -> None:
    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Test:
        field: char_field = b"1"

    assert Test().field == b"1"


@parametrize_all_sizes_and_byteorders()
@parametrize_fields(char_fields, "field_type")
def test_char_default_wrong_type_fails(byteorder, size, field_type) -> None:
    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: field_type = "s"


@parametrize_all_sizes_and_byteorders()
@pytest.mark.parametrize("c", (b"", b"ab"))
@parametrize_fields(char_fields, "field_type")
def test_char_default_wrong_length_fails(
    field_type, byteorder, size, c: bytes
) -> None:
    with pytest.raises(ValueError, match=r"^value must be a single byte$"):

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: field_type = c


@parametrize_all_sizes_and_byteorders()
@parametrize_fields(char_fields, "char_field")
def test_bytes_array_default(byteorder, size, char_field) -> None:
    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Test:
        field: Annotated[char_field, 10] = b"123"

    assert Test().field == b"123"


@parametrize_all_sizes_and_byteorders()
def test_bytes_array_default_too_long_fails(byteorder, size) -> None:
    with pytest.raises(
        ValueError,
        match=r"^bytes cannot be longer than 8 bytes$",
    ):

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: Annotated[bytes, 8] = b"123456789"


@parametrize_all_sizes_and_byteorders()
@parametrize_fields(float_fields, "float_field")
@pytest.mark.parametrize("default", (10, 10.12))
def test_float_default(size, byteorder, float_field, default) -> None:
    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Test:
        field: float_field = default

    assert Test().field == default


@parametrize_all_sizes_and_byteorders()
@parametrize_fields(float_fields, "float_field")
@pytest.mark.parametrize("default", ("wrong", "1.5", None))
def test_float_default_wrong_type_fails(
    byteorder, size, float_field, default
) -> None:
    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: float_field = default  # type: ignore


@parametrize_all_sizes_and_byteorders()
@parametrize_fields(bool_fields, "bool_field")
def test_bool_default(byteorder, size, bool_field) -> None:
    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Test:
        field: bool_field = False

    assert Test().field is False


@parametrize_all_sizes_and_byteorders()
@pytest.mark.parametrize("default", ("wrong", "1.5", None, "False"))
def test_bool_default_wrong_type_fails(byteorder, size, default) -> None:
    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: bool = default


def test_nested_dataclass_default_wrong_type_fails() -> None:
    @dcs.dataclass_struct()
    class A:
        x: int

    @dcs.dataclass_struct()
    class B:
        x: int

    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct()
        class _:
            a: A = field(default_factory=lambda: B(100))  # type: ignore


@contextmanager
def raises_fixed_length_array_wrong_length_error(expected: int, actual: int):
    with pytest.raises(
        ValueError,
        match=(
            r"^fixed-length array must have length of "
            rf"{expected}, got {actual}$"
        ),
    ):
        yield


@pytest.mark.parametrize("default", ([], [1, 2], [1, 2, 3, 4]))
@parametrize_all_list_types()
def test_array_default_wrong_length_fails(list_type, default: list[int]):
    with raises_fixed_length_array_wrong_length_error(3, len(default)):

        @dcs.dataclass_struct()
        class _:
            x: Annotated[list_type[int], 3] = field(
                default_factory=lambda: default
            )


@pytest.mark.parametrize("default", [1, (1, 2, 3)], ids=["scalar", "tuple"])
@parametrize_all_list_types()
def test_array_default_wrong_type_fails(list_type, default) -> None:
    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct()
        class _:
            x: Annotated[list_type[int], 3] = field(
                default_factory=lambda: default
            )


@parametrize_all_list_types()
def test_array_default_item_out_of_range_fails(list_type) -> None:
    with raises_default_value_out_of_range_error():

        @dcs.dataclass_struct()
        class _:
            x: Annotated[list_type[dcs.UnsignedInt], 3] = field(
                default_factory=lambda: [1, -2, 3]
            )


@parametrize_all_list_types()
def test_2d_array_default_item_out_of_range_fails(list_type) -> None:
    with raises_default_value_out_of_range_error():

        @dcs.dataclass_struct()
        class _:
            x: Annotated[
                list_type[Annotated[list_type[dcs.UnsignedInt], 2]], 3
            ] = field(default_factory=lambda: [[1, 2], [-3, 4], [5, 6]])


@parametrize_all_list_types()
def test_array_default_item_wrong_type_fails(list_type) -> None:
    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct()
        class _:
            x: Annotated[list_type[int], 3] = field(
                default_factory=lambda: [1, 2.0, 3]
            )


@parametrize_all_list_types()
def test_2d_array_default_item_wrong_type_fails(list_type) -> None:
    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct()
        class _:
            x: Annotated[list_type[Annotated[list_type[int], 2]], 3] = field(
                default_factory=lambda: [[1, 2], [3, 4.0], [5, 6]]
            )


@parametrize_all_list_types()
@pytest.mark.parametrize("default", ([], [1], [1, 2, 3]))
def test_2d_array_default_item_wrong_length_fails(
    list_type, default: list[int]
) -> None:
    with raises_fixed_length_array_wrong_length_error(2, len(default)):

        @dcs.dataclass_struct()
        class _:
            x: Annotated[list_type[Annotated[list_type[int], 2]], 3] = field(
                default_factory=lambda: [[1, 2], default, [3, 4]]
            )
