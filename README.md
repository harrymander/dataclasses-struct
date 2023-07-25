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
from typing import Annotated  # use typing_extensions on Python <3.9
import dataclasses_struct as dcs

@dcs.dataclass()
class Test:
    x: int  # or dcs.I64, i.e., a signed 64-bit integer
    y: float  # or dcs.Float64, i.e., a double-precision (64-bit) floating point
    z: dcs.U8  # unsigned 8-bit integer
    s: Annotated[bytes, 10]  # fixed-length byte array of length 10
```

```python
>>> t = Test(100, -0.25, 0xff, b'12345')
>>> t
Test(x=100, y=-0.25, z=255, s=b'12345')
>>> packed = t.pack()
>>> packed
b'd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0\xbf\xff12345\x00\x00\x00\x00\x00'
>>> Test.from_packed(packed)
Test(x=100, y=-0.25, z=255, s=b'12345\x00\x00\x00\x00\x00')
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

```python
from typing import Annotated  # use typing_extensions on Python <3.9
import dataclasses_struct as dcs

endians = (
    dcs.NATIVE_ENDIAN_ALIGNED,  # uses system endianness and alignment
    dcs.NATIVE_ENDIAN,  # system endianness, packed representation
    dcs.LITTLE_ENDIAN,
    dcs.BIG_ENDIAN,
    dcs.NETWORK_ENDIAN,
)

@dcs.dataclass(endians[0])  # if no endian provided, defaults to NATIVE_ENDIAN_ALIGNED
class Test:

    # Single char type (must be bytes)
    single_char: dcs.Char
    single_char_alias: bytes  # alias for Char

    # Boolean
    bool_1: dcs.Bool
    bool_2: bool  # alias for Bool

    # Iegers
    int8: dcs.I8
    uint8: dcs.U8
    int16: dcs.I16
    uint16: dcs.U16
    int32: dcs.I32
    uint32: dcs.U32
    uint64: dcs.U64
    int64: dcs.I64
    int64_alias: int  # alias for I64

    # Only supported with NATIVE_ENDIAN_ALIGNED
    unsigned_size: dcs.Size
    signed_size: dcs.SSize
    pointer: dcs.Pointer

    # Floating point types
    single_precision: dcs.Float32  # equivalent to float in C
    double_precision: dcs.Float64  # equivalent to double in C
    double_precision_alias: float  # alias for Float64

    # Byte arrays: values shorter than size will be padded with b'\x00'
    array: Annotated[bytes, 100]  # an array of length 100

    # Pad bytes can be added before and after fields: a b'\x00' will be
    # inserted for each pad byte.
    pad_before: Annotated[int, dcs.PadBefore(4)]
    pad_after: Annotated[int, dcs.PadAfter(2)]
    pad_before_and_after: Annotated[int, dcs.PadBefore(3), dcs.PadAfter(2)]
```

Decorated classes are transformed to a standard Python
[dataclass](https://docs.python.org/3/library/dataclasses.html) with boilerplate
`__init__`, `__repr__`, `__eq__` etc. auto-generated. Additionally, two methods
are added to the class: `pack`, a method for packing an instance of the class to
`bytes`, and `from_packed`, a class method that returns a new instance of the
class from its packed `bytes` representation.

An additional class attribute, `__dataclass_struct__`, of type
[`struct.Struct`](https://docs.python.org/3/library/struct.html#struct.Struct)
is added. The [`struct` format
string](https://docs.python.org/3/library/struct.html#format-strings) and packed
size can be accessed like so:

```python
>>> Test.__dataclass_struct__.format
'@cc??bBhHiIQqqNnPfdd100s4xqq2x3xq2x'
>>> Test.__dataclass_struct__.size
234
```

Default attribute values will be validated against their expected type and
allowable value range. For example,

```python3
import dataclasses_struct as dcs

@dcs.dataclass()
class Test:
    x: dcs.U8 = -1
```

will raise a `ValueError`. This can be disabled by passing `validate=False` to
the `dataclasses_struct.dataclass` decorator.
