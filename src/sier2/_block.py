from enum import StrEnum
import inspect
import param
from typing import Any

from . import _logger
from ._config import Config

class BlockError(Exception):
    """Raised if a Block configuration is invalid.

    If this exception is raised, the executing dag sets its stop
    flag (which must be manually reset), and displays a stacktrace.
    """

    pass

class BlockState(StrEnum):
    """The current state of a block; also used for logging."""

    DAG = 'DAG'                 # Dag logging.
    BLOCK = 'BLOCK'             # Block logging.
    INPUT = 'INPUT'
    READY = 'READY'
    EXECUTING = 'EXECUTING'
    WAITING = 'WAITING'
    SUCCESSFUL = 'SUCCESSFUL'
    INTERRUPTED = 'INTERRUPTED'
    ERROR = 'ERROR'

_WAIT_FOR_INPUT_DOC = '''If True, a block executes in two steps.

When the block is executed by a dag, the dag first sets the input
params, then calls ``prepare()``. Execution of the dag then stops.

The dag is then restarted using ``dag.execute_after_input(input_block)``.
(An input block must be specified because it is not required that the
same input block be used immediately.) This causes the block's
``execute()`` method to be called without resetting the input params.

Dag execution then continues as normal.
'''

# _HAS_PREPARED_DOC = '''Indicates that ``prepare()`` hsabeen called.

# This can be used in a GUI to enable a "Continue" button.
# '''

_VISIBLE_DOC = '''If True, the block will be visible in a GUI.

A block may not need to be visible in a dag with a GUI. For example,
it may be applying a pre-defined filter, or running an algorithm that
takes an indeterminate amount of time. Setting this parameter to False
tells the GUI not display this block. Dag execution will otherwise
proceed as normal.

This is also useful if a GUI application only requires a single block.
A dag requires at least two blocks, because blocks can only be added
by connecting them to another block. By making one block a "dummy"
that is not visible, the GUI effectivly has a single block.
'''

