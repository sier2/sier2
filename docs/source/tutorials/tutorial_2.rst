Tutorial part 2 - an application
================================

In this tutorial, we'll continue building a simple application to translate text.

Previously, we built a ``UserInput`` block and a ``Translate`` block.
This time, we'll make the ``Translate`` block a little more complicated,
and add an output block to the dag.

(The ``Translate`` dag won't actually translate anything. Instead, we'll
just mangle the words to look different: we'll shuffle the letters in each word.
If ``flag`` is ``True``, we'll also capitalise each word().)

We'll also create a ``Display`` block. Like the ``UserInput`` block,
``Display`` doesn't actually do anything - it just provides the application
a way of getting the result of the translation. The application could just
get the translation from the output param of the ``Translate`` block as it did
in the previous tutorial, but we want to keep "user input" and "user output"
blocks separate from "work" blocks. This will become useful in the next tutorial.

Now we can build our new dag, run it, and see the result.

The output (which may vary because of the randomness) is:

.. code-block:: text

    Input text:
    Hello world.

    Output text:
    Lhoel .lorwd

.. note::

    To see this dag in action, run ``tutorials/tutorial_2a.py``.
