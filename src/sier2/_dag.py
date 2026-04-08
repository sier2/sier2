import os
import sys
import threading
import tomllib
from collections import defaultdict, deque
from dataclasses import dataclass, field  # , KW_ONLY, field
from importlib.metadata import entry_points
from typing import Any

import param

from ._block import Block, BlockError, BlockState, BlockValidateError

# By default, loops in a dag aren't allowed.
#
_DISALLOW_CYCLES = True


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
            self.block._block_state = (
                BlockState.WAITING if self.block._wait_for_input else BlockState.SUCCESSFUL
            )
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
                    self.dag_logger.exception(block_name=self.block.name, block_state=state)

                # msg = f'While in {self.block.name}.execute(): {exc_val}'
                # LOGGER.exception(msg)
                if not self.dag._is_pyodide:
                    self.dag._stopper.event.set()

                if not issubclass(exc_type, BlockError):
                    # Convert non-BlockErrors in the block to a BlockError.
                    #
                    raise BlockError(f'Block {self.block.name}: {exc_val!s}') from exc_val

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
    if (liblen := len(library)) == 0:
        # There is no logging plugin, so return a dummy.
        #
        return lambda f, *args, **kwargs: f
    elif liblen > 1:
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

    SIER2_DAG_DEFAULTS = 'SIER2_DAG_DEFAULTS'

    def __init__(
        self,
        connections: list[tuple[param.Parameter, param.Parameter]],
        *,
        site: str = 'Block',
        title: str,
        doc: str,
        author: dict[str, str] | None = None,
        show_doc: bool = True,
    ):
        """A new dag.

        Parameters
        ----------
        site: str
            Name of the site.
        title: str
            A title to show in the header.
        doc: str
            Dag documentation.
        author: dict[str, str] | None
            The dag author. If present, a dictionary with 'name' and 'email' keys.
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
                self.author = {'name': author['name'], 'email': author['email']}
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

        # A cache of sorted blocks.
        # This makes get_sorted() faster.
        #
        self._sort_cache = None

        # Call out to a function to notify that status has been updated.
        # Used by the Panel dag chart.
        #
        self._on_context_exit = None

        try:
            self._connections(connections)
        except TypeError as e:
            if str(e).startswith('cannot unpack non-iterable'):
                raise BlockError('Connections must be 2-tuples') from e

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

    def _connections(self, connections: list[tuple[param.Parameter, param.Parameter]]):
        """Build a dag from a list of connections between output and input parameters.

        Can only be called once.

        This is an alternative to using several calls to connect().

        .. code-block:: python

            dag.connections([
                (b1.param.out1, b2.param.in1),
                (b1.param.out2, b2.param.in2),
                (b2.param.out_result, b3.param.in_display)
            ])

        Connections may be added in any order, but after all of the params
        are processed, the dag must be connected.

        If the environment variable `SIER2_DAG_DEFAULTS` is defined, it is the
        path of a TOML file containing default values for block params.

        Defaults are loaded by looking through the TOML tables.
        Look for a block name that is the table name with '-' replaced by ' '.
        If a table name does not match a block name, display a warning.
        If a key does not match a block param, display a warning.
        This is typically being done at development time, so be verbose to catch typos.
        """

        if self._block_pairs:
            raise BlockError('A dag can only be built once.')

        # if not connections:
        #     raise BlockError('There must be at least one connection')

        # Group watchers for each (src, dst) block.
        # This optimises the number of watchers.
        #
        # If we just add a watcher per param in the loop, then
        # param.update() won't batch the events.
        #
        src_out_params_dict = defaultdict(list)

        # Ensure that the sort cache is cleared.
        #
        self._sort_cache = None

        for ix, (src_param, dst_param) in enumerate(connections):
            if not isinstance(src_param, param.Parameter):
                raise BlockError(f'Source parameter at index {ix} is not a param')

            if not isinstance(dst_param, param.Parameter):
                raise BlockError(f'Destination parameter at index {ix} is not a param')

            src = src_param.owner
            dst = dst_param.owner

            # Because this is probably the first place that the Block instance is used,
            # this is a convenient place to check that the block was
            # correctly initialised.
            #
            for b in src, dst:
                if isinstance(b, param.parameterized.ParameterizedMetaclass):
                    raise BlockError(f'Did you call super().__init__() in {b} at index {ix}?')

            if not isinstance(src, Block):
                raise BlockError(
                    f'Source parameter at index {ix} does not belong to a Block object'
                )

            if not isinstance(dst, Block):
                raise BlockError(
                    f'Destination parameter at index {ix} does not belong to a Block object'
                )

            # # Because this is probably the first place that the Block instance is used,
            # # this is a convenient place to check that the block was correctly initialised.
            # #
            # # Pick an arbitrary attribute that should be present.
            # #
            # for b in src, dst:
            #     if not hasattr(b, 'doc'):
            #         raise BlockError(f'Did you call super().__init__() in {b}?')

            if src.name == dst.name:
                raise BlockError(f'Cannot add two blocks with the same name at index {ix}')

            if _DISALLOW_CYCLES:  # noqa: SIM102
                if _has_cycle(self._block_pairs + [(src, dst)]):
                    raise BlockError(f'The connection at index {ix} would create a cycle')

            # Checking for the same name also checks for the same block.
            #
            for block in _for_each_once(self._block_pairs):
                if (block is not src and block.name == src.name) or (
                    block is not dst and block.name == dst.name
                ):
                    raise BlockError(
                        f'A block with name "{block.name}" at index {ix} duplicates an existing name'
                    )

            # Check that these blocks aren't being watched already.
            # Maybe they're in another dag?
            #
            if src.param.watchers:
                raise BlockError(f'Source block at index {ix} has watchers')

            if dst.param.watchers:
                raise BlockError(f'Destination block at index {ix} has watchers')

            # for s, d in self._block_pairs:
            #     if src is s and dst is d:
            #         raise BlockError('These blocks are already connected')

            # We allow connections to be added in any order, we don't check
            # that new connections must connect to an existing block (if any exist).
            # This means that that dag could end up being disconnected;
            # we'll check for that at the end.
            #

            # if self._block_pairs:
            #     connected = any(
            #         src is s or src is d or dst is s or dst is d for s, d in self._block_pairs
            #     )
            #     if not connected:
            #         raise BlockError('A new block must connect to existing block')

            if src_param.allow_refs:
                raise BlockError(
                    f'Source parameter {src}.{src_param.name} must not be "allow_refs=True"'
                )

            if dst._block_name_map.get((src.name, src_param.name)) == dst_param.name:
                raise BlockError(f'The params at index {ix} are already connected')

            dst._block_name_map[src.name, src_param.name] = dst_param.name
            src_out_params_dict[src, dst].append(src_param.name)

            if (src, dst) not in self._block_pairs:
                self._block_pairs.append((src, dst))

        if not _is_connected(self._block_pairs):
            raise BlockError('Dag is not connected')

        # Load the block default values *before* we start watching params.
        #
        _load_block_defaults(self)

        # After we've gathered all the per-src-dst connections,
        # watch the source params for each connection.
        #
        for (src, dst), src_out_params in src_out_params_dict.items():
            src.param.watch(
                lambda *events, dst=dst: self._param_event(dst, *events),
                src_out_params,
                onlychanged=False,
            )

    def add_to_bag(self, block: Block):
        """Add a block to the block bag."""

        is_in_dag = any(block is src or block is dst for src, dst in self._block_pairs)
        if is_in_dag:
            raise BlockError('This block is in the dag')

        if block in self._block_bag:
            raise BlockError('This block is in the bag')

        if block.param.watchers:
            raise BlockError('This block has watchers')

        self._block_bag.append(block)

    def remove_from_bag(self, block: Block):
        """Remove a lock from the block bag."""

        if block in self._block_bag:
            ix = self._block_bag.find(block)
            del self._block_bag[ix]

    def _param_event(self, dst: Block, *events):
        """The callback for a watch event."""

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

    def execute(self, *, dag_logger=None) -> Block | None:
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

    def _execute(self, *, dag_logger=None) -> Block | None:
        self.logging(None, sier2_dag_=self)

        can_execute = True
        while self._block_queue:
            # print(len(self._block_queue), self._block_queue)
            # The user has set the "stop executing" flag.
            # Continue to set params, but don't execute anything
            #
            if not self._is_pyodide:  # noqa: SIM102
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
                    logging_params = {'sier2_dag_': self, 'sier2_block_': f'{item.dst}'}

                    # If we need to wait for a user, just run prepare().
                    # If we are restarting, just run execute().
                    # Otherwise, run both.
                    #
                    if is_input_block and not is_restart:
                        self.logging(g.prepare, **logging_params)()
                        # g._has_prepared = True
                    elif is_restart:
                        self.logging(g.execute, **logging_params)()

                        # If we've restarted after input,
                        # set the state of the downstream blocks to READY.
                        #
                        _set_downstream_state(self, g, BlockState.READY)
                    else:
                        self.logging(g.prepare, **logging_params)()
                        # g._has_prepared = True
                        self.logging(g.execute, **logging_params)()

            if is_input_block and not is_restart:  # and item.values:
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

    # TODO add a "dissolve()" method that unwatches everything,
    # so blocks can be reused in another dag.

    # def disconnect(self, g: Block) -> None:
    #     """Disconnect block g from other blocks in the dag.

    #     All parameters (input and output) will be disconnected.

    #     A :class:`~sier2.BlockError` will be raised if the disconnection would cause
    #     a disconnected dag.

    #     Parameters
    #     ----------
    #     g: Block
    #         The block to be disconnected.
    #     """

    #     # Ensure that the sort cache is cleared.
    #     #
    #     self._sort_cache = None

    #     # Check first to see if the dag would become disconnected.
    #     #
    #     maybe_pairs = [
    #         (src, dst) for src, dst in self._block_pairs if src is not g and dst is not g
    #     ]
    #     if not _is_connected(maybe_pairs):
    #         raise BlockError('Disconnecting this block would result in a disconnected dag')

    #     if self._block_queue:
    #         raise BlockError('Cannot disconnect blocks after executing the dag.')

    #     for watchers in g.param.watchers.values():
    #         for watcher in watchers['value']:
    #             # print(f'disconnect watcher {g.name}.{watcher}')
    #             g.param.unwatch(watcher)

    #     for src, dst in self._block_pairs:
    #         if dst is g:
    #             for watchers in src.param.watchers.values():
    #                 for watcher in watchers['value']:
    #                     # print(f'disconnect watcher {src.name}.{watcher}')
    #                     src.param.unwatch(watcher)

    #     # Remove this block from the dag.
    #     #
    #     # self._block_pairs[:] = [(src, dst) for src, dst in self._block_pairs if src is not g and dst is not g]
    #     self._block_pairs[:] = maybe_pairs

    #     # Because this block is no longer watching anything, the name map can be cleared.
    #     #
    #     g._block_name_map.clear()

    def block_by_name(self, name) -> Block | None:
        """Get a specific block by name."""

        for s, d in self._block_pairs:
            if s.name == name:
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

        if self._sort_cache is None:
            self._sort_cache = _get_sorted(self._block_pairs)

        return self._sort_cache

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
            vars = g.__init__.__code__.co_varnames[1 : g.__init__.__code__.co_argcount]  # type: ignore[misc]
            for var in vars:
                if hasattr(g, var):
                    args[var] = getattr(g, var)

            block = {'block': g.block_key(), 'instance': i, 'args': args}
            blocks.append(block)

        connections = []
        for s, d in self._block_pairs:
            connection: dict[str, Any] = {
                'src': block_instances[s],
                'dst': block_instances[d],
                'conn_args': [],
            }

            # Get src params that have been connected to dst params.
            #
            nmap = {
                (gname, sname): dname
                for (gname, sname), dname in d._block_name_map.items()
                if gname == s.name
            }

            for (gname, sname), dname in nmap.items():
                args = {'src_param_name': sname, 'dst_param_name': dname}

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
                'title': self.title,
            },
            'blocks': blocks,
            'connections': connections,
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
            if pair == (n, m):
                return ix

        return None

    def has_incoming(pairs, m):
        return any(d is m for _, d in pairs)

    remaining = pairs[:]
    L = []

    srcs, dsts = zip(*remaining)

    # Sort the current heads by name so they have a consistent ordering.
    #
    S = deque(sorted({s for s in srcs if s not in dsts}, key=lambda block: block.name))

    while S:
        # A topological sort is non-unique; this is why.
        # Nodes can be removed from S in arbitrary order.
        # We use .popleft() to maintain a consistent ordering.
        #
        n = S.popleft()
        L.append(n)
        S_next = []
        for _, m in remaining[:]:
            if (e := edge(remaining, n, m)) is not None:
                del remaining[e]
                if not has_incoming(remaining, m):
                    S_next.append(m)

        # Also sort this next layer of blocks.
        #
        S_next.sort(key=lambda block: block.name)
        S.extend(S_next)

    return L, remaining


