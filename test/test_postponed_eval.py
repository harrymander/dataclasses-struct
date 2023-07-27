from __future__ import annotations

from typing_extensions import Annotated

import dataclasses_struct as dcs


def test_postponed() -> None:
    @dcs.dataclass()
    class _:
        a: dcs.Char
        b: dcs.I8
        c: dcs.U8
        d: dcs.Bool
        e: dcs.I16
        f: dcs.U16
        g: dcs.I32
        h: dcs.U32
        i: dcs.I64
        j: dcs.U64
        k: dcs.F32
        l: dcs.F64
        m: Annotated[bytes, dcs.BytesField(10)]
        n: dcs.Size
        o: dcs.SSize
        p: dcs.Pointer
