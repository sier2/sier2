from gizmo import Gizmo, Dag
import param

class IfEvenElseOdd(Gizmo):
    """Demonstrate an if-else branch.

    This gizmo has three outputs: an integer value, and two constant booleans.
    The ``user_input()`` method takes an integer and determines if it is odd or even.
    The method sets the output parameter from the integer, and triggers either the
    ``true_out`` or ``false_out`` parameter.

    Two downstream gizmos are connected by either ``true_out`` or ``false_out``,
    so only the relevant gizmo executes.

    There is more than output parameter, so setting them individually would trigger
    two events, which we don't want. Therefore, the value is set inside a
    ``discard_events()`` context to avoid an event. Since the outputs are always
    ``True`` or ``False``, they can be constants, and ``trigger()` is used.
    """

    value = param.Integer()
    true_out = param.Boolean(True, constant=True)
    false_out = param.Boolean(False, constant=True)

    def user_input(self):
        i = int(input('Enter an integer: '))
        with param.parameterized.discard_events(self):
            self.value = i

        tf = 'true_out' if i%2==0 else 'false_out'
        self.param.trigger(tf)

class Notify(Gizmo):
    b = param.Boolean()
    value = param.Integer()

    def __init__(self, msg):
        super().__init__()
        self.msg = msg

    def execute(self):
        print(f'In gizmo {self.name}, {self.b} branch: value is {self.msg}')

if_else = IfEvenElseOdd()
is_even = Notify('even')
is_odd = Notify('odd')

dag = Dag()
dag.connect(if_else, is_even, ['true_out:b', 'value'])
dag.connect(if_else, is_odd, ['false_out:b', 'value'])

if_else.user_input()
