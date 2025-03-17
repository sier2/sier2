from functools import cache
import importlib
from importlib.metadata import entry_points
import sys
import warnings

from sier2 import BlockError

def _import_item(key):
    """Look up an object by key.

    The returned object may be a class (if a Block key) or a function (if a dag key).

    See the Entry points specification at
    https://packaging.python.org/en/latest/specifications/entry-points/#entry-points.
    """

    modname, qualname_separator, qualname = key.partition(':')
    try:
        obj = importlib.import_module(modname)
        if qualname_separator:
            for attr in qualname.split('.'):
                obj = getattr(obj, attr)

        return obj
    except ModuleNotFoundError as e:
        msg = str(e)
        if not qualname_separator:
            msg = f'{msg}. Is there a \':\' missing?'
        raise BlockError(msg)

@cache
def get_block_config():
    """A convenience function to get block configuration data.

    Block can run in different environments; for example, a block that has access to the
    Internet may use a different configuration to the same block running in a corporate
    environment.

    This function looks up a block configuration provider using the ``sier2.config`` entry point,
    which has the form `module-name:function-name`.

    If no config package is found, or more than one config package is found,
    a warning will be produced (using `warnings.warn()`), and a default config will be returned,
    with the ``'config'`` key having the value ``None``.

    See the `sier2-blocks-config` package for an example.
    """

    eps = list(entry_points(group='sier2.config'))
    if len(eps)==1:
        ep = eps[0].value
        config_func = _import_item(ep)
        config = config_func()
    else:
        msg = 'No block configuration found' if not eps else 'Multiple configs found'
        warnings.warn(f'{msg}: returning config None')
        config = {'config': None}

    if 'config' not in config:
        raise BlockError('config dictionary does not contain "config" key')

    return config

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
