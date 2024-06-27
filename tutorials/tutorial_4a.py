from gizmo import Dag, Connection
from gizmo.panel import show_dag

from tutorial_3b import UserInput, Translate, Display

if __name__=='__main__':
    ui = UserInput(name='User input')
    tr = Translate(name='Translation')
    di = Display(name='Display output')

    dag = Dag(doc='Translation')
    dag.connect(ui, tr, Connection('text', 'text_in'), Connection('flag'))
    dag.connect(tr, di, Connection('text_out', 'text'))

    show_dag(dag, site='Translation dag', title='translate text')
