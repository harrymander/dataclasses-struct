import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import pytest

pytestmark = pytest.mark.cc


def run(*args: str) -> None:
    subprocess.run(args, check=True)


if sys.platform.startswith('win'):
    CC = 'cl.exe'

    def build_cc_args(
        dir: Path, exe_path: Path, native: bool
    ) -> Sequence[str]:
        return (
            CC,
            'test\\struct.c',
            f'/Fo:{dir}',
            '/WX',
            f'/{"D" if native else "U"}TEST_NATIVE_INTS',
            '/link', f'/out:{exe_path}',
        )
else:
    CC = 'cc'

    def build_cc_args(
        dir: Path, exe_path: Path, native: bool
    ) -> Sequence[str]:
        return (
            CC,
            '-o', str(exe_path),
            'test/struct.c',
            '-Wall', '-Werror',
            f'-{"D" if native else "U"}TEST_NATIVE_INTS',
        )


def _struct_tester(dir: Path, native: bool) -> Path:
    assert shutil.which(CC), f"Cannot find C compiler '{CC}'"
    exe = dir / 'struct-tester.exe'
    args = build_cc_args(dir, exe, native)
    run(*args)
    return exe


@pytest.fixture
def struct_tester(tmp_path: Path) -> Path:
    return _struct_tester(tmp_path, native=False)


@pytest.fixture
def native_struct_tester(tmp_path: Path) -> Path:
    return _struct_tester(tmp_path, native=True)


@pytest.fixture
def cstruct(tmp_path: Path, struct_tester: Path) -> Path:
    outpath = tmp_path / 'struct'
    run(str(struct_tester), str(outpath))
    return outpath


@pytest.fixture
def native_cstruct(tmp_path: Path, native_struct_tester: Path) -> Path:
    outpath = tmp_path / 'struct'
    run(str(native_struct_tester), str(outpath))
    return outpath


def test_unpack_from_cstruct_with_native_size():
    assert False, "TODO"


def test_unpack_from_cstruct_with_std_size():
    assert False, "TODO"
