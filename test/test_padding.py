import pytest
from conftest import parametrize_all_sizes_and_byteorders

import dataclasses_struct as dcs
from dataclasses_struct import Annotated


@pytest.mark.parametrize('size', (-1,))
@pytest.mark.parametrize('padding', (dcs.PadBefore, dcs.PadAfter))
def test_invalid_padding_size(size: int, padding: type) -> None:
    with pytest.raises(ValueError, match=r'^size must be non-negative$'):
        @dcs.dataclass()
        class _:
            x: Annotated[int, padding(size)]


def assert_true_has_correct_padding(
    packed: bytes, before: int, after: int
) -> None:
    assert packed == (before * b'\x00') + b'\x01' + (after * b'\x00')


@pytest.mark.parametrize('padding', (dcs.PadBefore, dcs.PadAfter))
@parametrize_all_sizes_and_byteorders()
def test_padding_zero(size, byteorder, padding: type) -> None:
    @dcs.dataclass(size=size, byteorder=byteorder)
    class T:
        x: Annotated[bool, padding(0)]

    assert T(True).pack() == b'\x01'


@parametrize_all_sizes_and_byteorders()
def test_padding_before(size, byteorder) -> None:
    @dcs.dataclass(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadBefore(5)]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 5, 0)


@parametrize_all_sizes_and_byteorders()
def test_padding_after(size, byteorder) -> None:
    @dcs.dataclass(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadAfter(5)]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 0, 5)


@parametrize_all_sizes_and_byteorders()
def test_padding_before_and_after(size, byteorder) -> None:
    @dcs.dataclass(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadBefore(10), dcs.PadAfter(5)]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 10, 5)


@parametrize_all_sizes_and_byteorders()
def test_padding_before_and_after_with_after_before_before(
    size, byteorder
) -> None:
    @dcs.dataclass(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadAfter(5), dcs.PadBefore(10)]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 10, 5)


@parametrize_all_sizes_and_byteorders()
def test_padding_multiple(size, byteorder) -> None:
    @dcs.dataclass(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[
            bool,
            dcs.PadBefore(4),
            dcs.PadAfter(5),
            dcs.PadBefore(0),
            dcs.PadAfter(3),
            dcs.PadBefore(10),
        ]

    t = Test(True)
    assert_true_has_correct_padding(t.pack(), 14, 8)


@parametrize_all_sizes_and_byteorders()
def test_padding_with_bytes(size, byteorder) -> None:
    @dcs.dataclass(size=size, byteorder=byteorder)
    class Test:
        a: Annotated[bytes, dcs.PadBefore(2), 4, dcs.PadAfter(3)]

    t = Test(b'1234')
    assert t.pack() == b'\x00\x001234\x00\x00\x00'


@parametrize_all_sizes_and_byteorders()
def test_unpack_padding(size, byteorder) -> None:
    @dcs.dataclass(size=size, byteorder=byteorder)
    class Test:
        x: Annotated[bool, dcs.PadAfter(2)]
        y: Annotated[bool, dcs.PadBefore(2), dcs.PadAfter(7)]

    unpacked = Test.from_packed(
        b'\x00' + (b'\x00' * 4) + b'\x01' + (b'\x00' * 7)
    )
    assert unpacked == Test(False, True)
