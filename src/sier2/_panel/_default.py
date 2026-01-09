import panel as pn
from param.parameters import DataFrame

from .._block import Block, BlockError

from typing import Callable
import warnings

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

        return pn.Param(self, parameters=display_options, show_name=False)
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

        return pn.Param(self, **kwargs)

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
