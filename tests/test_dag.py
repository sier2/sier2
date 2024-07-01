import pytest

from gizmo import Gizmo, Dag, Connection, GizmoError, Library
import param

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-dag')

def test_load_doc(dag):
    """Ensure that a dag's doc is loaded."""

    dump = dag.dump()
    dag2 = Library.load(dump)

    assert dag2.doc == dag.doc

def test_mismatched_types(dag):
    """Ensure that mismatched parameter values can't be assigned, and raise a GizmoError."""

    class OneOut(Gizmo):
        """One output parameter."""

        o_out = param.String()

    class OneIn(Gizmo):
        """One input parameter."""

        o_in = param.Integer()

    oo = OneOut()
    oi = OneIn()
    dag.connect(oo, oi, Connection('o_out', 'o_in'))

    with pytest.raises(GizmoError):
        oo.o_out = 'plugh'
        dag.execute()

def test_gizmo_exception(dag):
    """Ensure that exceptions in a gizmo raise a GizmoError."""

    class OneOut(Gizmo):
        """One output parameter."""

        o_out = param.String()

    class OneIn(Gizmo):
        """One input parameter."""

        o_in = param.String()

        def execute(self):
            raise ValueError('This is an exception')

    oo = OneOut()
    oi = OneIn()
    dag.connect(oo, oi, Connection('o_out', 'o_in'))

    with pytest.raises(GizmoError):
        oo.o_out = 'plugh'
        dag.execute()
