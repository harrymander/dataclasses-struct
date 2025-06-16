import dataclasses
import itertools
from contextlib import contextmanager
from re import escape
from typing import Annotated

import pytest
from conftest import (
    ALL_VALID_SIZE_BYTEORDER_PAIRS,
    common_fields,
    native_only_int_fields,
    parametrize_all_list_types,
    parametrize_all_sizes_and_byteorders,
    parametrize_fields,
    parametrize_std_byteorders,
    raises_field_type_not_supported,
    raises_invalid_field_annotation,
    raises_unsupported_size_mode,
    skipif_kw_only_not_supported,
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
    with raises_unsupported_size_mode("standard"):

        @dcs.dataclass_struct(byteorder="native", size="native")
        class _:
            field: field_type


@parametrize_fields(std_only_int_fields, "field_type")
@parametrize_all_list_types()
def test_array_with_invalid_native_size_fields_fails(
    field_type, list_type
) -> None:
    with raises_unsupported_size_mode("standard"):

        @dcs.dataclass_struct(byteorder="native", size="native")
        class _:
            field: Annotated[list_type[field_type], 2]


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
    with raises_unsupported_size_mode("native"):

        @dcs.dataclass_struct(byteorder=byteorder, size="std")
        class _:
            field: field_type


@parametrize_fields(native_only_int_fields, "field_type")
@parametrize_all_list_types()
@parametrize_std_byteorders()
def test_array_with_invalid_std_size_fields_fails(
    field_type, list_type, byteorder
) -> None:
    with raises_unsupported_size_mode("native"):

        @dcs.dataclass_struct(byteorder=byteorder, size="std")
        class _:
            field: Annotated[list_type[field_type], 2]


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
    with raises_field_type_not_supported():

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


@pytest.mark.parametrize("length", (-1, 0, 1.0, "1"))
@parametrize_all_list_types()
def test_invalid_array_length_fails(length: int, list_type) -> None:
    with pytest.raises(
        ValueError,
        match=r"^fixed-length array length must be positive non-zero int$",
    ):

        @dcs.dataclass_struct()
        class _:
            x: Annotated[list_type[int], length]


@parametrize_all_sizes_and_byteorders()
@parametrize_all_list_types()
def test_unannotated_list_fails(size, byteorder, list_type) -> None:
    with pytest.raises(
        TypeError,
        match=r"^list types must be marked as a fixed-length using Annotated, "
        r"ex: Annotated\[list\[int\], 5\]$",
    ):

        @dcs.dataclass_struct(size=size, byteorder=byteorder)
        class _:
            x: list_type[int]


@parametrize_all_sizes_and_byteorders()
@parametrize_all_list_types()
def test_annotated_list_with_invalid_arg_type_fails(
    size, byteorder, list_type
) -> None:
    with raises_field_type_not_supported():

        @dcs.dataclass_struct(size=size, byteorder=byteorder)
        class _:
            x: Annotated[list_type[str], 5]


@parametrize_all_sizes_and_byteorders()
def test_annotated_list_without_arg_type_fails(size, byteorder) -> None:
    with raises_invalid_field_annotation():

        @dcs.dataclass_struct(size=size, byteorder=byteorder)
        class _:
            x: Annotated[list, 5]


@parametrize_all_sizes_and_byteorders()
def test_invalid_annotated_fails(byteorder, size) -> None:
    with raises_invalid_field_annotation():

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: Annotated[int, dcs.I64]


@parametrize_all_sizes_and_byteorders()
def test_bytes_with_too_many_annotations_fails(byteorder, size) -> None:
    with pytest.raises(TypeError, match=r"^too many annotations: 12$"):

        @dcs.dataclass_struct(byteorder=byteorder, size=size)
        class _:
            x: Annotated[bytes, 1, 12]


def parametrize_all_size_and_byteorder_combinations() -> pytest.MarkDecorator:
    """
    All combinations of size and byteorder, including invalid combinations.
    """
    return pytest.mark.parametrize(
        "nested_size_byteorder,container_size_byteorder",
        itertools.combinations(ALL_VALID_SIZE_BYTEORDER_PAIRS, 2),
    )


@contextmanager
def raises_mismatched_nested_class_error(
    nested_size,
    nested_byteorder,
    container_size,
    container_byteorder,
):
    exp_msg = f"""
    byteorder and size of nested dataclass-struct does not
    match that of container (expected '{container_size}' size and
    '{container_byteorder}' byteorder, got '{nested_size}' size and
    '{nested_byteorder}' byteorder)
    """
    exp_msg = " ".join(exp_msg.split())
    with pytest.raises(TypeError, match=f"^{escape(exp_msg)}$"):
        yield


@parametrize_all_size_and_byteorder_combinations()
def test_nested_dataclass_with_mismatched_size_and_byteorder_fails(
    nested_size_byteorder, container_size_byteorder
) -> None:
    nested_size, nested_byteorder = nested_size_byteorder
    container_size, container_byteorder = container_size_byteorder
    with raises_mismatched_nested_class_error(
        nested_size,
        nested_byteorder,
        container_size,
        container_byteorder,
    ):

        @dcs.dataclass_struct(size=nested_size, byteorder=nested_byteorder)
        class Nested:
            pass

        @dcs.dataclass_struct(
            size=container_size,
            byteorder=container_byteorder,
        )
        class _:
            y: Nested


@parametrize_all_size_and_byteorder_combinations()
@parametrize_all_list_types()
def test_list_of_dataclass_structs_with_mismatched_size_and_byteorder_fails(
    nested_size_byteorder, container_size_byteorder, list_type
) -> None:
    nested_size, nested_byteorder = nested_size_byteorder
    container_size, container_byteorder = container_size_byteorder
    with raises_mismatched_nested_class_error(
        nested_size,
        nested_byteorder,
        container_size,
        container_byteorder,
    ):

        @dcs.dataclass_struct(size=nested_size, byteorder=nested_byteorder)
        class Nested:
            pass

        @dcs.dataclass_struct(
            size=container_size,
            byteorder=container_byteorder,
        )
        class _:
            y: Annotated[list_type[Nested], 2]


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


@skipif_kw_only_not_supported
def test_kw_only_marker() -> None:
    from dataclasses import KW_ONLY  # type: ignore

    @dcs.dataclass_struct()
    class T:
        arg1: int
        arg2: int
        _: KW_ONLY
        kwarg1: float
        kwarg2: bool

    with pytest.raises(TypeError):
        T(1, 2, 1.2, False)  # type: ignore
