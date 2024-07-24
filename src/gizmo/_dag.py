from ._gizmo import Gizmo, GizmoError, GizmoState
from dataclasses import dataclass, field #, KW_ONLY, field
from collections import defaultdict, deque
import holoviews as hv
import threading
from typing import Any

# By default, loops in a dag aren't allowed.
#
_DISALLOW_CYCLES = True

@dataclass
class Connection:
    """Define a connection between an output parameter and an input parameter."""

    src_param_name: str
    dst_param_name: str
    # _: KW_ONLY
    # onlychanged: bool = False
    # queued: bool = False
    # precedence: int = 0

    def __post_init__(self):
        if not self.src_param_name.startswith('out_'):
            raise GizmoError('Output params must start with "out_"')

        if not self.dst_param_name.startswith('in_'):
            raise GizmoError('Input params must start with "in_"')

@dataclass
class _InputValues:
    """Record a param value change.

    When a gizmo updates an output param, the update is queued until
    the gizmo finishes executing. This class is what is queued.
    """

    # The gizmo to be updated.
    #
    dst: Gizmo

    # The values to be set before the gizmo executes.
    #
    values: dict[str, Any] = field(default_factory=dict)

class _GizmoContext:
    """A context manager to wrap the execution of a gizmo within a dag.

    This default context manager handles the gizmo state, the stopper,
    and converts gizmo execution errors to GimzoError exceptions.

    This could be done inline, but using a context manager allows
    the context manager to be replaced. For example, a panel-based
    dag runner could use a context manager that incorporates logging
    and displays information in a GUI.
    """

    def __init__(self, gizmo: Gizmo, dag: 'Dag'):
        self.gizmo = gizmo
        self.dag = dag

    def __enter__(self):
        self.gizmo._gizmo_state = GizmoState.EXECUTING

        return self.gizmo

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.gizmo._gizmo_state = GizmoState.WAITING if self.gizmo.user_input else GizmoState.SUCCESSFUL
        elif isinstance(exc_type, KeyboardInterrupt):
            self.gizmo_state._gizmo_state = GizmoState.INTERRUPTED
            self.dag._stopper.event.set()
            print(f'KEYBOARD INTERRUPT IN GIZMO {self.name}')
        else:
            self.gizmo._gizmo_state = GizmoState.ERROR
            msg = f'While in {self.gizmo.name}.execute(): {exc_val}'
            # LOGGER.exception(msg)
            self.dag._stopper.event.set()

            # Convert the error in the gizmo to a GizmoError.
            #
            raise GizmoError(f'Gizmo {self.gizmo.name}: {str(exc_val)}') from exc_val

        return False

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

