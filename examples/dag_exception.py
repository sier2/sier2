from gizmo import Gizmo, Dag, Connection
import param

class OneOut(Gizmo):
    o_out = param.String()

class OneIn(Gizmo):
    o_in = param.String()

    def execute(self):
        raise ValueError('This is an exception')

oo = OneOut()
oi = OneIn()
dag = Dag()
dag.connect(oo, oi, Connection('o_out', 'o_in'))

oo.o_out = 'plugh'
