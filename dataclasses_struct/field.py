import abc
from typing import Generic, Literal, TypeVar


T = TypeVar('T')


class Field(abc.ABC, Generic[T]):
    native_only: bool = False

    @abc.abstractmethod
    def format(self) -> str:
        ...

    def validate(self, val: T) -> None:
        pass


class BoolField(Field[bool]):
    def format(self) -> str:
        return '?'


class CharField(Field[bytes]):
    def format(self) -> str:
        return 'c'

    def validate(self, val: bytes) -> None:
        if len(val) != 1:
            raise ValueError('value must be a single byte')


class IntField(Field[int]):
    signed: bool
    size: int

    _formats = {
        1: 'b',
        2: 'h',
        4: 'i',
        8: 'q',
    }

    _signed_sizes = {
        1: (-0x80, 0x7f),
        2: (-0x8000, 0x7fff),
        4: (-0x8000_0000, 0x7fff_ffff),
        8: (-0x8000_0000_0000_0000, 0x7fff_ffff_ffff_ffff),
    }

    _unsigned_sizes = {
        1: (0, 0xff),
        2: (0, 0xffff),
        4: (0, 0xffff_ffff),
        8: (0, 0xffff_ffff_ffff_ffff),
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
        return f.upper() if self.signed else f

    def validate(self, val: int) -> None:
        sizes = self._signed_sizes if self.signed else self._unsigned_sizes
        min_, max_ = sizes[self.size]
        if not min_ <= val <= max_:
            sign = 'signed' if self.signed else 'unsigned'
            raise ValueError(
                f'value out of range for {self.size}-bit {sign} integer'
            )


class FloatField(Field[float]):
    def format(self) -> str:
        return 'f'


class DoubleField(Field[float]):
    def format(self) -> str:
        return 'd'


class SizeField(Field[int]):
    native_only = True

    def __init__(self, signed: bool):
        self.signed = signed

    def format(self) -> str:
        return 'n' if self.signed else 'N'


class StringField(Field[bytes]):
    def __init__(self, n: int):
        if n < 1:
            raise ValueError('n must be positive non-zero integer')

        self.n = n

    def format(self) -> str:
        return f'{self.n}s'

    def validate(self, val: bytes) -> None:
        if len(val) > self.n:
            raise ValueError(f'string cannot be longer than {self.n} bytes')


class VariableLengthStringField(Field[bytes]):
    def validate(self, val: bytes) -> None:
        if len(val) > 0xff:
            raise ValueError(f'string cannot be longer than {0xff} bytes')

    def format(self) -> str:
        return 'p'
