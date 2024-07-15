Tutorial part 3 - GUI
=====================

In this tutorial, we'll build on the dag we build previously to provide
a GUI interface. We'll be using ``panel``, an open-source Python library
designed to streamline the development of robust tools, dashboards,
and complex applications entirely within Python.

As a reminder, here is the ``UserInput`` gizmo.

.. code-block:: python

    from gizmo import Gizmo, Dag, Connection
    import param

    class UserInput(Gizmo):
        """A gizmo that provides user input."""

        out_text = param.String(label='User input', doc='Text to be translated')
        out_flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

There are a couple of ways of adding a ``panel`` user interface.
One is to subclass ``UserInput`` and add the ``panel`` code in the subclass.
This has the advantage of keeping the functionality and the user interface
separated from each other, and makes unit testing of the functionality simpler.
On the other hand, for the sake of simplicity, we'll just directly add
the ``panel`` code to the gizmo class.

Adding a panel interface is simple: just add a ``__panel__()`` method
that returns a ``panel`` component. We won't explain the ``panel`` code
here, see the `panel web site <https://panel.holoviz.org>`_ for more information.

.. note::

    This gizmo is in ``tutorials/tutorial_3a.py``.

.. code-block:: python

    from gizmo import Gizmo, Dag, Connection
    import param

    import panel as pn
    pn.extension(inline=True)

    class UserInput(Gizmo):
        """A gizmo that provides user input."""

        out_text = param.String(label='User input', doc='Text to be translated')
        out_flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

        def __panel__(self):
            text_in_widget = pn.widgets.TextAreaInput(
                name='Input text',
                placeholder='Enter text here',
                auto_grow=True,
                rows=8,
                max_rows=24,
                resizable='both',
                sizing_mode='stretch_width',
                value='The quick brown\nfox jumps over the lazy\ndog.\n'
            )
            flag_widget = pn.widgets.Checkbox(name='Capitalize', value=False, align='center')

            def on_button(event):
                self.out_text = text_in_widget.value
                self.out_flag = flag_widget.value

            button = pn.widgets.Button(name='Translate', button_type='primary', align='end')
            pn.bind(on_button, button, watch=True)

            return pn.Column(
                text_in_widget,
                pn.Row(flag_widget, button, align='end')
            )

The ``__panel__()`` method creates a text area, a checkbox, and a button.
When the button is clicked, the output params are updated.

We can test this panel by displaying it. In the directory above the ``tutorials``
directory, run python to get a REPL prompt and enter these commands.

.. code-block:: python

    >>> import tutorials.tutorial_3a as t3a
    >>> ui = t3a.UserInput()
    >>> ui
    UserInput(_gizmo_state=<GizmoState.READY: 2>, name='UserInput00882', out_flag=False, out_text='The quick brown\nfox jumps over the lazy\ndog.\n\nThe end.')
    >>> ui.__panel__().show()

This instantiates a ``UserInput`` gizmo and displays its default value,
including the params. It then calls the ``__panel__()``
method to get a panel component, and calls ``show()``. The input component
is displayed in your browser. The ``panel`` library is aware of ``param`` parameters;
we make use of this to create ``panel`` widgets tnat automatically update
their corresponding params.

Change the text and set the flag, then press Ctrl+C to get back to
the Python REPL prompt. Look at the value of ``ui`` again.

.. code-block:: python

    >>> ui
    UserInput(_gizmo_state=<GizmoState.READY: 2>, name='UserInput00882', out_flag=True, out_text='New text.')

Because the panel widgets automatically update the param values, we can see the new values of ``out_text`` and ``out_flag``.

After adding ``__panel__()`` methods to the other gizmos, we can
test our dag.

.. code-block:: python

    if __name__=='__main__':
        ui = UserInput(name='User input')
        tr = Translate(name='Translate')
        di = Display(name='Display output')

        dag = Dag(doc='Translation')
        dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
        dag.connect(tr, di, Connection('out_text', 'in_text'))

        pn.Column(ui, tr, di).show()

As before, we create instances of our gizmos and build a dag.
This time, we create a ``pn.Column()`` containing the gizmos and
``show()`` it.

.. note::

    To see this dag in action, run ``tutorials/tutorial_3b.py``.

However, we have a problem: there's no way to execute the dag.
We can't call ``dag.execute()`` because we're running a panel server.

We'll see how to fix that in the next tutorial.