class Dag:
    """A directed acyclic graph of gizmos."""

    def __init__(self, *, site: str, title: str, doc: str):
        self._gizmo_pairs: list[tuple[Gizmo, Gizmo]] = []
        self._stopper = _Stopper()
        self.site = site
        self.title = title
        self.doc = doc

        # We watch output params to be notified when they are set.
        # Events are queued here.
        #
        self._gizmo_queue: deque[_InputValues] = deque()

    def _for_each_once(self):
        """Yield each connected gizmo once."""

        seen = set()
        for s, d in self._gizmo_pairs:
            for g in s, d:
                if g not in seen:
                    seen.add(g)
                    yield g

    def stop(self):
        """Stop further execution of Gizmo instances in this dag."""

        self._stopper.event.set()

    def unstop(self):
        """Enable further execution of Gizmo instances in this dag."""

        self._stopper.event.clear()

    def connect(self, src: Gizmo, dst: Gizmo, *connections: Connection):
        if any(not isinstance(c, Connection) for c in connections):
            raise GizmoError('All arguments must be Connection instances')

        if _DISALLOW_CYCLES:
            if _has_cycle(self._gizmo_pairs + [(src, dst)]):
                raise GizmoError('This connection would create a cycle')

        if src.name==dst.name:
            raise GizmoError('Cannot add two gizmos with the same name')

        for g in self._for_each_once():
            if (g is not src and g.name==src.name) or (g is not dst and g.name==dst.name):
                raise GizmoError('A gizmo with this name already exists')

        for s, d in self._gizmo_pairs:
            if src is s and dst is d:
                raise GizmoError('These gizmos are already connected')

        if self._gizmo_pairs:
            connected = any(src is s or src is d or dst is s or dst is d for s, d in self._gizmo_pairs)
            if not connected:
                raise GizmoError('New gizmos must connect to existing gizmos')

        # Group watchers by their attributes.
        # This optimises the number of watchers.
        #
        # If we just add a watcher per param in the loop, then
        # param.update() won't batch the events.
        #
        # src_out_params = defaultdict(list)
        src_out_params = []

        for conn in connections:
            # dst_param = getattr(dst.param, conn.dst_param_name)
            # if dst_param.allow_refs:
            #     raise GizmoError(f'Destination parameter {dst}.{inp} must be "allow_refs=True"')

            src_param = getattr(src.param, conn.src_param_name)
            if src_param.allow_refs:
                raise GizmoError(f'Source parameter {src}.{conn.src_param_name} must not be "allow_refs=True"')

            dst._gizmo_name_map[src.name, conn.src_param_name] = conn.dst_param_name
            # src_out_params[conn.onlychanged, conn.queued, conn.precedence].append(conn.src_param_name)
            src_out_params.append(conn.src_param_name)

            # print(f'**** WATCH {src} {src_out_params} -> {dst} {src_out_params}')
            # watcher = src.param.watch(dst._gizmo_event, [conn.src_param_name], onlychanged=conn.onlychanged, queued=conn.queued, precedence=conn.precedence)

        # for (onlychanged, queued, precedence), names in src_out_params.items():
        # for names in src_out_params:
        src.param.watch(lambda *events: self._param_event(dst, *events), src_out_params, onlychanged=False)
        src._gizmo_out_params.extend(src_out_params)

            # src.param.watch(lambda *events: dst._gizmo_event(self._stopper, *events), names, onlychanged=onlychanged, queued=queued, precedence=precedence)

        self._gizmo_pairs.append((src, dst))

    def _param_event(self, dst: Gizmo, *events):
        """The callback for a watch event."""

        # print(f'DAG EVENTS: {events} -> {dst.name}')
        for event in events:
            cls = event.cls.name
            name = event.name
            new = event.new

            # The input param in the dst gizmo.
            #
            inp = dst._gizmo_name_map[cls, name]

            # Look for the destination gizmo in the event queue.
            # If found, update the param value dictionary,
            # else append a new item.
            # This ensures that all param updates for a destination
            # gizmo are merged into a single queue item, even if the
            # updates come from different source gizmos.
            #
            for item in self._gizmo_queue:
                if dst is item.dst:
                    item.values[inp] = new
                    break
            else:
                item = _InputValues(dst)
                item.values[inp] = new
                self._gizmo_queue.append(item)

    def execute(self):
        """Execute the dag.

        The dag is executed by iterating through the gizmo events queue
        and popping events from the head of the queue. For each event,
        update the destination gizmo's input parameters and call
        that gizmo's execute() method.

        If the current destination gizmo has user_flag True,
        the loop will continue to set param values until the queue is empty,
        but no execute() method will be called.

        To start (or restart) the dag, there must be something in the event queue.
        The first (or current) user_input gizmo must have updated at least one
        output param before the dag's execute() is called.
        """

        if not self._gizmo_queue:
            # Attempting to execute a dag with no updates is probably a mistake.
            #
            raise GizmoError('Nothing to execute')

        can_execute = True
        while self._gizmo_queue:
            # The user has set the "stop executing" flag.
            # Continue to set params, but don't execute anything
            #
            if self._stopper.is_stopped:
                can_execute = False

            item = self._gizmo_queue.popleft()
            try:
                item.dst.param.update(item.values)
            except ValueError as e:
                msg = f'While in {item.dst.name} setting a parameter: {e}'
                self._stopper.event.set()
                raise GizmoError(msg) from e

            if can_execute:
                with _GizmoContext(item.dst, self) as g:
                    g.execute()
                # try:
                #     item.dst._gizmo_state = GizmoState.EXECUTING
                #     item.dst.execute()
                #     item.dst._gizmo_state = GizmoState.WAITING if item.dst.user_input else GizmoState.SUCCESSFUL
                # except Exception as e:
                #     item.dst._gizmo_state = GizmoState.ERROR
                #     msg = f'While in {item.dst.name}.execute(): {e}'
                #     # LOGGER.exception(msg)
                #     self._stopper.event.set()
                #     raise GizmoError(msg) from e
                # except KeyboardInterrupt:
                #     item.dst._gizmo_state = GizmoState.INTERRUPTED
                #     self._stopper.event.set()
                #     print(f'KEYBOARD INTERRUPT IN GIZMO {item.dst.name}')

            if item.dst.user_input:
                # If the current destination gizmo requires user input,
                # continue to set params, but don't execute anything.
                #
                can_execute = False

    def disconnect(self, g: Gizmo) -> None:
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

        for src, dst in self._gizmo_pairs:
            if dst is g:
                for p, watchers in src.param.watchers.items():
                    for watcher in watchers['value']:
                        # print(f'disconnect watcher {src.name}.{watcher}')
                        src.param.unwatch(watcher)

        # Remove this gizmo from the dag.
        # Check for sources and destinations.
        #
        self._gizmo_pairs[:] = [(src, dst) for src, dst in self._gizmo_pairs if src is not g and dst is not g]

        # Because this gizmo is no longer watching anything, the name map can be cleared.
        #
        g._gizmo_name_map.clear()

    def gizmo_by_name(self, name) -> Gizmo | None:
        """Get a specific gizmo by name."""

        for s, d in self._gizmo_pairs:
            if s.name==name:
                return s

            if d.name == name:
                return d

        return None

    def get_sorted(self):
        """Return the gizmos in this dag in topological order.

        This is useful for arranging the gizmos in a GUI, for example.

        The returned dictionary is in no particular order:
        the rank values determine the order of the gizmos.

        Returns
        -------
        dict[Gizmo, int]
            A mapping of gizmo to rank
        """

        return _get_sorted(self._gizmo_pairs)

    def has_cycle(self):
        return _has_cycle(self._gizmo_pairs)

    def dump(self):
        """Dump the dag to a serialisable (eg to JSON) dictionary.

        The gizmos and connections are reduced to simple representations.
        There is no need to serialize code: the gizmos themselves are assumed
        to be available when loaded - it is just the attributes of the gizmos
        that need to be saved.

        Two sets of attributes in particular are saved.

        * The name of the gizmo class. Each gizmo has a name by virtue of it
            being a Parameterized subclass.
        * The ``__init__`` parameters, where possible. For each parameter,
            if the gizmo object has a matching instance name, the value of
            the name is saved.

        Returns
        -------
        dict
            A dictionary containing the serialised dag.
        """

        gizmo_instances: dict[Gizmo, int] = {}

        instance = 0
        for s, d in self._gizmo_pairs:
            if s not in gizmo_instances:
                gizmo_instances[s] = instance
                instance += 1
            if d not in gizmo_instances:
                gizmo_instances[d] = instance
                instance += 1

        gizmos = []
        for g, i in gizmo_instances.items():
            # We have to pass some arguments to the gizmo when it is reconstituted.
            # `name` is mandatory - what else?
            #
            args = {'name': g.name}

            # What are __init__'s plain Python parameters?
            # The first parameter is always self - skip that.
            #
            vars = g.__init__.__code__.co_varnames[1:g.__init__.__code__.co_argcount] # type: ignore[misc]
            for var in vars:
                if hasattr(g, var):
                    args[var] = getattr(g, var)

            # TODO is there a better way of checking for user_input?
            if hasattr(g, 'user_input'):
                args['user_input'] = getattr(g, 'user_input')

            gizmo = {
                'gizmo': g.gizmo_key(),
                'instance': i,
                'args': args
            }
            gizmos.append(gizmo)

        connections = []
        for s, d in self._gizmo_pairs:
            connection: dict[str, Any] = {
                'src': gizmo_instances[s],
                'dst': gizmo_instances[d],
                'conn_args': []
            }

            # Get src params that have been connected to dst params.
            #
            nmap = {(gname, sname): dname for (gname, sname), dname in d._gizmo_name_map.items() if gname==s.name}

            for (gname, sname), dname in nmap.items():
                args = {
                    'src_param_name': sname,
                    'dst_param_name': dname
                }

                # for pname, data in s.param.watchers.items():
                #     if pname==sname:
                #         for watcher in data['value']:
                #             args['onlychanged'] = watcher.onlychanged
                #             args['queued'] = watcher.queued
                #             args['precedence'] = watcher.precedence


                connection['conn_args'].append(args)

            connections.append(connection)

        return {
            'dag': {
                'doc': self.doc,
                'site': self.site,
                'title': self.title
            },
            'gizmos': gizmos,
            'connections': connections
        }

    def hv_graph(self):
        """Build a HoloViews Graph to visualise the gizmo connections."""

        src: list[Gizmo] = []
        dst: list[Gizmo] = []

        def build_layers():
            """Traverse the gizmo pairs and organise them into layers.

            The first layer contains the root (no input) nodes.
            """

            ranks = {}
            remaining = self._gizmo_pairs[:]

            # Find the root nodes and assign them a layer.
            #
            src[:], dst[:] = zip(*remaining)
            S = list(set([s for s in src if s not in dst]))
            for s in S:
                ranks[s.name] = 0

            n_layers = 1
            while remaining:
                for s, d in remaining:
                    if s.name in ranks:
                        # This destination could be from sources at different layers.
                        # Make sure the deepest one is used.
                        #
                        ranks[d.name] = max(ranks.get(d.name, 0), ranks[s.name] + 1)
                        n_layers = max(n_layers, ranks[d.name])

                remaining = [(s,d) for s,d in remaining if d.name not in ranks]

            return n_layers, ranks

        def layout(_):
            """Arrange the graph nodes."""

            max_width = 0

            # Arrange the graph y by layer from top to bottom.
            # For x, for no we start at 0 and +1 in each layer.
            #
            yx = {y:0 for y in ranks.values()}
            gxy = {}
            for g, y in ranks.items():
                gxy[g] = [yx[y], y]
                yx[y] += 1
                max_width = max(max_width, yx[y])

            # Balance out the x in each layer.
            #
            for y in range(n_layers+1):
                layer = {name: xy for name,xy in gxy.items() if xy[1]==y}
                if len(layer)<max_width:
                    for x, (name, xy) in enumerate(layer.items(), 1):
                        gxy[name][0] = x/max_width

            return gxy

        n_layers, ranks = build_layers()

        src_names = [g.name for g in src]
        dst_names = [g.name for g in dst]
        g = hv.Graph(((src_names, dst_names),))

        return hv.element.graphs.layout_nodes(g, layout=layout)

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

    while S:
        n = S.pop(0)
        L.append(n)
        for _, m in remaining[:]:
            if (e:=edge(remaining, n, m))is not None:
                del remaining[e]
                if not has_incoming(remaining, m):
                    S.append(m)

    return L, remaining

def _has_cycle(gizmo_pairs: list[tuple[Gizmo, Gizmo]]):
    _, remaining = topological_sort(gizmo_pairs)

    return len(remaining)>0

def _get_sorted(gizmo_pairs: list[tuple[Gizmo, Gizmo]]):
    ordered, remaining = topological_sort(gizmo_pairs)

    if remaining:
        raise GizmoError('Dag contains a cycle')

    return ordered

