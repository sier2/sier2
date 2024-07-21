from gizmo import Info

def gizmos():
    info = [
        Info(f'{__package__}.tutorial_3b.UserInput', 'A text area and flag for input.'),
        Info(f'{__package__}.tutorial_3b.Translate', 'Translate text to English.'),
        Info(f'{__package__}.tutorial_3b.Display', 'Display translated text.')
    ]

    return info

def dags():
    info = [
        Info(f'{__package__}.dag_library.translate_dag', 'Translation app')
    ]

    return info
