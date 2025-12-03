import pytest

from sier2 import Block, BlockState, Dag, Connection, BlockError, Library, BlockValidateError
import param

class PassThrough(Block):
    """Pass a value through unchanged."""

    in_p = param.Integer(default=0)
    out_p = param.Integer(default=0)

    def execute(self):
        self.out_p = self.in_p

cxn = Connection('out_p', 'in_p')

@pytest.fixture
def dag():
    """Ensure that each test starts with a clear dag."""

    return Dag(doc='test-dag', title='tests')

def test_empty_sort(dag):
    assert dag.get_sorted() == []

def test_cache1(dag):
    a = PassThrough()
    b = PassThrough()
    dag.connect(a, b, cxn)

    assert dag.get_sorted() == [a, b]

def test_cache1(dag):
    a = PassThrough()
    b = PassThrough()
    dag.connect(b, a, cxn)

    assert dag.get_sorted() == [b, a]

def test_cache_rebuild(dag):
    """Ensure that the sorted block cache is rebuilt correctly."""

    assert dag._sort_cache is None

    a = PassThrough()
    b = PassThrough()
    dag.connect(a, b, cxn)

    assert dag.get_sorted() == [a, b]

    c = PassThrough()
    dag.connect(b, c, cxn)

    assert dag._sort_cache is None

    assert dag.get_sorted() == [a, b, c]

    assert dag._sort_cache is not None
