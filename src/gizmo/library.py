import sys
from importlib.metadata import entry_points
from typing import Type

from gizmo import Gizmo

def collect() -> dict[str, Type[Gizmo]]:
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

    gizmo_library = {}
    library = entry_points(group='gizmo.library')

    for shelf in library:
        gizmos_func = shelf.load()
        gizmos_dict = gizmos_func()

        # Check that they really are gizmos.
        #
        for name in list(gizmos_dict):
            g = gizmos_dict[name]
            if not issubclass(g, Gizmo):
                del gizmos_dict[name]
                print(f'{name} is not a Gizmo: removed')

        gizmo_library.update(gizmos_dict)

    return gizmo_library
