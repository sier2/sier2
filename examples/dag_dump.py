#

# Demonstrate dumping and loading dags.
#

from pprint import pprint
import random

from gizmo import Library, Dag, Connection
from gizmo.xx.provided import AddGizmo, ConstantNumberGizmo

def main():
    n1 = random.randint(1, 100)
    n2 = random.randint(1, 100)

    r1 = ConstantNumberGizmo(n1)
    r2 = ConstantNumberGizmo(n2)
    ag = AddGizmo(name='adder')

    # Remember the names of the two number gizmos.
    #
    r1name = r1.name
    r2name = r2.name
    agname = ag.name

    dag_a = Dag(doc='Example: dump dag')
    dag_a.connect(r1, ag, Connection('out_constant', 'in_a'))
    dag_a.connect(r2, ag, Connection('out_constant', 'in_b'))

    print('Run the dag')
    r1.execute()
    r2.execute()
    dag_a.execute()
    result_a = ag.out_result

    dump_a = dag_a.dump()
    print('\nThe dumped dag:')
    pprint(dump_a)

    dag_b = Library.load_dag(dump_a)

    # Dumping the new dag should give us the same dump as the original dag.
    #
    dump_b = dag_b.dump()
    print(f'\ndump_b == dump_a: {dump_b==dump_a}')

    # We now have a new dag that is the same as the old dag.
    # If we had a GUI, the user could now provide input to run the dag.
    # Instead, we'll do it manually. Technically this is cheating, because
    # we shouldn't know what the gizmos are, but since we hard-coded them,
    # we can do it.
    #
    print('\nRun the dag loaded from the dump.')

    # The number gizmos will have the same names as in the original dag.
    #
    r1 = dag_b.gizmo_by_name(r1name)
    r2 = dag_b.gizmo_by_name(r2name)
    ag = dag_b.gizmo_by_name(agname)

    r1.go()
    r2.go()
    dag_b.execute()
    result_b = ag.out_result

    print(f'Results should be the same: {result_a=}, {result_b=}')

if __name__=='__main__':
    main()
