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
    class P(Gizmo):
        """A gizmo with a single output parameter."""

        one = param.Integer(label='output P')

    class Q(param.Parameterized):
        """A gizmo with a single input and a single output."""

        two = param.Integer(label='Int 2', doc='input Q', allow_refs=True)
        three = param.Integer(label='Int 3', doc='output Q')

        @param.depends('two', watch=True)
        def act(self, *args, **kwargs):
            print(f'Q acting {self.two=} {args=} {kwargs=}')
            self.three = self.two + 1

    class R(param.Parameterized):
        """A gizmo with a single input."""

        four = param.Integer(label='Int 4', doc='input R', allow_refs=True)

        @param.depends('four', watch=True)
        def act(self):
            print(f'R acting {self.four=}')

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
