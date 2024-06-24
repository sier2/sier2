from gizmo import Gizmo, GizmoError, Dag, Connection
import param

class OneOut(Gizmo):
    """One output parameter."""

    o_out = param.String()

class OneIn(Gizmo):
    """One input parameter."""

    o_in = param.String()

    def execute(self):
        raise ValueError('This is an exception')

oo = OneOut()
oi = OneIn()
dag = Dag(doc='Example: raise an exception in execute()')
dag.connect(oo, oi, Connection('o_out', 'o_in'))

try:
    oo.o_out = 'plugh'
except GizmoError as e:
    print(f'\nCaught expected Gizmo exception {e}')
    print(f'Actual cause: {type(e.__cause__)} {e.__cause__}')
else:
    print('SHOULD HAVE CAUGHT AN EXCEPTION HERE!')