import pytest
from typing_extensions import Annotated

import dataclasses_struct as dcs


@pytest.mark.parametrize('size', (-1,))
@pytest.mark.parametrize('padding', (dcs.PadBefore, dcs.PadAfter))
def test_invalid_padding_size(size: int, padding: type) -> None:
    with pytest.raises(ValueError, match=r'^size must be non-negative$'):
        @dcs.dataclass()
        class _:
            x: Annotated[int, padding(size)]


@pytest.mark.parametrize('padding', (dcs.PadBefore, dcs.PadAfter))
def test_padding_zero(padding: type) -> None:
    @dcs.dataclass(dcs.BIG_ENDIAN)
    class T:
        x: Annotated[int, padding(0)]

    assert T(0x45).pack() == b'\x00' * 7 + b'\x45'


def test_padding_before() -> None:
    @dcs.dataclass(dcs.LITTLE_ENDIAN)
    class Test:
        x: Annotated[dcs.U8, dcs.PadBefore(5)]

    t = Test(12)
    assert t.pack() == b'\x00' * 5 + b'\x0c'


def test_padding_after() -> None:
    @dcs.dataclass(dcs.LITTLE_ENDIAN)
    class Test:
        x: Annotated[dcs.U8, dcs.PadAfter(5)]

    t = Test(12)
    assert t.pack() == b'\x0c' + b'\x00' * 5


def test_padding_before_and_after() -> None:
    @dcs.dataclass(dcs.LITTLE_ENDIAN)
    class Test:
        x: Annotated[dcs.U8, dcs.PadAfter(5), dcs.PadBefore(3)]

    t = Test(12)
    assert t.pack() == b'\x00' * 3 + b'\x0c' + b'\x00' * 5


def test_padding_multiple() -> None:
    @dcs.dataclass(dcs.LITTLE_ENDIAN)
    class Test:
        x: Annotated[dcs.U8, dcs.PadAfter(5), dcs.PadAfter(3)]

    t = Test(12)
    assert t.pack() == b'\x0c' + b'\x00' * 8


def test_padding_with_bytes() -> None:
    @dcs.dataclass(dcs.LITTLE_ENDIAN)
    class Test:
        a: Annotated[bytes, dcs.PadBefore(2), 4, dcs.PadAfter(3)]

    t = Test(b'1234')
    assert t.pack() == b'\x00\x001234\x00\x00\x00'


def test_padding_with_builtin() -> None:
    @dcs.dataclass(dcs.LITTLE_ENDIAN)
    class Test:
        a: Annotated[int, dcs.PadBefore(2)]

    t = Test(0xff)
    assert t.pack() == b'\x00\x00' + b'\xff' + b'\x00' * 7


def test_unpack_padding() -> None:
    @dcs.dataclass(dcs.LITTLE_ENDIAN)
    class Test:
        x: Annotated[dcs.U8, dcs.PadAfter(2)]
        y: Annotated[dcs.U8, dcs.PadBefore(2), dcs.PadAfter(7)]

    unpacked = Test.from_packed(b'\x12' + b'\x00' * 4 + b'\x07' + b'\x00' * 7)
    assert unpacked == Test(0x12, 0x07)
