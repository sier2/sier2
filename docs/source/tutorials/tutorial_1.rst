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

In particular, we build a graph by connecting gizmos. More precisely,
gizmos are connected by connecting output params to input params.
Rather than invent a name, we call a dag made up of connected gizmos
a "dag".

The dag will contain three gizmos.

* A user input gizmo;
* A translation gizmo;
* A display gizmo.

We suggest that you create a new Python script file and follow along,
so you can see how gizmos work, and how changes affect the dag.
If things go wrong, copies of the tutorial scripts are in the ``tutorials``
directory.

As we saw in the previous tutorial, a gizmo is an instance of a class that
subclasses Gizmo, and uses at least one ``param`` for input and/or output.

.. code-block:: python

    from gizmo import Gizmo, Dag, Connection
    import param

    class UserInput(Gizmo):
        """A gizmo that provides user input."""

        # Outputs.
        #
        out_text = param.String(label='User input', doc='Text to be translated')
        out_flag = param.Boolean(label='Transform flag', doc='Changes how text is translated')

It has no inputs, and two outputs: a text parameter
containing text to be translated, and a flag that changes the form of the
translation.

The first thing to notice is that there are two parameters, defined using the
``param`` library. How do we know which are inputs and which are outputs?
We don't; there is no difference. Input and output params are only distinguished
by the way they are used in the code.

The second thing to notice is that a gizmo class called ``UserInput`` has no way of
asking for user input. This is because gizmos do not take input or produce output;
it is up to the application using a gizmo to get input from, and present output to,
users. The only input and output mechanism that gizmos use is their parameters.

Let's create a translation gizmo class. It won't do anything yet, apart from
display its input params.

.. code-block:: python

    class Translate(Gizmo):
        """A gizmo that transforms text.

        The text is split into paragraphs, then each word has its letters shuffled.
        If flag is set, capitalize each word.
        """

        # Inputs.
        #
        in_text = param.String(label='Input text', doc='Text to be transformed')
        in_flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

        # Outputs.
        #
        out_text = param.String(label='Output text', doc='Transformed text')

        def execute(self):
            print(f'in execute: {self.in_flag=} {self.in_text=}')
            self.out_text = self.in_text

The inputs for ``Translate`` match the outputs from ``UserInput``.

The ``Translate`` gizmo class has an ```execute()`` method. This method is called
autpmatically by the dag after the input value shave been set. We'll see this below
after we've connected the gizmos. For now, we just print the inputs and
set the output parameter.

Now we can create two gizmo instances and connect them.

.. code-block:: python

    ui = UserInput()
    tr = Translate()

    dag = Dag(doc='Translation')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))

After creating each gizmo, we create a dag, then use the dag to connect
the two gizmos. The ``connect()`` method connects the source gizmo ``ui``
to the destination gizmo  ``tr``. The ``Connection()`` arguments indicate
how the gizmos are connected.

* ``ui.out_text`` is connected to ``tr.in_text``
* ``ui.out_flag`` is connected to ``tr.in_flag``

Now we can try running the dag. To do this, we just assign values to
the output params of ``ui``,and call ``dag.execute()``. Finally, we print
the output param of ``tr``.

.. code-block:: python

    ui.out_text = 'Hello world.'
    ui.out_flag = True
    dag.execute()
    print(f'{tr.out_text=}')

.. note::

    To see this dag in action, run ``tutorials/tutorial_1a.py``.

The output resulting from this dag is:

.. code-block:: text

    in execute: self.in_flag=True self.in_text='Hello world.'
    tr.out_text='Hello world.'
