import param
import pytest

from sier2 import Block, BlockError, Connection, Connections, Dag
from sier2._dag import _is_connected


@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-dag', title='tests')


class PassThrough2(Block):
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

    b1 = PassThrough2()
    b2 = PassThrough2()
    b3 = PassThrough2()

    dag.connect(b1, b2, Connections({'out_p1': 'in_p1', 'out_p2': 'in_p2'}))

    dag.connect(b2, b3, Connections({'out_p1': 'in_p1', 'out_p2': 'in_p2'}))

    assert (b1, b2) in dag._block_pairs
    assert (b2, b3) in dag._block_pairs

    dag.disconnect(b1)
    assert (b1, b2) not in dag._block_pairs
    assert (b2, b3) in dag._block_pairs

    dag.disconnect(b2)
    assert not dag._block_pairs


def test_bad(dag):
    """Ensure that attempting to remove a block that will cause the dag to become disconnected will fail."""

    b1 = PassThrough2(name='PT1')
    b2 = PassThrough2(name='PT2')
    b3 = PassThrough2(name='PT3')
    b4 = PassThrough2(name='PT4')
    b5 = PassThrough2(name='PT5')

    dag.connect(b1, b2, Connections({'out_p1': 'in_p1', 'out_p2': 'in_p2'}))

    dag.connect(b2, b3, Connections({'out_p1': 'in_p1', 'out_p2': 'in_p2'}))

    dag.connect(b3, b4, Connections({'out_p1': 'in_p1', 'out_p2': 'in_p2'}))

    dag.connect(b4, b5, Connections({'out_p1': 'in_p1', 'out_p2': 'in_p2'}))

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


class PassThrough(Block):
    """A block with one input and one output."""

    in_p = param.Integer()
    out_p = param.Integer()

    def execute(self):
        self.out_p = self.in_p


class Add(Block):
    """A block that adds an addend to its input."""

    in_a = param.Integer()
    out_a = param.Integer()

    def __init__(self, addend: int):
        super().__init__()
        self.addend = addend

    def execute(self):
        self.out_a = self.in_a + self.addend


class TwoIn(Block):
    """A block with two inputs."""

    in_t1 = param.Integer()
    in_t2 = param.Integer()


def test_disconnect(dag):
    """Ensure that when blocks are disconnected, they are no longer watching or being watched.

    We also ensure that other refs still work.
    """

    def n_watchers(g: Block, param_name: str):
        """The number of watchers on this param.

        Before watchers are added:
            g.param.watchers == {}.
        After watcher of pp is added and removed:
            g.param.watchers == {'pp': {'value': []}}.

        In both cases, pp has no watchers.
        This function abstracts the difference.
        """

        return len(g.param.watchers.get(param_name, {}).get('value', []))

    p = PassThrough()
    a = Add(1)
    t = TwoIn()

    # Nothing is being watched by anything else.
    #
    assert n_watchers(p, 'out_p') == 0
    assert n_watchers(a, 'in_a') == 0
    assert n_watchers(a, 'out_a') == 0
    assert len(t.param.watchers) == 0
    # assert n_watchers(t, 't1_in') == 0
    # assert n_watchers(t, 't2_in') == 0

    dag.connect(p, a, Connection('out_p', 'in_a'))
    dag.connect(a, t, Connection('out_a', 'in_t1'))
    dag.connect(p, t, Connection('out_p', 'in_t2'))

    # Ensure that the dag is working.
    #
    p.in_p = 1
    dag.execute()

    assert a.in_a == 1  # p -> a
    assert a.out_a == 2  # p -> a
    assert t.in_t1 == 2  # p -> a -> t
    assert t.in_t2 == 1  # p -> t

    assert n_watchers(p, 'out_p') == 2
    assert n_watchers(a, 'in_a') == 0
    assert n_watchers(a, 'out_a') == 1
    assert len(t.param.watchers) == 0
    # assert n_watchers(t, 't1_in') == 0
    # assert n_watchers(t, 't2_in') == 0

    assert len(a._block_name_map) == 1

    dag.disconnect(a)

    # Block a is no longer watching b.b_out.
    #
    assert n_watchers(p, 'out_p') == 1

    # Block t is no longer watching a.a_out.
    #
    assert n_watchers(a, 'in_a') == 0
    assert n_watchers(a, 'out_a') == 0

    # Block t is still not being watched.
    #
    assert len(t.param.watchers) == 0

    assert len(a._block_name_map) == 0

    # Block a is no longer watching b.b_out.
    # Block t is still watching b.b_out.
    #
    p.in_p = 5
    dag.execute()

    assert a.in_a == 1
    assert a.out_a == 2
    assert t.in_t2 == 5
