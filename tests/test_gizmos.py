import pytest

from gizmo import Gizmo, GizmoManager, GizmoError
import param

class PassThrough(Gizmo):
    """A gizmo with one input and one output."""

    p_in = param.Integer(allow_refs=True)
    p_out = param.Integer()

    def execute(self):
        self.p_out = self.p_in

class Add(Gizmo):
    """A gizmo that adds an addend to its input."""

    a_in = param.Integer(allow_refs=True)
    a_out = param.Integer()

    def __init__(self, addend: int):
        super().__init__()
        self.addend = addend

    def execute(self):
        self.a_out = self.a_in + self.addend

class OneIn(Gizmo):
    """A gizmo with one input."""

    o_in = param.Integer(allow_refs=True)

class TwoIn(Gizmo):
    """A gizmo with two inputs."""

    t1_in = param.Integer(allow_refs=True)
    t2_in = param.Integer(allow_refs=True)

@pytest.fixture(autouse=True)
def setup():
    """Ensure that each test starts with a clear flow graph."""

    GizmoManager.clear()

    yield

    pass

def test_input_must_have_allow_refs():
    class P(Gizmo):
        s = param.String()

    class Q(Gizmo):
        s = param.String()

    with pytest.raises(GizmoError):
        GizmoManager.connect(P(), Q(), ['s'])

def test_output_must_not_allow_refs():
    class P(Gizmo):
        s = param.String(allow_refs=True)

    class Q(Gizmo):
        s = param.String(allow_refs=True)

    with pytest.raises(GizmoError):
        GizmoManager.connect(P(), Q(), ['s'])

def test_simple():
    """Ensure that a value flows through the first input parameter to the last output parameter."""

    p = PassThrough()
    a = Add(1)
    o = OneIn()

    GizmoManager.connect(p, a, ['p_out:a_in'])
    GizmoManager.connect(a, o, ['a_out:o_in'])

    p.p_out = 1
    assert p.p_out == 1
    assert a.a_in == 1
    assert a.a_out == 2
    assert o.o_in == 2

def test_disconnect():
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

    GizmoManager.connect(p, a, ['p_out:a_in'])
    GizmoManager.connect(a, t, ['a_out:t1_in'])
    GizmoManager.connect(p, t, ['p_out:t2_in'])

    # Ensure that the flow is working.
    #
    p.p_out = 1
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

    GizmoManager.disconnect(a)

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

    # Gizmo a is no longer watching b.b_out.
    # Gizmo t is still watching b.b_out.
    #
    p.p_out = 5
    assert a.a_in == 1
    assert a.a_out == 2
    assert t.t2_in == 5

def test_self_loop():
    """Ensure that gizmos can't connect to themselves."""

    p = PassThrough

    with pytest.raises(GizmoError):
        GizmoManager.connect(p, p, ['p_out:p_in'])

def test_loop1():
    """Ensure that connecting a gizmo doesn't create a loop in the flow DAG."""

    p = PassThrough()
    a = Add(1)

    GizmoManager.connect(p, a, ['p_out:a_in'])
    with pytest.raises(GizmoError):
        GizmoManager.connect(a, p, ['a_out:p_in'])

def test_loop2():
    """Ensure that loops aren't allowed."""

    p = PassThrough()
    a1 = Add(1)
    a2 = Add(2)

    GizmoManager.connect(p, a1, ['p_out:a_in'])
    GizmoManager.connect(a1, a2, ['a_out:a_in'])
    with pytest.raises(GizmoError):
        GizmoManager.connect(a2, p, ['a_out:p_in'])

def test_loop3():
    """Ensure that loops aren't allowed."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    GizmoManager.connect(p1, p2, ['p_out:p_in'])
    GizmoManager.connect(p2, p3, ['p_out:p_in'])
    GizmoManager.connect(p4, p1, ['p_out:p_in'])
    with pytest.raises(GizmoError):
        GizmoManager.connect(p3, p1, ['p_out:p_in'])

def test_loop4():
    """Ensure that loops aren't allowed."""

    p1 = PassThrough()
    p2 = PassThrough()
    p3 = PassThrough()
    p4 = PassThrough()

    GizmoManager.connect(p2, p3, ['p_out:p_in'])
    GizmoManager.connect(p1, p2, ['p_out:p_in'])
    GizmoManager.connect(p4, p1, ['p_out:p_in'])
    with pytest.raises(GizmoError):
        GizmoManager.connect(p3, p1, ['p_out:p_in'])
