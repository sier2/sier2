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
    """Determine the location of the config file sier2.ini.

    If the environment variable ``SIER2_INI`` is set,
    it specifies the path of the config file.

    Otherwise, if Windows, use ``$env:APPDATA/sier2/sier2.ini``.

    Otherwise, if ``XDG_CONFIG_HOME`` is set, use ``$XDG_CONFIG_HOME/sier2/sier2.ini``.

    Otherwise, use ``$HOME/.config/sier2/sier2.ini``.

    If not using ``SIER2_INI``, the ``sier2`` directory will be created
    if it does not exist.

    TODO don't create the sier2 directory until the ini file is written.
    """

    # If a config file has been explicitly set in an environment variable,
    # use it.
    #
    ini = os.environ.get('SIER2_INI', None)
    if ini:
        return Path(ini)

    if os.name=='nt':
        # Windows.
        #
        prdir = Path(os.environ['APPDATA']) / 'sier2'
    else:
        # Linux.
        #
        prdir = os.environ.get('XDG_CONFIG_HOME', None)
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

    @staticmethod
    def update(*, location: Path|str|None=None, config_block: str|None=None, update_arg: str|None=None, write_to_file: bool=False):
        """Update the config.

        If ``location`` has a value, that config file will be used instead of the default.

        If config_block has a value, it must be the name of a block that has
        an ``out_config`` param. The ``out_config`` param must contain a string that is
        the content of a sier2 ini file. If ``update_arg`` is specified and the block has
        an ``in_arg`` param, ``in_arg`` is set to ``update_arg``.

        Parameters
        ----------
        location: Path|str|None
            The location of a config file that will be loaded when a config is read.
        config_block: str|None
            A sier2 block that returns the contents of a config file in ``out_config``.
        update_arg: str|None
            A string that is passed to the ``config_block`` block is it has an ``in_arg`` param.
        write_to_file: bool
            If True, the config file at ``location`` is overwritten with the merged config.
        """

        if location:
            Config.location = location

        if config_block:
            # Import here, otherwise there's a circular dependency Library -> Config -> Library.
            # Config blocks better not have any config.
            #
            from sier2 import Library

            block = Library.get_block(config_block)()

            if not hasattr(block, 'out_config'):
                raise ValueError('config block does not have out param "out_config"')

            if hasattr(block, 'in_arg'):
                block.in_arg = update_arg

            block.execute()
            Config._update(block.out_config, write_to_file=write_to_file)

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

    def _update(self, ini: str, write_to_file: bool=False):
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
            if not config.has_section(section_name):
                config.add_section(section_name)
                config[section_name].update(new_config[section_name])
            else:
                update_section = True
                if CONFIG_UPDATE in config[section_name]:
                    update_section = ast.literal_eval(config[section_name][CONFIG_UPDATE])
                    if not isinstance(update_section, bool):
                        raise ValueError(f'Value of [{section_name}].{CONFIG_UPDATE} is not a bool')

                if update_section:
                    config[section_name].update(new_config[section_name])
                    # for k, v in new_config[section_name].items():
                    #     config[section_name][k] = new_config[section_name][k]

        if write_to_file:
            with open(self._location, 'w', encoding='utf-8') as f:
                config.write(f)

        self._config = config
        self._loaded = True

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
