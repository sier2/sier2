Tutorial - Part 3
=================

In this tutorial, we'll build on the dag we build previously do provide
a GUI interface. We'll be using ``panel``, an open-source Python library
designed to streamline the development of robust tools, dashboards,
and complex applications entirely within Python.

As a reminder, here is the ``UserInput`` gizmo.

.. code-block:: python

    from gizmo import Gizmo, Dag, Connection
    import param

    class UserInput(Gizmo):
        """A gizmo that provides user input."""

        # Outputs.
        #
        text = param.String(label='User input', doc='Text to be translated')
        flag = param.Boolean(label='Transform flag', doc='Changes how text is translated')

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

        text = param.String(label='User input', doc='Text to be translated')
        flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')

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
                # print(f'{text_in_widget.value=}, {flag_widget.value=}')
                self.param.update(
                    text=text_in_widget.value,
                    flag=flag_widget.value
                )

            button = pn.widgets.Button(name='Translate', button_type='primary', align='end')
            pn.bind(on_button, button, watch=True)

            return pn.Column(
                text_in_widget,
                pn.Row(flag_widget, button, align='end')
            )

The ``__panel__()`` method creates a text area, a checkbox, and a button.
When the button is clicked, the output params are updated.

It is easy to test this panel. In the directory above the ``tutorials``
directory, run python to get a REPL prompt.

.. code-block:: python

    >>> import tutorials.tutorial_3a as t3a
    >>> t3a.UserInput().__panel__().show()

This instantiates the ``UserInput`` gizmo, calls the ``__panel__()``
method to get a panel component, and calls ``show()``. The input component
is displayed in your browser.

If you'd like to check that the ``on_button()`` method is being called,
uncomment the ``print()`` line.

After adding ``__panel__()`` methods to the other gizmos, we can
test our dag.

.. code-block:: python

    if __name__=='__main__':
        ui = UserInput()
        tr = Translate()
        di = Display()

        dag = Dag(doc='Translation')
        dag.connect(ui, tr, Connection('text', 'text_in'), Connection('flag'))
        dag.connect(tr, di, Connection('text_out', 'text'))

        pn.Column(ui, tr, di).show()

As before, we create instances of our gizmos and build a dag.
This time, we create a ``pn.Column()`` containing the gizmos and
``show()`` it.

.. note::

    To see this dag in action, run ``tutorials/tutorial_3b.py``.
