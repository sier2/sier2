import pytest

from sr2 import Block, BlockState, Dag, Connection, BlockError, Library, BlockValidateError
from sr2 import _library
import param

class Block1(Block):
    """Any old block."""

    pass

def test_library_get():
    """The block key must be the same whether the block is imported or obtained via the Library."""

    b = Block1()
    # print(b.block_key())

    Library.add_block(Block1)

    # for entry_point, gi in _library._find_blocks():
    #     print(entry_point, gi)

    b_lib = Library.get_block('tests.test_library.Block1')
    # print(b_lib.block_key())

    assert b.block_key()==b_lib.block_key()
