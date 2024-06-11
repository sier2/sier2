#

# Demonstrate dumping and loading dags.
#

from pprint import pprint
import random

from gizmo import Library, Dag, Connection
from gizmo.provided import AddGizmo, ConstantNumberGizmo

def main():
    n1 = random.randint(1, 100)
    n2 = random.randint(1, 100)

    r1 = ConstantNumberGizmo(n1)
    r2 = ConstantNumberGizmo(n2)
    a = AddGizmo(name='adder')

    # Remember the names of the two number gizmos.
    #
    r1name = r1.name
    r2name = r2.name

    dag = Dag()
    dag.connect(r1, a, Connection('constant', 'a'))
    dag.connect(r2, a, Connection('constant', 'b'))

    print('Run the dag')
    r1.go()
    r2.go()

    dump = dag.dump()
    print('\nThe dumped dag:')
    pprint(dump)

    dag2 = Library.load(dump)

    # Dumping the new dag should give us the same dump as the original dag.
    #
    dump2 = dag2.dump()
    print(f'\ndump2 == dump: {dump2==dump}')

    # We now have a new dag that is the same as the old dag.
    # If we had a GUI, the user could now provide input to run the dag.
    # Instead, we'll do it manually. Technically this is cheating, because
    # we shouldn't know what the gizmos are, but since we hard-coded them,
    # we can do it.
    #
    print('\nRun the dag loaded from the dump')

    # The number gizmos will have the same names as in the original dag.
    #
    r1 = dag2.gizmo_by_name(r1name)
    r2 = dag2.gizmo_by_name(r2name)

    r1.go()
    r2.go()

if __name__=='__main__':
    main()
