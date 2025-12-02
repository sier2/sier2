from ._block import Block, BlockError, BlockValidateError, BlockState
from dataclasses import dataclass, field #, KW_ONLY, field
from collections import deque
from importlib.metadata import entry_points
import threading
import sys
from typing import Any

# By default, loops in a dag aren't allowed.
#
_DISALLOW_CYCLES = True

@dataclass
class Connection:
    """Define a connection between an output parameter and an input parameter.

    For example:

    .. code-block:: python

        dag.connect(b1, b2, Connection('out_x', 'in_x'), Connection('out_y', 'in_y'))
    """

    src_param_name: str
    dst_param_name: str

    def __post_init__(self):
        if not self.src_param_name.startswith('out_'):
            raise BlockError('Output params must start with "out_"')

        if not self.dst_param_name.startswith('in_'):
            raise BlockError('Input params must start with "in_"')

@dataclass
class Connections:
    """Using a dictionary, define connections between pairs of output parameters and input parameters.

    This is a convenience class to replace multiple :class:`~sier2.Connection`
    parameters in :func:`~sier2.Dag.connect`. For example:

    .. code-block:: python

        dag.connect(b1, b2, Connections({
            'out_x': 'in_x',
            'out_y': 'in_y'
        })

    is equivalent to:

    .. code-block:: python

        dag.connect(b1, b2, Connection('out_x', 'in_x'), Connection('out_y', 'in_y'))
    """

    connections: dict[str, str]

    def items(self):
        return self.connections.items()

    @staticmethod
    def conns(connections):
        """Handle a mixture of Connection and Connections parameters."""

        for c in connections:
            if isinstance(c, Connection):
                yield c.src_param_name, c.dst_param_name
            elif isinstance(c, Connections):
                for src, dst in c.items():
                    yield src, dst
            else:
                raise BlockError('Not a Connection or Connections')

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
    # Values will be non-empty when execute() is called.
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
            self.block._block_state = BlockState.WAITING if self.block._wait_for_input else BlockState.SUCCESSFUL
        elif exc_type is KeyboardInterrupt:
            self.block_state._block_state = BlockState.INTERRUPTED
            if not self.dag._is_pyodide:
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
                if not self.dag._is_pyodide:
                    self.dag._stopper.event.set()

                if not issubclass(exc_type, BlockError):
                    # Convert non-BlockErrors in the block to a BlockError.
                    #
                    raise BlockError(f'Block {self.block.name}: {str(exc_val)}') from exc_val

        if self.dag._on_context_exit:
            self.dag._on_context_exit()

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

def _find_logging():
    PLUGIN_GROUP = 'sier2.logging'
    library = entry_points(group=PLUGIN_GROUP)
    if (liblen:=len(library))==0:
        # There is no logging plugin, so return a dummy.
        #
        return lambda f, *args, **kwargs: f
    elif liblen>1:
        raise BlockError(f'More than one plugin for {PLUGIN_GROUP}')

    ep = next(iter(library))
    try:
        logging_func = ep.load()

        return logging_func
    except AttributeError as e:
        e.add_note(f'While attempting to load logging function {ep.value}')
        raise BlockError(e)

# A marker from Dag.execute_after_input() to tell Dag.execute()
# that this a restart.
#
_RESTART = ':restart:'

