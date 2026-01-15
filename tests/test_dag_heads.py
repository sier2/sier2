import pytest

from sr2 import Block, BlockState, Dag, Connection, BlockError, Library, BlockValidateError
import param

class BlockA(Block):
    """A test block."""

    in_i = param.String()
    out_o = param.String()

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-dag', title='tests')

def test_ht1(dag):
    h = BlockA(name='h')
    t = BlockA(name='t')
    dag.connect(h, t, Connection('out_o', 'in_i'))
    heads, tails = dag.heads_and_tails()

    assert heads==set([h])
    assert tails== set([t])

def test_ht2(dag):
    h = BlockA(name='h')
    m = BlockA(name='m')
    t = BlockA(name='t')
    dag.connect(h, m, Connection('out_o', 'in_i'))
    dag.connect(m, t, Connection('out_o', 'in_i'))
    heads, tails = dag.heads_and_tails()

    assert heads==set([h])
    assert tails== set([t])

def test_ht3(dag):
    h = BlockA(name='h')
    t1 = BlockA(name='t1')
    t2 = BlockA(name='t2')
    dag.connect(h, t1, Connection('out_o', 'in_i'))
    dag.connect(h, t2, Connection('out_o', 'in_i'))
    heads, tails = dag.heads_and_tails()

    assert heads==set([h])
    assert tails== set([t1, t2])

def test_ht4(dag):
    h1 = BlockA(name='h')
    h2 = BlockA(name='h2')
    t = BlockA(name='t')
    dag.connect(h1, t, Connection('out_o', 'in_i'))
    dag.connect(h2, t, Connection('out_o', 'in_i'))
    heads, tails = dag.heads_and_tails()

    assert heads==set([h1, h2])
    assert tails== set([t])
