Tutorial part 5 - gizmo library
==================================

In this tutorial, we find out how to use the gizmo library.

In the previous tutorial, we saw that because we imported another module,
we had to be in the correct directory. This tutorial will show how to use
plugins and the gizmo library to run a dag from anywhere.

First, let's see how the library works.

.. code:: python

    from gizmo import Dag, Connection, Library
    from gizmo.panel import show_dag

    from tutorial_3b import UserInput, Translate, Display

    Library.add(UserInput, 'tutorial_3b.UserInput')
    Library.add(Translate, 'tutorial_3b.Translate')
    Library.add(Display, 'tutorial_3b.Display')

We import the gizmo classes as before, but this time we add the classes
to the gizmo library. Each gizmo class has a unique key. This could be
anything - a UUID, a random string - but for ease of recognition,
we use ``module_name.class_name``.

The main part of the code is the same as the previous tutorial, except
instead of using the classes directly, we get them from the library using
their unique keys.

.. code:: python

    if __name__=='__main__':
        UiGizmo = Library.get('tutorial_3b.UserInput')
        ui = UiGizmo(name='User input', user_input=True)

        TrGizmo = Library.get('tutorial_3b.Translate')
        tr = TrGizmo(name='Translation')

        DiGizmo = Library.get('tutorial_3b.Display')
        di = DiGizmo(name='Display output')

        dag = Dag(doc='Translation', site='Translation dag', title='translate text')
        dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
        dag.connect(tr, di, Connection('out_text', 'in_text'))

        show_dag(dag)

.. note::

    To see this dag in action, cd into the ``tutorials`` directory and run ``tutorials/tutorial_5a.py``.

If there was a mechanism that pre-loaded gizmos into the library,
we wouldn't need to import them - we could just get them from the library
and use them.

Before proceeding, change to the ``examples-library`` directory and
run the command below.

.. code:: bash

    python -m pip install --user -e .

This will install a package called ``gizmo-examples``. The gizmos in the
package are accessible by the gizmo library. To see this, after installing
the package, run the command below.

.. code:: bash

    python -m gizmo plugins

The output should be similar to:

.. code:: text

    In gizmo_examples 0.0.1:
      gizmo_examples.tutorial_3b.UserInput
      gizmo_examples.tutorial_3b.Translate
      gizmo_examples.tutorial_3b.Display

Now we can use the gizmos without importing them, and without having to be
in any specific directory.

.. code:: python

    from gizmo import Dag, Connection, Library
    from gizmo.panel import show_dag

    print('Loading ui ...')
    UiGizmo = Library.get('gizmo_examples.tutorial_3b.UserInput')
    ui = UiGizmo(name='User input', user_input=True)

    print('Loading translator ...')
    TrGizmo = Library.get('gizmo_examples.tutorial_3b.Translate')
    tr = TrGizmo(name='Translation')

    print('Loading display ...')
    DiGizmo = Library.get('gizmo_examples.tutorial_3b.Display')
    di = DiGizmo(name='Display output')

    dag = Dag(doc='Translation', site='Translation dag', title='translate text')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
    dag.connect(tr, di, Connection('out_text', 'in_text'))

    show_dag(dag)

.. note::

    To see this dag in action, run ``tutorials/tutorial_5b.py``.
