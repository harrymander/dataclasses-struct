from typing_extensions import Annotated

from . import field

# Single char type
Char = Annotated[bytes, field.CharField()]

# Boolean type
Bool = Annotated[bool, field.BoolField()]

# Integer types
Int8 = Annotated[int, field.SignedIntField(1)]
Uint8 = Annotated[int, field.UnsignedIntField(1)]
Int16 = Annotated[int, field.SignedIntField(2)]
Uint16 = Annotated[int, field.UnsignedIntField(2)]
Int32 = Annotated[int, field.SignedIntField(4)]
Uint32 = Annotated[int, field.UnsignedIntField(4)]
Int64 = Annotated[int, field.SignedIntField(8)]
Uint64 = Annotated[int, field.UnsignedIntField(8)]

# Native size types
Size = Annotated[int, field.UnsignedSizeField()]
SSize = Annotated[int, field.SignedSizeField()]
Pointer = Annotated[int, field.PointerField()]

# Floating point types
Float32 = Annotated[float, field.FloatField()]
Float = Float32
Float64 = Annotated[float, field.DoubleField()]
Double = Float64


class _Padding:
    before: bool

    def __init__(self, size: int):
        if size < 1:
            raise ValueError('size must be >= 1')
        self.size = size

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.size})'


class PadBefore(_Padding):
    before = True

    def __init__(self, size: int):
        super().__init__(size)


class PadAfter(_Padding):
    before = False

    def __init__(self, size: int):
        super().__init__(size)
