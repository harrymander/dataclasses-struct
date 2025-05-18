import ctypes
import dataclasses
import itertools
from re import escape
from typing import Annotated

import pytest
from conftest import (
    ALL_VALID_SIZE_BYTEORDER_PAIRS,
    bool_fields,
    char_fields,
    common_fields,
    float_fields,
    native_only_int_fields,
    parametrize_all_sizes_and_byteorders,
    parametrize_fields,
    parametrize_std_byteorders,
    std_only_int_fields,
)

import dataclasses_struct as dcs


def assert_same_format(t1, t2) -> None:
    assert t1.__dataclass_struct__.format == t2.__dataclass_struct__.format


@parametrize_fields(
    native_only_int_fields + common_fields, "field_type", "fmt"
)
def test_native_size_field_has_correct_format(field_type, fmt) -> None:
    @dcs.dataclass_struct(byteorder="native", size="native")
    class Test:
        field: field_type

    assert Test.__dataclass_struct__.format[1:] == fmt


@parametrize_fields(std_only_int_fields, "field_type")
def test_invalid_native_size_fields_fails(field_type) -> None:
    with pytest.raises(
        TypeError,
        match=r"only supported in standard size mode$",
    ):

        @dcs.dataclass_struct(byteorder="native", size="native")
        class _:
            field: field_type


@parametrize_fields(std_only_int_fields + common_fields, "field_type", "fmt")
@parametrize_std_byteorders()
def test_valid_std_size_field_has_correct_format(
    byteorder, field_type, fmt
) -> None:
    @dcs.dataclass_struct(byteorder=byteorder, size="std")
    class Test:
        field: field_type

    assert Test.__dataclass_struct__.format[1:] == fmt


@parametrize_fields(native_only_int_fields, "field_type")
@parametrize_std_byteorders()
def test_invalid_std_size_fields_fails(byteorder, field_type) -> None:
    with pytest.raises(
        TypeError,
        match=r"only supported in native size mode$",
    ):

        @dcs.dataclass_struct(byteorder=byteorder, size="std")
        class _:
            field: field_type


def test_builtin_int_is_int() -> None:
    @dcs.dataclass_struct(byteorder="native", size="native")
    class Builtin:
        x: int

    @dcs.dataclass_struct(byteorder="native", size="native")
    class Field:
        x: dcs.Int

    assert_same_format(Builtin, Field)


@parametrize_all_sizes_and_byteorders()
def test_builtin_bool_is_bool(byteorder, size) -> None:
    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Builtin:
        x: bool

    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Field:
        x: dcs.Bool

    assert_same_format(Builtin, Field)


@parametrize_all_sizes_and_byteorders()
def test_builtin_float_is_f64(byteorder, size) -> None:
    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Builtin:
        x: float

    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Field:
        x: dcs.F64

    assert_same_format(Builtin, Field)


@parametrize_all_sizes_and_byteorders()
def test_builtin_bytes_is_char(byteorder, size) -> None:
    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Builtin:
        x: bytes

    @dcs.dataclass_struct(byteorder=byteorder, size=size)
    class Field:
        x: dcs.Char

    assert_same_format(Builtin, Field)


@dataclasses.dataclass
class DataClassTest:
    pass


class VanillaClassTest:
    pass


@parametrize_all_sizes_and_byteorders()
@pytest.mark.parametrize(
    "field_type", [str, list, dict, DataClassTest, VanillaClassTest]
)
def test_invalid_field_types_fail(byteorder, size, field_type) -> None:
    with pytest.raises(TypeError, match=r"^type not supported:"):

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: field_type


@parametrize_all_sizes_and_byteorders()
def test_valid_bytes_length_has_correct_format(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        field: Annotated[bytes, 3]

    assert Test.__dataclass_struct__.format[1:] == "3s"


@pytest.mark.parametrize("length", (-1, 0, 1.0, "1"))
@parametrize_all_sizes_and_byteorders()
def test_invalid_bytes_length_fails(size, byteorder, length: int) -> None:
    with pytest.raises(
        ValueError,
        match=r"^bytes length must be positive non-zero int$",
    ):

        @dcs.dataclass_struct(size=size, byteorder=byteorder)
        class _:
            x: Annotated[bytes, length]


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
    with pytest.raises(ValueError, match=r"^value out of range"):

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
    with pytest.raises(ValueError, match=r"^value out of range"):

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
    with pytest.raises(TypeError, match=r"^invalid type for field:"):

        @dcs.dataclass_struct(size="std", byteorder=byteorder)
        class _:
            x: int_type = default


@parametrize_fields(native_only_int_fields, "int_type")
@parametrize_invalid_int_defaults
def test_native_int_default_wrong_type_fails(int_type, default) -> None:
    with pytest.raises(TypeError, match=r"^invalid type for field:"):

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
    with pytest.raises(TypeError, match=r"^invalid type for field:"):

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
    with pytest.raises(TypeError, match=r"^invalid type for field:"):

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
    with pytest.raises(TypeError, match=r"^invalid type for field:"):

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: bool = default


@parametrize_all_sizes_and_byteorders()
def test_invalid_annotated_fails(byteorder, size) -> None:
    with pytest.raises(TypeError, match=r"^invalid field annotation:"):

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: Annotated[int, dcs.I64]


@parametrize_all_sizes_and_byteorders()
def test_bytes_with_too_many_annotations_fails(byteorder, size) -> None:
    with pytest.raises(TypeError, match=r"^too many annotations: 12$"):

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: Annotated[bytes, 1, 12]


@pytest.mark.parametrize(
    "nested_size_byteorder,container_size_byteorder",
    itertools.combinations(ALL_VALID_SIZE_BYTEORDER_PAIRS, 2),
)
def test_nested_dataclass_with_mismatched_size_and_byteorder_fails(
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


@pytest.mark.parametrize("size", (-1, 1.0, "1"))
@pytest.mark.parametrize("padding", (dcs.PadBefore, dcs.PadAfter))
def test_invalid_padding_size_fails(size: int, padding: type) -> None:
    with pytest.raises(
        ValueError,
        match=r"^padding size must be non-negative int$",
    ):

        @dcs.dataclass_struct()
        class _:
            x: Annotated[int, padding(size)]


def test_str_type_annotations() -> None:
    @dcs.dataclass_struct(size="std")
    class _:
        a: "dcs.Char"
        b: "dcs.I8"
        c: "dcs.U8"
        d: "dcs.Bool"
        e: "dcs.I16"
        f: "dcs.U16"
        g: "dcs.I32"
        h: "dcs.U32"
        i: "dcs.I64"
        j: "dcs.U64"
        k: "dcs.F32"
        l: "dcs.F64"  # noqa: E741
        m: "Annotated[bytes, 10]"
