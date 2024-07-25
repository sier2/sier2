import ctypes
from datetime import datetime
import panel as pn
import sys
import threading

from gizmo import Gizmo, GizmoState, Dag, GizmoError

NTHREADS = 2

pn.extension(inline=True, nthreads=NTHREADS, loading_spinner='bar')

def _hms(sec):
    h, sec = divmod(int(sec), 3600)
    m, sec = divmod(sec, 60)

    return f'{h:02}:{m:02}:{sec:02}'

class _PanelContext:
    """A context manager to wrap the execution of a gizmo within a dag.

    This default context manager handles the gizmo state, the stopper,
    and converts gizmo execution errors to GimzoError exceptions.

    It also uses the panel UI to provide extra information to the user.
    """

    def __init__(self, gizmo: Gizmo, dag: Dag, callback):
        self.gizmo = gizmo
        self.dag = dag
        self.callback = callback

    def __enter__(self):
        self.gizmo._gizmo_state = GizmoState.EXECUTING
        self.t0 = datetime.now()
        print(f'{self.gizmo.name} at {self.t0.strftime("%H:%M:%S")}')

        return self.gizmo

    def __exit__(self, exc_type, exc_val, exc_tb):
        delta = (datetime.now() - self.t0).total_seconds()
        if exc_type is None:
            self.gizmo._gizmo_state = GizmoState.WAITING if self.gizmo.user_input else GizmoState.SUCCESSFUL
            self.callback(f'  {self.gizmo._gizmo_state.value} after {_hms(delta)}')
        elif isinstance(exc_type, KeyboardInterrupt):
            self.gizmo_state._gizmo_state = GizmoState.INTERRUPTED
            self.dag._stopper.event.set()
            print(f'KEYBOARD INTERRUPT IN GIZMO {self.name}')
            self.callback(f'  {self.gizmo._gizmo_state} after {_hms(delta)}')
        else:
            self.gizmo._gizmo_state = GizmoState.ERROR
            self.callback(f'  {self.gizmo._gizmo_state} after {_hms(delta)}')
            msg = f'While in {self.gizmo.name}.execute(): {exc_val}'
            # LOGGER.exception(msg)
            self.dag._stopper.event.set()

            # Convert the error in the gizmo to a GizmoError.
            #
            raise GizmoError(f'Gizmo {self.gizmo.name}: {str(exc_val)}') from exc_val

        return False

def _quit(session_context):
    print(session_context)
    sys.exit()

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

def show_dag(dag: Dag):
    dag._gizmo_context = _PanelContext

    template = pn.template.BootstrapTemplate(
        site=dag.site,
        title=dag.title,
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
            print('THREADS', current_tid, [t for t in threading.enumerate()])
            all_threads = [t for t in threading.enumerate() if t.name.startswith('ThreadPoolExecutor')]
            assert len(all_threads)<=NTHREADS, f'{all_threads=}'
            other_thread = [t for t in all_threads if t.ident!=current_tid]

            # It's possible that since the user might not have done anything yet,
            # another thread hasn't spun up.
            #
            if other_thread:
                interrupt_thread(other_thread[0].ident, KeyboardInterrupt)
        else:
            dag.unstop()
            # TODO reset status for each card

    pn.bind(on_switch, switch, watch=True)

    def reset():
        """Experiment."""
        col = template.main.objects[0]
        for card in col:
            status = card.header[0]

    template.main.append(
        pn.Column(
            *(GizmoCard(template, dag, gw) for gw in dag.get_sorted())
        )
    )
    template.sidebar.append(
        pn.Column(
            switch,
            pn.panel(dag.hv_graph().opts(invert_yaxis=True, xaxis=None, yaxis=None))
        )
    )

    pn.state.on_session_destroyed(_quit)

    template.show(threaded=False)

class GizmoCard(pn.Card):
    """A custom card to wrap around a gizmo.

    This adds the gizmo title and a status light to the card header.
    The light updates to match the gizmo state.
    """

    @staticmethod
    def _get_status_light(color: str) -> pn.Spacer:
        return pn.Spacer(
            margin=(8, 0, 0, 0),
            styles={'width':'20px', 'height':'20px', 'background':color, 'border-radius': '10px'}
        )

    @staticmethod
    def _get_state_color(gs: GizmoState) -> str:
        """Convert a gizmo state to a color."""

        match gs:
            case GizmoState.INPUT:
                color='white'
            case GizmoState.READY:
                color='black'
            case GizmoState.EXECUTING:
                color='blue'
            case GizmoState.WAITING:
                color='yellow'
            case GizmoState.SUCCESSFUL:
                color = 'green'
            case GizmoState.INTERRUPTED:
                color= 'orange'
            case GizmoState.ERROR:
                color = 'red'

        return color

    def ui(self, message):
        """TODO connect this to the template"""
        print(message)

    def __init__(self, parent_template, dag: Dag, w: Gizmo, *args, **kwargs):
        # Make this look like <h3> (the default Card header text).
        #
        name_text = pn.widgets.StaticText(
            value=w.name,
            css_classes=['card-title'],
            styles={'font-size':'1.17em', 'font-weight':'bold'}
        )
        spacer = pn.HSpacer(
            styles=dict(
                min_width='1px', min_height='1px'
            )
        )

        if w.user_input:
            # This is a user_input gizmo, so add a 'Continue' button.
            #
            def on_continue(_event):
                # The user may not have changed anything from the default values,
                # so there won't be anything on the gizmo queue.
                # Therefore, we trigger the output params to put their
                # current values on the queue.
                # If their values are already there, it doesn't matter.
                #
                w.param.trigger(*w._gizmo_out_params)
                parent_template.main[0].loading = True
                try:
                    self.ui('\nExecute dag:')
                    dag.execute(callback=self.ui)
                finally:
                    parent_template.main[0].loading = False

            c_button = pn.widgets.Button(name='Continue', button_type='primary')
            pn.bind(on_continue, c_button, watch=True)

            w_ = pn.Column(
                w,
                pn.Row(c_button, align='end'),
                sizing_mode='scale_height',
                scroll='y-auto'
            )
        else:
            w_ = w

        super().__init__(w_, *args, sizing_mode='stretch_width', **kwargs)

        self.header = pn.Row(
            name_text,
            pn.VSpacer(),
            spacer,
            self._get_status_light(self._get_state_color(w._gizmo_state)),
        )

        # Watch the gizmo state so we can update the staus light.
        #
        w.param.watch_values(self.state_change, '_gizmo_state')

    def state_change(self, _gizmo_state: GizmoState):
        """Watcher for the gizmo state.

        Updates the status light.
        """

        self.header[-1] = self._get_status_light(self._get_state_color(_gizmo_state))
