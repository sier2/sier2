import pytest

from sier2 import Dag


@pytest.fixture
def Dag_f():
    """Ensure that each test starts with a clear dag."""

    return lambda connections: Dag(connections, doc='test-dag', title='tests')


@pytest.fixture
def Dag_bag_f():
    """Ensure that each test starts with a clear dag."""

    return lambda connections, bag: Dag(connections, bag=bag, doc='test-dag', title='tests')
