#

# Test serialisation / deserialisation.
#

import pytest

from sier2 import Block, InputBlock, Dag, Connection, Library
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

class InputIncrement(InputBlock):
    """Increment the input."""

    in_i = param.Integer()
    out_i = param.Integer()

    def __init__(self, incr, *args, **kwargs):
        super().__init__(name=f'Increment (with input) by {incr}')
        self.incr = incr

    def prepare(self):
        self.value = self.in_i

    def execute(self):
        self.out_i = self.value + self.incr

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-doc', title='tests')

def test_serialise(dag):
    """Ensure that a dag can be serialised and restored.

    We use pass-through blocks to start and end, and an InputBlock
    and a Block in the middle.
    """

    p1 = P()
    incri2 = InputIncrement(2)
    incr3 = Increment(3)
    p2 = P()
    dag.connect(p1, incri2, Connection('out_p', 'in_i'))
    dag.connect(incri2, incr3, Connection('out_i', 'in_i'))
    dag.connect(incr3, p2, Connection('out_i', 'in_p'))

    first_name = p1.name
    ii_name = incri2.name
    last_name = p2.name

    p1.out_p = 1
    dag.execute()
    assert incri2.value == 1

    dag.execute_after_input(incri2)
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

    incr_blocks = [g for g in dump['blocks'] if g['block'].endswith('Increment')]
    assert len(incr_blocks) == 2
    assert set([g['args']['incr'] for g in incr_blocks]) == set([2, 3])

    # Blocks must be in the library to be restored.
    #
    Library.add_block(P)
    Library.add_block(Increment)
    Library.add_block(InputIncrement)

    # Start again.
    # Asserts below must correspond with asserts above.
    #
    dag2 = Library.load_dag(dump)

    first_g = dag2.block_by_name(first_name)
    ii_g = dag2.block_by_name(ii_name)
    last_g = dag2.block_by_name(last_name)

    first_g.out_p = 1
    dag2.execute()
    assert ii_g.value == 1

    dag2.execute_after_input(ii_g)
    assert last_g.in_p == 6

    # Dumping again should produce the same dump.
    #
    assert dump == dag2.dump()
