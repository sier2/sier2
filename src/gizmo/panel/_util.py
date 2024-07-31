from .._gizmo import GizmoState

def _get_state_color(gs: GizmoState) -> str:
    """Convert a gizmo state to a color."""

    match gs:
        case GizmoState.LOG:
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
