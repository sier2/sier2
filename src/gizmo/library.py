import importlib
from importlib.metadata import entry_points
from typing import Any, Type
import warnings

from gizmo import Gizmo, Dag, Connection, GizmoError

# Store a mapping from a unique key to a Gizmo class.
# When plugins are initially scanned, the classes are not loaded.
#
_gizmo_library: dict[str, Type[Gizmo]|None] = {}

class Library:
    @staticmethod
    def collect() -> dict[str, type[Gizmo]]:
        """Collect gizmo implementations.

        This function uses ``importlib.metadata.entry_points`` to look up
        entry points named ``gizmo.library``.

        For each entry point, it then calls ``load()`` to get a module,
        and calls ``module.gizmos()`` to get a dictionary mapping
        the names of gizmo classes (strings) to Gizmo classes.

        Returns
        -------
        dict[str, Type[Gizmo]]
            A dictionary of {names: Gizmo classes}.
        """

        library = entry_points(group='gizmo.library')

        for plugin in library:
            try:
                gizmos_func = plugin.load()
                if not callable(gizmos_func):
                    warnings.warn(f'In {plugin.module}, {gizmos_func} is not a function')
                else:
                    gizmos_list = gizmos_func()
                    if not isinstance(gizmos_list, list) or any(not isinstance(s, str) for s in gizmos_list):
                        warnings.warn(f'In {plugin.module}, {gizmos_func} does not return a list of strings')
                    else:
                        for g in gizmos_list:
                            if g in _gizmo_library:
                                warnings.warn(f'Gizmo key {g} already in library: removing duplicate')
                            else:
                                _gizmo_library[g] = None
            except Exception as e:
                warnings.warn(f'While loading {plugin}:')
                raise GizmoError(str(e)) from e
                # traceback.print_stack()

        return _gizmo_library

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

        if not key:
            key = gizmo_class.gizmo_key()

        if key in _gizmo_library:
            raise GizmoError(f'Gizmo {key} is already in the library')

        _gizmo_library[key] = gizmo_class

    @staticmethod
    def get(key: str) -> type[Gizmo]:
        if not _gizmo_library:
            Library.collect()

        if key not in _gizmo_library:
            raise GizmoError(f'Name {key} is not in the library')

        if _gizmo_library[key] is None:
            ix = key.rfind('.')
            m = importlib.import_module(key[:ix])
            _gizmo_library[key] = getattr(m, key[ix+1:])

        return _gizmo_library[key]

    @staticmethod
    def load(dump: dict[str, Any]) -> Dag:
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
