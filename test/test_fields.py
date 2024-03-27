import ctypes

import pytest
from typing_extensions import Annotated

import dataclasses_struct as dcs


def assert_same_format(t1, t2) -> None:
    assert t1.__dataclass_struct__.format == t2.__dataclass_struct__.format


native_only_fields: list = [
    dcs.SignedChar,
    dcs.UnsignedChar,
    dcs.Short,
    dcs.UnsignedShort,
    int,
    dcs.Int,
    dcs.UnsignedInt,
    dcs.Long,
    dcs.UnsignedLong,
    dcs.LongLong,
    dcs.UnsignedLongLong,
    dcs.SignedSize,
    dcs.UnsignedSize,
    dcs.Pointer,
]

std_only_fields: list = [
    dcs.U8,
    dcs.U16,
    dcs.U32,
    dcs.U64,
    dcs.I8,
    dcs.I16,
    dcs.I32,
    dcs.I64,
]

common_fields: list = [
    dcs.Char,
    bytes,
    dcs.Bool,
    bool,
    dcs.F32,
    dcs.F64,
    float,
]
std_endians = ('native', 'little', 'big', 'network')


@pytest.mark.parametrize('field_type', native_only_fields + common_fields)
def test_valid_native_size_fields(field_type) -> None:
    @dcs.dataclass(endian='native', size='native')
    class _:
        field: field_type


@pytest.mark.parametrize('field_type', std_only_fields)
def test_invalid_native_size_fields(field_type) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(endian='native', size='native')
        class _:
            field: field_type


@pytest.mark.parametrize('field_type', std_only_fields + common_fields)
@pytest.mark.parametrize('endian', std_endians)
def test_valid_std_size_fields(endian, field_type) -> None:
    @dcs.dataclass(endian=endian, size='std')
    class _:
        field: field_type


@pytest.mark.parametrize('field_type', native_only_fields)
@pytest.mark.parametrize('endian', ('native', 'little', 'big', 'network'))
def test_invalid_std_size_fields(endian, field_type) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(endian=endian, size='std')
        class _:
            field: field_type


def test_builtin_int_is_int() -> None:
    @dcs.dataclass(endian='native', size='native')
    class Builtin:
        x: int

    @dcs.dataclass(endian='native', size='native')
    class Field:
        x: dcs.Int

    assert_same_format(Builtin, Field)


def parametrize_endian_size(f):
    return pytest.mark.parametrize(
        'endian,size',
        [
            ('native', 'native'),
            *((endian, 'std') for endian in std_endians)
        ]
    )(f)


@parametrize_endian_size
def test_builtin_bool_is_bool(endian, size) -> None:
    @dcs.dataclass(endian=endian, size=size)
    class Builtin:
        x: bool

    @dcs.dataclass(endian=endian, size=size)
    class Field:
        x: dcs.Bool

    assert_same_format(Builtin, Field)


@parametrize_endian_size
def test_builtin_float_is_f64(endian, size) -> None:
    @dcs.dataclass(endian=endian, size=size)
    class Builtin:
        x: float

    @dcs.dataclass(endian=endian, size=size)
    class Field:
        x: dcs.F64

    assert_same_format(Builtin, Field)


@parametrize_endian_size
def test_builtin_bytes_is_char(endian, size) -> None:
    @dcs.dataclass(endian=endian, size=size)
    class Builtin:
        x: bytes

    @dcs.dataclass(endian=endian, size=size)
    class Field:
        x: dcs.Char

    assert_same_format(Builtin, Field)


@parametrize_endian_size
def test_bytes_annotated_with_int_same_as_bytes_field(endian, size) -> None:
    @dcs.dataclass(endian=endian, size=size)
    class Builtin:
        x: Annotated[bytes, 10]

    @dcs.dataclass(endian=endian, size=size)
    class Field:
        x: Annotated[bytes, dcs.BytesField(10)]

    assert_same_format(Builtin, Field)


@parametrize_endian_size
def test_invalid_field_type(endian, size) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(endian=endian, size=size)
        class _:
            x: str


@pytest.mark.parametrize('size', (-1, 0))
def test_invalid_bytes_size(size: int) -> None:
    with pytest.raises(ValueError):
        class _:
            x: Annotated[bytes, dcs.BytesField(size)]


def int_min_max(nbits: int, signed: bool) -> tuple[int, int]:
    if signed:
        exp = 2**(nbits-1)
        return -exp, exp - 1
    else:
        return 0, 2**nbits - 1


std_int_out_of_range_vals = []
std_int_boundary_vals = []
for field_type, nbits, signed in (
    (dcs.I8, 8, True),
    (dcs.U8, 8, False),
    (dcs.I16, 16, True),
    (dcs.U16, 16, False),
    (dcs.I32, 32, True),
    (dcs.U32, 32, False),
    (dcs.I64, 64, True),
    (dcs.U64, 64, False),
):
    min_, max_ = int_min_max(nbits, signed)
    std_int_out_of_range_vals.append((field_type, min_ - 1))
    std_int_out_of_range_vals.append((field_type, max_ + 1))
    std_int_boundary_vals.append((field_type, min_))
    std_int_boundary_vals.append((field_type, max_))


@pytest.mark.parametrize('field_type,default', std_int_boundary_vals)
@pytest.mark.parametrize('endian', std_endians)
def test_std_int_default(field_type, default, endian) -> None:
    @dcs.dataclass(size='std', endian=endian)
    class Class:
        field: field_type = default

    assert Class().field == default


