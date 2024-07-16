from gizmo import Dag, Connection, Library
from gizmo.panel import show_dag

from tutorial_3b import UserInput, Translate, Display

Library.add(UserInput, 'tutorial_3b.UserInput')
Library.add(Translate, 'tutorial_3b.Translate')
Library.add(Display, 'tutorial_3b.Display')

if __name__=='__main__':
    UiGizmo = Library.get('tutorial_3b.UserInput')
    ui = UiGizmo(name='User input', user_input=True)

    TrGizmo = Library.get('tutorial_3b.Translate')
    tr = TrGizmo(name='Translation')

    DiGizmo = Library.get('tutorial_3b.Display')
    di = DiGizmo(name='Display output')

    dag = Dag(doc='Translation', site='Translation dag', title='translate text')
    dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
    dag.connect(tr, di, Connection('out_text', 'in_text'))

    show_dag(dag)
