import param
import pytest

from sier2 import Block, BlockError, Dag


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
def Dag_f():
    """Ensure that each test starts with a clear dag."""

    return lambda connections: Dag(connections, doc='test-dag', title='tests')


def test_output_must_not_allow_refs(Dag_f):
    class P(Block):
        s = param.String()

    class Q(Block):
        s = param.String(allow_refs=True)

    with pytest.raises(BlockError):
        # dag.connect(P(), Q(), ['s'])
        Dag_f([(P().param.s, Q().param.s)])


def test_simple(Dag_f):
    """Ensure that a value flows from the first input parameter, through the dag, to the last output parameter."""

    p = PassThrough()
    a = Add(1)
    o = OneIn()

    dag = Dag_f([
        (p.param.out_p, a.param.in_a),
        (a.param.out_a, o.param.in_o),
    ])

    p.in_p = 1
    dag.execute()
    assert p.out_p == 1
    assert a.in_a == 1
    assert a.out_a == 2
    assert o.in_o == 2


def test_cannot_connect_twice(Dag_f):
    """Ensure that two blocks cannot be connected more than once."""

    p0 = PassThrough()
    p1 = PassThrough()

    with pytest.raises(BlockError, match='at index 1 are already connected'):
        Dag_f([
            (p0.param.out_p, p1.param.in_p),
            (p0.param.out_p, p1.param.in_p),
        ])


def test_not_same_names(Dag_f):
    p0 = PassThrough(name='This')
    p1 = PassThrough(name='This')

    with pytest.raises(BlockError, match='same name at index 0'):
        Dag_f([
            (p0.param.out_p, p1.param.in_p),
        ])


def test_not_existing_name(Dag_f):
    p0 = PassThrough(name='This')
    p1 = PassThrough(name='That')
    p2 = PassThrough(name='This')

    # dag.connect(p0, p1, Connection('out_p', 'in_p'))
    with pytest.raises(BlockError, match='at index 1 duplicates an existing name'):
        Dag_f([
            (p0.param.out_p, p1.param.in_p),
            (p1.param.out_p, p2.param.in_p),
        ])


def test_self_loop(Dag_f):
    """Ensure that blocks can't connect to themselves."""

    p = PassThrough()

    with pytest.raises(BlockError, match='same name at index 0'):
        Dag_f([(p.param.out_p, p.param.in_p)])


def test_loop1(Dag_f):
    """Ensure that connecting a block doesn't create a loop in the dag."""

    p = PassThrough()
    a = Add(1)

    with pytest.raises(BlockError, match='index 1 would create a cycle'):
        Dag_f([
            (p.param.out_p, a.param.in_a),
            (a.param.out_a, p.param.in_p),
        ])


def test_loop2(Dag_f):
    """Ensure that loops aren't allowed."""

    p = PassThrough()
    a1 = Add(1)
    a2 = Add(2)

    with pytest.raises(BlockError, match='index 2 would create a cycle'):
        Dag_f([
            (p.param.out_p, a1.param.in_a),
            (a1.param.out_a, a2.param.in_a),
            (a2.param.out_a, p.param.in_p),
        ])


def test_loop3(Dag_f):
    """Ensure that loops aren't allowed."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    with pytest.raises(BlockError, match='index 3 would create a cycle'):
        Dag_f([
            (p1.param.out_p, p2.param.in_p),
            (p2.param.out_p, p3.param.in_p),
            (p4.param.out_p, p1.param.in_p),
            (p3.param.out_p, p1.param.in_p),
        ])


def test_loop4(Dag_f):
    """Ensure that loops aren't allowed."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    with pytest.raises(BlockError, match='index 3 would create a cycle'):
        Dag_f([
            (p2.param.out_p, p3.param.in_p),
            (p1.param.out_p, p2.param.in_p),
            (p4.param.out_p, p1.param.in_p),
            (p3.param.out_p, p1.param.in_p),
        ])


