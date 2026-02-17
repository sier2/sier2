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
        """Assign an initial value."""

        in_value = param.Integer(label='Initial value in')
        out_value = param.Integer(label='Initial value out')

        def execute(self):
            self.out_value = self.in_value

    class Increment(Block):
        """A block that adds one to the input value."""

        in_val = param.Integer(label='The input', doc='An integer')
        out_val = param.Integer(label='The output', doc='The incremented value')

        def execute(self):
            self.out_val = self.in_val + 1

    class Display(Block):
        """Display the result."""

        in_result = param.Integer(label='Result', doc='to be displayed')

        def execute(self):
            print(f'Result is {self.in_result}.')

The ``execute()`` method in each block is called automatically when an input parameter is assigned a value.

Creating a dag
--------------

A dag is created using an instance of :class:`sier2.Dag`.

.. code-block:: python

    dag = Dag(doc='Increment and display', title='Example')

The dag is used to connect block instances using the
:func:`sier2.Dag.connect` method.

.. code-block:: python

    assign = Assign()
    incr = Increment()
    disp = Display()
    dag.connect(assign, incr, Connection('out_value', 'in_val'))
    dag.connect(incr, disp, Connection('out_val', 'in_result'))

This creates instances of the ``Assign``,  ``Increment``, and ``Display`` blocks,
and connects them. A ``Connection`` specifies a pair of output (from the first block)
and input (to the second block) parameters.

After creating the connections, the dag is watching the output parameters.
Whenever an output parameter's value changes, the dag looks up the block that
the connection goes to, and adds that block to an execution queue.
After one block finishes executing, the next block on the execution queue is
selected, it's input values are set, and the block is executed.

To run the dag, assign a value to ``assign.in_value`` and call ``dag.execute()``.

.. code-block:: python

    assign.in_value = 1
    dag.execute()

The result is:

.. code-block:: text

    Result is 2.

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    block
    dag
    library
    config
    logging
    util

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
