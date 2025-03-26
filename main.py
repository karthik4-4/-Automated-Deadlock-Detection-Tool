import tkinter as tk
from deadlock_app import DeadlockApp

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockApp(root)
    root.mainloop()