# Debugging flags.
#
from enum import Flag, auto


class Debug(Flag):
    DAG_QUEUE = auto()  # Print the dag block queue.
    BLOCK_PARAMS = auto()  # Print the in_ params before executing a block.
