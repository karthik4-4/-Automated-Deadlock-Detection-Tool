import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import sv_ttk

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
        total_allocated = [sum(self.allocation[i][j] for i in range(len(self.processes))) 
                          for j in range(len(self.resources))]
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

    def draw_rag(self, G, cycle_edges=None, figsize=(8, 6)):
        # Use spring_layout with increased k for better node separation
        pos = nx.spring_layout(G, seed=42, k=1.0)  # Increased k for more spacing between nodes
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Draw process nodes (circles)
        process_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'process']
        nx.draw_networkx_nodes(G, pos, nodelist=process_nodes, node_shape='o', 
                             node_color='#87CEEB', node_size=1500, alpha=0.9, ax=ax)
        
        # Draw resource nodes (squares)
        resource_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'resource']
        nx.draw_networkx_nodes(G, pos, nodelist=resource_nodes, node_shape='s',
                             node_color='#98FB98', node_size=1000, alpha=0.9, ax=ax)

        # Draw labels
        labels = {node: f"{node}\n({G.nodes[node].get('quantity', '')})" if G.nodes[node]['type'] == 'resource' 
                 else node for node in G.nodes}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold', ax=ax)

        # Separate edges into allocation and request
        allocation_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'allocation']
        request_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'request']

        # Function to calculate dynamic rad based on node distance
        def calculate_rad(u, v, base_rad=0.3):
            # Calculate Euclidean distance between nodes
            dist = np.linalg.norm(np.array(pos[u]) - np.array(pos[v]))
            # Scale rad inversely with distance (closer nodes get larger rad)
            return base_rad * (1.5 / max(dist, 0.1))  # Avoid division by zero

        # Draw allocation edges (resource to process) with solid blue line
        for u, v in allocation_edges:
            rad = calculate_rad(u, v, base_rad=0.3)
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color='blue', 
                                 width=2, arrows=True, arrowsize=15, ax=ax, 
                                 connectionstyle=f"arc3,rad={rad}")

        # Draw request edges (process to resource) with dashed red line
        for u, v in request_edges:
            rad = calculate_rad(u, v, base_rad=-0.3)
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color='red', 
                                 width=2, arrows=True, arrowsize=15, ax=ax, 
                                 style='dashed', connectionstyle=f"arc3,rad={rad}")

        # Draw edge labels with offset to avoid overlap
        edge_labels = {(u, v): f"{d['weight']}" for u, v, d in G.edges(data=True)}
        for (u, v), label in edge_labels.items():
            # Calculate the midpoint of the edge
            x = (pos[u][0] + pos[v][0]) / 2
            y = (pos[u][1] + pos[v][1]) / 2
            # Offset the label slightly based on the edge type
            if (u, v) in allocation_edges:
                offset = 0.05  # Move allocation labels slightly up
            else:
                offset = -0.05  # Move request labels slightly down
            ax.text(x, y + offset, label, fontsize=8, ha='center', va='center')

        # Highlight cycle edges if any
        if cycle_edges:
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v) for u, v, _ in cycle_edges], 
                                 edge_color='red', width=3, arrows=True, arrowsize=25, 
                                 connectionstyle="arc3,rad=0.2", ax=ax)

        ax.set_title("Resource Allocation Graph", fontsize=14, pad=20)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.axis('off')
        plt.tight_layout()
        return fig

    def draw_allocation_table(self):
        # Dynamically calculate figure size based on number of processes and resources
        num_resources = len(self.resources)
        num_processes = len(self.processes)
        fig_width = max(8, 2 + num_resources * 2)  # Width scales with number of resources
        fig_height = max(4, 2 + num_processes * 0.5)  # Height scales with number of processes
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.axis('off')

        # Prepare table data
        allocation_data = np.array(self.allocation)
        request_data = np.array(self.request)
        combined_data = np.hstack((allocation_data, request_data))

        # Prepare the table data rows
        row_data = []
        for i in range(len(self.processes)):
            row = [self.processes[i]] + list(allocation_data[i]) + list(request_data[i])
            row_data.append(row)

        # Prepare the column labels
        # First row: "Process", "Allocation", "Request"
        # Second row: "", R1, R2, ..., R1, R2, ...
        col_labels = [""] + self.resources + self.resources  # Second row labels

        # Calculate column widths dynamically
        total_columns = 1 + num_resources * 2  # Process + Allocation + Request
        col_widths = [0.15] + [0.1] * (num_resources * 2)  # Process column wider, others equal

        # Create a table with an extra row for the header
        table_data = row_data
        table = ax.table(cellText=table_data, colLabels=col_labels, colWidths=col_widths,
                         loc='center', cellLoc='center', bbox=[0.1, 0.1, 0.8, 0.8])

        # Customize table appearance
        table.auto_set_font_size(False)
        table.set_fontsize(10)

        # Adjust the table cells for multi-row header
        cells = table.get_celld()
        for (i, j), cell in cells.items():
            cell.set_height(0.1)  # Adjust cell height for better spacing
            if i == 0:  # Header row
                cell.set_text_props(weight='bold')

        # Add the "Allocation" and "Request" labels as a second header row using a separate table
        header_data = [["Process", "Allocation", "Request"]]
        header_col_widths = [0.15, num_resources * 0.1, num_resources * 0.1]  # Span columns
        header_table = ax.table(cellText=header_data, colWidths=header_col_widths,
                                loc='center', cellLoc='center', bbox=[0.1, 0.8, 0.8, 0.1])

        # Customize the header table
        header_table.auto_set_font_size(False)
        header_table.set_fontsize(12)
        header_cells = header_table.get_celld()
        for (i, j), cell in header_cells.items():
            cell.set_text_props(weight='bold')
            cell.set_height(0.1)

        # Merge the "Allocation" and "Request" cells to span multiple columns
        header_cells[(0, 1)].set_text_props(text="Allocation")
        header_cells[(0, 2)].set_text_props(text="Request")

        plt.tight_layout()
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
        self.geometry(f"450x{num_processes*60+150}+{parent.winfo_rootx()+100}+{parent.winfo_rooty()+100}")

    def create_widgets(self):
        frame = ttk.Frame(self, padding="20")
        frame.pack(fill='both', expand=True)

        header_frame = ttk.Frame(frame)
        header_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(header_frame, text=f"Enter {self.matrix_type} Matrix", 
                 style='Header.TLabel').pack(side='left')
        
        entry_frame = ttk.Frame(frame)
        entry_frame.pack(pady=10)
        
        ttk.Label(entry_frame, text="Process").grid(row=0, column=0, padx=5, pady=5)
        for j in range(self.num_resources):
            ttk.Label(entry_frame, text=f"R{j+1}").grid(row=0, column=j+1, padx=5, pady=5)
            
        for i in range(self.num_processes):
            ttk.Label(entry_frame, text=f"P{i+1}", style='Process.TLabel').grid(row=i+1, column=0, padx=5, pady=5)
            row_entries = []
            for j in range(self.num_resources):
                entry = ttk.Entry(entry_frame, width=6, justify='center')
                entry.grid(row=i+1, column=j+1, padx=3, pady=3)
                entry.insert(0, "0")
                row_entries.append(entry)
            self.entries.append(row_entries)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=15)
        ttk.Button(button_frame, text="Submit", command=self.submit, 
                  style='Green.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy, 
                  style='Red.TButton').pack(side='left', padx=5)

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
        self.root.geometry("1400x900")
        self.root.configure(bg='#e6ecef')

        self.num_processes = tk.IntVar(value=2)
        self.num_resources = tk.IntVar(value=2)
        self.resource_quantities = {}
        self.allocation = []
        self.request = []

        self.setup_styles()
        self.create_widgets()
        self.canvas = None
        self.current_graph = None
        self.current_detector = None
        self.setup_tooltips()

    def setup_styles(self):
        sv_ttk.set_theme('light')
        style = ttk.Style()
        style.configure('TFrame', background='#f5f5f5')
        style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'), foreground='#2c3e50')
        style.configure('Process.TLabel', font=('Helvetica', 11, 'bold'), foreground='#2980b9')
        style.configure('Action.TButton', font=('Helvetica', 10, 'bold'), padding=8)
        
        style.configure('Green.TButton', font=('Helvetica', 10, 'bold'), padding=8)
        style.map('Green.TButton', background=[('!disabled', '#2ecc71'), ('active', '#27ae60')])
        style.configure('Blue.TButton', font=('Helvetica', 10, 'bold'), padding=8)
        style.map('Blue.TButton', background=[('!disabled', '#3498db'), ('active', '#2980b9')])
        style.configure('Orange.TButton', font=('Helvetica', 10, 'bold'), padding=8)
        style.map('Orange.TButton', background=[('!disabled', '#e67e22'), ('active', '#d35400')])
        style.configure('Red.TButton', font=('Helvetica', 10, 'bold'), padding=8)
        style.map('Red.TButton', background=[('!disabled', '#e74c3c'), ('active', '#c0392b')])

    def create_widgets(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Graph", command=self.save_graph)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help)

        self.paned_window = ttk.PanedWindow(self.root, orient='horizontal')
        self.paned_window.pack(fill='both', expand=True, padx=15, pady=15)

        left_frame = ttk.Frame(self.paned_window, style='TFrame')
        self.paned_window.add(left_frame, weight=1)

        self.right_frame = ttk.Frame(self.paned_window, style='TFrame')
        self.paned_window.add(self.right_frame, weight=3)

        config_frame = ttk.LabelFrame(left_frame, text=" System Configuration ", padding="15")
        config_frame.pack(pady=10, fill='x', padx=10)

        ttk.Label(config_frame, text="Processes:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.num_processes, 
                   width=5).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Resources:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.num_resources, 
                   width=5).grid(row=1, column=1, padx=5, pady=5)

        control_frame = ttk.LabelFrame(left_frame, text=" Control Panel ", padding="15")
        control_frame.pack(pady=10, fill='x', padx=10)

        buttons = [
            ("Resource Quantities", self.enter_resource_quantities, "Green", "Set resource quantities"),
            ("Allocation Matrix", self.enter_allocation, "Blue", "Define allocation matrix"),
            ("Request Matrix", self.enter_request, "Blue", "Define request matrix"),
            ("Show RAG", self.show_rag, "Orange", "Display Resource Allocation Graph"),
            ("Detect Deadlock", self.detect_deadlock, "Orange", "Check for deadlock"),
            ("Analyze Image", self.analyze_rag_image, "Orange", "Analyze RAG from image"),
            ("Save Graph", self.save_graph, "Green", "Save current graph"),
            ("Clear All", self.clear_all, "Red", "Reset everything")
        ]

        for i, (text, command, color, tooltip) in enumerate(buttons):
            btn = ttk.Button(control_frame, text=text, command=command, 
                           style=f"{color}.TButton")
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky='ew')
            btn.tooltip_text = tooltip

        self.status_var = tk.StringVar(value="Welcome! Configure the system to begin.")
        status_frame = ttk.Frame(left_frame, relief='sunken', padding=5)
        status_frame.pack(fill='x', pady=10, padx=10)
        ttk.Label(status_frame, textvariable=self.status_var, 
                 background='#dfe6e9').pack(fill='x')

        self.graph_frame = ttk.Frame(self.right_frame)
        self.graph_frame.pack(fill='both', expand=True, padx=10, pady=10)

        toolbar = ttk.Frame(self.right_frame)
        toolbar.pack(fill='x', pady=5, padx=10)
        
        self.size_slider = ttk.Scale(toolbar, from_=1, to=10, orient='horizontal', 
                                   command=self.update_size)
        self.size_slider.set(5)
        self.size_slider.pack(side='left', padx=5)
        ttk.Label(toolbar, text="Graph Size").pack(side='left', padx=5)
        
        ttk.Button(toolbar, text="Zoom In", command=self.zoom_in, 
                  style='Blue.TButton').pack(side='right', padx=5)
        ttk.Button(toolbar, text="Zoom Out", command=self.zoom_out, 
                  style='Blue.TButton').pack(side='right', padx=5)

    def setup_tooltips(self):
        def create_tooltip(widget, text):
            def enter(event):
                x, y = widget.winfo_pointerxy()
                tooltip = tk.Toplevel(widget)
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{x+10}+{y+10}")
                label = ttk.Label(tooltip, text=text, background="#ffffe0", 
                                relief='solid', borderwidth=1)
                label.pack()
                widget.tooltip_window = tooltip
            
            def leave(event):
                if hasattr(widget, 'tooltip_window'):
                    widget.tooltip_window.destroy()
            
            widget.bind('<Enter>', enter)
            widget.bind('<Leave>', leave)

        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button) and hasattr(widget, 'tooltip_text'):
                create_tooltip(widget, widget.tooltip_text)

    def update_size(self, value):
        if self.current_detector and self.current_graph:
            size_factor = float(value)
            total_nodes = len(self.current_graph.nodes)
            base_size = max(4, min(8, total_nodes * 0.5))  # Base size between 4 and 8
            figsize = (base_size * size_factor / 5, base_size * size_factor / 5)
            fig = self.current_detector.draw_rag(self.current_graph, figsize=figsize)
            self.display_rag(fig)

    def zoom_in(self):
        current = self.size_slider.get()
        if current < 10:
            self.size_slider.set(current + 1)
            self.update_size(current + 1)

    def zoom_out(self):
        current = self.size_slider.get()
        if current > 1:
            self.size_slider.set(current - 1)
            self.update_size(current - 1)

    def enter_resource_quantities(self):
        try:
            num_resources = self.num_resources.get()
            self.resource_quantities = {}
            dialog = tk.Toplevel(self.root)
            dialog.title("Resource Quantities")
            dialog.geometry("300x400")
            dialog.transient(self.root)
            dialog.grab_set()

            entries = []
            for i in range(num_resources):
                frame = ttk.Frame(dialog, padding=5)
                frame.pack(fill='x', pady=2)
                ttk.Label(frame, text=f"R{i+1}:").pack(side='left', padx=5)
                entry = ttk.Entry(frame)
                entry.insert(0, "1")
                entry.pack(side='left', padx=5)
                entries.append(entry)

            def submit():
                try:
                    for i, entry in enumerate(entries):
                        qty = int(entry.get())
                        if qty < 0: raise ValueError
                        self.resource_quantities[f"R{i+1}"] = qty
                    dialog.destroy()
                    self.status_var.set(f"Set quantities for {num_resources} resources")
                except ValueError:
                    messagebox.showerror("Error", "Please enter valid non-negative integers")

            ttk.Button(dialog, text="Submit", command=submit, 
                      style='Green.TButton').pack(pady=10)
            dialog.wait_window()
        except:
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
        self.current_detector = self.create_detector()
        self.current_graph = self.current_detector.build_rag()
        
        size_factor = self.size_slider.get()
        total_nodes = len(self.current_graph.nodes)
        base_size = max(4, min(8, total_nodes * 0.5))  # Base size between 4 and 8
        figsize = (base_size * size_factor / 5, base_size * size_factor / 5)
        fig = self.current_detector.draw_rag(self.current_graph, figsize=figsize)
        self.display_rag(fig)
        self.status_var.set("Displaying Resource Allocation Graph")

    def detect_deadlock(self):
        if not self.validate_inputs(): return
        detector = self.create_detector()
        deadlock, safe_sequence, steps = detector.detect_deadlock()

        result_window = tk.Toplevel(self.root)
        result_window.title("Deadlock Detection Result")
        result_window.geometry("900x700")
        result_window.configure(bg='#f5f5f5')

        fig = detector.draw_allocation_table()
        canvas = FigureCanvasTkAgg(fig, master=result_window)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10, padx=10)

        result_frame = ttk.Frame(result_window)
        result_frame.pack(pady=10)
        if deadlock:
            ttk.Label(result_frame, text="⚠ Deadlock Detected!", 
                     font=('Helvetica', 16, 'bold'), foreground='#e74c3c').pack()
        else:
            ttk.Label(result_frame, text="✓ No Deadlock Detected", 
                     font=('Helvetica', 16, 'bold'), foreground='#2ecc71').pack()
            ttk.Label(result_frame, text=f"Safe Sequence: {safe_sequence}", 
                     font=('Helvetica', 12)).pack()

        steps_frame = ttk.LabelFrame(result_window, text="Execution Steps", padding=10)
        steps_frame.pack(pady=10, padx=10, fill='both')
        
        table = ttk.Treeview(steps_frame, columns=("Step", "Process", "Available"), 
                           show="headings", height=10)
        table.heading("Step", text="Step")
        table.heading("Process", text="Process")
        table.heading("Available", text="Available Resources")
        table.pack(fill='both', expand=True)
        
        vsb = ttk.Scrollbar(steps_frame, orient="vertical", command=table.yview)
        vsb.pack(side='right', fill='y')
        table.configure(yscrollcommand=vsb.set)

        for i, step in enumerate(steps):
            process, work = step
            table.insert("", "end", values=(f"{i}", process, work))

        self.status_var.set("Deadlock detection completed")

    def analyze_rag_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not file_path: return
        processes = [f"P{i+1}" for i in range(2)]
        resources = [f"R{i+1}" for i in range(2)]
        detector = DeadlockDetector(processes, resources, [[1,0],[0,1]], [[0,1],[1,0]], {"R1":1, "R2":1})
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
        file_path = filedialog.asksaveasfilename(defaultextension=".png", 
                                              filetypes=[("PNG files", "*.png")])
        if file_path:
            self.canvas.figure.savefig(file_path)
            self.status_var.set(f"Graph saved to {file_path}")

    def export_data(self):
        if not self.validate_inputs(): return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                              filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("Deadlock Detection Data\n")
                f.write(f"Processes: {self.num_processes.get()}\n")
                f.write(f"Resources: {self.num_resources.get()}\n")
                f.write(f"Resource Quantities: {self.resource_quantities}\n")
                f.write("Allocation Matrix:\n")
                for row in self.allocation:
                    f.write(f"{row}\n")
                f.write("Request Matrix:\n")
                for row in self.request:
                    f.write(f"{row}\n")
            self.status_var.set(f"Data exported to {file_path}")

    def clear_all(self):
        self.num_processes.set(2)
        self.num_resources.set(2)
        self.resource_quantities = {}
        self.allocation = []
        self.request = []
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        self.current_graph = None
        self.current_detector = None
        self.status_var.set("System reset to initial state")

    def show_help(self):
        help_text = """Deadlock Detection System User Guide

1. Configure System:
   - Set number of processes and resources
   - Enter resource quantities
   - Define allocation and request matrices

2. Features:
   - Show RAG: Visualize resource allocation graph
   - Detect Deadlock: Check for deadlock conditions
   - Analyze Image: Analyze deadlock from RAG image
   - Save Graph: Export current graph as PNG
   - Export Data: Save system data as text file

3. Controls:
   - Use slider to adjust graph size
   - Zoom in/out buttons for better view
   - Tooltips provide button descriptions

4. Status:
   - Bottom bar shows current system state"""
        
        messagebox.showinfo("User Guide", help_text)

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
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockApp(root)
    root.mainloop()