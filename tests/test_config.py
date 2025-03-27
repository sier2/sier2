import pytest

from sier2 import Config

def test_config():
    INI = '''
[block.types]
string1 = 'one'
int1 = 1
bool1 = True
float1 = 1.0

[block.more]
'''

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

def test_bad():
    INI = '''
[block.badvalue]
string1 = one
'''
    Config._load_string(INI)

    with pytest.raises(ValueError):
        conf = Config['block.badvalue']