class Block(param.Parameterized):
    """The base class for blocks.

    A block is implemented as:

    .. code-block:: python

        class MyBlock(Block):
            ...

    The ``Block`` class inherits from ``param.Parameterized``, and uses parameters
    as described at https://param.holoviz.org/user_guide/Parameters.html.
    There are three kinds of parameters:
    * Input parameters start with ``in_``. These parameters are set before a block is executed.
    * Output parameters start with ``out_``. The block sets these in its ``execute()`` method.
    * Block parameters start with ``block_``. These are reserved for use by blocks.

    A typical block will have at least one input parameter, and an ``execute()``
    method that is called when an input parameter value changes.

    .. code-block:: python

        class MyBlock(Block):
            \"""Convert strings to uppercase.\"""

            in_value = param.String(label='Input Value')
            out_value = param.String(label='Output value')

            def execute(self):
                self.out_value = self.in_value.upper()

    The block parameter ``wait_for_input`` allows a block to act as an "input" block,
    particularly when the block has a GUI interface. When set to True and dag execution
    reaches this block, the block's ``prepare()`` method is called, then the dag stops executing.
    This allows the user to interact with a user interface.

    The dag is then restarted using ``dag.execute_after_input(input_block)`` (typically by
    a "Continue" button in the GUI.) When the dag is continued at this block,
    the block's ``execute()`` method is called, and dag execution continues.

    Displaying widgets
    ~~~~~~~~~~~~~~~~~~

    When the block is being used in a :class:`~sr2.panel.PanelDag`,
    the block's ``__panel__()`` method is called to display the params.
    The default ``__panel__()`` method supplied by the GUI displays the params returned by :func:`~sr2.Block.pick_params`, using the default Panel widgets for the param types.

    This can be inconvenient - for example, a block that allows the user to select columns
    in a dataframe will have an ``in_df`` param, but may not want to display the dataframe.

    The ``display_options`` parameter can be used to modify this behaviour.

    If ``display_options`` is a list of strings, only those params will be displayed.
    The params need not be limited to those starting with ``in_``.
    The default ``__panel__()`` method will return

    .. code-block:: python

        panel.Param(parameters=display_options)

    If ``display_options`` is a dictionary, it is treated as a ``kwargs`` dictionary and
    passed to ``panel.Param()``. In addition, if "parameters" is not one of the
    dictionary keys, it is added with the result of calling
    :func:`~sr2.Block.pick_params`.

    .. code-block:: python

        panel.Param(**display_options)

    See `Param <https://panel.holoviz.org/reference/panes/Param.html>` for a
    description of ``panel.Param``.

    To define your own custom display, override the ``__panel__()`` method in your block.
    This will override any value of ``display_options``. You can use
    ``self.display_options`` in your own ``__panel__()`` method if you like.
    """

    _wait_for_input = param.Boolean(default=False, label='Wait for input', doc=_WAIT_FOR_INPUT_DOC)
    # _has_prepared = param.Boolean(default=False, label='Has prepared', doc=_HAS_PREPARED_DOC)
    _visible = param.Boolean(default=True, label='Visible', doc=_VISIBLE_DOC)
    _is_card = param.Boolean(default=False, label='Is a card', doc='If True, the default __panel__() is wrapped by a panel.Card')

    _block_state = param.String(default=BlockState.READY)

    is_input_valid_ = param.Boolean(default=False, doc='If wait_for_input is true, indicates that user input is valid.')

    SIER2_KEY = '_sier2__key'

    def __init__(self, *args, wait_for_input: bool=False, visible: bool=True, doc: str|None=None, display_options: list[str]|dict[str, Any]|None=None, only_in=False, continue_label='Continue', is_card: bool=False, **kwargs):
        """
        Parameters
        ----------
        wait_for_input: bool
            If True, ``prepare()`` is called and dag execution stops.
        visible: bool
            If True (the default), the block will be visible in a GUI.
        doc: str|None
            Markdown documentation that may displayed in the user interface.
        display_options: list[str]|dict[str, Any]|None
            Display options to be used when displaying this block in a GUI.
        only_in: bool
            The default Panel display shows all params that begin with "in_"
            or do not begin with "_". Setting only_in to True will cause only "in_"
            parameters to be displayed.
        continue_label: bool
            If wait_for_input is True, a "Continue" button is displayed.
            This changes the label displayed on the button.
        is_card: bool
            If True, the default Panel display is wrapped in a ``panel.Card``.
        """

        super().__init__(*args, **kwargs)

        if not self.__doc__:
            raise BlockError(f'Class {self.__class__} must have a docstring')

        self._wait_for_input = wait_for_input
        self._visible = visible
        self.doc = doc
        self.display_options = display_options
        self.only_in = only_in
        self.continue_label = continue_label
        self._is_card = is_card
        # self._block_state = BlockState.READY
        self.logger = _logger.get_logger(self.name)

        # Maintain a map of "block+output parameter being watched" -> "input parameter".
        # This is used by _block_event() to set the correct input parameter.
        #
        self._block_name_map: dict[tuple[str, str], str] = {}

        # # Record this block's output parameters.
        # # If this is an input block, we need to trigger
        # # the output values before executing the next block,
        # # in case the user didn't change anything.
        # #
        # self._block_out_params = []

    @classmethod
    def block_key(cls):
        """The unique key of this block class.

        Blocks require a unique key so they can be identified in the block library.
        The default implementation should be sufficient, but can be overridden
        in case of refactoring or name clashes.
        """

        im = inspect.getmodule(cls)

        if hasattr(cls, Block.SIER2_KEY):
            return getattr(cls, Block.SIER2_KEY)

        return f'{im.__name__}.{cls.__qualname__}'

    def get_config(self, *, block: 'Block'=None):
        """Return a dictionary containing keys and values from the section specified by
        the block in the sier2 config file.

        The config file has the format described by the Python ``configparser`` module,
        with the added feature that values are evaluated using :func:`ast.literal_eval`,
        and therefore must be syntactically correct Python literals.

        They keys and values are read from the section ``[block.name]``, where ``name`` is
        this block's unique key as specified by :func:`sr2.Block.block_key`.
        If the ``block`` parameter is unspecified, the calling block is used by default.

        If the section is not present in the config file, an empty dictionary is returned.

        The default config file is looked for at
        (the default user config directory) / 'sier2.ini'.
        On Windows, the config directory is ``$ENV:APPDATA``; on Linux, ``$XDG_CONFIG_HOME``
        or ``$HOME/.config``.

        An alternative config file can be specified by setting ``Config.location`` before
        any dag or block is executed. THis can be done from a command line using
        the ``--config`` option.

        Parameters
        ----------
        block: Block
            The specified block's config section will be returned. Defaults to ``self``.

        Returns
        -------
        A dictionary containing the section's keys and values.
        """

        b = block if block is not None else self
        name = f'block.{b.block_key()}'

        return Config[name]

    def pick_params(self) -> list[str]:
        """Return the names of params to be displayed in a GUI.

        If ``self.only_in`` is True, only param names starting with
        ``in_`` are displayed. If ``self.only_in`` is False (the default),
        also include param names that do not start with
        ``out_`` or ``_`` (internal params), end with ``_``, or is not ``name``.

        Returns
        -------
        list[str]
            The names of params to be displayed in a GUI.
        """

        names = [name for name in self.param.values() if name.startswith('in_') or not (self.only_in or name.startswith(('out_', '_')) or name.endswith('_') or name=='name')]

        return names

    def get_config_value(self, key: str, default: Any=None, *, block: 'Block'=None):
        """Return an individual value from the section specified by
        the block in the sier2 config file.

        See :func:`~sr2.Block.get_config` for more details.

        Parameters
        ----------
        key: str
            The key of the value to be returned.
        default: Any
            The default value to return if the section or key are not present in the config file.
        block: Block
            The specified block's config section will be returned. Defaults to ``self``.
        """

        b = block if block is not None else self
        name = f'block.{b.block_key()}'
        value = Config[name, key]

        return value if value is not None else default

    def prepare(self):
        """Called by a dag before calling :func:`~sr2.Dag.execute`.

        If ``self.wait_for_input`` is True, block execution stops after calling
        ``prepare()``. This gives the block author an opportunity to perform
        "pre-execute" actions, such as validating input params or setting up
        a user interface.

        After the dag restarts on this block, :func:`~sr2.Dag.execute` will be called
        without calling ``prepare()``.
        """

        self.is_input_valid_ = True

    def execute(self, *_, **__):
        """This method is called when one or more of the input parameters causes an event.

        Override this method in a Block subclass.

        The ``execute()`` method can have arguments. The arguments can be specified
        in any order. It is not necessary to specify all, or any, arguments.
        Arguments will not be passed via ``*args`` or ``**kwargs``.

        * ``stopper`` - an indicator that the dag has been stopped. This may be
            set while the block is executing, in which case the block should
            stop executing as soon as possible.
        * ``events`` - the param events that caused execute() to be called.
        """

        # print(f'** EXECUTE {self.__class__=}')
        pass

    def _on_continue(self, event):
        """The event handler for the "Continue" button.

        If this block is being run by a dag, the dag has injected a
        dag_continue() method, so just call that - the dag will handle
        the execution of the block.

        Otherwise, execute the block, then call `on_continue()` if it exists.
        """

        if hasattr(self, '_dag_continue'):
            self._dag_continue(event)
        else:
            self.execute()
            if hasattr(self, 'on_continue'):
                self.on_continue(event)

    def __call__(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Allow a block to be called directly and return the output params as a dictionary.

        For example:

        .. code-block:: python

            >>> mb = MyBlock()
            >>> r = ab(in_value='hello')
            >>> print(r)
            {'out_value': 'HELLO'}

        The arguments passed in kwargs must match the block's input ("in\\_") params. Not all input params need to be specified.

        Calling the block calls :func:`~sr2.Block.prepare`, then :func:`~sr2.Block.execute`.

        The result of the call is a dictionary that maps output ("out\\_") names to their param values.

        Parameters
        ----------
        kwargs: dict[str, Any]
            A dictionary of input params and their values.

        Returns
        -------
        dict[str, Any]
            A dictionary that maps output ("out\\_") names to their param values.
        """

        in_names = [name for name in self.__class__.param if name.startswith('in_')]
        if any(name not in in_names for name in kwargs):
            raise BlockError('Only input params can be specified')

        for name, value in kwargs.items():
            setattr(self, name, value)

        self.prepare()
        self.execute()

        out_names = [name for name in self.__class__.param if name.startswith('out_')]
        result = {name: getattr(self, name) for name in out_names}

        return result

    def __panel__(self):
        """A default implementation of a Panel renderer.

        If Block is being used without a GUI (Panel), this method will
        never be called, so it doesn't hurt to have it present.

        If Panel is being used, then this method will inject a default
        ``__panel__()`` implementation into self. THe default implementation
        is not included because it needlessly imports Panel dependencies if
        Panel is not being used.

        A block implementer can therefore do one of these things to provide a Panel GUI.

        - Do nothing (do not implement ``__panel__()``) and let the block display itself.
        - Implement a ``__panel__()`` to provide a custom Panel GUI.
        - Implement ``__panel__()`` and call ``super().__panel__()`` to get the default implementation, then build more Panel widgets around the default (for example, instructions) or modify the default widgets.

        For example, to add some instructions alongside the default render:

        .. code-block:: python

            def __panel__(self):
                return pn.Row(
                    super().__panel__(),
                    pn.widgets.StaticText(
                        name='Instructions',
                        value='Please fill in the fields.'
                    )
                )
        """

        if not hasattr(self, '_panel'):
            from ._panel._default import add_panel_def
            add_panel_def(self)

        return self._panel()

class BlockValidateError(BlockError):
    """Raised if :func:`~sr2.Block.prepare` or :func:`~sr2.Block.execute` determines that input data is invalid.

    If this exception is raised, it will be caught by the executing dag.
    The dag will not set its stop flag, no stacktrace will be displayed,
    and the error message will be displayed.
    """

    def __init__(self, *, block_name: str, message: str):
        """
        Parameters
        ----------
        block_name: str
            The name of the block where the error occured.
        message: str
            A message describing the error.
        """

        super().__init__(message)
        self.block_name = block_name
