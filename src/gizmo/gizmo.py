import param
from typing import Any, Callable
from collections import defaultdict
import logging
import threading

LOGGER = logging.getLogger(__name__)

class _Stopper:
    def __init__(self):
        self.event = threading.Event()

    @property
    def is_stopped(self):
        return self.event

    @is_stopped.getter
    def is_stopped(self) -> bool:
        return self.event.is_set()

    def __repr__(self):
        return f'stopped={self.is_stopped}'

class GizmoError(Exception):
    """Raised if a Gizmo configuration is invalid."""

    pass

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Maintain a map of "gizmo+output parameter being watched" -> "input parameter".
        # This is used by _gizmo_event() to set the correct input parameter.
        #
        self._gizmo_name_map: dict[tuple[str, str], str] = {}

    @classmethod
    def gizmo_key(cls):
        """The unique key of this gizmo class.

        Gizmos require a unique key so they can be identified in the gizmo library.
        The default implementation should be sufficient, but can be overridden
        in case of refactoring or name clashes.
        """

        return f'{cls.__module__}.{cls.__name__}'

    def _gizmo_event(self, stopper: _Stopper, *events):
        """The callback method for param.watch().

        When watched parameters produce events, this callback is called
        with the events. The events caused by another Gizmo's output params
        are matched with self's input parameter name, and the param
        values are set accordingly.

        If Gizmo.execute() has a parameter, the events are passed as a tuple.
        """

        if stopper.is_stopped:
            return

        # print(f'WATCHER EVENT {self.__class__} {type(events)} {events}')

        # If an input parameter is being watched and is specified more than once,
        # use self.param.update() to only cause one event.
        #
        kwargs = {}
        # print(f'EVENTS: {events}')
        for event in events:
            cls = event.cls.name
            name = event.name
            inp = self._gizmo_name_map[cls, name]
            # print(f'EVENT {cls} {name} {inp} {event.new}')
            kwargs[inp] = event.new

        try:
            self.param.update(**kwargs)
        except ValueError as e:
            msg = f'While in{self.name} setting a parameter: {e}'
            LOGGER.exception(msg)
            stopper.event.set()
            raise GizmoError(msg) from e

        # At least one parameter has changed.
        # Execute this gizmo.
        #
        xparams = self.execute.__code__.co_varnames[1:self.execute.__code__.co_argcount] # type: ignore[misc]
        xkwargs: dict[str, Any] = {}
        for arg in xparams:
            if arg=='stopper':
                xkwargs[arg] = stopper
            elif arg=='events':
                xkwargs[arg] = events
            else:
                raise TypeError(f'Unrecognised argument {arg}')

        LOGGER.debug('execute %s', self.name)
        try:
            self.execute(**xkwargs)
        except Exception as e:
            msg = f'While in {self.name}.execute(): {e}'
            LOGGER.exception(msg)
            stopper.event.set()
            raise GizmoError(msg) from e

    def execute(self, *_, **__):
        """This method is called when one or more of the input parameters causes an event.

        Override this method in a Gizmo subclass.

        The ``execute()`` method can have arguments. The arguments can be specified
        in any order. It is not necessary to specify all, or any, arguments.
        Arguments will not be passed via ``*args`` or ``**kwargs``.

        * ``stopper`` - an indicator that the dag has been stopped. This may be
            set while the gizmo is executing, in which case the gizmo should
            stop executing as soon as possible.
        * ``events`` -  the param events that caused execute() to be called.
        """

        # print(f'** EXECUTE {self.__class__=}')
        pass

# _gizmo_pairs: list[tuple[Gizmo, Gizmo]] = []
