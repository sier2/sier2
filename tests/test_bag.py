import param
import pytest

from sier2 import Block, BlockError


class PassThrough(Block):
    """A block with one input and one output."""

    in_p = param.Integer()
    out_p = param.Integer()

    def execute(self):
        self.out_p = self.in_p


def test_add(Dag_bag_f):
    a = PassThrough()
    b = PassThrough()

    bag_block = PassThrough()
    bag_block.in_p = 22

    dag = Dag_bag_f([(a.param.out_p, b.param.in_p)], [bag_block])

    a.in_p = 33
    dag.execute()

    assert bag_block.out_p == 22


def test_add_in_dag(Dag_bag_f):
    a = PassThrough()
    b = PassThrough()
    with pytest.raises(BlockError, match='in the dag'):
        Dag_bag_f([(a.param.out_p, b.param.in_p)], [a])

    a = PassThrough()
    b = PassThrough()
    with pytest.raises(BlockError, match='in the dag'):
        Dag_bag_f([(a.param.out_p, b.param.in_p)], [b])


def test_watched(Dag_f, Dag_bag_f):
    a = PassThrough()
    b = PassThrough()

    dag1 = Dag_f([(a.param.out_p, b.param.in_p)])  # noqa: F841
    with pytest.raises(BlockError, match='has watchers'):
        Dag_bag_f([], [a])


def test_empty_with_bag(Dag_bag_f):
    a = PassThrough()
    dag = Dag_bag_f([], [a])

    a.in_p = 44
    dag.execute()

    assert a.out_p == 44
