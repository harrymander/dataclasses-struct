from typing_extensions import Annotated

from . import field

# Single char type
Char = Annotated[bytes, field.CharField()]

# Boolean type
Bool = Annotated[bool, field.BoolField()]

# Integer types
I8 = Annotated[int, field.SignedIntField(1)]
U8 = Annotated[int, field.UnsignedIntField(1)]
I16 = Annotated[int, field.SignedIntField(2)]
U16 = Annotated[int, field.UnsignedIntField(2)]
I32 = Annotated[int, field.SignedIntField(4)]
U32 = Annotated[int, field.UnsignedIntField(4)]
I64 = Annotated[int, field.SignedIntField(8)]
U64 = Annotated[int, field.UnsignedIntField(8)]

# Native size types
Size = Annotated[int, field.UnsignedSizeField()]
SSize = Annotated[int, field.SignedSizeField()]
Pointer = Annotated[int, field.PointerField()]

# Floating point types
F32 = Annotated[float, field.Float32Field()]
F64 = Annotated[float, field.Float64Field()]


class _Padding:
    before: bool

    def __init__(self, size: int):
        if size < 0:
            raise ValueError('size must be non-negative')
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
