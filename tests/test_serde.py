#

# Test serialisation / deserialisation.
#

import pytest

from sier2 import Block, Dag, Connection, Library
import param

class P(Block):
    """In and out parameters."""

    in_p = param.Number()
    out_p = param.Number()

class Increment(Block):
    """Increment the input."""

    in_i = param.Integer()
    out_i = param.Integer()

    def __init__(self, incr, *args, **kwargs):
        super().__init__(name=f'Increment by {incr}')
        self.incr = incr

    def execute(self):
        self.out_i = self.in_i + self.incr

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-doc', title='tests')

def test_serialise(dag):
    """Ensure that a dag can be serialised and restored."""

    p1 = P()
    p2 = P()
    incr2 = Increment(2)
    incr3 = Increment(3)
    dag.connect(p1, incr2, Connection('out_p', 'in_i'))
    dag.connect(incr2, incr3, Connection('out_i', 'in_i'))
    dag.connect(incr3, p2, Connection('out_i', 'in_p'))

    first_name = p1.name
    last_name = p2.name

    p1.out_p = 1
    dag.execute()
    assert p2.in_p == 6

    # We have a working dag.
    # Dump it out.
    #
    dump = dag.dump()
    # from pprint import pprint
    # pprint(dump)
    del dag

    assert len(dump['blocks']) == 4
    assert len(dump['connections']) == 3

    incr_blocks = [g for g in dump['blocks'] if g['block'].endswith('.Increment')]
    assert len(incr_blocks) == 2
    assert set([g['args']['incr'] for g in incr_blocks]) == set([2, 3])

    # Gizmos must be in the library to be restored.
    #
    Library.add(P)
    Library.add(Increment)

    # Start again.
    #
    dag2 = Library.load_dag(dump)

    first_g = dag2.block_by_name(first_name)
    last_g = dag2.block_by_name(last_name)

    first_g.out_p = 1
    dag2.execute()
    assert last_g.in_p == 6

    # Dumping again should produce the same dump.
    #
    assert dump == dag2.dump()
