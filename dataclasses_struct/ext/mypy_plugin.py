from typing import Callable, Optional, Type

from mypy.nodes import Argument, ArgKind, Var
from mypy.plugin import ClassDefContext, Plugin as BasePlugin
from mypy.plugins.common import add_attribute_to_class, add_method_to_class
from mypy.plugins.dataclasses import dataclass_class_maker_callback
from mypy.types import TypeType, TypeVarType


DATACLASS_STRUCT_DECORATOR = 'dataclasses_struct.dataclass.dataclass'


def transform_dataclass_struct(ctx: ClassDefContext) -> bool:
    bytes_type = ctx.api.named_type('builtins.bytes')
    tvd = TypeVarType(
        'T',
        f'{ctx.cls.info.fullname}.T',
        -1,
        [],
        ctx.api.named_type('builtins.object'),
        ctx.api.named_type('builtins.object'),
    )
    add_method_to_class(ctx.api, ctx.cls, 'pack', [], bytes_type)
    add_method_to_class(
        ctx.api,
        ctx.cls,
        'from_packed',
        [Argument(Var('data', bytes_type), bytes_type, None, ArgKind.ARG_POS)],
        tvd,
        self_type=TypeType(tvd),
        tvar_def=tvd,
        is_classmethod=True,
    )
    add_attribute_to_class(
        ctx.api,
        ctx.cls,
        '__dataclass_struct__',
        ctx.api.named_type(
            'dataclasses_struct.dataclass._DataclassStructInternal'),
        is_classvar=True,
    )

    # Not sure if this is the right thing to do here... needed because
    # @dataclass_transform doesn't seem to work with mypy when using this
    # custom plugin.
    dataclass_class_maker_callback(ctx)

    return True


class Plugin(BasePlugin):
    def get_class_decorator_hook_2(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], bool]]:
        if fullname == DATACLASS_STRUCT_DECORATOR:
            return transform_dataclass_struct
        return None


def plugin(version: str) -> Type[Plugin]:
    return Plugin
