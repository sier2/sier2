# from gizmo import GizmoState
import logging

_GIZMO_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s [%(gizmo_name)s] %(message)s', datefmt='%H:%M:%S')
# formatter = logging.Formatter('%(asctime)s %(levelname)s [%(gizmo_name)s] - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# class GizmoHandler(logging.StreamHandler):
#     def format(self, record):
#         fmt = info_formatter# if record.levelno==logging.INFO else formatter

#         return fmt.format(record)

class GizmoAdapter(logging.LoggerAdapter):
    """An adapter that log messages from gizmos.

    Each gizmo has its own adapter, so the log automatically includes the gizmo name.
    """

    def __init__(self, logger, gizmo_name: str, gizmo_state):
        super().__init__(logger)
        self.gizmo_name = gizmo_name
        self.gizmo_state = gizmo_state

    def debug(self, msg, *args):
        super().debug(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': self.gizmo_state})

    def info(self, msg, *args):
        super().info(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': self.gizmo_state})

    def warning(self, msg, *args):
        super().warning(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': self.gizmo_state})

    def error(self, msg, *args):
        super().error(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': self.gizmo_state})

    def exception(self, msg, *args, exc_info=True):
        super().error(msg, *args, exc_info=exc_info, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': self.gizmo_state})

    def critical(self, msg, *args):
        super().critical(msg, *args, extra={'gizmo_name': self.gizmo_name, 'gizmo_state': self.gizmo_state})

    def process(self, msg, kwargs):
        # print(f'GIZMOADAPTER {msg=} {kwargs=} {self.extra=}')
        if 'gizmo_state' not in kwargs['extra']:
            kwargs['extra']['gizmo_state'] = '?'
        if 'gizmo_name' not in kwargs['extra']:
            kwargs['extra']['gizmo_name'] = 'g'

        return msg, kwargs

_logger = logging.getLogger('gizmo.stream')
_logger.setLevel(logging.INFO)

# _ph = GizmoHandler()
# _ph.setLevel(logging.DEBUG)

_ph = logging.StreamHandler()
_ph.setFormatter(_GIZMO_FORMATTER)
_ph.setLevel(logging.DEBUG)

_logger.addHandler(_ph)

def get_logger(gizmo_name: str):
    adapter = GizmoAdapter(_logger, gizmo_name, None)

    return adapter
