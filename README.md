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

1. [Example](#example)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Development and contributing](#development-and-contributing)

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

## Usage

1. [Native size mode](#native-size-mode)
2. [Standard size mode](#standard-size-mode)
3. [Supported type annotations](#supported-type-annotations)
   1. [Native integer types](#native-integer-types)
   2. [Standard integer types](#standard-integer-types)
   3. [Floating point types](#floating-point-types)
   4. [Boolean](#boolean)
   5. [Characters and bytes arrays](#characters-and-bytes-arrays)
   6. [Nested structs](#nested-structs)
   7. [Fixed-length arrays](#fixed-length-arrays)
   8. [Manual padding](#manual-padding)

Use the `dataclass_struct` decorator to convert a class into a [stdlib
`dataclass`](https://docs.python.org/3/library/dataclasses.html) with struct
packing/unpacking functionality:

```python
def dataclass_struct(
    *,
    size: Literal["native", "std"] = "native",
    byteorder: Literal["native", "big", "little", "network"] = "native",
    validate_defaults: bool = True,
    **dataclass_kwargs,
):
    ...
```

The `size` argument can be either `"native"` (the default) or `"std"` and
controls the size and alignment of fields. See below for more details on the
different `size` and `byteorder` argument values.

Decorated classes are transformed to a standard Python
[dataclass](https://docs.python.org/3/library/dataclasses.html) with boilerplate
`__init__`, `__repr__`, `__eq__` etc. auto-generated. Additionally, two methods
are added to the class: `pack`, a method for packing an instance of the class to
`bytes`, and `from_packed`, a class method that returns a new instance of the
class from its packed `bytes` representation. The additional `dataclass_kwargs`
keyword arguments will be passed through to the [stdlib `dataclass`
decorator](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass):
all standard keyword arguments are supported except for `slots` and
`weakref_slot`.

Default attribute values will be validated against their expected type and
allowable value range. For example,

```python
import dataclasses_struct as dcs

@dcs.dataclass_struct()
class Test:
    x: dcs.UnsignedChar = -1
```

will raise a `ValueError`. This can be disabled by passing
`validate_defaults=False` to the decorator.

A class or object can be checked to see if it is a dataclass-struct using the
`is_dataclass_struct` function.


```python
>>> dcs.is_dataclass_struct(Test)
True
>>> t = Test(100)
>>> dcs.is_dataclass_struct(t)
True
```

The `get_struct_size` function will return the size in bytes of the packed
representation of a dataclass-struct class or an instance of one.

```python
>>> dcs.get_struct_size(Test)
234
```

An additional class attribute, `__dataclass_struct__`, is added to the decorated
class that contains the packed size, [`struct` format
string](https://docs.python.org/3/library/struct.html#format-strings), and
`struct` mode.

```python
>>> Test.__dataclass_struct__.size
234
>>> Test.__dataclass_struct__.format
'@cc??bBhHiIQqqNnPfdd100s4xqq2x3xq2x'
>>> Test.__dataclass_struct__.mode
'@'
```

### Native size mode

In `"native"` mode (the default), the struct is packed based on the platform and
compiler on which Python was built: padding bytes may be added to maintain
proper alignment of the fields and byte ordering (endianness) follows that of
the platform. (The `byteorder` argument must also be `"native"`.)

In `"native"` size mode, integer type sizes follow those of the standard C
integer types of the platform (`int`, `unsigned short` etc.).

```python
@dcs.dataclass_struct()
class NativeStruct:
    signed_char: dcs.SignedChar
    signed_short: dcs.Short
    unsigned_long_long: dcs.UnsignedLongLong
    void_pointer: dcs.Pointer
```

### Standard size mode

In `"std"` mode, the struct is packed without any additional padding for
alignment.

The `"std"` size mode supports four different `byteorder` values: `"native"`
(the default), `"little"`, `"big"`, and `"network"`. The `"native"` setting uses
the system byte order (similar to `"native"` size mode, but without alignment).
The `"network"` setting is equivalent to `"big"`.

The `"std"` size uses platform-independent integer sizes, similar to using the
integer types from `stdint.h` in C. When used with `byteorder` set to
`"little"`, `"big"`, or `"network"`, it is appropriate for marshalling data
across different platforms.

```python
@dcs.dataclass_struct(size="std", byteorder="native")
class NativeStruct:
    int8_t: dcs.I8
    uint64_t: dcs.U64
```

### Supported type annotations

#### Native integer types

These types are only supported in `"native"` size mode. Their native Python
types are all `int`.

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

These types are only supported in `"std"` size mode. Their native Python types
are all `int`.

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
| `F16`                                | Extension type (see below)  |
| `F32`                                | `float`                     |
| `F64`                                | `double`                    |
| `float` (builtin alias to `F64`)     | `double`                    |

`F16` is a half precision floating point. Some compilers provide support for it
on certain platforms (e.g.
[GCC](https://gcc.gnu.org/onlinedocs/gcc/Half-Precision.html),
[Clang](https://clang.llvm.org/docs/LanguageExtensions.html#half-precision-floating-point)).
It is also available as
[`std::float16_t`](https://en.cppreference.com/w/cpp/types/floating-point.html)
in C++23.

Note that floating point fields are always packed and unpacked using the IEEE
754 format, regardless of the underlying format used by the platform.

#### Boolean

The builtin `bool` type or `dataclasses_struct.Bool` type can be used to
represent a boolean, which uses a single byte in either native or standard size
modes.

#### Characters and bytes arrays

In both size modes, a single byte can be packed by annotating a field with the
builtin `bytes` type or the `dataclasses_struct.Char` type. The field's
unpacked Python representation will be a `bytes` of length 1.

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

#### Nested structs

Classes decorated with `dataclass_struct` can be used as fields in other
classes, as long as they have the same `size` and `byteorder` settings.

```python
@dcs.dataclass_struct()
class Vector2d:
    x: float
    y: float

@dcs.dataclass_struct()
class Vectors:
    direction: Vector2d
    velocity: Vector2d

# Will raise TypeError:
@dcs.dataclass_struct(size="std")
class VectorsStd:
    direction: Vector2d
    velocity: Vector2d
```

Default values for nested class fields cannot be set directly, as Python doesn't
allow using mutable default values in dataclasses. To get around this, pass
`frozen=True` to the inner class' `dataclass_struct` decorator. Alternatively,
pass a zero-argument callable that returns an instance of the class to the
`default_factory` keyword argument of
[`dataclasses.field`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field).
For example:

```python
from dataclasses import field

@dcs.dataclass_struct()
class VectorsStd:
    direction: Vector2d
    velocity: Vector2d = field(default_factory=lambda: Vector2d(0, 0))
```

The return type of the `default_factory` will be validated unless
`validate_defaults=False` is passed to the `dataclass_struct` decorator. Note
that this means the callable passed to `default_factory` will be called once
during class creation.

#### Fixed-length arrays

Fixed-length arrays can be represented by annotating a `list` field with
`typing.Annotated` and a positive length.

```python
from typing import Annotated

@dcs.dataclass_struct()
class FixedLength:
    fixed: Annotated[list[int], 5]
```

```python
>>> FixedLength.from_packed(FixedLength([1, 2, 3, 4, 5]).pack())
FixedLength(fixed=[1, 2, 3, 4, 5])
```

The values stored in fixed-length arrays can also be classes
decorated with `dataclass_struct`.

```python
from typing import Annotated

@dcs.dataclass_struct()
class Vector2d:
    x: float
    y: float

@dcs.dataclass_struct()
class FixedLength:
    fixed: Annotated[list[Vector2d], 3]
```

```python
>>> FixedLength.from_packed(FixedLength([Vector2d(1.0, 2.0), Vector2d(3.0, 4.0), Vector2d(5.0, 6.0)]).pack())
FixedLength(fixed=[Vector2d(x=1.0, y=2.0), Vector2d(x=3.0, y=4.0), Vector2d(x=5.0, y=6.0)])
```

Fixed-length arrays can also be multi-dimensional by nesting Annotated
`list` types.

```python
from typing import Annotated

@dcs.dataclass_struct()
class TwoDimArray:
    fixed: Annotated[list[Annotated[list[int], 2]], 3]
```

```python
>>> TwoDimArray.from_packed(TwoDimArray([[1, 2], [3, 4], [5, 6]]).pack())
TwoDimArray(fixed=[[1, 2], [3, 4], [5, 6]])
```

As with [nested structs](#nested-structs), a `default_factory` must be used to
set a default value. For example:

```python
from dataclasses import field
from typing import Annotated

@dcs.dataclass_struct()
class DefaultArray:
    x: Annotated[list[int], 3] = field(default_factory=lambda: [1, 2, 3])
```

The returned default value's length and type and values of its items will be
validated unless `validate_defaults=False` is passed to the `dataclass_struct`
decorator.

#### Manual padding

Padding can be manually controlled by annotating a type with `PadBefore` or
`PadAfter`:

```python
@dcs.dataclass_struct()
class WithPadding:
    # 4 padding bytes will be added before this field
    pad_before: Annotated[int, dcs.PadBefore(4)]

    # 2 padding bytes will be added before this field
    pad_after: Annotated[int, dcs.PadAfter(2)]

    # 3 padding bytes will be added before this field and 2 after
    pad_before_and_after: Annotated[int, dcs.PadBefore(3), dcs.PadAfter(2)]
```

A `b'\x00'` will be inserted into the packed representation for each padding
byte.

```python
>>> padded = WithPadding(100, 200, 300)
>>> packed = padded.pack()
>>> packed
b'\x00\x00\x00\x00d\x00\x00\x00\xc8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00,\x01\x00\x00\x00\x00'
>>> WithPadding.from_packed(packed)
WithPadding(pad_before=100, pad_after=200, pad_before_and_after=300)
```

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
