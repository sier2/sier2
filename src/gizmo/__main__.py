import argparse
from importlib.metadata import entry_points, version
import sys

# def quit(session_context):
#     print(session_context)
#     sys.exit()

def plugins_cmd(args):
    discovered_plugins = entry_points(group='gizmo.library')
    for plugin in discovered_plugins:
        # print(plugin)
        gizmos_func = plugin.load()
        gizmos_list = gizmos_func()

        print(f'In {plugin.module} {version(plugin.module)}:')
        for gizmo in gizmos_list:
            print(f'  {gizmo}')

def panel_cmd(args):
    import importlib
    tmp_m = importlib.machinery.SourceFileLoader('tmp', args.module)
    m = tmp_m.load_module()
    dag = m.make_dag()

    from gizmo.panel import show_dag
    # import panel as pn
    # NTHREADS = 2
    # pn.extension(nthreads=NTHREADS, loading_spinner='bar', inline=True)
    # pn.state.on_session_destroyed(quit)
    show_dag(dag)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    runpanel = subparsers.add_parser('panel', help='Run a dag using a panel UI')
    runpanel.add_argument('module', type=str, help='A python module containing a make_dag() function')
    runpanel.set_defaults(func=panel_cmd)

    plugins = subparsers.add_parser('plugins', help='List plugin gizmos')
    plugins.set_defaults(func=plugins_cmd)

    args = parser.parse_args()
    args.func(args)

if __name__=='__main__':
    main()
