from sier2 import Dag, Connection
from sier2.panel import show_dag

from .tutorial_3b import UserInput, Translate, Display

def translate_dag():
    ui = UserInput(name='User input', user_input=True)
    tr = Translate(name='Translation')
    di = Display(name='Display output')

    dag = Dag(doc='Translation', site='Translation dag', title='translate text')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
    dag.connect(tr, di, Connection('out_text', 'in_text'))

    show_dag(dag)
