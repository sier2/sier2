#

# This example deemonstrates that a dag can be run in textual context
# and panel context.
#
# The Calc block just sets its output from its inputs via a lengthy
# calculation, and does not implement a __panel__() method.
# In text context, nothing happens, but in Panel context,
# a default __panel__() method containing an indefinite progress bar
# is provided, and made active while the block is executing.
#

from sier2 import Block, Dag, Connection
from sier2.panel import PanelDag
import param
import panel as pn
import sys
import time

class In(Block):
    """input values."""

    out_a = param.Number(label='a')
    out_b = param.Number(label='b')

    def __panel__(self):
        aw = pn.widgets.FloatInput.from_param(
            self.param.out_a,
            name='input a'
        )
        bw = pn.widgets.FloatInput.from_param(
            self.param.out_b,
            name='input b'
        )

        return pn.Row(aw, bw)

class Calc(Block):
    """Calculate values.

    This block delberately does not implement a __panel__() method.

    The print calls in execute() are purely for indicative purposes.
    """

    in_a = param.Number(label='a')
    in_b = param.Number(label='b')
    out_result = param.Number(label='result')

    def execute(self):
        print(f'calc {self.in_a=} {self.in_b=}')

        delay = 2
        print(f'sleep({delay})')
        time.sleep(delay)

        self.out_result = self.in_a + self.in_b
        print('calc end')

class Out(Block):
    """Display result."""

    in_r = param.Number(label='result')

    def __panel__(self):
        rw = pn.widgets.FloatInput.from_param(
            self.param.in_r,
            name='result.'
        )

        return pn.Row(rw)

def make_dag(DagType):
    in_block = In(name='do inputs', user_input=True)
    calc_block = Calc(name='do calc')
    out_block = Out(name='do result')

    dag = DagType(title='The dag', doc='Demonstrate panel-less blocks.')
    dag.connect(
        in_block, calc_block,
        Connection('out_a', 'in_a'),
        Connection('out_b', 'in_b')
    )
    dag.connect(
        calc_block, out_block,
        Connection('out_result', 'in_r')
    )

    return dag

def main(context):
    is_text = context=='text'

    dag = make_dag(Dag if is_text else PanelDag)
    inb = dag.block_by_name('do inputs')
    inb.out_a = 8
    inb.out_b = 9

    if is_text:
        dag.execute()
        r = dag.block_by_name('do calc').out_result
        print(f'{r=}')
    else:
        dag.show()

if __name__=='__main__':
    context = sys.argv[1] if len(sys.argv)>1 else None
    if context in ('text', 'panel'):
        main(context)
    else:
        print('Specify "text" or "panel" as an argument.')
