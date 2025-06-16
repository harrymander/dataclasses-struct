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

if sys.version_info >= (3, 10):
    from dataclasses import KW_ONLY as _KW_ONLY_MARKER
else:
    # Placeholder for KW_ONLY on Python 3.9

    class _KW_ONLY_MARKER_TYPE:
        pass

    _KW_ONLY_MARKER = _KW_ONLY_MARKER_TYPE()


def _separate_padding_from_annotation_args(args) -> tuple[int, int, object]:
    pad_before = pad_after = 0
    extra_arg = None  # should be Field or integer for bytes/list types
    for arg in args:
        if isinstance(arg, PadBefore):
            pad_before += arg.size
        elif isinstance(arg, PadAfter):
            pad_after += arg.size
        elif extra_arg is not None:
            raise TypeError(f"too many annotations: {arg}")
        else:
            extra_arg = arg

    return pad_before, pad_after, extra_arg


def _format_str_with_padding(fmt: str, pad_before: int, pad_after: int) -> str:
    return "".join(
        (
            (f"{pad_before}x" if pad_before else ""),
            fmt,
            (f"{pad_after}x" if pad_after else ""),
        )
    )


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


@dataclasses.dataclass
class _FieldInfo:
    name: str
    field: Field[Any]
    type_: type
    init: bool


class DataclassStructInternal(Generic[T]):
    struct: Struct
    cls: type[T]
    _fields: list[_FieldInfo]

    @property
    def format(self) -> str:
        """
        The format string used by the `struct` module to pack/unpack data.

        See https://docs.python.org/3/library/struct.html#format-strings.
        """
        return self.struct.format

    @property
    def size(self) -> int:
        """Size of the packed representation in bytes."""
        return self.struct.size

    @property
    def mode(self) -> str:
        """
        The `struct` mode character that determines size, alignment, and
        byteorder.

        This is the first character of the `format` field. See
        https://docs.python.org/3/library/struct.html#byte-order-size-and-alignment
        for more info.
        """
        return self.format[0]

    def __init__(
        self,
        fmt: str,
        cls: type,
        fields: list[_FieldInfo],
    ):
        self.struct = Struct(fmt)
        self.cls = cls
        self._fields = fields

    def _flattened_attrs(self, outer_self: T) -> list[Any]:
        """
        Returns a list of all attributes of `outer_self`, including those of
        any nested structs.
        """
        attrs: list[Any] = []
        for field in self._fields:
            attr = getattr(outer_self, field.name)
            self._flatten_attr(attrs, attr)
        return attrs

    @staticmethod
    def _flatten_attr(attrs: list[Any], attr: object) -> None:
        if is_dataclass_struct(attr):
            attrs.extend(attr.__dataclass_struct__._flattened_attrs(attr))
        elif isinstance(attr, list):
            for sub_attr in attr:
                DataclassStructInternal._flatten_attr(attrs, sub_attr)
        else:
            attrs.append(attr)

    def _pack(self, obj: T) -> bytes:
        return self.struct.pack(*self._flattened_attrs(obj))

    def _arg_generator(self, args: Iterator) -> Generator:
        for field in self._fields:
            yield from DataclassStructInternal._generate_args_recursively(
                args, field.field, field.type_
            )

    @staticmethod
    def _generate_args_recursively(
        args: Iterator,
        field: Field[Any],
        field_type: type,
    ) -> Generator:
        if is_dataclass_struct(field_type):
            yield field_type.__dataclass_struct__._init_from_args(args)
        elif isinstance(field, _FixedLengthArrayField):
            items: list = []
            for _ in range(field.n):
                items.extend(
                    DataclassStructInternal._generate_args_recursively(
                        args, field.item_field, field.item_type
                    )
                )
            yield items
        else:
            yield field_type(next(args))

    def _init_from_args(self, args: Iterator) -> T:
        """
        Returns an instance of self.cls, consuming args
        """
        kwargs = {}
        no_init_args = {}

        for field, arg in zip(self._fields, self._arg_generator(args)):
            if field.init:
                kwargs[field.name] = arg
            else:
                no_init_args[field.name] = arg

        obj = self.cls(**kwargs)
        for name, arg in no_init_args.items():
            setattr(obj, name, arg)
        return obj

    def _unpack(self, data: bytes) -> T:
        return self._init_from_args(iter(self.struct.unpack(data)))