@pytest.mark.parametrize('field_type,default', std_int_out_of_range_vals)
@pytest.mark.parametrize('endian', std_endians)
def test_std_int_default_out_of_range(field_type, default, endian) -> None:
    with pytest.raises(ValueError):
        @dcs.dataclass(size='std', endian=endian)
        class _:
            x: field_type = default


@pytest.mark.parametrize('field_type,default', std_int_out_of_range_vals)
@pytest.mark.parametrize('endian', std_endians)
def test_std_int_unvalidated(field_type, default, endian) -> None:
    @dcs.dataclass(size='std', endian=endian, validate=False)
    class Class:
        x: field_type = default

    assert Class().x == default


native_int_out_of_range_vals = []
native_int_boundary_vals = []
for field_type, ctype_type, signed in (
    (dcs.SignedChar, ctypes.c_byte, True),
    (dcs.UnsignedChar, ctypes.c_ubyte, False),
    (dcs.Short, ctypes.c_short, True),
    (dcs.UnsignedShort, ctypes.c_ushort, False),
    (int, ctypes.c_int, True),
    (dcs.Int, ctypes.c_int, True),
    (dcs.UnsignedInt, ctypes.c_uint, False),
    (dcs.Long, ctypes.c_long, True),
    (dcs.UnsignedLong, ctypes.c_ulong, False),
    (dcs.LongLong, ctypes.c_longlong, True),
    (dcs.UnsignedLongLong, ctypes.c_ulonglong, False),
    (dcs.SignedSize, ctypes.c_ssize_t, True),
    (dcs.UnsignedSize, ctypes.c_size_t, False),
    (dcs.Pointer, ctypes.c_void_p, False),
):
    min_, max_ = int_min_max(ctypes.sizeof(ctype_type) * 8, signed)
    native_int_out_of_range_vals.append((field_type, min_ - 1))
    native_int_out_of_range_vals.append((field_type, max_ + 1))
    native_int_boundary_vals.append((field_type, min_))
    native_int_boundary_vals.append((field_type, max_))


@pytest.mark.parametrize('field_type,default', native_int_boundary_vals)
def test_native_int_default(field_type, default) -> None:
    @dcs.dataclass(size='native', endian='native')
    class Class:
        field: field_type = default

    assert Class().field == default


@pytest.mark.parametrize('field_type,default', native_int_out_of_range_vals)
def test_native_int_default_out_of_range(field_type, default) -> None:
    with pytest.raises(ValueError):
        @dcs.dataclass(size='native', endian='native')
        class _:
            x: field_type = default


@pytest.mark.parametrize('field_type,default', native_int_out_of_range_vals)
def test_native_int_unvalidated(field_type, default) -> None:
    @dcs.dataclass(size='native', endian='native', validate=False)
    class Class:
        x: field_type = default

    assert Class().x == default


def parametrize_invalid_int_defaults(f):
    return pytest.mark.parametrize(
        'default',
        (
            'wrong',
            1.5,
            '1',
        )
    )(f)


@pytest.mark.parametrize('int_type', std_only_fields)
@pytest.mark.parametrize('endian', std_endians)
@parametrize_invalid_int_defaults
def test_std_int_default_wrong_type(
    int_type, endian, default
) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(size='std', endian=endian)
        class _:
            x: int_type = default


@pytest.mark.parametrize('int_type', native_only_fields)
@parametrize_invalid_int_defaults
def test_native_int_default_wrong_type(int_type, default) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(size='std', endian='native')
        class _:
            x: int_type = default


@parametrize_endian_size
@pytest.mark.parametrize(
    'field_type',
    (dcs.Char, Annotated[bytes, dcs.BytesField(1)])
)
def test_bytes_default_wrong_type(endian, size, field_type) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(endian=endian, size=size)
        class _:
            x: field_type = 's'


@parametrize_endian_size
@pytest.mark.parametrize('c', (b'', b'ab'))
def test_char_default_wrong_length(endian, size, c: bytes) -> None:
    with pytest.raises(ValueError):
        @dcs.dataclass(endian=endian, size=size)
        class _:
            x: dcs.Char = c


@parametrize_endian_size
def test_default_fixed_length_bytes_wrong_length(endian, size) -> None:
    with pytest.raises(ValueError):
        @dcs.dataclass(endian=endian, size=size)
        class _:
            x: Annotated[bytes, dcs.BytesField(8)] = b'123456789'


@parametrize_endian_size
@pytest.mark.parametrize('float_type', (dcs.F32, dcs.F64))
@pytest.mark.parametrize('default', ('wrong', 1, '1.5'))
def test_float_default_wrong_type(
    endian, size, float_type: type, default
) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(endian=endian, size=size)
        class _:
            x: float_type = default  # type: ignore


@parametrize_endian_size
@pytest.mark.parametrize('default', ('wrong', 1, '1.5', None, 'False'))
def test_bool_default_wrong_type(endian, size, default) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(endian=endian, size=size)
        class _:
            x: bool = default


@parametrize_endian_size
def test_annotated_invalid(endian, size) -> None:
    with pytest.raises(TypeError):
        @dcs.dataclass(endian=endian, size=size)
        class _:
            x: Annotated[int, dcs.I64]


@parametrize_endian_size
def test_invalid_bytes_annotated(endian, size) -> None:
    with pytest.raises(TypeError, match=r'^too many annotations: 12$'):
        @dcs.dataclass(endian=endian, size=size)
        class _:
            x: Annotated[bytes, 1, 12]
