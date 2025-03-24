import tkinter as tk
from tkinter import messagebox, ttk, simpledialog  # Added simpledialog to the imports
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle

# Rest of the DeadlockDetector class remains unchanged
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
                    G.add_edge(self.resources[j], self.processes[i], weight=self.allocation[i][j])
                if self.request[i][j] > 0:
                    G.add_edge(self.processes[i], self.resources[j], weight=self.request[i][j])
        return G

    def detect_deadlock(self, G):
        try:
            cycle = nx.find_cycle(G, orientation="original")
            return True, cycle
        except nx.NetworkXNoCycle:
            return False, []

    def draw_rag(self, G, cycle_edges=None):
        pos = nx.spring_layout(G, seed=42)
        fig, ax = plt.subplots(figsize=(8, 6))
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

class MatrixDialog(tk.Toplevel):
    def __init__(self, parent, title, num_processes, num_resources, matrix_type):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.num_processes = num_processes
        self.num_resources = num_resources
        self.matrix_type = matrix_type
        
        self.entries = []
        self.create_widgets()
        self.grab_set()
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50, parent.winfo_rooty()+50))

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        for i in range(self.num_processes):
            ttk.Label(frame, text=f"P{i+1}").grid(row=i+1, column=0, padx=5, pady=5)
            row_entries = []
            for j in range(self.num_resources):
                entry = ttk.Entry(frame, width=5)
                entry.grid(row=i+1, column=j+1, padx=2, pady=2)
                row_entries.append(entry)
            self.entries.append(row_entries)

        ttk.Label(frame, text=f"{self.matrix_type} Matrix").grid(row=0, column=0, columnspan=self.num_resources+1, pady=5)
        ttk.Button(frame, text="Submit", command=self.submit).grid(row=self.num_processes+1, column=0, columnspan=self.num_resources+1, pady=10)

    def submit(self):
        try:
            matrix = []
            for row_entries in self.entries:
                row = [int(entry.get()) for entry in row_entries if entry.get()]
                if len(row) != self.num_resources:
                    raise ValueError
                if any(x < 0 for x in row):
                    raise ValueError
                matrix.append(row)
            self.result = matrix
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid non-negative integers for all fields")

class DeadlockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Deadlock Detection System")
        self.root.geometry("1000x700")

        self.num_processes = tk.IntVar(value=0)
        self.num_resources = tk.IntVar(value=0)
        self.resource_quantities = {}
        self.allocation = []
        self.request = []

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(expand=True, fill='both')
        
        self.status_var = tk.StringVar(value="Ready")
        self.create_widgets()
        
        self.canvas = None

    def create_widgets(self):
        # Input Frame
        input_frame = ttk.LabelFrame(self.main_frame, text="System Configuration", padding="10")
        input_frame.pack(fill='x', pady=5)

        ttk.Label(input_frame, text="Number of Processes:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.num_processes, width=5).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Number of Resources:").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.num_resources, width=5).grid(row=0, column=3, padx=5, pady=5)

        # Button Frame
        button_frame = ttk.LabelFrame(self.main_frame, text="Actions", padding="10")
        button_frame.pack(fill='x', pady=5)

        buttons = [
            ("Enter Resource Quantities", self.enter_resource_quantities, "lightgreen"),
            ("Enter Allocation Matrix", self.enter_allocation, "lightblue"),
            ("Enter Request Matrix", self.enter_request, "lightblue"),
            ("Show RAG", self.show_rag, "orange"),
            ("Detect Deadlock", self.detect_deadlock, "orange"),
            ("Analyze RAG Image", self.analyze_rag_image, "yellow"),
            ("Clear All", self.clear_all, "gray"),
            ("Exit", self.root.quit, "red")
        ]

        for i, (text, command, color) in enumerate(buttons):
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.grid(row=i//4, column=i%4, padx=5, pady=5)
            btn.configure(style=f"{color}.TButton")

        # Status Bar
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill='x', side='bottom', pady=5)

        # Configure button styles
        style = ttk.Style()
        for color in set(btn[2] for btn in buttons):
            style.configure(f"{color}.TButton", background=color)

    def enter_resource_quantities(self):
        try:
            num_resources = self.num_resources.get()
            if num_resources <= 0:
                raise ValueError
            self.resource_quantities = {}
            for i in range(num_resources):
                quantity = simpledialog.askinteger("Input", f"Enter quantity for Resource R{i + 1}:", minvalue=0)
                if quantity is None:
                    raise ValueError
                self.resource_quantities[f"R{i + 1}"] = quantity
            self.status_var.set(f"Resource quantities entered for {num_resources} resources")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid positive numbers")

    def enter_allocation(self):
        try:
            num_processes = self.num_processes.get()
            num_resources = self.num_resources.get()
            if num_processes <= 0 or num_resources <= 0:
                raise ValueError
            dialog = MatrixDialog(self.root, "Enter Allocation Matrix", num_processes, num_resources, "Allocation")
            self.root.wait_window(dialog)
            if dialog.result:
                self.allocation = dialog.result
                self.status_var.set(f"Allocation matrix entered for {num_processes}x{num_resources}")
        except ValueError:
            messagebox.showerror("Error", "Please set valid number of processes and resources first")

    def enter_request(self):
        try:
            num_processes = self.num_processes.get()
            num_resources = self.num_resources.get()
            if num_processes <= 0 or num_resources <= 0:
                raise ValueError
            dialog = MatrixDialog(self.root, "Enter Request Matrix", num_processes, num_resources, "Request")
            self.root.wait_window(dialog)
            if dialog.result:
                self.request = dialog.result
                self.status_var.set(f"Request matrix entered for {num_processes}x{num_resources}")
        except ValueError:
            messagebox.showerror("Error", "Please set valid number of processes and resources first")

    def show_rag(self):
        if not self.validate_inputs():
            return
        detector = self.create_detector()
        rag_graph = detector.build_rag()
        fig = detector.draw_rag(rag_graph)
        self.display_rag(fig)
        self.status_var.set("RAG displayed")

    def detect_deadlock(self):
        if not self.validate_inputs():
            return
        detector = self.create_detector()
        rag_graph = detector.build_rag()
        deadlock, cycle = detector.detect_deadlock(rag_graph)
        fig = detector.draw_rag(rag_graph, cycle if deadlock else None)
        self.display_rag(fig)
        self.status_var.set("Deadlock detection completed")
        messagebox.showinfo("Result", "Deadlock detected" if deadlock else "No deadlock detected")

    def analyze_rag_image(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not file_path:
            return
        processes = ["P1", "P2"]
        resources = ["R1", "R2"]
        resource_quantities = {"R1": 1, "R2": 1}
        allocation = [[1, 0], [0, 1]]
        request = [[0, 1], [1, 0]]
        detector = DeadlockDetector(processes, resources, allocation, request, resource_quantities)
        rag_graph = detector.build_rag()
        deadlock, cycle = detector.detect_deadlock(rag_graph)
        fig = detector.draw_rag(rag_graph, cycle if deadlock else None)
        self.display_rag(fig)
        self.status_var.set("RAG image analyzed")
        messagebox.showinfo("Result", "Deadlock detected in image" if deadlock else "No deadlock detected in image")

    def clear_all(self):
        self.num_processes.set(0)
        self.num_resources.set(0)
        self.resource_quantities = {}
        self.allocation = []
        self.request = []
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        self.status_var.set("All data cleared")

    def validate_inputs(self):
        if not self.allocation or not self.request or not self.resource_quantities:
            messagebox.showerror("Error", "Please enter all required data first")
            return False
        return True

    def create_detector(self):
        processes = [f"P{i + 1}" for i in range(self.num_processes.get())]
        resources = [f"R{i + 1}" for i in range(self.num_resources.get())]
        return DeadlockDetector(processes, resources, self.allocation, self.request, self.resource_quantities)

    def display_rag(self, fig):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(fig, master=self.main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(pady=10, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockApp(root)
    root.mainloop()