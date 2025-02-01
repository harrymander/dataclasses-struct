# dataclasses-struct

[![PyPI version](https://img.shields.io/pypi/v/dataclasses-struct)](https://pypi.org/project/dataclasses-struct/)
[![Python versions](https://img.shields.io/pypi/pyversions/dataclasses-struct)](https://pypi.org/project/dataclasses-struct/)
[![Tests status](https://github.com/harrymander/dataclasses-struct/actions/workflows/test.yml/badge.svg?event=push)]()
[![Code coverage](https://img.shields.io/codecov/c/gh/harrymander/dataclasses-struct)](https://app.codecov.io/gh/harrymander/dataclasses-struct)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/harrymander/dataclasses-struct/blob/main/LICENSE)

A simple Python package that combines
[`dataclasses`](https://docs.python.org/3/library/dataclasses.html) with
[`struct`](https://docs.python.org/3/library/struct.html) for packing and
unpacking Python dataclasses to fixed-length `bytes` representations.

```python
from typing import Annotated  # use typing_extensions on Python <3.9, or import
                              # from dataclasses_struct
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

## Usage

Use the `dataclass_struct` decorator to convert a class into a [stdlib
`dataclass`](https://docs.python.org/3/library/dataclasses.html) with struct
packing/unpacking functionality:

```python
def dataclass_struct(
    *,
    size: str = 'native',
    byteorder: str = 'native',
    validate_defaults: bool = True,
):
    ...
```

The `size` argument can be either `'native'` (the default) or `'std'`:

Decorated classes are transformed to a standard Python
[dataclass](https://docs.python.org/3/library/dataclasses.html) with boilerplate
`__init__`, `__repr__`, `__eq__` etc. auto-generated. Additionally, two methods
are added to the class: `pack`, a method for packing an instance of the class to
`bytes`, and `from_packed`, a class method that returns a new instance of the
class from its packed `bytes` representation.

A class or object can be check to see if it is a dataclass-struct using the
`is_dataclass_struct` function. The `get_struct_size` function will return
the size in bytes of the packed representation of a dataclass_struct class
or an instance of one.

An additional class attribute, `__dataclass_struct__`. The [`struct` format
string](https://docs.python.org/3/library/struct.html#format-strings), packed
size, and mode character can be accessed like so:

```python
>>> Test.__dataclass_struct__.format
'@cc??bBhHiIQqqNnPfdd100s4xqq2x3xq2x'
>>> Test.__dataclass_struct__.size
234
>>> Test.__dataclass_struct__.mode
'@'
```

Default attribute values will be validated against their expected type and
allowable value range. For example,

```python3
import dataclasses_struct as dcs

@dcs.dataclass_struct()
class Test:
    x: dcs.U8 = -1
```

will raise a `ValueError`. This can be disabled by passing
`validate_defaults=False` to the `dataclasses_struct.dataclass_struct`
decorator.

### Native size mode

In `native` mode, the struct is packed based on the platform and compiler on
which Python was built: padding bytes may be added to maintain proper alignment
of the fields and byte ordering (endianness) follows that of the platform. (The
`byteorder` argument must also be `native`.)

In `native` size mode, integer type sizes follow those of the standard C integer
types of the platform (`int`, `unsigned short` etc.).

```python
@dcs.dataclass_struct()  # defaults to size='native', byteorder='native'
class NativeStruct:
    signed_char: dcs.SignedChar
    signed_short: dcs.Short
    unsigned_long_long: dcs.UnsignedLongLong
    void_pointer: dcs.Pointer
```

### Standard size mode

In `std` mode, the struct is packed without any additional padding for
alignment.

The `std` size mode supports four different byte order settings: `'native'`,
`'little'`, `'big'`, and `'network'`. The `'native'` setting uses the system
byte order (similar to `native` size mode, but without alignment). The
`'network'` setting is equivalent to `'big'`.

The `std` size uses platform-independent integer sizes, similar to using the
integer types from `stdint.h` in C. When used with any of the non-`native` byte
orders, it is appropriate for marshalling data across different platforms, which
may have different alignment, byte ordering, and integer type sizes.

```python
@dcs.dataclass_struct()  # defaults to size='native', byteorder='native'
class NativeStruct:
    int8_t: dcs.I8
    uint64_t: dcs.U64
```

### Supported type annotations

#### Native integer types

These types are only supported in `native` size mode. Their native Python types
are all `int`.

| Type annotation                      | Equivalent C type           |
| ------------------------------------ | --------------------------- |
| `SignedChar`                         | `signed char`               |
| `UnsignedChar`                       | `unsigned char`             |
| `Short`                              | `short`                     |
| `UnsignedShort`                      | `unsigned short`            |
| `Int`                                | `int`                       |
| `int` (builtin type, alias to `Int`) | `int`                       |
| `UnsignedInt`                        | `unsigned int`              |
| `Long`                               | `long`                      |
| `UnsignedLong`                       | `unsigned long`             |
| `LongLong`                           | `long long`                 |
| `UnsignedLongLong`                   | `unsigned long long`        |
| `UnsignedSize`                       | `size_t`                    |
| `SignedSize`                         | `ssize_t` (POSIX extension) |
| `Pointer`                            | `void *`                    |

#### Standard integer types

These types are only supported in `std` size mode. Their native Python types are
all `int`.

| Type annotation                      | Equivalent C type           |
| ------------------------------------ | --------------------------- |
| `I8`                                 | `int8_t`                    |
| `U8`                                 | `uint8_t`                   |
| `I16`                                | `int16_t`                   |
| `U16`                                | `uint16_t`                  |
| `I32`                                | `int32_t`                   |
| `U32`                                | `uint32_t`                  |
| `I64`                                | `int64_t`                   |
| `U64`                                | `uint64_t`                  |

#### Floating point types

Supported in both size modes. The native Python type is `float`.

| Type annotation                      | Equivalent C type           |
| ------------------------------------ | --------------------------- |
| `F32`                                | `float`                     |
| `F64`                                | `double`                    |
| `float` (builtin alias to `F64`)     | `double`                    |

#### Boolean

The builtin `bool` type or `dataclasses_struct.Bool` type can be used to
represent a boolean, which uses a single byte in either native or standard size
modes.

#### Characters and bytes arrays

In both size modes, a single-byte ASCII character can be packed  by annotating a
field with the builtin `bytes` type or the `dataclasses_struct.Char` type. The
field's unpacked Python representation will be a `bytes` of length 1.

```python
@dcs.dataclass_struct()
class Chars:
    char: dcs.Char = b'x'
    builtin: bytes = b'\x04'
```

Fixed-length byte arrays can be represented by annotating a field with
`typing.Annotated` and a positive length. The field's unpacked Python
representation will be a `bytes` object zero-padded or truncated to the
specified length.

```python
from typing import Annotated

@dcs.dataclass_struct()
class FixedLength:
    fixed: Annotated[bytes, 10]
```

```python
>>> FixedLength.from_packed(FixedLength(b'Hello, world!').pack())
FixedLength(fixed=b'Hello, wor')
```

Note that `Annotated` was added in Python 3.9. For earlier versions, import from
`typing_extensions`. Alternatively for convenience, it can be imported from the
`dataclasses_struct` module, which will select the correct library to import
from based on the Python version.

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

Uses `ruff` and `flake8` for linting, which is enforced on pull requests:

```
uv run ruff check
uv run flake8 --exclude .venv
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
