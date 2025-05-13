# Generate a dag chart.
# We stick to raw python/html here to keep sier's dependencies to a minimum, 
# even if other libraries would be easier to get plots from.
#

from sier2 import Block, Dag


import panel as pn
import math

class HTMLGraph:
    """A class to generate network graph visualizations using Panel HTML pane"""
    
    def __init__(self, width=400, height=400, background="#f8f9fa"):
        self.width = width
        self.height = height
        self.background = background
        self.nodes = {}
        self.edges = []
        self.node_styles = {
            "default": {
                "background-color": "#4a86e8",
                "color": "black",
                "border": "none",
                "font-weight": "bold"
            },
            "input": {
                "background-color": "#f2df0c",
                "color": "black",
                "font-weight": "bold"
            }
        }
        self.edge_styles = {
            "default": {
                "background-color": "#666",
                "height": "2px"
            }
        }
    
    def add_node_style(self, style_name, style_dict):
        """Add a new node style"""
        self.node_styles[style_name] = style_dict
    
    def add_edge_style(self, style_name, style_dict):
        """Add a new edge style"""
        self.edge_styles[style_name] = style_dict
        
    def add_node(self, node_id, label, x=None, y=None, style="default"):
        """Add a node to the graph"""
        # If no position specified, assign random position
        if x is None:
            x = random.randint(50, self.width - 50)
        if y is None:
            y = random.randint(50, self.height - 50)
            
        self.nodes[node_id] = {
            "label": label,
            "x": x,
            "y": y,
            "style": style
        }
    
    def add_edge(self, source_id, target_id, label=None, style="default"):
        """Add an edge between two nodes"""
        if source_id in self.nodes and target_id in self.nodes:
            self.edges.append({
                "source": source_id,
                "target": target_id,
                "label": label,
                "style": style
            })
    
    # def layout_circle(self, center_x=None, center_y=None, radius=None):
    #     """Arrange nodes in a circle"""
    #     if center_x is None:
    #         center_x = self.width / 2
    #     if center_y is None:
    #         center_y = self.height / 2
    #     if radius is None:
    #         radius = min(self.width, self.height) / 3
            
    #     node_ids = list(self.nodes.keys())
    #     for i, node_id in enumerate(node_ids):
    #         angle = 2 * math.pi * i / len(node_ids)
    #         self.nodes[node_id]["x"] = center_x + radius * math.cos(angle)
    #         self.nodes[node_id]["y"] = center_y + radius * math.sin(angle)
    
    def generate_html(self):
        """Generate HTML representation of the network graph"""
        html = f"""
        <style>
          .graph-container {{
            position: relative;
            width: {self.width}px;
            height: {self.height}px;
            background-color: {self.background};
            border: 1px solid #ddd;
            overflow: hidden;
          }}
          
          .node {{
            position: absolute;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            cursor: pointer;
            transform-origin: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            z-index: 10;
          }}
          
          # .node:hover {{
          #   transform: scale(1.1);
          #   box-shadow: 0 4px 8px rgba(0,0,0,0.3);
          #   z-index: 20;
          # }}
          
          .edge {{
            position: absolute;
            height: 2px;
            transform-origin: left center;
            z-index: 5;
          }}
          
          .edge-label {{
            position: absolute;
            background-color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            z-index: 15;
          }}
        </style>
        
        <div class="graph-container">
        """
        
        # Add edges first (so they're behind nodes)
        for edge in self.edges:
            source = self.nodes[edge["source"]]
            target = self.nodes[edge["target"]]
            
            # Calculate edge properties
            x1, y1 = source["x"], source["y"]
            x2, y2 = target["x"], target["y"]
            
            # Calculate length and angle
            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            angle = math.atan2(y2 - y1, x2 - x1) * (180 / math.pi)
            
            # Get style properties
            style_props = self.edge_styles[edge["style"]]
            style_attr = "; ".join([f"{k}: {v}" for k, v in style_props.items()])
            
            # Create edge element
            html += f"""
            <div class="edge" 
                 style="width: {length}px; 
                        left: {x1}px; 
                        top: {y1}px; 
                        transform: rotate({angle}deg);
                        {style_attr}">
            </div>
            """
            
            # Add edge label if specified
            if edge["label"]:
                # Position label at the middle of the edge
                label_x = (x1 + x2) / 2 - 15
                label_y = (y1 + y2) / 2 - 10
                
                html += f"""
                <div class="edge-label" style="left: {label_x}px; top: {label_y}px;">
                    {edge["label"]}
                </div>
                """
        
        # Add nodes
        for node_id, node in self.nodes.items():
            # Get style properties
            style_props = self.node_styles[node["style"]]
            style_attr = "; ".join([f"{k}: {v}" for k, v in style_props.items()])
            
            # Create node element
            html += f"""
            <div class="node" id="node-{node_id}" 
                 style="left: {node['x'] - 30}px; 
                        top: {node['y'] - 30}px;
                        {style_attr}"
                 onclick="highlightNode('{node_id}')">
                {node["label"]}
            </div>
            """
        
        # # Add some basic interactivity with JavaScript
        # html += """
        # <script>
        # function highlightNode(nodeId) {
        #     // Reset all nodes
        #     const nodes = document.querySelectorAll('.node');
        #     nodes.forEach(n => n.style.transform = 'scale(1)');
            
        #     // Highlight the selected node
        #     const node = document.getElementById('node-' + nodeId);
        #     node.style.transform = 'scale(1.2)';
        # }
        # </script>
        # """
        
        html += "</div>"
        return html
    
    def get_pane(self, width=None, height=None):
        """Get a Panel pane with the graph"""
        if width is None:
            width = self.width + 50
        if height is None:
            height = self.height + 50
            
        return pn.pane.HTML(self.generate_html(), width=width, height=height)
        
