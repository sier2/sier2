import pytest

from gizmo import Gizmo, Dag, Connection, GizmoError
import param

class PassThrough(Gizmo):
    """A gizmo with one input and one output."""

    p_in = param.Integer()
    p_out = param.Integer()

    def execute(self):
        self.p_out = self.p_in

class Add(Gizmo):
    """A gizmo that adds an addend to its input."""

    a_in = param.Integer()
    a_out = param.Integer()

    def __init__(self, addend: int):
        super().__init__()
        self.addend = addend

    def execute(self):
        self.a_out = self.a_in + self.addend

class OneIn(Gizmo):
    """A gizmo with one input."""

    o_in = param.Integer()

class TwoIn(Gizmo):
    """A gizmo with two inputs."""

    t1_in = param.Integer()
    t2_in = param.Integer()

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-dag')

def test_output_must_not_allow_refs(dag):
    class P(Gizmo):
        s = param.String()

    class Q(Gizmo):
        s = param.String(allow_refs=True)

    with pytest.raises(GizmoError):
        dag.connect(P(), Q(), ['s'])

def test_simple(dag):
    """Ensure that a value flows from the first input parameter, through the dag, to the last output parameter."""

    p = PassThrough()
    a = Add(1)
    o = OneIn()

    dag.connect(p, a, Connection('p_out', 'a_in'))
    dag.connect(a, o, Connection('a_out', 'o_in'))

    p.p_out = 1
    dag.execute()
    assert p.p_out == 1
    assert a.a_in == 1
    assert a.a_out == 2
    assert o.o_in == 2

def test_disconnect(dag):
    """Ensure that when gizmos are disconnected, they are no longer watching or being watched.

    We also ensure that other refs still work.
    """

    def n_watchers(g: Gizmo, param_name: str):
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
    assert n_watchers(p, 'p_out') == 0
    assert n_watchers(a, 'a_in') == 0
    assert n_watchers(a, 'a_out') == 0
    assert len(t.param.watchers) == 0
    # assert n_watchers(t, 't1_in') == 0
    # assert n_watchers(t, 't2_in') == 0

    dag.connect(p, a, Connection('p_out', 'a_in'))
    dag.connect(a, t, Connection('a_out' ,'t1_in'))
    dag.connect(p, t, Connection('p_out', 't2_in'))

    # Ensure that the dag is working.
    #
    p.p_out = 1
    dag.execute()

    assert a.a_in == 1 # p -> a
    assert a.a_out == 2 # p -> a
    assert t.t1_in == 2 # p -> a -> t
    assert t.t2_in == 1 # p -> t

    assert n_watchers(p, 'p_out') == 2
    assert n_watchers(a, 'a_in') == 0
    assert n_watchers(a, 'a_out') == 1
    assert len(t.param.watchers) == 0
    # assert n_watchers(t, 't1_in') == 0
    # assert n_watchers(t, 't2_in') == 0

    assert len(a._gizmo_name_map) == 1

    dag.disconnect(a)

    # Gizmo a is no longer watching b.b_out.
    #
    assert n_watchers(p, 'p_out') == 1

    # Gizmo t is no longer watching a.a_out.
    #
    assert n_watchers(a, 'a_in') == 0
    assert n_watchers(a, 'a_out') == 0

    # Gizmo t is still not being watched.
    #
    assert len(t.param.watchers) == 0

    assert len(a._gizmo_name_map) == 0

    # Gizmo a is no longer watching b.b_out.
    # Gizmo t is still watching b.b_out.
    #
    p.p_out = 5
    dag.execute()

    assert a.a_in == 1
    assert a.a_out == 2
    assert t.t2_in == 5

def test_cannot_connect_twice(dag):
    """Ensure that two gizmos cannot be connected more than once."""

    p0 = PassThrough()
    p1 = PassThrough()

    dag.connect(p0, p1, Connection('p_out', 'p_in'))
    with pytest.raises(GizmoError):
        dag.connect(p0, p1, Connection('p_out' ,'p_in'))

def test_not_same_names(dag):
    p0 = PassThrough(name='This')
    p1 = PassThrough(name='This')

    with pytest.raises(GizmoError):
        dag.connect(p0, p1, ['p_out:p_in'])

