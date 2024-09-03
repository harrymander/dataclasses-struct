import dataclasses

import pytest

import dataclasses_struct as dcs


def test_no_parens_fails():
    with pytest.raises(TypeError):
        @dcs.dataclass
        class _:  # type: ignore
            pass


@pytest.mark.parametrize(
    'kwargs',
    (
        {'size': 'native', 'endian': 'big'},
        {'size': 'native', 'endian': 'little'},
        {'size': 'native', 'endian': 'network'},
        {'endian': 'big'},
        {'endian': 'little'},
        {'endian': 'network'},
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


# TODO
# @pytest.mark.parametrize('endian', dcs.ENDIANS)
# def test_valid_endians(endian: str) -> None:
#     @dcs.dataclass(endian)
#     class Test:
#         pass

#     assert Test.__dataclass_struct__.endianness == endian


# def test_default_endian_is_native_aligned() -> None:
#     @dcs.dataclass()
#     class Test:
#         pass

#     assert Test.__dataclass_struct__.endianness == dcs.NATIVE_ENDIAN_ALIGNED


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
