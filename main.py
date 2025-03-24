import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DeadlockDetector:
    def __init__(self):
        self.graph = nx.DiGraph()

    def detect_deadlock(self):
        """Detect deadlock by finding cycles in the graph."""
        try:
            cycle = nx.find_cycle(self.graph, orientation="original")
            return True, cycle
        except nx.NetworkXNoCycle:
            return False, []

    def draw_graph(self):
        """Draw the graph with processes as circles and resources as rectangles."""
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
            rect = plt.Rectangle((x - 0.1, y - 0.05), 0.2, 0.1, color='lightgreen', alpha=0.7)
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
        self.root.title("Deadlock Detection System")
        self.root.geometry("400x300")  # Set window size

        # Initialize deadlock detector
        self.detector = DeadlockDetector()

        # Create UI elements
        self.create_buttons()

    def create_buttons(self):
        """Create buttons for actions."""
        tk.Button(self.root, text="Upload RAG Image", command=self.upload_image, bg="lightgreen").grid(row=0, column=0, padx=10, pady=10)
        tk.Button(self.root, text="Detect Deadlock", command=self.detect_deadlock, bg="orange").grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self.root, text="Exit", command=self.root.quit, bg="red", fg="white").grid(row=1, column=0, columnspan=2, padx=10, pady=10)

    def upload_image(self):
        """Upload and process the RAG image."""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return

        # Load the image
        image = cv2.imread(file_path)
        if image is None:
            messagebox.showerror("Error", "Failed to load the image.")
            return

        # Process the image to detect nodes and edges
        self.process_image(image)

    def process_image(self, image):
        """Process the image to detect nodes and edges."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect circles (processes)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=50, param2=30, minRadius=10, maxRadius=50)
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for circle in circles[0, :]:
                x, y, r = circle
                self.detector.graph.add_node(f"P{x}", type='process')

        # Detect rectangles (resources)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:  # Rectangle has 4 vertices
                x, y, w, h = cv2.boundingRect(approx)
                self.detector.graph.add_node(f"R{x}", type='resource', quantity=1)  # Default quantity

        # Detect edges (allocations and requests)
        lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=50, minLineLength=10, maxLineGap=10)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # Find the nearest nodes for the line endpoints
                node1 = self.find_nearest_node(x1, y1)
                node2 = self.find_nearest_node(x2, y2)
                if node1 and node2:
                    self.detector.graph.add_edge(node1, node2)

        # Display the processed graph
        fig = self.detector.draw_graph()
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Processed RAG")
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def find_nearest_node(self, x, y):
        """Find the nearest node to the given coordinates."""
        min_dist = float('inf')
        nearest_node = None
        for node in self.detector.graph.nodes:
            node_x, node_y = self.detector.graph.nodes[node].get('pos', (0, 0))
            dist = np.sqrt((x - node_x) ** 2 + (y - node_y) ** 2)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
        return nearest_node

    def detect_deadlock(self):
        """Detect deadlock and show the result."""
        if not self.detector.graph.nodes:
            messagebox.showerror("Error", "Please upload a RAG image first.")
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