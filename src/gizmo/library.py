from collections.abc import Iterable
from dataclasses import dataclass
import importlib
from importlib.metadata import entry_points, EntryPoint
from typing import Any, cast
import warnings

from gizmo import Gizmo, Dag, Connection, GizmoError

# Store a mapping from a unique key to a Gizmo class.
# When plugins are initially scanned, the classes are not loaded.
#
_gizmo_library: dict[str, type[Gizmo]|None] = {}

@dataclass
class Info:
    key: str
    doc: str

def docstring(func) -> str:
    doc = func.__doc__.strip()

    return doc.split('\n')[0].strip()

def _find_gizmos():
    yield from _find('gizmos')

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
                    raise GizmoError(f'Found duplicate: {dag_name}, d')

                found_dag = d

        dag_name = found_dag.key
        ix = dag_name.rfind('.')

    m = importlib.import_module(dag_name[:ix])
    func = getattr(m, dag_name[ix+1:])
    # if not issubclass(cls, Gizmo):
    #     raise GizmoError(f'{key} is not a gizmo')

    func()

def _find(func_name: str) -> Iterable[tuple[EntryPoint, Info]]:
    """Use ``importlib.metadata.entry_points`` to look up entry points named ``gizmo.library``.

    For each entry point, call ``load()`` to get a module,
    then call ``getattr(module, func_name)()`` to get a list of
    ``GizmoInfo`` instances.
    """

    library = entry_points(group='gizmo.library')

    for entry_point in library:
        try:
            gizmos_lib = entry_point.load()
            gizmos_func = getattr(gizmos_lib, func_name, None)
            if gizmos_func is not None:
                if not callable(gizmos_func):
                    warnings.warn(f'In {entry_point.module}, {gizmos_func} is not a function')
                else:
                    gizmo_info_list: list[Info] = gizmos_func()
                    if not isinstance(gizmo_info_list, list) or any(not isinstance(s, Info) for s in gizmo_info_list):
                        warnings.warn(f'In {entry_point.module}, {gizmos_func} does not return a list of {Info.__name__} instances')
                    else:
                        for gi in gizmo_info_list:
                            yield entry_point, gi
        except Exception as e:
            warnings.warn(f'While loading {entry_point}:')
            raise GizmoError(str(e)) from e

class Library:
    @staticmethod
    def collect():
        """Collect gizmo information.

        Use ``_find_gizmos()`` to yield ``GizmoInfo`` instances.

        Note that we don't load the gizmos here. We don't want to import
        any modules: this would cause every gizmo module to be imported,
        which would cause a lot of imports to happen. Therefore, we just
        create the keys in the dictionary, and let ``get()`` import gizmo
        modules as required.
        """

        for entry_point, gi in _find_gizmos():
            if gi.key in _gizmo_library:
                warnings.warn(f'Gizmo plugin {entry_point}: key {gi.key} already in library')
            else:
                _gizmo_library[gi.key] = None

    @staticmethod
    def add(gizmo_class: type[Gizmo], key: str|None=None):
        """Add a local gizmo class to the library.

        The library initially loads gizmo classes using Python's entry_points() mechanism.
        This method allows local Gizmos to be added to the libray.

        This is useful for testing, for example.

        Parameters
        ----------
        gizmo_class: type[Gizmo]
            The Gizmo's class.
        key: str
            The Gizmo's unique key string. By default, the gizmo's gizmo_key()
            class method will be used to obtain the key.
        """

        if not issubclass(gizmo_class, Gizmo):
            print(f'{key} is not a Gizmo')

        # if not key:
        #     key = gizmo_class.gizmo_key()
        key_ = key if key else gizmo_class.gizmo_key()

        if key_ in _gizmo_library:
            raise GizmoError(f'Gizmo {key_} is already in the library')

        _gizmo_library[key_] = gizmo_class

    @staticmethod
    def get(key: str) -> type[Gizmo]:
        if not _gizmo_library:
            Library.collect()

        if key not in _gizmo_library:
            raise GizmoError(f'Name {key} is not in the library')

        if _gizmo_library[key] is None:
            ix = key.rfind('.')
            m = importlib.import_module(key[:ix])
            cls = getattr(m, key[ix+1:])
            if not issubclass(cls, Gizmo):
                raise GizmoError(f'{key} is not a gizmo')

            _gizmo_library[key] = cls

        return cast(type[Gizmo], _gizmo_library[key])

    @staticmethod
    def load_dag(dump: dict[str, Any]) -> Dag:
        """Load a dag from a serialised structure produced by Gizmo.dump()."""

        # Create new instances of the specified gizmos.
        #
        instances = {}
        for g in dump['gizmos']:
            class_name = g['gizmo']
            instance = g['instance']
            if instance not in instances:
                gclass = Library.get(class_name)
                instances[instance] = gclass(**g['args'])
            else:
                raise GizmoError(f'Instance {instance} ({class_name}) already exists')

        # Connect the gizmos.
        #
        dag = Dag(doc=dump['dag']['doc'], site=dump['dag']['site'], title=dump['dag']['title'])
        for conn in dump['connections']:
            conns = [Connection(**kwargs) for kwargs in conn['conn_args']]
            dag.connect(instances[conn['src']], instances[conn['dst']], *conns)

        return dag

# Library.collect()
