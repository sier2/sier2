import sys
from .._block import BlockState

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

def trim(docstring):
    """From PEP-257: Fix docstring indentation"""

    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)

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