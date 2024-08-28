from sier2 import Block, BlockError, Dag, Connection
import param

class OneOut(Block):
    """One output parameter."""

    out_o = param.String()

class OneIn(Block):
    """One input parameter."""

    in_o = param.String()

    def execute(self):
        raise ValueError('This is an exception')

oo = OneOut()
oi = OneIn()
dag = Dag(doc='Example: raise an exception in execute()', title='raise an exception')
dag.connect(oo, oi, Connection('out_o', 'in_o'))

try:
    oo.out_o = 'plugh'
    dag.execute()
except BlockError as e:
    print(f'\nCaught expected Block exception {e}')
    print(f'Actual cause: {type(e.__cause__)} {e.__cause__}')
else:
    print('SHOULD HAVE CAUGHT AN EXCEPTION HERE!')