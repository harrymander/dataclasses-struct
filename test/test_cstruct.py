import subprocess
import sys
from pathlib import Path
from typing import Annotated

import pytest

import dataclasses_struct as dcs

pytestmark = pytest.mark.cc


def run(*args: str) -> None:
    subprocess.run(args, check=True)


if sys.platform.startswith("win"):

    def _compile_cstruct(outdir: Path, native: bool) -> Path:
        exe_path = outdir / "struct-tester.exe"
        run(
            "cl.exe",
            "test\\struct.c",
            f"/Fo:{outdir}",
            "/WX",
            f"/{'D' if native else 'U'}TEST_NATIVE_INTS",
            "/link",
            f"/out:{exe_path}",
        )
        return exe_path

else:

    def _compile_cstruct(outdir: Path, native: bool) -> Path:
        exe_path = outdir / "struct-tester"
        run(
            "cc",
            "-o",
            str(exe_path),
            "test/struct.c",
            "-Wall",
            "-Werror",
            f"-{'D' if native else 'U'}TEST_NATIVE_INTS",
        )
        return exe_path


def _cstruct(tmp_path: Path, native: bool) -> bytes:
    exe = _compile_cstruct(tmp_path, native)
    outpath = tmp_path / "struct"
    run(str(exe), str(outpath))
    with open(outpath, "rb") as f:
        return f.read()


@pytest.fixture
def native_cstruct(tmp_path: Path) -> bytes:
    return _cstruct(tmp_path, native=True)


def test_unpack_from_cstruct_with_native_size(native_cstruct: bytes):
    @dcs.dataclass_struct(size="native")
    class Test:
        test_bool: bool = True
        test_float: dcs.F32 = 1.5
        test_double: float = 2.5
        test_char: bytes = b"!"
        test_char_array: Annotated[bytes, 10] = b"123456789\0"

        test_signed_char: dcs.SignedChar = -10
        test_unsigned_char: dcs.UnsignedChar = 10
        test_signed_short: dcs.Short = -500
        test_unsigned_short: dcs.UnsignedShort = 500
        test_signed_int: int = -5000
        test_unsigned_int: dcs.UnsignedInt = 5000
        test_signed_long: dcs.Long = -6000
        test_unsigned_long: dcs.UnsignedLong = 6000
        test_signed_long_long: dcs.LongLong = -7000
        test_unsigned_long_long: dcs.UnsignedLongLong = 7000
        test_size: dcs.UnsignedSize = 8000
        test_pointer: dcs.Pointer = 0

    @dcs.dataclass_struct(size="native")
    class Container:
        t1: Test
        t2: Test

    c = Container(Test(), Test())
    assert len(c.pack()) == len(native_cstruct)
    assert c == Container.from_packed(native_cstruct)


@pytest.fixture
def std_cstruct(tmp_path: Path) -> bytes:
    return _cstruct(tmp_path, native=False)


def uint_max(n: int) -> int:
    return 2**n - 1


def int_min(n: int) -> int:
    return -(2 ** (n - 1))


def test_unpack_from_cstruct_with_std_size(std_cstruct: bytes):
    @dcs.dataclass_struct(size="std")
    class Test:
        test_bool: bool = True
        test_float: dcs.F32 = 1.5
        test_double: float = 2.5
        test_char: bytes = b"!"
        test_char_array: Annotated[bytes, 10] = b"123456789\0"

        test_uint8: dcs.U8 = uint_max(8)
        test_int8: dcs.I8 = int_min(8)
        test_uint16: dcs.U16 = uint_max(16)
        test_int16: dcs.I16 = int_min(16)
        test_uint32: dcs.U32 = uint_max(32)
        test_int32: dcs.I32 = int_min(32)
        test_uint64: dcs.U64 = uint_max(64)
        test_int64: dcs.I64 = int_min(64)

    @dcs.dataclass_struct(size="std")
    class Container:
        t1: Test
        t2: Test

    c = Container(Test(), Test())
    assert len(c.pack()) == len(std_cstruct)
    assert c == Container.from_packed(std_cstruct)
