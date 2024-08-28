from sier2 import Info

def blocks() -> list[Info]:
    return [
        Info(f'{__package__}.blocks.RandomNumberGizmo', 'Random number generator'),
        Info(f'{__package__}.blocks.ConstantNumberGizmo', 'Constant number generator'),
        Info(f'{__package__}.blocks.AddGizmo', 'Add two numbers')
    ]

def dags() -> list[Info]:
    return [
        Info('sier2.provided.dags.demo_dag', 'Demonstrate adding random numbers')
    ]
