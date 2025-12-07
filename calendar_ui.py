import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime


class CalendarUI(ttk.Frame):
    def __init__(self, parent, fetch_transactions_callback):
        super().__init__(parent)
        self.fetch_transactions = fetch_transactions_callback

        now = datetime.now()
        self.year = now.year
        self.month = now.month

        self.build_header()
        self.build_calendar_grid()
        self.populate_calendar(self.year, self.month)

    def build_header(self):
        header = ttk.Frame(self)
        header.pack(fill='x', pady=(0, 5))

        self.prev_btn = ttk.Button(header, text='<', width=3, command=self.prev_month)
        self.prev_btn.pack(side='left')

        self.month_label = ttk.Label(header, text='', font=('TkDefaultFont', 12, 'bold'))
        self.month_label.pack(side='left', padx=10)

        self.next_btn = ttk.Button(header, text='>', width=3, command=self.next_month)
        self.next_btn.pack(side='left')

        spacer = ttk.Frame(header)
        spacer.pack(side='left', expand=True, fill='x')

        ttk.Button(header, text='Today', command=self.go_to_today).pack(side='right')

    def build_calendar_grid(self):
        self.grid_frame = ttk.Frame(self)
        self.grid_frame.pack()

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, d in enumerate(days):
            lbl = ttk.Label(self.grid_frame, text=d, anchor='center')
            lbl.grid(row=0, column=i, padx=2, pady=2)

        self.day_buttons = []
        for r in range(1, 7):
            row = []
            for c in range(7):
                btn = ttk.Button(self.grid_frame, text='', width=15)
                btn.grid(row=r, column=c, padx=5, pady=5, ipady=10, sticky='nsew')  # Use padding instead
                row.append(btn)
            self.day_buttons.append(row)

    def populate_calendar(self, year, month):
        self.month_label.config(text=f"{calendar.month_name[month]} {year}")
        cal = calendar.monthcalendar(year, month)

        while len(cal) < 6:
            cal.append([0]*7)

        for r in range(6):
            for c in range(7):
                day = cal[r][c]
                btn = self.day_buttons[r][c]

                if day == 0:
                    btn.config(text='', command=lambda: None)
                else:
                    btn.config(text=str(day),
                               command=lambda d=day: self.show_transactions(d))

    def show_transactions(self, day):
        txs = self.fetch_transactions(self.year, self.month, day)
        popup = tk.Toplevel(self)
        popup.title(f"Transactions for {self.month}/{day}/{self.year}")
        popup.geometry('400x300')

        frame = ttk.Frame(popup)
        frame.pack(fill='both', expand=True, padx=8, pady=8)

        if not txs:
            ttk.Label(frame, text='No transactions').pack()
            return

        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        for t in txs:
            desc = t.get('desc', '')
            amt = t.get('amount', 0)
            time = t.get('time', '')
            cat = t.get('category', '')
            lbl = ttk.Label(scroll_frame, text=f"{time} — {desc} — {cat} — ${amt}", anchor='w')
            lbl.pack(fill='x', pady=2)

    def prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.populate_calendar(self.year, self.month)

    def next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.populate_calendar(self.year, self.month)

    def go_to_today(self):
        now = datetime.now()
        self.year = now.year
        self.month = now.month
        self.populate_calendar(self.year, self.month)
