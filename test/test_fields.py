from ctypes import c_size_t, c_ssize_t, c_void_p, sizeof
from typing import Annotated

import pytest

import dataclasses_struct as dcs


SSIZE_MIN = -2**(sizeof(c_ssize_t) * 8 - 1)
SSIZE_MAX = -SSIZE_MIN - 1
SIZE_MAX = 2**(sizeof(c_size_t) * 8) - 1
POINTER_MAX = 2**(sizeof(c_void_p) * 8) - 1


def assert_same_format(t1: type, t2: type) -> None:
    assert (
        t1.__dataclass_struct__.format  # type: ignore
        == t2.__dataclass_struct__.format  # type: ignore
    )


def test_native_int_as_int64() -> None:
    @dcs.dataclass()
    class Native:
        x: int

    @dcs.dataclass()
    class Field:
        x: dcs.Int64

    assert_same_format(Native, Field)


def test_native_bool_as_bool() -> None:
    @dcs.dataclass()
    class Native:
        x: bool

    @dcs.dataclass()
    class Field:
        x: dcs.Bool

    assert_same_format(Native, Field)


def test_native_float_as_double() -> None:
    @dcs.dataclass()
    class Native:
        x: float

    @dcs.dataclass()
    class Field:
        x: dcs.Double

    assert_same_format(Native, Field)


def test_native_bytes_as_char() -> None:
    @dcs.dataclass()
    class Native:
        x: bytes

    @dcs.dataclass()
    class Field:
        x: dcs.Char

    assert_same_format(Native, Field)


def test_bytes_annotated_with_int_same_as_field() -> None:
    @dcs.dataclass()
    class Native:
        x: Annotated[bytes, 10]

    @dcs.dataclass()
    class Field:
        x: Annotated[bytes, dcs.BytesField(10)]

    assert_same_format(Native, Field)


def test_invalid_field_type() -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass()
        class _:
            x: str


@pytest.mark.parametrize(
    'endian',
    (
        dcs.NATIVE_ENDIAN,
        dcs.LITTLE_ENDIAN,
        dcs.BIG_ENDIAN,
        dcs.NETWORK_ENDIAN,
    )
)
@pytest.mark.parametrize(
    'native_type',
    (
        dcs.Size,
        dcs.SSize,
        dcs.Pointer,
    )
)
def test_invalid_non_native_size_fields(
    endian: str, native_type: type
) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(endian)
        class _:
            x: native_type  # type: ignore


def test_valid_native_size_fields() -> None:
    @dcs.dataclass(dcs.NATIVE_ENDIAN_ALIGNED)
    class _:
        a: dcs.Size
        b: dcs.SSize
        c: dcs.Pointer


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
def test_valid_non_native_fields(endian: str) -> None:
    @dcs.dataclass(endian)
    class _:
        a: dcs.Char
        b: dcs.Int8
        c: dcs.Uint8
        d: dcs.Bool
        e: dcs.Int16
        f: dcs.Uint16
        g: dcs.Int32
        h: dcs.Uint32
        i: dcs.Int64
        j: dcs.Uint64
        k: dcs.Float32
        l: dcs.Float
        m: dcs.Float64
        n: dcs.Double
        q: Annotated[bytes, dcs.BytesField(10)]


@pytest.mark.parametrize('size', (-1, 0))
def test_invalid_bytes_size(size: int) -> None:
    with pytest.raises(ValueError):
        class _:
            x: Annotated[bytes, dcs.BytesField(size)]


@pytest.mark.parametrize(
    'type_,default',
    (
        (dcs.Size, -1),
        (dcs.Size, SIZE_MAX + 1),
        (dcs.SSize, SSIZE_MIN - 1),
        (dcs.SSize, SSIZE_MAX + 1),

        (dcs.Pointer, -1),
        (dcs.Pointer, POINTER_MAX + 1),

        (dcs.Int8, -0x80 - 1),
        (dcs.Int8, 0x7f + 1),
        (dcs.Uint8, -1),
        (dcs.Uint8, 0xff + 1),

        (dcs.Int16, -0x8000 - 1),
        (dcs.Int16, 0x7fff + 1),
        (dcs.Uint16, -1),
        (dcs.Uint16, 0xffff + 1),

        (dcs.Int32, -0x8000_0000 - 1),
        (dcs.Int32, 0x7fff_ffff + 1),
        (dcs.Uint32, -1),
        (dcs.Uint32, 0xffff_ffff + 1),

        (dcs.Int64, -0x8000_0000_0000_0000 - 1),
        (dcs.Int64, 0x7fff_ffff_ffff_ffff + 1),
        (dcs.Uint64, -1),
        (dcs.Uint64, 0xffff_ffff_ffff_ffff + 1),
    )
)
def test_int_default_out_of_range(type_: type, default: int) -> None:
    with pytest.raises(ValueError):
        @dcs.dataclass()
        class _:
            x: type_ = default  # type: ignore


