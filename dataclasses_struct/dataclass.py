import dataclasses
import sys
from collections.abc import Generator, Iterator
from struct import Struct
from types import GenericAlias
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


class _DataclassStructInternal(Generic[T]):
    struct: Struct
    cls: type[T]
    _fieldnames: list[str]
    _fields: list[tuple[Field[Any], type]]

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
        fields: list[tuple[Field[Any], type]],
    ):
        self.struct = Struct(fmt)
        self.cls = cls
        self._fieldnames = fieldnames
        self._fields = fields

    def _flattened_attrs(self, outer_self: T) -> list[Any]:
        """
        Returns a list of all attributes of `outer_self`, including those of
        any nested structs.
        """
        attrs: list[Any] = []
        for fieldname in self._fieldnames:
            attr = getattr(outer_self, fieldname)
            self._flatten_attr(attrs, attr)
        return attrs

    @staticmethod
    def _flatten_attr(attrs: list[Any], attr: object) -> None:
        if is_dataclass_struct(attr):
            attrs.extend(attr.__dataclass_struct__._flattened_attrs(attr))
        elif isinstance(attr, list):
            for sub_attr in attr:
                _DataclassStructInternal._flatten_attr(attrs, sub_attr)
        else:
            attrs.append(attr)

    def pack(self, obj: T) -> bytes:
        return self.struct.pack(*self._flattened_attrs(obj))

    def _arg_generator(self, args: Iterator) -> Generator:
        for field, fieldtype in self._fields:
            yield from _DataclassStructInternal._generate_args_recursively(
                args, field, fieldtype
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
                    _DataclassStructInternal._generate_args_recursively(
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
        return self.cls(
            **{
                fieldname: arg
                for fieldname, arg in zip(
                    self._fieldnames, self._arg_generator(args)
                )
            }
        )

    def unpack(self, data: bytes) -> T:
        return self._init_from_args(iter(self.struct.unpack(data)))


class DataclassStructProtocol(Protocol):
    __dataclass_struct__: _DataclassStructInternal

    @classmethod
    def from_packed(cls: type[T], data: bytes) -> T: ...

    def pack(self) -> bytes: ...


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
    """
    Returns True if obj is a class that has been decorated with
    dataclasses_struct.dataclass or an instance of one.
    """
    return (
        dataclasses.is_dataclass(obj)
        and hasattr(obj, "__dataclass_struct__")
        and isinstance(obj.__dataclass_struct__, _DataclassStructInternal)
    )


def get_struct_size(cls_or_obj) -> int:
    """
    Returns the size of the packed representation of the struct in bytes.
    Accepts either a class or an instance of a dataclass_struct.
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


def _validate_and_parse_field(
    cls: type,
    name: str,
    field_type: type,
    is_native: bool,
    validate_defaults: bool,
    mode: str,
) -> tuple[str, Field, type]:
    field, type_, pad_before, pad_after = _resolve_field(field_type, mode)

    if is_native:
        if not field.is_native:
            raise TypeError(
                f"field {field} only supported in standard size mode"
            )
    elif not field.is_std:
        raise TypeError(f"field {field} only supported in native size mode")

    if validate_defaults and hasattr(cls, name):
        val = getattr(cls, name)
        if not isinstance(field.field_type, GenericAlias) and not isinstance(
            val, field.field_type
        ):
            raise TypeError(
                "invalid type for field: expected "
                f"{field.field_type} got {type(val)}"
            )
        field.validate_default(val)

    return (
        _format_str_with_padding(field.format(), pad_before, pad_after),
        field,
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
    fields = []
    for name, field in cls_annotations.items():
        if field is _KW_ONLY_MARKER:
            # KW_ONLY is handled by stdlib dataclass, nothing to do on our end.
            continue

        fmt, field, type_ = _validate_and_parse_field(
            cls,
            name=name,
            field_type=field,
            is_native=is_native,
            validate_defaults=validate_defaults,
            mode=mode,
        )
        struct_format.append(fmt)
        fields.append((field, type_))

    setattr(  # noqa: B010
        cls,
        "__dataclass_struct__",
        _DataclassStructInternal(
            "".join(struct_format),
            cls,
            list(cls_annotations.keys()),
            fields,
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
