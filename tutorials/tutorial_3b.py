#

# Tutorial: gizmos with panel widgets.
#
from gizmo import Gizmo, Dag, Connection
import param

import random
import re
import time

import panel as pn
pn.extension(inline=True)

class UserInput(Gizmo):
    """A gizmo that provides user input."""

    text = param.String(label='User input', doc='Text to be translated')
    flag = param.Boolean(label='Capitalise', doc='Changes how text is transformed')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = 'The quick brown\nfox jumps over the lazy\ndog.\n\nThe end.'

    def __panel__(self):
        text_widget = pn.widgets.TextAreaInput.from_param(
            self.param.text,
            name='Input text',
            placeholder='Enter text here',
            auto_grow=True,
            rows=8,
            resizable='both',
            sizing_mode='stretch_both'
        )

        return pn.Column(
            text_widget,
            pn.Row(self.param.flag, align='end')
        )

class Translate(Gizmo):
    """A gizmo that transforms text.

    The text is split into paragraphs, then each word has its letters shuffled.
    If flag is set, capitlaize each word.
    """

    text_in = param.String(label='Input text', doc='Text to be transformed')
    flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')
    text_out = param.String(label='Output text', doc='Transformed text')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.progress = pn.indicators.Progress(
            name='Translation progress',
            bar_color='primary',
            active=False,
            value=-1
        )

    def execute(self):
        self.progress.active = True
        try:
            paras = re.split(r'\n', self.text_in)
            para_words = [para.split() for para in paras]
            para_words = [[''.join(random.sample(word, k=len(word))) for word in para] for para in para_words]

            if self.flag:
                para_words = [[word.capitalize() for word in para] for para in para_words]

            text = '\n'.join(' '.join(word for word in para) for para in para_words)

            # Emulate work being done.
            #
            time.sleep(random.random() * 2.0)

            self.text_out = text

        finally:
            self.progress.active = False

    def __panel__(self):
        return self.progress

class Display(Gizmo):
    """A gizmo that displays text."""

    text = param.String(label='Text', doc='Display text')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.text_out = pn.widgets.TextAreaInput(
            name='Output text',
            placeholder='Translated text goes here',
            auto_grow=True,
            rows=8,
            resizable='both',
            sizing_mode='stretch_both',
            disabled=True,
            stylesheets=['.bk-input[disabled]{background-color:var(--current-background-color);color:var(--panel-on-secondary-color);opacity:1.0;cursor:text}']
        )

    def execute(self):
        self.text_out.value = self.text

    def __panel__(self):
        return self.text_out

if __name__=='__main__':
    ui = UserInput(name='User input')
    tr = Translate(name='Translate')
    di = Display(name='Display output')

    dag = Dag(doc='Translation')
    dag.connect(ui, tr, Connection('text', 'text_in'), Connection('flag'))
    dag.connect(tr, di, Connection('text_out', 'text'))

    pn.Column(ui, tr, di).show()