class Dag:
    """A directed acyclic graph of blocks."""

    def __init__(self, *, site: str='Block', title: str, doc: str, author: dict[str, str]=None, show_doc: bool=True):
        """A new dag.

        Parameters
        ----------
        site: str
            Name of the site.
        title: str
            A title to show in the header.
        doc: str
            Dag documentation.
        author: str
            The dag author.
        show_doc: bool
            Show the dag docstring if True.
        """

        # The dag: a list of edges between blocks.
        #
        self._block_pairs: list[tuple[Block, Block]] = []

        # A bag of blocks.
        # These are blocks that aren't connected to any other blocks.
        # When the dag executes, these are executed first.
        #
        self._block_bag: list[Block] = []

        self.site = site
        self.title = title
        self.doc = doc
        self.show_doc = show_doc

        if author is not None:
            if 'name' in author and 'email' in author:
                self.author = {'name': author['name', 'email': author: 'email']}
            else:
                raise ValueError('Author must contain name and email keys')
        else:
            self.author = None

        if not self._is_pyodide:
            self._stopper = _Stopper()

        # We watch output params to be notified when they are set.
        # Events are queued here.
        #
        self._block_queue: deque[_InputValues] = deque()

        # The context manager class to use to run blocks.
        #
        self._block_context = _BlockContext

        # Set up the logging hook.
        #
        self.logging = _find_logging()

        # Call out to a function to notify that status has been updated.
        # Used by the Panel dag chart.
        #
        self._on_context_exit = None

    @property
    def _is_pyodide(self) -> bool:
        return '_pyodide' in sys.modules

    # def _for_each_once(self):
    #     """Yield each connected block once."""

    #     seen = set()
    #     for s, d in self._block_pairs:
    #         for g in s, d:
    #             if g not in seen:
    #                 seen.add(g)
    #                 yield g

    def stop(self):
        """Stop further execution of Block instances in this dag."""
        if not self._is_pyodide:
            self._stopper.event.set()

    def unstop(self):
        """Enable further execution of Block instances in this dag."""
        if not self._is_pyodide:
            self._stopper.event.clear()

    def connect(self, src: Block, dst: Block, *connections: Connection|Connections):
        """Connect two Blocks within this dag.

        The source and destination :class:`~sier2.Block` instances are connected by providing
        one or more :class:`~sier2.Connections` or :class:`~sier2.Connection` parameters,
        defining connections between an output parameter (``out_``) in the source block,
        and an input parameter (``in_``) in the destination block. For example:

        .. code-block:: python

            dag.connect(srcb, dstb, Connections({
                'out_x': 'in_x',
                'out_y': 'in_y'
            })

        Various consistency checks are done to maintain the integrity of the dag.
        In particular, the blocks must not form a cycle in the dag:
        if block A is connected to block B, then block B cannot
        subsequently be connected directly or indirectly to block A.
        """

        # if any(not isinstance(c, Connection) for c in connections):
        #     raise BlockError('All arguments must be Connection instances')

        # Because this is probably the first place that the Block instance is used,
        # this is a convenient place to check that the block was correctly initialised.
        #
        # Pick an arbitrary attribute that should be present.
        #
        for b in src, dst:
            if not hasattr(b, 'doc'):
                raise BlockError(f'Did you call super().__init__() in {b}?')

        if _DISALLOW_CYCLES:
            if _has_cycle(self._block_pairs + [(src, dst)]):
                raise BlockError('This connection would create a cycle')

        if src.name==dst.name:
            raise BlockError('Cannot add two blocks with the same name')

        # for g in self._for_each_once():
        for g in _for_each_once(self._block_pairs):
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

        if len(connections)==0:
            raise BlockError('There must be at least one connection')

        # for conn in connections:
        for src_param_name, dst_param_name in Connections.conns(connections):
            # dst_param = getattr(dst.param, conn.dst_param_name)
            # if dst_param.allow_refs:
            #     raise BlockError(f'Destination parameter {dst}.{inp} must be "allow_refs=True"')

            src_param = getattr(src.param, src_param_name)
            if src_param.allow_refs:
                raise BlockError(f'Source parameter {src}.{src_param_name} must not be "allow_refs=True"')

            dst._block_name_map[src.name, src_param_name] = dst_param_name
            src_out_params.append(src_param_name)

        src.param.watch(lambda *events: self._param_event(dst, *events), src_out_params, onlychanged=False)
        # src._block_out_params.extend(src_out_params)

        self._block_pairs.append((src, dst))

    def add_block(self, block: Block):
        """Add a block to the block bag."""

        is_in_dag = any(block is src or block is dst for src, dst in self._block_pairs)
        if is_in_dag:
            raise BlockError('This block is in the dag')

        if block in self._block_bag:
            raise BlockError('This block is in the bag')

        self._block_bag.append(block)

    def remove_block(self, block: Block):
        """Remove a lock from the block bag."""

        if block in self._block_bag:
            ix = self._block_bag.find(block)
            del self._block_bag[ix]

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

    def execute_after_input(self, block: Block, *, dag_logger=None):
        """Restart dag execution at the specified block.

        When a block is run, its ``prepare()`` and ``execute()``
        methods are called. However, if the block's ``wait_for_input`` is True,
        ``prepare()`` is called, then dag execution stops.

        When dag execution restarts via this method, the block's ``execute()``
        method is called. Then dag execution continues with the next block.

        Parameters
        ----------
        block: Block
            The block to restart the dag at.
        dag_logger:
            A logger adapter that will accept log messages.
        """

        if not block._wait_for_input:
            raise BlockError(f'A dag can only restart a paused Block, not {block.name}')

        # Prime the block queue, using _RESTART
        # to indicate that this is a restart, and Block.execute()
        # must be called.
        #
        self._block_queue.appendleft(_InputValues(block, {_RESTART: True}))
        self._execute(dag_logger=dag_logger)

    def execute(self, *, dag_logger=None) -> Block|None:
        """Execute the dag.

        The dag is executed by iterating through a block queue
        and popping events from the head of the queue. For each popped block,
        update the destination block's input parameters and call
        that block's execute() method.

        If the current destination block's ``wait_for_input`` is True,
        the loop will call ``block.prepare()``, then stop; ``execute()``
        will return the destination block.
        The dag can then be restarted with ``dag.execute_after_input()``,
        using the paused block as the parameter.

        To execute the dag, the block queue is first cleared.
        Then blocks in the block bag are added to the queue in an arbitrary order,
        with ``wait_for_input`` blocks before other blocks. Finally, the dag's
        head blocks (blocks that have no incoming connections), are added to the
        queue in an arbitrary order, with ``wait_for_input`` blocks before other blocks.

        Calling ``dag.execute()`` will then execute the dag starting with
        the first block in the queue.

        Returns
        -------
        Block|None
            If execution stops at a block with ``wait_for_input`` True,
            returns that block.
            Otherwise, if the dag executes to completion, returns ``None``.
        """

        self._block_queue.clear()

        # Execute blocks in the bag first.
        # Non-waiting blocks go first, waiting blocks next.
        #
        if self._block_bag:
            blocks = sorted(self._block_bag, key=lambda block: block._wait_for_input)
            for block in blocks:
                self._block_queue.append(_InputValues(block, {}))

        # Do the same for the heads of the dag.
        #
        heads, _ = self.heads_and_tails()
        blocks = sorted(heads, key=lambda block: block._wait_for_input)
        for block in blocks:
            self._block_queue.append(_InputValues(block, {}))

        if not self._block_queue:
            # Attempting to execute a dag with no updates is probably a mistake.
            #
            raise BlockError('Nothing to execute')

        return self._execute(dag_logger=dag_logger)

    def _execute(self, *, dag_logger=None) -> Block|None:
        self.logging(None, sier2_dag_=self)

        can_execute = True
        while self._block_queue:
            # print(len(self._block_queue), self._block_queue)
            # The user has set the "stop executing" flag.
            # Continue to set params, but don't execute anything
            #
            if not self._is_pyodide:
                if self._stopper.is_stopped:
                    can_execute = False

            item = self._block_queue.popleft()
            is_restart = item.values.pop(_RESTART, False)
            try:
                item.dst.param.update(item.values)
            except ValueError as e:
                msg = f'While in {item.dst.name} setting a parameter: {e}'
                if not self._is_pyodide:
                    self._stopper.event.set()
                raise BlockError(msg) from e

            # Execute the block.
            # Don't execute input blocks when we get to them,
            # unless this is after the user has selected the "Continue"
            # button.
            #
            is_input_block = item.dst._wait_for_input
            if can_execute:
                with self._block_context(block=item.dst, dag=self, dag_logger=dag_logger) as g:

                    logging_params = {
                        'sier2_dag_': self,
                        'sier2_block_': f'{item.dst}'
                    }

                    # If we need to wait for a user, just run prepare().
                    # If we are restarting, just run execute().
                    # Otherwise, run both.
                    if is_input_block and not is_restart:
                        self.logging(g.prepare, **logging_params)()
                        g._has_prepared = True
                    elif is_restart:
                        self.logging(g.execute, **logging_params)()
                    else:
                        self.logging(g.prepare, **logging_params)()
                        g._has_prepared = True
                        self.logging(g.execute, **logging_params)()

            if is_input_block and not is_restart:# and item.values:
                # If the current destination block requires user input,
                # stop executing the dag immediately, because we don't
                # want to be setting the input params of further blocks
                # and causing them to do things.
                #
                # This possibly leaves items on the queue, which will be
                # executed on the next call to execute().
                #
                return item.dst

        return None

    def disconnect(self, g: Block) -> None:
        """Disconnect block g from other blocks in the dag.

        All parameters (input and output) will be disconnected.

        A :class:`~sier2.BlockError` will be raised if the disconnection would cause
        a disconnected dag.

        Parameters
        ----------
        g: Block
            The block to be disconnected.
        """

        # Check first to see if the dag would become disconnected.
        #
        maybe_pairs = [(src, dst) for src, dst in self._block_pairs if src is not g and dst is not g]
        if not _is_connected(maybe_pairs):
            raise BlockError('Disconnecting this block would result in a disconnected dag')

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
        #
        # self._block_pairs[:] = [(src, dst) for src, dst in self._block_pairs if src is not g and dst is not g]
        self._block_pairs[:] = maybe_pairs

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

    def get_sorted(self) -> list[Block]:
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

    def heads_and_tails(self):
        """A tuple of the heads (blocks with no source) and tails (blocks with no destination) of the dag."""

        srcs = set()
        dsts = set()
        for src, dst in self._block_pairs:
            srcs.add(src)
            dsts.add(dst)

        return srcs.difference(dsts), dsts.difference(srcs)

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

