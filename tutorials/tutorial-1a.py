#

# Tutorial that builds a translation dag.
#
from gizmo import Gizmo, Dag, Connection
import param

class UserInput(Gizmo):
    """A gizmo that provides user input."""

    # Outputs.
    #
    text = param.String(label='User input', doc='Text to be translated')
    flag = param.Boolean(label='Transform flag', doc='Changes how text is translated')

class Translate(Gizmo):
    """A gizmo that transforms text.

    The text is split into paragraphs, then each word has its letters shuffled.
    If flag is set, capitalize each word.
    """

    # Inputs.
    #
    text_in = param.String(label='Input text', doc='Text to be transformed')
    flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

    # Outputs.
    #
    text_out = param.String(label='Output text', doc='Transformed text')

    def execute(self):
        print(f'{self.flag=} {self.text_in=}')

def main():
    ui = UserInput()
    tr = Translate()

    dag = Dag(doc='Translation')
    dag.connect(ui, tr, Connection('text', 'text_in'), Connection('flag'))

    ui.text = 'Hello world.'
    ui.flag = True

if __name__=='__main__':
    main()
