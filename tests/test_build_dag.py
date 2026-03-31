import param
import pytest

from sier2 import Block, BlockError, Dag


class PassThrough(Block):
    """Pass a value through unchanged."""

    in_p = param.Integer(default=0)
    out_p = param.Integer(default=0)

    def execute(self):
        self.out_p = self.in_p


class PassThrough2(Block):
    """Pass a value through unchanged."""

    in_p1 = param.Integer(default=0)
    in_p2 = param.Integer(default=0)
    out_p1 = param.Integer(default=0)
    out_p2 = param.Integer(default=0)

    def execute(self):
        self.out_p1 = self.in_p1
        self.out_p2 = self.in_p2


@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-dag', title='tests')


def test_build1(dag):
    b1 = PassThrough()
    b2 = PassThrough()

    dag.build([(b1.param.out_p, b2.param.in_p)])

    b1.in_p = 86
    dag.execute()

    assert b2.out_p == 86


def test_build2(dag):
    b1 = PassThrough2()
    b2 = PassThrough2()

    dag.build([(b1.param.out_p1, b2.param.in_p1), (b1.param.out_p2, b2.param.in_p2)])

    b1.in_p1 = 86
    b1.in_p2 = 99
    dag.execute()

    assert b2.out_p1 == 86
    assert b2.out_p2 == 99


def test_build_dup_params(dag):
    b1 = PassThrough()
    b2 = PassThrough()

    with pytest.raises(BlockError):
        dag.build([(b1.param.out_p, b2.param.in_p), (b1.param.out_p, b2.param.in_p)])


def test_not_a_block_instance(dag):
    """Check that a Block object is used, not the Block class."""
    b1 = PassThrough()

    with pytest.raises(BlockError):
        dag.build([(b1.param.out_p, PassThrough.param.in_p)])


def test_not_a_param(dag):
    b1 = PassThrough()

    with pytest.raises(BlockError):
        dag.build([('hello', b1.in_p)])


def test_triangle(dag):
    root = PassThrough()
    leg1 = PassThrough()
    leg2 = PassThrough()

    dag.build([(root.param.out_p, leg1.param.in_p), (root.param.out_p, leg2.param.in_p)])

    root.in_p = 99
    dag.execute()

    assert leg1.out_p == 99
    assert leg2.out_p == 99