def topological_sort(pairs):
    """Implement a topological sort as described at
    `Topological sorting <https://en.wikipedia.org/wiki/Topological_sorting>`_.

    code-block:: python

        L ← Empty list that will contain the sorted elements
        S ← Collection of all nodes with no incoming edge

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

    # TODO use a cache - the chart does los of sorting.
    #
    if not pairs:
        return [], []

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

    # Sort the current heads by name so they have a consistent ordering.
    #
    S = deque(sorted(set([s for s in srcs if s not in dsts]), key=lambda block:block.name))

    while S:
        # A topological sort is non-unique; this is why.
        # Nodes can be removed from S in arbitrary order.
        # We use .popleft() to maintain a consistent ordering.
        #
        n = S.popleft()
        L.append(n)
        S_next = []
        for _, m in remaining[:]:
            if (e:=edge(remaining, n, m))is not None:
                del remaining[e]
                if not has_incoming(remaining, m):
                    S_next.append(m)

        # Also sort this next layer of blocks.
        #
        S_next.sort(key=lambda block:block.name)
        S.extend(S_next)

    return L, remaining

def _has_cycle(block_pairs: list[tuple[Block, Block]]):
    _, remaining = topological_sort(block_pairs)

    return len(remaining)>0

def _get_sorted(block_pairs: list[tuple[Block, Block]]) -> list[Block]:
    ordered, remaining = topological_sort(block_pairs)

    if remaining:
        raise BlockError('Dag contains a cycle')

    return ordered

def _for_each_once(pairs):
    """Yield each connected block once."""

    seen = set()
    for s, d in pairs:
        for g in s, d:
            if g not in seen:
                seen.add(g)
                yield g

def _is_connected(pairs: list[Block]):
    """Determine if the list of pairs forms a connected graph."""

    if not pairs:
        return True

    n_blocks = sum( 1 for _ in _for_each_once(pairs))

    visited = set()
    start = pairs[0][0]

    stack = [start]
    visited.add(start)
    while stack:
        current = stack.pop()
        for src, dst in pairs:
            if src==current and dst not in visited:
                visited.add(dst)
                stack.append(dst)
            elif dst==current and src not in visited:
                visited.add(src)
                stack.append(src)

    return len(visited)==n_blocks
