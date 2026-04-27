from os import PathLike

import graphviz

from sier2 import Dag


def vis(dag: Dag, format: str, output: PathLike | None = None, **kwargs):

    seen = set()

    dot = graphviz.Digraph(
        dag.title.replace(' ', '_'),
        format=format,
        graph_attr={'fontnames': 'svg'},
        node_attr={'fillcolor': '#00ff00', 'shape': 'rect', 'style': 'rounded,filled'},
    )
    for src, dst in dag._block_pairs:
        for node in [src, dst]:
            if not node in seen:
                # print(node._wait_for_input)
                color = '#f0c8207f' if node._wait_for_input else '#4682b47f'
                dot.node(node.name, fillcolor=color, fontname='Sans-Serif')
                seen.add(node)

        param_list = [
            (sname, dname)
            for (gname, sname), dname in dst._block_name_map.items()
            if gname == src.name
        ]
        # print(param_list)

        label = '\\n'.join(f'{sname} → {dname}' for (sname, dname) in param_list)
        dot.edge(src.name, dst.name, tooltip=label, penwidth='2')

    if output:
        dot.render(output, **kwargs)

    return dot.source
