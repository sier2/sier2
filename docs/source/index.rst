Sier2
=====

Connect modular pieces of Python code ("blocks") into
a processing pipeline that forms a directed acyclic graph.

Description
-----------

A block is a self-contained piece of code with input and output parameters.
Blocks can be connected to each other using a ``Dag`` to create
a dag of blocks. Unlike a library, where you must write an application
to use it, blocks are pieces of an application - you just have to connect them.

More precisely, output parameters in one block can be connected to input parameters
in another block. The connections need not be one-to-one: parameters in multiple
blocks can be connected to parameters in a single block; conversely, parameters
in a single block can be connected to parameters in multiple blocks.

Block parameters use `param <https://param.holoviz.org/>`_, which not only implements
triggering and watching of events, but allows parameters to be named and documented.

Simple Block implementations look like this.

.. code-block:: python

    from sier2 import Block, Dag, Connection
    import param

    class Assign(Block):
        initial = param.Integer(label='Initial value')

    class Increment(Block):
        """A block that adds one to the input value."""

        initial = param.Integer(label='The input', doc='An integer')
        int_out = param.Integer(label='The output', doc='The incremented value')

        def execute(self):
            self.int_out = self.initial + 1

    class Display(Block):
        result = param.Integer(label='Result', doc='to be displayed')

        def execute(self):
            print(f'Result is {self.result}.')

The ``execute()`` method in each block is called automatically when an input parameter is assigned a value.

Creating a dag
--------------

A dag is created using an instance of :class:`sier2.Dag`.

.. code-block:: python

    dag = Dag(doc='Increment and display')

The dag is used to connect block instances using the
:func:`sier2.Dag.connect` method.

.. code-block:: python

    assign = Assign()
    incr = Increment()
    disp = Display()
    dag.connect(assign, incr, Connection('initial'))
    dag.connect(incr, disp, Connection('int_out', 'result'))

This creates instances of the ``Assign``,  ``Increment``, and ``Display`` blocks,
and connects them.

A ``Connection`` specifies a pair of output and input parameters.
Because the output parameter of ``Assign`` and the input parameter of
``Increment`` have the same name, the parameter name only needs to be
specified once. The output parameter of ``Increment`` and the input parameter
of ``Display`` have different names, so each name must be specified.

After creating the connections, block ``incr`` is watching parameter
``assign.initial`` and block ``disp`` is watching parameter ``incr.int_out``.

When a value is assigned to ``assign.initial``, ``incr.initial``
is set to that value and ``incr.execute()`` is called.
Likewise, when a value is assigned to block ``incr.in_out``, ``disp.result``
is set to that value and ``disp.execute()`` is called.

To run the dag, assign a value to ``assign.initial``.

.. code-block:: python

    assign.initial = 1

The result is:

.. code-block:: text

    Result is 2.

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    block
    dag
    library
    logging
    util

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
