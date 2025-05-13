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

_PAUSE_EXECUTION_DOC = '''If True, a block executes in two steps.

When the block is executed by a dag, the dag first sets the input
params, then calls ``prepare()``. Execution of the dag then stops.

The dag is then restarted using ``dag.execute_after_input(input_block)``.
(An input block must be specified because it is not required that the
same input block be used immediately.) This causes the block's
``execute()`` method to be called without resetting the input params.

Dag execution then continues as normal.
'''

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
    * Block parameters start with ``block_``. THese are reserved for use by blocks.

    A typical block will have at least one input parameter, and an ``execute()``
    method that is called when an input parameter value changes.

    .. code-block:: python

        class MyBlock(Block):
            in_value = param.String(label='Input Value')
            out_upper = param.String(label='Output value)

            def execute(self):
                self.out_value = self.in_value.upper()
                print(f'New value is {self.out_value}')

    The block parameter ``block_pause_execution`` allows a block to act as an "input" block,
    particularly when the block hsa a GUI interface. When set to True and dag execution
    reaches this block, the block's ``prepare()`` method is called, then the dag stops executing.
    This allows the user to interact with a user interface.

    The dag is then restarted using ``dag.execute_after_input(input_block)`` (typically by
    a "Continue" button in the GUI.) When the dag is continued at this block,
    the block's ``execute()`` method is called, and dag execution continues.
    """

    block_pause_execution = param.Boolean(default=False, label='Pause execution', doc=_PAUSE_EXECUTION_DOC)
    block_visible = param.Boolean(default=True, label='Display block', doc=_VISIBLE_DOC)

    _block_state = param.String(default=BlockState.READY)

    SIER2_KEY = '_sier2__key'

    def __init__(self, *args, block_pause_execution: bool=False, block_visible: bool=True, block_doc: str|None=None, continue_label='Continue', **kwargs):
        """
        Parameters
        ----------
        block_pause_execution: bool
            If True, ``prepare()`` is called and dag execution stops.
        block_visible: bool
            If True (the default), the block will be visible in a GUI.
        block_doc: str|None
            Markdown documentation that may displayed in the user interface.
        """
        super().__init__(*args, **kwargs)

        if not self.__doc__:
            raise BlockError(f'Class {self.__class__} must have a docstring')

        self.block_pause_execution = block_pause_execution
        self.block_visible = block_visible
        self.block_doc = block_doc
        self.continue_label = continue_label
        # self._block_state = BlockState.READY
        self.logger = _logger.get_logger(self.name)

        # Maintain a map of "block+output parameter being watched" -> "input parameter".
        # This is used by _block_event() to set the correct input parameter.
        #
        self._block_name_map: dict[tuple[str, str], str] = {}

        # Record this block's output parameters.
        # If this is an input block, we need to trigger
        # the output values before executing the next block,
        # in case the user didn't change anything.
        #
        self._block_out_params = []

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
        this block's unique key as specified by :func:`sier2.Block.block_key`.
        If the ``block`` parameter is unspecified, the calling block is used by default.

        If the section is not present in the config file, an empty dictionary is returned.

        The default config file is looked for at
        (the default user config directory) / 'sier2sier2.ini'.
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

    def get_config_value(self, key: str, default: Any=None, *, block: 'Block'=None):
        """Return an individual value from the section specified by
        the block in the sier2 config file.

        See :func:`sier2.Block.get_config` for more details.

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
        """If blockpause_execution is True, called by a dag before calling ``execute()```.

        This gives the block author an opportunity to validate the
        input params and set up a user inteface.

        After the dag restarts on this block, ``execute()`` will be called.
        """

        pass

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

    def __call__(self, **kwargs) -> dict[str, Any]:
        """Allow a block to be called directly."""

        in_names = [name for name in self.__class__.param if name.startswith('in_')]
        if len(kwargs)!=len(in_names) or any(name not in in_names for name in kwargs):
            names = ', '.join(in_names)
            raise BlockError(f'All input params must be specified: {names}')

        for name, value in kwargs.items():
            setattr(self, name, value)

        self.execute()

        out_names = [name for name in self.__class__.param if name.startswith('out_')]
        result = {name: getattr(self, name) for name in out_names}

        return result

class BlockValidateError(BlockError):
    """Raised if ``Block.prepare()`` or ``Block.execute()`` determines that input data is invalid.

    If this exception is raised, it will be caught by the executing dag.
    The dag will not set its stop flag, no stacktrace will be displayed,
    and the error message will be displayed.
    """

    def __init__(self, *, block_name: str, error: str):
        super().__init__(error)
        self.block_name = block_name
