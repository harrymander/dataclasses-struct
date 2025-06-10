import dataclasses
import sys
from collections.abc import Generator, Iterator
from struct import Struct
from typing import (
    Annotated,
    Any,
    Callable,
    Generic,
    Literal,
    Protocol,
    TypedDict,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from ._typing import TypeGuard, Unpack, dataclass_transform
from .field import Field, builtin_fields
from .types import PadAfter, PadBefore


def _get_padding_and_field(fields):
    pad_before = pad_after = 0
    field = None
    for f in fields:
        if isinstance(f, PadBefore):
            pad_before += f.size
        elif isinstance(f, PadAfter):
            pad_after += f.size
        elif field is not None:
            raise TypeError(f"too many annotations: {f}")
        else:
            field = f

    return pad_before, pad_after, field


T = TypeVar("T")


_SIZE_BYTEORDER_MODE_CHAR: dict[tuple[str, str], str] = {
    ("native", "native"): "@",
    ("std", "native"): "=",
    ("std", "little"): "<",
    ("std", "big"): ">",
    ("std", "network"): "!",
}
_MODE_CHAR_SIZE_BYTEORDER: dict[str, tuple[str, str]] = {
    v: k for k, v in _SIZE_BYTEORDER_MODE_CHAR.items()
}


class _DataclassStructInternal(Generic[T]):
    struct: Struct
    cls: type[T]
    _fieldnames: list[str]
    _fieldtypes: list[type]

    @property
    def format(self) -> str:
        return self.struct.format

    @property
    def size(self) -> int:
        return self.struct.size

    @property
    def mode(self) -> str:
        return self.format[0]

    def __init__(
        self,
        fmt: str,
        cls: type,
        fieldnames: list[str],
        fieldtypes: list[type],
    ):
        self.struct = Struct(fmt)
        self.cls = cls
        self._fieldnames = fieldnames
        self._fieldtypes = fieldtypes

    def _flattened_attrs(self, obj) -> list[Any]:
        """
        Returns a list of all attributes, including those of any nested structs
        """
        attrs = []
        for fieldname in self._fieldnames:
            attr = getattr(obj, fieldname)
            if is_dataclass_struct(attr):
                attrs.extend(attr.__dataclass_struct__._flattened_attrs(attr))
            else:
                attrs.append(attr)
        return attrs

    def pack(self, obj: T) -> bytes:
        return self.struct.pack(*self._flattened_attrs(obj))

    def _arg_generator(self, args: Iterator) -> Generator:
        for fieldtype in self._fieldtypes:
            if is_dataclass_struct(fieldtype):
                yield fieldtype.__dataclass_struct__._init_from_args(args)
            else:
                yield fieldtype(next(args))

    def _init_from_args(self, args: Iterator) -> T:
        """
        Returns an instance of self.cls, consuming args
        """
        return self.cls(*self._arg_generator(args))

    def unpack(self, data: bytes) -> T:
        return self._init_from_args(iter(self.struct.unpack(data)))


class DataclassStructProtocol(Protocol):
    __dataclass_struct__: _DataclassStructInternal
    """
    Internal data used by the library for packing and unpacking structs.
    """

    @classmethod
    def from_packed(cls: type[T], data: bytes) -> T:
        """Return an instance of the class from its packed representation.

        Args:
            data: The packed representation of the class as returned by
                [`dataclasses_struct.DataclassStructProtocol.pack`][].

        Returns:
            An instance of the class unpacked from `data`.

        Raises:
            struct.error: If `data` is the wrong length.
        """
        ...

    def pack(self) -> bytes:
        """Return the packed representation in `bytes` of the object.

        Returns:
            The packed representation. Can be used to instantiate a new object
                with
                [`dataclasses_struct.DataclassStructProtocol.from_packed`][].

        Raises:
            struct.error: If any of the fields are out of range or the wrong
                type.
        """
        ...


@overload
def is_dataclass_struct(
    obj: type,
) -> TypeGuard[type[DataclassStructProtocol]]: ...


@overload
def is_dataclass_struct(obj: object) -> TypeGuard[DataclassStructProtocol]: ...


def is_dataclass_struct(
    obj: Union[type, object],
) -> Union[
    TypeGuard[DataclassStructProtocol],
    TypeGuard[type[DataclassStructProtocol]],
]:
    """Determine whether a type or object is a dataclass-struct.

    Args:
        obj: A class or object.

    Returns:
        `True` if obj is a class that has been decorated with
            [`dataclasses_struct.dataclass_struct`][] or is an instance of one.
    """
    return (
        dataclasses.is_dataclass(obj)
        and hasattr(obj, "__dataclass_struct__")
        and isinstance(obj.__dataclass_struct__, _DataclassStructInternal)
    )


def get_struct_size(cls_or_obj: object) -> int:
    """Get the size of the packed representation of the struct in bytes.

    Args:
        cls_or_obj: A class that has been decorated with
            [`dataclasses_struct.dataclass_struct`][] or an instance of one.

    Returns:
        The size of the packed representation in bytes.

    Raises:
        TypeError: if `cls_or_obj` is not a dataclass-struct.
    """
    if not is_dataclass_struct(cls_or_obj):
        raise TypeError(f"{cls_or_obj} is not a dataclass_struct")
    return cls_or_obj.__dataclass_struct__.size


class _BytesField(Field[bytes]):
    field_type = bytes

    def __init__(self, n: int):
        if not isinstance(n, int) or n < 1:
            raise ValueError("bytes length must be positive non-zero int")

        self.n = n

    def format(self) -> str:
        return f"{self.n}s"

    def validate_default(self, val: bytes) -> None:
        if len(val) > self.n:
            raise ValueError(f"bytes cannot be longer than {self.n} bytes")

    def __repr__(self) -> str:
        return f"{super().__repr__()}({self.n})"


class _NestedField(Field):
    field_type: type[DataclassStructProtocol]

    def __init__(self, cls: type[DataclassStructProtocol]):
        self.field_type = cls

    def format(self) -> str:
        # Return the format without the byteorder specifier at the beginning
        return self.field_type.__dataclass_struct__.format[1:]


def _validate_and_parse_field(
    cls: type,
    name: str,
    field_type: type,
    is_native: bool,
    validate_defaults: bool,
    mode: str,
) -> tuple[str, type]:
    """
    name is the name of the attribute, f is its type annotation.
    """

    if get_origin(field_type) == Annotated:
        # The types defined in .types (e.g. U32, F32, etc.) are of the form:
        #     Annotated[<builtin type>, Field(<field args>)]
        # Alternatively, accept annotations of the form:
        #     Annotated[<builtin type>, PadBefore(<size>), PadAfter(<size>)]
        # or:
        #     Annotated[<dcs.types type>, PadBefore(<size>), PadAfter(<size>)]
        # or:
        #     Annotated[bytes, <positive non-zero integer>]
        # which will expand to:
        #     Annotated[
        #         <builtin type associated with dcs.types type>,
        #         Field(<field args>),
        #         PadBefore(<size>),
        #         PadAfter(<size>),
        #     ]
        # PadBefore and PadAfter are optional and may be repeated or in
        # different orders
        type_, *fields = get_args(field_type)
        pad_before, pad_after, field = _get_padding_and_field(fields)
    else:
        # Accept type annotations without Annotated e.g. builtin types or
        # nested dataclass-structs
        pad_before = pad_after = 0
        type_ = field_type
        field = None

    if field is None:
        # Must be either a nested type or one of the supported builtins
        if is_dataclass_struct(type_):
            nested_mode = type_.__dataclass_struct__.mode
            if nested_mode != mode:
                size, byteorder = _MODE_CHAR_SIZE_BYTEORDER[nested_mode]
                exp_size, exp_byteorder = _MODE_CHAR_SIZE_BYTEORDER[mode]
                msg = (
                    "byteorder and size of nested dataclass-struct does not "
                    f"match that of container (expected '{exp_size}' size and "
                    f"'{exp_byteorder}' byteorder, got '{size}' size and "
                    f"'{byteorder}' byteorder)"
                )
                raise TypeError(msg)
            field = _NestedField(type_)
        else:
            field = builtin_fields.get(type_)
            if field is None:
                raise TypeError(f"type not supported: {field_type}")

    if not isinstance(field, Field):
        if issubclass(type_, bytes):
            # Annotated[bytes, <positive non-zero integer>] is a byte array
            field = _BytesField(field)
        else:
            raise TypeError(f"invalid field annotation: {field!r}")
    elif not issubclass(type_, field.field_type):
        raise TypeError(f"type {type_} not supported for field: {field}")

    if is_native:
        if not field.is_native:
            raise TypeError(
                f"field {field} only supported in standard size mode"
            )
    elif not field.is_std:
        raise TypeError(f"field {field} only supported in native size mode")

    if validate_defaults and hasattr(cls, name):
        val = getattr(cls, name)
        if not isinstance(val, field.field_type):
            raise TypeError(
                "invalid type for field: expected "
                f"{field.field_type} got {type(val)}"
            )
        field.validate_default(val)

    return (
        "".join(
            (
                (f"{pad_before}x" if pad_before else ""),
                field.format(),
                (f"{pad_after}x" if pad_after else ""),
            )
        ),
        type_,
    )


def _make_pack_method() -> Callable:
    func = """
def pack(self) -> bytes:
    '''Pack to bytes using struct.pack.'''
    return self.__dataclass_struct__.pack(self)
"""

    scope: dict[str, Any] = {}
    exec(func, {}, scope)
    return scope["pack"]


def _make_unpack_method(cls: type) -> classmethod:
    func = """
def from_packed(cls, data: bytes) -> cls_type:
    '''Unpack from bytes.'''
    return cls.__dataclass_struct__.unpack(data)
"""

    scope: dict[str, Any] = {"cls_type": cls}
    exec(func, {}, scope)
    return classmethod(scope["from_packed"])


def _make_class(
    cls: type,
    mode: str,
    is_native: bool,
    validate_defaults: bool,
    dataclass_kwargs,
) -> type[DataclassStructProtocol]:
    cls_annotations = get_type_hints(cls, include_extras=True)
    struct_format = [mode]
    fieldtypes = []
    for name, field in cls_annotations.items():
        fmt, type_ = _validate_and_parse_field(
            cls,
            name=name,
            field_type=field,
            is_native=is_native,
            validate_defaults=validate_defaults,
            mode=mode,
        )
        struct_format.append(fmt)
        fieldtypes.append(type_)

    setattr(  # noqa: B010
        cls,
        "__dataclass_struct__",
        _DataclassStructInternal(
            "".join(struct_format),
            cls,
            list(cls_annotations.keys()),
            fieldtypes,
        ),
    )
    setattr(cls, "pack", _make_pack_method())  # noqa: B010
    setattr(cls, "from_packed", _make_unpack_method(cls))  # noqa: B010

    return dataclasses.dataclass(cls, **dataclass_kwargs)


class _DataclassKwargsPre310(TypedDict, total=False):
    init: bool
    repr: bool
    eq: bool
    order: bool
    unsafe_hash: bool
    frozen: bool


if sys.version_info >= (3, 10):

    class DataclassKwargs(_DataclassKwargsPre310, total=False):
        match_args: bool
        kw_only: bool
else:

    class DataclassKwargs(_DataclassKwargsPre310, total=False):
        pass


@overload
def dataclass_struct(
    *,
    size: Literal["native"] = "native",
    byteorder: Literal["native"] = "native",
    validate_defaults: bool = True,
    **dataclass_kwargs: Unpack[DataclassKwargs],
) -> Callable[[type], type]: ...


@overload
def dataclass_struct(
    *,
    size: Literal["std"],
    byteorder: Literal["native", "big", "little", "network"] = "native",
    validate_defaults: bool = True,
    **dataclass_kwargs: Unpack[DataclassKwargs],
) -> Callable[[type], type]: ...


@dataclass_transform()
def dataclass_struct(
    *,
    size: Literal["native", "std"] = "native",
    byteorder: Literal["native", "big", "little", "network"] = "native",
    validate_defaults: bool = True,
    **dataclass_kwargs: Unpack[DataclassKwargs],
) -> Callable[[type], type]:
    """Create a dataclass struct.

    Should be used as a decorator on a class:

    ```python
    import dataclasses_struct as dcs

    @dcs.dataclass_struct()
    class A:
        data: dcs.Pointer
        size: dcs.UnsignedSize
    ```

    The allowed `size` and `byteorder` argument combinations are as as follows.

    | `size`     | `byteorder` | Notes                                                               |
    | ---------- | ----------- | ------------------------------------------------------------------  |
    | `"native"` | `"native"`  | The default. Native alignment and padding.                          |
    | `"std"`    | `"native"`  | Standard integer sizes and system endianness, no alignment/padding. |
    | `"std"`    | `"little"`  | Standard integer sizes and little endian, no alignment/padding.     |
    | `"std"`    | `"big"`     | Standard integer sizes and big endian, no alignment/padding.        |
    | `"std"`    | `"network"` | Equivalent to `byteorder="big"`.                                    |

    Args:
        size: The size mode.
        byteorder: The byte order of the generated struct. If `size="native"`,
            only `"native"` is allowed.
        validate_defaults: Whether to validate the default values of any
            fields.
        dataclass_kwargs: Any additional keyword arguments to pass to the
            [stdlib
            `dataclass`](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass)
            decorator. The `slots` and `weakref_slot` keyword arguments are not
            supported.

    Raises:
        ValueError: If the `size` and `byteorder` args are invalid or if
            `validate_defaults=True` and any of the fields' default values are
            invalid for their type.
        TypeError: If any of the fields' type annotations are invalid or
            not supported.
    """  # noqa: E501
    is_native = size == "native"
    if is_native:
        if byteorder != "native":
            raise ValueError("'native' size requires 'native' byteorder")
    elif size != "std":
        raise ValueError(f"invalid size: {size}")
    if byteorder not in ("native", "big", "little", "network"):
        raise ValueError(f"invalid byteorder: {byteorder}")

    for kwarg in ("slots", "weakref_slot"):
        if dataclass_kwargs.get(kwarg):
            msg = f"dataclass '{kwarg}' keyword argument is not supported"
            raise ValueError(msg)

    def decorator(cls: type) -> type:
        return _make_class(
            cls,
            mode=_SIZE_BYTEORDER_MODE_CHAR[(size, byteorder)],
            is_native=is_native,
            validate_defaults=validate_defaults,
            dataclass_kwargs=dataclass_kwargs,
        )

    return decorator
