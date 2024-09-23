import sys

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

def block_doc_text(block):
    """Generate text documentation for a block.

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
    text = []
    for name, doc in params:
        text.append(f'- {name}:  {doc}\n')

    return '---\n' + b_doc + '\n### Params\n' + '\n'.join(text)

def dag_doc_text(dag):
    """Generate text documentation for a dag."""

    # Force the first line of the dag doc to have a level 1 header.
    #
    dag_text =f'# {dag.site} - {dag.title}\n\n# ' + trim(dag.doc).lstrip(' #')

    return dag_text
