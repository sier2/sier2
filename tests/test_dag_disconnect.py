import pytest

from sr2 import Block, BlockState, Dag, Connections, BlockError, Library, BlockValidateError
from sr2._dag import _is_connected
import param

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-dag', title='tests')

class PassThrough(Block):
    """Pass a value through unchanged."""

    in_p1 = param.Integer(default=0)
    in_p2 = param.Integer(default=0)
    out_p1 = param.Integer(default=0)
    out_p2 = param.Integer(default=0)

    def execute(self):
        self.out_p1 = self.in_p1
        self.out_p2 = self.in_p2

def test_good(dag):
    """Blocks can lgally be disconnected from the dag."""

    b1 = PassThrough()
    b2 = PassThrough()
    b3 = PassThrough()

    dag.connect(b1, b2, Connections({
        'out_p1': 'in_p1',
        'out_p2': 'in_p2'
    }))

    dag.connect(b2, b3, Connections({
        'out_p1': 'in_p1',
        'out_p2': 'in_p2'
    }))

    assert (b1, b2) in dag._block_pairs
    assert (b2, b3) in dag._block_pairs

    dag.disconnect(b1)
    assert (b1, b2) not in dag._block_pairs
    assert (b2, b3) in dag._block_pairs

    dag.disconnect(b2)
    assert not dag._block_pairs

def test_bad(dag):
    """Ensure that attempting to remove a block that will cause the dag to become disconnected will fail."""

    b1 = PassThrough(name='PT1')
    b2 = PassThrough(name='PT2')
    b3 = PassThrough(name='PT3')
    b4 = PassThrough(name='PT4')
    b5 = PassThrough(name='PT5')

    dag.connect(b1, b2, Connections({
        'out_p1': 'in_p1',
        'out_p2': 'in_p2'
    }))

    dag.connect(b2, b3, Connections({
        'out_p1': 'in_p1',
        'out_p2': 'in_p2'
    }))

    dag.connect(b3, b4, Connections({
        'out_p1': 'in_p1',
        'out_p2': 'in_p2'
    }))

    dag.connect(b4, b5, Connections({
        'out_p1': 'in_p1',
        'out_p2': 'in_p2'
    }))

    with pytest.raises(BlockError):
        dag.disconnect(b3)

    assert (b1, b2) in dag._block_pairs
    assert (b2, b3) in dag._block_pairs
    assert (b3, b4) in dag._block_pairs
    assert (b4, b5) in dag._block_pairs

def test_connected_good1():
    pairs = [('a', 'b'), ('b', 'c'), ('c', 'd')]
    assert _is_connected(pairs)

def test_connected_good2():
    pairs = [('a', 'b'), ('c', 'a')]
    assert _is_connected(pairs)

def test_connected_bad():
    pairs = [('a', 'b'), ('c', 'd')]
    assert not _is_connected(pairs)
