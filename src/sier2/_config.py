# A configuration module.
#

import ast
import configparser
import os
from pathlib import Path
from typing import Any

# If this key exists in a section and has the value False,
# this section will not be updated.
#
CONFIG_UPDATE = 'config_update'

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
    """

    def __init__(self):
        self._clear()

    def _clear(self):
        self._location = _default_config_file()
        self._config = {}
        self._loaded = False

    @property
    def location(self) -> Path:
        """Get or set the config file location.

        By default, this is `$ENV:APPDATA/sier2/sier2.ini` on Window,
        and `$XDG_CONFIG_HOME/sier2/sier2.ini` on Linux.

        The location cannot be set if the config file has already been loaded.
        """

        return self._location

    @location.setter
    def location(self, config_file: Path|str):
        if self._loaded:
            raise ValueError('Config is already loaded')

        if not isinstance(config_file, Path):
            config_file = Path(config_file)

        self._location = config_file

    def _update(self, ini: str):
        """Update the config file using ini, which contains the contents of another config file.

        The current config is also updated.

        The config file cannot be updated if it has already been loaded.
        """

        if self._loaded:
            raise ValueError('Config is already loaded')

        new_config = configparser.ConfigParser()
        new_config.read_string(ini)

        config = configparser.ConfigParser()
        if self._location.is_file():
            config.read(self._location)

        for section_name in new_config.sections():
            if section_name not in config.sections():
                config[section_name] = new_config[section_name]
            else:
                update_section = True
                if CONFIG_UPDATE in config[section_name]:
                    update_section = ast.literal_eval(config[section_name][CONFIG_UPDATE])
                    if not isinstance(update_section, bool):
                        raise ValueError(f'Value of [{section_name}].{CONFIG_UPDATE} is not a bool')

                if update_section:
                    for k, v in new_config[section_name].items():
                        config[section_name][k] = new_config[section_name][k]

        with open(self._location, 'w', encoding='utf-8') as f:
            config.write(f)

        self._config = config

    def _load(self):
        """Load the config.

        Overwrites any previous config. If the location does not exist, the config will be empty.
        """

        self._config = configparser.ConfigParser()
        if self._location.is_file():
            self._config.read(self._location)

        # The config has been loaded, even if the file didn't exist.
        #
        self._loaded = True

    def _load_string(self, sconfig):
        """For testing."""

        self._config = configparser.ConfigParser()
        self._config.read_string(sconfig)
        self._loaded = True

    def __getitem__(self, section_name: str|tuple[str, str]) -> Any|dict[str, Any]:
        """If section_name is a string, get the config values for the given section name.

        The config file is lazily loaded. Non-existence of the file is normal.
        The keys and values for the specified section are loaded into a new dictionary,
        which is returned.

        Since configparser always returns values as strings, the values are evaluated
        using :func:`ast.literal_eval` to be correctly typed. This means that strings in the
        .ini file must be surrounded by quotes.

        A section name for a block is of the form 'block.block_key_name'.

        The name need not to exist; if it doesn't, an empty dictionary is returned.

        If section_name is a tuple, it is interpreted as (section_name, key). If the
        section_name and key exist, the value of the key is returned, else None is returned.
        Only that single value is evaluated.
        """

        if not self._loaded:
            self._load()

        if isinstance(section_name, tuple):
            section_name, key = section_name
            if section_name not in self._config:
                return None

            section = self._config[section_name]
            if key not in section:
                return None

            try:
                v = section[key]
                return ast.literal_eval(v)
            except ValueError:
                raise ValueError(f'Cannot eval section [{section_name}], key {key}, value {v}')

        if section_name not in self._config:
            return {}

        c = {}
        for key, v in self._config[section_name].items():
            try:
                c[key] = ast.literal_eval(v)
            except ValueError:
                raise ValueError(f'Cannot eval section [{section_name}], key {key}, value {v}')

        return c

Config = _Config()
