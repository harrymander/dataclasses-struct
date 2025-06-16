# dataclasses-struct

[![PyPI version](https://img.shields.io/pypi/v/dataclasses-struct)](https://pypi.org/project/dataclasses-struct/)
[![Python versions](https://img.shields.io/pypi/pyversions/dataclasses-struct)](https://pypi.org/project/dataclasses-struct/)
[![Tests status](https://github.com/harrymander/dataclasses-struct/actions/workflows/ci.yml/badge.svg?event=push)](https://github.com/harrymander/dataclasses-struct/actions/workflows/ci.yml)
[![Code coverage](https://img.shields.io/codecov/c/gh/harrymander/dataclasses-struct)](https://app.codecov.io/gh/harrymander/dataclasses-struct)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/harrymander/dataclasses-struct/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/Documentation-blue)](https://harrymander.xyz/dataclasses-struct)

A simple Python package that combines
[`dataclasses`](https://docs.python.org/3/library/dataclasses.html) with
[`struct`](https://docs.python.org/3/library/struct.html) for packing and
unpacking Python dataclasses to fixed-length `bytes` representations.

**Documentation**: https://harrymander.xyz/dataclasses-struct

## Example

```python
from typing import Annotated

import dataclasses_struct as dcs

@dcs.dataclass_struct()
class Test:
    x: int
    y: float
    z: dcs.UnsignedShort
    s: Annotated[bytes, 10]  # fixed-length byte array of length 10

@dcs.dataclass_struct()
class Container:
    test1: Test
    test2: Test
```

```python
>>> dcs.is_dataclass_struct(Test)
True
>>> t1 = Test(100, -0.25, 0xff, b'12345')
>>> dcs.is_dataclass_struct(t1)
True
>>> t1
Test(x=100, y=-0.25, z=255, s=b'12345')
>>> packed = t1.pack()
>>> packed
b'd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0\xbf\xff\x0012345\x00\x00\x00\x00\x00'
>>> Test.from_packed(packed)
Test(x=100, y=-0.25, z=255, s=b'12345\x00\x00\x00\x00\x00')
>>> t2 = Test(1, 100, 12, b'hello, world')
>>> c = Container(t1, t2)
>>> Container.from_packed(c.pack())
Container(test1=Test(x=100, y=-0.25, z=255, s=b'12345\x00\x00\x00\x00\x00'), test2=Test(x=1, y=100.0, z=12, s=b'hello, wor'))
```

## Installation

This package is available on pypi:

```
pip install dataclasses-struct
```

To work correctly with [`mypy`](https://www.mypy-lang.org/), an extension is
required; add to your `mypy.ini`:

```ini
[mypy]
plugins = dataclasses_struct.ext.mypy_plugin
```

See [the docs](https://harrymander.xyz/dataclasses-struct/guide/#type-checking)
for more info on type checking.

## Development and contributing

Pull requests are welcomed!

This project uses [uv](https://docs.astral.sh/uv/) for packaging and dependency
management. To install all dependencies (including development dependencies)
into a virtualenv for local development:

```
uv sync
```

Uses `pytest` for testing:

```
uv run pytest
```

(You may omit the `uv run` if the virtualenv is activated.)

Uses `ruff` for linting and formatting, which is enforced on pull requests:

```
uv run ruff format
uv run ruff check
```

See `pyproject.toml` for the list of enabled checks. I recommend installing the
provided [`pre-commmit`](https://pre-commit.com/) hooks to ensure new commits
pass linting:

```
pre-commit install
```

This will help speed-up pull requests by reducing the chance of failing CI
checks.

PRs must also pass `mypy` checks (`uv run mypy`).
