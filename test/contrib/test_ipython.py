import sys

import pytest
import rich


# @pytest.fixture()
# def no_rich():
#     sys.modules['rich'] = None
#     yield
#     del sys.modules['rich']


# @pytest.fixture()
# def reset_import(scope='module'):
#     keys = [
#         k for k in sys.modules.keys() if k.startswith('dataclasses_struct')
#     ]
#     for k in keys:
#         del sys.modules[keys]


# @pytest.mark.usefixtures('no_rich')
def test_fail_no_rich():
    sys.modules['rich'] = None
    from dataclasses_struct.contrib.ipython import init_pretty_repr
    sys.modules['rich'] = rich

    with pytest.raises(
        RuntimeError,
        match='^rich formatter requires the rich package to be installed'
    ):
        init_pretty_repr('rich')


def test_no_repr_pretty_attr_by_default() -> None:
    import dataclasses_struct as dcs

    @dcs.dataclass()
    class Struct:
        x: int

    assert not hasattr(Struct, '_repr_pretty_')
    assert not hasattr(Struct(1), '_repr_pretty_')


@pytest.mark.parametrize('formatter', [None, 'auto', 'pprint', 'rich'])
def test_repr_pretty_attr(formatter) -> None:
    import dataclasses_struct as dcs
    from dataclasses_struct.contrib.ipython import init_pretty_repr

    if formatter is None:
        init_pretty_repr()
    else:
        init_pretty_repr(formatter)

    @dcs.dataclass()
    class Struct:
        x: int

    assert hasattr(Struct, '_repr_pretty_')
    assert hasattr(Struct(1), '_repr_pretty_')
