import subprocess
import sys
from pathlib import Path

import pytest

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


def _cstruct(tmp_path: Path, native: bool) -> Path:
    exe = _compile_cstruct(tmp_path, native)
    outpath = tmp_path / "struct"
    run(str(exe), str(outpath))
    return outpath


@pytest.fixture
def native_cstruct(tmp_path: Path) -> Path:
    return _cstruct(tmp_path, native=True)


@pytest.mark.xfail
def test_unpack_from_cstruct_with_native_size(native_cstruct):
    assert False, "TODO"


@pytest.fixture
def std_cstruct(tmp_path: Path) -> Path:
    return _cstruct(tmp_path, native=False)


@pytest.mark.xfail
def test_unpack_from_cstruct_with_std_size(std_cstruct):
    assert False, "TODO"
