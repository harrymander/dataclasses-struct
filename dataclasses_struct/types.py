from typing import Annotated

from . import field

# Single char type
Char = bytes

# Boolean type
Bool = Annotated[bool, field.BoolField()]

# Standard integer types
I8 = Annotated[int, field.SignedStdIntField(1)]
U8 = Annotated[int, field.UnsignedStdIntField(1)]
I16 = Annotated[int, field.SignedStdIntField(2)]
U16 = Annotated[int, field.UnsignedStdIntField(2)]
I32 = Annotated[int, field.SignedStdIntField(4)]
U32 = Annotated[int, field.UnsignedStdIntField(4)]
I64 = Annotated[int, field.SignedStdIntField(8)]
U64 = Annotated[int, field.UnsignedStdIntField(8)]

# Native integer types
SignedChar = Annotated[int, field.NativeIntField("b", "byte")]
UnsignedChar = Annotated[int, field.NativeIntField("B", "ubyte")]
Short = Annotated[int, field.NativeIntField("h", "short")]
UnsignedShort = Annotated[int, field.NativeIntField("H", "ushort")]
Int = Annotated[int, field.NativeIntField("i", "int")]
UnsignedInt = Annotated[int, field.NativeIntField("I", "uint")]
Long = Annotated[int, field.NativeIntField("l", "long")]
UnsignedLong = Annotated[int, field.NativeIntField("L", "ulong")]
LongLong = Annotated[int, field.NativeIntField("q", "longlong")]
UnsignedLongLong = Annotated[int, field.NativeIntField("Q", "ulonglong")]

# Native size types
UnsignedSize = Annotated[int, field.SizeField(signed=False)]
SignedSize = Annotated[int, field.SizeField(signed=True)]

# Native pointer types
Pointer = Annotated[int, field.PointerField()]

# Floating point types
F16 = Annotated[float, field.FloatingPointField("e")]
F32 = Annotated[float, field.FloatingPointField("f")]
F64 = Annotated[float, field.FloatingPointField("d")]


class _Padding:
    before: bool

    def __init__(self, size: int):
        if not isinstance(size, int) or size < 0:
            raise ValueError("padding size must be non-negative int")
        self.size = size

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.size})"


class PadBefore(_Padding):
    before = True

    def __init__(self, size: int):
        super().__init__(size)


class PadAfter(_Padding):
    before = False

    def __init__(self, size: int):
        super().__init__(size)
