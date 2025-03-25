import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import sv_ttk  # For rounded buttons
import cv2  # OpenCV for image processing
import pytesseract  # For OCR
import re  # For text parsing
from PIL import Image  # For converting OpenCV images to Pillow images

# Configure the path to Tesseract (update this based on your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows example
# For Linux/macOS, it might be: /usr/local/bin/tesseract or /usr/bin/tesseract

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
        steps.append(("Initial", work.copy()))
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
        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(8, 6))  # Adjusted size to fit the layout

        # Define fixed positions for the nodes to match the image
        pos = {
            'P1': (0.2, 0.5),      # Left side
            'P2': (0.8, 0.8),      # Top-right
            'P3': (0.8, 0.2),      # Bottom-right
            'R1': (0.5, 0.65),     # Between P1 and P2, slightly above center
            'R2': (0.5, 0.35)      # Between P1 and P3, slightly below center
        }

        # Draw process nodes (circles)
        process_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'process']
        nx.draw_networkx_nodes(G, pos, nodelist=process_nodes, node_shape='o', 
                               node_color='white', edgecolors='black', node_size=1500, ax=ax)

        # Draw resource nodes (rectangles)
        resource_nodes = [node for node in G.nodes if G.nodes[node]['type'] == 'resource']
        nx.draw_networkx_nodes(G, pos, nodelist=resource_nodes, node_shape='s', 
                               node_color='white', edgecolors='black', node_size=1000, ax=ax)

        # Draw node labels (inside the nodes)
        labels = {node: node for node in G.nodes}
        nx.draw_networkx_labels(G, pos, labels, font_size=12, font_weight='bold', ax=ax)

        # Draw edges with arrows
        # Separate edges into "holding" (resource → process) and "waiting" (process → resource)
        holding_edges = [(u, v) for u, v in G.edges() if G.nodes[u]['type'] == 'resource']
        waiting_edges = [(u, v) for u, v in G.edges() if G.nodes[u]['type'] == 'process']

        # Draw "holding" edges (resource → process) with green labels
        for u, v in holding_edges:
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color='black', 
                                   width=2, arrows=True, arrowsize=20, ax=ax)
            # Add label for holding edge
            label = f"{v} is holding {u}"
            # Calculate the midpoint of the edge for label placement
            x = (pos[u][0] + pos[v][0]) / 2
            y = (pos[u][1] + pos[v][1]) / 2
            # Adjust label position slightly to avoid overlap
            if u == 'R1' and v == 'P1':
                x_offset, y_offset = -0.15, 0.05
            elif u == 'R2' and v == 'P2':
                x_offset, y_offset = 0.15, 0.05
            elif u == 'R2' and v == 'P3':
                x_offset, y_offset = 0.15, -0.05
            else:
                x_offset, y_offset = 0, 0
            ax.text(x + x_offset, y + y_offset, label, fontsize=10, color='green', 
                    ha='center', va='center')

        # Draw "waiting" edges (process → resource) with orange labels
        for u, v in waiting_edges:
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color='orange', 
                                   width=2, arrows=True, arrowsize=20, ax=ax)
            # Add label for waiting edge
            label = f"{u} is waiting for {v}"
            # Calculate the midpoint of the edge for label placement
            x = (pos[u][0] + pos[v][0]) / 2
            y = (pos[u][1] + pos[v][1]) / 2
            # Adjust label position slightly to avoid overlap
            if u == 'P1' and v == 'R2':
                x_offset, y_offset = -0.15, -0.05
            elif u == 'P2' and v == 'R1':
                x_offset, y_offset = 0.15, -0.05
            else:
                x_offset, y_offset = 0, 0
            ax.text(x + x_offset, y + y_offset, label, fontsize=10, color='orange', 
                    ha='center', va='center')

        # Remove grid, title, and axis
        ax.axis('off')

        return fig

    def draw_allocation_table(self):
        fig, ax = plt.subplots(figsize=(8, 4))  # Adjusted size for a compact layout
        ax.axis('off')

        # Combine Allocation and Request data into a single table
        allocation_data = np.array(self.allocation)
        request_data = np.array(self.request)
        combined_data = np.hstack((allocation_data, request_data))

        # Create the data for the table (excluding the header)
        row_data = []
        for i in range(len(self.processes)):
            row = [self.processes[i]] + list(allocation_data[i]) + list(request_data[i])
            row_data.append(row)

        # Create the table with only the data (no column labels yet)
        col_widths = [0.15] + [0.1] * (len(self.resources) * 2)  # Widths for "Process" and resource columns
        table = ax.table(cellText=row_data, loc='center', cellLoc='center',
                         colWidths=col_widths, bbox=[0.1, 0.1, 0.8, 0.5])
        table.auto_set_font_size(False)
        table.set_fontsize(10)

        # Add "Process" label on the left (vertically aligned, green)
        ax.text(0.05, 0.35, "Process", fontsize=10, fontweight='bold', rotation=90, color='green', va='center')

        # Add "Allocation" and "Request" titles above the respective sections
        ax.text(0.35, 0.75, "Allocation", fontsize=12, fontweight='bold', ha='center')
        ax.text(0.65, 0.75, "Request", fontsize=12, fontweight='bold', ha='center')

        # Add "Resource" labels below "Allocation" and "Request"
        ax.text(0.35, 0.65, "Resource", fontsize=10, fontweight='bold', ha='center')
        ax.text(0.65, 0.65, "Resource", fontsize=10, fontweight='bold', ha='center')

        # Add resource labels (R1, R2, etc.) below the "Resource" labels
        for i in range(len(self.resources)):
            # Allocation section
            ax.text(0.25 + (i + 1) * 0.1, 0.55, self.resources[i], fontsize=10, ha='center')
            # Request section
            ax.text(0.55 + (i + 1) * 0.1, 0.55, self.resources[i], fontsize=10, ha='center')

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
        self.root.configure(bg='#aab7b8')

        self.num_processes = tk.IntVar(value=1)
        self.num_resources = tk.IntVar(value=1)
        self.resource_quantities = {}
        self.allocation = []
        self.request = []

        # To store the analyzed data from the image
        self.image_analyzed = False
        self.analyzed_processes = []
        self.analyzed_resources = []
        self.analyzed_allocation = []
        self.analyzed_request = []
        self.analyzed_resource_quantities = {}

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
                quantity = simpledialog.askinteger("Input", f"Resource R{i + 1} Quantity:", minvalue=0, parent=self.root)
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

    def analyze_rag_image(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not file_path:
            return

        try:
            # Load the image using OpenCV
            image = cv2.imread(file_path)
            if image is None:
                messagebox.showerror("Error", "Could not load the image.")
                return

            # Preprocess the image to improve detection
            # Resize the image to make shapes larger (optional, adjust scale as needed)
            scale_factor = 2
            image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            # Enhance contrast
            gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

            # Apply adaptive thresholding to create a binary image
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 2)

            # 1. Detect circles (processes) using HoughCircles
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, dp=1, minDist=30,  # Reduced minDist to detect closer circles
                param1=50, param2=20,  # Lowered param2 for more sensitivity
                minRadius=10, maxRadius=50  # Adjusted radius range
            )

            processes = []
            process_positions = {}
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                print(f"Detected {len(circles)} circles (processes)")
                for i, (x, y, r) in enumerate(circles):
                    # Extract the region around the circle for OCR
                    y_min = max(0, y - r - 20)
                    y_max = y + r + 20
                    x_min = max(0, x - r - 20)
                    x_max = x + r + 20
                    if y_max <= y_min or x_max <= x_min:
                        print(f"Skipping invalid circle ROI at index {i}: ({x_min}, {y_min}, {x_max}, {y_max})")
                        continue  # Skip invalid regions
                    roi = image[y_min:y_max, x_min:x_max]
                    if roi.size == 0:
                        print(f"Skipping empty circle ROI at index {i}")
                        continue  # Skip empty regions

                    # Convert BGR to RGB for Pillow/Tesseract
                    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
                    # Convert to Pillow image
                    roi_pil = Image.fromarray(roi_rgb)
                    # Resize ROI to improve OCR accuracy
                    roi_pil = roi_pil.resize((roi_pil.width * 2, roi_pil.height * 2), Image.Resampling.LANCZOS)
                    text = pytesseract.image_to_string(roi_pil, config='--psm 6').strip()
                    print(f"Circle {i} OCR result: {text}")
                    if text.startswith('P'):
                        process_name = f"P{i+1}"
                        processes.append(process_name)
                        process_positions[process_name] = (x, y)

            # 2. Detect rectangles (resources) using contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            resources = []
            resource_positions = {}
            resource_quantities = {}
            for idx, contour in enumerate(contours):
                # Approximate the contour to a polygon
                approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                if len(approx) == 4:  # Rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    # Ensure valid dimensions
                    if w <= 0 or h <= 0:
                        print(f"Skipping invalid rectangle at index {idx}: w={w}, h={h}")
                        continue
                    # Extract the region for OCR
                    roi = image[y:y+h, x:x+w]
                    if roi.size == 0:
                        print(f"Skipping empty rectangle ROI at index {idx}")
                        continue  # Skip empty regions

                    # Convert BGR to RGB for Pillow/Tesseract
                    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
                    # Convert to Pillow image
                    roi_pil = Image.fromarray(roi_rgb)
                    # Resize ROI to improve OCR accuracy
                    roi_pil = roi_pil.resize((roi_pil.width * 2, roi_pil.height * 2), Image.Resampling.LANCZOS)
                    text = pytesseract.image_to_string(roi_pil, config='--psm 6').strip()
                    print(f"Rectangle {idx} OCR result: {text}")
                    if text.startswith('R'):
                        resource_name = text
                        resources.append(resource_name)
                        resource_positions[resource_name] = (x + w//2, y + h//2)

                        # Count dots inside the rectangle to determine quantity
                        roi_binary = binary[y:y+h, x:x+w]
                        dot_contours, _ = cv2.findContours(roi_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        dot_count = 0
                        for dot in dot_contours:
                            area = cv2.contourArea(dot)
                            if 5 < area < 50:  # Adjust based on dot size
                                dot_count += 1
                        resource_quantities[resource_name] = dot_count

            # 3. Detect arrows and their labels using edge detection and OCR
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=30, minLineLength=20, maxLineGap=10)

            allocation_edges = []  # (resource, process)
            request_edges = []    # (process, resource)
            if lines is not None:
                print(f"Detected {len(lines)} lines (arrows)")
                for idx, line in enumerate(lines):
                    x1, y1, x2, y2 = line[0]
                    # Extract the region around the line for OCR
                    y_min = max(0, min(y1, y2) - 20)
                    y_max = max(y1, y2) + 20
                    x_min = max(0, min(x1, x2) - 20)
                    x_max = max(x1, x2) + 20
                    if y_max <= y_min or x_max <= x_min:
                        print(f"Skipping invalid line ROI at index {idx}: ({x_min}, {y_min}, {x_max}, {y_max})")
                        continue  # Skip invalid regions
                    roi = image[y_min:y_max, x_min:x_max]
                    if roi.size == 0:
                        print(f"Skipping empty line ROI at index {idx}")
                        continue  # Skip empty regions

                    # Convert BGR to RGB for Pillow/Tesseract
                    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
                    # Convert to Pillow image
                    roi_pil = Image.fromarray(roi_rgb)
                    # Resize ROI to improve OCR accuracy
                    roi_pil = roi_pil.resize((roi_pil.width * 2, roi_pil.height * 2), Image.Resampling.LANCZOS)
                    text = pytesseract.image_to_string(roi_pil, config='--psm 6').strip()
                    print(f"Line {idx} OCR result: {text}")

                    # Parse the text to determine if it's an allocation or request
                    allocation_match = re.match(r"(P\d+) is holding (R\d+)", text)
                    request_match = re.match(r"(P\d+) is waiting for (R\d+)", text)

                    if allocation_match:
                        process, resource = allocation_match.groups()
                        allocation_edges.append((resource, process))
                    elif request_match:
                        process, resource = request_match.groups()
                        request_edges.append((process, resource))

            # 4. Build the allocation and request matrices
            processes.sort()  # Ensure consistent ordering: P1, P2, P3, ...
            resources.sort()  # Ensure consistent ordering: R1, R2, ...

            print(f"Processes detected: {processes}")
            print(f"Resources detected: {resources}")

            if not processes or not resources:
                messagebox.showerror("Error", "No processes or resources detected in the image.")
                return

            # Initialize matrices
            allocation = [[0 for _ in resources] for _ in processes]
            request = [[0 for _ in resources] for _ in processes]

            # Fill allocation matrix (resource → process)
            for resource, process in allocation_edges:
                if process in processes and resource in resources:
                    p_idx = processes.index(process)
                    r_idx = resources.index(resource)
                    allocation[p_idx][r_idx] = 1  # Assume 1 instance per allocation for simplicity

            # Fill request matrix (process → resource)
            for process, resource in request_edges:
                if process in processes and resource in resources:
                    p_idx = processes.index(process)
                    r_idx = resources.index(resource)
                    request[p_idx][r_idx] = 1  # Assume 1 instance per request

            # 5. Adjust resource quantities based on allocation
            for r_idx, resource in enumerate(resources):
                allocated_count = sum(allocation[p_idx][r_idx] for p_idx in range(len(processes)))
                resource_quantities[resource] = max(resource_quantities.get(resource, 1), allocated_count)

            # Store the analyzed data
            self.analyzed_processes = processes
            self.analyzed_resources = resources
            self.analyzed_allocation = allocation
            self.analyzed_request = request
            self.analyzed_resource_quantities = resource_quantities

            # Set the flag to indicate that an image has been analyzed
            self.image_analyzed = True
            self.status_var.set("Analysis completed")

        except pytesseract.TesseractNotFoundError:
            messagebox.showerror(
                "Error",
                "Tesseract OCR is not installed or the path is incorrect.\n"
                "Please install Tesseract and ensure the path in the code is correct.\n"
                "Expected path: C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze the image: {str(e)}")

    def detect_deadlock(self):
        # Check if an image has been analyzed
        if self.image_analyzed:
            # Use the analyzed data from the image
            detector = DeadlockDetector(
                self.analyzed_processes,
                self.analyzed_resources,
                self.analyzed_allocation,
                self.analyzed_request,
                self.analyzed_resource_quantities
            )
        else:
            # Use manually entered data if no image has been analyzed
            if not self.validate_inputs():
                return
            detector = self.create_detector()

        # Perform deadlock detection
        deadlock, safe_sequence, steps = detector.detect_deadlock()

        # Create a new window to display the table and explanation
        result_window = tk.Toplevel(self.root)
        result_window.title("Deadlock Detection Result")
        result_window.geometry("800x600")
        result_window.configure(bg='#f5f5f5')

        # Display the Resource Allocation Table
        fig = detector.draw_allocation_table()
        canvas = FigureCanvasTkAgg(fig, master=result_window)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)

        # Display the result
        if deadlock:
            result_label = ttk.Label(result_window, text="Deadlock Detected!", font=('Helvetica', 14, 'bold'), background='#f5f5f5')
            result_label.pack(pady=10)
        else:
            result_label = ttk.Label(result_window, text=f"No Deadlock. Safe Sequence: {safe_sequence}", font=('Helvetica', 14, 'bold'), background='#f5f5f5')
            result_label.pack(pady=10)

        # Display the steps in a table format
        steps_frame = ttk.Frame(result_window)
        steps_frame.pack(pady=10)

        # Create a table to display the steps
        table = ttk.Treeview(steps_frame, columns=("Step", "Process", "Available"), show="headings")
        table.heading("Step", text="Step")
        table.heading("Process", text="Process")
        table.heading("Available", text="Available Resources")
        table.pack()

        # Add the steps to the table
        for i, step in enumerate(steps):
            process, work = step
            table.insert("", "end", values=(f"{i}", process, work))

        self.status_var.set("Deadlock detection completed")

    def save_graph(self):
        if not self.canvas: 
            messagebox.showwarning("Warning", "No graph to save!")
            return
        file_path = tk.filedialog.asksaveasfilename(defaultextension=".png",filetypes=[("PNG files", "*.png")])
        if file_path:
            self.canvas.figure.savefig(file_path)
            self.status_var.set(f"Graph saved to {file_path}")

    def clear_all(self):
        self.num_processes.set(2)
        self.num_resources.set(2)
        self.resource_quantities = {}
        self.allocation = []
        self.request = []
        self.image_analyzed = False
        self.analyzed_processes = []
        self.analyzed_resources = []
        self.analyzed_allocation = []
        self.analyzed_request = []
        self.analyzed_resource_quantities = {}
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