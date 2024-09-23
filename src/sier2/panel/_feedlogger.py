
"""A logger that logs to a panel.widget.Feed."""

from datetime import datetime
import html
import logging
import panel as pn

from .._block import BlockState
from ._panel_util import _get_state_color

_INFO_FORMATTER = logging.Formatter('%(asctime)s %(block_state)s %(block_name)s %(message)s', datefmt='%H:%M:%S')
_FORMATTER = logging.Formatter('%(asctime)s %(block_state)s %(block_name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

class PanelHandler(logging.Handler):
    """A handler that emits log strings to a panel template sidebar Feed pane."""

    def __init__(self, log_feed):
        super().__init__()
        self.log_feed = log_feed

    def format(self, record):
        # TODO override logging.Formatter.formatException to <pre> the exception string.

        color = _get_state_color(record.block_state)

        record.block_name = f'[{html.escape(record.block_name)}]' if record.block_name else ''
        record.block_state = f'<span style="color:{color};">■</span>'
        record.msg = html.escape(record.msg)
        fmt = _INFO_FORMATTER if record.levelno==logging.INFO else _FORMATTER

        return fmt.format(record)

    def emit(self, record):
        if record.block_state is None:
            self.log_feed.clear()
            return

        try:
            msg = self.format(record)
            self.log_feed.append(pn.pane.HTML(msg))
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

class DagPanelAdapter(logging.LoggerAdapter):
    """An adapter that logs messages from a dag.

    Each message also specifies a block name and state.
    """

    def debug(self, msg, *args, block_name, block_state):
        super().debug(msg, *args, extra={'block_name': block_name, 'block_state': block_state})

    def info(self, msg, *args, block_name, block_state):
        super().info(msg, *args, extra={'block_name': block_name, 'block_state': block_state})

    def warning(self, msg, *args, block_name, block_state):
        super().warning(msg, *args, extra={'block_name': block_name, 'block_state': block_state})

    def error(self, msg, *args, block_name, block_state):
        super().error(msg, *args, extra={'block_name': block_name, 'block_state': block_state})

    def exception(self, msg, *args, block_name, block_state):
        super().exception(msg, *args, extra={'block_name': block_name, 'block_state': block_state})

    def critical(self, msg, *args, block_name, block_state):
        super().critical(msg, *args, extra={'block_name': block_name, 'block_state': block_state})

    def process(self, msg, kwargs):
        # print(f'ADAPTER {msg=} {kwargs=} {self.extra=}')
        if 'block_state' not in kwargs['extra']:
            kwargs['extra']['block_state'] = '?'
        if 'block_name' not in kwargs['extra']:
            kwargs['extra']['block_name'] = 'g'

        return msg, kwargs

_logger = logging.getLogger('block.panel')
_logger.setLevel(logging.INFO)

# ph = PanelHandler(log_feed)
# ph.log_feed = log_feed
# ph.setLevel(logging.INFO)

# _logger.addHandler(ph)

def getDagPanelLogger(log_feed):
    # _logger = logging.getLogger('block.panel')
    # _logger.setLevel(logging.INFO)

    ph = PanelHandler(log_feed)
    ph.log_feed = log_feed
    ph.setLevel(logging.INFO)

    _logger.addHandler(ph)

    adapter = DagPanelAdapter(_logger)

    return adapter

####

class BlockPanelAdapter(logging.LoggerAdapter):
    """An adapter that logs messages from a block.

    A state isn't required, because if a block is logging something,
    it's executing by definition.

    A name isn't required in the logging methods, because the name is
    implicit.
    """

    def __init__(self, logger, block_name, extra=None):
        super().__init__(logger, extra)
        self.block_name = block_name

    def debug(self, msg, *args):
        super().debug(msg, *args, extra={'block_name': self.block_name, 'block_state': BlockState.BLOCK})

    def info(self, msg, *args):
        super().info(msg, *args, extra={'block_name': self.block_name, 'block_state': BlockState.BLOCK})

    def warning(self, msg, *args):
        super().warning(msg, *args, extra={'block_name': self.block_name, 'block_state': BlockState.BLOCK})

    def error(self, msg, *args):
        super().error(msg, *args, extra={'block_name': self.block_name, 'block_state': BlockState.BLOCK})

    def exception(self, msg, *args):
        super().exception(msg, *args, extra={'block_name': self.block_name, 'block_state': BlockState.BLOCK})

    def critical(self, msg, *args):
        super().critical(msg, *args, extra={'block_name': self.block_name, 'block_state': BlockState.BLOCK})

    def process(self, msg, kwargs):
        # print(f'GP ADAPTER {msg=} {kwargs=} {self.extra=}')
        if 'block_state' not in kwargs['extra']:
            kwargs['extra']['block_state'] = BlockState.BLOCK
        if 'block_name' not in kwargs['extra']:
            kwargs['extra']['block_name'] = self.block_name

        return msg, kwargs

def getBlockPanelLogger(block_name: str):
    """A logger for blocks.

    The dag gets its logger first, so we can reuse _logger."""

    adapter = BlockPanelAdapter(_logger, block_name)

    return adapter