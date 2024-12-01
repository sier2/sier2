Logging
=======

The ``Dag`` class provides a hook to provide logging to an external Python library.

If an installed library provides the entry point ``sier2.logging``,
the specified function will be used to log ``Dag.execute()``
and as a decorator for each call to ``Block.prepare()`` and
``Block.execute()``.

For example, suppose a ``pyproject.toml`` contains:

.. code-block::

    [tool.poetry.plugins."sier2.logging"]
    export = "my_logging:logging_func"

The function ``my_logging.logging_func`` will be used as a decorator.

The logging function is exepcted to be defined as:

.. code-block:: python

    def logging_func(method, *args, **kwargs):
        ...

where ``method`` is the block's ``prepare`` or  ``execute()`` method, and
``*args`` and ``**kwargs`` are the logging parameters.

Dag execute
-----------

The logging function is called with ``method`` set to None and keyword parameters:

* ``sier2_dag_``: the dag being executed

In this case, since the dag is already executing, after any logging,
the logging function can simply return.

Block prepare / execute
-----------------------

The logging function is called with ``method`` set to the
``prepare`` or ``execute`` method of the block about to be executed,
and keyword parameters:

* ``sier2_dag_``: the dag being executed
* ``sier2_block_``: the block about to be executed.

In this case, the logging function must act as a decorator, and call
``method`` with the passed parameters after removing all keyword parameters
of the form ``sier2*_``.

Note that although currently, no other arguments are passed to the
``prepare`` and ``execute`` methods, this not guaranteed to remain so.
