import argparse
from importlib.metadata import version
from .library import _find_gizmos

def gizmos_cmd(args):
    """Display the gizmos found via plugin entry points."""

    curr_ep = None
    for entry_point, gi in _find_gizmos():
        if curr_ep is None or entry_point!=curr_ep:
            print(f'In {entry_point.module} {version(entry_point.module)}:')
            curr_ep = entry_point

        print(f'  {gi.key}: {gi.doc}')

def panel_cmd(args):
    import importlib
    tmp_m = importlib.machinery.SourceFileLoader('tmp', args.module)
    m = tmp_m.load_module()
    dag = m.make_dag()

    from gizmo.panel import show_dag
    show_dag(dag)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    runpanel = subparsers.add_parser('panel', help='Run a dag using a panel UI')
    runpanel.add_argument('module', type=str, help='A python module containing a make_dag() function')
    runpanel.set_defaults(func=panel_cmd)

    plugins = subparsers.add_parser('gizmos', help='Show available gizmos')
    plugins.set_defaults(func=gizmos_cmd)

    args = parser.parse_args()
    args.func(args)

if __name__=='__main__':
    main()
