import tkinter as tk
from tkinter import ttk, messagebox

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
        ttk.Label(header_frame, text=f"Enter {self.matrix_type} Matrix",style='Header.TLabel').pack(side='left')
        ttk.Button(header_frame, text="?", command=lambda: messagebox.showinfo("Help",f"Enter non-negative integers for each process-resource pair in the {self.matrix_type} matrix."),style='Help.TButton').pack(side='right')

        entry_frame = ttk.Frame(frame)
        entry_frame.pack(pady=10)
        
        ttk.Label(entry_frame, text="Process").grid(row=0, column=0, padx=5, pady=5)
        for j in range(self.num_resources):ttk.Label(entry_frame, text=f"R{j+1}").grid(row=0, column=j+1, padx=5, pady=5)
            
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