#

# Test the default panel implementation.
#

import pytest

from sr2 import Block
import param

class SimpleBlock(Block):
    """A very simple block."""

    in_p = param.String()
    out_p = param.String()

def test_no_panel():
    """A block has no default panel implementation."""

    b = SimpleBlock()

    assert hasattr(b, '__panel__')
    assert not hasattr(b, '_panel')

def test_has_panel():
    """A block defines its own panel implementation."""

    b = SimpleBlock()
    p = b.__panel__()

    assert hasattr(b, '_panel')
