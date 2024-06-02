#

# Test serialisation / deserialisation.
#

import pytest

from gizmo import Gizmo, DagManager, GizmoError, Library
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
    """Ensure that each test starts with a clear flow graph."""

    return DagManager()

def test_serialise(dag):
    p1 = P()
    p2 = P()
    incr2 = Increment(2)
    incr3 = Increment(3)
    dag.connect(p1, incr2, ['pout:iin'])
    dag.connect(incr2, incr3, ['iout:iin'])
    dag.connect(incr3, p2, ['iout:pin'])

    first_name = p1.name
    last_name = p2.name

    p1.pout = 1
    assert p2.pin == 6

    dump = dag.dump()

    assert len(dump['gizmos']) == 4
    assert len(dump['connections']) == 3

    incr_gizmos = [g for g in dump['gizmos'] if g['gizmo'].endswith('.Increment')]
    assert len(incr_gizmos) == 2
    assert set([g['args']['incr'] for g in incr_gizmos]) == set([2, 3])

    from pprint import pprint
    print()
    pprint(dump)

    Library.add(P.gizmo_key(), P)
    Library.add(Increment.gizmo_key(), Increment)

    dag2 = Library.load(dump)

    first_g = dag2.gizmo_by_name(first_name)
    last_g = dag2.gizmo_by_name(last_name)

    first_g.pout = 1
    assert last_g.pin == 6
