import tkinter as tk
from tkinter import ttk
from Investment import InvestmentApp  # Import the InvestmentApp


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Finance Flow")
        self.geometry("1500x1000")
        self.current_frame = None
        self.user_data = {}  # Store all user info and month data
        self.current_month_index = 0  # Start month index
        self.months = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        self.show_welcome()

    def switch(self, new_frame):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack(expand=True, fill="both")

    def center_widget(self, widget):
        widget.pack(pady=20)

    def show_welcome(self):
        frame = ttk.Frame(self)
        label = tk.Label(frame, text="Welcome to Finance Flow!", font=("Arial", 36))
        self.center_widget(label)
        btn = tk.Button(frame, text="Begin", font=("Arial", 24), command=self.show_first_name)
        self.center_widget(btn)
        self.switch(frame)

    def show_first_name(self):
        frame = ttk.Frame(self)
        tk.Label(frame, text="Enter First Name:", font=("Arial", 28)).pack(pady=10)
        entry = ttk.Entry(frame, font=("Arial", 24))
        entry.pack(pady=10)
        tk.Button(frame, text="Next", font=("Arial", 20),
                  command=lambda: self.save_and_next(entry.get(), 'first_name', self.show_last_name)).pack(pady=20)
        self.switch(frame)

    def show_last_name(self):
        frame = ttk.Frame(self)
        tk.Label(frame, text="Enter Last Name:", font=("Arial", 28)).pack(pady=10)
        entry = ttk.Entry(frame, font=("Arial", 24))
        entry.pack(pady=10)
        tk.Button(frame, text="Next", font=("Arial", 20),
                  command=lambda: self.save_and_next(entry.get(), 'last_name', self.show_start_month)).pack(pady=20)
        self.switch(frame)

    def show_start_month(self):
        frame = ttk.Frame(self)
        tk.Label(frame, text="Enter Starting Month (e.g., January):", font=("Arial", 28)).pack(pady=10)
        entry = ttk.Entry(frame, font=("Arial", 24))
        entry.pack(pady=10)
        tk.Button(frame, text="Next", font=("Arial", 20),
                  command=lambda: self.save_month(entry.get())).pack(pady=20)
        self.switch(frame)

    def save_month(self, month_name):
        month_name = month_name.strip().capitalize()
        if month_name in self.months:
            self.current_month_index = self.months.index(month_name)
        else:
            self.current_month_index = 0  # default to January if invalid
        self.show_calendar()

    def show_calendar(self):
        frame = ttk.Frame(self)

        # Top navigation and month label
        top_frame = ttk.Frame(frame)
        top_frame.pack(pady=10, fill='x')
        tk.Button(top_frame, text='<<', font=("Arial", 16),
                  command=lambda: self.change_month(-1)).pack(side='left', padx=20)
        self.current_month_name = self.months[self.current_month_index % 12]
        month_label = tk.Label(top_frame, text=f"{self.current_month_name}", font=("Arial", 28))
        month_label.pack(side='left', expand=True)
        tk.Button(top_frame, text='>>', font=("Arial", 16),
                  command=lambda: self.change_month(1)).pack(side='right', padx=20)

        # Total balance at top
        self.total_balance_label = tk.Label(frame, text="Total: $0", font=("Arial", 22))
        self.total_balance_label.pack(pady=5)

        # Initialize month data if not exists
        if self.current_month_name not in self.user_data:
            self.user_data[self.current_month_name] = {day: [] for day in range(1, 32)}

        # Days grid
        self.days_frame = ttk.Frame(frame)
        self.days_frame.pack(pady=10, fill='both', expand=True)
        self.day_buttons = {}
        for day in range(1, 32):
            btn = tk.Button(self.days_frame, text=self.get_day_text(self.current_month_name, day),
                            width=15, height=6, justify='left', anchor='nw',
                            command=lambda d=day: self.edit_day(self.current_month_name, d))
            row = (day - 1) // 7
            col = (day - 1) % 7
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            self.days_frame.grid_rowconfigure(row, weight=1)
            self.days_frame.grid_columnconfigure(col, weight=1)
            self.day_buttons[day] = btn

        # Bottom summary and extra buttons
        bottom_frame = ttk.Frame(frame)
        bottom_frame.pack(pady=10, fill='x')

        self.total_income_label = tk.Label(bottom_frame, text="Total Made: $0", font=("Arial", 20))
        self.total_income_label.pack(side='left', padx=20)
        self.total_expense_label = tk.Label(bottom_frame, text="Total Expenses: $0", font=("Arial", 20))
        self.total_expense_label.pack(side='right', padx=20)

        # Additional buttons - UPDATED TO USE REAL FUNCTIONS
        extra_frame = ttk.Frame(frame)
        extra_frame.pack(pady=10)

        # Investments button now opens the Investment Tracker
        tk.Button(extra_frame, text="Investment Tracker", font=("Arial", 18),
                  width=20, height=2, command=self.show_investment_tracker).pack(side='left', padx=20)

        # Visual Charts button (for future development)
        tk.Button(extra_frame, text="Visual Charts", font=("Arial", 18),
                  width=20, height=2, command=lambda: self.show_white_screen("Charts Coming Soon!")).pack(side='right',
                                                                                                          padx=20)

        self.update_summary()
        self.switch(frame)

    def show_investment_tracker(self):
        """Open the Investment Tracker in a new window"""
        investment_window = tk.Toplevel(self)
        investment_window.title("Investment Tracker")
        investment_window.geometry("1200x750")

        # Create the InvestmentApp in this new window
        investment_app = InvestmentApp(investment_window)

        # Add a back button
        back_btn = tk.Button(investment_window, text="Back to Calendar",
                             font=("Arial", 12), command=investment_window.destroy)
        back_btn.pack(side=tk.BOTTOM, pady=10)

    def show_white_screen(self, message="Feature Coming Soon!"):
        """Show a placeholder screen for future features"""
        frame = tk.Frame(self, bg='white')

        # Add message
        msg_label = tk.Label(frame, text=message, font=("Arial", 24), bg='white')
        msg_label.pack(expand=True, pady=50)

        # Back button
        back_btn = tk.Button(frame, text="Back", font=("Arial", 18),
                             command=self.show_calendar)
        back_btn.pack(side='bottom', pady=20)

        self.switch(frame)

    def change_month(self, direction):
        self.current_month_index = (self.current_month_index + direction) % 12
        self.show_calendar()

    def get_day_text(self, month, day):
        notes = self.user_data[month].get(day, [])
        return f"{day}\n" + "\n".join(notes)

    def edit_day(self, month, day):
        win = tk.Toplevel(self)
        win.title(f"Edit Day {day}")
        win.geometry("350x350")
        tk.Label(win, text=f"Day {day} Notes:", font=("Arial", 16)).pack(pady=5)
        text = tk.Text(win, height=10, font=("Arial", 14))
        existing = "\n".join(self.user_data[month][day])
        text.insert("1.0", existing)
        text.pack(pady=10)
        tk.Button(win, text="Save", font=("Arial", 14),
                  command=lambda: self.save_day_notes(win, month, day, text)).pack(pady=5)

    def save_day_notes(self, win, month, day, text_widget):
        content = text_widget.get("1.0", tk.END).strip().split("\n")
        self.user_data[month][day] = [c for c in content if c.strip()]
        self.day_buttons[day].config(text=self.get_day_text(month, day))
        self.update_summary()
        win.destroy()

    def update_summary(self):
        total_income = 0
        total_expense = 0
        month = self.current_month_name
        for notes in self.user_data[month].values():
            for line in notes:
                if line.startswith('+'):
                    try:
                        total_income += float(line.split()[0][1:])
                    except:
                        pass
                elif line.startswith('-'):
                    try:
                        total_expense += float(line.split()[0][1:])
                    except:
                        pass
        self.total_balance_label.config(text=f"Total: ${total_income - total_expense}")
        self.total_income_label.config(text=f"Total Made: ${total_income}")
        self.total_expense_label.config(text=f"Total Expenses: ${total_expense}")

    def save_and_next(self, value, key, next_screen):
        self.user_data[key] = value
        next_screen()


if __name__ == "__main__":
    app = App()
    app.mainloop()