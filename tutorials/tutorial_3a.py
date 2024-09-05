#

# Tutorial: UserInput block with a panel widget.
#
from sier2 import Block, Dag, Connection
import param

import panel as pn
pn.extension(inline=True)

class UserInput(Block):
    """A block that provides user input."""

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
