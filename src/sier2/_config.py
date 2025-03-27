# A configuration module.
#

import ast
import configparser
import os
from pathlib import Path
from typing import Any

def _default_config_file():
    if os.name=='nt':
        prdir = Path(os.environ['APPDATA']) / 'sier2'
    else:
        prdir = os.environ['XDG_CONFIG_HOME']
        if prdir:
            prdir = Path(prdir)
        else:
            prdir = Path.home() / '.config'

        prdir = prdir / 'sier2'

    if not prdir.exists():
        prdir.mkdir(parents=True)

    return prdir / 'sier2.ini'

class _Config:
    """This class is for internal use.

    A single instance of this class is exposed publicly as ``Config``.
    The only publicly supported ways of accessing ``Config`` are:
    - via __getitem__, i.e. using Config['section.name'] to retrieve
    a dictionary containing that section's keys and values;
    - the ``location`` property, to use an alternate non-default config file.

    Everything else is used internally by sier2.
    """

    def __init__(self):
        self._location = _default_config_file()
        self.config = {}
        self.loaded = False

    @property
    def location(self) -> Path:
        return self._location

    @location.setter
    def location(self, config_file: Path):
        if self.loaded:
            raise ValueError('Config is already loaded')

        if not isinstance(config_file, Path):
            config_file = Path(config_file)

        self._location = config_file

    def _load(self):
        """Load the config."""

        if self._location.is_file():
            self.config = configparser.ConfigParser()
            self.config.read(self._location)

        # The config has been loaded, even if the file didn't exist.
        #
        self.loaded = True

    def _load_string(self, sconfig):
        """For testing."""

        self.config = configparser.ConfigParser()
        self.config.read_string(sconfig)
        self.loaded = True

    def __getitem__(self, section: str) -> dict[str, Any]:
        """Get the config values for the given section name.

        The config file is lazily loaded. Non-existence of the file is normal.
        The keys and values for the specified section are loaded into a new dictionary,
        which is returned.

        Since configparser always returns values as strings, the values are evaluated
        using ast.literal_eval() to be correctly typed. This means that strings in the
        .ini file must be surrounded by quotes.

        A section name for a block is of the form 'block.block_key_name'.

        The name need not to exist; if it doesn't, an empty dictionary is returned.
        """

        if not self.loaded:
            self._load()

        if section not in self.config:
            return {}

        c = {}
        for k, v in self.config[section].items():
            try:
                c[k] = ast.literal_eval(v)
            except ValueError:
                raise ValueError(f'Cannot eval section [{section}], key {k}, value {v}')

        return c

Config = _Config()
