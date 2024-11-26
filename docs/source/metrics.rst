Metrics
=======

The ``Dag`` class provides a hook to provide metrics to an external Python library.

If an installed library provides the entry point ``sier2.metrics``,
the specified function will be used as a decorator for each call
to ``Block.prepare()`` and ``Block.execute()``.

For example, suppose a ``pyproject.toml`` contains:

.. code-block::

    [tool.poetry.plugins."sier2.metrics"]
    export = "my_metrics:metrics_func"

The function ``my_metrics.metrics_func`` will be used as a decorator.
