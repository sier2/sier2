import param
import pytest

from sier2 import Block, Dag


class BlockA(Block):
    """A test block."""

    in_i = param.String()
    out_o = param.String()


@pytest.fixture
def Dag_f():
    """Ensure that each test starts with a clear dag."""

    return lambda connections: Dag(connections, doc='test-dag', title='tests')


def test_ht1(Dag_f):
    h = BlockA(name='h')
    t = BlockA(name='t')
    dag = Dag_f([(h.param.out_o, t.param.in_i)])
    heads, tails = dag.heads_and_tails()

    assert heads == {h}
    assert tails == {t}


def test_ht2(Dag_f):
    h = BlockA(name='h')
    m = BlockA(name='m')
    t = BlockA(name='t')
    dag = Dag_f([
        (h.param.out_o, m.param.in_i),
        (m.param.out_o, t.param.in_i),
    ])
    heads, tails = dag.heads_and_tails()

    assert heads == {h}
    assert tails == {t}


def test_ht3(Dag_f):
    h = BlockA(name='h')
    t1 = BlockA(name='t1')
    t2 = BlockA(name='t2')
    dag = Dag_f([(h.param.out_o, t1.param.in_i), (h.param.out_o, t2.param.in_i)])
    heads, tails = dag.heads_and_tails()

    assert heads == {h}
    assert tails == {t1, t2}


def test_ht4(Dag_f):
    h1 = BlockA(name='h')
    h2 = BlockA(name='h2')
    t = BlockA(name='t')
    dag = Dag_f([
        (h1.param.out_o, t.param.in_i),
        (h2.param.out_o, t.param.in_i),
    ])
    heads, tails = dag.heads_and_tails()

    assert heads == {h1, h2}
    assert tails == {t}
