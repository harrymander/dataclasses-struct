from dataclasses import field
from typing import Any

import pytest
from conftest import (
    raises_default_value_invalid_type_error,
    raises_default_value_out_of_range_error,
)

import dataclasses_struct as dcs


def test_dataclasses_field_empty() -> None:
    @dcs.dataclass_struct()
    class T:
        x: int = field()

    T(12)

    with pytest.raises(
        TypeError,
        match="missing 1 required positional argument",
    ):
        T()


def parametrize_field_kwargs(val: Any) -> pytest.MarkDecorator:
    """
    Parametrise dataclasses.field kwargs on 'default' and 'default_kwargs'.
    """
    return pytest.mark.parametrize(
        "field_kwargs",
        ({"default": val}, {"default_factory": lambda: val}),
        ids=("default", "default_factory"),
    )


@parametrize_field_kwargs(100)
def test_dataclasses_field_default(field_kwargs) -> None:
    @dcs.dataclass_struct()
    class T:
        x: int = field(**field_kwargs)

    t = T()
    assert t.x == 100

    t = T(200)
    assert t.x == 200


@parametrize_field_kwargs(100.0)
def test_dataclasses_field_default_wrong_type_fails(field_kwargs) -> None:
    with raises_default_value_invalid_type_error():

        @dcs.dataclass_struct()
        class _:
            x: int = field(**field_kwargs)


@parametrize_field_kwargs(-100)
def test_dataclasses_field_default_invalid_value_fails(field_kwargs) -> None:
    with raises_default_value_out_of_range_error():

        @dcs.dataclass_struct()
        class _:
            x: dcs.UnsignedInt = field(**field_kwargs)


@parametrize_field_kwargs(200)
def test_dataclasses_field_no_init(field_kwargs) -> None:
    @dcs.dataclass_struct()
    class T:
        x: int = field()
        y: int = field(init=False, **field_kwargs)

    t = T(100)
    assert t.x == 100
    assert t.y == 200

    with pytest.raises(
        TypeError,
        match=r"takes 2 positional arguments but 3 were given$",
    ):
        T(1, 2)


class DefaultFactoryCallCounter:
    def __init__(self):
        self.call_count = 0

    def __call__(self) -> int:
        self.call_count += 1
        return 1


def test_default_factory_called_once_during_class_creation() -> None:
    factory = DefaultFactoryCallCounter()

    @dcs.dataclass_struct()
    class _:
        x: int = field(default_factory=factory)

    assert factory.call_count == 1


def test_default_factory_not_called_during_class_creation_if_validate_defaults_is_false() -> (  # noqa: E501
    None
):
    factory = DefaultFactoryCallCounter()

    @dcs.dataclass_struct(validate_defaults=False)
    class _:
        x: int = field(default_factory=factory)

    assert factory.call_count == 0
