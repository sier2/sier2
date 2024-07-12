from gizmo import Gizmo, GizmoError, Dag, Connection
import param

class OneOut(Gizmo):
    """One output parameter."""

    out_o = param.String()

class OneIn(Gizmo):
    """One input parameter."""

    in_o = param.String()

    def execute(self):
        raise ValueError('This is an exception')

oo = OneOut()
oi = OneIn()
dag = Dag(doc='Example: raise an exception in execute()')
dag.connect(oo, oi, Connection('out_o', 'in_o'))

try:
    oo.out_o = 'plugh'
    dag.execute()
except GizmoError as e:
    print(f'\nCaught expected Gizmo exception {e}')
    print(f'Actual cause: {type(e.__cause__)} {e.__cause__}')
else:
    print('SHOULD HAVE CAUGHT AN EXCEPTION HERE!')