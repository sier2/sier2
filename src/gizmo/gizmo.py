import param

class GizmoError(Exception):
    pass

class Gizmo(param.Parameterized):
    pass

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
