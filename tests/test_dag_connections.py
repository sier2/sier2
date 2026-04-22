import os
import tempfile
from datetime import UTC, datetime

import param
import pytest

from sier2 import Block, BlockError, Dag


class PassThrough(Block):
    """Pass a value through unchanged."""

    in_p = param.Integer(default=0)
    out_p = param.Integer(default=0)

    def execute(self):
        self.out_p = self.in_p


class PassThrough2(Block):
    """Pass a value through unchanged."""

    in_p1 = param.Integer(default=0)
    in_p2 = param.Integer(default=0)
    out_p1 = param.Integer(default=0)
    out_p2 = param.Integer(default=0)

    def execute(self):
        self.out_p1 = self.in_p1
        self.out_p2 = self.in_p2


class Types(Block):
    """Demonstrate loading default values."""

    in_int = param.Integer()
    in_num = param.Number()
    in_str = param.String()
    in_bool = param.Boolean()
    in_dt = param.Date()
    in_dtz = param.Date()
    in_dtr = param.DateRange()

    out_int = param.Integer()

    def execute(self):
        self.out_int = self.in_int


def test_build1(Dag_f):
    b1 = PassThrough()
    b2 = PassThrough()

    dag = Dag_f([(b1.param.out_p, b2.param.in_p)])

    b1.in_p = 86
    dag.execute()

    assert b2.out_p == 86


def test_build2(Dag_f):
    b1 = PassThrough2()
    b2 = PassThrough2()

    dag = Dag_f([(b1.param.out_p1, b2.param.in_p1), (b1.param.out_p2, b2.param.in_p2)])

    b1.in_p1 = 86
    b1.in_p2 = 99
    dag.execute()

    assert b2.out_p1 == 86
    assert b2.out_p2 == 99


def test_build_dup_params(Dag_f):
    b1 = PassThrough()
    b2 = PassThrough()

    with pytest.raises(BlockError, match='params at index 1 are already connected'):
        Dag_f([
            (b1.param.out_p, b2.param.in_p),
            (b1.param.out_p, b2.param.in_p),
        ])


def test_not_a_block_instance(Dag_f):
    """Check that a Block object is used, not the Block class."""
    b1 = PassThrough()

    with pytest.raises(BlockError, match='at index 0?'):
        Dag_f([(b1.param.out_p, PassThrough.param.in_p)])


def test_not_a_param(Dag_f):
    b1 = PassThrough()

    with pytest.raises(BlockError, match='Source parameter at index 0 is not a param'):
        Dag_f([('hello', b1.in_p)])


def test_out_to_out(Dag_f):
    a = PassThrough()
    b = PassThrough()

    with pytest.raises(BlockError, match='Destination block at index 0 must start with "in_"'):
        Dag_f([(a.param.out_p, b.param.out_p)])


def test_in_to_in(Dag_f):
    a = PassThrough()
    b = PassThrough()

    with pytest.raises(BlockError, match='Source block at index 0 must start with "out_"'):
        Dag_f([(a.param.in_p, b.param.in_p)])


def test_in_to_out(Dag_f):
    a = PassThrough()
    b = PassThrough()

    with pytest.raises(BlockError, match='Source block at index 0 must start with "out_"'):
        Dag_f([(a.param.in_p, b.param.out_p)])


def test_connected(Dag_f):
    a = PassThrough()
    b = PassThrough()
    c = PassThrough()
    d = PassThrough()

    dag = Dag_f({
        (a.param.out_p, b.param.in_p),
        (c.param.out_p, d.param.in_p),
        (b.param.out_p, c.param.in_p),
    })

    a.in_p = 86
    dag.execute()

    assert d.out_p == 86


def test_disconnected(Dag_f):
    a = PassThrough(name='a')
    b = PassThrough(name='b')
    c = PassThrough(name='c')
    d = PassThrough(name='d')

    with pytest.raises(BlockError, match='not connected'):
        Dag_f([
            (a.param.out_p, b.param.in_p),
            (c.param.out_p, d.param.in_p),
        ])


