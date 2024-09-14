import sys

# get_type_hints adds the include_extras param in 3.9. get_args and get_origin
# are supported in Python 3.8 but won't work with Annotated, so need to also
# get them from typing_extensions.
if sys.version_info < (3, 9):
    from typing_extensions import (
        Annotated,
        get_args,
        get_origin,
        get_type_hints,
    )
else:
    from typing import Annotated, get_args, get_origin, get_type_hints

if sys.version_info < (3, 10):
    from typing_extensions import TypeGuard
else:
    from typing import TypeGuard

if sys.version_info < (3, 11):
    from typing_extensions import dataclass_transform
else:
    from typing import dataclass_transform


__all__ = [
    'Annotated',
    'TypeGuard',
    'dataclass_transform',
    'get_args',
    'get_origin',
    'get_type_hints',
]
