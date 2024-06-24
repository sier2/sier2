#

# This demonstrates that two gizmos can provide inputs to a single gizmo.
#
# - NumberGizmo outputs a number.
# - AddGizmo takes outputs from two instances of NumberGizmo and adds them.
#
# AddGizmo must allow for either or both of the inputs being None, and only
# continue if both inputs are valid.
#

import random

from gizmo import Gizmo, Dag, Connection
import param

class NumberGizmo(Gizmo):
    """Produce a random number."""

    n = param.Integer(
        label='An integer',
        doc='What else is there to say',
        default=None
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def go(self):
        r = random.randint(1, 100)
        print(f'{self.name}={r}')
        self.n = r

class AddGizmo(Gizmo):
    """Add two numbers.

    The action does not happen if either of the inputs is None.
    """

    a = param.Integer(label='First integer', default=None)
    b = param.Integer(label='Second integer', default=None)

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def execute(self):
        print(f'Action {self.__class__.__name__} {self.a=} {self.b=}')

        # If some args aren't set, don't do anything.
        #
        if any(arg is None for arg in (self.a, self.b)):
            print('  Not all args set; ducking out.')
            return

        print(f'{self.a} + {self.b} = {self.a+self.b}')

def main():
    """Pretend to be a gizmo manager."""

    nga = NumberGizmo(name='a')
    ngb = NumberGizmo(name='b')
    addg = AddGizmo()

    dag = Dag(doc='Example: add numbers')
    # dag.connect(nga, addg, ['n:a'])
    # dag.connect(ngb, addg, ['n:b'])
    dag.connect(nga, addg, Connection('n', 'a'))
    dag.connect(ngb, addg, Connection('n', 'b'))

    print(f'\nSet gizmo {nga}')
    nga.go()

    print(f'\nSet gizmo {ngb}')
    ngb.go()

if __name__=='__main__':
    main()
