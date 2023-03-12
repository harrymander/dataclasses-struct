from typing_extensions import Annotated

from math import pi as PI
import pytest

import dataclasses_struct as dcs


@pytest.mark.parametrize(
    'endian',
    (
        dcs.NATIVE_ENDIAN_ALIGNED,
        dcs.NATIVE_ENDIAN,
        dcs.LITTLE_ENDIAN,
        dcs.BIG_ENDIAN,
        dcs.NETWORK_ENDIAN,
    )
)
def test_pack_unpack(endian: str) -> None:
    @dcs.dataclass(endian)
    class Test:
        a: dcs.Uint8
        b: dcs.Uint16
        c: dcs.Uint32
        d: dcs.Uint64

        e: dcs.Int8
        f: dcs.Int16
        g: dcs.Int32
        h: dcs.Int64

        j: bool
        k: bytes

        m: dcs.Float32
        n: dcs.Float64

        o: Annotated[bytes, 3]

    t = Test(
        a=0xff,
        b=0xffff,
        c=0xffff_ffff,
        d=0xffff_ffff_ffff_ffff,
        e=-0x80,
        f=-0x8000,
        g=-0x8000_0000,
        h=-0x8000_0000_0000_0000,
        j=True,
        k=b'x',
        m=0.25,
        n=PI,
        o=b'123',
    )

    packed = t.pack()
    assert isinstance(packed, bytes)

    unpacked = Test.from_packed(packed)
    assert isinstance(unpacked, Test)

    assert t == unpacked


def test_pack_unpack_native_types() -> None:
    @dcs.dataclass()
    class Test:
        size: dcs.Size
        ssize: dcs.SSize
        pointer: dcs.Pointer

    t = Test(10, -10, 100)
    packed = t.pack()
    unpacked = Test.from_packed(packed)
    assert t == unpacked


@pytest.mark.parametrize(
    'endian',
    (
        dcs.NATIVE_ENDIAN_ALIGNED,
        dcs.NATIVE_ENDIAN,
        dcs.LITTLE_ENDIAN,
        dcs.BIG_ENDIAN,
        dcs.NETWORK_ENDIAN,
    )
)
def test_packed_bytes_padding(endian: str) -> None:
    @dcs.dataclass(endian)
    class Test:
        x: Annotated[bytes, 5]

    t = Test(b'').pack()
    assert t == b'\x00' * 5
    assert Test.from_packed(t) == Test(b'\x00' * 5)

    t = Test(b'123').pack()
    assert t == b'123\x00\x00'
    assert Test.from_packed(t) == Test(b'123\x00\x00')