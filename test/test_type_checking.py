import os
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

import mypy.api
import pytest


def _add_line_numbers(s: str) -> str:
    lines = s.splitlines()
    width = len(str(len(lines)))
    return "\n".join(
        f"{i + 1:>{width}}| {line}" for i, line in enumerate(lines)
    )


def _format_output(
    type_checker_name: str,
    source: str,
    stdout: str,
    stderr: str,
) -> str:
    indent = "  "
    msg = ["=== source ==="]
    msg.append(_add_line_numbers(source))
    if stdout:
        msg.append(f"=== {type_checker_name} stdout ===")
        msg.append(textwrap.indent(stdout, indent))
    if stderr:
        msg.append(f"=== {type_checker_name} stderr ===")
        msg.append(textwrap.indent(stderr, indent))
    return "\n".join(msg)


class TypeCheckRunner:
    def run(self, source: str) -> tuple[str, str, int]:
        """Run type checker on source, return (stdout, stderr, exit code)."""
        raise NotImplementedError("run must be defined in subclass")

    def pre_check(self) -> None:
        """Additional checks to run before type checking (e.g. checking if
        executable exists)."""
        pass


class _MypyRunner(TypeCheckRunner):
    def run(self, source: str) -> tuple[str, str, int]:
        # Disable the cache dir. See:
        # https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-cache-dir
        return mypy.api.run(
            [
                f"--cache-dir={os.devnull}",
                "--no-incremental",
                "--command",
                source,
            ]
        )


class _TyRunner(TypeCheckRunner):
    TY = "ty"

    def pre_check(self) -> None:
        assert shutil.which(self.TY), f"{self.TY} not found"

    def run(self, source: str) -> tuple[str, str, int]:
        # ty defaults to minimum Python version in pyproject.toml
        # requires-python. Explicitly set Python version to the version of the
        # current interpreter to ensure that ty doesn't fail when importing
        # typing.assert_type on >=3.11
        ty_python_version = ".".join(map(str, sys.version_info[:2]))
        with TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "source.py"
            path.write_text(source)
            r = subprocess.run(
                [
                    self.TY,
                    "check",
                    "--output-format=concise",
                    f"--python-version={ty_python_version}",
                    "--",
                    path,
                ],
                capture_output=True,
                text=True,
            )

        return r.stdout, r.stderr, r.returncode


def _assert_type_check_passes(
    source: str,
    runner: TypeCheckRunner,
    type_checker_name: str,
) -> None:
    """
    Assert that source passes on the given source code with checker.

    typing.assert_type is automatically imported.

    `source` is dedented before passing to type checker.
    """
    __tracebackhide__ = True
    source = textwrap.dedent(source)

    assert_type_module = (
        "typing_extensions" if sys.version_info < (3, 11) else "typing"
    )
    source = "\n".join(
        (f"from {assert_type_module} import assert_type", source)
    )

    stdout, stderr, ret = runner.run(source)
    if ret == 0:
        if stderr:
            msg = f"type checker passed, but got data on stderr:\n{stderr}"
            raise AssertionError(msg)
        return

    output = _format_output(type_checker_name, source, stdout, stderr)
    msg = f"{type_checker_name} type checking failed\n{output}"
    raise AssertionError(msg)


TypeCheckAsserter = Callable[[str], None]


_TYPE_CHECKERS: dict[str, TypeCheckRunner] = {
    "mypy": _MypyRunner(),
    "ty": _TyRunner(),
}


@pytest.fixture(params=_TYPE_CHECKERS.keys())
def type_checker(request: pytest.FixtureRequest) -> TypeCheckAsserter:
    type_checker_name = request.param
    assert isinstance(type_checker_name, str)
    runner = _TYPE_CHECKERS[type_checker_name]
    runner.pre_check()

    if type_checker_name == "ty":
        pytest.xfail(f"{type_checker_name} not supported")

    def _checker(source: str) -> None:
        _assert_type_check_passes(source, runner, type_checker_name)

    return _checker


def test_is_dataclass(type_checker: TypeCheckAsserter):
    type_checker("""\
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    t = Test(x=1)
    t = Test(1)
    assert_type(t.x, int)
    """)


def test_pack_returns_bytes(type_checker: TypeCheckAsserter):
    type_checker("""\
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    t = Test(2)
    assert_type(t.pack(), bytes)
    """)


def test_dataclass_struct_attribute(type_checker: TypeCheckAsserter):
    type_checker("""\
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    assert_type(Test.__dataclass_struct__.size, int)
    assert_type(Test.__dataclass_struct__.format, str)
    assert_type(Test.__dataclass_struct__.mode, str)
    """)


def test_from_packed_returns_instance(type_checker: TypeCheckAsserter):
    type_checker("""\
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    t = Test.from_packed(Test(1).pack())
    assert_type(t, Test)
    """)


def test_from_packed_supports_bytearray_argument(
    type_checker: TypeCheckAsserter,
):
    type_checker("""\
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    t = Test.from_packed(bytearray(Test(1).pack()))
    assert_type(t, Test)
    """)


def test_from_packed_supports_mmap_argument(type_checker: TypeCheckAsserter):
    type_checker("""\
    import mmap
    import tempfile
    from pathlib import Path

    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    packed = Test(1).pack()
    with tempfile.TemporaryDirectory() as tempdir:
        path = Path(tempdir) / "data"
        path.write_bytes(packed)
        with path.open("rb+") as f, mmap.mmap(f.fileno(), 0) as mapped:
          t = Test.from_packed(mapped)

    assert_type(t, Test)
    """)
