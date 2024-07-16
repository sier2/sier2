Tutorial part 4 - themed application
====================================

In this tutorial, we'll use the dag we built previously to create a themed
gizmo application.

We'll reuse the gizmos by importing them from the previous tutorial.
Then, as before, we'll build a dag.

This time, we'll use the :func:`gizmo.panel.show_dag` method to display the dag.
``show_dag`` first extracts the gizmos from the dag in sorted order (see below);
each gizmo is wrapped in a ``panel`` ``Card``, and the cards are displayed in
a column. All of this is displayed in a ``panel`` template.

* The card titles display the gizmo names anda status indicator.
* The sidebar displays a visualisation of the dag, and a stop / unstop switch.

What does "sorted order" mean? A dag is a directed acyclic graph: a graph
where the edges between nodes have directions, and there are no cycles
(aka loops). A consequence of this is that a dag has at least one "start"
gizmo (a gizmo with no inputs) and at least one "end" gizmo (a gizmo with
no outputs). The gizmos are displayed in *topological* sort order: gizmos
closer to the start are above gizmos further from the start.

We also have to find a way to execute the dag. We do this by telling the dag
the the ``UserInput`` gizmo requires user input: when input is complete, the dag
can be executed. Specifically, we pass ``user_input=True`` when creating the gizmo.
This adds a ``Continue`` button to this gizmo's card - pressing the button
calls ``dag.execute()``.

.. code-block:: python

    from gizmo import Dag, Connection
    from gizmo.panel import show_dag

    from tutorial_3b import UserInput, Translate, Display

    ui = UserInput(name='User input', user_input=True)
    tr = Translate(name='Translation')
    di = Display(name='Display output')

    dag = Dag(doc='Translation')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
    dag.connect(tr, di, Connection('out_text', 'in_text'))

    show_dag(dag, site='Translation dag', title='translate text')

.. note::

    To see this dag in action, cd into the ``tutorials`` directory and run ``tutorials/tutorial_4a.py``.

An obvious disadvantage of importing gizmo classes from another module is
that we have to be in the correct directory in order for the imports to work.
