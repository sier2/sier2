#

# Demonstrate that the Gizmo execute() method can have arguments.
# The arguments can be specified in any order.
# It is not necessary to specify all, or any, arguments.
#
# * stopper - an indicator that the dag has been stopped.
# * events -  the param events that caused execute() to be called.
#

from gizmo import Gizmo, Dag, Connection
import param

class P(Gizmo):
    """A gizmo with a single output parameter."""

    one = param.Integer(label='output P')

class Q(Gizmo):
    """A gizmo with a single input and a single output."""

    two = param.Integer(label='Int 2', doc='input Q')

    def execute(self, events, stopper):
        print(f'{stopper=}')
        print(f'{events=}')

p = P()
q = Q()

dag = Dag(doc='Example: execute() args')
dag.connect(p, q, Connection('one', 'two'))

p.one = 1
