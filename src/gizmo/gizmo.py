import param
from typing import Callable

# By default, loops in a flow DAG aren't allowed.
#
_DISALLOW_LOOPS = True

class GizmoError(Exception):
    pass

class Gizmo(param.Parameterized):
    pass

_gizmo_graph: list[tuple[Gizmo, Gizmo]] = []

def _has_loop(src: Gizmo, dst: Gizmo) -> bool:
    """Find loops in the gizmo graph.

    Use _gizmo_graph to build a dictionary of relative ranks
    based on src -> dst connections. If the new src has a
    greater rank than the new dst, then a loop would be created.

    It's probably a bit inefficient to redo the ranks for every
    new connection, but we don't have to maintain another global,
    and I doubt if any flow will be big enough for anyone to notice.

    Returns
    -------
    bool
        True if connecting src to dst would create a loop.
    """

    if src is dst:
        # A self-loop.
        #
        raise GizmoError('Gizmos cannot be connected to themselves')

    if not _gizmo_graph:
        # Can't create a loop if there is only one connection.
        #
        return False

    # A unique key for a gizmo.
    #
    uniq: Callable[[Gizmo], int] = lambda g: id(g)

    rank = 0
    ranks: dict[int, int] = {}
    for s, d in _gizmo_graph + [(src, dst)]:
        sid = uniq(s)
        did = uniq(d)
        if sid in ranks and did in ranks:
            # Both gizmos are already in the graph.
            # Not a problem (a bit strange, though).
            #
            pass
        elif sid not in ranks and did not in ranks:
            # Neither gizmo is in the graph,
            # so they don't connect to anything else.
            # Not a problem.
            #
            ranks[sid] = rank
            ranks[did] = rank + 1
            rank += 2
        elif sid not in ranks:
            ranks[sid] = ranks[did] - 1
        elif did not in ranks:
            ranks[did] = ranks[sid] + 1

    srank = ranks[uniq(src)]
    drank = ranks[uniq(dst)]

    if srank < drank:
        return False

    return True

class GizmoManager:
    @staticmethod
    def clear() -> None:
        """Clear the flow graph."""

        _gizmo_graph.clear()

    @staticmethod
    def connect(src: Gizmo, dst: Gizmo, param_names: list[str]) -> None:
        """Connect a source gizmo to a destination gizmo.

        Input parameters in the destination gizmo watch output parameters
        in the source gizmo so that changes in the source are reflected in
        the destination.

        Parameters
        ----------
        src: Gizmo
            A Gizmo with output parameters.
        dst:
            A Gizmo with input parameters.
        """

        if _DISALLOW_LOOPS:
            if _has_loop(src, dst):
                raise GizmoError('This connection would create a loop')

        for name in param_names:
            names = name.split(':')
            if len(names)==1:
                outp = inp = names[0]
            elif len(names)==2:
                outp, inp = names
            else:
                raise GizmoError(f'Name {name} cannot have more than one ":"')

            srcp = getattr(src.param, outp)
            if srcp.allow_refs:
                raise GizmoError(f'Source parameter {inp} must not be "allow_refs=True"')

            dstp = getattr(dst.param, inp)
            if not dstp.allow_refs:
                raise GizmoError(f'Destination parameter {inp} must be "allow_refs=True"')

            # print(f'connect {src}.{outp} -> {dst}.{inp}')

            # If this doesn't work, it's possible that a gizmo didn't call super().__init__().
            #
            setattr(dst, inp, getattr(src.param, outp))

        _gizmo_graph.append((src, dst))

    @staticmethod
    def disconnect(g: Gizmo) -> None:
        """Disconnect gizmo g from other gizmos.

        We can look in the gizmo to see what it is watching,
        but we need to look through all the other gizmos to see
        if they watch this one.
        """

        for p, watchers in g.param.watchers.items():
            for watcher in watchers['value']:
                # print(f'disconnect watcher {g.name}.{watcher}')
                g.param.unwatch(watcher)

        for src, dst in _gizmo_graph:
            if dst is g:
                for p, watchers in src.param.watchers.items():
                    for watcher in watchers['value']:
                        # print(f'disconnect watcher {src.name}.{watcher}')
                        src.param.unwatch(watcher)

        _gizmo_graph[:] = [(src, dst) for src, dst in _gizmo_graph if src is not g and dst is not g]
