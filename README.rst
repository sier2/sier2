Sier2
======

Connect modular pieces of Python code ("blocks") into
a processing dag pipeline. Blocks are an improvement on libraries;
if you have a library, you still need to build an application.
Blocks are pieces of an application, you just have to connect them.

See the ``examples`` directory in the ``sier2-tutorial`` repository for examples.

Description
-----------

A ``block`` is a self-contained piece of code with input and output parameters.
Blocks can be connected to each other using a ``Dag`` to create
a dag of blocks.

More precisely, output parameters in one block can be connected to input parameters
in another block. The connections need not be one-to-one: parameters in multiple blocks
can be connected to parameters in a single block; conversely, parameters in a single block
can be connected to parameters in multiple blocks.

Block parameters use `param <https://param.holoviz.org/>`_, which not only implement
triggering and watching of events, but allow parameters to be named and documented.

A typical block implementation looks like this.

.. code-block:: python

    from sier2 import Block

    class Increment(Block):
        """A block that adds one to the input value."""

        in_int = param.Integer(label='The input', doc='An integer')
        out_int = param.Integer(label='The output', doc='The incremented value')

        def execute(self):
            self.out_int = self.in_int + 1

See the examples in ``examples`` (Python scripts) and ``examples-panel`` (scripts that use `Panel <https://panel.holoviz.org/>`_ as a UI).

Documentation
-------------

To build the documentation from the repository root directory:

.. code-block:: powershell

    docs/make html
