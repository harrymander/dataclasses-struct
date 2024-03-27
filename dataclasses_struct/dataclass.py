import dataclasses
from collections.abc import Generator, Iterator
from struct import Struct
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import (
    Annotated,
    TypeGuard,
    dataclass_transform,
    get_args,
    get_origin,
    get_type_hints,
)

from .field import BytesField, Field, primitive_fields
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
            raise TypeError(f'too many annotations: {f}')
        else:
            field = f

    return pad_before, pad_after, field


T = TypeVar('T')


_SIZE_ENDIAN_MODE_CHAR: dict[tuple[str, str], str] = {
    ('native', 'native'): '@',
    ('std', 'native'): '=',
    ('std', 'little'): '<',
    ('std', 'big'): '>',
    ('std', 'network'): '!',
}
_MODE_CHAR_SIZE_ENDIAN: dict[str, tuple[str, str]] = {
    v: k for k, v in _SIZE_ENDIAN_MODE_CHAR.items()
}


class _DataclassStructInternal(Generic[T]):
    struct: Struct
    cls: Type[T]
    _fieldnames: List[str]
    _fieldtypes: List[type]

    @property
    def format(self) -> str:
        return self.struct.format

    @property
    def size(self) -> int:
        return self.struct.size

    @property
    def mode_char(self) -> str:
        return self.format[0]

    def __init__(
        self,
        fmt: str,
        cls: type,
        fieldnames: List[str],
        fieldtypes: List[type],
    ):
        self.struct = Struct(fmt)
        self.cls = cls
        self._fieldnames = fieldnames
        self._fieldtypes = fieldtypes

    def _flattened_attrs(self, obj) -> List[Any]:
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

    @classmethod
    def from_packed(cls: Type[T], data: bytes) -> T: ...

    def pack(self) -> bytes: ...


@overload
def is_dataclass_struct(obj: type) -> TypeGuard[Type[DataclassStructProtocol]]:
    ...


@overload
def is_dataclass_struct(obj: Any) -> TypeGuard[DataclassStructProtocol]:
    ...


def is_dataclass_struct(obj: Union[type, Any]) -> Union[
    TypeGuard[DataclassStructProtocol],
    TypeGuard[Type[DataclassStructProtocol]]
]:
    """
    Returns True if obj is a class that has been decorated with
    dataclasses_struct.dataclass or an instance of one.
    """
    return (
        dataclasses.is_dataclass(obj)
        and hasattr(obj, '__dataclass_struct__')
        and isinstance(obj.__dataclass_struct__, _DataclassStructInternal)
    )


def get_struct_size(cls_or_obj: Any) -> int:
    """
    Returns the size of the packed representation of the struct in bytes.
    Accepts either a class or an instance of a dataclass_struct.
    """
    if not is_dataclass_struct(cls_or_obj):
        raise TypeError(f'{cls_or_obj} is not a dataclass_struct')
    return cls_or_obj.__dataclass_struct__.size


class _NestedField(Field):
    type_: Type[DataclassStructProtocol]

    def __init__(self, cls: Type[DataclassStructProtocol]):
        self.type_ = cls

    def format(self) -> str:
        # Return the format without the endian specifier at the beginning
        return self.type_.__dataclass_struct__.format[1:]


