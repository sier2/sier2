import param

class GizmoError(Exception):
    pass

class Gizmo(param.Parameterized):
    pass

_gizmo_graph = []

class GizmoManager:
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

        for name in param_names:
            names = name.split(':')
            if len(names)==1:
                outp = inp = names[0]
            elif len(names)==2:
                outp, inp = names
            else:
                raise GizmoError(f'Name {name} cannot have more than one ":"')

            dstp = getattr(dst.param, inp)
            if not dstp.allow_refs:
                raise GizmoError(f'Destination parameter {inp} must be "allow_refs=True"')

            # print(f'connect {src}.{outp} -> {dst}.{inp}')
            setattr(dst, inp, getattr(src.param, outp))

        _gizmo_graph.append((src, dst))

    @staticmethod
    def disconnect(g: Gizmo):
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
