import param

from sier2 import Block


def test_implicit_not_wait():
    class PassThrough(Block):
        """A block with one input and one output."""

        in_p = param.Integer()
        out_p = param.Integer()

        def execute(self):
            self.out_p = self.in_p

    pt = PassThrough()

    assert not pt._wait_for_input


def test_explicit_wait():
    class PassThrough(Block):
        """A block with one input and one output."""

        in_p = param.Integer()
        out_p = param.Integer()

        def __init__(self):
            super().__init__(wait_for_input=True)

        def execute(self):
            self.out_p = self.in_p

    pt = PassThrough()

    assert pt._wait_for_input


def test_class_wait():
    class PassThrough(Block):
        """A block with one input and one output."""

        wait_for_input = True

        in_p = param.Integer()
        out_p = param.Integer()

        def execute(self):
            self.out_p = self.in_p

    pt = PassThrough()

    assert pt._wait_for_input


def test_class_wait_override():
    class PassThrough(Block):
        """A block with one input and one output."""

        wait_for_input = True

        in_p = param.Integer()
        out_p = param.Integer()

        def __init__(self):
            super().__init__(wait_for_input=False)

        def execute(self):
            self.out_p = self.in_p

    pt = PassThrough()

    assert not pt._wait_for_input


#


def test_implicit_continue():
    class PassThrough(Block):
        """A block with one input and one output."""

        in_p = param.Integer()
        out_p = param.Integer()

        def execute(self):
            self.out_p = self.in_p

    pt = PassThrough()

    assert pt._continue_label == 'Continue'


def test_explicit_continue():
    class PassThrough(Block):
        """A block with one input and one output."""

        in_p = param.Integer()
        out_p = param.Integer()

        def __init__(self):
            super().__init__(continue_label='Something')

        def execute(self):
            self.out_p = self.in_p

    pt = PassThrough()

    assert pt._continue_label == 'Something'


def test_class_continue():
    class PassThrough(Block):
        """A block with one input and one output."""

        continue_label = 'Something'

        in_p = param.Integer()
        out_p = param.Integer()

        def execute(self):
            self.out_p = self.in_p

    pt = PassThrough()

    assert pt._continue_label == 'Something'


def test_class_continue_override():
    class PassThrough(Block):
        """A block with one input and one output."""

        continue_label = 'Something'

        in_p = param.Integer()
        out_p = param.Integer()

        def __init__(self):
            super().__init__(continue_label='Else')

        def execute(self):
            self.out_p = self.in_p

    pt = PassThrough()

    assert pt._continue_label == 'Else'
