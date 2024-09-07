Tutorial part 9 - dumping a dag
===============================

In this tutorial, we find out how to dump a dag to a file,
and run the app from that file.

We now have a fully functioning app, using blocks from the library,
which in turn has found them in their pip installed package.

We'll reuse the code from ``tutorial_5b.py``, but instead of showing the dag,
we do this.

.. code:: python

    dumped_dag = dag.dump()

    import json
    from pathlib import Path
    import tempfile

    p = Path(tempfile.gettempdir()) / 'translate.dag'
    print(f'Saving dag to {p} ...')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(dumped_dag, f, indent=2)

This dumps the dag to a data structure (which happens to be JSON),
then saves that structure to a file.

.. note::

    To see this dag in action, run ``tutorials/tutorial_6a.py``.

When run, the script prints the path of the file containing the saved dag.

Now we can run the application using the saved dag. Substitute the path of
the saved dag.

.. code:: bash

    python -m sier2 panel <saved file>

The application should be displayed in your browser.
