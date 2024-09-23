from sier2 import Block, Connection
from sier2.panel import PanelDag
import panel as pn
import param

class NumberBlock(Block):
    """Take user input and output it."""

    out_number = param.Number(label='Output number', default=None, doc='Output number')

    def __init__(self, number, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.out_number = number

    def __panel__(self):
        return pn.widgets.FloatInput.from_param(self.param.out_number)

class AddBlock(Block):
    """Add two numbers.

    The action does not happen if either of the inputs is None.
    """

    in_a = param.Number(label='First number', default=None, doc='First number')
    in_b = param.Number(label='Second number', default=None, doc='Second number')
    out_result = param.Number(label='Result', default=None, doc='Result of addding in_a and in_b')

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def execute(self):
        self.logger.debug('Execute block (debug)')
        self.logger.info('Execute block (info)')
        self.logger.warning('Execute block (warning)')
        self.logger.error('Execute block (error)')
        self.logger.critical('Execute block (critical)')

        self.logger.warning('Execute %s', self.name)
        self.logger.info('Inputs: a=%s b=%s', self.in_a, self.in_b)

        # If any args aren't set, don't do anything.
        #
        if any(arg is None for arg in (self.in_a, self.in_b)):
            self.logger.warning('None value in a=%s b=%s', self.in_a, self.in_b)
            return

        self.out_result = self.in_a+self.in_b
        # print(f'{self.in_a} + {self.in_b} = {self.out_result}')

    def __panel__(self):
        return pn.widgets.FloatInput.from_param(self.param.out_result)

class Display(Block):
    """Display a number."""

    in_result = param.Number(label='Result', default=None, doc='The result')

    def __panel__(self):
        return pn.widgets.FloatInput.from_param(self.param.in_result)

if __name__=='__main__':
    n1 = NumberBlock(3, name='num1', user_input=True)
    n2 = NumberBlock(5, name='num2', user_input=True)
    n3 = NumberBlock(7,name='num3', user_input=True)
    aa = AddBlock(name='First add')
    ab = AddBlock(name='Second add')
    display = Display()

    dag = PanelDag(site='examples', title='Logging', doc='Demonstrate logging')
    dag.connect(n1, aa, Connection('out_number', 'in_a'))
    dag.connect(n2, aa, Connection('out_number', 'in_b'))
    dag.connect(aa, ab, Connection('out_result', 'in_a'))
    dag.connect(n3, ab, Connection('out_number', 'in_b'))
    dag.connect(ab, display, Connection('out_result', 'in_result'))

    dag.show()
