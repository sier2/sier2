Tutorial part 5 - block library
==================================

In this tutorial, we find out how to use the block library.

In the previous tutorial, we saw that because we imported another module,
we had to be in the correct directory. This tutorial will show how to use
plugins and the block library to run a dag from anywhere.

First, let's see how the library works.

We import the block classes as before, but this time we add the classes
to the block library. Each block class has a unique key. This could be
anything - a UUID, a random string - but for ease of recognition,
we use ``module_name.class_name``.

The main part of the code is the same as the previous tutorial, except
instead of using the classes directly, we get them from the library using
``Library,get()`` and their unique keys.

.. note::

    To see this dag in action, cd into the ``tutorials`` directory and run ``tutorials/tutorial_5a.py``.

If there was a mechanism that pre-loaded blocks into the library,
we wouldn't need to import them - we could just get them from the library
and use them.

Before proceeding, change to the ``examples-library`` directory and
run the command below.

.. code:: bash

    python -m pip install --user .

This will install a package called ``sier2-examples``. The blocks in the
package are accessible by the block library. To see this, after installing
the package, run the command below.

.. code:: bash

    python -m sier2 blocks

The output should be similar to:

.. code:: text

    In sier2_examples v0.13.3
      sier2_examples.tutorial_3b.UserInput: A text area and flag for input.
      sier2_examples.tutorial_3b.Translate: Translate text to English.
      sier2_examples.tutorial_3b.Display: Display translated text.

Now we can use the blocks in the ``sier2-examples`` library without importing them,
and without having to be in any specific directory.

.. note::

    To see this dag in action, run ``tutorials/tutorial_5b.py``.
