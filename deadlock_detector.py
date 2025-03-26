import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

class DeadlockDetector:
    def __init__(self, processes, resources, allocation, request, resource_quantities):
        self.processes = processes
        self.resources = resources
        self.allocation = allocation
        self.request = request
        self.resource_quantities = resource_quantities

    def build_rag(self):
        G = nx.DiGraph()
        for process in self.processes:
            G.add_node(process, type='process')
        for resource in self.resources:
            G.add_node(resource, type='resource', quantity=self.resource_quantities[resource])

        for i in range(len(self.processes)):
            for j in range(len(self.resources)):
                if self.allocation[i][j] > 0:
                    G.add_edge(self.resources[j], self.processes[i], weight=self.allocation[i][j], type='allocation')
                if self.request[i][j] > 0:
                    G.add_edge(self.processes[i], self.resources[j], weight=self.request[i][j], type='request')
        return G

    def detect_deadlock(self):
        total_resources = list(self.resource_quantities.values())
        total_allocated = [sum(self.allocation[i][j] for i in range(len(self.processes)))for j in range(len(self.resources))]
        available = [total_resources[j] - total_allocated[j] for j in range(len(self.resources))]

        work = available.copy()
        finish = [False] * len(self.processes)

        safe_sequence = []
        steps = []
        steps.append(("Initial", work.copy()))
        while True:
            found = False
            for i in range(len(self.processes)):
                if not finish[i] and all(self.request[i][j] <= work[j] for j in range(len(self.resources))):
                    for j in range(len(self.resources)):
                        work[j] += self.allocation[i][j]
                    finish[i] = True
                    safe_sequence.append(self.processes[i])
                    steps.append((self.processes[i], work.copy()))
                    found = True

            if not found:
                break

        if all(finish):
            return False, safe_sequence, steps
        else:
            return True, [], steps

    def draw_rag(self, G, cycle_edges=None, figsize=(8, 6), process_color='#87CEEB', resource_color='#98FB98',allocation_color='blue', request_color='red'):
        pos = nx.spring_layout(G, seed=42, k=0.5)
        fig, ax = plt.subplots(figsize=figsize)
        
        process_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'process']
        nx.draw_networkx_nodes(G, pos, nodelist=process_nodes, node_shape='o',node_color=process_color, node_size=1500, alpha=0.9, ax=ax)
        
        resource_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'resource']
        nx.draw_networkx_nodes(G, pos, nodelist=resource_nodes, node_shape='s',node_color=resource_color, node_size=1000, alpha=0.9, ax=ax)

        labels = {node: f"{node}\n({G.nodes[node].get('quantity', '')})" if G.nodes[node]['type'] == 'resource' 
                 else node for node in G.nodes}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold', ax=ax)

        allocation_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'allocation']
        request_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'request']

        nx.draw_networkx_edges(G, pos, edgelist=allocation_edges, edge_color=allocation_color,width=2, arrows=True, arrowsize=15, ax=ax,connectionstyle="arc3,rad=0.2")

        nx.draw_networkx_edges(G, pos, edgelist=request_edges, edge_color=request_color,width=2, arrows=True, arrowsize=15, ax=ax,style='dashed', connectionstyle="arc3,rad=-0.2")

        edge_labels = {(u, v): f"{d['weight']}" for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8,label_pos=0.5, verticalalignment='center')

        if cycle_edges:
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v) for u, v, _ in cycle_edges],edge_color='red', width=3, arrows=True, arrowsize=25,connectionstyle="arc3,rad=0.2", ax=ax)

        ax.set_title("Resource Allocation Graph", fontsize=14, pad=20)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.axis('off')
        plt.tight_layout()
        return fig

    def draw_allocation_table(self, figsize=(8, 4)):
        num_resources = len(self.resources)
        num_processes = len(self.processes)
        fig_width = max(6, 2 + num_resources * 1.5)
        fig_height = max(3, 1 + num_processes * 0.5)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.axis('off')

        allocation_data = np.array(self.allocation)
        request_data = np.array(self.request)

        table_data = []
        header_row = ["Process"] + self.resources + self.resources
        table_data.append(header_row)

        for i in range(num_processes):
            row = [self.processes[i]] + list(allocation_data[i]) + list(request_data[i])
            table_data.append(row)

        col_widths = [0.15] + [0.1] * (num_resources * 2)
        table = ax.table(cellText=table_data, colWidths=col_widths,loc='center', cellLoc='center', bbox=[0.1, 0.1, 0.8, 0.8])

        table.auto_set_font_size(False)
        table.set_fontsize(10)

        cells = table.get_celld()
        for (i, j), cell in cells.items():
            cell.set_height(0.1)
            if i == 0:
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#d3d3d3')

        bbox = table.get_window_extent(renderer=fig.canvas.get_renderer())
        bbox = bbox.transformed(ax.transData.inverted())
        x_min, y_max = bbox.x0, bbox.y1

        col_widths_cumsum = np.cumsum([0] + col_widths)
        allocation_center_x = (x_min + col_widths_cumsum[1] + x_min + col_widths_cumsum[num_resources + 1]) / 2
        request_center_x = (x_min + col_widths_cumsum[num_resources + 1] + x_min + col_widths_cumsum[2 * num_resources + 1]) / 2

        ax.text(allocation_center_x, y_max + 0.05, "Allocation",ha='center', va='bottom', fontsize=12, fontweight='bold', color='#2c3e50')
        ax.text(request_center_x, y_max + 0.05, "Request", ha='center', va='bottom', fontsize=12, fontweight='bold', color='#2c3e50')

        plt.tight_layout()
        return fig