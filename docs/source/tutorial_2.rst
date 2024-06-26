Tutorial - Part 2
=================

In this tutorial, we'll continue building a simple dag to translate text.

Previously, we built a ``UserInput`` gizmo and a ``Translate`` gizmo,
but the ``Translate`` gizmo just printed its params. This time, we'll complete
the translation dag.

The ``Translate`` dag won't actually translate anything. Instead, we'll
just mangle the words to look different: we'll shuffle the letters in each word.
If ``flag`` is ``True``, we'll also capitalise each word().

.. code-block:: python

    import random
    import re

    class Translate(Gizmo):
        """A gizmo that transforms text.

        The text is split into paragraphs, then each word has its letters shuffled.
        If flag is set, capitlaize each word.
        """

        text_in = param.String(label='Input text', doc='Text to be transformed')
        flag = param.Boolean(label='Transform flag', doc='Changes how text is transformed')
        text_out = param.String(label='Output text', doc='Transformed text')

        def execute(self):
            paras = re.split(r'\n{2,}', self.text_in)
            para_words = [para.split() for para in paras]
            para_words = [[''.join(random.sample(word, k=len(word))) for word in para] for para in para_words]

            if self.flag:
                para_words = [[word.capitalize() for word in para] for para in para_words]

            text = '\n\n'.join(' '.join(word for word in para) for para in para_words)

            self.text_out = text

After all the transforming in ``execute()``, the last thing that happens is
assigning the transformed text to ``self.text_out``.

We'll also create a ``Display`` gizmo. Like the ``UserInput`` gizmo,
``Display`` doesn't actually do anything - it just provides the application
a way of getting the result of the translation. (The application could just
get the translation from the output param of the ``Translate`` gizmo, but
we want to keep "user input" and "user output" gizmos separate from "work" gizmos.)

.. code-block:: python

    class Display(Gizmo):
        """A gizmo that displays text."""

        text = param.String(label='Text', doc='Display text')

Now we can build our new dag, run it, and see the result.

.. code-block:: python

    ui = UserInput()
    tr = Translate()
    di = Display()

    dag = Dag(doc='Translation')
    dag.connect(ui, tr, Connection('text', 'text_in'), Connection('flag'))
    dag.connect(tr, di, Connection('text_out', 'text'))

    user_text = 'Hello world.'
    print('Input text:')
    print(user_text)
    print()

    ui.param.update(
        text=user_text,
        flag=True
    )

    print('Output text:')
    print(di.text)
    print()

.. note::

    To see this dag in action, run ``tutorials/tutorial_2a.py``.

The output (which may vary because of the randomness) is:

.. code-block:: text

    Input text:
    Hello world.

    Output text:
    Lhoel .lorwd
