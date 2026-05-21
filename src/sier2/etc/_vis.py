from io import StringIO

from sier2 import Dag


def to_dot(dag: Dag, *, edge_label: str = 'label') -> str:
    """Produce a graphviz DOT layout program from the given dag.

    Parameters
    ----------
    dag: Dag
        A dag.
    edge_label: str
        Specifies the label as "label" (good for -Tpng) or "tooltip" (good for -Tsvg).

    Returns
    -------
    str
        A DOT program that can be processed by dot.
    """

    if edge_label not in ['label', 'tooltip']:
        raise ValueError('edge_label must be label or tooltip')

    buf = StringIO()
    p = lambda *args, **kwargs: print(*args, **kwargs, file=buf)

    p('digraph {')
    p('  graph [splines=true]')
    p('  node [fillcolor="#00ff00", shape="rect", style="rounded,filled", fontnames="svg", fontname="Sans-Serif"]')
    p('  edge [splines=true fontnames="svg", fontname="Sans-Serif"]')

    seen = set()
    for src, dst in dag._block_pairs:
        for node in [src, dst]:
            if node not in seen:
                color = '#f0c8207f' if node._wait_for_input else '#4682b47f'
                p(f'  {node.name} [label="{node.name}", fillcolor="{color}"]')
            seen.add(node)

    for src, dst in dag._block_pairs:
        param_list = [(sname, dname) for (gname, sname), dname in dst._block_name_map.items() if gname == src.name]
        for sname, dname in param_list:
            p(f'  {src.name} -> {dst.name} [{edge_label}="{sname} → {dname}", penwidth=2]')

    p('}')

    return buf.getvalue()
