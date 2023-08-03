import pprint
from shutil import get_terminal_size
from typing import Callable, Literal

import dataclasses_struct

try:
    from rich.console import Console as RichConsole  # type: ignore
    rich_available = True
except ModuleNotFoundError:
    rich_available = False


def _pprint_method(*, width=None, **kwargs) -> Callable:
    def repr(self, p, cycle):
        p.text(pprint.pformat(
            self,
            width=width or get_terminal_size().columns,
            **kwargs
        ).strip())

    return repr


def _rich_method(**kwargs: dict) -> Callable:
    def repr(self, p, cycle):
        console = RichConsole(**kwargs)
        with console.capture() as cap:
            console.print(self)
        p.text(cap.get().strip())

    return repr


_FORMATTERS = ('auto', 'rich', 'pprint')


def init_pretty_repr(
    formatter: Literal['auto', 'rich', 'pprint'] = 'auto',
    **kwargs,
) -> None:
    """
    Add IPython/Jupyter Notebook-compatible pretty reprs to all classes
    decorated with `dataclasses_struct.dataclass`.

    When called before calling `dataclasses_struct.dataclass`, will patch
    `dataclasses_struct._dataclass` to add a `_repr_pretty_` method to any
    generated dataclass-structs. This will override the __repr__ method in the
    IPython shell or Jupyter notebooks (and any other environments that use
    `_repr_pretty_`).

    By default, uses `rich` (https://pypi.org/project/rich/) to generate the
    pretty-formatted representation, if available. Otherwise falls back to
    `pprint` from the stdlib.

    Args:
        formatter: One of 'auto', 'rich', 'pprint'. If 'auto', will use `rich`
            unless it is not available, in which case will use 'pprint'.
        kwargs: Keyword arguments to pass to `rich.console.Console` or
            `pprint.format`. If using `pprint`, the `width` argument will be
            automatically determined from the terminal width unless provided
            explicitly.

    Raises:
        RuntimeError: if `formatter` is 'rich' and `rich` is not installed.
    """
    if formatter not in _FORMATTERS:
        raise ValueError(
            f'invalid formatter; must be one of {", ".join(_FORMATTERS)}'
        )

    if formatter == 'rich' and not rich_available:
        raise RuntimeError(
            'rich formatter requires the rich package to be installed'
        )

    if formatter == 'auto':
        formatter = 'rich' if rich_available else 'pprint'

    method = (
        _rich_method(**kwargs) if formatter == 'rich'
        else _pprint_method(**kwargs)
    )

    old_make_class = dataclasses_struct._dataclass._make_class

    def _make_class(*args, **kwargs):
        cls = old_make_class(*args, **kwargs)
        setattr(cls, '_repr_pretty_', method)
        return cls

    dataclasses_struct._dataclass._make_class = _make_class
