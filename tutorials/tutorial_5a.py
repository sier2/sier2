from sier2 import Dag, Connection, Library
from sier2.panel import show_dag

from tutorial_3b import UserInput, Translate, Display

Library.add(UserInput, 'tutorial_3b.UserInput')
Library.add(Translate, 'tutorial_3b.Translate')
Library.add(Display, 'tutorial_3b.Display')

if __name__=='__main__':
    UiBlock = Library.get('tutorial_3b.UserInput')
    ui = UiBlock(name='User input', user_input=True)

    TrBlock = Library.get('tutorial_3b.Translate')
    tr = TrBlock(name='Translation')

    DiBlock = Library.get('tutorial_3b.Display')
    di = DiBlock(name='Display output')

    dag = Dag(doc='Translation', title='translate text')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
    dag.connect(tr, di, Connection('out_text', 'in_text'))

    show_dag(dag)
