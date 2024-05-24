import param
from typing import Callable

# By default, loops in a flow DAG aren't allowed.
#
_DISALLOW_LOOPS = True

class GizmoError(Exception):
    pass

class Gizmo(param.Parameterized):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._gizmo_name_map = {}

    def _gizmo_event(self, *events):
        # print(f'WATCHER EVENT {self.__class__} {events}')
        for event in events:
            # print(f'ARG: {event.cls.name=} {event.name=} {event.new=}')
            cls = event.cls.name
            name = event.name
            inp = self._gizmo_name_map[cls, name]
            setattr(self, inp, event.new)

        # At least one parameter has changed.
        # Execute this gizmo.
        #
        self.execute()

    def execute(self):
        # print(f'** EXECUTE {self.__class__=}')
        pass

_gizmo_graph: list[tuple[Gizmo, Gizmo]] = []

def _has_loop(src: Gizmo, dst: Gizmo) -> bool:
    """Find loops in the gizmo graph.

    Use _gizmo_graph to build a dictionary of relative ranks
    based on src -> dst connections. If the new src has a
    greater rank than the new dst, then a loop would be created.

    It's probably a bit inefficient to redo the ranks for every
    new connection, but we don't have to maintain another global,
    and I doubt if any flow will be big enough for anyone to notice.

    Returns
    -------
    bool
        True if connecting src to dst would create a loop.
    """

    if src is dst:
        # A self-loop.
        #
        raise GizmoError('Gizmos cannot be connected to themselves')

    if not _gizmo_graph:
        # Can't create a loop if there is only one connection.
        #
        return False

    # A unique key for a gizmo.
    #
    uniq: Callable[[Gizmo], int] = lambda g: id(g)

    rank = 0
    ranks: dict[int, int] = {}
    for s, d in _gizmo_graph + [(src, dst)]:
        sid = uniq(s)
        did = uniq(d)
        if sid in ranks and did in ranks:
            # Both gizmos are already in the graph.
            # Not a problem (a bit strange, though).
            #
            pass
        elif sid not in ranks and did not in ranks:
            # Neither gizmo is in the graph,
            # so they don't connect to anything else.
            # Not a problem.
            #
            ranks[sid] = rank
            ranks[did] = rank + 1
            rank += 2
        elif sid not in ranks:
            ranks[sid] = ranks[did] - 1
        elif did not in ranks:
            ranks[did] = ranks[sid] + 1

    srank = ranks[uniq(src)]
    drank = ranks[uniq(dst)]

    if srank < drank:
        return False

    return True

class GizmoManager:
    @staticmethod
    def clear() -> None:
        """Clear the flow graph."""

        _gizmo_graph.clear()

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

        if _DISALLOW_LOOPS:
            if _has_loop(src, dst):
                raise GizmoError('This connection would create a loop')

        src_out_params = []
        for name in param_names:
            names = name.split(':')
            if len(names)==1:
                outp = inp = names[0]
            elif len(names)==2:
                outp, inp = names
            else:
                raise GizmoError(f'Name {name} cannot have more than one ":"')

            dstp = getattr(dst.param, inp)
            if not dstp.allow_refs:
                raise GizmoError(f'Destination parameter {dst}.{inp} must be "allow_refs=True"')

            srcp = getattr(src.param, outp)
            if srcp.allow_refs:
                raise GizmoError(f'Source parameter {src}.{outp} must not be "allow_refs=True"')

            dst._gizmo_name_map[src.name, outp] = inp
            src_out_params.append(outp)

        # print(f'{dst} watch {src} {src_out_params}')
        watcher = src.param.watch(dst._gizmo_event, src_out_params, onlychanged=onlychanged, queued=queued, precedence=precedence)

        _gizmo_graph.append((src, dst))

    @staticmethod
    def disconnect(g: Gizmo) -> None:
        """Disconnect gizmo g from other gizmos.

        We can look in the gizmo to see what it is watching,
        but we need to look through all the other gizmos to see
        if they watch this one.
        """

        for p, watchers in g.param.watchers.items():
            for watcher in watchers['value']:
                # print(f'disconnect watcher {g.name}.{watcher}')
                g.param.unwatch(watcher)

        for src, dst in _gizmo_graph:
            if dst is g:
                for p, watchers in src.param.watchers.items():
                    for watcher in watchers['value']:
                        # print(f'disconnect watcher {src.name}.{watcher}')
                        src.param.unwatch(watcher)

        _gizmo_graph[:] = [(src, dst) for src, dst in _gizmo_graph if src is not g and dst is not g]
