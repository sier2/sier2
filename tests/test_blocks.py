import pytest

from sr2 import Block, Dag, Connection, BlockError
import param

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

class OneIn(Block):
    """A block with one input."""

    in_o = param.Integer()

class TwoIn(Block):
    """A block with two inputs."""

    in_t1 = param.Integer()
    in_t2 = param.Integer()

def test_params():
    class ParamBlock(Block):
        """Test picked params."""

        in_a = param.String()
        in_b = param.String()
        c = param.String()
        d = param.String()
        out_e = param.String()
        out_f = param.String()

    pb = ParamBlock(only_in=False)
    assert pb.pick_params() == ['c', 'd', 'in_a', 'in_b']

    pb = ParamBlock(only_in=True)
    assert pb.pick_params() == ['in_a', 'in_b']

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-dag', title='tests')

def test_output_must_not_allow_refs(dag):
    class P(Block):
        s = param.String()

    class Q(Block):
        s = param.String(allow_refs=True)

    with pytest.raises(BlockError):
        dag.connect(P(), Q(), ['s'])

def test_simple(dag):
    """Ensure that a value flows from the first input parameter, through the dag, to the last output parameter."""

    p = PassThrough()
    a = Add(1)
    o = OneIn()

    dag.connect(p, a, Connection('out_p', 'in_a'))
    dag.connect(a, o, Connection('out_a', 'in_o'))

    p.in_p = 1
    dag.execute()
    assert p.out_p == 1
    assert a.in_a == 1
    assert a.out_a == 2
    assert o.in_o == 2

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
    dag.connect(a, t, Connection('out_a' ,'in_t1'))
    dag.connect(p, t, Connection('out_p', 'in_t2'))

    # Ensure that the dag is working.
    #
    p.in_p = 1
    dag.execute()

    assert a.in_a == 1 # p -> a
    assert a.out_a == 2 # p -> a
    assert t.in_t1 == 2 # p -> a -> t
    assert t.in_t2 == 1 # p -> t

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

def test_cannot_connect_twice(dag):
    """Ensure that two blocks cannot be connected more than once."""

    p0 = PassThrough()
    p1 = PassThrough()

    dag.connect(p0, p1, Connection('out_p', 'in_p'))
    with pytest.raises(BlockError):
        dag.connect(p0, p1, Connection('p_out' ,'p_in'))

def test_not_same_names(dag):
    p0 = PassThrough(name='This')
    p1 = PassThrough(name='This')

    with pytest.raises(BlockError):
        dag.connect(p0, p1, Connection('out_p', 'in_p'))

def test_not_existing_name(dag):
    p0 = PassThrough(name='This')
    p1 = PassThrough(name='That')
    p2 = PassThrough(name='This')

    dag.connect(p0, p1, Connection('out_p', 'in_p'))
    with pytest.raises(BlockError):
        dag.connect(p1, p2, Connection('out_p', 'in_p'))

def test_self_loop(dag):
    """Ensure that blocks can't connect to themselves."""

    p = PassThrough()

    with pytest.raises(BlockError):
        dag.connect(p, p, Connection('out_p', 'in_p'))

def test_loop1(dag):
    """Ensure that connecting a block doesn't create a loop in the dag."""

    p = PassThrough()
    a = Add(1)

    dag.connect(p, a, Connection('out_p', 'in_p'))
    with pytest.raises(BlockError):
        dag.connect(a, p, Connection('out_a', 'in_p'))

def test_loop2(dag):
    """Ensure that loops aren't allowed."""

    p = PassThrough()
    a1 = Add(1)
    a2 = Add(2)

    dag.connect(p, a1, Connection('out_p', 'in_a'))
    dag.connect(a1, a2, Connection('out_a', 'in_a'))
    with pytest.raises(BlockError):
        dag.connect(a2, p, Connection('out_a', 'in_p'))

def test_loop3(dag):
    """Ensure that loops aren't allowed."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    dag.connect(p1, p2, Connection('out_p', 'in_p'))
    dag.connect(p2, p3, Connection('out_p', 'in_p'))
    dag.connect(p4, p1, Connection('out_p', 'in_p'))
    with pytest.raises(BlockError):
        dag.connect(p3, p1, Connection('out_p', 'in_p'))

def test_loop4(dag):
    """Ensure that loops aren't allowed."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    dag.connect(p2, p3, Connection('out_p', 'in_p'))
    dag.connect(p1, p2, Connection('out_p', 'in_p'))
    dag.connect(p4, p1, Connection('out_p', 'in_p'))
    with pytest.raises(BlockError):
        dag.connect(p3, p1, Connection('out_p', 'in_p'))

def test_nonloop1(dag):
    """Ensure that non-loops are allowed."""

    gs = [PassThrough(name=f'P{i}') for i in range(4)]
    dag.connect(gs[2], gs[3], Connection('out_p', 'in_p'))
    dag.connect(gs[1], gs[2], Connection('out_p', 'in_p'))
    dag.connect(gs[0], gs[1], Connection('out_p', 'in_p'))

def test_must_connect(dag):
    """Ensure that new blocks are connected to existing blocks."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    dag.connect(p1, p2, Connection('out_p', 'in_p'))
    with pytest.raises(BlockError):
        dag.connect(p3, p4, Connection('out_p', 'in_p'))

def test_sorted1(dag):
    gs = [PassThrough(name=f'PT{i}') for i in range(4)]
    dag.connect(gs[2], gs[3], Connection('out_p', 'in_p'))
    dag.connect(gs[1], gs[2], Connection('out_p', 'in_p'))
    dag.connect(gs[0], gs[1], Connection('out_p', 'in_p'))

    tsorted = [g.name for g in dag.get_sorted()]

    assert tsorted == ['PT0', 'PT1', 'PT2', 'PT3']

def test_sorted2(dag):
    """Ensure that the ranks reflect the order in the dag."""

    g1 = PassThrough(name='PT1')
    g2 = PassThrough(name='PT2')
    g3 = PassThrough(name='PT3')
    g4 = PassThrough(name='PT4')
    g5 = PassThrough(name='PT5')

    dag.connect(g4, g5, Connection('out_p', 'in_p'))
    dag.connect(g3, g4, Connection('out_p', 'in_p'))
    dag.connect(g2, g3, Connection('out_p', 'in_p'))
    dag.connect(g1, g2, Connection('out_p', 'in_p'))

    tsorted = [g.name for g in dag.get_sorted()]

    assert tsorted == ['PT1', 'PT2', 'PT3', 'PT4', 'PT5']

def test_onlychanged(dag):
    """Ensure that params are triggered when set with the same value."""

    p = PassThrough()
    a = Add(1)

    dag.connect(p, a, Connection('out_p', 'in_a'))

    assert p.out_p == 0
    assert a.in_a == 0
    assert a.out_a == 0

    p.out_p = 0
    dag.execute()

    assert a.in_a == 0
    assert a.out_a == 1

def test_call_block():
    """Ensure that we can call a block directly."""

    a = Add(1)
    result = a(in_a=5)

    assert result=={'out_a': 6}

def test_init_called():
    class A(Block):
        in_a = param.Integer(doc='int a')
        out_a = param.Integer(doc='int a')
        def __init__(self):
            pass
            # Oops, didn't call super().__init__()

    a = A()
    p = PassThrough()
    dag = Dag(title='Test', doc='Check for super().__init_()')
    with pytest.raises(BlockError, match=r'super\(\)\.__init__\(\)'):
        dag.connect(a, p, Connection('out_a', 'in_o'))
