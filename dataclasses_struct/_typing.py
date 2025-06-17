import sys

if sys.version_info >= (3, 10):
    from typing import TypeGuard
else:
    from typing_extensions import TypeGuard

if sys.version_info >= (3, 11):
    from typing import Self, Unpack, dataclass_transform
else:
    from typing_extensions import Self, Unpack, dataclass_transform


__all__ = [
    "Self",
    "TypeGuard",
    "Unpack",
    "dataclass_transform",
]
