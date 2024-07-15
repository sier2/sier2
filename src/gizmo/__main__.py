import argparse

def runpy_cmd(args):
    print('in cmd', args)

def panel_cmd(args):
    import importlib
    tmp_m = importlib.machinery.SourceFileLoader('tmp', args.module)
    m = tmp_m.load_module()
    dag = m.make_dag()

    from gizmo.panel import show_dag
    import panel as pn
    NTHREADS = 2
    pn.extension(nthreads=NTHREADS, loading_spinner='bar', inline=True)
    show_dag(dag)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    # runpy = subparsers.add_parser('runpy', help='Run a python module')
    # runpy.add_argument('module', type=str, help='Python module')
    # runpy.set_defaults(func=runpy_cmd)

    runpanel = subparsers.add_parser('panel', help='Run a dag using a panel UI')
    runpanel.add_argument('module', type=str, help='A python module containing a make_dag() function')
    runpanel.set_defaults(func=panel_cmd)

    args = parser.parse_args()
    print(args)
    args.func(args)

if __name__=='__main__':
    main()