def html_graph(dag: Dag):
    """Build a Bokeh figure to visualise the block connections."""

    src: list[Block] = []
    dst: list[Block] = []

    def build_layers():
        """Traverse the block pairs and organise them into layers.

        The first layer contains the root (no input) nodes.
        """

        ranks = {}
        remaining = dag._block_pairs[:]

        # Find the root nodes and assign them a layer.
        #
        src[:], dst[:] = zip(*remaining)
        S = list(set([s for s in src if s not in dst]))
        for s in S:
            ranks[s.name] = 0

        n_layers = 1
        while remaining:
            for s, d in remaining:
                if s.name in ranks:
                    # This destination could be from sources at different layers.
                    # Make sure the deepest one is used.
                    #
                    ranks[d.name] = max(ranks.get(d.name, 0), ranks[s.name] + 1)
                    n_layers = max(n_layers, ranks[d.name])

            remaining = [(s,d) for s,d in remaining if d.name not in ranks]

        return n_layers, ranks

    def layout():
        """Arrange the graph nodes."""

        max_width = 0

        # Arrange the graph y by layer from top to bottom.
        # For x, for now we start at 0 and +1 in each layer.
        #
        yx = {y:0 for y in ranks.values()}
        gxy = {}
        for g, y in ranks.items():
            gxy[g] = [yx[y], y]
            yx[y] += 1
            max_width = max(max_width, yx[y])

        # Balance out the x in each layer.
        #
        for y in range(n_layers+1):
            layer = {name: xy for name,xy in gxy.items() if xy[1]==y}
            if len(layer)<max_width:
                for x, (name, xy) in enumerate(layer.items(), 1):
                    gxy[name][0] = x/max_width

        return gxy

    graph = HTMLGraph()

    n_layers, ranks = build_layers()

    ly = layout()

    max_layer_width = max([ly[n][0] for n in ly.keys()])
        
    vertical_scale = graph.height / (n_layers + 2)
    horizontal_scale = graph.width / (max_layer_width + 2)

    for node in ly.keys():
        graph.add_node(
            node, node, 
            x=(ly[node][0] + 1) * horizontal_scale, 
            y=(ly[node][1] + 1) * vertical_scale,
            style='default' if not dag.block_by_name(node).block_pause_execution else 'input'
        )

    for s, d in dag._block_pairs:
        graph.add_edge(s.name, d.name)

    return graph.get_pane()
