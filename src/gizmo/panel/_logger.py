from datetime import datetime
import html
import logging
import panel as pn

from .._gizmo import GizmoState
from ._util import _get_state_color

info_formatter = logging.Formatter('%(asctime)s %(gizmo_state)s %(gizmo_name)s %(message)s', datefmt='%H:%M:%S')
formatter = logging.Formatter('%(asctime)s %(gizmo_state)s %(gizmo_name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# def c(status):
#      return pn.Spacer(
#             margin=(8, 0, 0, 0),
#             styles={'width':'20px', 'height':'20px', 'background':status, 'border-radius': '10px'}
#         )

class PanelHandler(logging.Handler):
    def __init__(self, log_feed):
        super().__init__()
        self.log_feed = log_feed

    def format(self, record):
        # TODO override logging.Formatter.formatException to <pre> the exception string.

        # print(f'FORMAT {record.levelname} {record};{record.status=};')
        # color = 'red'
        color = _get_state_color(record.gizmo_state)
        # record.state = c(record.status, f'█{record.status}')

        # record.gizmo_state = f'<span style="width:20px;height:20px;background:{color};border-radius:10px">●</span>' █
        record.gizmo_name = f'[{html.escape(record.gizmo_name)}]' if record.gizmo_name else ''
        record.gizmo_state = f'<span style="color:{color};">●</span>'
        record.msg = html.escape(record.msg)
        fmt = info_formatter if record.levelno==logging.INFO else formatter

        return fmt.format(record)

    def emit(self, record):
        if record.gizmo_state is None:
            self.log_feed.clear()
            return

        try:
            msg = self.format(record)
            # print(f'{record}; {record.args}:\n  {msg}')
            # print(msg)
            self.log_feed.append(pn.pane.HTML(msg))
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

class PanelAdapter(logging.LoggerAdapter):
    def info(self, msg, *args, gizmo_name, gizmo_state):
        super().info(msg, *args, extra={'gizmo_name': gizmo_name, 'gizmo_state': gizmo_state})

    def exception(self, msg, *args, gizmo_name, gizmo_state):
        super().exception(msg, *args, extra={'gizmo_name': gizmo_name, 'gizmo_state': gizmo_state})

    def process(self, msg, kwargs):
        # print(f'ADAPTER {msg=} {kwargs=} {self.extra=}')
        if 'gizmo_status' not in kwargs['extra']:
            kwargs['extra']['gizmo_status'] = '?'
        if 'gizmo_name' not in kwargs['extra']:
            kwargs['extra']['gizmo_name'] = 'g'

        return msg, kwargs

def getPanelLogger(log_feed):
    logger = logging.getLogger('gizmo.panel')
    logger.setLevel(logging.INFO)

    ph = PanelHandler(log_feed)
    ph.log_feed = log_feed
    ph.setLevel(logging.INFO)

    logger.addHandler(ph)

    adapter = PanelAdapter(logger, {})

    return adapter
