#

# Tutorial: gizmos with panel widgets.
#
from gizmo import Gizmo, Dag, Connection
import param

import random
import re
import time

import panel as pn
# pn.extension(inline=True)

class UserInput(Gizmo):
    """A gizmo that provides user input."""

    out_text = param.String(label='Input text', doc='Text to be translated')
    out_flag = param.Boolean(label='Capitalise', doc='Changes how text is transformed')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.out_text = 'The quick brown\nfox jumps over the lazy\ndog.\n\nThe end.'

    def __panel__(self):
        text_widget = pn.widgets.TextAreaInput.from_param(
            self.param.out_text,
            name='Input text',
            placeholder='Enter text here',
            auto_grow=True,
            rows=8,
            resizable='both',
            sizing_mode='stretch_width'
        )

        return pn.Column(
            text_widget,
            pn.Row(pn.HSpacer(), self.param.out_flag, sizing_mode='stretch_width'),
            sizing_mode='stretch_width'
        )

class Translate(Gizmo):
    """A gizmo that transforms text.

    The text is split into paragraphs, then each word has its letters shuffled.
    If flag is set, capitlaize each word.
    """

    in_text = param.String(label='Input text', doc='Text to be transformed')
    in_flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')
    out_text = param.String(label='Output text', doc='Transformed text')

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
            if not self.in_text:
                raise ValueError('Empty text not valid')

            paras = re.split(r'\n', self.in_text)
            para_words = [para.split() for para in paras]
            para_words = [[''.join(random.sample(word, k=len(word))) for word in para] for para in para_words]

            if self.in_flag:
                para_words = [[word.capitalize() for word in para] for para in para_words]

            text = '\n'.join(' '.join(word for word in para) for para in para_words)

            # Emulate work being done.
            #
            time.sleep(random.random() * 2.0)

            self.out_text = text

        finally:
            self.progress.active = False

    def __panel__(self):
        return self.progress

class Display(Gizmo):
    """A gizmo that displays text."""

    in_text = param.String(label='Text', doc='Display text')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.text_widget = pn.widgets.TextAreaInput(
            name='Output text',
            placeholder='Translated text goes here',
            auto_grow=True,
            rows=8,
            resizable='both',
            sizing_mode='stretch_width',
            disabled=True,
            stylesheets=['.bk-input[disabled]{background-color:var(--current-background-color);color:var(--panel-on-secondary-color);opacity:1.0;cursor:text}']
        )

    def execute(self):
        self.text_widget.value = self.in_text

    def __panel__(self):
        return self.text_widget
