from sier2 import Info

def blocks() -> list[Info]:
    return [
        Info('sier2.blocks.RandomNumberBlock', 'Random number generator'),
        Info('sier2.blocks.ConstantNumberBlock', 'Constant number generator'),
        Info('sier2.blocks.AddBlock', 'Add two numbers')
    ]

def dags() -> list[Info]:
    return [
        Info('sier2.dags.demo_dag', 'Demonstrate adding random numbers')
    ]
