Tutorial part 1 - Dag
=====================

In this tutorial, we'll start to build a simple application to translate text.
(By "translate", we mean "transform the text" - we won't need any external help.)

A "dag" is a `directed acyclic graph <https://en.wikipedia.org/wiki/Directed_acyclic_graph>`_. Each connection in the graph has a direction,
so in the graph below, node ``a`` is connected to node ``b``,
but node ``b`` is not connected to node ``a``. In addition, starting at
any given node and following connections will never lead back to that node.

.. image:: Tred-G.svg.png
    :align: center

In particular, we build a graph by connecting blocks. More precisely,
blocks are connected by connecting output params to input params.
Rather than invent a name, we call a dag made up of connected blocks
a "dag".

The dag will contain two blocks.

* A user input block;
* A translation block;

We suggest that you create a new Python script file and follow along,
so you can see how blocks work, and how changes affect the dag.
If things go wrong, copies of the tutorial scripts are in the ``tutorials``
directory.

As we saw in the previous tutorial, a block is an instance of a class that
subclasses ``Block``, and uses at least one ``param`` for input and/or output.

First we'll look at the ``UserInput`` class. There are two parameters,
defined using the ``param`` library. How do we know which are inputs and
which are outputs? Inputs start with ``in_``, outputs start with ``out_``.

``UserInput`` has no inputs, and two outputs: a text parameter
containing text to be translated, and a flag that changes the form of the
translation.

(Below we'll set the values of the outputs manually from Python.
In later tutorials, we'll see how to accept user input via a GUI.)

Notice is that a ``Block`` class does not ask for user input.
This is because blocks do not take input or produce
output; it is up to the application using a block to get input from, and present
output to, users. The only input and output mechanism that blocks use is their
parameters.

The ``Translate`` class has two input params (that correspond to ``UserInput``s
output params) and an output param. It also has an ```execute()`` method.
This method is called automatically by the dag after the input values have been set.
(For convenience, ``execute()`` prints its input params so we can see what the input
param values are.)

The ``main()`` function creates two block instances, then creates a ``Dag`` and
connects the two blocks. After creating each block, we create a dag, then use the
dag to connect the two blocks. The ``connect()`` method connects the source block
``ui`` to the destination block  ``tr``. The ``Connection()`` arguments indicate
how the blocks are connected.

* ``out_text`` (in the ``ui`` block) is connected to ``in_text`` (in the ``tr`` block)
* ``out_flag`` (in the ``ui`` block) is connected to ``in_flag`` (in the ``tr`` block)

Now we can try running the dag. To do this, we assign values to
the output params of ``ui``,and call ``dag.execute()``. Finally, we print
the output param of ``tr``.

The output resulting from this dag is:

.. code-block:: text

    in execute: self.in_flag=True self.in_text='Hello world.'
    tr.out_text='[HELLO WORLD.]'

.. note::

    To see this dag in action, run ``tutorials/tutorial_1a.py``.
