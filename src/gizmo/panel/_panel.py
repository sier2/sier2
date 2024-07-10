import ctypes
import panel as pn
import threading

from gizmo import Gizmo, Dag

NTHREADS = 2

pn.extension(nthreads=NTHREADS, inline=True)

# class StatusContext:
#     def __init__(self, status):
#         self.status = status

#     def __enter__(self):
#         print('ENTER')
#         self.status.value = True

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         print('EXIT')
#         # self.status.value = False
#         if exc_type is None:
#             self.status.color = 'success'
#         else:
#             self.status.color = 'danger'

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
    template = pn.template.BootstrapTemplate(
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

    # def wrap(w: Gizmo):
    #     name_text = pn.widgets.StaticText(
    #         value=w.name,
    #         css_classes=['card-title'],
    #         styles={'font-size':'1.17em', 'font-weight':'bold'}
    #     )
    #     spacer = pn.HSpacer(
    #         styles=dict(
    #             min_width='1px', min_height='1px'
    #         )
    #     )
    #     status_light = pn.Spacer(
    #         margin=(8, 0, 0, 0),
    #         styles={'width':'20px', 'height':'20px', 'background':'orange', 'border-radius': '10px'}
    #     )

    #     if w.user_input:
    #         # This is a user_input gizmo, so add a 'Continue' button.
    #         #
    #         def on_continue(_event):
    #             # The user may not have changed anything from the default values,
    #             # so there won't be anything on the gizmo queue.
    #             # Therefore, we trigger the output params to put their
    #             # current values on the queue.
    #             # If their values are already there, it doesn't matter.
    #             #
    #             w.param.trigger(*w._gizmo_out_params)
    #             dag.execute()

    #         c_button = pn.widgets.Button(name='Continue', button_type='primary')
    #         pn.bind(on_continue, c_button, watch=True)

    #         w_ = pn.Column(w, pn.Row(c_button, align='end'))
    #     else:
    #         w_ = w

    #     return pn.Card(
    #         w_,
    #         header=pn.Row(
    #             name_text,
    #             pn.VSpacer(),
    #             spacer,
    #             status_light
    #         ),
    #         sizing_mode='stretch_width'
    #     )

    def reset():
        """Experiment."""
        col = template.main.objects[0]
        for card in col:
            status = card.header[0]

    # template.main.append(pn.Column(*(wrap(gw) for gw in dag.get_sorted())))
    # content = [GizmoCard(template, dag, gw) for gw in dag.get_sorted()]
    # print(f'{content=}')
    # template.main.append(content)
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
    template.show(threaded=False)

class GizmoCard(pn.Card):
    def __init__(self, parent_template, dag: Dag, w: Gizmo, *args, **kwargs):

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
        status_light = pn.Spacer(
            margin=(8, 0, 0, 0),
            styles={'width':'20px', 'height':'20px', 'background':'orange', 'border-radius': '10px'}
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
                    dag.execute()
                finally:
                    parent_template.main[0].loading = False

            c_button = pn.widgets.Button(name='Continue', button_type='primary')
            pn.bind(on_continue, c_button, watch=True)

            w_ = pn.Column(w, pn.Row(c_button, align='end'))
        else:
            w_ = w

        super().__init__(w_, *args, sizing_mode='stretch_width', **kwargs)

        self.header = pn.Row(
            name_text,
            pn.VSpacer(),
            spacer,
            status_light
        )

        # self.loading = parent_template.busy_indicator
