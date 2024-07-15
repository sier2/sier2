Tutorial part 0 - Gizmo
=======================

This is the first in a series of tutorials that explains gizmos and dags,
and how to use them to build applications.

We suggest that you create a new Python script file and follow along,
so you can see how gizmos work.
If things go wrong, copies of the tutorial scripts are in the ``tutorials``
directory.

Gizmos
------

A gizmo is a unit of Python code that performs a specific action:
adding two numbers, querying a database, or displaying data.

Gizmos pass input and output values using a Python library called ``param``
(see `the param web site <https://param.holoviz.org>`_). You don't need to
know the details of how to use params - gizmos take care of the complexity.
Tou just need to know how to declare params as inputs or outputs.

Gizmos are implemented as Python classes. A gizmo must:

* be a subclass of ``Gizmo``;
* have at least one input or output param;
* input param names must start with ``in_``; output param names must start with ``out_``;
* have an optional ``execute()`` method.

Here is a simple gizmo that adds one to its input.

.. code-block:: python

    from gizmo import Gizmo
    import param

    class AddOne(Gizmo):
        """A gizmo that adds one to its input."""

        in_a = param.Integer()
        out_a = param.Integer()

        def execute(self):
            self.out_a = self.in_a + 1

The class ``AddOne`` is a subclass of ``Gizmo``. It has two params:
an input param called ``in_a`` and an output param called ``out_a``.
Both of these params are declared as type integer; we'll see why this matters
below.

The ``execute()`` method defines what the gizmo does. In this case, the output
param (``self.out_a``) is set to the input param plus one (``self.in_a + 1``).

We can test our gizmo by creating an instance of ``AddOne``, setting the
value of the input param, calling ``execute()``, and displaying the value of
the output param.

.. code-block:: python

    a1_gizmo = AddOne()
    a1_gizmo.in_a = 3
    a1_gizmo.execute()
    print(a1_gizmo.out_a)

The output is:

.. code-block:: text

    4

Gizmos provide a short cut that does the same thing.

.. code-block:: python

    print(a1_gizmo(in_a=3))

Calling the gizmo instance with the input params as keyword arguments will
set the inputs, call ``execute()``, and return the result as a dictionary
where the keys are the output param names. The output is:

.. code-block:: text

    {'out_a': 4}

Param types
-----------

An advantage of using ``param`` to define parameters is that they can be
specified with specific types. If you attempt to assign a non-integer value
to an input parameter, ``param`` will raise an error.

.. code-block:: python

    a1_gizmo.in_a = 'x'

.. code-block:: text

    ValueError: Integer parameter 'AddOne.in_a' must be an integer, not <class 'str'>.

See `Parameter types <https://param.holoviz.org/user_guide/Parameter_Types.html>`_
for a list of pre-defined parameter types.
