from typing import Annotated


Pad = Annotated[None, 'x']
Char = Annotated[bytes, 'c']
Int8 = Annotated[int, 'b']
Uint8 = Annotated[int, 'B']
Bool = Annotated[bool, '?']
Int16 = Annotated[int, 'h']
Uint16 = Annotated[int, 'H']
Int32 = Annotated[int, 'i']
Uint32 = Annotated[int, 'I']
Int64 = Annotated[int, 'q']
Uint64 = Annotated[int, 'Q']

# size_t = 'n' (native only)
# ssize_t = 'N' (native only)

Float32 = Annotated[float, 'f']
Float = Float32
Float64 = Annotated[float, 'd']
Double = Float64


class String:
    def __init__(self, n: int):
        self.n = n


PascalString = bytes
FixedString = bytes
