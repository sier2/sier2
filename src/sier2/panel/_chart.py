# Generate a dag chart.
#

from sier2 import Block, Dag

from bokeh.plotting import figure, show, ColumnDataSource, curdoc, output_notebook
from bokeh.models import HoverTool

from bokeh.resources import INLINE
output_notebook(resources=INLINE)

def bokeh_graph(dag: Dag):
    """Build a Bokeh figure to visualise the block connections."""

    src: list[Block] = []
    dst: list[Block] = []

    def build_layers():
        """Traverse the block pairs and organise them into layers.

        The first layer contains the root (no input) nodes.
        """

        ranks = {}
        remaining = dag._block_pairs[:]

        # Find the root nodes and assign them a layer.
        #
        src[:], dst[:] = zip(*remaining)
        S = list(set([s for s in src if s not in dst]))
        for s in S:
            ranks[s.name] = 0

        n_layers = 1
        while remaining:
            for s, d in remaining:
                if s.name in ranks:
                    # This destination could be from sources at different layers.
                    # Make sure the deepest one is used.
                    #
                    ranks[d.name] = max(ranks.get(d.name, 0), ranks[s.name] + 1)
                    n_layers = max(n_layers, ranks[d.name])

            remaining = [(s,d) for s,d in remaining if d.name not in ranks]

        return n_layers, ranks

    def layout():
        """Arrange the graph nodes."""

        max_width = 0

        # Arrange the graph y by layer from top to bottom.
        # For x, for now we start at 0 and +1 in each layer.
        #
        yx = {y:0 for y in ranks.values()}
        gxy = {}
        for g, y in ranks.items():
            gxy[g] = [yx[y], y]
            yx[y] += 1
            max_width = max(max_width, yx[y])

        # Balance out the x in each layer.
        #
        for y in range(n_layers+1):
            layer = {name: xy for name,xy in gxy.items() if xy[1]==y}
            if len(layer)<max_width:
                for x, (name, xy) in enumerate(layer.items(), 1):
                    gxy[name][0] = x/max_width

        return gxy

    n_layers, ranks = build_layers()

    ly = layout()

    linexs = []
    lineys = []
    for s, d in dag._block_pairs:
        print(s.name, d.name)
        linexs.append((ly[s.name][0], ly[d.name][0]))
        lineys.append((ly[s.name][1], ly[d.name][1]))

    xs, ys = zip(*ly.values())

    c_source = ColumnDataSource({
        'xs': xs,
        'ys': ys,
        'names': list(ly.keys())
    })
    l_source = ColumnDataSource({
        'linexs': linexs,
        'lineys': lineys
    })

    curdoc().theme = 'dark_minimal'
    p = figure(tools='pan,wheel_zoom,box_zoom,reset', height=300, width=300)
    p.axis.visible = False
    p.xgrid.visible = False
    p.ygrid.visible = False
    p.y_range.flipped = True # y-axis goes down instead of up.
    l = p.multi_line(xs='linexs', ys='lineys', source=l_source)
    c = p.circle(x='xs', y='ys', radius=0.05, line_color='black', fill_color='steelblue', hover_fill_color='#7f7f7f', source=c_source)
    p.add_tools(HoverTool(tooltips=[('Block', '@names')], renderers=[c]))

    return p
