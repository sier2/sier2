
"""A logger that logs to a panel.widget.Feed."""

from datetime import datetime
import html
import logging
import panel as pn

from .._gizmo import GizmoState
from ._util import _get_state_color

_INFO_FORMATTER = logging.Formatter('%(asctime)s %(gizmo_state)s %(gizmo_name)s %(message)s', datefmt='%H:%M:%S')
_FORMATTER = logging.Formatter('%(asctime)s %(gizmo_state)s %(gizmo_name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

class PanelHandler(logging.Handler):
    """A handler that emits log strings to a panel template sidebar Feed pane."""

    def __init__(self, log_feed):
        super().__init__()
        self.log_feed = log_feed

    def format(self, record):
        # TODO override logging.Formatter.formatException to <pre> the exception string.

        color = _get_state_color(record.gizmo_state)

        record.gizmo_name = f'[{html.escape(record.gizmo_name)}]' if record.gizmo_name else ''
        record.gizmo_state = f'<span style="color:{color};">■</span>'
        record.msg = html.escape(record.msg)
        fmt = _INFO_FORMATTER if record.levelno==logging.INFO else _FORMATTER

        return fmt.format(record)

    def emit(self, record):
        if record.gizmo_state is None:
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

    Each message also specifies a gizmo name and state.
    """

    def debug(self, msg, *args, gizmo_name, gizmo_state):
        super().debug(msg, *args, extra={'gizmo_name': gizmo_name, 'gizmo_state': gizmo_state})

    def info(self, msg, *args, gizmo_name, gizmo_state):
        super().info(msg, *args, extra={'gizmo_name': gizmo_name, 'gizmo_state': gizmo_state})

    def warning(self, msg, *args, gizmo_name, gizmo_state):
        super().warning(msg, *args, extra={'gizmo_name': gizmo_name, 'gizmo_state': gizmo_state})

    def error(self, msg, *args, gizmo_name, gizmo_state):
        super().error(msg, *args, extra={'gizmo_name': gizmo_name, 'gizmo_state': gizmo_state})

    def exception(self, msg, *args, gizmo_name, gizmo_state):
        super().exception(msg, *args, extra={'gizmo_name': gizmo_name, 'gizmo_state': gizmo_state})

    def critical(self, msg, *args, gizmo_name, gizmo_state):
        super().critical(msg, *args, extra={'gizmo_name': gizmo_name, 'gizmo_state': gizmo_state})

    def process(self, msg, kwargs):
        # print(f'ADAPTER {msg=} {kwargs=} {self.extra=}')
        if 'gizmo_state' not in kwargs['extra']:
            kwargs['extra']['gizmo_state'] = '?'
        if 'gizmo_name' not in kwargs['extra']:
            kwargs['extra']['gizmo_name'] = 'g'

        return msg, kwargs

_logger = logging.getLogger('gizmo.panel')
_logger.setLevel(logging.INFO)

# ph = PanelHandler(log_feed)
# ph.log_feed = log_feed
# ph.setLevel(logging.INFO)

# _logger.addHandler(ph)

def getDagPanelLogger(log_feed):
    # _logger = logging.getLogger('gizmo.panel')
    # _logger.setLevel(logging.INFO)

    ph = PanelHandler(log_feed)
    ph.log_feed = log_feed
    ph.setLevel(logging.INFO)

    _logger.addHandler(ph)

    adapter = DagPanelAdapter(_logger)

    return adapter

####

class GizmoPanelAdapter(logging.LoggerAdapter):
    """An adapter that logs messages from a gizmo.

    A state isn't required, because if a gizmo is logging something,
    it's executing by definition.

    A name isn't required in the logging methods, because the name is
    implicit.
    """

    def __init__(self, logger, gizmo_name, extra=None):
        super().__init__(logger, extra)
        self.gizmo_name = gizmo_name

    def debug(self, msg, *args):
        super().debug(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': GizmoState.GIZMO})

    def info(self, msg, *args):
        super().info(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': GizmoState.GIZMO})

    def warning(self, msg, *args):
        super().warning(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': GizmoState.GIZMO})

    def error(self, msg, *args):
        super().error(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': GizmoState.GIZMO})

    def exception(self, msg, *args):
        super().exception(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': GizmoState.GIZMO})

    def critical(self, msg, *args):
        super().critical(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': GizmoState.GIZMO})

    def process(self, msg, kwargs):
        # print(f'GP ADAPTER {msg=} {kwargs=} {self.extra=}')
        if 'gizmo_state' not in kwargs['extra']:
            kwargs['extra']['gizmo_state'] = GizmoState.GIZMO
        if 'gizmo_name' not in kwargs['extra']:
            kwargs['extra']['gizmo_name'] = self.gizmo_name

        return msg, kwargs

def getGizmoPanelLogger(gizmo_name: str):
    """A logger for gizmos.

    The dag gets its logger first, so we can reuse _logger."""

    adapter = GizmoPanelAdapter(_logger, gizmo_name)

    return adapter