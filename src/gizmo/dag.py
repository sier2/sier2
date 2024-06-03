from .gizmo import Gizmo, GizmoError
import holoviews as hv
from typing import Any

# By default, loops in a dag aren't allowed.
#
_DISALLOW_CYCLES = True

class Dag:
    """The manager of a directed acyclic graph of gizmos."""

    def __init__(self):
        self._gizmo_pairs: list[tuple[Gizmo, Gizmo]] = []

    def _for_each_once(self):
        """Yield each connected gizmo once."""

        seen = set()
        for s, d in self._gizmo_pairs:
            for g in s, d:
                if g not in seen:
                    seen.add(g)
                    yield g

    def connect(self, src: Gizmo, dst: Gizmo, param_names: list[str], *, onlychanged=False, queued=False, precedence=0):
        """Connect parameters in a source gizmo to parameters in a destination gizmo.

        Connecting parameters in two gizmos creates a watcher for each pair of parameters.
        Assigning a value to an output parameter triggers an event that is handled
        by a callback method in the destination gizmo that sets the corresponding input
        parameter and calls ``dst.execute()``.

        The `param_names`` list specifies the parameters that should be connected.
        For example::

            dag.connect(query, report, ['result:data'])

        connects ``query.result`` to ``report.data``, so that setting ``query.result``
        causes ``report.data`` to be updated and ``report.execute()`` to be called.

        If the output and input parameters have the same name, only the one name is required.::

            dag.connect(query, report, [':data'])

        connects ``query.date`` to ``report.data``.

        The ``onlychanged``, ``queued``, and ``precedence`` values are passed through
        to ``src.param.watch()``.

        Parameters
        ----------
        src: Gizmo
            A Gizmo with output parameters.
        dst: Gizmo
            A Gizmo with input parameters.
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
            connected = any(src is s or src is d or dst is s or dst is d for s,d in self._gizmo_pairs)
            if not connected:
                raise GizmoError('New gizmos must connect to existing gizmos')

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
            if dstp.allow_refs:
                raise GizmoError(f'Destination parameter {dst}.{inp} must be "allow_refs=True"')

            srcp = getattr(src.param, outp)
            if srcp.allow_refs:
                raise GizmoError(f'Source parameter {src}.{outp} must not be "allow_refs=True"')

            dst._gizmo_name_map[src.name, outp] = inp
            src_out_params.append(outp)

        # print(f'{dst} watch {src} {src_out_params}')
        watcher = src.param.watch(dst._gizmo_event, src_out_params, onlychanged=onlychanged, queued=queued, precedence=precedence)

        self._gizmo_pairs.append((src, dst))

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

    def gizmo_by_name(self, name):
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

        TODO other connect() parameters.

        Returns
        -------
        dict
            A dictionary containing the serialised dag.
        """

        gizmo_instances = {}

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
                'dst': gizmo_instances[d]
            }
            params_map = {k:v for k,v in d._gizmo_name_map.items() if k[0]==s.name}
            params = [f'{k[1]}:{v}' for k,v in params_map.items()]
            connection['args'] = {'param_names': params}

            connections.append(connection)

        return {
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