def test_int_default_range_boundary() -> None:
    @dcs.dataclass()
    class _:
        a: dcs.Size = 0
        b: dcs.Size = SIZE_MAX
        c: dcs.SSize = SSIZE_MIN
        d: dcs.SSize = SSIZE_MAX

        e: dcs.Pointer = 0
        f: dcs.Pointer = POINTER_MAX

        g: dcs.Int8 = -0x80
        h: dcs.Int8 = 0x7f
        i: dcs.Uint8 = 0
        j: dcs.Uint8 = 0xff

        k: dcs.Int16 = -0x8000
        l: dcs.Int16 = 0x7fff
        m: dcs.Uint16 = 0
        n: dcs.Uint16 = 0xffff

        o: dcs.Int32 = -0x8000_0000
        p: dcs.Int32 = 0x7fff_ffff
        q: dcs.Uint32 = 0
        r: dcs.Uint32 = 0xffff_ffff

        s: dcs.Int64 = -0x8000_0000_0000_0000
        t: dcs.Int64 = 0x7fff_ffff_ffff_ffff
        u: dcs.Uint64 = 0
        v: dcs.Uint64 = 0xffff_ffff_ffff_ffff

        w: int = -0x8000_0000_0000_0000
        x: int = 0x7fff_ffff_ffff_ffff


@pytest.mark.parametrize(
    'int_type',
    (
        dcs.Size,
        dcs.SSize,
        dcs.Pointer,
        dcs.Uint8,
        dcs.Uint16,
        dcs.Uint32,
        dcs.Uint64,
        dcs.Int8,
        dcs.Int16,
        dcs.Int32,
        dcs.Int64,
    )
)
@pytest.mark.parametrize(
    'default',
    (
        'wrong',
        1.5,
        '1',
    )
)
def test_int_default_wrong_type(int_type: type, default) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass()
        class _:
            x: int_type = default  # type: ignore


@pytest.mark.parametrize(
    'type_',
    (dcs.Char, Annotated[bytes, dcs.BytesField(1)])
)
def test_bytes_default_wrong_type(type_: type) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass()
        class _:
            x: type_ = 's'  # type: ignore


@pytest.mark.parametrize('c', (b'', b'ab'))
def test_char_default_wrong_length(c: bytes) -> None:
    with pytest.raises(ValueError):
        @dcs.dataclass()
        class _:
            x: dcs.Char = c


def test_default_fixed_length_bytes_wrong_length() -> None:
    with pytest.raises(ValueError):
        @dcs.dataclass()
        class _:
            x: Annotated[bytes, dcs.BytesField(8)] = b'123456789'


@pytest.mark.parametrize('float_type', (dcs.Float32, dcs.Float64))
@pytest.mark.parametrize('default', ('wrong', 1, '1.5'))
def test_float_default_wrong_type(float_type: type, default) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass()
        class _:
            x: float_type = default  # type: ignore


@pytest.mark.parametrize('default', ('wrong', 1, '1.5', None, 'False'))
def test_bool_default_wrong_type(default) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass()
        class _:
            x: bool = default


def test_unvalidated() -> None:
    @dcs.dataclass(validate=False)
    class _:
        a: dcs.Size = -1
        b: dcs.Size = SIZE_MAX + 1
        c: dcs.SSize = SSIZE_MIN - 1
        d: dcs.SSize = SSIZE_MAX + 1

        e: dcs.Pointer = -1
        f: dcs.Pointer = POINTER_MAX

        g: dcs.Int8 = -0x80 - 1
        h: dcs.Int8 = 0x7f + 1
        i: dcs.Uint8 = -1
        j: dcs.Uint8 = 0xff + 1

        k: dcs.Int16 = -0x8000 - 1
        l: dcs.Int16 = 0x7fff + 1
        m: dcs.Uint16 = -1
        n: dcs.Uint16 = 0xffff + 1

        o: dcs.Int32 = -0x8000_0000 - 1
        p: dcs.Int32 = 0x7fff_ffff + 1
        q: dcs.Uint32 = -1
        r: dcs.Uint32 = 0xffff_ffff + 1

        s: dcs.Int64 = -0x8000_0000_0000_0000 - 1
        t: dcs.Int64 = 0x7fff_ffff_ffff_ffff + 1
        u: dcs.Uint64 = -1
        v: dcs.Uint64 = 0xffff_ffff_ffff_ffff + 1

        w: int = -0x8000_0000_0000_0000 - 1
        x: int = 0x7fff_ffff_ffff_ffff + 1

        y: int = 'wrong'  # type: ignore
        z: float = 1
        aa: bytes = 'a'  # type: ignore
        ab: bool = 'False'  # type: ignore

        ac: dcs.Char = 'a'  # type: ignore
        ad: dcs.Char = b''
        ae: dcs.Char = b'aa'

        af: Annotated[bytes, 3] = b'1234'
