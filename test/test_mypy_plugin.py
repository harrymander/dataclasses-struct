import os
import textwrap

import mypy.api


def _add_line_numbers(s: str) -> str:
    lines = s.splitlines()
    width = len(str(len(lines)))
    return "\n".join(
        f"{i + 1:>{width}}| {line}" for i, line in enumerate(lines)
    )


def _format_mypy_output(source: str, stdout: str, stderr: str) -> str:
    indent = "  "
    msg = ["=== source ==="]
    msg.append(_add_line_numbers(source))
    if stdout:
        msg.append("=== mypy stdout ===")
        msg.append(textwrap.indent(stdout, indent))
    if stderr:
        msg.append("=== mypy stderr ===")
        msg.append(textwrap.indent(stderr, indent))
    return "\n".join(msg)


def _run_mypy(source: str) -> tuple[str, str, int]:
    # Disable the cache dir. See:
    # https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-cache-dir
    return mypy.api.run(
        [f"--cache-dir={os.devnull}", "--no-incremental", "--command", source]
    )


def _assert_mypy_passes(source: str) -> None:
    __tracebackhide__ = True
    stdout, stderr, ret = _run_mypy(source)
    if ret == 0:
        return

    error_msg = _format_mypy_output(source, stdout, stderr)
    header = (
        "mypy type checking failed"
        if ret == 1
        else f"mypy internal error (exit code = {ret})"
    )
    raise AssertionError(f"{header}\n{error_msg}")


def assert_mypy_passes(source: str) -> None:
    """
    Assert that mypy passes on the given source code.

    `source` is dedented before passing to mypy.
    """
    __tracebackhide__ = True
    _assert_mypy_passes(textwrap.dedent(source))


def test_is_dataclass() -> None:
    assert_mypy_passes("""\
    from typing import assert_type
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    t = Test(x=1)
    t = Test(1)
    assert_type(t.x, int)
    """)


def test_pack_returns_bytes() -> None:
    assert_mypy_passes("""\
    from typing import assert_type
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    t = Test(2)
    assert_type(t.pack(), bytes)
    """)


def test_dataclass_struct_attribute() -> None:
    assert_mypy_passes("""\
    from typing import assert_type
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    assert_type(Test.__dataclass_struct__.size, int)
    assert_type(Test.__dataclass_struct__.format, str)
    assert_type(Test.__dataclass_struct__.mode, str)
    """)


def test_from_packed_returns_instance() -> None:
    assert_mypy_passes("""\
    from typing import assert_type
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    t = Test.from_packed(Test(1).pack())
    assert_type(t, Test)
    """)


def test_from_packed_supports_bytearray_argument() -> None:
    assert_mypy_passes("""\
    from typing import assert_type
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Test:
        x: int

    t = Test.from_packed(bytearray(Test(1).pack()))
    assert_type(t, Test)
    """)


def test_from_packed_supports_mmap_argument() -> None:
    assert_mypy_passes("""\
    import mmap
    import tempfile
    from pathlib import Path
    from typing import assert_type

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
