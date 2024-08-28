#

# A basic demonstration of connecting blocks into a dag.
#
# The first block (P) outputs an integer.
# The second block (Q) takes an integer output, and outputs the input+1.
# The third block (R) prints its input.
#

from sier2 import Block, Dag, Connection
import param

class P(Block):
    """A block with a single output parameter."""

    out_p = param.Integer(label='output P')

class Q(Block):
    """A block with a single input and a single output."""

    in_q = param.Integer(label='Int 2', doc='input Q')
    out_q = param.Integer(label='Int 3', doc='output Q')

    def execute(self):
        print(f'{self.name} acting {self.in_q=}')
        self.out_q = self.in_q + 1

class R(Block):
    """A block with a single input."""

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
    {p.out_p= } (expecting {start_number})
    {q.in_q = } (expecting {start_number})
    {q.out_q= } (expecting {start_number+1})
    {r.in_r = } (expecting {start_number+1})
''')
