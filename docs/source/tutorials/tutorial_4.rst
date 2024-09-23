Tutorial part 4 - themed application
====================================

In this tutorial, we'll use the blocks we built in the previous tutorial
to create a themed block application. We'll import them and build a dag.

This time, we'll use the :class:`sier2.panel.PanelDag` class to display the dag.
A ``PanelDag`` is just like a normal "text-only" ``Dag``, but it adds the
necessary plumbing to provide a graphical user interface using the ``panel``
library.

``PanelDag`` first extracts the blocks from the dag in sorted order (see below);
each block is wrapped in a ``panel`` ``Card``, and the cards are displayed in
a column. All of this is displayed in a ``panel`` template.

* The card titles display the block names and a status indicator.
* The sidebar displays a visualisation of the dag, and a stop / unstop switch.

What does "sorted order" mean? A dag is a directed acyclic graph: a graph
where the edges between nodes have directions, and there are no cycles
(aka loops). A consequence of this is that a dag has at least one "start"
block (a block with no inputs) and at least one "end" block (a block with
no outputs). The blocks are displayed in *topological* sort order: blocks
closer to the start are shown above blocks further from the start.

We also have to find a way to execute the dag. We do this by telling the dag
the the ``UserInput`` block requires user input: when input is complete, the dag
can be executed. Specifically, we pass ``user_input=True`` when creating the block.
This adds a ``Continue`` button to this block's card - pressing the button
calls ``dag.execute()``.

.. note::

    To see this dag in action, cd into the ``tutorials`` directory and run ``tutorials/tutorial_4a.py``.

An obvious disadvantage of importing block classes from another module is
that we have to be in the correct directory in order for the imports to work.
