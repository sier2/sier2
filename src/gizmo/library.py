import sys
from importlib.metadata import entry_points
import traceback
from typing import Any
import warnings

from gizmo import Gizmo, Dag, Connection, GizmoError

_gizmo_library = {}

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

        for shelf in library:
            try:
                gizmos_func = shelf.load()
                gizmos_dict = gizmos_func()

                # Check that they really are gizmos.
                #
                for key in list(gizmos_dict):
                    g = gizmos_dict[key]
                    if not issubclass(g, Gizmo):
                        del gizmos_dict[key]
                        warnings.warn(f'{key} is not a Gizmo: removed')

                    if key in _gizmo_library:
                        warnings.warn(f'Gizmo key {key} already in library: removing duplicate')
                        del gizmos_dict[key]

                _gizmo_library.update(gizmos_dict)

            except Exception as e:
                print(f'While loading {shelf}:', file=sys.stderr)
                traceback.print_stack()

        return _gizmo_library

    @staticmethod
    def add(gizmo_class: type[Gizmo], key: str|None=None):
        """Add a local gizmo class to the library.

        The library initially loads gizmo classes using Python's entry_points() mechanism.
        This method allows local Gizmos to be added to the libray.

        This is useful fo testing, for example.

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
        if key in _gizmo_library:
            return _gizmo_library[key]

        raise GizmoError(f'Name {key} is not in the library')

    @staticmethod
    def load(dump: dict[str, Any]) -> Dag:
        """Load a dag from a serialised structure produced by Gizmo.dump().
        """

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
        dag = Dag(doc=dump['dag']['doc'])
        for conn in dump['connections']:
            conns = [Connection(**kwargs) for kwargs in conn['conn_args']]
            dag.connect(instances[conn['src']], instances[conn['dst']], *conns)

        return dag

Library.collect()
