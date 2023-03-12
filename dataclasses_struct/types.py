from typing import Annotated

from . import field

# Single char type
Char = Annotated[bytes, field.CharField()]

# Boolean type
Bool = Annotated[bool, field.BoolField()]

# Integer types
Int8 = Annotated[int, field.IntField(True, 1)]
Uint8 = Annotated[int, field.IntField(False, 1)]
Int16 = Annotated[int, field.IntField(True, 2)]
Uint16 = Annotated[int, field.IntField(False, 2)]
Int32 = Annotated[int, field.IntField(True, 4)]
Uint32 = Annotated[int, field.IntField(False, 4)]
Int64 = Annotated[int, field.IntField(True, 8)]
Uint64 = Annotated[int, field.IntField(False, 8)]

# Native size types
Size = Annotated[int, field.SizeField(False)]
SSize = Annotated[int, field.SizeField(True)]
Pointer = Annotated[int, field.PointerField()]

# Floating point types
Float32 = Annotated[float, field.FloatField()]
Float = Float32
Float64 = Annotated[float, field.DoubleField()]
Double = Float64
