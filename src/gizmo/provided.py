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

class AddGizmo(Gizmo):
    """Add two numbers.

    The action does not happen if either of the inputs is None.
    """

    a = param.Integer(label='First integer', default=None, allow_refs=True)
    b = param.Integer(label='Second integer', default=None, allow_refs=True)

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
        _name(cls): cls for cls in [RandomNumberGizmo, AddGizmo]
    }
