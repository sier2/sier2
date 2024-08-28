from .._block import BlockState

def _get_state_color(gs: BlockState) -> str:
    """Convert a block state (as logged by the dag) to a color.

    The colors are arbitrary, except for GIZMO. When a block logs a message,
    it is executing by definition, so no color is required.
    """

    match gs:
        case BlockState.BLOCK:
            color = 'var(--panel-background-color)'
        case BlockState.DAG:
            color = 'grey'
        case BlockState.INPUT:
            color = '#f0c820'
        case BlockState.READY:
            color='white'
        case BlockState.EXECUTING:
            color='steelblue'
        case BlockState.WAITING:
            color='yellow'
        case BlockState.SUCCESSFUL:
            color = 'green'
        case BlockState.INTERRUPTED:
            color= 'orange'
        case BlockState.ERROR:
            color = 'red'
        case _:
            color = 'magenta'

    return color
