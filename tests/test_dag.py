import param
import pytest

from sier2 import Block, BlockError, BlockState, BlockValidateError, Dag, Library
from sier2._dag import _set_downstream_state


class PassThrough(Block):
    """Pass a value through unchanged."""

    in_p = param.Integer(default=0)
    out_p = param.Integer(default=0)

    def execute(self):
        self.out_p = self.in_p


def test_load_doc(Dag_f):
    """Ensure that a dag's doc is loaded."""

    Library.clear()
    Library.add_block(PassThrough)

    dag = Dag_f([(PassThrough().param.out_p, PassThrough().param.in_p)])
    dump = dag.dump()
    dag2 = Library.load_dag(dump)

    assert dag2.doc == dag.doc

    Library.clear()


def test_empty_dag(Dag_f):
    dag = Dag_f([])
    with pytest.raises(BlockError, match='Nothing to execute'):
        dag.execute()


# def test_no_connections(dag):
#     # class PassThrough(Block):
#     #     """Pass a value through unchanged."""

#     #     in_p = param.Integer(default=0)
#     #     out_p = param.Integer(default=0)

#     #     def execute(self):
#     #         self.out_p = self.in_p

#     b1 = PassThrough()
#     b2 = PassThrough()
#     with pytest.raises(BlockError):
#         dag.connect(b1, b2)


def test_no_inputs(Dag_f):
    """Even though two blocks are connected, the first block is not required
    to send data to the second block."""

    class OneOut(Block):
        """One output parameter."""

        out_o = param.Integer(default=1)

    class OneIn(Block):
        """One input parameter."""

        in_p = param.Integer(default=2)

        def execute(self):
            self.in_p = 3

    oo = OneOut()
    oi = OneIn()
    dag = Dag_f([
        (oo.param.out_o, oi.param.in_p),
    ])
    # dag.connect(oo, oi, Connection('out_o', 'in_p'))

    dag.execute()
    assert oo.out_o == 1
    assert oi.in_p == 2


def test_mismatched_types(Dag_f):
    """Ensure that mismatched parameter values can't be assigned, and raise a BlockError."""

    class OneOut(Block):
        """One output parameter."""

        out_o = param.String()

        def execute(self):
            self.out_o = 'out'

    class OneIn(Block):
        """One input parameter."""

        in_o = param.Integer()

    oo = OneOut()
    oi = OneIn()
    # dag.connect(oo, oi, Connection('out_o', 'in_o'))
    dag = Dag_f([
        (oo.param.out_o, oi.param.in_o),
    ])

    with pytest.raises(BlockError, match='setting a parameter'):
        dag.execute()


def test_block_exception(Dag_f):
    """Ensure that exceptions in a block raise a BlockError."""

    class OneOut(Block):
        """One output parameter."""

        out_o = param.String()

        def execute(self):
            self.out_o = 'out'

    class OneIn(Block):
        """One input parameter."""

        in_o = param.String()

        def execute(self):
            raise ValueError('This is an exception')

    oo = OneOut()
    oi = OneIn()
    dag = Dag_f([
        (oo.param.out_o, oi.param.in_o),
    ])

    with pytest.raises(BlockError, match='This is an exception'):
        dag.execute()


