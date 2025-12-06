from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ChartsUI(ttk.Frame):
    def __init__(self, parent, data_fetcher):
        super().__init__(parent)
        self.get_data = data_fetcher
        self.canvas = None
        self.build_ui()

    def build_ui(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=(0, 6))

        ttk.Button(button_frame, text='Spending Over Time', command=self.show_line_chart).pack(side='left', padx=4)
        ttk.Button(button_frame, text='Category Breakdown', command=self.show_pie_chart).pack(side='left', padx=4)
        ttk.Button(button_frame, text='Income vs Expenses', command=self.show_bar_chart).pack(side='left', padx=4)

        self.figure_container = ttk.Frame(self)
        self.figure_container.pack(fill='both', expand=True)

    def display_chart(self, fig):
        # clear previous
        for widget in self.figure_container.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.figure_container)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()
        self.canvas = canvas

    def show_line_chart(self):
        year = 2025
        month = 11
        data = self.get_data('daily_totals', year, month)
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.plot(data['dates'], data['values'], marker='o')
        ax.set_title('Daily Totals')
        ax.set_xlabel('Day')
        ax.set_ylabel('Net amount')
        fig.tight_layout()
        self.display_chart(fig)

    def show_pie_chart(self):
        year = 2025
        month = 11
        data = self.get_data('categories', year, month)
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        if not data['values']:
            ax.text(0.5, 0.5, 'No category data', ha='center', va='center')
        else:
            ax.pie(data['values'], labels=data['labels'], autopct='%1.1f%%')
        ax.set_title('Spending by Category (abs values)')
        fig.tight_layout()
        self.display_chart(fig)

    def show_bar_chart(self):
        year = 2025
        month = 11
        data = self.get_data('income_expenses', year, month)
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.bar(['Income', 'Expenses'], [data['income'], data['expenses']])
        ax.set_title('Income vs Expenses')
        fig.tight_layout()
        self.display_chart(fig)