def test_nonloop1(Dag_f):
    """Ensure that non-loops are allowed."""

    gs = [PassThrough(name=f'P{i}') for i in range(4)]

    Dag_f([
        (gs[2].param.out_p, gs[3].param.in_p),
        (gs[1].param.out_p, gs[2].param.in_p),
        (gs[0].param.out_p, gs[1].param.in_p),
    ])


def test_must_connect(Dag_f):
    """Ensure that new blocks are connected to existing blocks."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    with pytest.raises(BlockError, match='not connected'):
        Dag_f([
            (p1.param.out_p, p2.param.in_p),
            (p3.param.out_p, p4.param.in_p),
        ])


def test_sorted1(Dag_f):
    gs = [PassThrough(name=f'PT{i}') for i in range(4)]

    dag = Dag_f([
        (gs[2].param.out_p, gs[3].param.in_p),
        (gs[1].param.out_p, gs[2].param.in_p),
        (gs[0].param.out_p, gs[1].param.in_p),
    ])

    tsorted = [g.name for g in dag.get_sorted()]

    assert tsorted == ['PT0', 'PT1', 'PT2', 'PT3']


def test_sorted2(Dag_f):
    """Ensure that the ranks reflect the order in the dag."""

    g1 = PassThrough(name='PT1')
    g2 = PassThrough(name='PT2')
    g3 = PassThrough(name='PT3')
    g4 = PassThrough(name='PT4')
    g5 = PassThrough(name='PT5')

    dag = Dag_f([
        (g4.param.out_p, g5.param.in_p),
        (g3.param.out_p, g4.param.in_p),
        (g2.param.out_p, g3.param.in_p),
        (g1.param.out_p, g2.param.in_p),
    ])

    tsorted = [g.name for g in dag.get_sorted()]

    assert tsorted == ['PT1', 'PT2', 'PT3', 'PT4', 'PT5']


def test_sorted_not_depth_first(Dag_f):
    """The current topological sort algorithm does not sort depth-first.

    If the sort algorithm changes, change this test.
    """

    a = PassThrough(name='a')
    b = PassThrough(name='b')
    c = PassThrough(name='c')
    d = PassThrough(name='d')
    e = PassThrough(name='e')
    f = PassThrough(name='f')
    g = PassThrough(name='g')

    dag = Dag_f([
        (a.param.out_p, b.param.in_p),
        (b.param.out_p, c.param.in_p),
        (c.param.out_p, d.param.in_p),
        (a.param.out_p, e.param.in_p),
        (e.param.out_p, f.param.in_p),
        (f.param.out_p, g.param.in_p),
    ])

    tsorted = [g.name for g in dag.get_sorted()]

    assert tsorted != ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    assert tsorted != ['a', 'e', 'f', 'g', 'b', 'c', 'd']


def test_onlychanged(Dag_f):
    """Ensure that params are triggered when set with the same value."""

    p = PassThrough()
    a = Add(1)

    # dag.connect(p, a, Connection('out_p', 'in_a'))
    dag = Dag_f([
        (p.param.out_p, a.param.in_a),
    ])

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

    assert result == {'out_a': 6}


def test_init_called():
    class A(Block):
        """."""

        in_a = param.Integer(doc='int a')
        out_a = param.Integer(doc='int a')

        def __init__(self):
            pass
            # Oops, didn't call super().__init__()

    a = A()
    p = PassThrough()
    with pytest.raises(BlockError, match=r'super\(\)\.__init__\(\)'):
        Dag([(a.param.out_a, p.param.in_p)], title='Test', doc='Check for super().__init_()')


def test_banners():
    class B(Block):
        """Test banners."""

        def __init__(self, top, bot):
            super().__init__(banners=(top, bot))

    b = B('top', None)
    assert b.banner_top_.rx.value == 'top'
    assert b.banner_bot_.rx.value is None

    b.banners(('top2', None))
    assert b.banner_top_.rx.value == 'top2'

    with pytest.raises(BlockError, match='uninitialised'):
        b.banners((None, 'bot'))


def test_no_banners():
    class B(Block):
        """Test banners."""

    b = B()
    assert b.banner_top_.rx.value is None
    assert b.banner_bot_.rx.value is None
