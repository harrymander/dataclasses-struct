import sys

if sys.version_info >= (3, 10):
    from typing import TypeGuard
else:
    from typing_extensions import TypeGuard

if sys.version_info >= (3, 11):
    from typing import Unpack, dataclass_transform
else:
    from typing_extensions import Unpack, dataclass_transform

if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    from typing_extensions import Buffer


__all__ = [
    "Buffer",
    "TypeGuard",
    "Unpack",
    "dataclass_transform",
]
