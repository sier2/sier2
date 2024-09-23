from sier2 import Connection
from sier2.panel import PanelDag

from tutorial_3b import UserInput, Translate, Display

if __name__=='__main__':
    ui = UserInput(name='User input', user_input=True)
    tr = Translate(name='Translation')
    di = Display(name='Display output')

    dag = PanelDag(doc='Translation', title='translate text')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
    dag.connect(tr, di, Connection('out_text', 'in_text'))

    dag.show()
