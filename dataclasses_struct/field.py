import abc
import ctypes
from typing import Any, ClassVar, Generic, Literal, TypeVar, Union

T = TypeVar("T")


class Field(abc.ABC, Generic[T]):
    is_native: bool = True
    is_std: bool = True
    field_type: Union[type[T], tuple[type[T], ...]]

    @abc.abstractmethod
    def format(self) -> str: ...

    def validate_default(self, val: T) -> None:
        pass

    def __repr__(self) -> str:
        return f"{type(self).__name__}"


class BoolField(Field[bool]):
    field_type = bool

    def format(self) -> str:
        return "?"


class CharField(Field[bytes]):
    field_type = bytes

    def format(self) -> str:
        return "c"

    def validate_default(self, val: bytes) -> None:
        if len(val) != 1:
            raise ValueError("value must be a single byte")


class IntField(Field[int]):
    field_type = int

    def __init__(
        self,
        fmt: str,
        signed: bool,
        size: int,
    ):
        if signed and fmt.isupper():
            raise ValueError(
                "signed integer should have lowercase format string"
            )

        self.signed = signed
        self.size = size
        self._format = fmt

        nbits = self.size * 8
        if signed:
            exp = 1 << (nbits - 1)
            self.min_ = -exp
            self.max_ = exp - 1
        else:
            self.min_ = 0
            self.max_ = (1 << nbits) - 1

    def format(self) -> str:
        return self._format

    def validate_default(self, val: int) -> None:
        if not (self.min_ <= val <= self.max_):
            sign = "signed" if self.signed else "unsigned"
            n = self.size * 8
            raise ValueError(f"value out of range for {n}-bit {sign} integer")

    def __repr__(self) -> str:
        sign = "signed" if self.signed else "unsigned"
        return f"{super().__repr__()}({sign}, {self.size * 8}-bit)"


class StdIntField(IntField):
    is_native = False
    _unsigned_formats: ClassVar = {
        1: "B",
        2: "H",
        4: "I",
        8: "Q",
    }

    def __init__(self, signed: bool, size: Literal[1, 2, 4, 8]):
        fmt = self._unsigned_formats[size]
        if signed:
            fmt = fmt.lower()
        super().__init__(fmt, signed, size)


class SignedStdIntField(StdIntField):
    def __init__(self, size: Literal[1, 2, 4, 8]):
        super().__init__(True, size)


class UnsignedStdIntField(StdIntField):
    def __init__(self, size: Literal[1, 2, 4, 8]):
        super().__init__(False, size)


class FloatingPointField(Field[float]):
    field_type = (int, float)

    def __init__(self, format: str):
        self._format = format

    def format(self) -> str:
        return self._format


class NativeIntField(IntField):
    is_std = False

    def __init__(self, fmt: str, ctype_name: str):
        size = ctypes.sizeof(getattr(ctypes, f"c_{ctype_name}"))
        signed = not ctype_name.startswith("u")
        super().__init__(fmt, signed, size)


class SizeField(IntField):
    is_std = False

    def __init__(self, signed: bool):
        fmt = "n" if signed else "N"
        size = ctypes.sizeof(ctypes.c_ssize_t if signed else ctypes.c_size_t)
        super().__init__(fmt, signed, size)

    def validate_default(self, val: int) -> None:
        if not (self.min_ <= val <= self.max_):
            sign = "signed" if self.signed else "unsigned"
            raise ValueError(f"value out of range for {sign} size type")


class PointerField(IntField):
    is_std = False

    def __init__(self):
        super().__init__("P", False, ctypes.sizeof(ctypes.c_void_p))

    def format(self) -> str:
        return "P"

    def validate_default(self, val: int) -> None:
        if not (self.min_ <= val <= self.max_):
            raise ValueError("value out of range for system pointer")


builtin_fields: dict[type[Any], Field[Any]] = {
    int: NativeIntField("i", "int"),
    float: FloatingPointField("d"),
    bool: BoolField(),
    bytes: CharField(),
}
