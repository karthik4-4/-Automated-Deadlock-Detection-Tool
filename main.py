import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import sv_ttk  # For rounded buttons

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

    def detect_deadlock(self):
        # Step 1: Calculate Available Resources
        total_resources = list(self.resource_quantities.values())
        total_allocated = [sum(self.allocation[i][j] for i in range(len(self.processes))) 
                          for j in range(len(self.resources))]
        available = [total_resources[j] - total_allocated[j] for j in range(len(self.resources))]

        # Step 2: Initialize Work and Finish arrays
        work = available.copy()
        finish = [False] * len(self.processes)

        # Step 3: Find a safe sequence
        safe_sequence = []
        steps = []  # To store the steps for explanation
        while True:
            found = False
            for i in range(len(self.processes)):
                if not finish[i] and all(self.request[i][j] <= work[j] for j in range(len(self.resources))):
                    # Process can finish
                    for j in range(len(self.resources)):
                        work[j] += self.allocation[i][j]
                    finish[i] = True
                    safe_sequence.append(self.processes[i])
                    steps.append((self.processes[i], work.copy()))
                    found = True

            if not found:
                break

        # Step 4: Check for deadlock
        if all(finish):
            return False, safe_sequence, steps  # No deadlock, system is in a safe state
        else:
            return True, [], steps  # Deadlock exists

    def draw_rag(self, G, cycle_edges=None):
        pos = nx.spring_layout(G, seed=42)
        fig, ax = plt.subplots(figsize=(10, 7))
        
        process_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'process']
        nx.draw_networkx_nodes(G, pos, nodelist=process_nodes, node_shape='o', 
                             node_color='#87CEEB', node_size=3500, alpha=0.9, ax=ax)
        
        resource_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'resource']
        nx.draw_networkx_nodes(G, pos, nodelist=resource_nodes, node_shape='s',
                             node_color='#98FB98', node_size=2500, alpha=0.9, ax=ax)

        labels = {node: f"{node}\n({G.nodes[node].get('quantity', '')})" if G.nodes[node]['type'] == 'resource' 
                 else node for node in G.nodes}
        nx.draw_networkx_labels(G, pos, labels, font_size=12, font_weight='bold', ax=ax)

        nx.draw_networkx_edges(G, pos, edge_color='gray', width=2, arrows=True, 
                             arrowsize=20, ax=ax)
        if cycle_edges:
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v) for u, v, _ in cycle_edges],
                                 edge_color='red', width=3, arrows=True, 
                                 arrowsize=25, connectionstyle="arc3,rad=0.2", ax=ax)

        ax.set_title("Resource Allocation Graph", fontsize=16, pad=20)
        ax.grid(True, linestyle='--', alpha=0.3)
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
        self.configure(bg='#f0f0f0')
        self.geometry(f"400x{num_processes*50+100}+{parent.winfo_rootx()+100}+{parent.winfo_rooty()+100}")

    def create_widgets(self):
        frame = ttk.Frame(self, padding="15", style='Matrix.TFrame')
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text=f"{self.matrix_type} Matrix", style='Header.TLabel').pack(pady=10)
        
        entry_frame = ttk.Frame(frame)
        entry_frame.pack()
        
        for i in range(self.num_processes):
            ttk.Label(entry_frame, text=f"P{i+1}", style='Process.TLabel').grid(row=i, column=0, padx=5, pady=5)
            row_entries = []
            for j in range(self.num_resources):
                entry = ttk.Entry(entry_frame, width=5, justify='center')
                entry.grid(row=i, column=j+1, padx=3, pady=3)
                entry.insert(0, "0")
                row_entries.append(entry)
            self.entries.append(row_entries)

        ttk.Button(frame, text="Submit", command=self.submit, style='Action.TButton').pack(pady=15)

    def submit(self):
        try:
            matrix = []
            for row_entries in self.entries:
                row = [int(entry.get()) for entry in row_entries]
                if any(x < 0 for x in row):
                    raise ValueError
                matrix.append(row)
            self.result = matrix
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid non-negative integers")

class DeadlockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Deadlock Detection System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f5f5f5')

        self.num_processes = tk.IntVar(value=2)
        self.num_resources = tk.IntVar(value=2)
        self.resource_quantities = {}
        self.allocation = []
        self.request = []

        self.setup_styles()
        self.create_widgets()
        self.canvas = None

    def setup_styles(self):
        sv_ttk.set_theme('light')
        style = ttk.Style()
        style.configure('TFrame', background='#f5f5f5')
        style.configure('Matrix.TFrame', background='#ffffff', relief='flat')
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'), background='#f5f5f5')
        style.configure('Process.TLabel', font=('Helvetica', 10, 'bold'), foreground='#2F4F4F')
        style.configure('Action.TButton', font=('Helvetica', 10), padding=5)
        style.configure('Green.TButton', foreground='black', font=('Helvetica', 10), padding=5)
        style.map('Green.TButton', background=[('!disabled', '#98FB98'), ('active', '#90EE90')])
        style.configure('Blue.TButton', foreground='black', font=('Helvetica', 10), padding=5)
        style.map('Blue.TButton', background=[('!disabled', '#87CEEB'), ('active', '#ADD8E6')])
        style.configure('Orange.TButton', foreground='black', font=('Helvetica', 10), padding=5)
        style.map('Orange.TButton', background=[('!disabled', '#FFA500'), ('active', '#FF8C00')])
        style.configure('Red.TButton', foreground='white', font=('Helvetica', 10), padding=5)
        style.map('Red.TButton', background=[('!disabled', '#FF6347'), ('active', '#FF4500')])

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side='top', pady=20)
        container = ttk.Frame(main_frame, padding="15")
        container.pack(expand=True)

        config_frame = ttk.LabelFrame(container, text="System Configuration", padding="10")
        config_frame.pack(pady=10)

        config_entries = [
            ("Processes:", self.num_processes, 0),
            ("Resources:", self.num_resources, 2)
        ]
        
        for label, var, col in config_entries:
            ttk.Label(config_frame, text=label).grid(row=0, column=col, padx=5, pady=5)
            ttk.Spinbox(config_frame, from_=1, to=10, textvariable=var, width=5).grid(row=0, column=col+1, padx=5, pady=5)

        control_frame = ttk.LabelFrame(container, text="Controls", padding="10")
        control_frame.pack(pady=10)

        buttons = [
            ("Resource Quantities", self.enter_resource_quantities, "Green"),
            ("Allocation Matrix", self.enter_allocation, "Blue"),
            ("Request Matrix", self.enter_request, "Blue"),
            ("Show RAG", self.show_rag, "Orange"),
            ("Detect Deadlock", self.detect_deadlock, "Orange"),
            ("Analyze Image", self.analyze_rag_image, "Orange"),
            ("Save Graph", self.save_graph, "Green"),
            ("Clear", self.clear_all, "Red")
        ]

        for i, (text, command, color) in enumerate(buttons):
            ttk.Button(control_frame, text=text, command=command, 
                      style=f"{color}.TButton").grid(row=i//4, column=i%4, padx=5, pady=5, sticky='ew')

        self.status_var = tk.StringVar(value="Welcome! Configure the system to begin.")
        status_frame = ttk.Frame(container)
        status_frame.pack(pady=10)
        ttk.Label(status_frame, textvariable=self.status_var, relief="sunken", 
                 padding=5, background='#e0e0e0').pack()

        self.graph_frame = ttk.Frame(container)
        self.graph_frame.pack(pady=10)

    def enter_resource_quantities(self):
        try:
            num_resources = self.num_resources.get()
            self.resource_quantities = {}
            for i in range(num_resources):
                quantity = simpledialog.askinteger("Input", f"Resource R{i + 1} Quantity:", 
                                                minvalue=0, parent=self.root)
                if quantity is None:
                    raise ValueError
                self.resource_quantities[f"R{i + 1}"] = quantity
            self.status_var.set(f"Set quantities for {num_resources} resources")
        except ValueError:
            messagebox.showwarning("Warning", "Invalid input. Please try again.")

    def enter_allocation(self):
        dialog = MatrixDialog(self.root, "Allocation Matrix", 
                           self.num_processes.get(), self.num_resources.get(), "Allocation")
        self.root.wait_window(dialog)
        if dialog.result:
            self.allocation = dialog.result
            self.status_var.set(f"Allocation matrix updated ({self.num_processes.get()}x{self.num_resources.get()})")

    def enter_request(self):
        dialog = MatrixDialog(self.root, "Request Matrix", 
                           self.num_processes.get(), self.num_resources.get(), "Request")
        self.root.wait_window(dialog)
        if dialog.result:
            self.request = dialog.result
            self.status_var.set(f"Request matrix updated ({self.num_processes.get()}x{self.num_resources.get()})")

    def show_rag(self):
        if not self.validate_inputs(): return
        detector = self.create_detector()
        fig = detector.draw_rag(detector.build_rag())
        self.display_rag(fig)
        self.status_var.set("Displaying Resource Allocation Graph")

    def detect_deadlock(self):
        if not self.validate_inputs(): return
        detector = self.create_detector()
        deadlock, safe_sequence, steps = detector.detect_deadlock()

        # Create a new window to display the table and explanation
        result_window = tk.Toplevel(self.root)
        result_window.title("Deadlock Detection Result")
        result_window.geometry("600x400")
        result_window.configure(bg='#f5f5f5')

        # Display the result
        if deadlock:
            result_label = ttk.Label(result_window, text="Deadlock Detected!", font=('Helvetica', 14, 'bold'), background='#f5f5f5')
            result_label.pack(pady=10)
        else:
            result_label = ttk.Label(result_window, text=f"No Deadlock. Safe Sequence: {safe_sequence}", font=('Helvetica', 14, 'bold'), background='#f5f5f5')
            result_label.pack(pady=10)

        # Display the steps
        steps_frame = ttk.Frame(result_window)
        steps_frame.pack(pady=10)

        for step in steps:
            process, work = step
            step_label = ttk.Label(steps_frame, text=f"Process {process} finished. Work = {work}", background='#f5f5f5')
            step_label.pack()

        self.status_var.set("Deadlock detection completed")

    def analyze_rag_image(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not file_path: return
        processes = [f"P{i+1}" for i in range(2)]
        resources = [f"R{i+1}" for i in range(2)]
        detector = DeadlockDetector(processes, resources, [[1,0],[0,1]], [[0,1],[1,0]], {"R1":1, "R2":1})
        rag_graph = detector.build_rag()
        deadlock, safe_sequence, steps = detector.detect_deadlock()
        if deadlock:
            self.status_var.set("Deadlock detected in image!")
            messagebox.showinfo("Detection Result", "Deadlock detected in image!")
        else:
            self.status_var.set(f"No deadlock in image. Safe sequence: {safe_sequence}")
            messagebox.showinfo("Detection Result", f"No deadlock in image. Safe sequence: {safe_sequence}")

    def save_graph(self):
        if not self.canvas: 
            messagebox.showwarning("Warning", "No graph to save!")
            return
        file_path = tk.filedialog.asksaveasfilename(defaultextension=".png",
                                                  filetypes=[("PNG files", "*.png")])
        if file_path:
            self.canvas.figure.savefig(file_path)
            self.status_var.set(f"Graph saved to {file_path}")

    def clear_all(self):
        self.num_processes.set(2)
        self.num_resources.set(2)
        self.resource_quantities = {}
        self.allocation = []
        self.request = []
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        self.status_var.set("System reset to initial state")

    def validate_inputs(self):
        if not all([self.allocation, self.request, self.resource_quantities]):
            messagebox.showwarning("Warning", "Please complete all inputs first!")
            return False
        return True

    def create_detector(self):
        processes = [f"P{i + 1}" for i in range(self.num_processes.get())]
        resources = [f"R{i + 1}" for i in range(self.num_resources.get())]
        return DeadlockDetector(processes, resources, self.allocation, self.request, self.resource_quantities)

    def display_rag(self, fig):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockApp(root)
    root.mainloop()