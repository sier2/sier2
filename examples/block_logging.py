#

# Demonstrate how to do logging in a block.
#
# Blocks are provided with a logger in self.logger.
# This is a stanndard Python logger implemented using the logger module,
# so read the Python documentation for details.
#
# All blocks use the same logger, wrapped with an adapter that provides
# each block's name. Therefore, changing the log level on any block
# changes the log level on all blocks.
#

from sier2 import Block, Dag, Connection
import param
import logging

class NumberBlock(Block):
    """Take user input and output it."""

    out_number = param.Number(label='Output number', default=None, doc='Output number')

class AddBlock(Block):
    """Add two numbers.

    The action does not happen if either of the inputs is None.
    """

    in_a = param.Number(label='First number', default=None, doc='First number')
    in_b = param.Number(label='Second number', default=None, doc='Second number')
    out_result = param.Number(label='Result', default=None, doc='Result of addding in_a and in_b')

    def execute(self):
        self.logger.debug('Execute block (debug)')
        self.logger.info('Execute block (info)')
        self.logger.warning('Execute block (warning)')
        self.logger.error('Execute block (error)')
        self.logger.critical('Execute block (critical)')

        self.logger.info('Inputs: a=%s b=%s', self.in_a, self.in_b)

        # If any args aren't set, don't do anything.
        #
        if any(arg is None for arg in (self.in_a, self.in_b)):
            return

        self.out_result = self.in_a+self.in_b
        self.logger.debug('Result is %s', self.out_result)
        # print(f'{self.in_a} + {self.in_b} = {self.out_result}')

class Display(Block):
    """Display a number."""

    in_result = param.Number(label='Result', default=None, doc='The result')

if __name__=='__main__':
    n1 = NumberBlock()
    n2 = NumberBlock()
    n3 = NumberBlock(user_input=True)
    aa = AddBlock(name='First add')
    ab = AddBlock(name='Second add')
    display = Display()
    # display.logger.setLevel(logging.INFO)

    dag = Dag(title='Logging', doc='Demonstrate logging')
    dag.connect(n1, aa, Connection('out_number', 'in_a'))
    dag.connect(n2, aa, Connection('out_number', 'in_b'))
    dag.connect(aa, ab, Connection('out_result', 'in_a'))
    dag.connect(n3, ab, Connection('out_number', 'in_b'))
    dag.connect(ab, display, Connection('out_result', 'in_result'))

    print('level debug')
    aa.logger.setLevel(logging.DEBUG)
    n1.out_number = 2
    n2.out_number = 3
    n3.out_number = 5
    dag.execute()

    assert display.in_result == 10

    print()
    print('level warning')
    aa.logger.setLevel(logging.WARNING)
    n1.out_number = 7
    n2.out_number = 11
    n3.out_number = 13
    dag.execute()

    assert display.in_result == 31
