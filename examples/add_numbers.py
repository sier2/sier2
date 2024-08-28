#

# This demonstrates that two blocks can provide inputs to a single block.
#
# - NumberGizmo outputs a number.
# - AddGizmo takes outputs from two instances of NumberGizmo and adds them.
#
# AddGizmo must allow for either or both of the inputs being None, and only
# continue if both inputs are valid.
#

import random

from sier2 import Block, Dag, Connection
import param

class NumberBlock(Block):
    """Produce a random number."""

    out_n = param.Integer(
        label='An integer',
        doc='What else is there to say',
        default=None
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def go(self):
        r = random.randint(1, 100)
        print(f'{self.name}={r}')
        self.out_n = r

class AddBlock(Block):
    """Add two numbers.

    The action does not happen if either of the inputs is None.
    """

    in_a = param.Integer(label='First integer', default=None)
    in_b = param.Integer(label='Second integer', default=None)

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def execute(self):
        print(f'Action {self.__class__.__name__} {self.in_a=} {self.in_b=}')

        # If some args aren't set, don't do anything.
        #
        if any(arg is None for arg in (self.in_a, self.in_b)):
            print('  Not all args set; ducking out.')
            return

        print(f'{self.in_a} + {self.in_b} = {self.in_a+self.in_b}')

def main():
    """Pretend to be a block manager."""

    nga = NumberBlock(name='source-of-a')
    ngb = NumberBlock(name='source-of-b')
    addg = AddBlock()

    dag = Dag(doc='Example: add numbers', title='add numbers')
    dag.connect(nga, addg, Connection('out_n', 'in_a'))
    dag.connect(ngb, addg, Connection('out_n', 'in_b'))

    print(f'\nSet block {nga}')
    nga.go()

    print(f'\nSet block {ngb}')
    ngb.go()

    print()
    dag.execute()

if __name__=='__main__':
    main()
