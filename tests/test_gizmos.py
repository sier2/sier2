import pytest

from gizmo import Gizmo, GizmoManager, GizmoError
import param

def test_input_must_have_allow_refs():
    class P(Gizmo):
        s = param.String()

    class Q(Gizmo):
        s = param.String()

    with pytest.raises(GizmoError):
        GizmoManager.connect(P(), Q(), ['s'])

def test_basic():
    """Ensure that a value flows through the first input parameter to the lsat output parameter."""

    class P(Gizmo):
        """A gizmo with a single output parameter."""

        one = param.Integer(label='output P')

    class Q(param.Parameterized):
        """A gizmo with a single input and a single output (=input+1)."""

        two = param.Integer(label='Int 2', doc='input Q', allow_refs=True)
        three = param.Integer(label='Int 3', doc='output Q')

        @param.depends('two', watch=True)
        def act(self, *args, **kwargs):
            """Add 1 and pass it through."""

            self.three = self.two + 1

    class R(param.Parameterized):
        """A gizmo with a single input."""

        four = param.Integer(label='Int 4', doc='input R', allow_refs=True)

    p = P()
    q = Q()
    r = R()
    GizmoManager.connect(p, q, ['one:two'])
    GizmoManager.connect(q, r, ['three:four'])

    p.one = 1
    assert p.one == 1
    assert q.two == p.one
    assert q.three == q.two+1
    assert r.four == q.three

def test_disconnect():
    """Ensure that when gizmos are disconnected, they are no longer watching or being watched.

    We also ensure that other refs still work.
    """

    class P(Gizmo):
        pp = param.String()

    class Q(Gizmo):
        qp = param.String(allow_refs=True)

    class R(Gizmo):
        rp1 = param.String(allow_refs=True)
        rp2 = param.String(allow_refs=True)

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

    p = P()
    q = Q()
    r = R()

    # Nothing is being watched by anything.
    #
    assert n_watchers(p, 'pp') == 0
    assert n_watchers(q, 'qp') == 0
    assert len(r.param.watchers) == 0
    # assert n_watchers(r, 'rp1') == 0
    # assert n_watchers(r, 'rp2') == 0

    GizmoManager.connect(p, q, ['pp:qp'])
    GizmoManager.connect(q, r, ['qp:rp1'])
    GizmoManager.connect(p, r, ['pp:rp2'])

    # Ensure that the flow is working.
    #
    p.pp = 'plugh'
    assert q.qp == 'plugh'
    assert r.rp1 == 'plugh' # p -> q -> r
    assert r.rp2 == 'plugh' # p -> r

    assert n_watchers(p, 'pp') == 2
    assert n_watchers(q, 'qp') == 1
    assert len(r.param.watchers) == 0
    # assert n_watchers(r, 'rp1') == 0
    # assert n_watchers(r, 'rp2') == 0

    GizmoManager.disconnect(q)

    # Gizmo q is no longer watching p.pp.
    #
    assert n_watchers(p, 'pp') == 1

    # Gizmo r is no longer watching q.qp.
    #
    assert n_watchers(q, 'qp') == 0

    # Gizmo r is still not being watched.
    #
    assert len(r.param.watchers) == 0

    # Gizmo q is no longer watching p.pp.
    # Gizmo r is still watching p.pp.
    #
    p.pp = 'xyzzy'
    assert q.qp == 'plugh'
    assert r.rp2=='xyzzy'
