from gizmo import GizmoInfo

def gizmos():
    info = [
        ('tutorial_3b.UserInput', 'A text area and flag for input.'),
        ('tutorial_3b.Translate', 'Translate text to English.'),
        ('tutorial_3b.Display', 'Display translated text.')
    ]

    return [
        GizmoInfo(f'{__package__}.{c}', doc)
        for c, doc in info
    ]