def _has_cycle(block_pairs: list[tuple[Block, Block]]):
    _, remaining = topological_sort(block_pairs)

    return len(remaining) > 0


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


def _is_connected(pairs: list[tuple[Block, Block]]):
    """Determine if the list of pairs forms a connected graph."""

    if not pairs:
        return True

    n_blocks = sum(1 for _ in _for_each_once(pairs))

    visited = set()
    start = pairs[0][0]

    stack = [start]
    visited.add(start)
    while stack:
        current = stack.pop()
        for src, dst in pairs:
            if src == current and dst not in visited:
                visited.add(dst)
                stack.append(dst)
            elif dst == current and src not in visited:
                visited.add(src)
                stack.append(src)

    return len(visited) == n_blocks


def _set_downstream_state(dag: Dag, block: Block, state: BlockState) -> set[Block]:
    """Starting at (but not including) the given block, set the state of the downstream blocks.

    For example, when the dag is paused at a given block, we want to
    set the state of the downstream blocks to READY.

    Parameters
    ----------
    dag: Dag
        The dag.
    block: Block
        The starting block.
    state: BlockState
        The state to set the downstream blocks to.

    Returns
    -------
    set[Block]
        The blocks that had their state changed.
    """

    # Build a mapping from source blocks to their destination blocks.
    #
    block_dict = {}
    for src, dst in dag._block_pairs:
        block_dict[src] = block_dict.get(src, [])
        block_dict[src].append(dst)

    # for k, v in block_dict.items():
    #     print('*', k.name, [i.name for i in v])

    downstream = set()
    next_block = [block]
    while next_block:
        block = next_block.pop()
        if block in block_dict:
            down = block_dict[block]
            downstream.update(down)
            next_block.extend(down)

    for block in downstream:
        block._block_state = state

    return downstream


