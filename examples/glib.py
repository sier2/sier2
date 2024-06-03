#

# Demonstrate how the gizmo library works.
#

from gizmo import library, Dag

def main():
    lib = library.collect()

    # This is a prospective data structure that provides enough information
    # to build a dag.
    # This would be stored somewhere as JSON.
    #
    dagj = {
        'gizmos': [
            {
                'gizmo': 'gizmo.provided.RandomNumberGizmo',
                'instance': 0,
                'params': {
                    'name': 'random1'
                }
            },
            {
                'gizmo': 'gizmo.provided.RandomNumberGizmo',
                'instance': 1,
                'params': {
                    'name': 'random2'
                }
            },
            {
                'gizmo': 'gizmo.provided.AddGizmo',
                'instance': 2,
                'params': {
                    'name': 'adder'
                }
            }
        ],
        'connections': [
            {
                'src': 0,
                'dst': 2,
                'params': ['n:a']
            },
            {
                'src': 1,
                'dst': 2,
                'params': ['n:b']
            }
        ]
    }

    # Create new instances of the specified gizmos.
    #
    instances = {}
    for g in dagj['gizmos']:
        class_name = g['gizmo']
        instance = g['instance']
        if instance not in instances:
            gclass = lib[class_name]
            instances[instance] = gclass(**g['params'])

    # Connect the gizmos.
    #
    dag = Dag()
    for conn in dagj['connections']:
        param_names = conn['params']
        dag.connect(instances[conn['src']], instances[conn['dst']], param_names)

    # We now have a dag.
    # If we had a GUI, the user could now provide input.
    # Instead, we'll do it manually. Technically this is cheating, because
    # we shouldn't know what the gizmos are, but since we hard-coded them,
    # we can do it.
    #
    instances[0].go()
    instances[1].go()

if __name__=='__main__':
    main()
