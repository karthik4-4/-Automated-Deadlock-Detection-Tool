import tkinter as tk
from tkinter import messagebox, simpledialog
import cv2
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle

class DeadlockDetector:
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_rag_manual(self, processes, resources, allocation, request, resource_quantities):
        """Build the RAG manually from user inputs."""
        self.graph.clear()
        # Add processes and resources to the graph
        for process in processes:
            self.graph.add_node(process, type='process')
        for resource in resources:
            self.graph.add_node(resource, type='resource', quantity=resource_quantities[resource])

        # Add edges for allocations and requests
        for i in range(len(processes)):
            for j in range(len(resources)):
                if allocation[i][j] > 0:
                    self.graph.add_edge(resources[j], processes[i], weight=allocation[i][j])  # Resource -> Process (allocation)
                if request[i][j] > 0:
                    self.graph.add_edge(processes[i], resources[j], weight=request[i][j])  # Process -> Resource (request)

    def build_rag_from_image(self, image):
        """Build the RAG from an uploaded image."""
        self.graph.clear()
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect circles (processes)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=50, param2=30, minRadius=10, maxRadius=50)
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for circle in circles[0, :]:
                x, y, r = circle
                self.graph.add_node(f"P{x}", type='process', pos=(x, y))

        # Detect rectangles (resources)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:  # Rectangle has 4 vertices
                x, y, w, h = cv2.boundingRect(approx)
                self.graph.add_node(f"R{x}", type='resource', quantity=1, pos=(x, y))  # Default quantity

        # Detect edges (allocations and requests)
        lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=50, minLineLength=10, maxLineGap=10)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # Find the nearest nodes for the line endpoints
                node1 = self.find_nearest_node(x1, y1)
                node2 = self.find_nearest_node(x2, y2)
                if node1 and node2:
                    self.graph.add_edge(node1, node2)

    def find_nearest_node(self, x, y):
        """Find the nearest node to the given coordinates."""
        min_dist = float('inf')
        nearest_node = None
        for node in self.graph.nodes:
            node_x, node_y = self.graph.nodes[node].get('pos', (0, 0))
            dist = np.sqrt((x - node_x) ** 2 + (y - node_y) ** 2)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
        return nearest_node

    def detect_deadlock(self):
        """Detect deadlock by finding cycles in the graph."""
        try:
            cycle = nx.find_cycle(self.graph, orientation="original")
            return True, cycle
        except nx.NetworkXNoCycle:
            return False, []

    def draw_rag(self):
        """Draw the RAG with processes as circles and resources as rectangles."""
        pos = nx.spring_layout(self.graph, seed=42)  # Use spring layout for better node positioning
        fig, ax = plt.subplots()

        # Draw processes as circles
        process_nodes = [node for node in self.graph.nodes if self.graph.nodes[node]['type'] == 'process']
        nx.draw_networkx_nodes(self.graph, pos, nodelist=process_nodes, node_shape='o', node_color='lightblue', node_size=3000, ax=ax)
        nx.draw_networkx_labels(self.graph, pos, labels={node: node for node in process_nodes}, font_size=10, font_weight='bold', ax=ax)

        # Draw resources as rectangles
        resource_nodes = [node for node in self.graph.nodes if self.graph.nodes[node]['type'] == 'resource']
        for node in resource_nodes:
            x, y = pos[node]
            rect = Rectangle((x - 0.1, y - 0.05), 0.2, 0.1, color='lightgreen', alpha=0.7)
            ax.add_patch(rect)
            ax.text(x, y, f"{node}\n({self.graph.nodes[node]['quantity']})", ha='center', va='center', fontsize=10, fontweight='bold')

        # Draw edges
        nx.draw_networkx_edges(self.graph, pos, edgelist=self.graph.edges, edge_color='black', width=1, arrows=True, ax=ax)

        ax.set_title("Resource Allocation Graph (RAG)")
        ax.axis('off')  # Hide axes
        return fig

class DeadlockApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # Hide the main window initially

        # Initialize deadlock detector
        self.detector = DeadlockDetector()

        # Prompt user to choose between manual entry and image upload
        self.choose_mode()

    def choose_mode(self):
        """Prompt the user to choose between manual entry and image upload."""
        self.mode_window = tk.Toplevel()
        self.mode_window.title("Choose Mode")
        self.mode_window.geometry("300x150")

        tk.Label(self.mode_window, text="Choose how to proceed:").pack(pady=10)
        tk.Button(self.mode_window, text="Manual Entry", command=self.manual_entry, bg="lightblue").pack(pady=5)
        tk.Button(self.mode_window, text="Upload RAG Image", command=self.upload_image, bg="lightgreen").pack(pady=5)

    def manual_entry(self):
        """Handle manual entry of processes, resources, allocation, and request."""
        self.mode_window.destroy()

        # Create a new window for manual entry
        self.manual_window = tk.Toplevel()
        self.manual_window.title("Manual Entry")
        self.manual_window.geometry("400x300")

        # Input: Number of processes and resources
        tk.Label(self.manual_window, text="Number of Processes:").grid(row=0, column=0, padx=10, pady=5)
        self.num_processes_entry = tk.Entry(self.manual_window)
        self.num_processes_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.manual_window, text="Number of Resources:").grid(row=1, column=0, padx=10, pady=5)
        self.num_resources_entry = tk.Entry(self.manual_window)
        self.num_resources_entry.grid(row=1, column=1, padx=10, pady=5)

        # Button to proceed to resource quantities
        tk.Button(self.manual_window, text="Next", command=self.enter_resource_quantities, bg="orange").grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    def enter_resource_quantities(self):
        """Input quantities for each resource."""
        try:
            num_processes = int(self.num_processes_entry.get())
            num_resources = int(self.num_resources_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for processes and resources.")
            return

        self.resource_quantities = {}
        for i in range(num_resources):
            quantity = simpledialog.askinteger("Input", f"Enter quantity for Resource R{i + 1}:")
            self.resource_quantities[f"R{i + 1}"] = quantity

        # Proceed to allocation and request matrices
        self.enter_allocation_matrix(num_processes, num_resources)

    def enter_allocation_matrix(self, num_processes, num_resources):
        """Input allocation matrix."""
        self.allocation = []
        for i in range(num_processes):
            row = simpledialog.askstring("Input", f"Enter allocation for Process P{i + 1} (space-separated):")
            self.allocation.append(list(map(int, row.split())))

        # Proceed to request matrix
        self.enter_request_matrix(num_processes, num_resources)

    def enter_request_matrix(self, num_processes, num_resources):
        """Input request matrix."""
        self.request = []
        for i in range(num_processes):
            row = simpledialog.askstring("Input", f"Enter request for Process P{i + 1} (space-separated):")
            self.request.append(list(map(int, row.split())))

        # Build the RAG
        processes = [f"P{i + 1}" for i in range(num_processes)]
        resources = [f"R{i + 1}" for i in range(num_resources)]
        self.detector.build_rag_manual(processes, resources, self.allocation, self.request, self.resource_quantities)

        # Show the RAG
        self.show_rag()

    def upload_image(self):
        """Handle uploading and processing of RAG image."""
        self.mode_window.destroy()
        self.root.deiconify()  # Show the main window

        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return

        # Load the image
        image = cv2.imread(file_path)
        if image is None:
            messagebox.showerror("Error", "Failed to load the image.")
            return

        # Build the RAG from the image
        self.detector.build_rag_from_image(image)

        # Show the RAG
        self.show_rag()

    def show_rag(self):
        """Display the RAG."""
        fig = self.detector.draw_rag()
        rag_window = tk.Toplevel(self.root)
        rag_window.title("Resource Allocation Graph (RAG)")
        canvas = FigureCanvasTkAgg(fig, master=rag_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def detect_deadlock(self):
        """Detect deadlock and show the result."""
        if not self.detector.graph.nodes:
            messagebox.showerror("Error", "No graph data available.")
            return

        deadlock, cycle = self.detector.detect_deadlock()
        if deadlock:
            messagebox.showinfo("Deadlock Detected", "The system is in a deadlock state.")
        else:
            messagebox.showinfo("No Deadlock Detected", "The system is in a safe state.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockApp(root)
    root.mainloop()