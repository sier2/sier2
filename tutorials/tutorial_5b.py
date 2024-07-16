from gizmo import Dag, Connection, Library
from gizmo.panel import show_dag

print('Loading ui ...')
UiGizmo = Library.get('gizmo_examples.tutorial_3b.UserInput')
ui = UiGizmo(name='User input', user_input=True)

print('Loading translator ...')
TrGizmo = Library.get('gizmo_examples.tutorial_3b.Translate')
tr = TrGizmo(name='Translation')

print('Loading display ...')
DiGizmo = Library.get('gizmo_examples.tutorial_3b.Display')
di = DiGizmo(name='Display output')

dag = Dag(doc='Translation', site='Translation dag', title='translate text')
dag.connect(ui, tr, Connection('out_text', 'in_text'), Connection('out_flag', 'in_flag'))
dag.connect(tr, di, Connection('out_text', 'in_text'))

show_dag(dag)
