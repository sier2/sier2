from ._block import Block, InputBlock, BlockError, BlockValidateError, BlockState
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

    def __post_init__(self):
        if not self.src_param_name.startswith('out_'):
            raise BlockError('Output params must start with "out_"')

        if not self.dst_param_name.startswith('in_'):
            raise BlockError('Input params must start with "in_"')

@dataclass
class _InputValues:
    """Record a param value change.

    When a block updates an output param, the update is queued until
    the block finishes executing. Instances of this class are
    what is queued.
    """

    # The block to be updated.
    #
    dst: Block

    # The values to be set before the block executes.
    # For a normal block, values will be non-empty when execute() is called.
    # For an input block, if values is non-empty, prepare()
    # will be called, else execute() will be called
    #
    values: dict[str, Any] = field(default_factory=dict)

class _BlockContext:
    """A context manager to wrap the execution of a block within a dag.

    This default context manager handles the block state, the stopper,
    and converts block execution errors to GimzoError exceptions.

    This could be done inline, but using a context manager allows
    the context manager to be replaced. For example, a panel-based
    dag runner could use a context manager that incorporates logging
    and displays information in a GUI.
    """

    def __init__(self, *, block: Block, dag: 'Dag', dag_logger=None):
        self.block = block
        self.dag = dag
        self.dag_logger = dag_logger

    def __enter__(self):
        self.block._block_state = BlockState.EXECUTING

        return self.block

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.block._block_state = BlockState.WAITING if isinstance(self.block, InputBlock) else BlockState.SUCCESSFUL
        elif exc_type is KeyboardInterrupt:
            self.block_state._block_state = BlockState.INTERRUPTED
            self.dag._stopper.event.set()
            print(f'KEYBOARD INTERRUPT IN BLOCK {self.name}')
        else:
            state = BlockState.ERROR
            self.block._block_state = state
            if exc_type is not BlockValidateError:
                # Validation errors don't set the stopper;
                # they just stop execution.
                #
                if self.dag_logger:
                    self.dag_logger.exception(
                        block_name=self.block.name,
                        block_state=state
                    )

                # msg = f'While in {self.block.name}.execute(): {exc_val}'
                # LOGGER.exception(msg)
                self.dag._stopper.event.set()

                if not issubclass(exc_type, BlockError):
                    # Convert non-BlockErrors in the block to a BlockError.
                    #
                    raise BlockError(f'Block {self.block.name}: {str(exc_val)}') from exc_val

        # Don't suppress the original exception.
        #
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
    """A directed acyclic graph of blocks."""

    def __init__(self, *, site: str='Block', title: str, doc: str):
        self._block_pairs: list[tuple[Block, Block]] = []
        self._stopper = _Stopper()
        self.site = site
        self.title = title
        self.doc = doc

        # We watch output params to be notified when they are set.
        # Events are queued here.
        #
        self._block_queue: deque[_InputValues] = deque()

        # The context manager class to use to run blocks.
        #
        self._block_context = _BlockContext

    def _for_each_once(self):
        """Yield each connected block once."""

        seen = set()
        for s, d in self._block_pairs:
            for g in s, d:
                if g not in seen:
                    seen.add(g)
                    yield g

    def stop(self):
        """Stop further execution of Block instances in this dag."""

        self._stopper.event.set()

    def unstop(self):
        """Enable further execution of Block instances in this dag."""

        self._stopper.event.clear()

    def connect(self, src: Block, dst: Block, *connections: Connection):
        if any(not isinstance(c, Connection) for c in connections):
            raise BlockError('All arguments must be Connection instances')

        if _DISALLOW_CYCLES:
            if _has_cycle(self._block_pairs + [(src, dst)]):
                raise BlockError('This connection would create a cycle')

        if src.name==dst.name:
            raise BlockError('Cannot add two blocks with the same name')

        for g in self._for_each_once():
            if (g is not src and g.name==src.name) or (g is not dst and g.name==dst.name):
                raise BlockError('A block with this name already exists')

        for s, d in self._block_pairs:
            if src is s and dst is d:
                raise BlockError('These blocks are already connected')

        if self._block_pairs:
            connected = any(src is s or src is d or dst is s or dst is d for s, d in self._block_pairs)
            if not connected:
                raise BlockError('A new block must connect to existing block')

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
            #     raise BlockError(f'Destination parameter {dst}.{inp} must be "allow_refs=True"')

            src_param = getattr(src.param, conn.src_param_name)
            if src_param.allow_refs:
                raise BlockError(f'Source parameter {src}.{conn.src_param_name} must not be "allow_refs=True"')

            dst._block_name_map[src.name, conn.src_param_name] = conn.dst_param_name
            src_out_params.append(conn.src_param_name)

        src.param.watch(lambda *events: self._param_event(dst, *events), src_out_params, onlychanged=False)
        src._block_out_params.extend(src_out_params)

        self._block_pairs.append((src, dst))

    def _param_event(self, dst: Block, *events):
        """The callback for a watch event."""

        # print(f'DAG EVENTS: {events} -> {dst.name}')
        for event in events:
            cls = event.cls.name
            name = event.name
            new = event.new

            # The input param in the dst block.
            #
            inp = dst._block_name_map[cls, name]

            # Look for the destination block in the event queue.
            # If found, update the param value dictionary,
            # else append a new item.
            # This ensures that all param updates for a destination
            # block are merged into a single queue item, even if the
            # updates come from different source blocks.
            #
            for item in self._block_queue:
                if dst is item.dst:
                    item.values[inp] = new
                    break
            else:
                item = _InputValues(dst)
                item.values[inp] = new
                self._block_queue.append(item)

    def execute_after_input(self, block: InputBlock, *, dag_logger=None):
        """Execute the dag after running ``prepare()`` in an input block.

        After prepare() executes, and the user has possibly
        provided input, the dag must continue with execute() in the
        same block.

        This method will prime the block queue with the specified block's
        output, and call execute().

        Parameters
        ----------
        block: InputBlock
            The block to restart the dag at.
        dag_logger:
            A logger adapter that will accept log messages.
        """

        if not isinstance(block, InputBlock):
            raise BlockError(f'A dag can only restart an InputBlock, not {block.name}')

        # Prime the block queue, using an empty input param values dict
        # to indicate that this is a restart, and Block.execute()
        # must be called.
        #
        self._block_queue.appendleft(_InputValues(block, {}))
        self.execute(dag_logger=dag_logger)

    def execute(self, *, dag_logger=None):
        """Execute the dag.

        The dag is executed by iterating through the block event queue
        and popping events from the head of the queue. For each event,
        update the destination block's input parameters and call
        that block's execute() method.

        If the current destination block is an ``InputBlock``,
        the loop will call ``block.prepare()` instead of ``block.execute()``,
        then stop. The dag can then be restarted with
        ``dag.execute_after_input()``.

        To start the dag, there must be something in the event queue -
        the dag must be "primed". A block must have updated at least one
        output param before the dag's execute() is called. Calling
        ``dag.execute()`` will then execute the dag starting with
        the blocks connected to the first block.
        """

        if not self._block_queue:
            # Attempting to execute a dag with no updates is probably a mistake.
            #
            raise BlockError('Nothing to execute')

        can_execute = True
        while self._block_queue:
            # print(len(self._block_queue), self._block_queue)
            # The user has set the "stop executing" flag.
            # Continue to set params, but don't execute anything
            #
            if self._stopper.is_stopped:
                can_execute = False

            item = self._block_queue.popleft()
            try:
                item.dst.param.update(item.values)
            except ValueError as e:
                msg = f'While in {item.dst.name} setting a parameter: {e}'
                self._stopper.event.set()
                raise BlockError(msg) from e

            # Execute the block.
            # Don't execute input blocks when we get to them,
            # unless this is after the user has selected the "Continue"
            # button.
            #
            is_input_block = isinstance(item.dst, InputBlock)
            if can_execute:
                with self._block_context(block=item.dst, dag=self, dag_logger=dag_logger) as g:
                    # If this is an input block, and there are input
                    # values, call prepare() if it exists.
                    #
                    if is_input_block and item.values:
                        g.prepare()
                    else:
                        g.execute()

            if is_input_block and item.values:
                # If the current destination block requires user input,
                # stop executing the dag immediately, because we don't
                # want to be setting the input params of further blocks
                # and causing them to do things.
                #
                # This possibly leaves items on the queue, which will be
                # executed on the next call to execute().
                #
                break

    def disconnect(self, g: Block) -> None:
        """Disconnect block g from other blocks.

        All parameters (input and output) will be disconnected.

        Parameters
        ----------
        g: Block
            The block to be disconnected.
        """

        for p, watchers in g.param.watchers.items():
            for watcher in watchers['value']:
                # print(f'disconnect watcher {g.name}.{watcher}')
                g.param.unwatch(watcher)

        for src, dst in self._block_pairs:
            if dst is g:
                for p, watchers in src.param.watchers.items():
                    for watcher in watchers['value']:
                        # print(f'disconnect watcher {src.name}.{watcher}')
                        src.param.unwatch(watcher)

        # Remove this block from the dag.
        # Check for sources and destinations.
        #
        self._block_pairs[:] = [(src, dst) for src, dst in self._block_pairs if src is not g and dst is not g]

        # Because this block is no longer watching anything, the name map can be cleared.
        #
        g._block_name_map.clear()

    def block_by_name(self, name) -> Block | None:
        """Get a specific block by name."""

        for s, d in self._block_pairs:
            if s.name==name:
                return s

            if d.name == name:
                return d

        return None

    def get_sorted(self):
        """Return the blocks in this dag in topological order.

        This is useful for arranging the blocks in a GUI, for example.

        The returned dictionary is in no particular order:
        the rank values determine the order of the blocks.

        Returns
        -------
        dict[Block, int]
            A mapping of block to rank
        """

        return _get_sorted(self._block_pairs)

    def has_cycle(self):
        return _has_cycle(self._block_pairs)

    def dump(self):
        """Dump the dag to a serialisable (eg to JSON) dictionary.

        The blocks and connections are reduced to simple representations.
        There is no need to serialize code: the blocks themselves are assumed
        to be available when loaded - it is just the attributes of the blocks
        that need to be saved.

        Two sets of attributes in particular are saved.

        * The name of the block class. Each block has a name by virtue of it
            being a Parameterized subclass.
        * The ``__init__`` parameters, where possible. For each parameter,
            if the block object has a matching instance name, the value of
            the name is saved.

        Returns
        -------
        dict
            A dictionary containing the serialised dag.
        """

        block_instances: dict[Block, int] = {}

        instance = 0
        for s, d in self._block_pairs:
            if s not in block_instances:
                block_instances[s] = instance
                instance += 1
            if d not in block_instances:
                block_instances[d] = instance
                instance += 1

        blocks = []
        for g, i in block_instances.items():
            # We have to pass some arguments to the block when it is reconstituted.
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

            block = {
                'block': g.block_key(),
                'instance': i,
                'args': args
            }
            blocks.append(block)

        connections = []
        for s, d in self._block_pairs:
            connection: dict[str, Any] = {
                'src': block_instances[s],
                'dst': block_instances[d],
                'conn_args': []
            }

            # Get src params that have been connected to dst params.
            #
            nmap = {(gname, sname): dname for (gname, sname), dname in d._block_name_map.items() if gname==s.name}

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
                'type': self.__class__.__name__,
                'doc': self.doc,
                'site': self.site,
                'title': self.title
            },
            'blocks': blocks,
            'connections': connections
        }

    def hv_graph(self):
        """Build a HoloViews Graph to visualise the block connections."""

        src: list[Block] = []
        dst: list[Block] = []

        def build_layers():
            """Traverse the block pairs and organise them into layers.

            The first layer contains the root (no input) nodes.
            """

            ranks = {}
            remaining = self._block_pairs[:]

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

def _has_cycle(block_pairs: list[tuple[Block, Block]]):
    _, remaining = topological_sort(block_pairs)

    return len(remaining)>0

def _get_sorted(block_pairs: list[tuple[Block, Block]]):
    ordered, remaining = topological_sort(block_pairs)

    if remaining:
        raise BlockError('Dag contains a cycle')

    return ordered
