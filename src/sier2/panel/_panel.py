import ctypes
from datetime import datetime
import html
import panel as pn
import sys
import threading
from typing import Callable

import param.parameterized as paramp

from sier2 import Block, BlockValidateError, BlockState, Dag, BlockError
from .._dag import _InputValues
from .._util import trim
from ._feedlogger import getDagPanelLogger, getBlockPanelLogger
from ._panel_util import _get_state_color, dag_doc
from ._chart import html_graph

NTHREADS = 2

# From https://tabler.io/icons/icon/info-circle
#
INFO_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path stroke="none" d="M0 0h24v24H0z" fill="none" />
  <path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" />
  <path d="M12 9h.01" />
  <path d="M11 12h1v4h1" />
</svg>
'''

if '_pyodide' in sys.modules:
    # Pyodide (to be specific, WASM) doesn't allow threads.
    # Specifying one thread for panel for some reason tries to start one, so we need to rely on the default.
    #
    pn.extension(
        'floatpanel',
        inline=True,
        loading_spinner='bar',
        notifications=True,
    )
else:
    pn.extension(
        'floatpanel',
        inline=True,
        nthreads=NTHREADS,
        loading_spinner='bar',
        notifications=True,
    )



def _hms(sec):
    h, sec = divmod(int(sec), 3600)
    m, sec = divmod(sec, 60)

    return f'{h:02}:{m:02}:{sec:02}'

class _PanelContext:
    """A context manager to wrap the execution of a block within a dag.

    This default context manager handles the block state, the stopper,
    and converts block execution errors to BlockError exceptions.

    It also uses the panel UI to provide extra information to the user.
    """

    def __init__(self, *, block: Block, dag: Dag, dag_logger=None):
        self.block = block
        self.dag = dag
        self.dag_logger = dag_logger

    def __enter__(self):
        state = BlockState.EXECUTING
        self.block._block_state = state
        self.t0 = datetime.now()
        if self.dag_logger:
            self.dag_logger.info('Execute', block_name=self.block.name, block_state=state)

        block_logger = getBlockPanelLogger(self.block.name)
        self.block.logger = block_logger

        # if self.block._progress:
        #     self.block._progress.active = True

        return self.block

    def __exit__(self, exc_type, exc_val, exc_tb):
        delta = (datetime.now() - self.t0).total_seconds()

        # if self.block._progress:
        #     self.block._progress.active = False

        if exc_type is None:
            state = BlockState.WAITING if self.block.block_pause_execution else BlockState.SUCCESSFUL
            self.block._block_state = state
            if self.dag_logger:
                self.dag_logger.info(f'after {_hms(delta)}', block_name=self.block.name, block_state=state.value)
        elif isinstance(exc_type, KeyboardInterrupt):
            state = BlockState.INTERRUPTED
            self.block_state._block_state = state
            if not self.dag._is_pyodide:
                self.dag._stopper.event.set()
            if self.dag_logger:
                self.dag_logger.exception(f'KEYBOARD INTERRUPT after {_hms(delta)}', block_name=self.block.name, block_state=state)
        else:
            state = BlockState.ERROR
            self.block._block_state = state
            if exc_type is not BlockValidateError:
                if self.dag_logger:
                    self.dag_logger.exception(
                        f'after {_hms(delta)}',
                        block_name=self.block.name,
                        block_state=state
                    )

                # msg = f'While in {self.block.name}.execute(): {exc_val}'
                if not self.dag._is_pyodide:
                    self.dag._stopper.event.set()

                if not issubclass(exc_type, BlockError):
                    # Convert the error in the block to a BlockError.
                    #
                    raise BlockError(f'Block {self.block.name}: {str(exc_val)}') from exc_val
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

def _prepare_to_show(dag: Dag):
    # Replace the default text-based context with the panel-based context.
    #
    dag._block_context = _PanelContext

    info_button = pn.widgets.ButtonIcon(
        icon=INFO_SVG,
        active_icon=INFO_SVG,
        description='Dag Help',
        align='center'
    )

    # A place to stash the info FloatPanel.
    #
    info_fp_holder = pn.Column(visible=False)

    sidebar_title = pn.Row(info_button, '## Blocks')
    template = pn.template.BootstrapTemplate(
        site=dag.site,
        title=dag.title,
        theme='dark',
        sidebar=pn.Column(sidebar_title),
        collapsed_sidebar=True,
        sidebar_width=440
    )

    def display_info(_event):
        """Display a FloatPanel containing help for the dag and blocks."""

        text = dag_doc(dag)
        config = {
            'headerControls': {'maximize': 'remove'},
            'contentOverflow': 'scroll'
        }
        fp = pn.layout.FloatPanel(text, name=dag.title, width=550, height=450, contained=False, position='center', theme='dark filleddark', config=config)
        info_fp_holder[:] = [fp]

    info_button.on_click(display_info)

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

    # We use a Panel Feed widget to display log messages.
    #
    log_feed = pn.Feed(
        view_latest=True,
        scroll_button_threshold=20,
        auto_scroll_limit=1,
        sizing_mode='stretch_width'
    )
    dag_logger = getDagPanelLogger(log_feed)

    cards = []
    if dag.show_doc:
        # The first line of the dag doc is the card header.
        #
        doc = dag.doc.strip()
        ix = doc.find('\n')
        if ix>=0:
            header = doc[:ix]
            doc = doc[ix:].strip()
        else:
            header = ''

        name_text = pn.widgets.StaticText(
            value=header,
            css_classes=['card-title'],
            styles={'font-size':'1.17em', 'font-weight':'bold'}
        )

        card = pn.Card(pn.pane.Markdown(doc, sizing_mode='stretch_width'), header=pn.Row(name_text), sizing_mode='stretch_width')
        cards.append(card)

    cards.extend(BlockCard(parent_template=template, dag=dag, w=gw, dag_logger=dag_logger) for gw in dag.get_sorted() if gw.block_visible)

    template.main.append(pn.Column(*cards))
    template.sidebar.append(
        pn.Column(
            switch,
            # pn.panel(dag.hv_graph().opts(invert_yaxis=True, xaxis=None, yaxis=None)),
            pn.Row(
                pn.panel(html_graph(dag)), 
                max_width=400, 
                max_height=200,
            ),
            log_feed,
            info_fp_holder
        )
    )

    return template

def _show_dag(dag: Dag):
    """Display the dag in a panel template."""

    template = _prepare_to_show(dag)

    pn.state.on_session_destroyed(_quit)

    # Execute the dag.
    # Since this is a panel dag, we expect the first block to be an input nlock.
    # This ensures that the first block's prepare() method is called.
    # If the first block is not an input block, it must be primed, just like a plain dag.
    #
    dag.execute()

    template.show(threaded=False)

def _serveable_dag(dag: Dag):
    """Serve the dag in a panel template."""

    template = _prepare_to_show(dag)

    pn.state.on_session_destroyed(_quit)

    # Execute the dag.
    # Since this is a panel dag, we expect the first block to be an input nlock.
    # This ensures that the first block's prepare() method is called.
    # If the first block is not an input block, it must be primed, just like a plain dag.
    #
    dag.execute()

    template.servable()

def _default_panel(self) -> Callable[[Block], pn.Param]:
    """Provide a default __panel__() implementation for blocks that don't have one.

    This default will display the in_ parameters.
    """

    in_names = [name for name in self.param.values() if name.startswith('in_')]

    return pn.Param(self, parameters=in_names, show_name=False)

class BlockCard(pn.Card):
    """A custom card to wrap around a block.

    This adds the block title and a status light to the card header.
    The light updates to match the block state.
    """

    @staticmethod
    def _get_state_light(color: str) -> pn.Spacer:
        return pn.Spacer(
            margin=(8, 0, 0, 0),
            styles={'width':'20px', 'height':'20px', 'background':color, 'border-radius': '10px'}
        )

    # def ui(self, message):
    #     """TODO connect this to the template"""
    #     print(message)

    def __init__(self, *args, parent_template, dag: Dag, w: Block, dag_logger=None, **kwargs):
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

        # Does this block have documentation to be displayed in the card?
        #
        doc = pn.pane.Markdown(w.block_doc, sizing_mode='scale_width') if w.block_doc else None

        # If a block has no __panel__() method, Panel will by default
        # inspect the class and display the param attributes.
        # This is obviously not what we want.
        #
        # We just want to display the in_ params.
        #
        has_panel = '__panel__' in w.__class__.__dict__
        if not has_panel:
            # w._progress = pn.indicators.Progress(
            #     name='Block progress',
            #     bar_color='primary',
            #     active=False,
            #     value=-1
            # )

            # Go go gadget descriptor protocol.
            #
            w.__panel__ = _default_panel.__get__(w)

        if w.block_pause_execution:
            # This is an input block, so add a 'Continue' button.
            #
            def on_continue(_event):
                # The user may not have changed anything from the default values,
                # so there won't be anything on the block queue.
                # Therefore, we trigger the output params to put their
                # current values on the queue.
                # If their values are already there, it doesn't matter.
                #
                parent_template.main[0].loading = True
                w.param.trigger(*w._block_out_params)

                try:
                    if dag_logger:
                        dag_logger.info('', block_name=None, block_state=None)
                        dag_logger.info('Execute dag', block_name='', block_state=BlockState.DAG)

                    # We want this block's execute() method to run first
                    # after the user clicks the "Continue" button.
                    # We make this happen by pushing this block on the head
                    # of the queue, but without any values - we don't want
                    # to trigger any param changes.
                    #
                    try:
                        dag.execute_after_input(w, dag_logger=dag_logger)
                    except BlockValidateError as e:
                        # Display the error as a notification.
                        #
                        block_name = html.escape(e.block_name)
                        error = html.escape(str(e))
                        notif = f'<b>{block_name}</b>:<br>{error}'
                        pn.state.notifications.error(notif, duration=0)
                finally:
                    parent_template.main[0].loading = False
            c_button = pn.widgets.Button(name=w.continue_label, button_type='primary', align='end')
            c_button.on_click(on_continue)

            row = [doc, c_button] if doc else [c_button]
            w_ = pn.Column(
                w,
                pn.Row(*row),
               sizing_mode='stretch_width'
            )
        elif doc:
            w_ = pn.Column(w, doc)
        else:
            w_ = w

        super().__init__(w_, *args, sizing_mode='stretch_width', **kwargs)

        self.header = pn.Row(
            name_text,
            pn.VSpacer(),
            spacer,
            self._get_state_light(_get_state_color(w._block_state))
        )

        # Watch the block state so we can update the staus light.
        #
        w.param.watch_values(self.state_change, '_block_state')

    def state_change(self, _block_state: BlockState):
        """Watcher for the block state.

        Updates the state light.
        """

        self.header[-1] = self._get_state_light(_get_state_color(_block_state))

def _sier2_label_formatter(pname: str):
    """Default formatter to turn parameter names into appropriate widget labels.

    Make labels nicer for Panel.

    Panel uses the label to display a caption for the corresponding input widgets.
    The default label is taken from the name of the param, which means the default
    caption starts with "In ".

    Removes the "in_" prefix from input parameters, then passes the param name
    to paramp.default_label_formatter.
    """

    if pname.startswith('in_'):
        pname = pname[3:]

    return paramp.default_label_formatter(pname)

class PanelDag(Dag):
    def __init__(self, *, site: str='Panel Dag', title: str, doc: str):
        super().__init__(site=site, title=title, doc=doc)

        paramp.label_formatter = _sier2_label_formatter

    def show(self):
        _show_dag(self)

    def servable(self):
        _serveable_dag(self)