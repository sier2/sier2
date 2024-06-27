Gizmos
======

Connect modular pieces of Python code ("gizmos") into
a processing pipeline that forms a directed acyclic graph.

Description
-----------

A gizmo is a self-contained piece of code with input and output parameters.
Gizmos can be connected to each other using a ``Dag`` to create
a dag of gizmos.

More precisely, output parameters in one gizmo can be connected to input parameters
in another gizmo. The connections need not be one-to-one: parameters in multiple gizmos
can be connected to parameters in a single gizmo; conversely, parameters in a single gizmo
can be connected to parameters in multiple gizmos.

Gizmo parameters use `param <https://param.holoviz.org/>`_, which not only implements
triggering and watching of events, but allows parameters to be named and documented.

Simple Gizmo implementations look like this.

.. code-block:: python

    from gizmo import Gizmo, Dag, Connection
    import param

    class Assign(Gizmo):
        initial = param.Integer(label='Initial value')

    class Increment(Gizmo):
        """A gizmo that adds one to the input value."""

        initial = param.Integer(label='The input', doc='An integer')
        int_out = param.Integer(label='The output', doc='The incremented value')

        def execute(self):
            self.int_out = self.initial + 1

    class Display(Gizmo):
        result = param.Integer(label='Result', doc='to be displayed')

        def execute(self):
            print(f'Result is {self.result}.')

The ``execute()`` method in each Gizmo is called automatically when an input parameter is assigned a value.

Creating a dag
--------------

A dag is created using an instance of :class:`gizmo.Dag`.

.. code-block:: python

    dag = Dag(doc='Increment and display')

The dag is used to connect gizmo instances using the
:func:`gizmo.Dag.connect` method.

.. code-block:: python

    assign = Assign()
    incr = Increment()
    disp = Display()
    dag.connect(assign, incr, Connection('initial'))
    dag.connect(incr, disp, Connection('int_out', 'result'))

This creates instances of the ``Assign``,  ``Increment``, and ``Display`` gizmos,
and connects them.

A ``Connection`` specifies a pair of output and input parameters.
Because the output parameter of ``Assign`` and the input parameter of
``Increment`` have the same name, the parameter name only needs to be
specified once. The output parameter of ``Increment`` and the input parameter
of ``Display`` have different names, so each name must be specified.

After creating the connections, gizmo ``incr`` is watching parameter
``assign.initial`` and gizmo ``disp`` is watching parameter ``incr.int_out``.

When a value is assigned to ``assign.initial``, ``incr.initial``
is set to that value and ``incr.execute()`` is called.
Likewise, when a value is assigned to gizmo ``incr.in_out``, ``disp.result``
is set to that value and ``disp.execute()`` is called.

To run the dag, assign a value to ``assign.initial``.

.. code-block:: python

    assign.initial = 1

The result is:

.. code-block:: text

    Result is 2.

Examples
--------

See the ``examples`` directory in the source code for examples.

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    tutorial_1
    tutorial_2
    tutorial_3
    tutorial_4
    gizmo
    dag
    library

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
