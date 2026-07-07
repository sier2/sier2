import ctypes
import html
import os
import sys
import threading
from collections.abc import Iterable
from datetime import datetime

import panel as pn
import param
import param.parameterized as paramp

from .. import Block, BlockError, BlockState, BlockValidateError, Dag
from ._dag_chart import dag_pane
from ._feedlogger import getBlockPanelLogger, getDagPanelLogger
from ._panel_util import dag_doc

# from .._panel._default import _card_for_block

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
        self.t0 = datetime.now().astimezone()
        if self.dag_logger:
            self.dag_logger.info('Execute', block_name=self.block.name, block_state=state)

        block_logger = getBlockPanelLogger(self.block.name)
        self.block.logger = block_logger

        # if self.block._progress:
        #     self.block._progress.active = True

        return self.block

    def __exit__(self, exc_type, exc_val, exc_tb):
        delta = (datetime.now().astimezone() - self.t0).total_seconds()

        # if self.block._progress:
        #     self.block._progress.active = False

        if exc_type is None:
            state = BlockState.WAITING if self.block._wait_for_input else BlockState.SUCCESSFUL
            self.block._block_state = state
            if self.dag_logger:
                self.dag_logger.info(
                    f'after {_hms(delta)}',
                    block_name=self.block.name,
                    block_state=state.value,
                )
        elif isinstance(exc_type, KeyboardInterrupt):
            state = BlockState.INTERRUPTED
            self.block._block_state = state
            if not self.dag._is_pyodide:
                self.dag._stopper.event.set()
            if self.dag_logger:
                self.dag_logger.exception(
                    f'KEYBOARD INTERRUPT after {_hms(delta)}',
                    block_name=self.block.name,
                    block_state=state,
                )
        else:
            state = BlockState.ERROR
            self.block._block_state = state
            if exc_type is not BlockValidateError:
                if self.dag_logger:
                    self.dag_logger.exception(
                        f'after {_hms(delta)}',
                        block_name=self.block.name,
                        block_state=state,
                    )

                # msg = f'While in {self.block.name}.execute(): {exc_val}'
                if not self.dag._is_pyodide:
                    self.dag._stopper.event.set()

                if not issubclass(exc_type, BlockError):
                    # Convert the error in the block to a BlockError.
                    #
                    raise BlockError(f'Block {self.block.name}: {exc_val!s}') from exc_val

        if self.dag._on_context_exit:
            self.dag._on_context_exit(is_pyodide=self.dag._is_pyodide)

        return False


def _quit(session_context):
    print(session_context)
    sys.exit()


def interrupt_thread(tid, exctype):
    """Raise exception exctype in thread tid."""

    r = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(tid), ctypes.py_object(exctype))
    if r == 0:
        raise ValueError('Invalid thread id')
    elif r != 1:
        # "if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"
        #
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(tid), None)
        raise SystemError('PyThreadState_SetAsyncExc failed')


def _prepare_to_show(dag: 'PanelDag'):
    # Replace the default text-based context with the panel-based context.
    #
    dag._block_context = _PanelContext

    info_button = pn.widgets.ButtonIcon(icon=INFO_SVG, active_icon=INFO_SVG, description='Dag Help', align='center')

    # A place to stash the info FloatPanel.
    #
    info_fp_holder = pn.Column(visible=False)

    sidebar_title = pn.Row(info_button, '## Blocks')
    template = pn.template.BootstrapTemplate(
        site=dag.site,
        title=dag.title,
        theme='dark',
        header_background='#1e2329',
        header_color='#7dd3fc',
        sidebar=pn.Column(sidebar_title),
        collapsed_sidebar=True,
        sidebar_width=440,
        logo=dag.logo,
        favicon=dag.favicon,
    )

    def display_info(_event):
        """Display a FloatPanel containing help for the dag and blocks."""

        text = dag_doc(dag)
        config = {'headerControls': {'maximize': 'remove'}, 'contentOverflow': 'scroll'}
        fp = pn.layout.FloatPanel(
            text,
            name=dag.title,
            width=550,
            height=450,
            contained=False,
            position='center',
            theme='dark filleddark',
            config=config,
        )
        info_fp_holder[:] = [fp]

    info_button.on_click(display_info)

    switch = pn.widgets.Switch(name='Stop')

    def on_switch(event):
        if switch.value:
            dag.stop()
            # reset()

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
            assert len(all_threads) <= NTHREADS, f'{all_threads=}'
            other_thread = [t for t in all_threads if t.ident != current_tid]

            # It's possible that since the user might not have done anything yet,
            # another thread hasn't spun up.
            #
            if other_thread:
                interrupt_thread(other_thread[0].ident, KeyboardInterrupt)
        else:
            dag.unstop()
            # TODO reset status for each card

    pn.bind(on_switch, switch, watch=True)

    # def reset():
    #     """Experiment: reset the status lights."""
    #     col = template.main.objects[0]
    #     for card in col:
    #         status = card.header[0]

    # We use a Panel Feed widget to display log messages.
    #
    log_feed = pn.Feed(
        view_latest=True,
        scroll_button_threshold=20,
        auto_scroll_limit=1,
        sizing_mode='stretch_width',
    )
    dag_logger = getDagPanelLogger(log_feed)

    cards = []

    if dag.show_doc:
        # The card doesn't need a header: the dag author can do what they like
        # with free-form Markdown.
        #
        card = pn.Card(
            pn.pane.Markdown(dag.doc, sizing_mode='stretch_width'),
            hide_header=True,
            sizing_mode='stretch_width',
        )
        cards.append(card)

    # cards.extend(BlockCard(parent_template=template, dag=dag, block=gw, dag_logger=dag_logger) for gw in dag.get_sorted() if gw._visible)

    def dag_continue(self, _event):
        template.main[0].loading = True

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
                dag.execute_after_input(self, dag_logger=dag_logger)
            except BlockValidateError as e:
                # Display the error as a notification.
                #
                block_name = html.escape(e.block_name)
                error = html.escape(str(e))
                notif = f'<b>{block_name}</b>:<br>{error}'
                pn.state.notifications.error(notif, duration=0)
        finally:
            template.main[0].loading = False

    # Be lazy to avoid a circular import.
    #
    from .._panel._default import _card_for_block

    for block in dag.get_sorted():
        if block._visible:
            card = _card_for_block(block, block.__panel__(), _with_light=True)
            block._dag_continue = dag_continue.__get__(block)
            cards.append(card)

    template.main.append(pn.panel(pn.Column(*cards)))

    author = dag.author['name'] if dag.author else 'Unknown'
    email = dag.author['email'] if dag.author else 'Unknown'
    template.sidebar.append(
        pn.Column(
            switch,
            pn.Row(
                dag_pane(dag),
                max_width=400,
                max_height=200,
            ),
            log_feed,
            info_fp_holder,
            pn.widgets.StaticText(value=f'Author: {author}', margin=0),
            pn.widgets.StaticText(value=f'Email: {email}', margin=0),
        )
    )

    return template


