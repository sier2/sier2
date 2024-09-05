#

# Tutorial that builds a translation dag.
#
from sier2 import Block, Dag, Connection
import param

import random
import re

class UserInput(Block):
    """A block that provides user input."""

    out_text = param.String(label='User input', doc='Text to be translated')
    out_flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

class Translate(Block):
    """A block that transforms text.

    The text is split into paragraphs, then each word has its letters shuffled.
    If flag is set, capitalise each word.
    """

    in_text = param.String(label='Input text', doc='Text to be transformed')
    in_flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')
    out_text = param.String(label='Output text', doc='Transformed text')

    def execute(self):
        paras = re.split(r'\n{2,}', self.in_text)
        para_words = [para.split() for para in paras]
        para_words = [[''.join(random.sample(word, k=len(word))) for word in para] for para in para_words]

        if self.in_flag:
            para_words = [[word.capitalize() for word in para] for para in para_words]

        text = '\n'.join(' '.join(word for word in para) for para in para_words)

        self.out_text = text

class Display(Block):
    """A block that displays text."""

    in_text = param.String(label='Text', doc='Display text')

def main():
    ui = UserInput()
    tr = Translate()
    di = Display()

    dag = Dag(doc='Translation', title='tutorial_2a')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
    dag.connect(tr, di, Connection('out_text', 'in_text'))

    user_text = 'Hello world.'
    print('Input text:')
    print(user_text)
    print()

    ui.out_text = user_text
    ui.out_flag = True
    dag.execute()

    print('Output text:')
    print(di.in_text)
    print()

if __name__=='__main__':
    main()