def test_not_existing_name(dag):
    p0 = PassThrough(name='This')
    p1 = PassThrough(name='That')
    p2 = PassThrough(name='This')

    dag.connect(p0, p1, Connection('p_out', 'p_in'))
    with pytest.raises(GizmoError):
        dag.connect(p1, p2, Connection('p_out', 'p_in'))

def test_self_loop(dag):
    """Ensure that gizmos can't connect to themselves."""

    p = PassThrough()

    with pytest.raises(GizmoError):
        dag.connect(p, p, ['p_out:p_in'])

def test_loop1(dag):
    """Ensure that connecting a gizmo doesn't create a loop in the dag."""

    p = PassThrough()
    a = Add(1)

    dag.connect(p, a, Connection('p_out', 'a_in'))
    with pytest.raises(GizmoError):
        dag.connect(a, p, Connection('a_out', 'p_in'))

def test_loop2(dag):
    """Ensure that loops aren't allowed."""

    p = PassThrough()
    a1 = Add(1)
    a2 = Add(2)

    dag.connect(p, a1, Connection('p_out', 'a_in'))
    dag.connect(a1, a2, Connection('a_out', 'a_in'))
    with pytest.raises(GizmoError):
        dag.connect(a2, p, Connection('a_out', 'p_in'))

def test_loop3(dag):
    """Ensure that loops aren't allowed."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    dag.connect(p1, p2, Connection('p_out', 'p_in'))
    dag.connect(p2, p3, Connection('p_out','p_in'))
    dag.connect(p4, p1, Connection('p_out','p_in'))
    with pytest.raises(GizmoError):
        dag.connect(p3, p1, Connection('p_out', 'p_in'))

def test_loop4(dag):
    """Ensure that loops aren't allowed."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    dag.connect(p2, p3, Connection('p_out', 'p_in'))
    dag.connect(p1, p2, Connection('p_out', 'p_in'))
    dag.connect(p4, p1, Connection('p_out', 'p_in'))
    with pytest.raises(GizmoError):
        dag.connect(p3, p1, Connection('p_out', 'p_in'))

def test_nonloop1(dag):
    """Ensure that non-loops are allowed."""

    gs = [PassThrough(name=f'P{i}') for i in range(4)]
    dag.connect(gs[2], gs[3], Connection('p_out', 'p_in'))
    dag.connect(gs[1], gs[2], Connection('p_out', 'p_in'))
    dag.connect(gs[0], gs[1], Connection('p_out', 'p_in'))

def test_must_connect(dag):
    """Ensure that new gizmos are connected to existing gizmos."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    dag.connect(p1, p2, Connection('p_out', 'p_in'))
    with pytest.raises(GizmoError):
        dag.connect(p3, p4, Connection('p_out', 'p_in'))

def test_sorted1(dag):
    gs = [PassThrough(name=f'PT{i}') for i in range(4)]
    dag.connect(gs[2], gs[3], Connection('p_out', 'p_in'))
    dag.connect(gs[1], gs[2], Connection('p_out', 'p_in'))
    dag.connect(gs[0], gs[1], Connection('p_out', 'p_in'))

    tsorted = [g.name for g in dag.get_sorted()]

    assert tsorted == ['PT0', 'PT1', 'PT2', 'PT3']

def test_sorted2(dag):
    """Ensure that the ranks reflect the order in the dag."""

    g1 = PassThrough(name='PT1')
    g2 = PassThrough(name='PT2')
    g3 = PassThrough(name='PT3')
    g4 = PassThrough(name='PT4')
    g5 = PassThrough(name='PT5')

    dag.connect(g4, g5, Connection('p_out', 'p_in'))
    dag.connect(g3, g4, Connection('p_out', 'p_in'))
    dag.connect(g2, g3, Connection('p_out', 'p_in'))
    dag.connect(g1, g2, Connection('p_out', 'p_in'))

    tsorted = [g.name for g in dag.get_sorted()]

    assert tsorted == ['PT1', 'PT2', 'PT3', 'PT4', 'PT5']

def test_onlychanged(dag):
    """Ensure that params are triggered when set with the same value."""

    p = PassThrough()
    a = Add(1)

    dag.connect(p, a, Connection('p_out', 'a_in'))

    assert p.p_out == 0
    assert a.a_in == 0
    assert a.a_out == 0

    p.p_out = 0
    dag.execute()

    assert a.a_in == 0
    assert a.a_out == 1
