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

Block input and output parameters use `param <https://param.holoviz.org/>`_,
which not only implements watching of parameter value changes,
but also allows parameters to be named and documented.

Simple Block implementations look like this.

.. code-block:: python

    from sier2 import Block, Dag
    from sier2.panel import PanelDag
    import param

    class Assign(Block):
        """Assign an initial value from the caller / user."""

        in_value = param.Integer(label='Initial value in')
        out_value = param.Integer(label='Initial value out')

        wait_for_input = True

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

The :func:`~sier2.Block.execute` method in each block is called automatically when an input parameter is assigned a value.

Creating a dag
--------------

A dag is created using by passing a list of param connections to :class:`sier2.Dag`.
Create the blocks, then create the dag by specifying connections between params.

.. code-block:: python

    assign = Assign()
    incr = Increment()
    disp = Display()
    dag = Dag([
            (assign.param.out_value, incr.param.in_val),
            (incr.param.out_val, disp.param.in_result)
        ],
        doc='Increment and display',
        title='Increment example'
    )

This creates instances of the ``Assign``,  ``Increment``, and ``Display`` blocks,
and connects them.

After creating the connections, the dag is watching the output parameters.
Whenever an output parameter's value changes, the dag looks up the block that
the connection goes to, and adds that block to an execution queue.
After one block finishes executing, the next block on the execution queue is
selected, it's input values are set, and the block is executed.

To run the dag, call ``dag.execute()``. ``Assign`` is an input block, so execution
will pause before calling ``execute()``, to allow the caller to assign a value
to``in_value``. The dag can then be restarted at ``assign.execute()``.

.. code-block:: python

    b = dag.execute()
    assign.in_value = int(input('Enter an initial integer value: '))
    dag.execute_after_input(b)

The result (after entering "1") is:

.. code-block:: text

    Result is 2.

The dag script is very easily modified to become a GUI app: just replace
``Dag`` with ``PanelDag``, then call ``dag.show()``.

.. code-block:: python

    # dag = Dag([
    #         (assign.param.out_value, incr.param.in_val),
    #         (incr.param.out_val, disp.param.in_result)
    #     ],
    #     doc='Increment and display',
    #     title='Increment example'
    # )
    dag = Dag([
            (assign.param.out_value, incr.param.in_val),
            (incr.param.out_val, disp.param.in_result)
        ],
        doc='Increment and display',
        title='Increment example'
    )

    ...

    # b = dag.execute()
    # assign.in_value = int(input('Enter an initial integer value: '))
    # dag.execute_after_input(b)
    dag.show()

The dag app is now displayed in a web browser using `Panel <https://panel.holoviz.org/>`_,
with the input params mapped to suitable Panel widgets. The blocks work as-is - only the
code above needed to be modified.

The ``sier2-tutorial`` repository at `https://github.com/sier2/sier2-tutorial <https://github.com/sier2/sier2-tutorial>`_ contains a tutorial and many examples.

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
