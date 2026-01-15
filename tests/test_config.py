from pathlib import Path
import tempfile

import pytest

from sr2 import Config

CONFIG_NAME = 'test.ini'

def test_config():
    INI = '''
[block.types]
string1 = 'one'
int1 = 1
bool1 = True
float1 = 1.0

[block.more]
'''

    Config._clear()
    Config._load_string(INI)

    conf = Config['block.none']
    assert not conf

    conf = Config['block.types']

    string1 = conf['string1']
    assert string1=='one' and type(string1) is str

    int1 = conf['int1']
    assert int1==1 and type(int1) is int

    bool1 = conf['bool1']
    assert bool1 is True and type(bool1) is bool

    float1 = conf['float1']
    assert float1==1.0 and type(float1) is float

def test_bad_block():
    INI = '''
[block.badvalue]
string1 = one
'''
    Config._clear()
    Config._load_string(INI)

    with pytest.raises(ValueError):
        conf = Config['block.badvalue']

def test_bad_value():
    INI = '''
[block.badvalue]
string1 = one
int1 = 1
'''
    Config._clear()
    Config._load_string(INI)

    int1 = Config['block.badvalue', 'int1']
    assert int1==1

    with pytest.raises(ValueError):
        string1 = Config['block.badvalue', 'string1']

def test_update():
    # Initial config.
    #
    INI = '''
[section1]
key1a = 'value1a'
[section2]
key2a = 'value2a'
config_update = False
[section3]
key3a = 'value3a'
'''

    NEW_INI = '''
[section1]
key1a = 'value1a-new'
key1b = 'value1b-new'
[section2]
key2a = 'value2a-new'
key2b = 'value2b-new'
[section4]
key4a = 'value4a-new'
'''

    tmp_config = Path(tempfile.gettempdir()) / CONFIG_NAME
    with open(tmp_config, 'w') as f:
        print(INI, file=f)

    try:
        Config._clear()
        Config.location = tmp_config

        Config._update(NEW_INI, write_to_file=True)

        Config._clear()
        Config.location = tmp_config
        Config._load()

        sections = Config._config.sections()
        assert len(sections)==4

        # section1 has been updated
        assert Config['section1', 'key1a']=='value1a-new'
        assert Config['section1', 'key1b']=='value1b-new'

        # section2 is untouched (config_update = False)
        assert Config['section2', 'key2a']=='value2a'
        assert Config['section2', 'key2b'] is None

        # section3 is untouched (no update)
        assert Config['section3', 'key3a']=='value3a'

        # section4 has been created
        assert Config['section4', 'key4a']=='value4a-new'
    finally:
        tmp_config.unlink()