def test_first_no_input(Dag_f):
    """A dag with no input blocks will run all the way."""

    class Incr(Block):
        """Pass a value through unchanged."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def execute(self):
            self.out_p = self.in_p + 1

    p0 = Incr()
    p1 = Incr()
    dag = Dag_f([
        (p0.param.out_p, p1.param.in_p),
    ])

    dag.execute()
    assert p1.out_p == 2


def test_first_input(Dag_f):
    """A dag where the first block is an input block does not need to be primed."""

    class Initial(Block):
        """Initial input block, no in_ params required."""

        INITIAL = 11
        out_p = param.Integer(default=INITIAL)

        VALUE = 99

        def __init__(self):
            super().__init__(wait_for_input=True)

        def execute(self):
            self.out_p = self.VALUE

    p0 = Initial()
    p1 = PassThrough()
    dag = Dag_f([
        (p0.param.out_p, p1.param.in_p),
    ])
    paused = dag.execute()
    assert p0.out_p == Initial.INITIAL
    assert p1.out_p == 0
    final = dag.execute_after_input(paused)

    assert p0.out_p == Initial.VALUE
    assert p1.out_p == Initial.VALUE
    assert final is None


def test_input_block(Dag_f):
    """Ensure that dag execution stops at a user-input block."""

    class PassThroughI(Block):
        """Pass value+1 through."""

        in_p = param.Integer()
        out_p = param.Integer()

        def __init__(self):
            super().__init__(wait_for_input=True)

        def prepare(self):
            self.value = self.in_p

        def execute(self):
            self.out_p = self.value + 1

    p0 = PassThrough()
    p1 = PassThrough()
    p2 = PassThroughI()
    p3 = PassThrough()
    p4 = PassThrough()

    # dag.connect(p0, p1, Connection('out_p', 'in_p'))
    # dag.connect(p1, p2, Connection('out_p', 'in_p'))
    # dag.connect(p2, p3, Connection('out_p', 'in_p'))
    # dag.connect(p3, p4, Connection('out_p', 'in_p'))
    dag = Dag_f([
        (p0.param.out_p, p1.param.in_p),
        (p1.param.out_p, p2.param.in_p),
        (p2.param.out_p, p3.param.in_p),
        (p3.param.out_p, p4.param.in_p),
    ])

    # Emulate user input, and execute the dag up to the input block.
    #
    p0.in_p = 5
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
    assert len(dag._block_queue) == 0


def test_input_block_validation(Dag_f):
    """Ensure that input validation works."""

    class ValidateInput(Block):
        """Pass a value through unchanged."""

        in_p = param.Integer(default=0)
        out_p = param.Integer(default=0)

        def __init__(self):
            super().__init__(wait_for_input=True)

        def prepare(self):
            if self.in_p == 1:
                raise BlockValidateError(block_name=self.name, message='validation')

        def execute(self):
            self.out_p = self.in_p

    p0 = PassThrough()
    p1 = ValidateInput()
    p2 = PassThrough()
    # dag.connect(p0, p1, Connection('out_p', 'in_p'))
    # dag.connect(p1, p2, Connection('out_p', 'in_p'))
    dag = Dag_f([
        (p0.param.out_p, p1.param.in_p),
        (p1.param.out_p, p2.param.in_p),
    ])

    # Invalid input.
    #
    p0.in_p = 1
    with pytest.raises(BlockValidateError):
        dag.execute()

    assert p1.in_p == 1

    # Start a new execution with valid input.
    #
    p0.in_p = 2
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


def test_block_state(Dag_f):
    """Ensure that block states are set correctly."""

    class IncrementBlock(Block):
        """Increment the input."""

        in_p = param.Integer()
        out_p = param.Integer()

        def execute(self):
            self.out_p = self.in_p + 1

    class InputIncrementBlock(Block):
        """Increment the input with input."""

        in_p = param.Integer()
        out_p = param.Integer()

        def __init__(self, name):
            super().__init__(name=name, wait_for_input=True)

        def prepare(self):
            self.value = self.in_p

        def execute(self):
            self.out_p = self.value + 1

    inc0 = IncrementBlock(name='inc0')
    inc1 = IncrementBlock(name='inc1')
    iinc2 = InputIncrementBlock(name='iinc2')
    inc3 = IncrementBlock(name='inc3')
    inc4 = IncrementBlock(name='inc4')

    # dag.connect(inc0, inc1, Connection('out_p', 'in_p'))
    # dag.connect(inc1, iinc2, Connection('out_p', 'in_p'))
    # dag.connect(iinc2, inc3, Connection('out_p', 'in_p'))
    # dag.connect(inc3, inc4, Connection('out_p', 'in_p'))
    dag = Dag_f([
        (inc0.param.out_p, inc1.param.in_p),
        (inc1.param.out_p, iinc2.param.in_p),
        (iinc2.param.out_p, inc3.param.in_p),
        (inc3.param.out_p, inc4.param.in_p),
    ])

    inc0.in_p = 1
    b = dag.execute()
    assert b is iinc2

    assert inc1.out_p == 3
    assert iinc2.in_p == 3
    assert iinc2.out_p == 0

    assert inc0._block_state == BlockState.SUCCESSFUL
    assert inc1._block_state == BlockState.SUCCESSFUL
    assert iinc2._block_state == BlockState.WAITING
    assert inc3._block_state == BlockState.READY
    assert inc4._block_state == BlockState.READY

    iinc2.value = 5
    dag.execute_after_input(b)

    assert inc3.in_p == 6
    assert inc4.in_p == 7
    assert inc4.out_p == 8

    assert inc0._block_state == BlockState.SUCCESSFUL
    assert inc1._block_state == BlockState.SUCCESSFUL
    assert iinc2._block_state == BlockState.WAITING
    assert inc3._block_state == BlockState.SUCCESSFUL
    assert inc4._block_state == BlockState.SUCCESSFUL


def test_multiple_heads_without_pause(Dag_f):
    class Increment(Block):
        """Increment the input."""

        in_p = param.Integer()
        out_p = param.Integer()

        def execute(self):
            self.out_p = self.in_p + 1

    h1 = Increment(name='h1')
    h2 = Increment(name='h2')
    t = Increment(name='t')
    # dag.connect(h1, t, Connection('out_p', 'in_p'))
    # dag.connect(h2, t, Connection('out_p', 'in_p'))
    dag = Dag_f([
        (h1.param.out_p, t.param.in_p),
        (h2.param.out_p, t.param.in_p),
    ])

    h1.in_p = 1
    h2.in_p = 1
    dag.execute()

    assert h1.out_p == 2
    assert h2.out_p == 2
    assert t.in_p == 2
    assert t.out_p == 3


def test_multiple_heads_with_pause(Dag_f):
    class Has(Block):
        """An instrumented block."""

        in_i = param.String(default='str')
        out_o = param.String()

        def __init__(self, name, wait=False):
            super().__init__(name=name, wait_for_input=wait)
            self.has_prepared = False
            self.has_executed = False

        def prepare(self):
            self.has_prepared = True

        def execute(self):
            self.out_o = self.in_i
            self.has_executed = True

    h1 = Has(name='h1', wait=True)
    h2 = Has(name='h2')
    t = Has(name='t')
    # dag.connect(h1, t, Connection('out_o', 'in_i'))
    # dag.connect(h2, t, Connection('out_o', 'in_i'))
    dag = Dag_f([
        (h1.param.out_o, t.param.in_i),
        (h2.param.out_o, t.param.in_i),
    ])

    b = dag.execute()
    assert b is h1

    assert h1.has_prepared
    assert not h1.has_executed

    assert h2.has_prepared
    assert h2.has_executed

    assert not t.has_prepared
    assert not t.has_executed

    dag.execute_after_input(b)

    assert h1.has_prepared
    assert h1.has_executed

    assert h2.has_prepared
    assert h2.has_executed

    assert t.has_prepared
    assert t.has_executed


def _triangle_dag(Dag_f, base=False) -> Dag:
    """Create a triangular dag.

    a -> b -> c -> d.
    a -> e -> f -> g.
    """

    a = PassThrough(name='a')
    b = PassThrough(name='b')
    c = PassThrough(name='c')
    d = PassThrough(name='d')
    e = PassThrough(name='e')
    f = PassThrough(name='f')
    g = PassThrough(name='g')

    conns = [
        (a.param.out_p, b.param.in_p),
        (b.param.out_p, c.param.in_p),
        (c.param.out_p, d.param.in_p),
        (a.param.out_p, e.param.in_p),
        (e.param.out_p, f.param.in_p),
        (f.param.out_p, g.param.in_p),
    ]
    if base:
        # Join the base corners of the triangle to a final block.
        #
        h = PassThrough(name='h')
        conns.extend([
            (d.param.out_p, h.param.in_p),
            (g.param.out_p, h.param.in_p),
        ])

    dag = Dag_f(conns)

    return dag


def _reset_blocks(dag: Dag):
    """Set all block states to READY.

    Do this via the dag block pairs, so some get set twice. Nobody cares.
    """

    for src, dst in dag._block_pairs:
        src._block_state = BlockState.READY
        dst._block_state = BlockState.READY


def test_downstream_blocks1(Dag_f):
    dag = _triangle_dag(Dag_f)
    a, b, c, d, e, f, g = [dag.block_by_name(name) for name in 'abcdefg']
    _reset_blocks(dag)
    downstream = _set_downstream_state(dag, a, BlockState.SUCCESSFUL)
    assert downstream == {b, c, d, e, f, g}
    assert all(i._block_state == BlockState.READY for i in [a])
    assert all(i._block_state == BlockState.SUCCESSFUL for i in [b, c, d, e, f, g])


def test_downstream_blocks2(Dag_f):
    dag = _triangle_dag(Dag_f)
    a, b, c, d, e, f, g = [dag.block_by_name(name) for name in 'abcdefg']
    _reset_blocks(dag)
    downstream = _set_downstream_state(dag, b, BlockState.SUCCESSFUL)
    assert downstream == {c, d}
    assert all(i._block_state == BlockState.READY for i in [a, b, e, f, g])
    assert all(i._block_state == BlockState.SUCCESSFUL for i in [c, d])


def test_downstream_blocks3(Dag_f):
    dag = _triangle_dag(Dag_f)
    a, b, c, d, e, f, g = [dag.block_by_name(name) for name in 'abcdefg']
    _reset_blocks(dag)
    downstream = _set_downstream_state(dag, c, BlockState.SUCCESSFUL)
    assert downstream == {d}
    assert all(i._block_state == BlockState.READY for i in [a, b, c, e, f, g])
    assert all(i._block_state == BlockState.SUCCESSFUL for i in [d])


def test_downstream_blocks4(Dag_f):
    dag = _triangle_dag(Dag_f)
    a, b, c, d, e, f, g = [dag.block_by_name(name) for name in 'abcdefg']
    _reset_blocks(dag)
    downstream = _set_downstream_state(dag, e, BlockState.SUCCESSFUL)
    assert downstream == {f, g}
    assert all(i._block_state == BlockState.READY for i in [a, b, c, d, e])
    assert all(i._block_state == BlockState.SUCCESSFUL for i in [f, g])


def test_downstream_blocks5(Dag_f):
    dag = _triangle_dag(Dag_f)
    a, b, c, d, e, f, g = [dag.block_by_name(name) for name in 'abcdefg']
    _reset_blocks(dag)
    downstream = _set_downstream_state(dag, f, BlockState.SUCCESSFUL)
    assert downstream == {g}
    assert all(i._block_state == BlockState.READY for i in [a, b, c, d, e, f])
    assert all(i._block_state == BlockState.SUCCESSFUL for i in [g])


def test_downstream_blocks6(Dag_f):
    dag = _triangle_dag(Dag_f, base=True)
    a, b, c, d, e, f, g, h = [dag.block_by_name(name) for name in 'abcdefgh']

    _reset_blocks(dag)
    downstream = _set_downstream_state(dag, a, BlockState.SUCCESSFUL)
    assert downstream == {b, c, d, e, f, g, h}
    assert all(i._block_state == BlockState.READY for i in [a])
    assert all(i._block_state == BlockState.SUCCESSFUL for i in [b, c, d, e, f, g, h])


def test_downstream_blocks7(Dag_f):
    dag = _triangle_dag(Dag_f, base=True)
    a, b, c, d, e, f, g, h = [dag.block_by_name(name) for name in 'abcdefgh']

    _reset_blocks(dag)
    downstream = _set_downstream_state(dag, b, BlockState.SUCCESSFUL)
    assert downstream == {c, d, h}
    assert all(i._block_state == BlockState.READY for i in [a, b, e, f, g])
    assert all(i._block_state == BlockState.SUCCESSFUL for i in [c, d, h])


# def test_connect_after_execute(dag):
#     class PassThrough(Block):
#         """Pass a value through unchanged."""

#         in_p = param.Integer(default=0)
#         out_p = param.Integer(default=0)

#         def __init__(self):
#             super().__init__(wait_for_input=True)

#         def execute(self):
#             self.out_p = self.in_p

#     cxn = Connection('out_p', 'in_p')

#     a = PassThrough()
#     b = PassThrough()
#     dag.connect(a, b, cxn)

#     paused = dag.execute()
#     assert paused is a

#     with pytest.raises(BlockError):
#         c = PassThrough()
#         dag.connect(b, c, cxn)

#     with pytest.raises(BlockError):
#         dag.disconnect(a)
