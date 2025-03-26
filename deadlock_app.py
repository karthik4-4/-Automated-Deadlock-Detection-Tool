import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sv_ttk
import os
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdfcanvas
import threading
from deadlock_detector import DeadlockDetector
from custom_toolbar import CustomNavigationToolbar
from matrix_dialog import MatrixDialog
import matplotlib.pyplot as plt
import hashlib

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
        self.toolbar = None  # Track the toolbar
        self.current_fig = None  # Track the current Matplotlib figure
        self.last_graph_hash = None  # Track the hash of the last graph data
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

        style.configure('TButton', font=('Helvetica', 10), background='#E8ECEF', foreground='#333333', bordercolor='#D3D3D3', relief='flat', padding=8)
        style.map('TButton', background=[('active', '#D3D3D3'), ('!disabled', '#E8ECEF')], foreground=[('active', '#333333'), ('!disabled', '#333333')])

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
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.num_processes, width=5).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="?", command=lambda: messagebox.showinfo("Help","Set the number of processes (1-10)."), style='Help.TButton').grid(row=0, column=2)

        ttk.Label(config_frame, text="Resources:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.num_resources, width=5).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="?", command=lambda: messagebox.showinfo("Help", "Set the number of resources (1-10)."), style='Help.TButton').grid(row=1, column=2)

        ttk.Label(config_frame, text="Examples:").grid(row=2, column=0, padx=5, pady=5)
        examples = {"Custom": None, "Deadlock 2x2": self.load_deadlock_example, "Safe 3x2": self.load_safe_example}
        self.example_combobox = ttk.Combobox(config_frame, values=list(examples.keys()), state="readonly", width=10)
        self.example_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.example_combobox.set("Custom")
        ttk.Button(config_frame, text="Load", command=lambda: examples[self.example_combobox.get()]() if examples[self.example_combobox.get()] else None).grid(row=2, column=2)

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
        ttk.Label(status_frame, textvariable=self.status_var, background='#dfe6e9').pack(fill='x')

        self.graph_frame = ttk.Frame(self.right_frame)
        self.graph_frame.pack(fill='both', expand=True, padx=10, pady=10)

        toolbar = ttk.Frame(self.right_frame)
        toolbar.pack(fill='x', pady=5, padx=10)
        
        self.size_slider = ttk.Scale(toolbar, from_=1, to=10, orient='horizontal', command=self.update_size)
        self.size_slider.set(5)
        self.size_slider.pack(side='left', padx=5)
        ttk.Label(toolbar, text="Graph Size").pack(side='left', padx=5)
        
        ttk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side='right', padx=5)
        ttk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side='right', padx=5)
        
        ttk.Label(toolbar, text="Language:").pack(side='left', padx=5)
        ttk.Combobox(toolbar, textvariable=self.language, values=["English", "Spanish"], width=10, state="readonly").pack(side='left', padx=5)

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
                label = ttk.Label(tooltip, text=text, background="#ffffe0", relief='solid', borderwidth=1)
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

    def compute_graph_hash(self):
        """Compute a hash of the current graph data to detect changes."""
        data = (
            str(self.num_processes.get()),
            str(self.num_resources.get()),
            str(sorted(self.resource_quantities.items())),
            str(self.allocation),
            str(self.request),
            str(sorted(self.colors.items())),
            str(self.size_slider.get())  # Include size factor in the hash
        )
        return hashlib.md5("".join(data).encode()).hexdigest()

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
        if not self.validate_inputs():
            return

        # Compute the hash of the current graph data
        current_hash = self.compute_graph_hash()

        # If the graph data hasn't changed and we already have a figure, do nothing
        if self.last_graph_hash == current_hash and self.current_fig is not None:
            self.status_var.set("Graph already displayed")
            return

        # Update the last hash
        self.last_graph_hash = current_hash

        # Generate the new graph
        self.current_detector = self.create_detector()
        self.current_graph = self.current_detector.build_rag()

        size_factor = self.size_slider.get()
        total_nodes = len(self.current_graph.nodes)
        base_size = max(4, min(8, total_nodes * 0.5))
        figsize = (base_size * size_factor / 5, base_size * size_factor / 5)
        fig = self.current_detector.draw_rag(self.current_graph, figsize=figsize, **self.colors)

        # Display the new figure and update the current figure reference
        self.display_rag(fig)
        self.status_var.set("Displaying Resource Allocation Graph")

    def detect_deadlock(self):
        if not self.validate_inputs():
            return
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
        ttk.Label(header_frame, text="Deadlock Detection Result", font=('Helvetica', 18, 'bold'), foreground='#2c3e50').pack()

        fig = detector.draw_allocation_table()
        canvas_widget = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(pady=10, padx=10, anchor="center")

        result_frame = ttk.Frame(scrollable_frame, padding="10")
        result_frame.pack(pady=20, anchor="center")
        if deadlock:
            ttk.Label(result_frame, text="⚠ Deadlock Detected!" if self.language.get() == "English" else "¡Deadlock Detectado!", font=('Helvetica', 16, 'bold'), foreground='#e74c3c').pack()
        else:
            ttk.Label(result_frame, text="✓ No Deadlock Detected" if self.language.get() == "English" else "✓ No se Detectó Deadlock", font=('Helvetica', 16, 'bold'), foreground='#2ecc71').pack()
            ttk.Label(result_frame, text=f"Safe Sequence: {safe_sequence}", font=('Helvetica', 12, 'italic'), foreground='#34495e').pack(pady=5)

        steps_frame = ttk.LabelFrame(scrollable_frame, text="Execution Steps" if self.language.get() == "English" else "Pasos de Ejecución", padding=10)
        steps_frame.pack(pady=20, padx=20, anchor="center")
        
        table = ttk.Treeview(steps_frame, columns=("Step", "Process", "Available"), show="headings", height=10, style='Custom.Treeview')
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
        if not file_path:
            return
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
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            self.canvas.figure.savefig(file_path)
            self.status_var.set(f"Graph saved to {file_path}")

    def export_data(self, auto=False):
        if not self.validate_inputs():
            return
        file_path = "autosave.txt" if auto else filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
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
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
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
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None
        if self.current_fig:
            plt.close(self.current_fig)
            self.current_fig = None
        self.current_detector = None
        self.current_graph = None
        self.last_graph_hash = None
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
        messagebox.showinfo("User Guide" if self.language.get() == "English" else "Guía del Usuario", help_text[self.language.get()])

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
        # Close the previous figure if it exists
        if self.current_fig:
            plt.close(self.current_fig)

        # If the canvas doesn't exist, create it
        if not self.canvas:
            self.canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            self.canvas.draw()
            # Create the toolbar only if it doesn't exist
            if not self.toolbar:
                self.toolbar = CustomNavigationToolbar(self.canvas, self.graph_frame)
                self.toolbar.update()
            self.canvas.get_tk_widget().pack(fill='both', expand=True)
        else:
            # Update the existing canvas with the new figure
            self.canvas.figure = fig
            self.canvas.draw()

        # Update the current figure reference
        self.current_fig = fig

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
        # Invalidate the graph hash since the state has changed
        self.last_graph_hash = None

    def undo(self):
        if not self.history:
            return
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
        # Invalidate the graph hash since the state has changed
        self.last_graph_hash = None

    def redo(self):
        if not self.redo_stack:
            return
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
        # Invalidate the graph hash since the state has changed
        self.last_graph_hash = None

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