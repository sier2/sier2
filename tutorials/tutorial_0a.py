from sier2 import Block
import param

class AddOne(Block):
    """A block that adds one to its input."""

    in_a = param.Integer()
    out_a = param.Integer()

    def execute(self):
        self.out_a = self.in_a + 1

if __name__=='__main__':
    # Test the block.
    #
    a1_block = AddOne()
    a1_block.in_a = 3
    a1_block.execute()
    print(f'{a1_block.out_a=}')

    # Use the short cut.
    #
    print(a1_block(in_a=3))
