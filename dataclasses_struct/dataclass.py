from collections.abc import Generator, Iterator
import dataclasses
import struct
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
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

from .field import primitive_fields, Field, BytesField
from .types import PadBefore, PadAfter


NATIVE_ENDIAN_ALIGNED = '@'
NATIVE_ENDIAN = '='
LITTLE_ENDIAN = '<'
BIG_ENDIAN = '>'
NETWORK_ENDIAN = '!'


ENDIANS = frozenset((
    NATIVE_ENDIAN_ALIGNED,
    NATIVE_ENDIAN,
    LITTLE_ENDIAN,
    BIG_ENDIAN,
    NETWORK_ENDIAN,
))


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


class _DataclassStructInternal(Generic[T]):
    struct: struct.Struct
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
    def endianness(self) -> str:
        return self.format[0]

    def __init__(
        self,
        fmt: str,
        cls: type,
        fieldnames: List[str],
        fieldtypes: List[type],
    ):
        self.struct = struct.Struct(fmt)
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
                yield next(args)

    def _init_from_args(self, args: Iterator) -> T:
        """
        Returns an instance of self.cls, consuming args
        """
        return self.cls(*self._arg_generator(args))

    def unpack(self, data: bytes) -> T:
        return self._init_from_args(iter(self.struct.unpack(data)))


class DataclassStructProtocol(Protocol):
    __dataclass_struct__: _DataclassStructInternal


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
    f: Type[Any],
    allow_native: bool,
    validate: bool,
    endianness: str,
) -> Tuple[str, type]:
    """
    name is the name of the attribute, f is its type annotation.
    """

    if get_origin(f) == Annotated:
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
        type_, *fields = get_args(f)
        pad_before, pad_after, field = _get_padding_and_field(fields)
    else:
        # Accept type annotations without Annotated e.g. primitive types or
        # nested dataclass-structs
        pad_before = pad_after = 0
        type_ = f
        field = None

    if field is None:
        # Must be either a nested type or one of the supported primitives
        if is_dataclass_struct(type_):
            nested_endian = type_.__dataclass_struct__.endianness
            if nested_endian != endianness:
                raise TypeError(
                    'endianness of contained dataclass-struct does not match '
                    'that of container (expected '
                    f'{endianness}, got {nested_endian})'
                )
            field = _NestedField(type_)
        else:
            field = primitive_fields.get(type_)
            if field is None:
                raise TypeError(f'type not supported: {f}')

    if issubclass(type_, bytes) and isinstance(field, int):
        # Annotated[bytes, <positive non-zero integer>] is a byte array
        field = BytesField(field)
    elif not isinstance(field, Field):
        raise TypeError(f'invalid field annotation: {field}')

    if not issubclass(type_, field.type_):
        raise TypeError(f'type {type_} not supported for field: {field}')

    if field.native_only and not allow_native:
        raise TypeError(f'field {field} only supported for native alignment')

    if validate and hasattr(cls, name):
        val = getattr(cls, name)
        if not isinstance(val, field.type_):
            raise TypeError(
                'invalid type for field: expected '
                f'{field.type_} got {type(val)}'
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
    cls: type, endian: str, allow_native: bool, validate: bool
) -> type:
    cls_annotations = get_type_hints(cls, include_extras=True)
    struct_format = [endian]
    fieldtypes = []
    for name, field in cls_annotations.items():
        fmt, type_ = _validate_and_parse_field(
            cls,
            name,
            field,
            allow_native,
            validate,
            endian,
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


@dataclass_transform()
def dataclass(
    endian: str = NATIVE_ENDIAN_ALIGNED,
    validate: bool = True,
) -> Callable[[type], type]:
    if endian not in ENDIANS:
        raise ValueError(
            f'invalid endianness: {endian}. '
            '(Did you forget to add parentheses: @dataclass()?)'
        )

    def decorator(cls: type) -> type:
        return _make_class(
            cls,
            endian,
            endian == NATIVE_ENDIAN_ALIGNED,
            validate
        )

    return decorator
