Tutorial part 6 - dag library
=============================

In this tutorial, we find out how to use the dag library to
run a pre-defined dag.

In the previous tutorial, we installed the ``sier2-examples`` package,
which defined some blocks we used in our dag. The package also contains
a pre-defined dag, which we can run directly without writing any Python code.

To see the dags that the dag library knows about, run the command below.

.. code:: bash

    python -m sier2 dags

The output should be similar to:

.. code:: text

    In sier2_examples v0.13.3
    sier2_examples.dag_library.translate_dag: Translation app

To run the dag, we use the ``sier2`` ``run`` command, specifying the
name of the dag. We can just use the last part of the dag name; we only
need to use the full name if another library defines a dag called
``translate_dag``.

.. code:: bash

    python -m sier2 run translate_dag