def _validate_and_parse_field(
    cls: type,
    name: str,
    field_type: Type[Any],
    is_native: bool,
    validate: bool,
    mode_char: str,
) -> Tuple[str, type]:
    """
    name is the name of the attribute, f is its type annotation.
    """

    if get_origin(field_type) == Annotated:
        # The types defined in .types (e.g. U32, F32, etc.) are of the form:
        #     Annotated[<primitive type>, Field(<field args>)]
        # Alternatively, accept annotations of the form:
        #     Annotated[<primitive type>, PadBefore(<size>), PadAfter(<size>)]
        # or:
        #     Annotated[<dcs.types type>, PadBefore(<size>), PadAfter(<size>)]
        # which will expand to:
        #     Annotated[
        #         <primitive type associated with dcs.types type>,
        #         Field(<field args>),
        #         PadBefore(<size>),
        #         PadAfter(<size>),
        #     ]
        # PadBefore and PadAfter are optional and may be repeated or in
        # different orders
        type_, *fields = get_args(field_type)
        pad_before, pad_after, field = _get_padding_and_field(fields)
    else:
        # Accept type annotations without Annotated e.g. primitive types or
        # nested dataclass-structs
        pad_before = pad_after = 0
        type_ = field_type
        field = None

    if field is None:
        # Must be either a nested type or one of the supported primitives
        if is_dataclass_struct(type_):
            nested_mode = type_.__dataclass_struct__.mode_char
            if nested_mode != mode_char:
                size, endian = _MODE_CHAR_SIZE_ENDIAN[mode_char]
                exp_size, exp_endian = _MODE_CHAR_SIZE_ENDIAN[nested_mode]
                msg = (
                    'endianness and size mode of nested dataclass-struct does '
                    f'not match that of container (expected {exp_size} size '
                    f'and {exp_endian} endian, got {size} size and '
                    f'{endian} endian)'
                )
                raise TypeError(msg)
            field = _NestedField(type_)
        else:
            field = primitive_fields.get(type_)
            if field is None:
                raise TypeError(f'type not supported: {field_type}')

    if issubclass(type_, bytes) and isinstance(field, int):
        # Annotated[bytes, <positive non-zero integer>] is a byte array
        field = BytesField(field)
    elif not isinstance(field, Field):
        raise TypeError(f'invalid field annotation: {field}')

    if not issubclass(type_, field.field_type):
        raise TypeError(f'type {type_} not supported for field: {field}')

    if is_native:
        if not field.is_native:
            raise TypeError(
                f'field {field} only support in standard size mode'
            )
    elif not field.is_std:
        raise TypeError(f'field {field} only supported in native size mode')

    if validate and hasattr(cls, name):
        val = getattr(cls, name)
        if not isinstance(val, field.field_type):
            raise TypeError(
                'invalid type for field: expected '
                f'{field.field_type} got {type(val)}'
            )
        field.validate(val)

    return (
        ''.join((
            (f'{pad_before}x' if pad_before else ''),
            field.format(),
            (f'{pad_after}x' if pad_after else ''),
        )),
        type_
    )


def _make_pack_method() -> Callable:
    func = """
def pack(self) -> bytes:
    '''Pack to bytes using struct.pack.'''
    return self.__dataclass_struct__.pack(self)
"""

    scope: Dict[str, Any] = {}
    exec(func, {}, scope)
    return scope['pack']


def _make_unpack_method(cls: type) -> classmethod:
    func = """
def from_packed(cls, data: bytes) -> cls_type:
    '''Unpack from bytes.'''
    return cls.__dataclass_struct__.unpack(data)
"""

    scope: Dict[str, Any] = {'cls_type': cls}
    exec(func, {}, scope)
    return classmethod(scope['from_packed'])


def _make_class(
    cls: type, mode_char: str, is_native: bool, validate: bool
) -> Type[DataclassStructProtocol]:
    cls_annotations = get_type_hints(cls, include_extras=True)
    struct_format = [mode_char]
    fieldtypes = []
    for name, field in cls_annotations.items():
        fmt, type_ = _validate_and_parse_field(
            cls,
            name=name,
            field_type=field,
            is_native=is_native,
            validate=validate,
            mode_char=mode_char,
        )
        struct_format.append(fmt)
        fieldtypes.append(type_)

    setattr(
        cls,
        '__dataclass_struct__',
        _DataclassStructInternal(
            ''.join(struct_format),
            cls,
            list(cls_annotations.keys()),
            fieldtypes,
        )
    )
    setattr(cls, 'pack', _make_pack_method())
    setattr(cls, 'from_packed', _make_unpack_method(cls))

    return dataclasses.dataclass(cls)


@overload
def dataclass(
    *,
    size: Literal['native'] = 'native',
    endian: Literal['native'] = 'native',
    validate: bool = ...
):
    ...


@overload
def dataclass(
    *,
    size: Literal['std'],
    endian: Literal['native', 'big', 'little', 'network'] = 'native',
    validate: bool = ...
):
    ...


@dataclass_transform()
def dataclass(
    *,
    size: Literal['native', 'std'] = 'native',
    endian: Literal['native', 'big', 'little', 'network'] = 'native',
    validate: bool = True,
) -> Callable[[type], type]:
    is_native = size == 'native'
    if is_native:
        if endian != 'native':
            raise TypeError("'native' size requires 'native' endian")
    elif size != 'std':
        raise TypeError(f'invalid size: {size}')
    if endian not in ('native', 'big', 'little', 'network'):
        raise TypeError(f'invalid endian: {endian}')

    def decorator(cls: type) -> type:
        return _make_class(
            cls,
            mode_char=_SIZE_ENDIAN_MODE_CHAR[(size, endian)],
            is_native=is_native,
            validate=validate,
        )

    return decorator
