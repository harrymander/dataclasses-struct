from typing import Callable, Optional

from mypy.nodes import ArgKind, Argument, Var
from mypy.plugin import ClassDefContext
from mypy.plugin import Plugin as BasePlugin
from mypy.plugins.common import add_attribute_to_class, add_method_to_class
from mypy.plugins.dataclasses import dataclass_class_maker_callback
from mypy.types import TypeType, TypeVarId, TypeVarType

DATACLASS_STRUCT_DECORATOR = "dataclasses_struct.dataclass.dataclass_struct"


def transform_dataclass_struct(ctx: ClassDefContext) -> bool:
    buffer_type = ctx.api.named_type("dataclasses_struct._typing.Buffer")
    bytes_type = ctx.api.named_type("builtins.bytes")
    tvd = TypeVarType(
        "T",
        f"{ctx.cls.info.fullname}.T",
        TypeVarId(-1),
        [],
        ctx.api.named_type("builtins.object"),
        ctx.api.named_type("builtins.object"),
    )
    add_method_to_class(ctx.api, ctx.cls, "pack", [], bytes_type)
    add_method_to_class(
        ctx.api,
        ctx.cls,
        "from_packed",
        [
            Argument(
                Var("data", buffer_type),
                buffer_type,
                None,
                ArgKind.ARG_POS,
            )
        ],
        tvd,
        self_type=TypeType(tvd),
        tvar_def=tvd,
        is_classmethod=True,
    )
    add_attribute_to_class(
        ctx.api,
        ctx.cls,
        "__dataclass_struct__",
        ctx.api.named_type(
            "dataclasses_struct.dataclass.DataclassStructInternal"
        ),
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


def plugin(version: str) -> type[Plugin]:
    return Plugin
