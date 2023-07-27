import abc
from ctypes import c_size_t, c_ssize_t, c_void_p, sizeof
from typing import Generic, Literal, Type, TypeVar

from . import intsizes

T = TypeVar('T')


class Field(abc.ABC, Generic[T]):
    native_only: bool = False
    type_: Type[T]

    @abc.abstractmethod
    def format(self) -> str:
        ...

    def validate(self, val: T) -> None:
        pass

    def __repr__(self) -> str:
        return f'{type(self).__name__}'


class BoolField(Field[bool]):
    type_ = bool

    def format(self) -> str:
        return '?'


class CharField(Field[bytes]):
    type_ = bytes

    def format(self) -> str:
        return 'c'

    def validate(self, val: bytes) -> None:
        if len(val) != 1:
            raise ValueError('value must be a single byte')


class IntField(Field[int]):
    signed: bool
    size: int
    type_ = int

    _formats = {
        1: 'b',
        2: 'h',
        4: 'i',
        8: 'q',
    }

    _signed_sizes = {
        1: (intsizes.I8_MIN, intsizes.I8_MAX),
        2: (intsizes.I16_MIN, intsizes.I16_MAX),
        4: (intsizes.I32_MIN, intsizes.I32_MAX),
        8: (intsizes.I64_MIN, intsizes.I64_MAX),
    }

    _unsigned_sizes = {
        1: (intsizes.U8_MIN, intsizes.U8_MAX),
        2: (intsizes.U16_MIN, intsizes.U16_MAX),
        4: (intsizes.U32_MIN, intsizes.U32_MAX),
        8: (intsizes.U64_MIN, intsizes.U64_MAX),
    }

    def __init__(
        self,
        signed: bool,
        size: Literal[1, 2, 4, 8]
    ):
        self.signed = signed
        self.size = size

        if size not in self._formats:
            allowed = ', '.join(map(str, self._formats))
            raise ValueError(f'only allowed sizes of: {allowed}')

    def format(self) -> str:
        f = self._formats[self.size]
        return f if self.signed else f.upper()

    def validate(self, val: int) -> None:
        sizes = self._signed_sizes if self.signed else self._unsigned_sizes
        min_, max_ = sizes[self.size]
        if not (min_ <= val <= max_):
            sign = 'signed' if self.signed else 'unsigned'
            n = self.size * 8
            raise ValueError(f'value out of range for {n}-bit {sign} integer')

    def __repr__(self) -> str:
        sign = 'signed' if self.signed else 'unsigned'
        bits = self.size * 8
        return f'{super().__repr__()}({sign}, {bits}-bit)'


class SignedIntField(IntField):
    def __init__(self, size: Literal[1, 2, 4, 8]):
        super().__init__(True, size)


class UnsignedIntField(IntField):
    def __init__(self, size: Literal[1, 2, 4, 8]):
        super().__init__(False, size)


class Float32Field(Field[float]):
    type_ = float

    def format(self) -> str:
        return 'f'


class Float64Field(Field[float]):
    type_ = float

    def format(self) -> str:
        return 'd'


class SizeField(Field[int]):
    native_only = True
    type_ = int

    signed_field = IntField(True, sizeof(c_ssize_t))  # type: ignore
    unsigned_field = IntField(False, sizeof(c_size_t))  # type: ignore

    def __init__(self, signed: bool):
        self.signed = signed

    def format(self) -> str:
        return 'n' if self.signed else 'N'

    def validate(self, val: int) -> None:
        if self.signed:
            self.signed_field.validate(val)
        else:
            self.unsigned_field.validate(val)


class UnsignedSizeField(SizeField):
    def __init__(self):
        super().__init__(False)


class SignedSizeField(SizeField):
    def __init__(self):
        super().__init__(True)


class PointerField(Field[int]):
    native_only = True
    type_ = int
    max_ = 2**(sizeof(c_void_p) * 8) - 1

    def format(self) -> str:
        return 'P'

    def validate(self, val: int) -> None:
        if not (0 <= val <= self.max_):
            raise ValueError('value out of range for system pointer')


class BytesField(Field[bytes]):
    type_ = bytes

    def __init__(self, n: int):
        if n < 1:
            raise ValueError('n must be positive non-zero integer')

        self.n = n

    def format(self) -> str:
        return f'{self.n}s'

    def validate(self, val: bytes) -> None:
        if len(val) > self.n:
            raise ValueError(f'bytes cannot be longer than {self.n} bytes')

    def __repr__(self) -> str:
        return f'{super().__repr__()}({self.n})'


primitive_fields = {
    int: SignedIntField(8),
    float: Float64Field(),
    bool: BoolField(),
    bytes: CharField(),
}
