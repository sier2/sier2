#

# A basic demonstration of connecting gizmos into a dag.
#
# The first gizmo (P) outputs an integer.
# The second gizmo (Q) takes an integer output, and outputs the input+1.
# The third gizmo (R) prints its input.
#

from gizmo import Gizmo, Dag, Connection
import param

class P(Gizmo):
    """A gizmo with a single output parameter."""

    one = param.Integer(label='output P')

class Q(Gizmo):
    """A gizmo with a single input and a single output."""

    two = param.Integer(label='Int 2', doc='input Q')
    three = param.Integer(label='Int 3', doc='output Q')

    def execute(self, *args, **kwargs):
        print(f'Q acting {self.two=} {args=} {kwargs=}')
        self.three = self.two + 1

class R(Gizmo):
    """A gizmo with a single input."""

    four = param.Integer(label='Int 4', doc='input R')

    def execute(self):
        print(f'R acting {self.four=}')

p = P()
q = Q()
r = R()

dag = Dag(doc='Simple dag')
dag.connect(p, q, Connection('one', 'two'))
dag.connect(q, r, Connection('three', 'four'))

start_number = 1
p.one = start_number

print(f'''
    {p.one=} (expecting {start_number})
    {q.two=} (expecting {start_number})
    {q.three=} (expecting {start_number+1})
    {r.four=} (expecting {start_number+1})
''')
