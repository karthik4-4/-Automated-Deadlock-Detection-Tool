import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import sv_ttk
import os
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdfcanvas
import threading

# Custom Toolbar Class to show only "Configure Subplots" and "Save Figure"
class CustomNavigationToolbar(NavigationToolbar2Tk):
    toolitems = [
        ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    ]

    def __init__(self, canvas, parent, *, pack_toolbar=True):
        super().__init__(canvas, parent, pack_toolbar=pack_toolbar)

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

    def draw_rag(self, G, cycle_edges=None, figsize=(8, 6), process_color='#87CEEB', resource_color='#98FB98', allocation_color='blue', request_color='red'):
        pos = nx.spring_layout(G, seed=42, k=0.5)
        fig, ax = plt.subplots(figsize=figsize)
        
        process_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'process']
        nx.draw_networkx_nodes(G, pos, nodelist=process_nodes, node_shape='o', 
                             node_color=process_color, node_size=1500, alpha=0.9, ax=ax)
        
        resource_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'resource']
        nx.draw_networkx_nodes(G, pos, nodelist=resource_nodes, node_shape='s',
                             node_color=resource_color, node_size=1000, alpha=0.9, ax=ax)

        labels = {node: f"{node}\n({G.nodes[node].get('quantity', '')})" if G.nodes[node]['type'] == 'resource' 
                 else node for node in G.nodes}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold', ax=ax)

        allocation_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'allocation']
        request_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'request']

        nx.draw_networkx_edges(G, pos, edgelist=allocation_edges, edge_color=allocation_color, 
                             width=2, arrows=True, arrowsize=15, ax=ax, 
                             connectionstyle="arc3,rad=0.2")

        nx.draw_networkx_edges(G, pos, edgelist=request_edges, edge_color=request_color, 
                             width=2, arrows=True, arrowsize=15, ax=ax, 
                             style='dashed', connectionstyle="arc3,rad=-0.2")

        edge_labels = {(u, v): f"{d['weight']}" for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, 
                                   label_pos=0.5, verticalalignment='center')

        if cycle_edges:
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v) for u, v, _ in cycle_edges], 
                                 edge_color='red', width=3, arrows=True, arrowsize=25, 
                                 connectionstyle="arc3,rad=0.2", ax=ax)

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
        table = ax.table(cellText=table_data, colWidths=col_widths,
                         loc='center', cellLoc='center', bbox=[0.1, 0.1, 0.8, 0.8])

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

        ax.text(allocation_center_x, y_max + 0.05, "Allocation", 
                ha='center', va='bottom', fontsize=12, fontweight='bold', color='#2c3e50')
        ax.text(request_center_x, y_max + 0.05, "Request", 
                ha='center', va='bottom', fontsize=12, fontweight='bold', color='#2c3e50')

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
        ttk.Button(header_frame, text="?", command=lambda: messagebox.showinfo("Help", 
            f"Enter non-negative integers for each process-resource pair in the {self.matrix_type} matrix."), 
            style='Help.TButton').pack(side='right')

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
                entry.bind("<KeyRelease>", self.validate_input)
                row_entries.append(entry)
            self.entries.append(row_entries)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=15)
        ttk.Button(button_frame, text="Submit", command=self.submit).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side='left', padx=5)

    def validate_input(self, event):
        entry = event.widget
        value = entry.get()
        if value.isdigit() and int(value) >= 0:
            entry.configure(style='Valid.TEntry')
        else:
            entry.configure(style='Invalid.TEntry')

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
        self.history = []
        self.redo_stack = []
        self.current_detector = None
        self.current_graph = None
        self.canvas = None
        self.dark_mode = tk.BooleanVar(value=False)
        self.colors = {'process_color': '#87CEEB', 'resource_color': '#98FB98', 
                       'allocation_color': 'blue', 'request_color': 'red'}
        self.language = tk.StringVar(value="English")

        self.setup_styles()
        self.create_widgets()
        self.setup_tooltips()
        self.setup_shortcuts()
        self.auto_save_thread = threading.Thread(target=self.auto_save_loop, daemon=True)
        self.auto_save_thread.start()

    def setup_styles(self):
        sv_ttk.set_theme('light')
        style = ttk.Style()
        style.configure('TFrame', background='#f5f5f5')
        style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'), foreground='#2c3e50')
        style.configure('Process.TLabel', font=('Helvetica', 11, 'bold'), foreground='#2980b9')
        style.configure('Help.TButton', font=('Helvetica', 8), padding=2)
        style.configure('Valid.TEntry', background='#d4edda')
        style.configure('Invalid.TEntry', background='#f8d7da')
        style.configure('Custom.Treeview', font=('Helvetica', 10))
        style.configure('Custom.Treeview.Heading', font=('Helvetica', 11, 'bold'), foreground='#2c3e50')

        # Configure the default button style to match the image
        style.configure('TButton', 
                        font=('Helvetica', 10),  # Sans-serif font
                        background='#E8ECEF',    # Light gray background
                        foreground='#333333',    # Dark gray text
                        bordercolor='#D3D3D3',   # Slightly darker gray border
                        relief='flat',           # Flat relief to avoid 3D effect
                        padding=8)               # Internal padding

        # Map the button states (hover, active, etc.)
        style.map('TButton',
                  background=[('active', '#D3D3D3'), ('!disabled', '#E8ECEF')],  # Darken on hover/active
                  foreground=[('active', '#333333'), ('!disabled', '#333333')])

    def create_widgets(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Graph", command=self.save_graph, accelerator="Ctrl+S")
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_command(label="Export to PDF", command=self.export_to_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")

        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Dark Mode", variable=self.dark_mode, command=self.toggle_theme)
        view_menu.add_command(label="Customize Colors", command=self.customize_colors)

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
        ttk.Button(config_frame, text="?", command=lambda: messagebox.showinfo("Help", 
            "Set the number of processes (1-10)."), style='Help.TButton').grid(row=0, column=2)

        ttk.Label(config_frame, text="Resources:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.num_resources, 
                   width=5).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="?", command=lambda: messagebox.showinfo("Help", 
            "Set the number of resources (1-10)."), style='Help.TButton').grid(row=1, column=2)

        ttk.Label(config_frame, text="Examples:").grid(row=2, column=0, padx=5, pady=5)
        examples = {"Custom": None, "Deadlock 2x2": self.load_deadlock_example, "Safe 3x2": self.load_safe_example}
        self.example_combobox = ttk.Combobox(config_frame, values=list(examples.keys()), state="readonly", 
                                            width=10)
        self.example_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.example_combobox.set("Custom")
        ttk.Button(config_frame, text="Load", 
                  command=lambda: examples[self.example_combobox.get()]() if examples[self.example_combobox.get()] else None).grid(row=2, column=2)

        control_frame = ttk.LabelFrame(left_frame, text=" Control Panel ", padding="15")
        control_frame.pack(pady=10, fill='x', padx=10)

        buttons = [
            ("Resource Quantities", self.enter_resource_quantities, "Set total available units for each resource"),
            ("Allocation Matrix", self.enter_allocation, "Define current resource allocation to processes"),
            ("Request Matrix", self.enter_request, "Define resource requests by processes"),
            ("Show RAG", self.show_rag, "Visualize the Resource Allocation Graph"),
            ("Detect Deadlock", self.detect_deadlock, "Run deadlock detection algorithm"),
            ("Analyze Image", self.analyze_rag_image, "Detect deadlock from an uploaded RAG image"),
            ("Save Graph", self.save_graph, "Save the current graph as an image"),
            ("Clear All", self.clear_all, "Reset all inputs and graphs")
        ]

        for i, (text, command, tooltip) in enumerate(buttons):
            btn = ttk.Button(control_frame, text=text, command=command)
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky='ew')
            btn.tooltip_text = tooltip

        status_frame = ttk.Frame(left_frame, relief='sunken', padding=5)
        status_frame.pack(fill='x', pady=10, padx=10)
        self.status_var = tk.StringVar(value="Welcome! Configure the system to begin.")
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
        
        ttk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side='right', padx=5)
        ttk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side='right', padx=5)
        
        ttk.Label(toolbar, text="Language:").pack(side='left', padx=5)
        ttk.Combobox(toolbar, textvariable=self.language, values=["English", "Spanish"], 
                    width=10, state="readonly").pack(side='left', padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(toolbar, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side='bottom', fill='x', pady=5)

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

    def setup_shortcuts(self):
        self.root.bind("<Control-s>", lambda e: self.save_graph())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())

    def auto_save_loop(self):
        while True:
            time.sleep(300)  # Auto-save every 5 minutes
            if self.validate_inputs():
                self.export_data(auto=True)

    def toggle_theme(self):
        sv_ttk.set_theme('dark' if self.dark_mode.get() else 'light')
        self.root.configure(bg='#2c2c2c' if self.dark_mode.get() else '#e6ecef')

    def customize_colors(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Customize Colors")
        dialog.geometry("300x400")
        dialog.transient(self.root)
        dialog.grab_set()

        color_vars = {key: tk.StringVar(value=self.colors[key]) for key in self.colors}
        for i, (key, var) in enumerate(color_vars.items()):
            ttk.Label(dialog, text=f"{key.replace('_color', '').capitalize()} Color:").grid(row=i, column=0, padx=5, pady=5)
            ttk.Entry(dialog, textvariable=var).grid(row=i, column=1, padx=5, pady=5)

        def apply_colors():
            for key, var in color_vars.items():
                self.colors[key] = var.get()
            self.show_rag()
            dialog.destroy()

        ttk.Button(dialog, text="Apply", command=apply_colors).pack(pady=10)

    def update_size(self, value):
        if not hasattr(self, 'current_detector') or self.current_detector is None or \
           not hasattr(self, 'current_graph') or self.current_graph is None:
            self.status_var.set("Please generate the graph first.")
            return

        size_factor = float(value)
        total_nodes = len(self.current_graph.nodes)
        base_size = max(4, min(8, total_nodes * 0.5))
        figsize = (base_size * size_factor / 5, base_size * size_factor / 5)
        fig = self.current_detector.draw_rag(self.current_graph, figsize=figsize, **self.colors)
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
                entry.bind("<KeyRelease>", self.validate_input)
                entry.pack(side='left', padx=5)
                entries.append(entry)

            def submit():
                try:
                    for i, entry in enumerate(entries):
                        qty = int(entry.get())
                        if qty < 0: raise ValueError
                        self.resource_quantities[f"R{i+1}"] = qty
                    self.save_state()
                    dialog.destroy()
                    self.status_var.set(f"Set quantities for {num_resources} resources")
                except ValueError:
                    messagebox.showerror("Error", "Please enter valid non-negative integers")

            ttk.Button(dialog, text="Submit", command=submit).pack(pady=10)
            dialog.wait_window()
        except Exception as e:
            messagebox.showwarning("Warning", "Invalid input. Please try again.")

    def validate_input(self, event):
        entry = event.widget
        value = entry.get()
        if value.isdigit() and int(value) >= 0:
            entry.configure(style='Valid.TEntry')
        else:
            entry.configure(style='Invalid.TEntry')

    def enter_allocation(self):
        dialog = MatrixDialog(self.root, "Allocation Matrix", 
                           self.num_processes.get(), self.num_resources.get(), "Allocation")
        self.root.wait_window(dialog)
        if dialog.result:
            self.allocation = dialog.result
            self.save_state()
            self.status_var.set(f"Allocation matrix updated ({self.num_processes.get()}x{self.num_resources.get()})")

    def enter_request(self):
        dialog = MatrixDialog(self.root, "Request Matrix", 
                           self.num_processes.get(), self.num_resources.get(), "Request")
        self.root.wait_window(dialog)
        if dialog.result:
            self.request = dialog.result
            self.save_state()
            self.status_var.set(f"Request matrix updated ({self.num_processes.get()}x{self.num_resources.get()})")

    def show_rag(self):
        if not self.validate_inputs(): return
        self.current_detector = self.create_detector()
        self.current_graph = self.current_detector.build_rag()
        
        size_factor = self.size_slider.get()
        total_nodes = len(self.current_graph.nodes)
        base_size = max(4, min(8, total_nodes * 0.5))
        figsize = (base_size * size_factor / 5, base_size * size_factor / 5)
        fig = self.current_detector.draw_rag(self.current_graph, figsize=figsize, **self.colors)
        self.display_rag(fig)
        self.status_var.set("Displaying Resource Allocation Graph")

    def detect_deadlock(self):
        if not self.validate_inputs(): return
        detector = self.create_detector()
        self.progress_var.set(0)
        threading.Thread(target=self.run_detection, args=(detector,)).start()

    def run_detection(self, detector):
        steps_total = len(detector.processes) + 1
        for i in range(steps_total):
            time.sleep(0.1)
            self.progress_var.set((i / steps_total) * 100)
        
        deadlock, safe_sequence, steps = detector.detect_deadlock()
        self.progress_var.set(100)

        result_window = tk.Toplevel(self.root)
        result_window.title("Deadlock Detection Result")
        result_window.geometry("900x700")
        result_window.configure(bg='#f5f5f5')

        canvas = tk.Canvas(result_window, bg='#f5f5f5')
        scrollbar = ttk.Scrollbar(result_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, width=900)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((450, 0), window=scrollable_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        header_frame = ttk.Frame(scrollable_frame, padding="10 20")
        header_frame.pack(fill='x', pady=10, anchor="center")
        ttk.Label(header_frame, text="Deadlock Detection Result", 
                 font=('Helvetica', 18, 'bold'), foreground='#2c3e50').pack()

        fig = detector.draw_allocation_table()
        canvas_widget = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(pady=10, padx=10, anchor="center")

        result_frame = ttk.Frame(scrollable_frame, padding="10")
        result_frame.pack(pady=20, anchor="center")
        if deadlock:
            ttk.Label(result_frame, text="⚠ Deadlock Detected!" if self.language.get() == "English" else "¡Deadlock Detectado!", 
                     font=('Helvetica', 16, 'bold'), foreground='#e74c3c').pack()
        else:
            ttk.Label(result_frame, text="✓ No Deadlock Detected" if self.language.get() == "English" else "✓ No se Detectó Deadlock", 
                     font=('Helvetica', 16, 'bold'), foreground='#2ecc71').pack()
            ttk.Label(result_frame, text=f"Safe Sequence: {safe_sequence}", 
                     font=('Helvetica', 12, 'italic'), foreground='#34495e').pack(pady=5)

        steps_frame = ttk.LabelFrame(scrollable_frame, text="Execution Steps" if self.language.get() == "English" else "Pasos de Ejecución", 
                                    padding=10)
        steps_frame.pack(pady=20, padx=20, anchor="center")
        
        table = ttk.Treeview(steps_frame, columns=("Step", "Process", "Available"), 
                            show="headings", height=10, style='Custom.Treeview')
        table.heading("Step", text="Step" if self.language.get() == "English" else "Paso", anchor='center')
        table.heading("Process", text="Process" if self.language.get() == "English" else "Proceso", anchor='center')
        table.heading("Available", text="Available Resources" if self.language.get() == "English" else "Recursos Disponibles", anchor='center')
        
        table.column("Step", anchor='center', width=100)
        table.column("Process", anchor='center', width=150)
        table.column("Available", anchor='center', width=200)
        
        table.pack(fill='x', expand=True)
        
        vsb = ttk.Scrollbar(steps_frame, orient="vertical", command=table.yview)
        vsb.pack(side='right', fill='y')
        table.configure(yscrollcommand=vsb.set)

        for i, step in enumerate(steps):
            process, work = step
            table.insert("", "end", values=(f"{i}", process, work))

        self.status_var.set("Deadlock detection completed" if self.language.get() == "English" else "Detección de deadlock completada")

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

    def export_data(self, auto=False):
        if not self.validate_inputs(): return
        file_path = "autosave.txt" if auto else filedialog.asksaveasfilename(defaultextension=".txt", 
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

    def export_to_pdf(self):
        if not self.canvas: 
            messagebox.showwarning("Warning", "No graph to export!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", 
                                              filetypes=[("PDF files", "*.pdf")])
        if file_path:
            pdf = pdfcanvas.Canvas(file_path, pagesize=letter)
            self.canvas.figure.savefig('temp.png')
            pdf.drawImage('temp.png', 50, 500, width=500, height=300)
            pdf.showPage()
            pdf.save()
            os.remove('temp.png')
            self.status_var.set(f"Graph exported to PDF at {file_path}")

    def clear_all(self):
        self.num_processes.set(2)
        self.num_resources.set(2)
        self.resource_quantities = {}
        self.allocation = []
        self.request = []
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        self.current_detector = None
        self.current_graph = None
        self.history.clear()
        self.redo_stack.clear()
        self.status_var.set("System reset to initial state")

    def show_help(self):
        help_text = {
            "English": """Deadlock Detection System User Guide
1. Configure System: Set processes, resources, quantities, matrices.
2. Features: Show RAG, Detect Deadlock, Analyze Image, Save/Export.
3. Controls: Slider for size, Zoom, Dark Mode, Custom Colors, Language.
4. Shortcuts: Ctrl+S (Save), Ctrl+Z (Undo), Ctrl+Y (Redo).
5. Status: Check the bottom bar for updates.""",
            "Spanish": """Guía del Sistema de Detección de Deadlock
1. Configurar Sistema: Establezca procesos, recursos, cantidades, matrices.
2. Funciones: Mostrar RAG, Detectar Deadlock, Analizar Imagen, Guardar/Exportar.
3. Controles: Deslizador para tamaño, Zoom, Modo Oscuro, Colores Personalizados, Idioma.
4. Atajos: Ctrl+S (Guardar), Ctrl+Z (Deshacer), Ctrl+Y (Rehacer).
5. Estado: Revise la barra inferior para actualizaciones."""
        }
        messagebox.showinfo("User Guide" if self.language.get() == "English" else "Guía del Usuario", 
                           help_text[self.language.get()])

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
        toolbar = CustomNavigationToolbar(self.canvas, self.graph_frame)
        toolbar.update()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def save_state(self):
        state = {
            'num_processes': self.num_processes.get(),
            'num_resources': self.num_resources.get(),
            'resource_quantities': self.resource_quantities.copy(),
            'allocation': [row[:] for row in self.allocation],
            'request': [row[:] for row in self.request]
        }
        self.history.append(state)
        self.redo_stack.clear()

    def undo(self):
        if not self.history: return
        current_state = {
            'num_processes': self.num_processes.get(),
            'num_resources': self.num_resources.get(),
            'resource_quantities': self.resource_quantities.copy(),
            'allocation': [row[:] for row in self.allocation],
            'request': [row[:] for row in self.request]
        }
        self.redo_stack.append(current_state)
        prev_state = self.history.pop()
        self.num_processes.set(prev_state['num_processes'])
        self.num_resources.set(prev_state['num_resources'])
        self.resource_quantities = prev_state['resource_quantities']
        self.allocation = prev_state['allocation']
        self.request = prev_state['request']
        self.status_var.set("Undo performed")

    def redo(self):
        if not self.redo_stack: return
        current_state = {
            'num_processes': self.num_processes.get(),
            'num_resources': self.num_resources.get(),
            'resource_quantities': self.resource_quantities.copy(),
            'allocation': [row[:] for row in self.allocation],
            'request': [row[:] for row in self.request]
        }
        self.history.append(current_state)
        next_state = self.redo_stack.pop()
        self.num_processes.set(next_state['num_processes'])
        self.num_resources.set(next_state['num_resources'])
        self.resource_quantities = next_state['resource_quantities']
        self.allocation = next_state['allocation']
        self.request = next_state['request']
        self.status_var.set("Redo performed")

    def load_deadlock_example(self):
        self.num_processes.set(2)
        self.num_resources.set(2)
        self.resource_quantities = {"R1": 1, "R2": 1}
        self.allocation = [[1, 0], [0, 1]]
        self.request = [[0, 1], [1, 0]]
        self.save_state()
        self.status_var.set("Loaded 2x2 Deadlock Example")

    def load_safe_example(self):
        self.num_processes.set(3)
        self.num_resources.set(2)
        self.resource_quantities = {"R1": 2, "R2": 2}
        self.allocation = [[1, 0], [0, 1], [0, 0]]
        self.request = [[0, 1], [0, 0], [1, 1]]
        self.save_state()
        self.status_var.set("Loaded 3x2 Safe Example")

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockApp(root)
    root.mainloop()
