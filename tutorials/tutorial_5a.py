from sier2 import Connection, Library
from sier2.panel import PanelDag

from tutorial_3b import UserInput, Translate, Display

Library.add_block(UserInput, 'tutorial_3b.UserInput')
Library.add_block(Translate, 'tutorial_3b.Translate')
Library.add_block(Display, 'tutorial_3b.Display')

if __name__=='__main__':
    UiBlock = Library.get_block('tutorial_3b.UserInput')
    ui = UiBlock(name='User input', user_input=True)

    TrBlock = Library.get_block('tutorial_3b.Translate')
    tr = TrBlock(name='Translation')

    DiBlock = Library.get_block('tutorial_3b.Display')
    di = DiBlock(name='Display output')

    dag = PanelDag(doc='Translation', title='translate text')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
    dag.connect(tr, di, Connection('out_text', 'in_text'))

    dag.show()