def _sier2_label_formatter(pname: str):
    """Default formatter to turn parameter names into appropriate widget labels.

    Make labels nicer for Panel.

    Panel uses the label to display a caption for the corresponding input widgets.
    The default label is taken from the name of the param, which means the default
    caption starts with "In ".

    Removes the "in_" prefix from input parameters, then passes the param name
    to the default label formatter.
    """

    return paramp.default_label_formatter(pname.removeprefix('in_'))


class PanelDag(Dag):
    """A Dag that displays blocks using Panel (https://panel.holoviz.org).

    Blocks are displayed in a column starting with the dag heads
    (blocks with no inputs), and ordered using a topological sort,
    i.e. parent blocks before child blocks. If a block has multiple children,
    they are displayed in the same order that they first appeared in
    the connections list.
    """

    SIER2_SHOW_PORT = 'SIER2_SHOW_PORT'

    def __init__(
        self,
        connections: Iterable[tuple[param.Parameter, param.Parameter]],
        *,
        bag: Iterable[Block] | None = None,
        site: str = '',
        title: str,
        doc: str,
        author: dict[str, str] | None = None,
        logo: str = '',
        favicon: str = '',
    ):
        """
        Parameters
        ----------
        connections: Iterable[tuple[param.Parameter, param.Parameter]]
            Connections between params that define the dag.
        bag: Iterable[Block]
            Blocks to be added to the dags bag.
        site: str
            Name of the site. Will be shown in the header. Default is '', i.e. not shown.
        title: str
            A title to show in the header.
        doc: str
            Dag documentation.
        logo: str
            URI of logo to add to the header (if local file, logo is base64 encoded as URI).
        favicon: str
            URI of favicon to add to the document head (if local file, favicon is base64 encoded as URI).
        """

        super().__init__(connections=connections, bag=bag, site=site, title=title, doc=doc, author=author)
        paramp.label_formatter = _sier2_label_formatter
        self.logo = logo
        self.favicon = favicon
        # self.template = _prepare_to_show(self)

    @property
    def template(self):
        return _prepare_to_show(self)

    def show(self, port: int = 0):
        """Execute the dag and call show() on the Panel servable.

        If the environment variable `SIER2_SHOW_PORT` is defined as a integer,
        that value will override the value of the port argument.

        Windows:

        .. code-block:: powershell

            $env:SIER2_SHOW_PORT=32001
            python app.py
            rm env:\\DAG_PORT

        Linux:

        .. code-block:: bash

            SIER2_SHOW_PORT=32001 ./app.py

        Parameters
        ----------
        port: int
            The port to listen on.
        """
        pn.state.on_session_destroyed(_quit)

        dag_port = os.getenv(PanelDag.SIER2_SHOW_PORT)
        if dag_port:
            try:
                port = int(dag_port)
            except ValueError as e:
                raise ValueError(f'Invalid {PanelDag.SIER2_SHOW_PORT} value') from e

        # Execute the dag.
        #
        self.execute()

        self.template.show(threaded=False, port=port)

    def servable(self):
        pn.state.on_session_destroyed(_quit)

        # Execute the dag.
        #
        self.execute()

        self.template.servable()