def test_already_connected(Dag_f):
    a = PassThrough(name='a')
    b = PassThrough(name='b')

    with pytest.raises(BlockError, match='already connected'):
        Dag_f([
            (a.param.out_p, b.param.in_p),
            (a.param.out_p, b.param.in_p),
        ])


def test_same_name(Dag_f):
    a = PassThrough(name='a')
    b = PassThrough(name='a')

    with pytest.raises(BlockError, match='same name at index 0'):
        Dag_f([
            (a.param.out_p, b.param.in_p),
        ])


def test_same_name2(Dag_f):
    a = PassThrough(name='a')
    b = PassThrough(name='b')
    c = PassThrough(name='a')

    with pytest.raises(BlockError, match='name "a" at index 1 duplicates'):
        Dag_f([
            (a.param.out_p, b.param.in_p),
            (b.param.out_p, c.param.in_p),
        ])


def test_triangle(Dag_f):
    root = PassThrough(name='root')
    leg1 = PassThrough(name='leg1')
    leg2 = PassThrough(name='leg2')

    dag = Dag_f([
        (root.param.out_p, leg1.param.in_p),
        (root.param.out_p, leg2.param.in_p),
    ])

    root.in_p = 99
    dag.execute()

    assert leg1.out_p == 99
    assert leg2.out_p == 99


def test_load_defaults(Dag_f):
    """Demonstrate loading default values.

    During development, it is convenient to pre-load some default values to save typing
    when running the app. These values should not be hard-coded into the code:
    they may contain API keys, development-time defaults cannot be differentiated
    from run-time defaults, and the developer may forget to remove them before publishing
    the app.

    Instead, we use the presence of an environment variable referring to a TOML file.
    If the environment variable is present when the dag is built, the values will be
    loaded: TOML table headers -> block names, TOML keys -> block params.
    """

    # Create a config file containing default values.
    # This is typically done by the developer when testing an app.
    #
    tmp = tempfile.gettempdir()
    fnam = f'{tmp}/test_defaults.toml'
    with open(fnam, 'w') as f:
        print(
            '''[DefaultsBlock]
in_int = 86
in_num = 2.718
in_str = 'This is a string'
in_bool = true
in_dt = 2022-12-01 12:34:56
in_dtz = 2022-12-01 12:34:56Z
in_dtr = [2022-01-01 12:34:56Z, 2022-12-01 12:34:56Z]
''',
            file=f,
        )

    # The existence of the SIER2_DAG_DEFAULTS environment variable
    # indicates that there is a defaults file.
    # This is typically done at a command prompt before running the app.
    # (More convenient on Linux than Windows.)
    #
    os.environ[Dag.SIER2_DAG_DEFAULTS] = fnam

    try:
        # The dag / app.
        #
        types = Types(name='DefaultsBlock')
        b2 = PassThrough()

        # Because the environment variable is set, default loading happens by magic.
        #
        dag = Dag_f([
            (types.param.out_int, b2.param.in_p),
        ])

        assert types.in_int == 86
        assert types.in_num == 2.718
        assert types.in_str == 'This is a string'
        assert types.in_bool
        assert types.in_dt == datetime(2022, 12, 1, 12, 34, 56)  # noqa: DTZ001
        assert types.in_dtz == datetime(2022, 12, 1, 12, 34, 56, tzinfo=UTC)
        assert types.in_dtr == (
            datetime(2022, 1, 1, 12, 34, 56, tzinfo=UTC),
            datetime(2022, 12, 1, 12, 34, 56, tzinfo=UTC),
        )

        dag.execute()

        assert b2.in_p == 86
    finally:
        # Undo the temporary things.
        #
        del os.environ[Dag.SIER2_DAG_DEFAULTS]
        os.unlink(fnam)
