#

# Gizmos provided by a builtin library.
# These are here to demonstrate building a dag from a data structure.
#

from gizmo import Gizmo
import param
import random
from typing import Type

class RandomNumberGizmo(Gizmo):
    """Produce a random number."""

    n = param.Integer(
        label='An integer',
        doc='What else is there to say',
        default=None
    )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def go(self):
        n = random.randint(1, 100)
        print(f'Random: {n}')
        self.n = n

class ConstantNumberGizmo(Gizmo):
    """Produce a constant number specified when the gizmo is created."""

    constant = param.Number(
        label='A constant number',
        doc='The number is determined at gizmo creation time'
    )

    def __init__(self, x, name=None):
        """Initialise the number. Use id(self) to allow two gizmos with the same constant."""

        if name is None:
            name = f'Number{x}-{id(self)}'

        super().__init__(name=name)
        self.x = x

    def go(self):
        self.constant = self.x

class AddGizmo(Gizmo):
    """Add two numbers.

    The action does not happen if either of the inputs is None.
    """

    a = param.Number(label='First number', default=None)
    b = param.Number(label='Second number', default=None)

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def execute(self):
        # If some args aren't set, don't do anything.
        #
        if any(arg is None for arg in (self.a, self.b)):
            return

        print(f'{self.a} + {self.b} = {self.a+self.b}')

def _name(cls):
    return f'{cls.__module__}.{cls.__name__}'

def gizmos() -> dict[str, Type[Gizmo]]:
    return {
        _name(cls): cls for cls in [RandomNumberGizmo, ConstantNumberGizmo, AddGizmo]
    }
