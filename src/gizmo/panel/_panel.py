import ctypes
import panel as pn
import threading

from gizmo import Gizmo, Dag

NTHREADS = 2

pn.extension(nthreads=NTHREADS, inline=True)

class StatusContext:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        print('ENTER')
        self.status.value = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('EXIT')
        # self.status.value = False
        if exc_type is None:
            self.status.color = 'success'
        else:
            self.status.color = 'danger'

def interrupt_thread(tid, exctype):
    """Raise exception exctype in thread tid."""

    r = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(tid),
        ctypes.py_object(exctype)
    )
    if r==0:
        raise ValueError('Invalid thread id')
    elif r!=1:
        # "if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"
        #
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(tid), None)
        raise SystemError('PyThreadState_SetAsyncExc failed')

def show_dag(dag: Dag, *, site: str, title: str):
    template = pn.template.MaterialTemplate(
        site=site,
        title=title,
        theme='dark',
        sidebar=pn.Column('## Gizmos'),
        collapsed_sidebar=True
    )

    switch = pn.widgets.Switch(name='Stop')

    def on_switch(event):
        if switch.value:
            dag.stop()
            reset()

            # Which thread are we running on?
            #
            current_tid = threading.current_thread().ident

            # What other threads are running?
            # There are multiple threads running, including the main thread
            # and the bokeh server thread. We need to find the panel threads.
            # Unfortunately, there is nothing special about them.
            #
            all_threads = [t for t in threading.enumerate() if t.name.startswith('ThreadPoolExecutor')]
            assert len(all_threads)==NTHREADS, f'{all_threads=}'
            other_thread = [t for t in all_threads if t.ident!=current_tid][0]
            interrupt_thread(other_thread.ident, KeyboardInterrupt)
        else:
            dag.unstop()
            # TODO reset status for each card

    pn.bind(on_switch, switch, watch=True)

    def wrap(w: Gizmo):
        running_status = pn.indicators.BooleanStatus(value=False, color='primary', align=('end', 'center'))
        w._gizmo_context = StatusContext(running_status)
        return pn.Card(
            w,
            header=pn.Row(
                running_status,
                pn.pane.HTML(
                    f'<h3 class="card-title">{w.name}</h3>',
                    css_classes=['card-title'], margin=(0, 0)
                )
            ),
            sizing_mode='stretch_width'
        )

    def reset():
        """Experiment."""
        col = template.main.objects[0]
        for card in col:
            status = card.header[0]

    template.main.objects = [pn.Column(*(wrap(gw) for gw in dag.get_sorted()))]
    template.sidebar.objects = [
        pn.Column(
            switch,
            pn.panel(dag.hv_graph().opts(invert_yaxis=True, xaxis=None, yaxis=None))
        )
    ]
    template.show(threaded=False)
