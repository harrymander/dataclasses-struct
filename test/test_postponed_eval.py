from __future__ import annotations

from typing_extensions import Annotated

import dataclasses_struct as dcs


def test_postponed() -> None:
    @dcs.dataclass()
    class _:
        a: dcs.Char
        b: dcs.Int8
        c: dcs.Uint8
        d: dcs.Bool
        e: dcs.Int16
        f: dcs.Uint16
        g: dcs.Int32
        h: dcs.Uint32
        i: dcs.Int64
        j: dcs.Uint64
        k: dcs.Float32
        l: dcs.Float
        m: dcs.Float64
        n: dcs.Double
        q: Annotated[bytes, dcs.BytesField(10)]
        r: dcs.Size
        s: dcs.SSize
        t: dcs.Pointer
