import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle

class DeadlockDetector:
    def __init__(self, processes, resources, allocation, request, resource_quantities):
        self.processes = processes
        self.resources = resources
        self.allocation = allocation
        self.request = request
        self.resource_quantities = resource_quantities

    def build_rag(self):
        """Build the Resource Allocation Graph (RAG)."""
        G = nx.DiGraph()
        for process in self.processes:
            G.add_node(process, type='process')
        for resource in self.resources:
            G.add_node(resource, type='resource', quantity=self.resource_quantities[resource])

        for i in range(len(self.processes)):
            for j in range(len(self.resources)):
                if self.allocation[i][j] > 0:
                    G.add_edge(self.resources[j], self.processes[i], weight=self.allocation[i][j])  # Resource -> Process
                if self.request[i][j] > 0:
                    G.add_edge(self.processes[i], self.resources[j], weight=self.request[i][j])  # Process -> Resource
        return G

    def detect_deadlock(self, G):
        """Detect deadlock by finding cycles in the RAG."""
        try:
            cycle = nx.find_cycle(G, orientation="original")
            return True, cycle
        except nx.NetworkXNoCycle:
            return False, []

    def draw_rag(self, G, cycle_edges=None):
        """Draw the Resource Allocation Graph (RAG)."""
        pos = nx.spring_layout(G, seed=42)
        fig, ax = plt.subplots()
        process_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'process']
        nx.draw_networkx_nodes(G, pos, nodelist=process_nodes, node_shape='o', node_color='lightblue', node_size=3000, ax=ax)
        nx.draw_networkx_labels(G, pos, labels={node: node for node in process_nodes}, font_size=10, font_weight='bold', ax=ax)

        resource_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'resource']
        for node in resource_nodes:
            x, y = pos[node]
            rect = Rectangle((x - 0.1, y - 0.05), 0.2, 0.1, color='lightgreen', alpha=0.7)
            ax.add_patch(rect)
            ax.text(x, y, f"{node}\n({G.nodes[node]['quantity']})", ha='center', va='center', fontsize=10, fontweight='bold')

        nx.draw_networkx_edges(G, pos, edgelist=G.edges, edge_color='black', width=1, arrows=True, ax=ax)
        if cycle_edges:
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v) for u, v, _ in cycle_edges], edge_color='red', width=2, arrows=True, connectionstyle="arc3,rad=0.2", ax=ax)
        ax.set_title("Resource Allocation Graph (RAG)")
        ax.axis('off')
        return fig

class DeadlockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Deadlock Detection System")
        self.root.geometry("800x600")  # Larger window to accommodate centered content

        self.num_processes = tk.IntVar()
        self.num_resources = tk.IntVar()
        self.resource_quantities = {}
        self.allocation = []
        self.request = []

        # Main frame to center content
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True)

        self.create_input_fields()
        self.create_buttons()

        # Canvas for displaying RAG
        self.canvas = None

    def create_input_fields(self):
        """Create input fields for processes, resources, and resource quantities."""
        input_frame = tk.Frame(self.main_frame)
        input_frame.pack(pady=20)

        tk.Label(input_frame, text="Number of Processes:").grid(row=0, column=0, padx=10, pady=5)
        tk.Entry(input_frame, textvariable=self.num_processes).grid(row=0, column=1, padx=10, pady=5)

        tk.Label(input_frame, text="Number of Resources:").grid(row=1, column=0, padx=10, pady=5)
        tk.Entry(input_frame, textvariable=self.num_resources).grid(row=1, column=1, padx=10, pady=5)

    def create_buttons(self):
        """Create buttons for actions."""
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Enter Resource Quantities", command=self.enter_resource_quantities, bg="lightgreen").grid(row=0, column=0, padx=10, pady=5)
        tk.Button(button_frame, text="Enter Allocation Matrix", command=self.enter_allocation, bg="lightblue").grid(row=0, column=1, padx=10, pady=5)
        tk.Button(button_frame, text="Enter Request Matrix", command=self.enter_request, bg="lightblue").grid(row=0, column=2, padx=10, pady=5)
        tk.Button(button_frame, text="Show RAG", command=self.show_rag, bg="orange").grid(row=1, column=0, padx=10, pady=5)
        tk.Button(button_frame, text="Detect Deadlock", command=self.detect_deadlock, bg="orange").grid(row=1, column=1, padx=10, pady=5)
        tk.Button(button_frame, text="Analyze RAG Image", command=self.analyze_rag_image, bg="yellow").grid(row=1, column=2, padx=10, pady=5)
        tk.Button(button_frame, text="Exit", command=self.root.quit, bg="red", fg="white").grid(row=2, column=1, padx=10, pady=5)

    def enter_resource_quantities(self):
        num_resources = self.num_resources.get()
        self.resource_quantities = {}
        for i in range(num_resources):
            quantity = simpledialog.askinteger("Input", f"Enter quantity for Resource R{i + 1}:")
            self.resource_quantities[f"R{i + 1}"] = quantity

    def enter_allocation(self):
        num_processes = self.num_processes.get()
        num_resources = self.num_resources.get()
        self.allocation = []
        for i in range(num_processes):
            row = simpledialog.askstring("Input", f"Enter allocation for Process P{i + 1} (space-separated):")
            self.allocation.append(list(map(int, row.split())))

    def enter_request(self):
        num_processes = self.num_processes.get()
        num_resources = self.num_resources.get()
        self.request = []
        for i in range(num_processes):
            row = simpledialog.askstring("Input", f"Enter request for Process P{i + 1} (space-separated):")
            self.request.append(list(map(int, row.split())))

    def show_rag(self):
        if not self.allocation or not self.request or not self.resource_quantities:
            messagebox.showerror("Error", "Please enter resource quantities, allocation, and request matrices first.")
            return

        processes = [f"P{i + 1}" for i in range(self.num_processes.get())]
        resources = [f"R{i + 1}" for i in range(self.num_resources.get())]
        detector = DeadlockDetector(processes, resources, self.allocation, self.request, self.resource_quantities)

        rag_graph = detector.build_rag()
        fig = detector.draw_rag(rag_graph)
        self.display_rag(fig)

    def detect_deadlock(self):
        if not self.allocation or not self.request or not self.resource_quantities:
            messagebox.showerror("Error", "Please enter resource quantities, allocation, and request matrices first.")
            return

        processes = [f"P{i + 1}" for i in range(self.num_processes.get())]
        resources = [f"R{i + 1}" for i in range(self.num_resources.get())]
        detector = DeadlockDetector(processes, resources, self.allocation, self.request, self.resource_quantities)

        rag_graph = detector.build_rag()
        deadlock, cycle = detector.detect_deadlock(rag_graph)
        if deadlock:
            fig = detector.draw_rag(rag_graph, cycle)
            self.display_rag(fig)
            messagebox.showinfo("Deadlock Detected", "The system is in a deadlock state.")
        else:
            messagebox.showinfo("No Deadlock Detected", "The system is in a safe state.")

    def analyze_rag_image(self):
        """Analyze a dropped RAG image to detect deadlock."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not file_path:
            return

        # Simulated image analysis (replace with actual logic if using OpenCV or similar)
        # For now, we'll assume a hardcoded RAG from an "image" as an example
        processes = ["P1", "P2"]
        resources = ["R1", "R2"]
        resource_quantities = {"R1": 1, "R2": 1}
        allocation = [[1, 0], [0, 1]]  # P1 has R1, P2 has R2
        request = [[0, 1], [1, 0]]     # P1 requests R2, P2 requests R1

        detector = DeadlockDetector(processes, resources, allocation, request, resource_quantities)
        rag_graph = detector.build_rag()
        deadlock, cycle = detector.detect_deadlock(rag_graph)

        fig = detector.draw_rag(rag_graph, cycle if deadlock else None)
        self.display_rag(fig)

        if deadlock:
            messagebox.showinfo("Deadlock Detected", "The RAG image indicates a deadlock state.")
        else:
            messagebox.showinfo("No Deadlock Detected", "The RAG image indicates a safe state.")

    def display_rag(self, fig):
        """Display the RAG in the main window."""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(fig, master=self.main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockApp(root)
    root.mainloop()