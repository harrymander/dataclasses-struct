from collections.abc import Callable

from mypy.nodes import Argument, ArgKind, Var
from mypy.plugin import ClassDefContext, Plugin as BasePlugin
from mypy.plugins.common import add_attribute_to_class, add_method_to_class
from mypy.types import TypeVarType


DATACLASS_STRUCT_DECORATOR = 'dataclasses_struct.dataclass.dataclass'


def transform_dataclass_struct(ctx: ClassDefContext) -> bool:
    bytes_type = ctx.api.named_type('builtins.bytes')
    tvd = TypeVarType(
        'T',
        f'{ctx.cls.info.fullname}.T',
        -1,
        [],
        ctx.api.named_type('builtins.object')
    )
    add_method_to_class(ctx.api, ctx.cls, 'pack', [], bytes_type)
    add_method_to_class(
        ctx.api,
        ctx.cls,
        'from_packed',
        [Argument(Var('data', bytes_type), bytes_type, None, ArgKind.ARG_POS)],
        tvd,
        self_type=tvd,
        tvar_def=tvd,
        is_classmethod=True,
    )
    add_attribute_to_class(
        ctx.api,
        ctx.cls,
        '__dataclass_struct__',
        ctx.api.named_type('struct.Struct'),
        is_classvar=True,
    )

    return True


class Plugin(BasePlugin):
    def get_class_decorator_hook_2(
        self, fullname: str
    ) -> Callable[[ClassDefContext], bool] | None:
        if fullname == DATACLASS_STRUCT_DECORATOR:
            return transform_dataclass_struct
        return None


def plugin(version: str) -> type[Plugin]:
    return Plugin
