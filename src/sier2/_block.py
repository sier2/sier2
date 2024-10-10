from enum import StrEnum
import inspect
import param
from typing import Any, Callable
from collections import defaultdict

from . import _logger

class BlockError(Exception):
    """Raised if a Block configuration is invalid."""

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

class Block(param.Parameterized):
    """The base class for blocks.

    A block is implemented as:

    .. code-block:: python

        class MyBlock(Block):
            ...

    A typical block will have at least one input parameter, and an ``execute()``
    method that is called when an input parameter value changes.

    .. code-block:: python

        class MyBlock(Block):
            value_in = param.String(label='Input Value')

            def execute(self):
                print(f'New value is {self.value_in}')
    """

    _block_state = param.String(default=BlockState.READY)

    SIER2_KEY = '_sier2__key'

    def __init__(self, *args, user_input=False, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.__doc__:
            raise BlockError(f'Class {self.__class__} must have a docstring')

        self.user_input = user_input
        self._block_state = BlockState.INPUT if user_input else BlockState.READY
        self.logger = _logger.get_logger(self.name)

        # Maintain a map of "block+output parameter being watched" -> "input parameter".
        # This is used by _block_event() to set the correct input parameter.
        #
        self._block_name_map: dict[tuple[str, str], str] = {}

        # Record this block's output parameters.
        # If this is a user_input block, we need to trigger
        # the output values before executing the next block,
        # in case the user didn't change anything.
        #
        self._block_out_params = []

        # self._block_context = _EmptyContext()

        self._progress = None

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

    def __panel__(self):
        """A default Panel component.

        When run in a Panel context, a block will typically implement
        its own __panel__() method. If it doesn't, this method will be
        used as a default. When a block without a __panel__() is wrapped
        in a Card, self.progress will be assigned a pn.indicators.Progress()
        widget which is returned here. The Panel context will make it active
        before executing the block, and non-active after executing the block.
        (Why not have a default Progress()? Because we don't want any
        Panel-related code in the core implementation.)

        If the block implements __panel__(), this will obviously be overridden.

        When run in non-Panel context, this will remain unused.
        """

        return self._progress

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
