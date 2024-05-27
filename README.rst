Gizmos
======

Connect modular pieces of Python code ("gizmos") into
a processing flow pipeline.

See the ``examples`` directory for examples.

Description
-----------

A gizmo is a self-contained piece of code with input and output parameters.
Gizmos can be connected to each other using the ``GizmoManager`` to a create
a "flow".

More precisely, output parameters in one gizmo can be connected to input parameters
in another gizmo. The connections need not be one-to-one: parameters in multiple gizmos
can be connected to parameters in a single gizmo; conversely, parameters in a single gizmo
can be connected to parameters in multiple gizmos.

Gizmo parameters use `param <https://param.holoviz.org/>`, which not only implement
triggering and watching of events, but allow parameters to be named and documented.

A typical Gizmo implementation looks like this.

.. code-block:: python

    class Increment(Gizmo):
        """A gizmo that adds one to the input value."""

        int_in = param.Integer(label='The input', doc='An integer')
        int_out = param.Integer(label='The output', doc='The incremented value')

        def execute(self):
            self.int_out = self.int_in + 1

See the examples in ``examples`` (Python scripts) and ``examples-panel`` (scripts that use Panel as a UI).
