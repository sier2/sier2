from enum import IntEnum, auto
import param
from typing import Any, Callable
from collections import defaultdict
import logging

LOGGER = logging.getLogger(__name__)

class _EmptyContext:
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class GizmoError(Exception):
    """Raised if a Gizmo configuration is invalid."""

    pass

class GizmoState(IntEnum):
    """The current state of this gizmo."""

    INPUT = auto()
    READY = auto()
    EXECUTING = auto()
    WAITING = auto()
    SUCCESSFUL = auto()
    INTERRUPTED = auto()
    ERROR = auto()

class Gizmo(param.Parameterized):
    """The base class for gizmos.

    A gizmo is implemented as:

    .. code-block:: python

        class MyGizmo(Gizmo):
            ...

    A typical gizmo will have at least one input parameter, and an ``execute()``
    method that is called when an input parameter value changes.

    .. code-block:: python

        class MyGizmo(Gizmo):
            value_in = param.String(label='Input Value')

            def execute(self):
                print(f'New value is {self.value_in}')
    """

    _gizmo_state = param.Integer(default=GizmoState.READY)

    def __init__(self, *args, user_input=False, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.__doc__:
            raise GizmoError(f'Class {self.__class__} must have a docstring')

        self.user_input = user_input
        self._gizmo_state = GizmoState.INPUT if user_input else GizmoState.READY

        # Maintain a map of "gizmo+output parameter being watched" -> "input parameter".
        # This is used by _gizmo_event() to set the correct input parameter.
        #
        self._gizmo_name_map: dict[tuple[str, str], str] = {}

        # Record this gizmo's output parameters.
        # If this is a user_input gizmo, we need to trigger
        # the output values before executing the next gizmo,
        # in case the user didn't change anything.
        #
        self._gizmo_out_params = []

        self._gizmo_context = _EmptyContext()

    @classmethod
    def gizmo_key(cls):
        """The unique key of this gizmo class.

        Gizmos require a unique key so they can be identified in the gizmo library.
        The default implementation should be sufficient, but can be overridden
        in case of refactoring or name clashes.
        """

        return f'{cls.__module__}.{cls.__name__}'

    def execute(self, *_, **__):
        """This method is called when one or more of the input parameters causes an event.

        Override this method in a Gizmo subclass.

        The ``execute()`` method can have arguments. The arguments can be specified
        in any order. It is not necessary to specify all, or any, arguments.
        Arguments will not be passed via ``*args`` or ``**kwargs``.

        * ``stopper`` - an indicator that the dag has been stopped. This may be
            set while the gizmo is executing, in which case the gizmo should
            stop executing as soon as possible.
        * ``events`` - the param events that caused execute() to be called.
        """

        # print(f'** EXECUTE {self.__class__=}')
        pass

    def __call__(self, **kwargs) -> dict[str, Any]:
        """Allow a gizmo to be called directly."""

        in_names = [name for name in self.__class__.param if name.startswith('in_')]
        if len(kwargs)!=len(in_names) or any(name not in in_names for name in kwargs):
            names = ', '.join(in_names)
            raise GizmoError(f'All input params must be specified: {names}')

        for name, value in kwargs.items():
            setattr(self, name, value)

        self.execute()

        out_names = [name for name in self.__class__.param if name.startswith('out_')]
        result = {name: getattr(self, name) for name in out_names}

        return result
