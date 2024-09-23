import sys
from .._block import BlockState
from .._util import trim

def _get_state_color(gs: BlockState) -> str:
    """Convert a block state (as logged by the dag) to a color.

    The colors are arbitrary, except for BLOCK. When a block logs a message,
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

########
# Documentation utilities
########

def block_doc(block):
    """Generate Markdown documentation for a block.

    The documentation is taken from the docstring of the block class
    and the doc of each 'in_' and 'out_' param.
    """

    # Force the first line of the block docstring to have a level 2 header.
    #
    b_doc = '## ' + trim(block.__doc__).lstrip(' #')

    params = []
    for name, p in block.param.objects().items():
        if name.startswith(('in_', 'out_')):
            doc = p.doc if p.doc else ''
            params.append((name, doc.strip()))

    params.sort()
    text = ['| Name | Description |', '| ---- | ---- |']
    for name, doc in params:
        text.append(f'| {name} | {doc}')

    return '---\n' + b_doc + '\n### Params\n' + '\n'.join(text)

def dag_doc(dag):
    """Generate Markdown documentation for a dag and its blocks."""

    # A Block may be in the dag more than once.
    # Don't include the documentation for such blocks more than once.
    #
    blocks = dag.get_sorted()
    uniq_blocks = []
    seen_blocks = set()
    for b in blocks:
        if type(b) not in seen_blocks:
            uniq_blocks.append(b)
            seen_blocks.add(type(b))
    block_docs = '\n\n'.join(block_doc(block) for block in uniq_blocks)

    # Force the first line of the dag doc to have a level 1 header.
    #
    dag_text =f'# {dag.site} - {dag.title}\n\n# ' + trim(dag.doc).lstrip(' #')

    return f'{dag_text}\n\n{block_docs}'
