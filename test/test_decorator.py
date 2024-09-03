import dataclasses

import pytest
from conftest import parametrize_all_sizes_and_endians

import dataclasses_struct as dcs


def test_no_parens_fails():
    with pytest.raises(TypeError):
        @dcs.dataclass
        class _:  # type: ignore
            pass


@pytest.mark.parametrize(
    'kwargs',
    (
        # Invalid endian with explicit arg size='native'
        {'size': 'native', 'endian': 'big'},
        {'size': 'native', 'endian': 'little'},
        {'size': 'native', 'endian': 'network'},

        # Invalid endian with default arg size='native'
        {'endian': 'big'},
        {'endian': 'little'},
        {'endian': 'network'},

        # Invalid parameters
        {'endian': 'invalid_endian'},
        {'size': 'invalid_size'},
        {'size': 'std', 'endian': 'invalid_endian'},
    )
)
def test_invalid_decorator_args(kwargs):
    with pytest.raises(TypeError):
        @dcs.dataclass(**kwargs)
        class _:
            pass


@parametrize_all_sizes_and_endians()
def test_valid_sizes_and_endians(size, endian) -> None:
    @dcs.dataclass(size=size, endian=endian)
    class Test:
        pass

    assert Test.__dataclass_struct__.size == size
    assert Test.__dataclass_struct__.endianness == endian


def test_class_is_dataclass_struct() -> None:
    @dcs.dataclass()
    class Test:
        pass

    assert dcs.is_dataclass_struct(Test)


def test_object_is_dataclass_struct() -> None:
    @dcs.dataclass()
    class Test:
        pass

    assert dcs.is_dataclass_struct(Test())


def test_object_is_dataclass() -> None:
    @dcs.dataclass()
    class Test:
        pass

    assert dataclasses.is_dataclass(Test())


def test_class_is_dataclass() -> None:
    @dcs.dataclass()
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
