from gizmo import Dag, Connection, Library
from gizmo.panel import show_dag

from tutorial_3b import UserInput, Translate, Display

import panel as pn
NTHREADS = 2
pn.extension(nthreads=NTHREADS, loading_spinner='bar', inline=True)

if __name__=='__main__':
    ui = Library.get('gizmo_tutorials.tutorial_3b.UserInput')(name='User input', user_input=True)
    tr = Library.get('gizmo_tutorials.tutorial_3b.Translate')(name='Translation')
    di = Library.get('gizmo_tutorials.tutorial_3b.Display')(name='Display output')

    dag = Dag(doc='Translation', site='Translation dag', title='translate text')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
    dag.connect(tr, di, Connection('out_text', 'in_text'))

    show_dag(dag)
