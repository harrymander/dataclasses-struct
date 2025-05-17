import dataclasses_struct as dcs
from dataclasses_struct import Annotated


def test_str_type_annotations() -> None:
    @dcs.dataclass_struct(size="std")
    class _:
        a: "dcs.Char"
        b: "dcs.I8"
        c: "dcs.U8"
        d: "dcs.Bool"
        e: "dcs.I16"
        f: "dcs.U16"
        g: "dcs.I32"
        h: "dcs.U32"
        i: "dcs.I64"
        j: "dcs.U64"
        k: "dcs.F32"
        l: "dcs.F64"  # noqa: E741
        m: "Annotated[bytes, 10]"
