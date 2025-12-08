import tkinter as tk
from tkinter import ttk
from Investment import InvestmentApp  # Import the InvestmentApp
from calendar_ui import CalendarUI  # Import CalendarUI
from charts_ui import ChartsUI  # Import ChartsUI
import data_fetch  # Import for data fetching


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

    def show_welcome(self):
        frame = ttk.Frame(self)
        frame.pack(expand=True, fill="both")

        label = tk.Label(frame, text="Welcome to Finance Flow!", font=("Arial", 36))
        label.pack(pady=20)

        btn = tk.Button(frame, text="Begin", font=("Arial", 24), command=self.show_first_name)
        btn.pack(pady=20)

        self.switch(frame)

    def switch(self, new_frame):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack(expand=True, fill="both")

    def center_widget(self, widget):
        widget.pack(pady=20)

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
        from datetime import datetime
        current_month = datetime.now().strftime("%B")  # Get the current month name
        self.save_month(current_month)  # Automatically save the current month

    def save_month(self, month_name):
        month_name = month_name.strip().capitalize()
        if month_name in self.months:
            self.current_month_index = self.months.index(month_name)
        else:
            self.current_month_index = 0  # default to January if invalid
        self.show_calendar()

    def show_calendar(self):
        frame = ttk.Frame(self)

        # Top frame for totals
        top_frame = ttk.Frame(frame)
        top_frame.pack(pady=10, fill='x')

        self.total_income_label = tk.Label(top_frame, text="Total Made: $0", font=("Arial", 20))
        self.total_income_label.pack(side='left', padx=20)

        self.total_balance_label = tk.Label(top_frame, text="Total: $0", font=("Arial", 22))
        self.total_balance_label.pack(side='top', padx=20)

        self.total_expense_label = tk.Label(top_frame, text="Total Expenses: $0", font=("Arial", 20))
        self.total_expense_label.pack(side='right', padx=20)

        # Calendar in the middle
        calendar_ui = CalendarUI(frame, data_fetch.get_transactions_for_day)
        calendar_ui.pack(fill='both', expand=True, pady=40)
        frame.calendar_ui = calendar_ui

        # Additional buttons at the bottom
        extra_frame = ttk.Frame(frame)
        extra_frame.pack(pady=10)

        tk.Button(extra_frame, text="Investment Tracker", font=("Arial", 18),
                  width=20, height=2, command=self.show_investment_tracker).pack(side='left', padx=20)

        tk.Button(extra_frame, text="Visual Charts", font=("Arial", 18),
                  width=20, height=2, command=self.show_charts_ui).pack(side='right', padx=20)

        tk.Button(extra_frame, text="Add Transaction", font=("Arial", 18),
                  width=20, height=2, command=self.add_transaction_popup).pack(side='left', padx=20)

        self.update_summary()
        self.switch(frame)

    def show_investment_tracker(self):
        investment_window = tk.Toplevel(self)
        investment_window.title("Investment Tracker")
        investment_window.geometry("1200x750")

        investment_app = InvestmentApp(investment_window)

        back_btn = tk.Button(investment_window, text="Back to Calendar",
                             font=("Arial", 12), command=investment_window.destroy)
        back_btn.pack(side=tk.BOTTOM, pady=10)

    def show_charts_ui(self):
        charts_window = tk.Toplevel(self)
        charts_window.title("Visual Charts")
        charts_window.geometry("1200x750")

        # Create a container frame for ChartsUI
        container = ttk.Frame(charts_window)
        container.pack(fill='both', expand=True)

        # Charts UI
        calendar_ui = self.current_frame.calendar_ui
        charts_ui = ChartsUI(container, data_fetch.data_fetcher, calendar_ui)
        charts_ui.pack(fill='both', expand=True)

        # Back button
        back_btn = tk.Button(charts_window, text="Back to Calendar",
                             font=("Arial", 12), command=charts_window.destroy)
        back_btn.pack(side=tk.BOTTOM, pady=10)

    def add_transaction_popup(self):
        import json
        from datetime import datetime

        popup = tk.Toplevel(self)
        popup.title("Add Transaction")
        popup.geometry("400x400")

        # Default = today's date (YYYY-MM-DD)
        today = datetime.now().strftime("%Y-%m-%d")

        tk.Label(popup, text="Date (YYYY-MM-DD):", font=("Arial", 14)).pack(pady=5)
        date_entry = tk.Entry(popup, font=("Arial", 14))
        date_entry.insert(0, today)
        date_entry.pack(pady=5)

        tk.Label(popup, text="Description:", font=("Arial", 14)).pack(pady=5)
        desc_entry = tk.Entry(popup, font=("Arial", 14))
        desc_entry.pack(pady=5)

        tk.Label(popup, text="Amount: (Note: Use a '-' for Expenses)", font=("Arial", 14)).pack(pady=5)
        amount_entry = tk.Entry(popup, font=("Arial", 14))
        amount_entry.pack(pady=5)

        tk.Label(popup, text="Category:", font=("Arial", 14)).pack(pady=5)
        category_entry = tk.Entry(popup, font=("Arial", 14))
        category_entry.pack(pady=5)

        def save_transaction():
            try:
                date = date_entry.get().strip()
                desc = desc_entry.get().strip()
                amount = float(amount_entry.get().strip())
                category = category_entry.get().strip()

                with open("transactions.json", "r") as f:
                    data = json.load(f)

                if date not in data:
                    data[date] = []

                data[date].append({
                    "desc": desc,
                    "amount": amount,
                    "category": category
                })

                with open("transactions.json", "w") as f:
                    json.dump(data, f, indent=4)

                self.update_summary()
                popup.destroy()

            except Exception as e:
                tk.messagebox.showerror("Error", f"Could not save transaction:\n{e}")

        tk.Button(
            popup, text="Save", font=("Arial", 16),
            command=save_transaction
        ).pack(pady=20)

    def update_summary(self):
        import json

        try:
            with open("transactions.json", "r") as f:
                data = json.load(f)
        except:
            return

        total_income = 0
        total_expense = 0

        selected_month = self.months[self.current_month_index]

        for date, entries in data.items():
            try:
                year, month, day = date.split("-")
            except:
                continue

            month_name = self.months[int(month) - 1]

            if month_name != selected_month:
                continue

            for entry in entries:
                amt = entry.get("amount", 0)
                if amt >= 0:
                    total_income += amt
                else:
                    total_expense += abs(amt)

        total_balance = total_income - total_expense

        self.total_income_label.config(text=f"Total Made: ${total_income:.2f}")
        self.total_expense_label.config(text=f"Total Expenses: ${total_expense:.2f}")
        self.total_balance_label.config(text=f"Total: ${total_balance:.2f}")

    def save_and_next(self, value, key, next_screen):
        self.user_data[key] = value
        next_screen()


if __name__ == "__main__":
    app = App()
    app.mainloop()