import panel as pn
from param.parameters import DataFrame

from .._block import Block, BlockError
from ..panel._panel_util import _get_state_color

from typing import Callable
import warnings

def _get_state_light(color: str) -> pn.Spacer:
    return pn.Spacer(
        margin=(8, 0, 0, 0),
        styles={'width':'20px', 'height':'20px', 'background':color, 'border-radius': '10px'}
    )

def _card_for_block(block: Block, pane: pn.pane.Pane, _with_light: bool=False) -> pn.Card:
    """Wrap a block's __panel__() GUI in a panel.Card."""

    name_text = pn.widgets.StaticText(
        value=block.name,
        css_classes=['card-title'],
        styles={'font-size':'1.17em', 'font-weight':'bold'}
    )
    spacer = pn.HSpacer(
        styles=dict(
            min_width='1px', min_height='1px'
        )
    )

    # Does this block have documentation to be displayed in the card?
    #
    doc = pn.pane.Markdown(block.doc, sizing_mode='scale_width') if block.doc else None

    c_button = None
    if block._wait_for_input:
        # Add a "continue" button to restart the dag.
        # The panel GUI is built after dag.execute() runs,
        # so the initial button must reflect the current
        # (negated) is_input_valid_ state.
        #
        c_button = pn.widgets.Button(name=block.continue_label, button_type='primary', align='end', disabled=not block.is_input_valid_)
        c_button.on_click(block._on_continue)

        # Ensure that the button state reflects not is_input_valid_.
        #
        def on_valid(is_input_valid_):
            c_button.disabled = not block.is_input_valid_
        block.param.watch_values(on_valid, 'is_input_valid_')

        row = [doc, c_button] if doc else [c_button]
        w_ = pn.Column(
            pane,
            pn.Row(*row),
            sizing_mode='stretch_width'
        )
    elif doc:
        w_ = pn.Column(block, doc)
    else:
        w_ = block

    row = [name_text, pn.VSpacer()]
    if _with_light:
        row.extend([spacer, _get_state_light(_get_state_color(block._block_state))])

    header = pn.Row(*row)

    if _with_light:
        def state_change(_block_state):#: BlockState):
            """Watcher for the block state.

            Updates the state light.
            """

            header[-1] = _get_state_light(_get_state_color(block._block_state))

        # Watch the block state so we can update the status light.
        #
        block.param.watch_values(state_change, '_block_state')

    # header = pn.Row(
    #     name_text,
    #     pn.VSpacer(),
    #     spacer,
    #     _get_state_light(_get_state_color(block._block_state))
    # )

    card = pn.Card(w_, header=header, sizing_mode='stretch_width')
    # card.continue_button = c_button

    return card

# A default definition of __panel__().
# This exists in its own package so it can be used without dragging in
# everything else in the ``panel`` package. This is useful if using
# standalone blocks without a dag.
#

def _default_panel(self: Block) -> Callable[[Block], pn.Param]:
    """Provide a default __panel__() implementation for blocks that don't have one.

    This is injected into a block as "panel", so self is the Block instance.
    """

    display_options = self.display_options
    if display_options is None:
        display_options = self.pick_params()

    if isinstance(display_options, list):
        # A list of strings of param names.
        # This is the simple way of saying "display these params using their
        # default displays".
        #

        # Check if we need tabulator installed.
        # Ostensibly param uses the DataFrame widget if the tabulator extension
        # isn't present, but this doesn't seem to work properly.
        #
        if any([isinstance(self.param[name], DataFrame) for name in display_options]):
            if 'tabulator' not in pn.extension._loaded_extensions:
                tabulator_warning = f'One of your blocks ({self.__class__.__name__}) requires Tabulator, a panel extension for showing data frames. You should explicitly load this with "pn.extension(\'tabulator\')" in your block'
                warnings.warn(tabulator_warning)
                pn.extension('tabulator')

        pane = pn.Param(self, parameters=display_options, show_name=False)
    elif not isinstance(display_options, dict):
        raise BlockError('display_options must be a list or dict')
    else:
        # A dict of kwargs that is passed to panel.Param().
        # If the "parameters" parameter is not specified,
        # pick the parameters and use those to only show sensible params.
        #
        kwargs = {'show_name': False}
        kwargs.update(display_options)
        if 'parameters' not in kwargs:
            kwargs['parameters'] = self.pick_params()

        pane = pn.Param(self, **kwargs)

    if self._is_card:
        pane = _card_for_block(self, pane, True)

    return pane

def add_panel_def(block: Block):
        """Add the _default_panel function to a block as "_panel".

        Blocks have a default __panel__() method that is called by Panel to provide
        a GUI. The default calls ``self._panel()`` and returns the result.

        Parameters
        ----------
        block: Block
            A block.
        """

        # If a block has no __panel__() method, Panel will by default
        # inspect the class and display the param attributes.
        # This is obviously not what we want.
        #
        # We just want to display the in_ params.
        #
        has_panel = 'panel' in block.__class__.__dict__
        if not has_panel:
            # Go go gadget descriptor protocol.
            #
            block._panel = _default_panel.__get__(block)
