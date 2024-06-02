import param
from typing import Callable
from collections import defaultdict

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

    def _gizmo_event(self, *events):
        """The callback method for param.watch().

        When watched parameters produce events, this callback is called
        with the events. The events are matched with self's input parameter name,
        and sets the parameter values accordingly.

        If Gizmo.execute() has a parameter, the events are passed as a tuple.
        """

        # print(f'WATCHER EVENT {self.__class__} {type(events)} {events}')

        # If an input parameter is being watched and is specified more than once,
        # use self.param.update() to only cause one event.
        #
        kwargs = {}
        for event in events:
            # print(f'ARG: {event.cls.name=} {event.name=} {event.new=}')
            cls = event.cls.name
            name = event.name
            inp = self._gizmo_name_map[cls, name]
            kwargs[inp] = event.new

        self.param.update(**kwargs)

        # At least one parameter has changed.
        # Execute this gizmo.
        #
        if self.execute.__code__.co_argcount==1:
            self.execute()
        else:
            self.execute(events)

    def execute(self, *args, **kwargs):
        """This method is called when one or more of the input parameters causes an event.

        Override this method in a Gizmo subclass.

        If ``execute()`` has a parameter, the triggered events will be passed as a tuple.
        """

        # print(f'** EXECUTE {self.__class__=}')
        pass

# _gizmo_pairs: list[tuple[Gizmo, Gizmo]] = []
