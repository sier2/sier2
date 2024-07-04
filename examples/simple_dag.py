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

    po = param.Integer(label='output P')

class Q(Gizmo):
    """A gizmo with a single input and a single output."""

    qi = param.Integer(label='Int 2', doc='input Q')
    qo = param.Integer(label='Int 3', doc='output Q')

    def execute(self, *args, **kwargs):
        print(f'{self.name} acting {self.qi=} {args=} {kwargs=}')
        self.qo = self.qi + 1

class R(Gizmo):
    """A gizmo with a single input."""

    ri = param.Integer(label='Int 4', doc='input R')

    def execute(self):
        print(f'{self.name} acting {self.ri=}')

p = P()
q = Q()
r = R()

dag = Dag(doc='Simple dag')
dag.connect(p, q, Connection('po', 'qi'))
dag.connect(q, r, Connection('qo', 'ri'))

start_number = 1
p.po = start_number
dag.execute()

print(f'''
    {p.po=} (expecting {start_number})
    {q.qi=} (expecting {start_number})
    {q.qo=} (expecting {start_number+1})
    {r.ri=} (expecting {start_number+1})
''')
