import pytest

from sier2 import Block, BlockState, Dag, Connection, BlockError, Library
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
    class OneOut(Block):
        """One output parameter."""

        out_o = param.String()

    class OneIn(Block):
        """One input parameter."""

        in_p = param.String()

    oo = OneOut()
    oi = OneIn()
    dag.connect(oo, oi, Connection('out_o', 'in_p'))

    with pytest.raises(BlockError):
        dag.execute()

def test_mismatched_types(dag):
    """Ensure that mismatched parameter values can't be assigned, and raise a BlockError."""

    class OneOut(Block):
        """One output parameter."""

        out_o = param.String()

    class OneIn(Block):
        """One input parameter."""

        in_o = param.Integer()

    oo = OneOut()
    oi = OneIn()
    dag.connect(oo, oi, Connection('out_o', 'in_o'))

    with pytest.raises(BlockError):
        oo.out_o = 'plugh'
        dag.execute()

def test_block_exception(dag):
    """Ensure that exceptions in a block raise a BlockError."""

    class OneOut(Block):
        """One output parameter."""

        out_o = param.String()

    class OneIn(Block):
        """One input parameter."""

        in_o = param.String()

        def execute(self):
            raise ValueError('This is an exception')

    oo = OneOut()
    oi = OneIn()
    dag.connect(oo, oi, Connection('out_o', 'in_o'))

    with pytest.raises(BlockError):
        oo.out_o = 'plugh'
        dag.execute()

def test_user_input(dag):
    """Ensure that dag execution stops at a user-input block."""

    class PassThrough(Block):
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

    # Emulate user input, and execute the dag up to user_input.
    #
    p0.out_p = 5
    dag.execute()

    assert p1.in_p == 5
    assert p2.in_p == 5
    assert p3.in_p == 0
    assert p4.in_p == 0

    # assert len(dag._block_queue) == 0

    # # Executing without any pending events should raise.
    # #
    # with pytest.raises(BlockError):
    #     dag.execute()

    # Emulate user input, and execute the dag to completion.
    #
    p2.out_p = 7
    dag.execute()

    assert p1.in_p == 5
    assert p2.in_p == 5
    assert p3.in_p == 7
    assert p4.in_p == 7

    assert len(dag._block_queue) == 0

    # Executing without any pending events should raise.
    #
    with pytest.raises(BlockError):
        dag.execute()

def test_block_state(dag):
    """Ensure that block states are set correctly."""

    class IncrementBlock(Block):
        """Increment the input."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def execute(self):
            self.out_p = self.in_p + 1

    inc0 = IncrementBlock(name='inc0')
    inc1 = IncrementBlock(name='inc1')
    inc2 = IncrementBlock(name='inc2', user_input=True)
    inc3 = IncrementBlock(name='inc3')
    inc4 = IncrementBlock(name='inc4')

    dag.connect(inc0, inc1, Connection('out_p', 'in_p'))
    dag.connect(inc1, inc2, Connection('out_p', 'in_p'))
    dag.connect(inc2, inc3, Connection('out_p', 'in_p'))
    dag.connect(inc3, inc4, Connection('out_p', 'in_p'))

    inc0.out_p = 1
    dag.execute()

    assert inc2.out_p == 3

    assert inc0._block_state == BlockState.READY
    assert inc1._block_state == BlockState.SUCCESSFUL
    assert inc2._block_state == BlockState.WAITING
    assert inc3._block_state == BlockState.READY
    assert inc4._block_state == BlockState.READY

    inc2.out_p = 5
    dag.execute()

    assert inc0._block_state == BlockState.READY
    assert inc1._block_state == BlockState.SUCCESSFUL
    assert inc2._block_state == BlockState.WAITING
    assert inc3._block_state == BlockState.SUCCESSFUL
    assert inc4._block_state == BlockState.SUCCESSFUL
