from collections.abc import Iterable
from dataclasses import dataclass
import importlib
from importlib.metadata import entry_points, EntryPoint
from typing import Any, cast
import warnings

from sier2 import Block, Dag, Connection, BlockError

# Store a mapping from a unique key to a Gizmo class.
# When plugins are initially scanned, the classes are not loaded.
#
_block_library: dict[str, type[Block]|None] = {}

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

        dag_name = found_dag.key
        ix = dag_name.rfind('.')

    m = importlib.import_module(dag_name[:ix])
    func = getattr(m, dag_name[ix+1:])
    # if not issubclass(cls, Gizmo):
    #     raise GizmoError(f'{key} is not a block')

    func()

def _find(func_name: str) -> Iterable[tuple[EntryPoint, Info]]:
    """Use ``importlib.metadata.entry_points`` to look up entry points named ``sier2.library``.

    For each entry point, call ``load()`` to get a module,
    then call ``getattr(module, func_name)()`` to get a list of
    ``GizmoInfo`` instances.
    """

    library = entry_points(group='sier2.library')

    for entry_point in library:
        try:
            blocks_lib = entry_point.load()
            blocks_func = getattr(blocks_lib, func_name, None)
            if blocks_func is not None:
                if not callable(blocks_func):
                    warnings.warn(f'In {entry_point.module}, {blocks_func} is not a function')
                else:
                    block_info_list: list[Info] = blocks_func()
                    if not isinstance(block_info_list, list) or any(not isinstance(s, Info) for s in block_info_list):
                        warnings.warn(f'In {entry_point.module}, {blocks_func} does not return a list of {Info.__name__} instances')
                    else:
                        for gi in block_info_list:
                            yield entry_point, gi
        except Exception as e:
            warnings.warn(f'While loading {entry_point}:')
            raise BlockError(str(e)) from e

class Library:
    @staticmethod
    def collect():
        """Collect block information.

        Use ``_find_blocks()`` to yield ``GizmoInfo`` instances.

        Note that we don't load the blocks here. We don't want to import
        any modules: this would cause every block module to be imported,
        which would cause a lot of imports to happen. Therefore, we just
        create the keys in the dictionary, and let ``get()`` import block
        modules as required.
        """

        for entry_point, gi in _find_blocks():
            if gi.key in _block_library:
                warnings.warn(f'Gizmo plugin {entry_point}: key {gi.key} already in library')
            else:
                _block_library[gi.key] = None

    @staticmethod
    def add(block_class: type[Block], key: str|None=None):
        """Add a local block class to the library.

        The library initially loads block classes using Python's entry_points() mechanism.
        This method allows local Gizmos to be added to the libray.

        This is useful for testing, for example.

        Parameters
        ----------
        block_class: type[Gizmo]
            The Gizmo's class.
        key: str
            The Gizmo's unique key string. By default, the block's block_key()
            class method will be used to obtain the key.
        """

        if not issubclass(block_class, Block):
            print(f'{key} is not a Gizmo')

        # if not key:
        #     key = block_class.block_key()
        key_ = key if key else block_class.block_key()

        if key_ in _block_library:
            raise BlockError(f'Gizmo {key_} is already in the library')

        _block_library[key_] = block_class

    @staticmethod
    def get(key: str) -> type[Block]:
        if not _block_library:
            Library.collect()

        if key not in _block_library:
            raise BlockError(f'Name {key} is not in the library')

        if _block_library[key] is None:
            ix = key.rfind('.')
            m = importlib.import_module(key[:ix])
            cls = getattr(m, key[ix+1:])
            if not issubclass(cls, Block):
                raise BlockError(f'{key} is not a block')

            _block_library[key] = cls

        return cast(type[Block], _block_library[key])

    @staticmethod
    def load_dag(dump: dict[str, Any]) -> Dag:
        """Load a dag from a serialised structure produced by Gizmo.dump()."""

        # Create new instances of the specified blocks.
        #
        instances = {}
        for g in dump['blocks']:
            class_name = g['block']
            instance = g['instance']
            if instance not in instances:
                gclass = Library.get(class_name)
                instances[instance] = gclass(**g['args'])
            else:
                raise BlockError(f'Instance {instance} ({class_name}) already exists')

        # Connect the blocks.
        #
        dag = Dag(doc=dump['dag']['doc'], site=dump['dag']['site'], title=dump['dag']['title'])
        for conn in dump['connections']:
            conns = [Connection(**kwargs) for kwargs in conn['conn_args']]
            dag.connect(instances[conn['src']], instances[conn['dst']], *conns)

        return dag

# Library.collect()
