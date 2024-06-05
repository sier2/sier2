#

# Test serialisation / deserialisation.
#

import pytest

from gizmo import Gizmo, Dag, Connection, GizmoError, Library
import param

class P(Gizmo):
    pin = param.Number()
    pout = param.Number()

class Increment(Gizmo):
    iin = param.Integer()
    iout = param.Integer()

    def __init__(self, incr, *args, **kwargs):
        super().__init__(name=f'Increment by {incr}')
        self.incr = incr

    def execute(self):
        self.iout = self.iin + self.incr

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag()

def test_serialise(dag):
    """Ensure that a dag can be serialised and restored."""

    p1 = P()
    p2 = P()
    incr2 = Increment(2)
    incr3 = Increment(3)
    dag.connect(p1, incr2, Connection('pout', 'iin'))
    dag.connect(incr2, incr3, Connection('iout', 'iin'))
    dag.connect(incr3, p2, Connection('iout', 'pin'))

    first_name = p1.name
    last_name = p2.name

    p1.pout = 1
    assert p2.pin == 6

    # We have a working dag.
    # Dump it out.
    #
    dump = dag.dump()
    # from pprint import pprint
    # pprint(dump)
    del dag

    assert len(dump['gizmos']) == 4
    assert len(dump['connections']) == 3

    incr_gizmos = [g for g in dump['gizmos'] if g['gizmo'].endswith('.Increment')]
    assert len(incr_gizmos) == 2
    assert set([g['args']['incr'] for g in incr_gizmos]) == set([2, 3])

    # Gizmos must be in the library to be restored.
    #
    Library.add(P)
    Library.add(Increment)

    # Start again.
    #
    dag2 = Library.load(dump)

    first_g = dag2.gizmo_by_name(first_name)
    last_g = dag2.gizmo_by_name(last_name)

    first_g.pout = 1
    assert last_g.pin == 6

    # Dumping again should produce the same dump.
    #
    assert dump == dag2.dump()
