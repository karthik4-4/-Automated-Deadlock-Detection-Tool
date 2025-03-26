from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

class CustomNavigationToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)
    toolitems = [
        ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    ]

    def __init__(self, canvas, parent, *, pack_toolbar=True):
        super().__init__(canvas, parent, pack_toolbar=pack_toolbar)