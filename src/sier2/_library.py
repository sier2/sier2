from collections.abc import Iterable
from dataclasses import dataclass
import importlib
from importlib.metadata import entry_points, EntryPoint
from typing import Any, cast
import warnings

from sier2 import Block, Dag, Connection, BlockError
from sier2.panel import PanelDag

# Store a mapping from a unique key to a Block class.
# When plugins are initially scanned, the classes are not loaded.
#
_block_library: dict[str, type[Block]|None] = {}
_dag_library: set[str] = set()

@dataclass
class Info:
    key: str
    doc: str

def docstring(func) -> str:
    doc = func.__doc__.strip()

    return doc.split('\n')[0].strip()

def _find_blocks():
    yield from _find('blocks')

def _find_dags():
    yield from _find('dags')

def run_dag(dag_name):
    """Run the named dag."""

    ix = dag_name.rfind('.')
    if ix==-1:
        found_dag = None
        for _, d in _find_dags():
            dparts = d.key.split('.')
            if dparts[-1]==dag_name:
                if found_dag:
                    raise BlockError(f'Found duplicate: {dag_name}, d')

                found_dag = d

        if found_dag is None:
            raise BlockError('No such dag')

        dag_name = found_dag.key
        ix = dag_name.rfind('.')

    m = importlib.import_module(dag_name[:ix])
    func = getattr(m, dag_name[ix+1:])
    # if not issubclass(cls, Block):
    #     raise BlockError(f'{key} is not a block')

    dag = func()
    if not hasattr(dag, 'show'):
        raise BlockError(f'Dag {dag_name} does not have a user interface')

    dag.show()

def _find(func_name: str) -> Iterable[tuple[EntryPoint, Info]]:
    """Use ``importlib.metadata.entry_points`` to look up entry points named ``sier2.library``.

    For each entry point, call ``load()`` to get a module,
    then call ``getattr(module, func_name)()`` to get a list of
    ``BlockInfo`` instances.

    Parameters
    ----------
    func_name: str
        The name of the function that will be called to get a list[Info].
        Either ``'blocks'`` or ``'dags'``.
    """

    library = entry_points(group='sier2.library')

    for entry_point in library:
        try:
            lib = entry_point.load()
            func = getattr(lib, func_name, None)
            if func is not None:
                if not callable(func):
                    warnings.warn(f'In {entry_point.module}, {func} is not a function')
                else:
                    info_list: list[Info] = func()
                    if not isinstance(info_list, list) or any(not isinstance(s, Info) for s in info_list):
                        warnings.warn(f'In {entry_point.module}, {func} does not return a list of {Info.__name__} instances')
                    else:
                        for gi in info_list:
                            yield entry_point, gi
        except Exception as e:
            raise BlockError(f'While loading {entry_point}: {e}') from e

class Library:
    @staticmethod
    def collect_blocks():
        """Collect block information.

        Use ``_find_blocks()`` to yield ``BlockInfo`` instances.

        Note that we don't load the blocks here. We don't want to import
        any modules: this would cause every block module to be imported,
        which would cause a lot of imports to happen. Therefore, we just
        create the keys in the dictionary, and let ``get_block()`` import
        block modules as required.
        """

        for entry_point, gi in _find_blocks():
            if gi.key in _block_library:
                warnings.warn(f'Block plugin {entry_point}: key {gi.key} already in library')
            else:
                _block_library[gi.key] = None

    @staticmethod
    def collect_dags():
        for entry_point, gi in _find_dags():
            if gi.key in _dag_library:
                warnings.warn(f'Dag plugin {entry_point}: key {gi.key} already in library')
            else:
                _dag_library.add(gi.key)

    @staticmethod
    def add_block(block_class: type[Block], key: str|None=None):
        """Add a local block class to the library.

        The library initially loads block classes using Python's entry_points() mechanism.
        This method allows local Blocks to be added to the library.

        This is useful for testing, for example.

        Parameters
        ----------
        block_class: type[Block]
            The Block's class.
        key: str
            The Block's unique key string. By default, the block's block_key()
            class method will be used to obtain the key.
        """

        if not issubclass(block_class, Block):
            print(f'{key} is not a Block')

        # if not key:
        #     key = block_class.block_key()
        key_ = key if key else block_class.block_key()

        if key_ in _block_library:
            raise BlockError(f'Block {key_} is already in the library')

        _block_library[key_] = block_class

    @staticmethod
    def get_block(key: str) -> type[Block]:
        if not _block_library:
            Library.collect_blocks()

        if key not in _block_library:
            raise BlockError(f'Block name {key} is not in the library')

        if _block_library[key] is None:
            ix = key.rfind('.')
            m = importlib.import_module(key[:ix])
            cls = getattr(m, key[ix+1:])
            if not issubclass(cls, Block):
                raise BlockError(f'{key} is not a block')

            # The fully qualified name of the class is probably not the same as
            # the library key string. This matters when the dag is dumped and loaded.
            # Therefore we tell the class what its key is so the key can be dumped,
            # and when the dag is loaded, the block can be found using
            # Library.get_block().
            #
            setattr(cls, Block.SIER2_KEY, key)

            _block_library[key] = cls

        return cast(type[Block], _block_library[key])

    @staticmethod
    def get_dag(key: str) -> type[Dag]:
        if not _dag_library:
            Library.collect_dags()

        if key not in _dag_library:
            raise BlockError(f'Dag name {key} is not in the library')

        if key in _dag_library:
            ix = key.rfind('.')
            m = importlib.import_module(key[:ix])
            func = getattr(m, key[ix+1:])
            dag = func()
            if not isinstance(dag, Dag):
                raise BlockError(f'{key} is not a dag')

        return cast(type[Dag], dag)

    @staticmethod
    def load_dag(dump: dict[str, Any]) -> Dag:
        """Load a dag from a serialised structure produced by Block.dump()."""

        # Create new instances of the specified blocks.
        #
        instances = {}
        for g in dump['blocks']:
            block_key = g['block']
            instance = g['instance']
            if instance not in instances:
                gclass = Library.get_block(block_key)
                instances[instance] = gclass(**g['args'])
            else:
                raise BlockError(f'Instance {instance} ({block_key}) already exists')

        # Connect the blocks.
        #
        DagType = PanelDag if dump['dag']['type']=='PanelDag' else Dag
        dag = DagType(doc=dump['dag']['doc'], site=dump['dag']['site'], title=dump['dag']['title'])
        for conn in dump['connections']:
            conns = [Connection(**kwargs) for kwargs in conn['conn_args']]
            dag.connect(instances[conn['src']], instances[conn['dst']], *conns)

        return dag

# Library.collect()
