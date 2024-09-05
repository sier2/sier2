#

# Tutorial that builds a translation dag.
#
from sier2 import Block, Dag, Connection
import param

class UserInput(Block):
    """A block that provides user input."""

    # Outputs.
    #
    out_text = param.String(label='User input', doc='Text to be translated')
    out_flag = param.Boolean(label='Transform flag', doc='Changes how text is translated')

class Translate(Block):
    """A block that transforms text.

    The text is split into paragraphs, then each word has its letters shuffled.
    If flag is set, capitalize each word.
    """

    # Inputs.
    #
    in_text = param.String(label='Input text', doc='Text to be transformed')
    in_flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

    # Outputs.
    #
    out_text = param.String(label='Output text', doc='Transformed text')

    def execute(self):
        print(f'in execute: {self.in_flag=} {self.in_text=}')
        text = self.in_text.upper() # Translate.
        if self.in_flag:
            text = f'[{text}]' # Optional transform.

        self.out_text = text

def main():
    ui = UserInput()
    tr = Translate()

    dag = Dag(doc='Translation', title='tutorial_1a')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))

    ui.out_text = 'Hello world.'
    ui.out_flag = True
    dag.execute()

    print(f'{tr.out_text=}')

if __name__=='__main__':
    main()
