import param
from typing import Callable
from collections import defaultdict

# By default, loops in a flow DAG aren't allowed.
#
_DISALLOW_CYCLES = True

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

    def execute(self):
        """This method is called when one or more of the input parameters causes an event.

        Override this method in a Gizmo subclass.

        If ``execute()`` has a parameter, the triggered events will be passed as a tuple.
        """

        # print(f'** EXECUTE {self.__class__=}')
        pass

_gizmo_pairs: list[tuple[Gizmo, Gizmo]] = []

def topological_sort(pairs):
    """Implement a topological sort as described at
    `Topological sorting <https://en.wikipedia.org/wiki/Topological_sorting>`_.

    code-block:: python

        L ← Empty list that will contain the sorted elements
        S ← Set of all nodes with no incoming edge

        while S is not empty do
            remove a node n from S
            add n to L
            for each node m with an edge e from n to m do
                remove edge e from the graph
                if m has no other incoming edges then
                    insert m into S

        if graph has edges then
            return error   (graph has at least one cycle)
        else
            return L   (a topologically sorted order)
    """

    def edge(pairs, n, m):
        for ix, pair in enumerate(pairs):
            if pair==(n, m):
                return ix

        return None

    def has_incoming(pairs, m):
        return any(d is m for _,d in pairs)

    remaining = pairs[:]
    L = []

    srcs, dsts = zip(*remaining)
    S = list(set([s for s in srcs if s not in dsts]))
    # print(S)

    while S:
        n = S.pop(0)
        L.append(n)
        print(f'{n=}')
        for _, m in remaining[:]:
            if (e:=edge(remaining, n, m))is not None:
                del remaining[e]
                if not has_incoming(remaining, m):
                    S.append(m)

    # print(f'Remaining: {remaining}')
    return L, remaining

def _has_cycle(gizmo_pairs: list[tuple[Gizmo, Gizmo]]):
    _, remaining = topological_sort(gizmo_pairs)

    return len(remaining)>0

def _get_sorted(gizmo_pairs: list[tuple[Gizmo, Gizmo]]):
    ordered, remaining = topological_sort(gizmo_pairs)

    if remaining:
        raise GizmoError('flow contains a cycle')

    return ordered

class GizmoManager:
    @staticmethod
    def clear() -> None:
        """Clear the flow graph."""

        _gizmo_pairs.clear()

    @staticmethod
    def connect(src: Gizmo, dst: Gizmo, param_names: list[str], *, onlychanged=False, queued=False, precedence=0):
        """Connect parameters in a source gizmo to parameters in a destination gizmo.

        Connecting parameters in two gizmos creates a watcher for each pair of parameters.
        Assigning a value to an output parameter triggers an event that is handled
        by a callback method in the destination gizmo that sets the corresponding input
        parameter and calls ``dst.execute()``.

        The `param_names`` list specifies the parameters that should be connected.
        For example::

            GizmoManager.connect(query, report, ['result:data'])

        connects ``query.result`` to ``report.data``, so that setting ``query.result``
        causes ``report.data`` to be updated and ``report.execute()`` to be called.

        If the output and input parameters have the same name, only the one name is required.::

            GizmoManager.connect(query, report, [':data'])

        connects ``query.date`` to ``report.data``.

        Input parameters must have ``allow_refs=True``. This is used solely as a check
        to differentiate inputs from outputs - it isn't actually used as a reference.

        The ``onlychanged``, ``queued``, and ``precedence`` values are passed through
        to ``src.param.watch()``.

        Parameters
        ----------
        src: Gizmo
            A Gizmo with output parameters.
            Output parameters must be specified with ``allow_refs=False`` (the default).
        dst: Gizmo
            A Gizmo with input parameters.
            Input parameters must be specified with ``allow_refs=True``.
        param_names: list[str]
            A list of 'out_param:in_param' strings.
        onlychanged: bool
            By default, always triggers an event when the
            watched parameter changes, but if ``onlychanged=True`` only triggers
            an event when the parameter is set to something other than its current value.
            Note that this is the opposite of the param default.
        queued: bool
            By default, additional watcher events generated
            inside the callback method are dispatched immediately, effectively
            doing depth-first processing of Watcher events. However, in
            certain scenarios, it is helpful to wait to dispatch such
            downstream events until all events that triggered this watcher
            have been processed. In such cases setting ``queued=True`` on
            this Watcher will queue up new downstream events generated
            during the callback until it completes and all other watchers
            invoked by that same event have finished executing),
            effectively doing breadth-first processing of Watcher events.
        precedence: int
            Declares a precedence level for the Watcher that
            determines the priority with which the callback is executed.
            Lower precedence levels are executed earlier. Negative
            precedences are reserved for internal Watchers, i.e. those
            set up by param.depends.
        """

        if _DISALLOW_CYCLES:
            if _has_cycle(_gizmo_pairs + [(src, dst)]):
                raise GizmoError('This connection would create a cycle')

        src_out_params = []
        for name in param_names:
            names = name.split(':')
            if len(names)==1:
                outp = inp = names[0]
            elif len(names)==2:
                outp, inp = names
            else:
                raise GizmoError(f'Name {name} cannot have more than one ":"')

            # dstp = getattr(dst.param, inp)
            # if not dstp.allow_refs:
            #     raise GizmoError(f'Destination parameter {dst}.{inp} must be "allow_refs=True"')

            srcp = getattr(src.param, outp)
            if srcp.allow_refs:
                raise GizmoError(f'Source parameter {src}.{outp} must not be "allow_refs=True"')

            dst._gizmo_name_map[src.name, outp] = inp
            src_out_params.append(outp)

        # print(f'{dst} watch {src} {src_out_params}')
        watcher = src.param.watch(dst._gizmo_event, src_out_params, onlychanged=onlychanged, queued=queued, precedence=precedence)

        _gizmo_pairs.append((src, dst))

    @staticmethod
    def disconnect(g: Gizmo) -> None:
        """Disconnect gizmo g from other gizmos.

        All parameters (input and output) will be disconnected.

        Parameters
        ----------
        g: Gizmo
            The gizmo to be disconnected.
        """

        for p, watchers in g.param.watchers.items():
            for watcher in watchers['value']:
                # print(f'disconnect watcher {g.name}.{watcher}')
                g.param.unwatch(watcher)

        for src, dst in _gizmo_pairs:
            if dst is g:
                for p, watchers in src.param.watchers.items():
                    for watcher in watchers['value']:
                        # print(f'disconnect watcher {src.name}.{watcher}')
                        src.param.unwatch(watcher)

        # Remove this gizmo from the graph.
        # Check for sources and destinations.
        #
        _gizmo_pairs[:] = [(src, dst) for src, dst in _gizmo_pairs if src is not g and dst is not g]

        # Because this gizmo is no longer watching anything, the name map can be cleared.
        #
        g._gizmo_name_map.clear()

    @staticmethod
    def get_sorted():
        """Return the gizmos in this dag in topological order.

        This is useful for arranging the gizmos in a GUI, for example.

        The returned dictionary is in no particular order:
        the rank values determine the order of the gizmos.

        Returns
        -------
        dict[Gizmo, int]
            A mapping of gizmo to rank
        """

        return _get_sorted(_gizmo_pairs)

    @staticmethod
    def has_cycle():
        return _has_cycle(_gizmo_pairs)

    @staticmethod
    def gizmo_pairs():
        return _gizmo_pairs
