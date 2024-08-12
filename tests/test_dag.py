import pytest

from gizmo import Gizmo, GizmoState, Dag, Connection, GizmoError, Library
import param

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-dag', title='tests')

def test_load_doc(dag):
    """Ensure that a dag's doc is loaded."""

    dump = dag.dump()
    dag2 = Library.load_dag(dump)

    assert dag2.doc == dag.doc

def test_no_inputs(dag):
    class OneOut(Gizmo):
        """One output parameter."""

        out_o = param.String()

    class OneIn(Gizmo):
        """One input parameter."""

        in_p = param.String()

    oo = OneOut()
    oi = OneIn()
    dag.connect(oo, oi, Connection('out_o', 'in_p'))

    with pytest.raises(GizmoError):
        dag.execute()

def test_mismatched_types(dag):
    """Ensure that mismatched parameter values can't be assigned, and raise a GizmoError."""

    class OneOut(Gizmo):
        """One output parameter."""

        out_o = param.String()

    class OneIn(Gizmo):
        """One input parameter."""

        in_o = param.Integer()

    oo = OneOut()
    oi = OneIn()
    dag.connect(oo, oi, Connection('out_o', 'in_o'))

    with pytest.raises(GizmoError):
        oo.out_o = 'plugh'
        dag.execute()

def test_gizmo_exception(dag):
    """Ensure that exceptions in a gizmo raise a GizmoError."""

    class OneOut(Gizmo):
        """One output parameter."""

        out_o = param.String()

    class OneIn(Gizmo):
        """One input parameter."""

        in_o = param.String()

        def execute(self):
            raise ValueError('This is an exception')

    oo = OneOut()
    oi = OneIn()
    dag.connect(oo, oi, Connection('out_o', 'in_o'))

    with pytest.raises(GizmoError):
        oo.out_o = 'plugh'
        dag.execute()

def test_user_input(dag):
    """Ensure that dag execution stops at a user-input gizmo."""

    class PassThrough(Gizmo):
        """Pass a value through unchanged."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def execute(self):
            self.out_p = self.in_p

    p0 = PassThrough()
    p1 = PassThrough()
    p2 = PassThrough(user_input=True)
    p3 = PassThrough()
    p4 = PassThrough()

    dag.connect(p0, p1, Connection('out_p', 'in_p'))
    dag.connect(p1, p2, Connection('out_p', 'in_p'))
    dag.connect(p2, p3, Connection('out_p', 'in_p'))
    dag.connect(p3, p4, Connection('out_p', 'in_p'))

    p0.out_p = 5
    dag.execute()

    assert p1.in_p == 5
    assert p2.in_p == 5
    assert p3.in_p == 5
    assert p4.in_p == 0

    assert len(dag._gizmo_queue) == 0

    # Executing without any pending events should raise.
    #
    with pytest.raises(GizmoError):
        dag.execute()

    # Emulate user input.
    #
    p2.out_p = 7
    dag.execute()

    assert p1.in_p == 5
    assert p2.in_p == 5
    assert p3.in_p == 7
    assert p4.in_p == 7

    assert len(dag._gizmo_queue) == 0

    # Executing without any pending events should raise.
    #
    with pytest.raises(GizmoError):
        dag.execute()

def test_gizmo_state(dag):
    """Ensure that gizmo states are set correctly."""

    class IncrementGizmo(Gizmo):
        """Increment the input."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def execute(self):
            self.out_p = self.in_p + 1

    inc0 = IncrementGizmo(name='inc0')
    inc1 = IncrementGizmo(name='inc1')
    inc2 = IncrementGizmo(name='inc2', user_input=True)
    inc3 = IncrementGizmo(name='inc3')
    inc4 = IncrementGizmo(name='inc4')

    dag.connect(inc0, inc1, Connection('out_p', 'in_p'))
    dag.connect(inc1, inc2, Connection('out_p', 'in_p'))
    dag.connect(inc2, inc3, Connection('out_p', 'in_p'))
    dag.connect(inc3, inc4, Connection('out_p', 'in_p'))

    inc0.out_p = 1
    dag.execute()

    assert inc2.out_p == 3

    assert inc0._gizmo_state == GizmoState.READY
    assert inc1._gizmo_state == GizmoState.SUCCESSFUL
    assert inc2._gizmo_state == GizmoState.WAITING
    assert inc3._gizmo_state == GizmoState.READY
    assert inc4._gizmo_state == GizmoState.READY

    inc2.out_p = 5
    dag.execute()

    assert inc0._gizmo_state == GizmoState.READY
    assert inc1._gizmo_state == GizmoState.SUCCESSFUL
    assert inc2._gizmo_state == GizmoState.WAITING
    assert inc3._gizmo_state == GizmoState.SUCCESSFUL
    assert inc4._gizmo_state == GizmoState.SUCCESSFUL
