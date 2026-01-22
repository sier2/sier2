from bokeh.plotting import figure, curdoc
from bokeh.core.enums import RenderLevel
from bokeh.models import HoverTool, PanTool, ColumnDataSource

from ._panel_util import _get_state_color

import panel as pn

import math

def _count_param(block, prefix):
    """Count the params starting with a given prefix."""

    return sum(1 for p in block.param if p.startswith(prefix))

class _BokehDag:
    # def __init__(self):
    #     self.doc = curdoc()

    def draw_dag(self, dag, plain=True):
        """Use bokeh to draw a dag.

        Drawing a "traditional" layout is very complex. Instead, we just
        sort the blocks, lay them out in a line, and draw bezier curves
        between blocks reflecting their connections.
        """

        self.dag = dag

        COLOR = 'steelblue'
        COLOR_BG = '#212529'

        topo_blocks = dag.get_sorted()
        states = [block._block_state for block in topo_blocks]
        colors = [_get_state_color(state) for state in states]

        n = len(topo_blocks)

        fig = figure(width=400, height=400, #title=title, #toolbar_location=None,
            toolbar_location=None if plain else 'right',
            aspect_ratio=1,
            # Ranges must be equal to go with aspect_ratio=1.
            x_range=(-1, n), y_range=(-1, n)
        )

        if plain:
            fig.remove_tools(*fig.tools)

        curdoc().theme = 'dark_minimal'
        fig.background_fill_color = COLOR_BG

        hover = HoverTool(tooltips=[('Name', '@name'), ('In', '@icount'), ('Out', '@ocount')])
        fig.add_tools(hover)

        data = {
            'name': [block.name for block in topo_blocks],
            'x': list(range(n)),
            'y': list(range(n-1, -1, -1)),
            'state': colors, #[COLOR for _ in range(n)],
            'icount': [_count_param(block, 'in_') for block in topo_blocks],
            'ocount': [_count_param(block, 'out_') for block in topo_blocks],
        }
        self.cds = ColumnDataSource(data)
        xys = {name: (x,y) for name, x, y in zip(data['name'], data['x'], data['y'])}

        SIZE = 0.25

        circle = fig.circle(
            name=f'circles',
            source=self.cds,
            x='x', y='y',
            radius=SIZE,
            # alpha=0,
            # line_alpha=1,
            color='state',
            # line_color='line_color',
            radius_units='data'
        )

        def next_to_topo(topo_blocks, b1, b2):
            """Are blocks b1 and b2 next to each other in the topological sort?"""

            ix = topo_blocks.index(b1)

            return ix<len(topo_blocks) and topo_blocks[ix+1]==b2

        lw = 2
        side = True
        heads = []
        OFFSET = 1.5 * SIZE
        h = math.sin(math.pi/4) * OFFSET
        for b1, b2 in dag._block_pairs:
            x0, y0 = xys[b1.name]
            x1, y1 = xys[b2.name]
            if next_to_topo(topo_blocks, b1, b2):
                # Draw a line directly from source to destination.
                #
                x0 += h
                y0 -= h
                x1 -= h + h*OFFSET
                y1 += h + h*OFFSET
                angle = -math.pi/12
                fig.line([x0, x1], [y0, y1], line_color=COLOR, line_width=lw)
            else:
                # Define how far out the Bezier curve control points are.
                #
                c = (x1-x0) * 0.75

                if side:
                    # Below.
                    cx0, cy0 = x0, y0-c
                    cx1, cy1 = x1-c, y1
                    x0, y0 = x0, y0 - OFFSET
                    x1, y1 = x1 - OFFSET*1.5, y1
                    angle = -math.pi/2
                else:
                    # Above.
                    cx0, cy0 = x0+c, y0
                    cx1, cy1 = x1, y1+c
                    x0, y0 = x0 + OFFSET, y0
                    x1, y1 = x1, y1 + OFFSET*1.5
                    angle = -math.pi/3

                # # Plot the Bezier control points for debugging.
                # #
                # p.circle([cx0, cx1], [cy0, cy1], radius=0.05, color='red')

                # Draw a background line under the actual line
                # so overlapping curves look nice.
                #
                # fig.bezier([x0], [y0], [x1], [y1], [cx0], [cy0], [cx1], [cy1], line_color=COLOR_BG, line_width=lw+5)
                # fig.bezier([x0], [y0], [x1], [y1], [cx0], [cy0], [cx1], [cy1], line_color=COLOR, line_width=lw)
                fig.bezier([x0, x0], [y0, y0], [x1, x1], [y1, y1], [cx0, cx0], [cy0, cy0], [cx1, cx1], [cy1, cy1], line_color=[COLOR_BG, COLOR], line_width=[lw+5, lw])

            heads.append((x1, y1, angle))
            side = not side

        text = fig.text(source=self.cds, x='x', y='y', text='name', anchor='center', color='white', background_fill_color='black', background_fill_alpha=0.25, alpha=0.5, level=RenderLevel.annotation)

        # Draw the triangles to look like arrowheads.
        #
        xtri, ytri, atri = list(zip(*heads))
        fig.scatter(xtri, ytri, marker='triangle', angle=atri, color=COLOR, size=10)

        hover.renderers = [circle]

        if plain:
            fig.axis.visible = False
            # fig.border_fill_color = 'black'
            # fig.background_fill_color = 'black'
            fig.outline_line_color = None
            fig.grid.grid_line_color = None

        return fig

    def update_(self):
        topo_blocks = self.dag.get_sorted()
        states = [block._block_state for block in topo_blocks]
        colors = [_get_state_color(state) for state in states]

        patch = {
            'state': [(slice(len(topo_blocks)), colors)]
        }
        self.cds.patch(patch)

    def update(self):
        curdoc().add_next_tick_callback(self.update_)

_bokeh_dag = _BokehDag()

def dag_pane(dag, plain=True):
    """Build and return a Bokeh pane containing the dag chart.

    Also sets dag._on_context_exit to be notified of status changes.
    """
    dag._on_context_exit = _bokeh_dag.update

    bok = pn.pane.Bokeh(_bokeh_dag.draw_dag(dag, plain))

    return bok
