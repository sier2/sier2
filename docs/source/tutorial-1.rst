Tutorial - Part 1
=================

In this tutorial, we'll start to build a simple dag to translate text.
(By "translate", we mean "transform the text" - we won't need any external help.)

The dag will contain three gizmos.

* A user input gizmo;
* A translation gizmo;
* A display gizmo.

We suggest that you create a new Python script file and follow along,
so you can see how gizmos work, and how changes affect the dag.

A gizmo is an instance of a class that subclasses Gizmo, and uses at least
one ``param`` for input and/or output.

.. code-block:: python

    from gizmo import Gizmo, Dag, Connection
    import param

    class UserInput(Gizmo):
        """A gizmo that provides user input."""

        # Outputs.
        #
        text = param.String(label='User input', doc='Text to be translated')
        flag = param.Boolean(label='Transform flag', doc='Changes how text is translated')

This is our first gizmo class. It has no inputs, and two outputs: a text parameter
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
        text_in = param.String(label='Input text', doc='Text to be transformed')
        flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

        # Outputs.
        #
        text_out = param.String(label='Output text', doc='Transformed text')

        def execute(self):
            print(f'{self.flag=} {self.text_in=}')

The inputs for ``Translate`` match the outputs from ``UserInput``.

This gizmo class has an ```execute()`` method. This method is called when a value
is assigned to an input. We'll see this below after we've connected the gizmos.
For now, we just print the inputs.

Now we can create two gizmo instances and connect them.

.. code-block:: python

    ui = UserInput()
    tr = Translate()

    dag = Dag(doc='Translation')
    dag.connect(ui, tr, Connection('text', 'text_in'), Connection('flag'))

After creating each gizmo, we create a dag, then use the dag to connect
the two gizmos. The ``connect()`` method connects the source gizmo ``ui``
to the destination gizmo  ``tr``. The ``Connection()`` arguments indicate
how the gizmos are connected.

* ``ui.text`` is connected to ``tr.text_in``
* ``ui.flag`` is connected to ``tr.flag``

(Note that since the second ``Connection()`` is between two parameters with
the same name, the name only needs to be given once.)

Now we can try running the dag. To do this, we just assign values to
the output params of ``ui``.

.. code-block:: python

    ui.text = 'Hello world.'
    ui.flag = True

This will cause the params in ``tr`` to be updated, and ``tr.execute()`` will
be called.

.. note::

    To see this dag in action, run ``tutorials/tutorial-1a.py``.

The output resulting from this dag is:

.. code-block:: text

    self.flag=False self.text_in='Hello world.'
    self.flag=True self.text_in='Hello world.'

The values are being printed twice, which must mean that ``tr.execute()`` is
being called twice. Why?

When two gizmos are connected, a *watcher* is created for each ``Connection``.
The watchers are in the destination gizmo, watching the specified params
in the source gizmo. When a watched param is assigned a value, the watcher
assigns that value to the corresponding param in the destination gizmo,
and calls ``execute()``.

Because we set ``ui.text`` then ``ui.flag`` separately, the ``ui.text`` watcher
updates ``tr.text_in`` and calls ``tr.execute()``, then the ``ui.flag`` watcher
updates ``tr.flag`` and calls ``tr.execute()``. This not only explains why
the output appears twice, but why ``flag`` is ``False`` the first time, and
``True`` the second time. The first time, ``flag`` has its default value of
``False`` - the second output happens because we set ``flag`` to ``True``.

We can fix this by updating both parameters as a batch.

.. code-block:: python

    ui.param.update(
        text = 'Hello world.',
        flag = True
    )

.. note::

    To see this dag in action, run ``tutorials/tutorial-1b.py``.

Now we only get the single output we expected.

.. code-block:: text

    self.flag=True self.text_in='Hello world.'
