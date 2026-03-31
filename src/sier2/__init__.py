from ._block import Block, BlockError, BlockValidateError
from ._config import Config
from ._dag import BlockState, Connection, Connections, Dag
from ._library import Info, Library
from ._util import get_block_config
from ._version import __version__

Block.__module__ = 'sier2'
BlockError.__module__ = 'sier2'
BlockValidateError.__module__ = 'sier2'
Config.__module__ = 'sier2'
BlockState.__module__ = 'sier2'
Connection.__module__ = 'sier2'
Connections.__module__ = 'sier2'
Dag.__module__ = 'sier2'
Info.__module__ = 'sier2'
Library.__module__ = 'sier2'
get_block_config.__module__ = 'sier2'

__all__ = [
    'Block',
    'BlockError',
    'BlockValidateError',
    'Config',
    'BlockState',
    'Connection',
    'Connections',
    'Dag',
    'Info',
    'Library',
    'get_block_config',
    '__version__',
]
