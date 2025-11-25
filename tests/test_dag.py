import pytest

from sier2 import Block, BlockState, Dag, Connection, BlockError, Library, BlockValidateError
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

def test_first_no_input(dag):
    """A dag where the first block is not an input block, and the dag is not primed, will fail."""

    class PassThrough(Block):
        """Pass a value through unchanged."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def execute(self):
            self.out_p = self.in_p

    p0 = PassThrough()
    p1 = PassThrough()
    dag.connect(p0, p1, Connection('out_p', 'in_p'))

    with pytest.raises(BlockError):
        dag.execute()

def test_first_input(dag):
    """A dag where the first block is an input block does not need to be primed."""

    VALUE = 99

    class Initial(Block):
        """Initial input block, no in_ params required."""
        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def __init__(self):
            super().__init__(wait_for_input=True)

        def prepare(self):
            self.in_p = VALUE

        def execute(self):
            self.out_p = self.in_p
            pass

    class PassThrough(Block):
        """Pass a value through unchanged."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def execute(self):
            self.out_p = self.in_p

    p0 = Initial()
    p1 = PassThrough()
    dag.connect(p0, p1, Connection('out_p', 'in_p'))
    paused = dag.execute()
    final = dag.execute_after_input(paused)

    assert p1.out_p == VALUE
    assert final is None

def test_input_block(dag):
    """Ensure that dag execution stops at a user-input block."""

    class PassThrough(Block):
        """Pass a value through unchanged."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def execute(self):
            self.out_p = self.in_p

    class PassThroughI(Block):
        """Pass a value through unchanged."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def __init__(self):
            super().__init__(wait_for_input=True)

        def prepare(self):
            self.value = self.in_p

        def execute(self):
            self.out_p = self.value+1

    p0 = PassThrough()
    p1 = PassThrough()
    p2 = PassThroughI()
    p3 = PassThrough()
    p4 = PassThrough()

    dag.connect(p0, p1, Connection('out_p', 'in_p'))
    dag.connect(p1, p2, Connection('out_p', 'in_p'))
    dag.connect(p2, p3, Connection('out_p', 'in_p'))
    dag.connect(p3, p4, Connection('out_p', 'in_p'))

    # Emulate user input, and execute the dag up to the input block.
    #
    p0.out_p = 5
    pinput = dag.execute()
    assert pinput is p2

    assert p1.in_p == 5
    assert p2.in_p == 5
    assert p2.value == 5
    assert p2.out_p == 0
    assert p3.in_p == 0
    assert p4.in_p == 0

    # Emulate user input, and execute the dag to completion.
    #
    p2.value = 7
    final = dag.execute_after_input(pinput)
    assert final is None

    assert p1.in_p == 5
    assert p2.in_p == 5
    assert p2.value == 7
    assert p2.out_p == 8
    assert p3.in_p == 8
    assert p4.in_p == 8

    assert len(dag._block_queue) == 0

    # Executing without any pending events should raise.
    #
    with pytest.raises(BlockError):
        dag.execute()

def test_input_block_validation(dag):
    """Ensure that input validation works."""

    class PassThrough(Block):
        """Pass a value through unchanged."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def execute(self):
            self.out_p = self.in_p

    class ValidateInput(Block):
        """Pass a value through unchanged."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def __init__(self):
            super().__init__(wait_for_input=True)

        def prepare(self):
            if self.in_p == 1:
                raise BlockValidateError(block_name=self.name, error='validation')

        def execute(self):
            self.out_p = self.in_p

    p0 = PassThrough()
    p1 = ValidateInput()
    p2 = PassThrough()
    dag.connect(p0, p1, Connection('out_p', 'in_p'))
    dag.connect(p1, p2, Connection('out_p', 'in_p'))

    # Invalid input.
    #
    p0.out_p = 1
    with pytest.raises(BlockValidateError):
        dag.execute()

    assert p1.in_p == 1

    # Start a new execution with valid input.
    #
    p0.out_p = 2
    dag.execute()
    assert p1.in_p == 2

    # User input.
    #
    p1.in_p = 3

    # Waiting for input.
    # Give the dag something to execute.
    # Continue execution().
    #
    dag.execute_after_input(p1)
    assert p1.out_p == 3
    assert p2.in_p == 3
    assert p2.out_p == 3

def test_block_state(dag):
    """Ensure that block states are set correctly."""

    class IncrementBlock(Block):
        """Increment the input."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def execute(self):
            self.out_p = self.in_p + 1

    class InputIncrementBlock(Block):
        """Increment the input."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def __init__(self, name):
            super().__init__(name=name, wait_for_input=True)

        def prepare(self):
            self.value = self.in_p

        def execute(self):
            self.out_p = self.value + 1

    inc0 = IncrementBlock(name='inc0')
    inc1 = IncrementBlock(name='inc1')
    inc2 = InputIncrementBlock(name='inc2')
    inc3 = IncrementBlock(name='inc3')
    inc4 = IncrementBlock(name='inc4')

    dag.connect(inc0, inc1, Connection('out_p', 'in_p'))
    dag.connect(inc1, inc2, Connection('out_p', 'in_p'))
    dag.connect(inc2, inc3, Connection('out_p', 'in_p'))
    dag.connect(inc3, inc4, Connection('out_p', 'in_p'))

    inc0.out_p = 1
    dag.execute()

    assert inc1.out_p == 2
    assert inc2.in_p == 2
    assert inc2.out_p == 0

    assert inc0._block_state == BlockState.READY
    assert inc1._block_state == BlockState.SUCCESSFUL
    assert inc2._block_state == BlockState.WAITING
    assert inc3._block_state == BlockState.READY
    assert inc4._block_state == BlockState.READY

    inc2.value = 5
    dag.execute_after_input(inc2)

    assert inc3.in_p == 6
    assert inc4.in_p == 7
    assert inc4.out_p == 8

    assert inc0._block_state == BlockState.READY
    assert inc1._block_state == BlockState.SUCCESSFUL
    assert inc2._block_state == BlockState.WAITING
    assert inc3._block_state == BlockState.SUCCESSFUL
    assert inc4._block_state == BlockState.SUCCESSFUL

def test_multiple_heads_without_pause(dag):
    class BlockA(Block):
        """A test block."""

        in_i = param.String()
        out_o = param.String()

    h1 = BlockA(name='h1')
    h2 = BlockA(name='h2')
    t = BlockA(name='t')
    dag.connect(h1, t, Connection('out_o', 'in_i'))
    dag.connect(h2, t, Connection('out_o', 'in_i'))

    with pytest.raises(BlockError):
        dag.execute()

def test_multiple_heads_with_pause(dag):
    class BlockA(Block):
        """A test block."""

        in_i = param.String()
        out_o = param.String()

        def __init__(self, name, pause=False):
            super().__init__(name=name, wait_for_input=pause)
            self.has_prepared = False
            self.has_executed = False

        def prepare(self):
            self.has_prepared = True

        def execute(self):
            self.out_o = self.in_i
            self.has_executed = True

    h1 = BlockA(name='h1', pause=True)
    h2 = BlockA(name='h2')
    t = BlockA(name='t')
    dag.connect(h1, t, Connection('out_o', 'in_i'))
    dag.connect(h2, t, Connection('out_o', 'in_i'))

    dag.execute()

    assert h1.has_prepared
    assert not h1.has_executed

    assert not h2.has_prepared
    assert not h2.has_executed
