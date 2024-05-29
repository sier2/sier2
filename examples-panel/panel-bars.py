import holoviews as hv
import panel as pn
from panel.viewable import Viewer
import random
import pandas as pd

from gizmo import Gizmo, DagManager
import param

hv.extension('bokeh', inline=True)
pn.extension(inline=True)
# hv.renderer('bokeh').theme = 'dark_minimal'

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

class Query(Gizmo):
    """A plain Python gizmo that accepts a "query" (a maximum count value) and outputs a dataframe."""

    df_out = param.DataFrame(default=None)

    def query(self, max_height):
        """Output a dataframe with a maximum counts value."""

        self.df_out = _make_df(max_height)

class QueryWidget(Query):#, Viewer):
    def __panel__(self):
        def query_value(max_height):
            """A function that returns self.df.

            The query() method in the Query widget doesn't return a value,
            but pn.bind() expects a function that does return a value.
            This function just returns the output param.
            (Yes, I could have written Query.query() to return a value,
            but a plain Python gizmo wouldn't do that, so I'm demonstrating that
            it's easy to make it work.)
            """

            self.query(max_height)
            return self.df_out

        height = pn.widgets.FloatSlider(value=10, start=1, end=10, name='Maximum height')
        df2 = pn.bind(query_value, max_height=height)
        df_pane = pn.pane.DataFrame(df2, index=False, sizing_mode='stretch_width')
        text = '''
            This query widget has a slider setting the maximum counts in a randomly generated dataframe.
            When the slider is moved, a new dataframe is generated (displayed to the right),
            with the slider specifying the maximum random count value.

            Two instances of a barchart widget display the counts (one normal, one inverted).
        '''

        return pn.Card(pn.Row(pn.Column(height, text), df_pane), title=self.name)

class BarchartWidget(Gizmo):#, Viewer):
    """A barchart widget.

    This could have been written as separate Gizmo + Viewer classes,
    but since the only thing this does is display a HoloViews Chart, why bother.
    """

    df_in = param.DataFrame(default=None)

    def __init__(self, inverted=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.inverted = inverted

    def execute(self):
        if self.df_in is not None:
            df = self.df_in
            if self.inverted:
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

        return pn.pane.HoloViews(bars, sizing_mode='stretch_width')

    def __panel__(self):
        return pn.Card(pn.panel(self.execute), title=self.name)#, sizing_mode='stretch_width'))

def main():
    title = 'Example GUI'

    template = pn.template.MaterialTemplate(
        title=title,
        theme='dark',
        site='PoC ',
        sidebar=pn.Column('## Gizmos'),
        collapsed_sidebar=True
    )

    q = QueryWidget(name='Run a query')
    b = BarchartWidget(name='Results bars')
    bi = BarchartWidget(inverted=True, name='Results bars (inverted)')

    dag = DagManager()
    dag.connect(q, b, ['df_out:df_in'])
    dag.connect(q, bi, ['df_out:df_in'])

    template.main.objects = [pn.Column(q, b, bi)]
    template.sidebar.objects = [pn.panel(dag.hv_graph().opts(invert_yaxis=True, xaxis=None, yaxis=None))]
    template.show(threaded=False)

if __name__=='__main__':
    main()
