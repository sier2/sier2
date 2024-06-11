#

# Demonstrate that a dag can be loaded from a dump.
# First, run panel-bars.py to create a dumped dag in dag.json.
# Then run this to load and start the dumped dag.
#

import holoviews as hv
import panel as pn
import json
from pathlib import Path
import tempfile

from gizmo import Gizmo, Dag, Connection, Library
import param

from _panel_widgets import QueryWidget, BarchartWidget

hv.extension('bokeh', inline=True)
pn.extension(inline=True)
# hv.renderer('bokeh').theme = 'dark_minimal'

def main():
    # Load the dag.
    #
    p = Path(tempfile.gettempdir()) / 'dag.json'
    print(f'Loading dag from {p} ...')
    with open(p, encoding='utf-8') as f:
        dump = json.load(f)

    dag = Library.load(dump)
    title = dump['panel']['title']

    # Build a panel app.
    #
    template = pn.template.MaterialTemplate(
        title=title,
        theme='dark',
        site='PoC ',
        sidebar=pn.Column('## Gizmos'),
        collapsed_sidebar=True
    )
    gizmos = dag.get_sorted()
    template.main.objects = [pn.Column(*gizmos)]
    template.sidebar.objects = [pn.panel(dag.hv_graph().opts(invert_yaxis=True, xaxis=None, yaxis=None))]
    template.show(threaded=False)

if __name__=='__main__':
    # Gizmos that are loaded from a dumped dag must be in the dag library.
    # Because this is a demonstration, we load the required gizmo classes manually.
    #
    Library.add(QueryWidget)
    Library.add(BarchartWidget)

    main()
