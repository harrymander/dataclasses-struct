from typing import Annotated

from . import field

Char = bytes
"""Single char type. Supported in both size modes."""

Bool = Annotated[bool, field.BoolField()]
"""Boolean type. Supported in both size modes."""

I8 = Annotated[int, field.SignedStdIntField(1)]
"""Fixed-width 8-bit signed integer. Supported with `size="std"`."""

U8 = Annotated[int, field.UnsignedStdIntField(1)]
"""Fixed-width 8-bit unsigned integer. Supported with `size="std"`."""

I16 = Annotated[int, field.SignedStdIntField(2)]
"""Fixed-width 16-bit signed integer. Supported with `size="std"`."""

U16 = Annotated[int, field.UnsignedStdIntField(2)]
"""Fixed-width 16-bit unsigned integer. Supported with `size="std"`."""

I32 = Annotated[int, field.SignedStdIntField(4)]
"""Fixed-width 32-bit signed integer. Supported with `size="std"`."""

U32 = Annotated[int, field.UnsignedStdIntField(4)]
"""Fixed-width 32-bit unsigned integer. Supported with `size="std"`."""

I64 = Annotated[int, field.SignedStdIntField(8)]
"""Fixed-width 64-bit signed integer. Supported with `size="std"`."""

U64 = Annotated[int, field.UnsignedStdIntField(8)]
"""Fixed-width 64-bit unsigned integer. Supported with `size="std"`."""


# Native integer types
SignedChar = Annotated[int, field.NativeIntField("b", "byte")]
"""Equivalent to native C `signed char`. Supported with `size="native"`."""

UnsignedChar = Annotated[int, field.NativeIntField("B", "ubyte")]
"""Equivalent to native C `unsigned char`. Supported with `size="native"`."""

Short = Annotated[int, field.NativeIntField("h", "short")]
"""Equivalent to native C `short`. Supported with `size="native"`."""

UnsignedShort = Annotated[int, field.NativeIntField("H", "ushort")]
"""Equivalent to native C `unsigned short`. Supported with `size="native"`."""

Int = Annotated[int, field.NativeIntField("i", "int")]
"""Equivalent to native C `int`. Supported with `size="native"`."""

UnsignedInt = Annotated[int, field.NativeIntField("I", "uint")]
"""Equivalent to native C `unsigned int`. Supported with `size="native"`."""

Long = Annotated[int, field.NativeIntField("l", "long")]
"""Equivalent to native C `long`. Supported with `size="native"`."""

UnsignedLong = Annotated[int, field.NativeIntField("L", "ulong")]
"""Equivalent to native C `unsigned long`. Supported with `size="native"`."""

LongLong = Annotated[int, field.NativeIntField("q", "longlong")]
"""Equivalent to native C `long long`. Supported with `size="native"`."""

UnsignedLongLong = Annotated[int, field.NativeIntField("Q", "ulonglong")]
"""Equivalent to native C `unsigned long long`. Supported with
`size="native"`."""


# Native size types
UnsignedSize = Annotated[int, field.SizeField(signed=False)]
"""Equivalent to native C `size_t`. Supported with `size="native"`."""

SignedSize = Annotated[int, field.SizeField(signed=True)]
"""Equivalent to native C `ssize_t` (a POSIX extension type). Supported with
`size="native"`."""

# Native pointer types
Pointer = Annotated[int, field.PointerField()]
"""Equivalent to native C `void *` pointer. Supported with `size="native"`."""

# Floating point types
F16 = Annotated[float, field.FloatingPointField("e")]
"""Half-precision floating point number. Supported in both size modes.

Some compilers provide support for half precision floats on certain platforms
(e.g. [GCC](https://gcc.gnu.org/onlinedocs/gcc/Half-Precision.html),
[Clang](https://clang.llvm.org/docs/LanguageExtensions.html#half-precision-floating-point)).
It is also available as
[`std::float16_t`](https://en.cppreference.com/w/cpp/types/floating-point.html)
in C++23.
"""

F32 = Annotated[float, field.FloatingPointField("f")]
"""Single-precision floating point number, equivalent to `float` in C.
Supported in both size modes."""

F64 = Annotated[float, field.FloatingPointField("d")]
"""Double-precision floating point number, equivalent to `double` in C.
Supported in both size modes."""


class _Padding:
    before: bool

    def __init__(self, size: int):
        if not isinstance(size, int) or size < 0:
            raise ValueError("padding size must be non-negative int")
        self.size = size

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.size})"


class PadBefore(_Padding):
    """Add zero-bytes padding before the field.

    Should be used with `typing.Annotated`.

    ```python
    from typing import Annotated
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Padded:
        x: Annotated[int, dcs.PadBefore(5)]
    ```

    Args:
        size: The number of padding bytes to add before the field.
    """

    before = True

    def __init__(self, size: int):
        super().__init__(size)


class PadAfter(_Padding):
    """Add zero-bytes padding after the field.

    Should be used with `typing.Annotated`.

    ```python
    from typing import Annotated
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class Padded:
        x: Annotated[int, dcs.PadAfter(5)]
    ```

    Args:
        size: The number of padding bytes to add after the field.
    """

    before = False

    def __init__(self, size: int):
        super().__init__(size)
