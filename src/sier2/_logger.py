import logging

_BLOCK_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s [%(block_name)s] %(message)s', datefmt='%H:%M:%S')
# formatter = logging.Formatter('%(asctime)s %(levelname)s [%(block_name)s] - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# class BlockHandler(logging.StreamHandler):
#     def format(self, record):
#         fmt = info_formatter# if record.levelno==logging.INFO else formatter

#         return fmt.format(record)

class BlockAdapter(logging.LoggerAdapter):
    """An adapter that log messages from blocks.

    Each block has its own adapter, so the log automatically includes the block name.
    """

    def __init__(self, logger, block_name: str, block_state):
        super().__init__(logger)
        self.block_name = block_name
        self.block_state = block_state

    def debug(self, msg, *args):
        super().debug(msg, *args, extra={'block_name': self.block_name, 'block_state': self.block_state})

    def info(self, msg, *args):
        super().info(msg, *args, extra={'block_name': self.block_name, 'block_state': self.block_state})

    def warning(self, msg, *args):
        super().warning(msg, *args, extra={'block_name': self.block_name, 'block_state': self.block_state})

    def error(self, msg, *args):
        super().error(msg, *args, extra={'block_name': self.block_name, 'block_state': self.block_state})

    def exception(self, msg, *args, exc_info=True):
        super().error(msg, *args, exc_info=exc_info, extra={'block_name': self.block_name, 'block_state': self.block_state})

    def critical(self, msg, *args):
        super().critical(msg, *args, extra={'block_name': self.block_name, 'block_state': self.block_state})

    def process(self, msg, kwargs):
        # print(f'BLOCKADAPTER {msg=} {kwargs=} {self.extra=}')
        if 'block_state' not in kwargs['extra']:
            kwargs['extra']['block_state'] = '?'
        if 'block_name' not in kwargs['extra']:
            kwargs['extra']['block_name'] = 'g'

        return msg, kwargs

_logger = logging.getLogger('block.stream')
_logger.setLevel(logging.INFO)

# _ph = BlockHandler()
# _ph.setLevel(logging.DEBUG)

_ph = logging.StreamHandler()
_ph.setFormatter(_BLOCK_FORMATTER)
_ph.setLevel(logging.DEBUG)

_logger.addHandler(_ph)

def get_logger(block_name: str):
    adapter = BlockAdapter(_logger, block_name, None)

    return adapter
