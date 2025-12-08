"""
Fixed Investment Tracker - Tkinter GUI
- Cleaned threading and UI updates
- Robust yfinance fallbacks
- Autocomplete fixed
- Auto-refresh controlled and safe
- Thread stopped on close
- Added Gold Investment tab
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import yfinance as yf
import threading
import time
import json
import os
from datetime import datetime
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import requests
import webbrowser
import random

# ---------------------------
# Config / Constants
# ---------------------------
AUTO_REFRESH_SECONDS = 10
FAV_FILE = "favorites.json"
PORT_FILE = "portfolio.json"
GOLD_FILE = "gold_portfolio.json"
POPULAR_TICKERS = [
    "AAPL", "MSFT", "TSLA", "GOOG", "AMZN", "NVDA", "META", "SPY", "QQQ", "AMD",
    "INTC", "NFLX", "BABA", "DIS", "V", "MA", "PYPL", "UBER", "LYFT", "KO", "PEP"
]

# Gold price - will be fetched from API
CURRENT_GOLD_PRICE = 4197.38  # Default value, will be updated

# Gold portfolio structure
gold_portfolio = {
    "balance": 0.0,
    "gold_owned": 0.0,
    "avg_purchase_price": 0.0
}


# ---------------------------
# Helpers: Storage
# ---------------------------
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print("Failed to save", path, e)


# ---------------------------
# Gold Investment Functions
# ---------------------------
def fetch_gold_price():
    """Fetch current gold price from API"""
    try:
        # Try yahoo finance for gold (GC=F is gold futures)
        gold_ticker = yf.Ticker("GC=F")
        df = gold_ticker.history(period="1d")
        if not df.empty:
            return float(df["Close"].iloc[-1])

        # Fallback to metals API
        url = "https://api.metals.live/v1/spot/gold"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return float(data[0].get("price", CURRENT_GOLD_PRICE))
    except Exception as e:
        print(f"Error fetching gold price: {e}")

    return CURRENT_GOLD_PRICE  # Return default if API fails


def set_gold_balance(amount):
    """Set starting balance for gold investment"""
    try:
        gold_portfolio["balance"] = float(amount)
        save_json(GOLD_FILE, gold_portfolio)
        return True, f"Balance set to ${gold_portfolio['balance']:.2f}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def buy_gold(amount):
    """Buy gold with specified amount"""
    try:
        amount = float(amount)
        if amount > gold_portfolio["balance"]:
            return False, "Not enough balance."

        current_price = fetch_gold_price()
        gold_bought = amount / current_price
        old_gold = gold_portfolio["gold_owned"]
        old_price = gold_portfolio["avg_purchase_price"]

        if old_gold == 0:
            new_avg = current_price
        else:
            total_old = old_gold * old_price
            new_avg = (total_old + amount) / (old_gold + gold_bought)

        gold_portfolio["gold_owned"] += gold_bought
        gold_portfolio["avg_purchase_price"] = new_avg
        gold_portfolio["balance"] -= amount

        save_json(GOLD_FILE, gold_portfolio)
        return True, f"Bought {gold_bought:.4f} oz at ${current_price:.2f} per oz."

    except Exception as e:
        return False, f"Error: {str(e)}"


def get_portfolio_summary():
    """Get gold portfolio summary"""
    current_price = fetch_gold_price()
    gold = gold_portfolio["gold_owned"]

    if gold == 0:
        return (
            f"Balance: ${gold_portfolio['balance']:.2f}\n"
            f"Gold Owned: 0 oz\n"
            f"Current Gold Price: ${current_price:.2f}\n"
            f"Profit/Loss: $0.00 (0.00%)"
        )
    else:
        current_value = gold * current_price
        profit = current_value - gold * gold_portfolio["avg_purchase_price"]
        pct = (profit / (gold * gold_portfolio["avg_purchase_price"])) * 100 if gold_portfolio[
                                                                                    "avg_purchase_price"] > 0 else 0

        return (
            f"Balance: ${gold_portfolio['balance']:.2f}\n"
            f"Gold Owned: {gold:.4f} oz\n"
            f"Avg Purchase Price: ${gold_portfolio['avg_purchase_price']:.2f}\n"
            f"Current Gold Price: ${current_price:.2f}\n"
            f"Current Value: ${current_value:.2f}\n"
            f"Profit/Loss: ${profit:.2f} ({pct:.2f}%)"
        )


def simulate_and_sell_best(years):
    """Simulate gold prices and sell at best year"""
    try:
        years = int(years)
        if gold_portfolio["gold_owned"] == 0:
            return False, "You do not own any gold.", None

        gold = gold_portfolio["gold_owned"]
        avg_price = gold_portfolio["avg_purchase_price"]
        future_price = fetch_gold_price()
        best_year = (0, 0, -999999)  # (year, price, profit)
        result_text = ""

        for year in range(1, years + 1):
            # Moderate yearly growth: +1% to +5%
            change = random.uniform(0.01, 0.05)
            future_price = round(future_price * (1 + change), 2)

            value = gold * future_price
            profit = value - gold * avg_price
            pct = (profit / (gold * avg_price)) * 100 if avg_price > 0 else 0

            result_text += (
                f"Year {year}: Price = ${future_price:.2f} | "
                f"Profit = ${profit:.2f} ({pct:.2f}%)\n"
            )

            if profit > best_year[2]:
                best_year = (year, future_price, profit)

        # Sell at best year
        year, price, profit = best_year
        cash = gold * price

        gold_portfolio["balance"] += cash
        gold_portfolio["gold_owned"] = 0
        gold_portfolio["avg_purchase_price"] = 0

        save_json(GOLD_FILE, gold_portfolio)

        final_message = (
            f"{result_text}\n"
            f"--- BEST YEAR TO SELL ---\n"
            f"Year: {year}\n"
            f"Sell Price: ${price:.2f}\n"
            f"Cash Received: ${cash:.2f}\n"
            f"Profit: ${profit:.2f}"
        )
        return True, final_message, cash

    except Exception as e:
        return False, f"Error: {str(e)}", None


# ---------------------------
# App State
# ---------------------------
state = {
    "favorites": load_json(FAV_FILE, []),
    "portfolio": load_json(PORT_FILE, {"cash": 10000.0, "positions": {}}),
    "gold_portfolio": load_json(GOLD_FILE, gold_portfolio),
    "mode": "light",
    "last_price": None,
    "auto_refresh": True,
    "_running": True,  # controls background threads
}

# Update gold_portfolio from saved state
gold_portfolio.update(state["gold_portfolio"])


# ---------------------------
# Autocomplete Entry (fixed placement)
# ---------------------------
class AutocompleteEntry(ttk.Entry):
    def __init__(self, master=None, tickers=None, **kwargs):
        super().__init__(master, **kwargs)
        self.tickers = sorted(set(tickers or []))
        self.var = tk.StringVar()
        self.configure(textvariable=self.var)
        self.var.trace_add("write", self._on_change)
        self.listbox = None
        self.master = master
        # handle clicking elsewhere to hide
        self.bind("<FocusOut>", lambda e: self._hide_listbox_delayed())

    def _on_change(self, *args):
        val = self.var.get().upper().strip()
        if val == "":
            self.hide_listbox()
            return
        matches = [t for t in self.tickers if t.startswith(val)]
        if not matches:
            self.hide_listbox()
            return
        self.show_listbox(matches)

    def show_listbox(self, matches):
        # create listbox as a Toplevel so it floats above other widgets
        if self.listbox is None:
            self.lb_win = tk.Toplevel(self)
            self.lb_win.wm_overrideredirect(True)
            self.listbox = tk.Listbox(self.lb_win, height=6)
            self.listbox.pack()
            self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.delete(0, tk.END)
        for m in matches[:20]:
            self.listbox.insert(tk.END, m)

        # position under the entry
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.lb_win.geometry(f"+{x}+{y}")
        self.lb_win.deiconify()

    def _on_select(self, evt):
        if not self.listbox: return
        sel = self.listbox.curselection()
        if sel:
            val = self.listbox.get(sel[0])
            self.var.set(val)
        self.hide_listbox()

    def hide_listbox(self):
        if hasattr(self, "lb_win") and self.lb_win:
            try:
                self.lb_win.withdraw()
                self.lb_win.destroy()
            except Exception:
                pass
            self.listbox = None
            self.lb_win = None

    def _hide_listbox_delayed(self):
        # slight delay so double-clicks register
        self.after(150, self.hide_listbox)


# ---------------------------
# Networking / Data helpers
# ---------------------------
def fetch_price(ticker, timeout=6):
    """Return float price or None"""
    if not ticker:
        return None
    try:
        t = yf.Ticker(ticker)
        # try historical closes (5d)
        df = t.history(period="5d")
        if isinstance(df, (pd.DataFrame,)) and not df.empty:
            closes = df["Close"].dropna()
            if not closes.empty:
                return float(closes.iloc[-1])
        # fallback: try fast_info safely
        try:
            fast = getattr(t, "fast_info", None)
            if fast:
                # fast_info might be a dict-like
                if isinstance(fast, dict):
                    p = fast.get("last_price")
                else:
                    p = getattr(fast, "get", lambda k, d=None: None)("last_price")
                if p:
                    return float(p)
        except Exception:
            pass
        # last fallback: direct Yahoo chart API
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            return float(data["chart"]["result"][0]["meta"]["regularMarketPrice"])
        except Exception:
            return None
    except Exception:
        return None


def fetch_history(ticker, period="1y", interval="1d", timeout=8):
    if not ticker:
        return None
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
        if df is None or df.empty:
            return None
        return df
    except Exception:
        return None


def fetch_news(ticker, timeout=6):
    if not ticker:
        return []
    try:
        t = yf.Ticker(ticker)
        news = getattr(t, "news", None)
        items = []
        if news:
            for n in news[:10]:
                title = n.get("title") or n.get("publisher") or "News"
                link = n.get("link") or n.get("url") or None
                items.append({"title": title, "link": link})
        if not items:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}"
            resp = requests.get(url, timeout=timeout).json()
            for r in resp.get("news", [])[:10]:
                items.append({"title": r.get("title"), "link": r.get("link")})
        return items
    except Exception:
        return []


def fetch_earnings_calendar(ticker):
    if not ticker:
        return None
    try:
        t = yf.Ticker(ticker)
        cal = getattr(t, "calendar", None)
        if cal is None or cal.empty:
            return None
        return cal.to_dict()
    except Exception:
        return None


# ---------------------------
# Portfolio
# ---------------------------
def portfolio_buy(ticker, qty, price):
    p = state["portfolio"]
    cost = qty * price
    if cost > p["cash"]:
        raise Exception("Not enough cash")
    p["cash"] -= cost
    pos = p["positions"].setdefault(ticker, {"qty": 0, "avg": 0.0})
    total_shares = pos["qty"] + qty
    pos["avg"] = (pos["avg"] * pos["qty"] + price * qty) / total_shares if total_shares > 0 else 0.0
    pos["qty"] = total_shares
    save_json(PORT_FILE, p)


def portfolio_sell(ticker, qty, price):
    p = state["portfolio"]
    pos = p["positions"].get(ticker)
    if not pos or pos["qty"] < qty:
        raise Exception("Not enough shares")
    pos["qty"] -= qty
    p["cash"] += qty * price
    if pos["qty"] == 0:
        del p["positions"][ticker]
    save_json(PORT_FILE, p)


# ---------------------------
# GUI App
# ---------------------------
class InvestmentApp:
    def __init__(self, root):
        self.root = root
        try:
            root.winfo_toplevel().title("Investment Flow")
        except:
            pass

        self._chart_canvas = None
        self._chart_fig = None
        self._ticker = None

        self._build_ui()

        # Start background refresh thread (daemon)
        self._refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
        self._refresh_thread.start()

    def _build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)

        ttk.Label(top, text="Enter Stock Ticker:").pack(side=tk.LEFT, padx=(2, 4))
        self.ticker_entry = AutocompleteEntry(top, tickers=POPULAR_TICKERS, width=12)
        self.ticker_entry.pack(side=tk.LEFT)
        # enter key -> load ticker
        self.ticker_entry.bind("<Return>", lambda e: self.load_ticker())

        ttk.Button(top, text="Get Price", command=self.load_ticker).pack(side=tk.LEFT, padx=6)
        ttk.Button(top, text="Add Favorite", command=self.add_favorite).pack(side=tk.LEFT)
        ttk.Button(top, text="Remove Favorite", command=self.remove_favorite).pack(side=tk.LEFT, padx=(4, 0))

        self.auto_btn_text = tk.StringVar(value="AutoRefresh: ON")
        ttk.Button(top, textvariable=self.auto_btn_text, command=self.toggle_auto).pack(side=tk.LEFT, padx=8)

        ttk.Button(top, text="Portfolio", command=self.open_portfolio_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(top, text="Compare Multi", command=self.open_compare_dialog).pack(side=tk.LEFT)

        # Left: favorites
        left = ttk.Frame(self.root, width=180)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)
        ttk.Label(left, text="Favorites").pack(anchor=tk.NW)
        self.fav_list = tk.Listbox(left, height=20)
        self.fav_list.pack(fill=tk.BOTH, expand=True)
        self.fav_list.bind("<Double-Button-1>", lambda e: self._load_selected_favorite())
        self._refresh_fav_list()

        # Center notebook
        center = ttk.Frame(self.root)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.nb = ttk.Notebook(center)
        self.nb.pack(fill=tk.BOTH, expand=True)

        # Live tab
        self.tab_live = ttk.Frame(self.nb)
        self.nb.add(self.tab_live, text="Live Price")
        self.live_price_label = ttk.Label(self.tab_live, text="Current Price: --", font=("Arial", 18))
        self.live_price_label.pack(pady=10)
        self.live_time_label = ttk.Label(self.tab_live, text="Updated: --")
        self.live_time_label.pack()

        # Chart tab
        self.tab_chart = ttk.Frame(self.nb)
        self.nb.add(self.tab_chart, text="Historical Chart")
        chart_controls = ttk.Frame(self.tab_chart)
        chart_controls.pack(fill=tk.X, padx=6, pady=6)
        ttk.Label(chart_controls, text="Period:").pack(side=tk.LEFT)
        self.period_combo = ttk.Combobox(chart_controls, values=["1mo", "3mo", "6mo", "1y", "5y"], width=6)
        self.period_combo.set("1y");
        self.period_combo.pack(side=tk.LEFT, padx=4)
        ttk.Label(chart_controls, text="Interval:").pack(side=tk.LEFT, padx=(8, 0))
        self.interval_combo = ttk.Combobox(chart_controls, values=["1d", "1wk", "1mo", "1h"], width=6)
        self.interval_combo.set("1d");
        self.interval_combo.pack(side=tk.LEFT, padx=4)
        ttk.Button(chart_controls, text="Show Chart", command=self.show_chart).pack(side=tk.LEFT, padx=6)
        self.chart_frame = ttk.Frame(self.tab_chart)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        # Market overview
        self.tab_market = ttk.Frame(self.nb)
        self.nb.add(self.tab_market, text="Market Overview")
        ttk.Button(self.tab_market, text="Load Market Indexes", command=self.load_market).pack(pady=6)
        self.market_text = tk.Text(self.tab_market, height=15)
        self.market_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Gold Investment Tab
        self.tab_gold = ttk.Frame(self.nb)
        self.nb.add(self.tab_gold, text="Gold Investment")
        self._build_gold_tab()

        # Tips & Tricks tab
        self.tab_tips = ttk.Frame(self.nb)
        self.nb.add(self.tab_tips, text="Tips & Tricks")

        # Outer frame to add padding
        tips_frame = ttk.Frame(self.tab_tips, padding=20)
        tips_frame.pack(fill=tk.BOTH, expand=True)

        tips = [
            "Start with companies you understand.",
            "Don't invest money you can't afford to lose.",
            "Diversify across different sectors.",
            "Focus on long-term gains, not daily noise.",
            "Use dollar-cost averaging for long-term buys."
        ]

        # Text widget with spacing
        txt = tk.Text(
            tips_frame,
            font=("Segoe UI", 12),
            spacing1=10,  # space above each line
            spacing2=4,  # space between wrapped lines
            spacing3=10,  # space below each line
            state="normal"  # temporarily editable so we can insert text
        )
        txt.pack(fill=tk.BOTH, expand=True)

        # Insert content
        txt.insert(tk.END, "\n".join(f"- {t}" for t in tips))

        # Make read-only
        txt.config(state="disabled")

        # News Tab
        self.tab_news = ttk.Frame(self.nb)
        self.nb.add(self.tab_news, text="News")

        news_main = ttk.Frame(self.tab_news, padding=20)
        news_main.pack(fill=tk.BOTH, expand=True)

        news_controls = ttk.Frame(news_main)
        news_controls.pack(fill=tk.X, padx=(10), pady=(10, 15))

        ttk.Button(news_controls, text="Load News for Ticker", command=self.load_news).pack(side=tk.LEFT)

        # Listbox frame (adds padding + scrollbar)
        list_frame = ttk.Frame(news_main)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.news_list = tk.Listbox(
            list_frame,
            yscrollcommand=scroll.set,
            font=("Segoe UI", 11),
            activestyle="none"
        )
        self.news_list.pack(fill=tk.BOTH, expand=True)

        scroll.config(command=self.news_list.yview)

        self.news_list.bind("<Double-Button-1>", self.open_selected_news)

        # Status
        self.status = ttk.Label(self.root, text="Ready", anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_gold_tab(self):
        """Build the Gold Investment tab interface"""
        # Main container with padding
        main_frame = ttk.Frame(self.tab_gold, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Gold Investment System", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Current Gold Price Display
        price_frame = ttk.Frame(main_frame)
        price_frame.pack(fill=tk.X, pady=(0, 20))

        self.gold_price_label = ttk.Label(
            price_frame,
            text="Current Gold Price: $--",
            font=("Arial", 12, "bold")
        )
        self.gold_price_label.pack()

        ttk.Button(price_frame, text="Refresh Gold Price", command=self.refresh_gold_price).pack(pady=5)

        # Portfolio Summary Display
        summary_frame = ttk.Frame(main_frame, relief="groove", borderwidth=2)
        summary_frame.pack(fill=tk.X, pady=(0, 20), padx=20)

        self.gold_summary_label = ttk.Label(
            summary_frame,
            text="Load your portfolio to see summary...",
            font=("Arial", 10),
            wraplength=400,
            justify="left"
        )
        self.gold_summary_label.pack(padx=10, pady=10)

        # Balance Section
        balance_frame = ttk.LabelFrame(main_frame, text="Set Balance", padding=10)
        balance_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(balance_frame, text="Starting Balance ($):").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.balance_entry = ttk.Entry(balance_frame, width=15)
        self.balance_entry.grid(row=0, column=1, padx=(0, 10))
        ttk.Button(balance_frame, text="Set Balance", command=self.set_gold_balance).grid(row=0, column=2)

        # Buy Gold Section
        buy_frame = ttk.LabelFrame(main_frame, text="Buy Gold", padding=10)
        buy_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(buy_frame, text="Amount to Invest ($):").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.buy_entry = ttk.Entry(buy_frame, width=15)
        self.buy_entry.grid(row=0, column=1, padx=(0, 10))
        ttk.Button(buy_frame, text="Buy Gold", command=self.buy_gold).grid(row=0, column=2)

        # Simulation Section
        sim_frame = ttk.LabelFrame(main_frame, text="Simulation & Auto-Sell", padding=10)
        sim_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(sim_frame, text="Years to Simulate:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.sim_years_entry = ttk.Entry(sim_frame, width=10)
        self.sim_years_entry.grid(row=0, column=1, padx=(0, 10))
        ttk.Button(sim_frame, text="Simulate & Auto-Sell Best Year",
                   command=self.simulate_and_sell).grid(row=0, column=2)

        # Action Buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(pady=20)

        ttk.Button(action_frame, text="View Portfolio",
                   command=self.view_gold_portfolio).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Reset Portfolio",
                   command=self.reset_gold_portfolio).pack(side=tk.LEFT, padx=5)

        # Initialize gold price display
        self.refresh_gold_price()

    def _generate_market_sentiment(self, lines):
        ups = sum("▲" in line for line in lines)
        downs = sum("▼" in line for line in lines)

        if ups > downs:
            return "Markets are trending UP today with positive momentum."
        elif downs > ups:
            return "Markets are showing weakness today with negative movement."
        else:
            return "Markets are mixed with no clear direction."

    # -------------------------
    # Gold Investment Methods
    # -------------------------
    def refresh_gold_price(self):
        """Fetch and display current gold price"""

        def bg_task():
            price = fetch_gold_price()
            self.root.after(0, lambda: self._update_gold_price_display(price))

        threading.Thread(target=bg_task, daemon=True).start()

    def _update_gold_price_display(self, price):
        """Update gold price label on UI thread"""
        self.gold_price_label.config(text=f"Current Gold Price: ${price:,.2f}")

    def set_gold_balance(self):
        """Set starting balance for gold investment"""
        amount = self.balance_entry.get()
        if not amount:
            messagebox.showerror("Error", "Please enter a balance amount.")
            return

        success, msg = set_gold_balance(amount)
        if success:
            messagebox.showinfo("Success", msg)
            self.view_gold_portfolio()
        else:
            messagebox.showerror("Error", msg)

    def buy_gold(self):
        """Buy gold with specified amount"""
        amount = self.buy_entry.get()
        if not amount:
            messagebox.showerror("Error", "Please enter an amount to invest.")
            return

        success, msg = buy_gold(amount)
        if success:
            messagebox.showinfo("Gold Purchased", msg)
            self.view_gold_portfolio()
        else:
            messagebox.showerror("Error", msg)

    def view_gold_portfolio(self):
        """Display gold portfolio summary"""
        summary = get_portfolio_summary()
        self.gold_summary_label.config(text=summary)

    def simulate_and_sell(self):
        """Run simulation and auto-sell at best year"""
        years = self.sim_years_entry.get()
        if not years:
            messagebox.showerror("Error", "Please enter number of years to simulate.")
            return

        success, msg, cash = simulate_and_sell_best(years)
        if success:
            messagebox.showinfo("Simulation Complete", msg)
            self.view_gold_portfolio()
        else:
            messagebox.showerror("Error", msg)

    def reset_gold_portfolio(self):
        """Reset gold portfolio to initial state"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset your gold portfolio?"):
            gold_portfolio.update({
                "balance": 0.0,
                "gold_owned": 0.0,
                "avg_purchase_price": 0.0
            })
            save_json(GOLD_FILE, gold_portfolio)
            messagebox.showinfo("Success", "Gold portfolio reset successfully.")
            self.view_gold_portfolio()

    # -------------------------
    # Favorites
    # -------------------------
    def _refresh_fav_list(self):
        self.fav_list.delete(0, tk.END)
        for f in state["favorites"]:
            self.fav_list.insert(tk.END, f)

    def add_favorite(self):
        t = self.ticker_entry.var.get().upper().strip()
        if not t:
            messagebox.showerror("Error", "Enter a ticker")
            return
        if t in state["favorites"]:
            messagebox.showinfo("Info", "Already in favorites")
            return
        state["favorites"].append(t)
        save_json(FAV_FILE, state["favorites"])
        self._refresh_fav_list()

    def remove_favorite(self):
        t = self.ticker_entry.var.get().upper().strip()
        if t in state["favorites"]:
            state["favorites"].remove(t)
            save_json(FAV_FILE, state["favorites"])
            self._refresh_fav_list()
        else:
            messagebox.showinfo("Info", "Ticker not in favorites")

    def _load_selected_favorite(self):
        sel = self.fav_list.curselection()
        if not sel:
            return
        t = self.fav_list.get(sel[0])
        self.ticker_entry.var.set(t)
        self.load_ticker()

    # -------------------------
    # Auto refresh loop
    # -------------------------
    def toggle_auto(self):
        state["auto_refresh"] = not state["auto_refresh"]
        self.auto_btn_text.set("AutoRefresh: ON" if state["auto_refresh"] else "AutoRefresh: OFF")

    def _auto_refresh_loop(self):
        # runs in background daemon thread
        while state.get("_running", True):
            try:
                if state.get("auto_refresh", True):
                    # only refresh if a ticker is set
                    ticker_text = self.ticker_entry.var.get().upper().strip()
                    if ticker_text:
                        # schedule load_ticker on main thread
                        self.root.after(0, lambda t=ticker_text: self._start_price_thread(t))
                time.sleep(AUTO_REFRESH_SECONDS)
            except Exception:
                time.sleep(AUTO_REFRESH_SECONDS)

    # -------------------------
    # Price loading
    # -------------------------
    def load_ticker(self):
        ticker = self.ticker_entry.var.get().upper().strip()
        if not ticker:
            messagebox.showerror("Error", "Please enter a ticker symbol.")
            return
        self._start_price_thread(ticker)

    def _start_price_thread(self, ticker):
        # spawn a short-lived thread to fetch price
        threading.Thread(target=self._fetch_and_update_live, args=(ticker,), daemon=True).start()

    def _fetch_and_update_live(self, ticker):
        # network call, not on UI thread
        self._set_status(f"Fetching price for {ticker}...")
        price = fetch_price(ticker)
        if price is None:
            # show error on UI thread
            self.root.after(0, lambda: (self._set_status("Failed to fetch price"),
                                        messagebox.showerror("Error", f"Price not available for {ticker}")))
            return
        last = state.get("last_price")

        def ui_update():
            arrow = ""
            color = "black"
            if last is not None:
                if price > last:
                    arrow = " ▲";
                    color = "green"
                elif price < last:
                    arrow = " ▼";
                    color = "red"
            state["last_price"] = price
            text = f"{ticker}: ${price:,.2f}{arrow}"
            try:
                self.live_price_label.config(text=text, foreground=color)
            except Exception:
                self.live_price_label.config(text=text)
            self.live_time_label.config(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self._ticker = ticker
            self._set_status("Price updated")

        self.root.after(0, ui_update)

    # -------------------------
    # Market overview
    # -------------------------
    def load_market(self):
        self._set_status("Loading market overview...")

        def bg():
            try:
                idx = {
                    "S&P 500": "^GSPC",
                    "Dow Jones": "^DJI",
                    "NASDAQ": "^IXIC",
                    "Russell 2000": "^RUT",
                    "VIX Volatility Index": "^VIX"
                }

                lines = []

                for name, symbol in idx.items():
                    data = yf.Ticker(symbol).history(period="1d")

                    if data.empty:
                        lines.append(f"{name} ({symbol}): N/A\n")
                        continue

                    price = data["Close"].iloc[-1]
                    open_price = data["Open"].iloc[-1]
                    high = data["High"].iloc[-1]
                    low = data["Low"].iloc[-1]
                    vol = data["Volume"].iloc[-1]

                    change = price - open_price
                    pct = (change / open_price) * 100

                    direction = "▲" if change >= 0 else "▼"
                    color = "green" if change >= 0 else "red"

                    lines.append(
                        f"{name} ({symbol})\n"
                        f"  Price: ${price:,.2f} {direction} ({pct:.2f}%)\n"
                        f"  High / Low: ${high:,.2f} / ${low:,.2f}\n"
                        f"  Volume: {vol:,}\n"
                    )

                # Add a simple sentiment summary
                sentiment = self._generate_market_sentiment(lines)
                lines.append("\nMarket Summary:\n" + sentiment)

                self.root.after(
                    0,
                    lambda: (
                        self.market_text.delete("1.0", tk.END),
                        self.market_text.insert(tk.END, "\n".join(lines)),
                        self._set_status("Market overview loaded.")
                    )
                )

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=bg, daemon=True).start()

    # -------------------------
    # News
    # -------------------------
    def load_news(self):
        ticker = self.ticker_entry.var.get().upper().strip()
        if not ticker:
            messagebox.showerror("Error", "Enter a ticker to load news")
            return
        self._set_status("Loading news...")
        threading.Thread(target=self._fetch_news_thread, args=(ticker,), daemon=True).start()

    def _fetch_news_thread(self, ticker):
        items = []

        try:
            # Try to get news from yfinance
            stock = yf.Ticker(ticker)
            raw_items = stock.news or []

            # Normalize each news item safely
            for n in raw_items:
                if not isinstance(n, dict):
                    continue

                # Extract title
                title = (
                        n.get("title") or
                        n.get("headline") or
                        (n.get("content") or {}).get("title") or
                        "Untitled Article"
                )

                # Extract link/URL
                link = (
                        n.get("link") or
                        n.get("url") or
                        (n.get("content") or {}).get("clickThroughUrl") or
                        None
                )

                items.append({"title": title, "link": link})

        except Exception as e:
            print(f"Error fetching news: {e}")
            items = []

        # If no items from yfinance, try alternative source
        if not items:
            try:
                url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}"
                resp = requests.get(url, timeout=10).json()

                for r in resp.get("news", [])[:10]:
                    title = r.get("title") or "Untitled Article"
                    link = r.get("link") or r.get("url")
                    items.append({"title": title, "link": link})
            except Exception as e:
                print(f"Error fetching alternative news: {e}")

        def ui():
            self.news_list.delete(0, tk.END)

            if not items:
                self.news_list.insert(tk.END, "No news found for this ticker.")
                self.news_list.links = []
                return

            links = []

            for n in items:
                title = n["title"]
                link = n["link"]

                # Shorten long titles for display
                display = title if len(title) <= 120 else title[:120] + "..."

                self.news_list.insert(tk.END, display)
                self.news_list.insert(tk.END, "")
                links.append(link)

            # Store the links (could be strings or dicts)
            self.news_list.links = links
            self._set_status(f"Loaded {len(items)} news items")

        self.root.after(0, ui)

    def open_selected_news(self, evt):
        sel = self.news_list.curselection()
        if not sel:
            return

        idx = sel[0]
        links = getattr(self.news_list, "links", [])

        if idx >= len(links):
            return

        link = links[idx]

        # Handle if link is a dictionary (extract the URL)
        if isinstance(link, dict):
            # Try to get URL from common dictionary keys
            url = link.get("link") or link.get("url") or link.get("clickThroughUrl")
            if url:
                webbrowser.open(url)
            else:
                messagebox.showinfo("Info", "No valid URL found in news data")
        elif isinstance(link, str) and link:
            webbrowser.open(link)
        else:
            messagebox.showinfo("Info", "No link available for this article")

    # -------------------------
    # Charting (Simplified - Only line charts)
    # -------------------------
    def show_chart(self):
        ticker = self.ticker_entry.var.get().upper().strip()
        if not ticker:
            messagebox.showerror("Error", "Enter a ticker")
            return
        period = self.period_combo.get()
        interval = self.interval_combo.get()
        self._set_status(f"Loading history for {ticker}...")
        threading.Thread(target=self._fetch_and_plot, args=(ticker, period, interval), daemon=True).start()

    def _fetch_and_plot(self, ticker, period, interval):
        df = fetch_history(ticker, period=period, interval=interval)
        if df is None or df.empty:
            self.root.after(0, lambda: (messagebox.showerror("Error", "No historical data"),
                                        self._set_status("Failed to load history")))
            return
        self.root.after(0, lambda: self._plot_dataframe(ticker, df))

    def _clear_chart(self):
        # remove old canvas properly
        if self._chart_canvas is not None:
            try:
                self._chart_canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self._chart_canvas = None
            self._chart_fig = None
        for w in self.chart_frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    def _plot_dataframe(self, ticker, df):
        self._clear_chart()
        self._chart_fig = plt.Figure(figsize=(9, 5))
        ax = self._chart_fig.add_subplot(111)

        try:
            ax.plot(df.index, df["Close"], label="Close", linewidth=2)
            ax.set_title(f"{ticker} - {self.period_combo.get()} {self.interval_combo.get()}")
            ax.set_ylabel("Price")
            ax.legend()
            ax.grid(True)
        except Exception as e:
            ax.text(0.5, 0.5, f"Plot error: {e}", transform=ax.transAxes)

        # tooltip
        try:
            annot = ax.annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                                bbox=dict(boxstyle="round", fc="w"),
                                arrowprops=dict(arrowstyle="->"))
            annot.set_visible(False)
            xdata = matplotlib.dates.date2num(df.index.to_pydatetime())
            ydata = df["Close"].values

            def on_move(event):
                if event.inaxes != ax:
                    annot.set_visible(False)
                    try:
                        self._chart_canvas.draw_idle()
                    except Exception:
                        pass
                    return
                try:
                    x = event.xdata
                    idx = np.abs(xdata - x).argmin()
                    x_val = df.index.to_pydatetime()[idx]
                    y_val = ydata[idx]
                    annot.xy = (matplotlib.dates.date2num(x_val), y_val)
                    annot.set_text(f"{x_val.strftime('%Y-%m-%d')}\n${y_val:,.2f}")
                    annot.get_bbox_patch().set_alpha(0.9)
                    annot.set_visible(True)
                    self._chart_canvas.draw_idle()
                except Exception:
                    pass
        except Exception:
            pass

        self._chart_canvas = FigureCanvasTkAgg(self._chart_fig, master=self.chart_frame)
        self._chart_canvas.mpl_connect("motion_notify_event", on_move)
        self._chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._chart_canvas.draw()
        self._set_status("Chart loaded")

    # -------------------------
    # Compare multiple tickers
    # -------------------------
    def open_compare_dialog(self):
        txt = simpledialog.askstring("Compare", "Enter tickers separated by commas (e.g. AAPL,MSFT,TSLA):")
        if not txt:
            return
        tickers = [t.strip().upper() for t in txt.split(",") if t.strip()]
        if len(tickers) < 2:
            messagebox.showerror("Error", "Enter at least two tickers")
            return
        threading.Thread(target=self._compare_and_plot, args=(tickers,), daemon=True).start()

    def _compare_and_plot(self, tickers):
        dfs = {}
        for t in tickers:
            df = fetch_history(t, period="1y", interval="1d")
            dfs[t] = df["Close"] if df is not None else None

        def ui():
            self._clear_chart()
            fig = plt.Figure(figsize=(9, 5))
            ax = fig.add_subplot(111)
            for t, series in dfs.items():
                if series is not None:
                    ax.plot(series.index, series.values, label=t, linewidth=2)
                else:
                    ax.plot([], [], label=f"{t} (N/A)")
            ax.set_title("Comparison (normalized)")
            ax.legend()
            ax.grid(True)
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            canvas.draw()
            self._chart_canvas = canvas
            self._chart_fig = fig
            self._set_status("Comparison loaded")

        self.root.after(0, ui)

    # -------------------------
    # Portfolio dialog
    # -------------------------
    def open_portfolio_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Portfolio Simulator")
        dlg.geometry("600x400")

        # Top frame with cash display
        top = ttk.Frame(dlg)
        top.pack(fill=tk.X, padx=6, pady=6)
        self.port_cash_lbl = ttk.Label(top, text=f"Cash: ${state['portfolio'].get('cash', 0):,.2f}",
                                       font=("Arial", 12, "bold"))
        self.port_cash_lbl.pack(side=tk.LEFT)

        # Positions list
        pos_frame = ttk.Frame(dlg)
        pos_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        ttk.Label(pos_frame, text="Your Positions:").pack(anchor=tk.W)
        self.pos_list = tk.Listbox(pos_frame)
        self.pos_list.pack(fill=tk.BOTH, expand=True)

        # Load initial positions
        self._refresh_port_ui()

        # Operations buttons
        ops = ttk.Frame(dlg)
        ops.pack(fill=tk.X, padx=6, pady=6)
        ttk.Button(ops, text="Buy", command=lambda: self._portfolio_trade(dlg, "buy")).pack(side=tk.LEFT, padx=4)
        ttk.Button(ops, text="Sell", command=lambda: self._portfolio_trade(dlg, "sell")).pack(side=tk.LEFT, padx=4)
        ttk.Button(ops, text="Export", command=lambda: save_json("portfolio_export.json", state["portfolio"])).pack(
            side=tk.RIGHT)

    def _refresh_port_ui(self):
        p = state["portfolio"]
        try:
            # Update cash label
            self.port_cash_lbl.config(text=f"Cash: ${p.get('cash', 0):,.2f}")

            # Update positions list
            self.pos_list.delete(0, tk.END)

            # Add header if there are positions
            if p.get("positions", {}):
                self.pos_list.insert(tk.END, "Ticker     Quantity     Avg Price     Current Value")
                self.pos_list.insert(tk.END, "-" * 50)

            # Add each position
            for t, v in p.get("positions", {}).items():
                # Try to get current price for value calculation
                current_price = fetch_price(t)
                if current_price:
                    current_value = v['qty'] * current_price
                    self.pos_list.insert(tk.END, f"{t:10} {v['qty']:10} ${v['avg']:10,.2f} ${current_value:12,.2f}")
                else:
                    self.pos_list.insert(tk.END, f"{t:10} {v['qty']:10} ${v['avg']:10,.2f} (Price N/A)")

            # Show total portfolio value if we have positions
            if p.get("positions", {}):
                self.pos_list.insert(tk.END, "-" * 50)
                total_value = p.get("cash", 0)
                for t, v in p.get("positions", {}).items():
                    current_price = fetch_price(t)
                    if current_price:
                        total_value += v['qty'] * current_price
                self.pos_list.insert(tk.END, f"Total Portfolio Value: ${total_value:,.2f}")

        except Exception as e:
            print(f"Error refreshing portfolio UI: {e}")

    def _portfolio_trade(self, parent, action):
        t = simpledialog.askstring("Ticker", "Enter ticker:", parent=parent)
        if not t: return
        t = t.upper().strip()
        qty = simpledialog.askinteger("Quantity", "Enter quantity:", parent=parent, minvalue=1)
        if not qty: return
        price = fetch_price(t)
        if price is None:
            messagebox.showerror("Error", "Can't fetch price")
            return
        try:
            if action == "buy":
                portfolio_buy(t, qty, price)
            else:
                portfolio_sell(t, qty, price)
            messagebox.showinfo("Done", f"{action.title()} {qty} {t} @ ${price:,.2f}")
            self._refresh_port_ui()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # -------------------------
    # Earnings
    # -------------------------
    def show_earnings(self):
        t = self.ticker_entry.var.get().upper().strip()
        if not t:
            messagebox.showerror("Error", "Enter ticker")
            return
        cal = fetch_earnings_calendar(t)
        if not cal:
            messagebox.showinfo("Info", "No earnings calendar data")
            return
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Earnings - {t}")
        txt = tk.Text(dlg)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert(tk.END, json.dumps(cal, indent=2))

    # -------------------------
    # Utilities
    # -------------------------
    def _set_status(self, text):
        try:
            self.status.config(text=text)
        except Exception:
            pass

    def stop(self):
        # indicate background loop should stop
        state["_running"] = False


# ---------------------------
# Run app
# ---------------------------
def main():
    root = tk.Tk()
    app = InvestmentApp(root)

    def on_close():
        # save state and stop threads
        save_json(FAV_FILE, state["favorites"])
        save_json(PORT_FILE, state["portfolio"])
        save_json(GOLD_FILE, gold_portfolio)
        app.stop()
        # give a moment for background thread to see flag (daemon thread will exit on program close)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()