from gizmo import Dag, Connection
from .gizmos import RandomNumberGizmo, AddGizmo

def demo_dag():
    rnga = RandomNumberGizmo()
    rngb = RandomNumberGizmo()
    add = AddGizmo()

    dag = Dag(doc='Demonstrate adding random numbers', site='Example', title='Addition')
    dag.connect(rnga, add, Connection('out_n', 'in_a'))
    dag.connect(rngb, add, Connection('out_n', 'in_b'))

    rnga.go()
    rngb.go()

    dag.execute()
