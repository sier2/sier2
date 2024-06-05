#

# Demonstrate how the gizmo library works.
#

from pprint import pprint

from gizmo import Library, Dag, Connection
from gizmo.provided import AddGizmo, RandomNumberGizmo

def main():
    lib = Library.collect()

    r1 = RandomNumberGizmo(name='random1')
    r2 = RandomNumberGizmo(name='random2')
    a = AddGizmo(name='adder')
    dag = Dag()
    dag.connect(r1, a, Connection('n', 'a'))
    dag.connect(r2, a, Connection('n', 'b'))

    r1.go()
    r2.go()

    dump = dag.dump()
    pprint(dump)

    dag2 = Library.load(dump)

    # We now have a new that is the same as the old dag.
    # If we had a GUI, the user could now provide input.
    # Instead, we'll do it manually. Technically this is cheating, because
    # we shouldn't know what the gizmos are, but since we hard-coded them,
    # we can do it.
    r1 = dag2.gizmo_by_name('random1')
    r2 = dag2.gizmo_by_name('random2')
    r1.go()
    r2.go()

if __name__=='__main__':
    main()
