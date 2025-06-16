import sys
from collections.abc import Iterable
from contextlib import contextmanager
from typing import Callable, List  # noqa: UP035

import pytest

import dataclasses_struct as dcs

std_byteorders = ("native", "big", "little", "network")
native_byteorders = ("native",)

ALL_VALID_SIZE_BYTEORDER_PAIRS = (
    *(("native", e) for e in native_byteorders),
    *(("std", e) for e in std_byteorders),
)


ParametrizeDecorator = Callable[[Callable], pytest.MarkDecorator]

TestFields = list[tuple[type, str]]
native_only_int_fields: TestFields = [
    (dcs.SignedChar, "b"),
    (dcs.UnsignedChar, "B"),
    (dcs.Short, "h"),
    (dcs.UnsignedShort, "H"),
    (int, "i"),
    (dcs.Int, "i"),
    (dcs.UnsignedInt, "I"),
    (dcs.Long, "l"),
    (dcs.UnsignedLong, "L"),
    (dcs.LongLong, "q"),
    (dcs.UnsignedLongLong, "Q"),
    (dcs.SignedSize, "n"),
    (dcs.UnsignedSize, "N"),
    (dcs.Pointer, "P"),
]
std_only_int_fields: TestFields = [
    (dcs.U8, "B"),
    (dcs.U16, "H"),
    (dcs.U32, "I"),
    (dcs.U64, "Q"),
    (dcs.I8, "b"),
    (dcs.I16, "h"),
    (dcs.I32, "i"),
    (dcs.I64, "q"),
]
float_fields: TestFields = [
    (dcs.F16, "e"),
    (dcs.F32, "f"),
    (dcs.F64, "d"),
    (float, "d"),
]
bool_fields: TestFields = [(dcs.Bool, "?"), (bool, "?")]
char_fields: TestFields = [(dcs.Char, "c"), (bytes, "c")]
common_fields: TestFields = float_fields + bool_fields + char_fields


def parametrize_fields(
    fields: TestFields, field_argname: str, format_argname=None
):
    fields_iter: Iterable
    if format_argname:
        argnames = ",".join((field_argname, format_argname))
        fields_iter = fields
    else:
        argnames = field_argname
        fields_iter = (field[0] for field in fields)

    def mark(f):
        return pytest.mark.parametrize(argnames, fields_iter)(f)

    return mark


def parametrize_std_byteorders(
    argname: str = "byteorder",
) -> ParametrizeDecorator:
    def mark(f) -> pytest.MarkDecorator:
        return pytest.mark.parametrize(argname, std_byteorders)(f)

    return mark


def parametrize_all_sizes_and_byteorders(
    size_argname: str = "size", byteorder_argname: str = "byteorder"
) -> ParametrizeDecorator:
    def mark(f) -> pytest.MarkDecorator:
        return pytest.mark.parametrize(
            ",".join((size_argname, byteorder_argname)),
            ALL_VALID_SIZE_BYTEORDER_PAIRS,
        )(f)

    return mark


def parametrize_all_list_types() -> ParametrizeDecorator:
    def mark(f) -> pytest.MarkDecorator:
        return pytest.mark.parametrize(
            "list_type",
            [list, List],  # noqa: UP006
        )(f)

    return mark


skipif_kw_only_not_supported = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="kw_only added in Python 3.10",
)


@contextmanager
def raises_default_value_out_of_range_error():
    with pytest.raises(ValueError, match=r"^value out of range for"):
        yield


@contextmanager
def raises_default_value_invalid_type_error():
    with pytest.raises(TypeError, match=r"^invalid type for field: expected"):
        yield


@contextmanager
def raises_unsupported_size_mode(supported_mode: str):
    with pytest.raises(
        TypeError,
        match=rf"^field .+? only supported in {supported_mode} size mode$",
    ):
        yield


@contextmanager
def raises_field_type_not_supported():
    with pytest.raises(TypeError, match=r"^type not supported:"):
        yield


@contextmanager
def raises_invalid_field_annotation():
    with pytest.raises(TypeError, match=r"^invalid field annotation:"):
        yield
