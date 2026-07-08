import random

import param

from sier2 import Block, Dag


class ExecuteOrder(Block):
    """Pass a value through unchanged."""

    in_p = param.Integer(default=0)
    out_p = param.Integer(default=0)

    def __init__(self, *args, recorder, **kwargs):
        super().__init__(*args, **kwargs)
        self.recorder = recorder

    def execute(self):
        self.recorder.append(self.name)
        self.out_p = self.in_p


def test_branch1_ab(Dag_f):
    recorder = []
    head = ExecuteOrder(recorder=recorder, name='head')
    a = ExecuteOrder(recorder=recorder, name='a')
    b = ExecuteOrder(recorder=recorder, name='b')

    dag = Dag_f([(head.param.out_p, a.param.in_p), (head.param.out_p, b.param.in_p)])

    dag.execute()

    assert recorder == ['head', 'a', 'b']


def test_branch1_ba(Dag_f):
    recorder = []
    head = ExecuteOrder(recorder=recorder, name='head')
    a = ExecuteOrder(recorder=recorder, name='a')
    b = ExecuteOrder(recorder=recorder, name='b')

    dag = Dag_f([(head.param.out_p, b.param.in_p), (head.param.out_p, a.param.in_p)])

    dag.execute()

    assert recorder == ['head', 'b', 'a']


def test_branch1_bah(Dag_f):
    recorder = []
    head = ExecuteOrder(recorder=recorder, name='head')
    a = ExecuteOrder(recorder=recorder, name='a')
    b = ExecuteOrder(recorder=recorder, name='b')

    dag = Dag_f([(a.param.out_p, b.param.in_p), (head.param.out_p, a.param.in_p)])

    dag.execute()

    assert recorder == ['head', 'a', 'b']


def test_branch1_bah2(Dag_bag_f):
    recorder = []
    x = ExecuteOrder(recorder=recorder, name='x')
    y = ExecuteOrder(recorder=recorder, name='y')
    head1 = ExecuteOrder(recorder=recorder, name='head1')
    head2 = ExecuteOrder(recorder=recorder, name='head2')
    a = ExecuteOrder(recorder=recorder, name='a')
    b = ExecuteOrder(recorder=recorder, name='b')

    dag = Dag_bag_f([(a.param.out_p, b.param.in_p), (head1.param.out_p, a.param.in_p), (head2.param.out_p, a.param.in_p)], [x, y])

    from sier2.debug import Debug

    dag._debug = Debug.DAG_QUEUE

    dag.execute()

    assert recorder == ['x', 'y', 'head1', 'head2', 'a', 'b']


def test_branch2_abc(Dag_f):
    recorder = []
    head = ExecuteOrder(recorder=recorder, name='head')
    a = ExecuteOrder(recorder=recorder, name='a')
    b = ExecuteOrder(recorder=recorder, name='b')
    c = ExecuteOrder(recorder=recorder, name='c')

    dag = Dag_f([(head.param.out_p, a.param.in_p), (a.param.out_p, b.param.in_p), (head.param.out_p, c.param.in_p)])

    dag.execute()

    assert recorder == ['head', 'a', 'b', 'c']


def test_branch2_acb(Dag_f):
    recorder = []
    head = ExecuteOrder(recorder=recorder, name='head')
    a = ExecuteOrder(recorder=recorder, name='a')
    b = ExecuteOrder(recorder=recorder, name='b')
    c = ExecuteOrder(recorder=recorder, name='c')

    dag = Dag_f([(head.param.out_p, a.param.in_p), (head.param.out_p, c.param.in_p), (a.param.out_p, b.param.in_p)])

    dag.execute()

    assert recorder == ['head', 'a', 'c', 'b']


def test_branch_wait_abc(Dag_f):
    recorder = []
    head = ExecuteOrder(recorder=recorder, name='head')
    a = ExecuteOrder(recorder=recorder, name='a')
    b = ExecuteOrder(recorder=recorder, name='b')
    c = ExecuteOrder(recorder=recorder, name='c', wait_for_input=True)

    dag = Dag_f([(head.param.out_p, a.param.in_p), (a.param.out_p, b.param.in_p), (head.param.out_p, c.param.in_p)])

    b = dag.execute()
    while b:
        b = dag.execute_after_input(b)

    assert recorder == ['head', 'a', 'b', 'c']


def test_branch_wait_acb(Dag_f):
    recorder = []
    head = ExecuteOrder(recorder=recorder, name='head')
    a = ExecuteOrder(recorder=recorder, name='a')
    b = ExecuteOrder(recorder=recorder, name='b')
    c = ExecuteOrder(recorder=recorder, name='c', wait_for_input=True)

    dag = Dag_f([(head.param.out_p, a.param.in_p), (head.param.out_p, c.param.in_p), (a.param.out_p, b.param.in_p)])

    b = dag.execute()
    while b:
        b = dag.execute_after_input(b)

    assert recorder == ['head', 'a', 'c', 'b']
