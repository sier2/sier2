Tutorial part 5 - full application
==================================

In this tutorial, we use the gizmo library to run the application for us.

The gizmo library provides a ``panel`` command, which imports the provided
python file, calls ``make_dag()`` to get a dag, and runs the GUI application.

The ``tutorial_5a.py`` module contains only what is needed to create a
gizmo application. The ``panel`` command does everything else.

.. code:: python

    from gizmo import Dag, Connection

    from tutorial_3b import UserInput, Translate, Display

    def make_dag():
        ui = UserInput(name='User input', user_input=True)
        tr = Translate(name='Translation')
        di = Display(name='Display output')

        dag = Dag(doc='Translation', site='Translation dag', title='translate text')
        dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
        dag.connect(tr, di, Connection('out_text', 'in_text'))

        return dag

.. note::

    The tutorial module imports a previous tutorial. Therefore,
    to run the app, you must first ``cd`` into the ``tutorials`` directory.

To run the application:

.. code:: bash

    python -m gizmo panel tutorial_5a.py
