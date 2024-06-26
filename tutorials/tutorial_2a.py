#

# Tutorial that builds a translation dag.
#
from gizmo import Gizmo, Dag, Connection
import param

import random
import re

class UserInput(Gizmo):
    """A gizmo that provides user input."""

    text = param.String(label='User input', doc='Text to be translated')
    flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

class Translate(Gizmo):
    """A gizmo that transforms text.

    The text is split into paragraphs, then each word has its letters shuffled.
    If flag is set, capitlaize each word.
    """

    text_in = param.String(label='Input text', doc='Text to be transformed')
    flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')
    text_out = param.String(label='Output text', doc='Transformed text')

    def execute(self):
        paras = re.split(r'\n{2,}', self.text_in)
        para_words = [para.split() for para in paras]
        para_words = [[''.join(random.sample(word, k=len(word))) for word in para] for para in para_words]

        if self.flag:
            para_words = [[word.capitalize() for word in para] for para in para_words]

        text = '\n\n'.join(' '.join(word for word in para) for para in para_words)

        self.text_out = text

class Display(Gizmo):
    """A gizmo that displays text."""

    text = param.String(label='Text', doc='Display text')

def main():
    ui = UserInput()
    tr = Translate()
    di = Display()

    dag = Dag(doc='Translation')
    dag.connect(ui, tr, Connection('text', 'text_in'), Connection('flag'))
    dag.connect(tr, di, Connection('text_out', 'text'))

    user_text = 'Hello world.'
    print('Input text:')
    print(user_text)
    print()

    ui.param.update(
        text=user_text,
        flag=True
    )

    print('Output text:')
    print(di.text)
    print()

if __name__=='__main__':
    main()
