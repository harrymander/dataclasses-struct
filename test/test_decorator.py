import dataclasses
from re import escape

import pytest

import dataclasses_struct as dcs


@pytest.mark.parametrize('endian', dcs.ENDIANS)
def test_valid_endians(endian: str) -> None:
    @dcs.dataclass(endian)
    class Test:
        pass

    assert Test.__dataclass_struct__.endianness == endian


def test_default_endian_is_native_aligned() -> None:
    @dcs.dataclass()
    class Test:
        pass

    assert Test.__dataclass_struct__.endianness == dcs.NATIVE_ENDIAN_ALIGNED


def test_invalid_endian() -> None:
    with pytest.raises(ValueError, match=escape('invalid endianness: ?')):
        @dcs.dataclass('?')
        class Test:
            pass


def test_missing_parens() -> None:
    with pytest.raises(ValueError, match=escape('invalid endianness')):
        @dcs.dataclass  # type: ignore
        class Test:
            pass


def test_is_dataclass_struct() -> None:
    @dcs.dataclass()
    class Test:
        pass

    assert dataclasses.is_dataclass(Test)
    assert dataclasses.is_dataclass(Test())
    assert dcs.is_dataclass_struct(Test)
    assert dcs.is_dataclass_struct(Test())


def test_undecorated_is_not_dataclass_struct() -> None:
    class Test:
        pass

    assert not dataclasses.is_dataclass(Test)
    assert not dataclasses.is_dataclass(Test())
    assert not dcs.is_dataclass_struct(Test)
    assert not dcs.is_dataclass_struct(Test())


def test_stdlib_dataclass_is_not_dataclass_struct() -> None:
    @dataclasses.dataclass
    class Test:
        pass

    assert dataclasses.is_dataclass(Test)
    assert dataclasses.is_dataclass(Test())
    assert not dcs.is_dataclass_struct(Test)
    assert not dcs.is_dataclass_struct(Test())
