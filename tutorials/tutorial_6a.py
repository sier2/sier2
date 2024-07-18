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

dumped_dag = dag.dump()

# Save the dump.
#
import json
from pathlib import Path
import tempfile

p = Path(tempfile.gettempdir()) / 'translate.dag'
print(f'Saving dag to {p} ...')
with open(p, 'w', encoding='utf-8') as f:
    json.dump(dumped_dag, f, indent=2)