class DataclassStructProtocol(Protocol):
    __dataclass_struct__: DataclassStructInternal
    """
    Internal data used by the library for packing and unpacking structs.

    See
    [`DataclassStructInternal`][dataclasses_struct.DataclassStructInternal].
    """

    @classmethod
    def from_packed(cls: type[T], data: bytes) -> T:
        """Return an instance of the class from its packed representation.

        Args:
            data: The packed representation of the class as returned by
                [`pack`][dataclasses_struct.DataclassStructProtocol.pack].

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
                [`from_packed`][dataclasses_struct.DataclassStructProtocol.from_packed].

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
            [`dataclass_struct`][dataclasses_struct.dataclass_struct] or is an
            instance of one.
    """
    return (
        dataclasses.is_dataclass(obj)
        and hasattr(obj, "__dataclass_struct__")
        and isinstance(obj.__dataclass_struct__, DataclassStructInternal)
    )


def get_struct_size(cls_or_obj: object) -> int:
    """Get the size of the packed representation of the struct in bytes.

    Args:
        cls_or_obj: A class that has been decorated with
            [`dataclass_struct`][dataclasses_struct.dataclass_struct] or an
            instance of one.

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

    def __init__(self, n: object):
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


class _FixedLengthArrayField(Field[list]):
    field_type = list

    def __init__(self, item_type_annotation: Any, mode: str, n: object):
        if not isinstance(n, int) or n < 1:
            raise ValueError(
                "fixed-length array length must be positive non-zero int"
            )

        self.item_field, self.item_type, self.pad_before, self.pad_after = (
            _resolve_field(item_type_annotation, mode)
        )
        self.n = n
        self.is_native = self.item_field.is_native
        self.is_std = self.item_field.is_std

    def format(self) -> str:
        fmt = _format_str_with_padding(
            self.item_field.format(),
            self.pad_before,
            self.pad_after,
        )
        return fmt * self.n

    def __repr__(self) -> str:
        return f"{super().__repr__()}({self.item_field!r}, {self.n})"

    def validate_default(self, val: list) -> None:
        n = len(val)
        if n != self.n:
            msg = f"fixed-length array must have length of {self.n}, got {n}"
            raise ValueError(msg)

        for i in val:
            _validate_field_default(self.item_field, i)


def _validate_modes_match(mode: str, nested_mode: str) -> None:
    if mode != nested_mode:
        size, byteorder = _MODE_CHAR_SIZE_BYTEORDER[nested_mode]
        exp_size, exp_byteorder = _MODE_CHAR_SIZE_BYTEORDER[mode]
        msg = (
            "byteorder and size of nested dataclass-struct does not "
            f"match that of container (expected '{exp_size}' size and "
            f"'{exp_byteorder}' byteorder, got '{size}' size and "
            f"'{byteorder}' byteorder)"
        )
        raise TypeError(msg)


def _resolve_field(
    annotation: Any,
    mode: str,
) -> tuple[Field[Any], type, int, int]:
    """
    Returns 4-tuple of:
    * field
    * type
    * number of padding bytes before
    * number of padding bytes after

    Valid type annotations are:

    1. <bool | int | float | bytes> | Annotated[<bool | int | float | bytes>, <padding>]

       Supported builtin types.

    2. Annotated[<bool | int | float | bytes>, Field(...), <padding>]

       (These are the types defined in dataclasses_struct.types e.g. U32, F32).

    3. <dataclasses_struct class> | Annotated[<dataclasses_struct class>, <padding>]

       Must have the same size and byteorder as the container.

    4. Annotated[bytes, <n>, <padding>]

       Where <n> is >0.

    5. Annotated[list[<type>], <n>, <padding>]

       Where <n> is >0 and <type> is one of the above.

    <padding> is an optional mixture of PadBefore and PadAfter annotations,
    which may be repeated. E.g.

      Annotated[int, PadBefore(5), PadAfter(2), PadBefore(3)]
    """  # noqa: E501

    if get_origin(annotation) == Annotated:
        type_, *args = get_args(annotation)
        pad_before, pad_after, annotation_arg = (
            _separate_padding_from_annotation_args(args)
        )
    else:
        pad_before = pad_after = 0
        type_ = annotation
        annotation_arg = None

    field: Field[Any]
    if annotation_arg is None:
        if get_origin(type_) is list:
            msg = (
                "list types must be marked as a fixed-length using "
                "Annotated, ex: Annotated[list[int], 5]"
            )
            raise TypeError(msg)

        # Must be either a nested type or one of the supported builtins
        if is_dataclass_struct(type_):
            _validate_modes_match(mode, type_.__dataclass_struct__.mode)
            field = _NestedField(type_)
        else:
            opt_field = builtin_fields.get(type_)
            if opt_field is None:
                raise TypeError(f"type not supported: {annotation}")
            field = opt_field
    elif isinstance(annotation_arg, Field):
        field = annotation_arg
    elif get_origin(type_) is list:
        item_annotations = get_args(type_)
        assert len(item_annotations) == 1
        field = _FixedLengthArrayField(
            item_annotations[0], mode, annotation_arg
        )
    elif issubclass(type_, bytes):
        field = _BytesField(annotation_arg)
    else:
        raise TypeError(f"invalid field annotation: {annotation!r}")

    return field, type_, pad_before, pad_after


def _get_default_from_dataclasses_field(field: dataclasses.Field) -> Any:
    if field.default is not dataclasses.MISSING:
        return field.default

    if field.default_factory is not dataclasses.MISSING:
        return field.default_factory()

    return dataclasses.MISSING


def _validate_field_default(field: Field[T], val: Any) -> None:
    if not isinstance(val, field.field_type):
        msg = (
            "invalid type for field: expected "
            f"{field.field_type} got {type(val)}"
        )
        raise TypeError(msg)

    field.validate_default(val)


def _validate_and_parse_field(
    cls: type,
    *,
    name: str,
    field_type: type,
    is_native: bool,
    validate_defaults: bool,
    mode: str,
    init: bool,
) -> tuple[str, _FieldInfo]:
    """Returns format string and info."""
    field, type_, pad_before, pad_after = _resolve_field(field_type, mode)

    if is_native:
        if not field.is_native:
            raise TypeError(
                f"field {field} only supported in standard size mode"
            )
    elif not field.is_std:
        raise TypeError(f"field {field} only supported in native size mode")

    init_field = init
    if hasattr(cls, name):
        val = getattr(cls, name)
        if isinstance(val, dataclasses.Field):
            if not val.init:
                init_field = False

            if validate_defaults:
                val = _get_default_from_dataclasses_field(val)

        if validate_defaults and val is not dataclasses.MISSING:
            _validate_field_default(field, val)

    return (
        _format_str_with_padding(field.format(), pad_before, pad_after),
        _FieldInfo(name, field, type_, init_field),
    )


def _make_pack_method() -> Callable:
    func = """
def pack(self) -> bytes:
    '''Pack to bytes using struct.pack.'''
    return self.__dataclass_struct__._pack(self)
"""

    scope: dict[str, Any] = {}
    exec(func, {}, scope)
    return scope["pack"]


def _make_unpack_method(cls: type) -> classmethod:
    func = """
def from_packed(cls, data: bytes) -> cls_type:
    '''Unpack from bytes.'''
    return cls.__dataclass_struct__._unpack(data)
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
    fields: list[_FieldInfo] = []
    init = dataclass_kwargs.get("init", True)
    for name, field in cls_annotations.items():
        if field is _KW_ONLY_MARKER:
            # KW_ONLY is handled by stdlib dataclass, nothing to do on our end.
            continue

        fmt, field = _validate_and_parse_field(
            cls,
            name=name,
            field_type=field,
            is_native=is_native,
            validate_defaults=validate_defaults,
            mode=mode,
            init=init,
        )
        struct_format.append(fmt)
        fields.append(field)

    setattr(  # noqa: B010
        cls,
        "__dataclass_struct__",
        DataclassStructInternal("".join(struct_format), cls, fields),
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
        if kwarg in dataclass_kwargs:
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
