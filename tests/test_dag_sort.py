import param
import pytest

from sier2 import Block, Dag


class PassThrough(Block):
    """Pass a value through unchanged."""

    in_p = param.Integer(default=0)
    out_p = param.Integer(default=0)

    def execute(self):
        self.out_p = self.in_p


@pytest.fixture
def Dag_f():
    """Ensure that each test starts with a clear dag."""

    return lambda connections: Dag(connections, doc='test-dag', title='tests')


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
