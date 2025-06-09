import dataclasses
import re

import pytest
from conftest import parametrize_all_sizes_and_byteorders

import dataclasses_struct as dcs


def test_no_parens_fails():
    msg = "dataclass_struct() takes 0 positional arguments but 1 was given"
    with pytest.raises(TypeError, match=rf"^{re.escape(msg)}$"):

        @dcs.dataclass_struct
        class _:  # type: ignore
            pass


@pytest.mark.parametrize(
    "kwargs",
    (
        # Invalid byteorder with explicit arg size='native'
        {"size": "native", "byteorder": "big"},
        {"size": "native", "byteorder": "little"},
        {"size": "native", "byteorder": "network"},
        # Invalid byteorder with default arg size='native'
        {"byteorder": "big"},
        {"byteorder": "little"},
        {"byteorder": "network"},
        # Invalid parameters
        {"byteorder": "invalid_byteorder"},
        {"size": "invalid_size"},
        {"size": "std", "byteorder": "invalid_byteorder"},
    ),
)
def test_invalid_decorator_args(kwargs):
    with pytest.raises(ValueError):

        @dcs.dataclass_struct(**kwargs)
        class _:
            pass


@parametrize_all_sizes_and_byteorders()
def test_valid_sizes_and_byteorders(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class _:
        pass


@pytest.mark.parametrize(
    "size,byteorder,mode",
    (
        ("native", "native", "@"),
        ("std", "native", "="),
        ("std", "little", "<"),
        ("std", "big", ">"),
        ("std", "network", "!"),
    ),
)
def test_mode_char(size, byteorder, mode: str) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)  # type: ignore
    class Test:
        pass

    assert Test.__dataclass_struct__.mode == mode
    assert Test.__dataclass_struct__.format == mode


def test_default_mode_char_is_native() -> None:
    @dcs.dataclass_struct()
    class Test:
        pass

    assert Test.__dataclass_struct__.mode == "@"
    assert Test.__dataclass_struct__.format == "@"


@parametrize_all_sizes_and_byteorders()
def test_empty_class_has_zero_size(size, byteorder) -> None:
    @dcs.dataclass_struct(size=size, byteorder=byteorder)
    class Test:
        pass

    assert Test.__dataclass_struct__.size == 0


def test_class_is_dataclass_struct() -> None:
    @dcs.dataclass_struct()
    class Test:
        pass

    assert dcs.is_dataclass_struct(Test)


def test_object_is_dataclass_struct() -> None:
    @dcs.dataclass_struct()
    class Test:
        pass

    assert dcs.is_dataclass_struct(Test())


def test_object_is_dataclass() -> None:
    @dcs.dataclass_struct()
    class Test:
        pass

    assert dataclasses.is_dataclass(Test())


def test_class_is_dataclass() -> None:
    @dcs.dataclass_struct()
    class Test:
        pass

    assert dataclasses.is_dataclass(Test)


def test_undecorated_class_is_not_dataclass_struct() -> None:
    class Test:
        pass

    assert not dcs.is_dataclass_struct(Test)


def test_undecorated_object_is_not_dataclass_struct() -> None:
    class Test:
        pass

    assert not dcs.is_dataclass_struct(Test())


def test_stdlib_dataclass_class_is_not_dataclass_struct() -> None:
    @dataclasses.dataclass
    class Test:
        pass

    assert not dcs.is_dataclass_struct(Test)


def test_stdlib_dataclass_object_is_not_dataclass_struct() -> None:
    @dataclasses.dataclass
    class Test:
        pass

    assert not dcs.is_dataclass_struct(Test())


@pytest.mark.parametrize(
    "kwarg,value",
    [("slots", True), ("weakref_slot", True)],
)
def test_unsupported_dataclass_kwarg_fails(kwarg: str, value):
    escaped = re.escape(kwarg)
    with pytest.raises(
        ValueError,
        match=rf"^dataclass '{escaped}' keyword argument is not supported$",
    ):
        dcs.dataclass_struct(**{kwarg: value})
