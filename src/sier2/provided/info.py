from sier2 import Info

def blocks() -> list[Info]:
    return [
        Info(f'{__package__}.blocks.RandomNumberBlock', 'Random number generator'),
        Info(f'{__package__}.blocks.ConstantNumberBlock', 'Constant number generator'),
        Info(f'{__package__}.blocks.AddBlock', 'Add two numbers')
    ]

def dags() -> list[Info]:
    return [
        Info('sier2.provided.dags.demo_dag', 'Demonstrate adding random numbers')
    ]
