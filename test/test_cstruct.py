from pathlib import Path
import subprocess
import sys
from typing_extensions import Annotated

import pytest

import dataclasses_struct as dcs

pytestmark = pytest.mark.cc


def run(*args: str) -> None:
    subprocess.run(args, check=True)


if sys.platform.startswith('win'):
    def _struct_tester(dir: Path, packed: bool = False) -> Path:
        """
        Compiles struct.c and returns path to executable
        """
        exe_path = dir / 'struct-test.exe'
        args = [
            'cl.exe',
            'test\\struct.c',
            f'/Fo:{dir}',
            '/WX',
        ]
        if packed:
            args.append('/DTEST_PACKED_STRUCT')
        args.extend(('/link', f'/out:{exe_path}'))

        run(*args)
        return exe_path
else:
    def _struct_tester(dir: Path, packed: bool = False) -> Path:
        exe_path = dir / 'struct-test'
        args = [
            'gcc',
            '-o', str(exe_path),
            'test/struct.c',
            '-Wall',
            '-Werror',
        ]
        if packed:
            args.append('-DTEST_PACKED_STRUCT')

        run(*args)
        return exe_path


@pytest.fixture
def struct_tester(tmp_path: Path) -> Path:
    return _struct_tester(tmp_path, packed=False)


@pytest.fixture
def packed_struct_tester(tmp_path: Path) -> Path:
    return _struct_tester(tmp_path, packed=True)


@pytest.fixture
def cstruct(tmp_path: Path, struct_tester: Path) -> Path:
    outpath = tmp_path / 'struct'
    run(str(struct_tester), str(outpath))
    return outpath


@pytest.fixture
def packed_cstruct(tmp_path: Path, packed_struct_tester: Path) -> Path:
    outpath = tmp_path / 'struct'
    run(str(packed_struct_tester), str(outpath))
    return outpath


class StructTest:
    str_test: Annotated[bytes, dcs.BytesField(13)]
    u32_test: dcs.Uint32
    double_test: dcs.Double


def assert_struct(struct_path: Path, packed: bool) -> None:
    Test = dcs.dataclass(
        dcs.NATIVE_ENDIAN if packed else dcs.NATIVE_ENDIAN_ALIGNED
    )(StructTest)
    unpacked = Test.from_packed(struct_path.read_bytes())  # type: ignore
    assert unpacked.u32_test == 5
    assert unpacked.double_test == -0.5
    assert unpacked.str_test.rstrip(b'\x00') == b'Hello!'


def test_cstruct(cstruct: Path) -> None:
    assert_struct(cstruct, False)


def test_packed_cstruct(packed_cstruct: Path) -> None:
    assert_struct(packed_cstruct, True)
