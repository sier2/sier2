Tutorial - Part 4
=================

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

.. code-block:: python

    from gizmo import Dag, Connection
    from gizmo.panel import show_dag

    from tutorial_3b import UserInput, Translate, Display

    if __name__=='__main__':
        ui = UserInput()
        tr = Translate()
        di = Display()

        dag = Dag(doc='Translation')
        dag.connect(ui, tr, Connection('text', 'text_in'), Connection('flag'))
        dag.connect(tr, di, Connection('text_out', 'text'))

        show_dag(dag, site='Translation dag', title='translate text')
