from gizmo import Info

def gizmos() -> list[Info]:
    return [
        Info(f'{__package__}.gizmos.RandomNumberGizmo', 'Random number generator'),
        Info(f'{__package__}.gizmos.ConstantNumberGizmo', 'Constant number generator'),
        Info(f'{__package__}.gizmos.AddGizmo', 'Add two numbers')
    ]

def dags() -> list[Info]:
    return [
        Info('gizmo.provided.dags.demo_dag', 'Demonstrate adding random numbers')
    ]
