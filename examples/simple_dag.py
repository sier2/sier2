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

    out_p = param.Integer(label='output P')

class Q(Gizmo):
    """A gizmo with a single input and a single output."""

    in_q = param.Integer(label='Int 2', doc='input Q')
    out_q = param.Integer(label='Int 3', doc='output Q')

    def execute(self, *args, **kwargs):
        print(f'{self.name} acting {self.in_q=} {args=} {kwargs=}')
        self.out_q = self.in_q + 1

class R(Gizmo):
    """A gizmo with a single input."""

    in_r = param.Integer(label='Int 4', doc='input R')

    def execute(self):
        print(f'{self.name} acting {self.in_r=}')

p = P()
q = Q()
r = R()

dag = Dag(doc='Simple dag', title='simple dag')
dag.connect(p, q, Connection('out_p', 'in_q'))
dag.connect(q, r, Connection('out_q', 'in_r'))

start_number = 1
p.out_p = start_number
dag.execute()

print(f'''
    {p.out_p=} (expecting {start_number})
    {q.in_q=} (expecting {start_number})
    {q.out_q=} (expecting {start_number+1})
    {r.in_r=} (expecting {start_number+1})
''')
