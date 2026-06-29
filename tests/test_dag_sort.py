import random

import param

from sier2 import Block, Dag


class PassThrough(Block):
    """Pass a value through unchanged."""

    in_p = param.Integer(default=0)
    out_p = param.Integer(default=0)

    def execute(self):
        self.out_p = self.in_p


def test_cache1(Dag_f):
    a = PassThrough()
    b = PassThrough()
    dag = Dag_f([
        (a.param.out_p, b.param.in_p),
    ])

    assert dag.get_sorted() == [a, b]
    assert dag._sort_cache is not None


def test_cache2(Dag_f):
    a = PassThrough()
    b = PassThrough()
    dag = Dag_f([
        (b.param.out_p, a.param.in_p),
    ])

    assert dag.get_sorted() == [b, a]
    assert dag._sort_cache is not None


def test_sort1(Dag_f):
    """Blocks with the same parent sort in the order in which they were listed."""

    a = PassThrough(name='a')
    b = PassThrough(name='b')
    c = PassThrough(name='c')
    dag1 = Dag_f([
        (a.param.out_p, b.param.in_p),
        (a.param.out_p, c.param.in_p),
    ])

    sdag1 = [d.name for d in dag1.get_sorted()]
    assert sdag1 == ['a', 'b', 'c']


def test_sort2(Dag_f):
    """Blocks with the same parent sort in the order in which they were listed."""
    a = PassThrough(name='a')
    b = PassThrough(name='b')
    c = PassThrough(name='c')
    dag2 = Dag_f([
        (a.param.out_p, c.param.in_p),
        (a.param.out_p, b.param.in_p),
    ])

    sdag2 = [d.name for d in dag2.get_sorted()]
    assert sdag2 == ['a', 'c', 'b']


def test_shuffled(Dag_f):
    blocks = [PassThrough(name=chr(ord('a') + i)) for i in range(10)]
    tail = PassThrough(name='tail')

    rblocks = blocks[:]
    random.shuffle(rblocks)

    connections = []
    for block in rblocks:
        connections.append((block.param.out_p, tail.param.in_p))

    dag = Dag_f(connections)
    sdag = [b.name for b in dag.get_sorted()]

    assert sdag == [b.name for b in rblocks] + [tail.name]


def test_execute_heads(Dag_f):
    """Check that head input blocks execute in the same order that they're sorted.

    Also tests that execute() and execute_after_input() return blocks
    where wait_for_input is True.
    """

    blocks = [PassThrough(name=chr(ord('a') + i), wait_for_input=True) for i in range(10)]
    tail = PassThrough(name='tail')
    tail.in_p = 99

    rblocks = blocks[:]
    random.shuffle(rblocks)

    connections = []
    for block in rblocks:
        connections.append((block.param.out_p, tail.param.in_p))

    dag: Dag = Dag_f(connections)

    defined_order = [b.name for b in rblocks]

    b = dag.execute()
    execute_order = []
    while b is not None:
        execute_order.append(b.name)
        b = dag.execute_after_input(b)

    assert tail.out_p == 0
    assert execute_order == defined_order
