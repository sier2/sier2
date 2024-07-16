def gizmos():
    modules = [
        'tutorial_3b.UserInput',
        'tutorial_3b.Translate',
        'tutorial_3b.Display'
    ]

    return [f'{__package__}.{m}' for m in modules]
