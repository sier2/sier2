from sier2 import Dag, Connection, Library
from sier2.panel import show_dag

print('Loading ui ...')
UiBlock = Library.get('sier2_examples.tutorial_3b.UserInput')
ui = UiBlock(name='User input', user_input=True)

print('Loading translator ...')
TrBlock = Library.get('sier2_examples.tutorial_3b.Translate')
tr = TrBlock(name='Translation')

print('Loading display ...')
DiBlock = Library.get('sier2_examples.tutorial_3b.Display')
di = DiBlock(name='Display output')

dag = Dag(doc='Translation', title='translate text')
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
