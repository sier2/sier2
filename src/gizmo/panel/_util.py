from .._gizmo import GizmoState

def _get_state_color(gs: GizmoState) -> str:
    """Convert a gizmo state (as logged by the dag) to a color.

    The colors are arbitrary, except for GIZMO. When a gizmo logs a message,
    it is executing by definition, so no color is required.
    """

    match gs:
        case GizmoState.GIZMO:
            color = 'var(--panel-background-color)'
        case GizmoState.DAG:
            color = 'grey'
        case GizmoState.INPUT:
            color = '#f0c820'
        case GizmoState.READY:
            color='white'
        case GizmoState.EXECUTING:
            color='steelblue'
        case GizmoState.WAITING:
            color='yellow'
        case GizmoState.SUCCESSFUL:
            color = 'green'
        case GizmoState.INTERRUPTED:
            color= 'orange'
        case GizmoState.ERROR:
            color = 'red'
        case _:
            color = 'magenta'

    return color
