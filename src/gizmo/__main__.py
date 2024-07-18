import argparse
from importlib.metadata import version
import json

from gizmo import Library
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
    with open(args.dagfile) as f:
        dag_json = json.load(f)
        dag = Library.load_dag(dag_json)

    from gizmo.panel import show_dag
    show_dag(dag)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    runpanel = subparsers.add_parser('panel', help='Run a dag using a panel UI')
    runpanel.add_argument('dagfile', type=str, help='A file containing a dumped dag')
    runpanel.set_defaults(func=panel_cmd)

    plugins = subparsers.add_parser('gizmos', help='Show available gizmos')
    plugins.set_defaults(func=gizmos_cmd)

    args = parser.parse_args()
    args.func(args)

if __name__=='__main__':
    main()
