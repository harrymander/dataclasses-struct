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

## Example usage

```python
from typing import Annotated

import dataclasses_struct as dcs

@dcs.dataclass_struct()
class Test:
    x: int # (1)!
    y: float # (2)!
    z: dcs.UnsignedShort # (3)!
    s: Annotated[bytes, 10] # (4)!

@dcs.dataclass_struct()
class Container:
    test1: Test # (5)!
    test2: Test
```

1. Equivalent to `int` in C.
2. Equivalent to `double` in C, i.e. a double precision floating point.
3. Equivalent to `unsigned short` in C.
4. Equivalent to `char[10]` in C, i.e. a fixed-length byte array of length 10.
   Values shorter than the size are padded with zeros and values longer than the
   size are truncated.
5. Classes decorated with `dataclass_struct` can be nested in other classes, as
   long as they have the same `std` and `byteorder` args.

Instances of decorated classes have a `pack` method that returns the packed
representation of the object in `bytes`:

```python
>>> t1 = Test(100, -0.25, 0xff, b'12345')
>>> packed = t1.pack()
>>> packed
b'd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0\xbf\xff\x0012345\x00\x00\x00\x00\x00'
```

Decorated classes have an `unpack` class method that takes the packed
representation returns an instance of the class:

```python
>>> Test.from_packed(packed)
Test(x=100, y=-0.25, z=255, s=b'12345\x00\x00\x00\x00\x00')
```
