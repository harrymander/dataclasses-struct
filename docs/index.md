# dataclasses-struct

[![PyPI version](https://img.shields.io/pypi/v/dataclasses-struct)](https://pypi.org/project/dataclasses-struct/)
[![Python versions](https://img.shields.io/pypi/pyversions/dataclasses-struct)](https://pypi.org/project/dataclasses-struct/)
[![Tests status](https://github.com/harrymander/dataclasses-struct/actions/workflows/ci.yml/badge.svg?event=push)](https://github.com/harrymander/dataclasses-struct/actions/workflows/ci.yml)
[![Code coverage](https://img.shields.io/codecov/c/gh/harrymander/dataclasses-struct)](https://app.codecov.io/gh/harrymander/dataclasses-struct)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/harrymander/dataclasses-struct/blob/main/LICENSE)

A simple Python package that combines
[`dataclasses`](https://docs.python.org/3/library/dataclasses.html) with
[`struct`](https://docs.python.org/3/library/struct.html) for packing and
unpacking Python dataclasses to fixed-length `bytes` representations.

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

## Quick start

By default, dataclass-structs use native sizes, alignment, and byte ordering
(endianness).

```python
import dataclasses
from typing import Annotated

import dataclasses_struct as dcs  # (1)!

@dcs.dataclass_struct(size="native", byteorder="native")  # (2)!
class Vector2d:
    x: dcs.F64  # (3)!
    y: float  #(4)!

@dcs.dataclass_struct(kw_only=True)  #(5)!
class Object:
    position: Vector2d  #(6)!
    velocity: Vector2d = dataclasses.field(  # (7)!
        default_factory=lambda: Vector2d(0, 0)
    )
    name: Annotated[bytes, 8]  #(8)!
```

1. This convention of importing `dataclasses_struct` under the alias `dcs` is
   used throughout these docs, but you don't have to follow this if you don't
   want to.
2. The `size` and `byteorder` keyword arguments control the size, alignment, and
   endianness of the class' packed binary representation. The default mode
   `"native"` is native for both arguments.
3. A double precision floating point, equivalent to `double` in C.
4. The builtin `float` type is an alias to `dcs.F64`.
5. The [`dataclass_struct`][dataclasses_struct.dataclass_struct] decorator
   supports most of the keyword arguments supported by the stdlib
   [`dataclass`](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass)
   decorator.
6. Classes decorated with
   [`dcs.dataclass_struct`][dataclasses_struct.dataclass_struct] can be used as
   fields in other dataclass-structs provided they have the same size and
   byteorder modes.
7. The stdlib
   [`dataclasses.field`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field)
   function can be used for more complex field configurations, such as using
   a mutable value as a field default.
8. Fixed-length `bytes` arrays can be represented by annotating a field with
   a non-zero positive integer using `typing.Annotated`. Values longer than the
   length will be truncated and values shorted will be zero-padded.

Instances of decorated classes have a
[`pack`][dataclasses_struct.DataclassStructProtocol.pack] method that returns
the packed representation of the object in `bytes`:

```python
>>> obj = Object(position=Vector2d(1.5, -5.6), name=b"object1")
>>> obj
Object(position=Vector2d(x=1.5, y=-5.6), velocity=Vector2d(x=0, y=0), name=b'object1')
>>> packed = obj.pack()
>>> packed
b'\x00\x00\x00\x00\x00\x00\xf8?ffffff\x16\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00object1\x00'
```

Decorated classes have an
[`from_packed`][dataclasses_struct.DataclassStructProtocol.from_packed] class
method that takes the packed representation and returns an instance of the
class:

```python
>>> Object.from_packed(packed)
Object(position=Vector2d(x=1.5, y=-5.6), velocity=Vector2d(x=0.0, y=0.0), name=b'object1\x00')
```

In `size="native"` mode, integer type names follow the standard C integer type
names:

```python
@dcs.dataclass_struct()
class NativeIntegers:
   c_int: dcs.Int
   c_int_alias: int  # (1)!
   c_unsigned_short: dcs.UnsignedShort
   void_pointer: dcs.Pointer  # (2)!
   size_t: dcs.UnsignedSize

   # etc.
```

1. Alias to `dcs.Int`.
2. Equivalent to `void *` pointer in C.

In `size="std"` mode, integer type names follow the standard [fixed-width
integer type](https://en.cppreference.com/w/c/types/integer.html#Types) names in
C:

```python
@dcs.dataclass_struct(size="std")
class StdIntegers:
   int8_t: dcs.I8
   int32_t: dcs.I32
   uint64_t: dcs.U64

   # etc.
```

See [the guide](guide.md#supported-type-annotations) for the full list of
supported field types.