def _load_block_defaults(dag: Dag):

    default_toml = os.environ.get(Dag.SIER2_DAG_DEFAULTS)
    if not default_toml:
        return

    try:
        with open(default_toml, 'rb') as f:
            default_values = tomllib.load(f)
    except FileNotFoundError:
        print(
            f'Environment variable {Dag.SIER2_DAG_DEFAULTS} filepath {default_toml} not found',
            file=sys.stderr,
        )
        return
    except tomllib.TOMLDecodeError as e:
        print(f'TOML file {default_toml}: {e}', file=sys.stderr)
        return

    # Go through the TOML tables.
    # Look for a block name that is the table name with '-' replaced by ' '.
    # If a table name does not match a block name, say so.
    # If a key does not match a block aparam, say so.
    # This is being done at development time, so be verbose to catch typos.
    #
    for block_name, block_values in default_values.items():
        block = dag.block_by_name(block_name.replace('-', ' '))
        if block:
            for k, v in block_values.items():
                if k in block.param:
                    if isinstance(block.param[k], param.Tuple):
                        v = tuple(v)

                    setattr(block, k, v)
                else:
                    print(f'No param "{k}" in block "{block_name}"', file=sys.stderr)
        else:
            print(f'No block called "{block_name}"', file=sys.stderr)

    # The other way around: look up blocks in the TOML.
    #
    # for block in _for_each_once(dag._block_pairs):
    #     values = default_values.get(block.name)
    #     if values:
    #         for k, v in values.items():
    #             if k in block.param:
    #                 if isinstance(block.param[k], param.DateRange):
    #                     v = tuple(v)

    #                 setattr(block, k, v)
