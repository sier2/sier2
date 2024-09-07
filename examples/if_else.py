from sier2 import Block, Dag, Connection
import param

class IfEvenElseOdd(Block):
    """Demonstrate an if-else branch.

    This block has three outputs: an integer value, and two constant booleans.
    The ``ask_user()`` method takes an integer and determines if it is odd or even.
    The method sets the output parameter from the integer, and triggers either the
    ``true_out`` or ``false_out`` parameter.

    Two downstream blocks are connected by either ``true_out`` or ``false_out``,
    so only the relevant block executes.

    There is more than output parameter, so setting them individually would trigger
    two events, which we don't want. Therefore, the value is set inside a
    ``discard_events()`` context to avoid an event. Since the outputs are always
    ``True`` or ``False``, they can be constants, and ``trigger()` is used.
    """

    out_value = param.Integer()
    out_true = param.Boolean(True, constant=True)
    out_false = param.Boolean(False, constant=True)

    def ask_user(self):
        i = int(input('Enter an integer: '))
        with param.parameterized.discard_events(self):
            self.out_value = i

        tf = 'out_true' if i%2==0 else 'out_false'
        self.param.trigger(tf)

class Notify(Block):
    """Display a message."""

    in_b = param.Boolean()
    in_value = param.Integer()

    def __init__(self, *, name, msg):
        super().__init__(name=name)
        self.msg = msg

    def execute(self):
        print(f'In block {self.name}, {self.in_b} branch: value is {self.msg}')

if_else = IfEvenElseOdd()
is_even = Notify(name='EvenBlock', msg='even')
is_odd = Notify(name='OddBlock', msg='odd')

dag = Dag(doc='Example: run a branch depending on a value', title='run a branch depending on a value')
dag.connect(if_else, is_even,
    Connection('out_true', 'in_b'),
    Connection('out_value', 'in_value')
)
dag.connect(if_else, is_odd,
    Connection('out_false', 'in_b'),
    Connection('out_value', 'in_value')
)

if_else.ask_user()
dag.execute()
