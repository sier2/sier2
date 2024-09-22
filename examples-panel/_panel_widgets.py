import holoviews as hv
import panel as pn
import pandas as pd
import random

from sier2 import Block#, Dag, Connection
import param

MAX_HEIGHT = 10

def _make_df(max_height=MAX_HEIGHT) -> pd.DataFrame:
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']

    return pd.DataFrame(
        zip(
            colors,
            [random.random()*max_height for _ in range(len(colors))]
        ),
        columns=['Colors', 'Counts']
    )

class Query(Block):
    """A plain Python block that accepts a "query" (a maximum count value) and outputs a dataframe."""

    out_df = param.DataFrame(default=None, doc='A dataframe with columns `Colors` and `Counts`. The counts are a random number between 0 and the slider value.')

    def query(self, max_height):
        """Output a dataframe with a maximum counts value."""

        self.out_df = _make_df(max_height)

class QueryWidget(Query):
    """An example block widget.

    Moving the slider causes `Query.query()` to be called with the value of the slider.
    """

    def __panel__(self):
        def query_value(max_height):
            """A function that returns self.df.

            The query() method in the Query widget doesn't return a value,
            but pn.bind() expects a function that does return a value.
            This function just returns the output param.
            (Yes, I could have written Query.query() to return a value,
            but a plain Python block wouldn't do that, so I'm demonstrating that
            it's easy to make it work.)
            """

            self.query(max_height)
            return self.out_df

        height = pn.widgets.FloatSlider(value=10, start=1, end=10, name='Maximum height')
        df2 = pn.bind(query_value, max_height=height)
        df_pane = pn.pane.DataFrame(df2, index=False, sizing_mode='stretch_width')
        text = '''
            This query widget has a slider setting the maximum counts in a randomly generated dataframe.
            When the slider is moved, a new dataframe is generated (displayed to the right),
            with the slider specifying the maximum random count value.

            Two instances of a barchart widget display the counts (one normal, one inverted).
        '''

        return pn.Row(pn.Column(height, text), df_pane)

class BarchartWidget(Block):#, Viewer):
    """## A barchart widget.

    This could have been written as separate "text-only" `Block` class,
    and a separate subclass implementing `__panel__()`,
    but since the only thing this does is display a HoloViews Chart, why bother.
    """

    in_df = param.DataFrame(default=None, doc='A dataframe with columns `Colors` and `Counts`.')

    def __init__(self, inverted=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.inverted = inverted
        self.hv_pane = pn.pane.HoloViews(sizing_mode='stretch_width')

    def execute(self):
        if self.in_df is not None:
            df = self.in_df
            if self.inverted:
                df = df.copy()
                df['Counts'] = MAX_HEIGHT - df['Counts']

            bars = hv.Bars(df, 'Colors', 'Counts').opts(
                title=f'Inverted={self.inverted}',
                color='Colors',
                ylim=(0, MAX_HEIGHT),
                show_grid=True,
                max_width=600
            )
        else:
            bars = hv.Bars([])

        self.hv_pane.object = bars

    def __panel__(self):
        return self.hv_pane

