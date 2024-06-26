#

# Tutorial: UserInput gizmo with a panel widget.
#
from gizmo import Gizmo, Dag, Connection
import param

import panel as pn
pn.extension(inline=True)

class UserInput(Gizmo):
    """A gizmo that provides user input."""

    text = param.String(label='User input', doc='Text to be translated')
    flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

    def __panel__(self):
        text_in_widget = pn.widgets.TextAreaInput(
            name='Input text',
            placeholder='Enter text here',
            auto_grow=True,
            rows=8,
            max_rows=24,
            resizable='both',
            sizing_mode='stretch_width',
            value='The quick brown\nfox jumps over the lazy\ndog.\n'
        )
        flag_widget = pn.widgets.Checkbox(name='Capitalize', value=False, align='center')

        def on_button(event):
            # print(f'{text_in_widget.value=}, {flag_widget.value=}')
            self.param.update(
                text=text_in_widget.value,
                flag=flag_widget.value
            )

        button = pn.widgets.Button(name='Translate', button_type='primary', align='end')
        pn.bind(on_button, button, watch=True)

        return pn.Column(
            text_in_widget,
            pn.Row(flag_widget, button, align='end')
        )
