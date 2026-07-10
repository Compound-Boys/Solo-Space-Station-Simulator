import tkinter as tk
import math
import random
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox, ttk

from game.helper_methods.game_clock import get_elapsed_seconds
from game.helper_methods.ui_panels import patch_destroy_cleanup

DEFAULT_COMPANY_NAMES = [
    "TechCorp",
    "GlobalBank",
    "HealthCare Plus",
    "EnergyCo",
    "FoodChain",
    "AutoMakers",
    "RetailGiant",
    "PharmaTech",
    "RealEstate Co",
    "MediaGroup",
    "Aerospace Inc",
    "TechStart",
    "GreenEnergy",
    "DigitalBank",
    "SmartHome",
]

CYCLE_INTERVAL_SECONDS = 300  # a new cycle every 5 minutes of master game time

class Company:
    def __init__(self, name, starting_value):
        self.name = name
        self.current_value = starting_value
        self.previous_value = starting_value
        self.price_history = [starting_value]
        self.owned_shares = 0
        
    def update_value(self):
        """Update the company's stock value"""
        self.previous_value = self.current_value
        
        # Random change between -10% and +10%
        change = random.uniform(-0.10, 0.10)
        
        self.current_value = max(1.0, self.current_value * (1 + change))
        
        self.price_history.append(self.current_value)
        
        # Limit price history to most recent 50 cycles
        if len(self.price_history) > 50:
            self.price_history.pop(0)


def create_default_companies(history_cycles=5):
    """Create the default company list with optional price history."""
    companies = [Company(name, random.uniform(10, 1000)) for name in DEFAULT_COMPANY_NAMES]
    for _ in range(history_cycles):
        for company in companies:
            company.update_value()
    return companies


def serialize_companies(companies):
    """Serialize live company objects for player_data storage."""
    return [
        {
            "name": company.name,
            "current_value": company.current_value,
            "previous_value": company.previous_value,
            "price_history": company.price_history,
            "owned_shares": company.owned_shares if hasattr(company, "owned_shares") else 0,
        }
        for company in companies
    ]


def apply_companies_from_save(companies, company_data_list):
    """Restore live company objects from saved player_data."""
    if not company_data_list or len(company_data_list) != len(companies):
        return

    for i, company_data in enumerate(company_data_list):
        companies[i].name = company_data["name"]
        companies[i].current_value = company_data["current_value"]
        companies[i].previous_value = company_data["previous_value"]
        companies[i].price_history = company_data["price_history"]
        companies[i].owned_shares = company_data.get("owned_shares", 0)


def sync_holdings_to_companies(companies, stock_holdings):
    """Sync player stock holdings onto company owned_shares fields."""
    holdings = stock_holdings or {}
    for company in companies:
        company.owned_shares = holdings.get(company.name, 0)


def refresh_companies_from_player_data(companies, player_data):
    """Apply saved company prices, then restore ownership from stock_holdings."""
    market_data = player_data.get("stock_market", {})
    apply_companies_from_save(companies, market_data.get("companies"))
    sync_holdings_to_companies(companies, player_data.get("stock_holdings"))


def migrate_stock_holdings_from_companies(player_data):
    """Backfill stock_holdings from serialized company owned_shares for old saves."""
    if player_data.get("stock_holdings"):
        return

    market_data = player_data.get("stock_market", {})
    companies = market_data.get("companies")
    if not companies:
        return

    holdings = {
        company["name"]: company["owned_shares"]
        for company in companies
        if company.get("owned_shares", 0) > 0
    }
    if holdings:
        player_data["stock_holdings"] = holdings


def get_seconds_until_next_cycle(elapsed_seconds, interval=CYCLE_INTERVAL_SECONDS):
    """Calculate seconds remaining until the next market cycle, per the master timer."""
    return int(max(0, interval - (elapsed_seconds % interval)))


def default_stock_market_state():
    """Return a fresh stock_market block for player_data."""
    return {
        "cycle_number": 1,
        "companies": [],
        "trade_log": [],
    }


def truncate_credits(value):
    """Truncate credits to 2 decimal places (toward zero, never round up)."""
    return math.trunc(value * 100) / 100


def record_trade(player_data, cycle, side, company_name, shares, price, total):
    """Append or merge a buy/sell entry in the current cycle trade log."""
    if "stock_market" not in player_data:
        player_data["stock_market"] = {}

    if "trade_log" not in player_data["stock_market"]:
        player_data["stock_market"]["trade_log"] = []

    current_cycle_entry = None
    for entry in player_data["stock_market"]["trade_log"]:
        if entry.get("cycle") == cycle:
            current_cycle_entry = entry
            break

    if not current_cycle_entry:
        current_cycle_entry = {
            "cycle": cycle,
            "trades": {"bought": {}, "sold": {}},
        }
        player_data["stock_market"]["trade_log"].append(current_cycle_entry)

    if side not in current_cycle_entry["trades"]:
        current_cycle_entry["trades"][side] = {}

    side_trades = current_cycle_entry["trades"][side]
    if company_name in side_trades:
        existing = side_trades[company_name]
        existing["amount"] += shares
        existing["total"] += total
        existing["price"] = existing["total"] / existing["amount"]
    else:
        side_trades[company_name] = {
            "amount": shares,
            "price": price,
            "total": total,
        }


def generate_market_tip(companies_data):
    """Return a random overheard market tip, or None if no companies exist."""
    if not companies_data:
        return None

    company = random.choice(companies_data)
    direction = random.choice(["rise", "fall"])
    name = company["name"]

    if direction == "rise":
        return f"Overheard that {name} stock is expected to rise soon!"
    return f"Overheard that {name} stock might be dropping in value soon!"


class StockMarketEngine:
    """Owns live market state and master-timer-driven tick logic."""

    def __init__(self, companies=None):
        self.companies = companies if companies is not None else create_default_companies()
        self.cycle_number = 1

    def tick_if_due(self, elapsed_seconds):
        """Advance the market to match the master timer. Returns True if it changed.

        Cycles are scheduled purely off ``elapsed_seconds``: cycle N ends at
        ``N * CYCLE_INTERVAL_SECONDS``. Catches up fully (not just one cycle)
        if a lot of time passed since the last check, e.g. after loading a
        save that sat untouched for a while.
        """
        target_cycle = int(elapsed_seconds // CYCLE_INTERVAL_SECONDS) + 1
        if target_cycle <= self.cycle_number:
            return False

        while self.cycle_number < target_cycle:
            for company in self.companies:
                company.update_value()
            self.cycle_number += 1

        return True

    def sync_to_player_data(self, player_data):
        """Write current market state into player_data."""
        if "stock_market" not in player_data:
            player_data["stock_market"] = default_stock_market_state()

        sync_holdings_to_companies(self.companies, player_data.get("stock_holdings"))

        player_data["stock_market"].update({
            "cycle_number": self.cycle_number,
            "companies": serialize_companies(self.companies),
        })

        if "trade_log" not in player_data["stock_market"]:
            player_data["stock_market"]["trade_log"] = []

    def load_from_player_data(self, player_data):
        """Restore market state from player_data."""
        if "stock_market" not in player_data:
            return

        market_data = player_data["stock_market"]
        self.cycle_number = market_data.get("cycle_number", 1)

        migrate_stock_holdings_from_companies(player_data)

        if "companies" in market_data:
            refresh_companies_from_player_data(self.companies, player_data)


def hydrate_companies(companies):
    """Return live Company objects from Company instances or serialized dicts."""
    if not companies:
        return create_default_companies()
    if all(isinstance(company, Company) for company in companies):
        return list(companies)
    live = create_default_companies(history_cycles=0)
    apply_companies_from_save(live, companies)
    return live


class StockMarket:
    def __init__(self, parent_window, player_data, companies, cycle_number, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.companies = hydrate_companies(companies)
        self.cycle_number = cycle_number
        self.return_callback = return_callback
        self.current_company = None

        self.stock_transactions = []

        self.current_filter = "All" # Default filter shows all stocks

        # Sort order: "price_asc" (low to high) or "price_desc" (high to low)
        self.sort_order = "price_asc"

        # Ownership filter: "all", "owned", "not_owned"
        self.ownership_filter = "all"

        # Trend filter: "all", "rising", "falling"
        self.trend_filter = "all"

        # Dedicated window (matplotlib needs a real Toplevel, not an overlay Frame)
        self.stock_window = tk.Toplevel(parent_window)
        self.stock_window.title("Stock Market")
        self.stock_window.geometry("1150x978")
        self.stock_window.configure(bg="black")
        self.stock_window.minsize(1035, 805)
        self.stock_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.stock_window.transient(parent_window)
        self.stock_window.grab_set()

        sync_holdings_to_companies(self.companies, player_data.get("stock_holdings"))

        self.left_frame = tk.Frame(self.stock_window, bg="black", width=300)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

        # Left column: filters → listbox → trade → History/Back (normal pack order)
        self.left_content = tk.Frame(self.left_frame, bg="black")
        self.left_content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(self.stock_window, bg="black")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.header_frame = tk.Frame(self.right_frame, bg="black")
        self.header_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 0))

        self.info_frame = tk.Frame(self.header_frame, bg="black")
        self.info_frame.pack(side=tk.LEFT, anchor="nw", padx=(0, 20))

        self.cycle_label = tk.Label(self.info_frame, text=f"Cycle: {self.cycle_number}",
                                   font=("Arial", 12), bg="black", fg="white")
        self.cycle_label.grid(row=0, column=0, sticky="w", pady=1)

        self.timer_label = tk.Label(self.info_frame, text="Next Update: Calculating...",
                                  font=("Arial", 12), bg="black", fg="yellow")
        self.timer_label.grid(row=1, column=0, sticky="w", pady=1)

        self.credits_label = tk.Label(self.info_frame, text=f"Credits: {player_data['credits']:.2f}",
                                    font=("Arial", 12), bg="black", fg="white")
        self.credits_label.grid(row=2, column=0, sticky="w", pady=1)

        self.company_info_frame = tk.Frame(self.header_frame, bg="black")
        self.company_info_frame.pack(side=tk.RIGHT, anchor="ne", fill=tk.X, expand=True)

        self.filter_frame = tk.Frame(self.left_content, bg="black")
        self.filter_frame.pack(fill=tk.X, pady=(0, 2))

        filter_label = tk.Label(self.filter_frame, text="Filter Stocks:",
                             font=("Arial", 12), bg="black", fg="white")
        filter_label.pack(anchor="w", pady=(0, 0))

        self.filter_buttons_frame = tk.Frame(self.filter_frame, bg="black")
        self.filter_buttons_frame.pack(fill=tk.X, pady=2)

        self.all_btn = tk.Button(self.filter_buttons_frame, text="Show All",
                            font=("Arial", 10), bg="#333333", fg="white", relief=tk.SUNKEN,
                            command=lambda: self.filter_companies("All"))
        self.all_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.affordable_btn = tk.Button(self.filter_buttons_frame, text="Affordable",
                                 font=("Arial", 10), bg="#333333", fg="white",
                                 command=lambda: self.filter_companies("Affordable"))
        self.affordable_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.expensive_btn = tk.Button(self.filter_buttons_frame, text="Expensive",
                                font=("Arial", 10), bg="#333333", fg="white",
                                command=lambda: self.filter_companies("Expensive"))
        self.expensive_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        sort_label = tk.Label(self.filter_frame, text="Sort By Price:",
                            font=("Arial", 12), bg="black", fg="white")
        sort_label.pack(anchor="w", pady=(4, 0))

        self.sort_buttons_frame = tk.Frame(self.filter_frame, bg="black")
        self.sort_buttons_frame.pack(fill=tk.X, pady=2)

        self.low_high_btn = tk.Button(self.sort_buttons_frame, text="Low to High",
                                  font=("Arial", 10), bg="#333333", fg="white", relief=tk.SUNKEN,
                                  command=lambda: self.sort_companies("price_asc"))
        self.low_high_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.high_low_btn = tk.Button(self.sort_buttons_frame, text="High to Low",
                                  font=("Arial", 10), bg="#333333", fg="white",
                                  command=lambda: self.sort_companies("price_desc"))
        self.high_low_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        ownership_label = tk.Label(self.filter_frame, text="Ownership:",
                                 font=("Arial", 12), bg="black", fg="white")
        ownership_label.pack(anchor="w", pady=(4, 0))

        self.ownership_buttons_frame = tk.Frame(self.filter_frame, bg="black")
        self.ownership_buttons_frame.pack(fill=tk.X, pady=2)

        self.all_ownership_btn = tk.Button(self.ownership_buttons_frame, text="All Stocks",
                                          font=("Arial", 10), bg="#333333", fg="white", relief=tk.SUNKEN,
                                          command=lambda: self.filter_by_ownership("all"))
        self.all_ownership_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.owned_btn = tk.Button(self.ownership_buttons_frame, text="Owned",
                                  font=("Arial", 10), bg="#333333", fg="white",
                                  command=lambda: self.filter_by_ownership("owned"))
        self.owned_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.not_owned_btn = tk.Button(self.ownership_buttons_frame, text="Not Owned",
                                     font=("Arial", 10), bg="#333333", fg="white",
                                     command=lambda: self.filter_by_ownership("not_owned"))
        self.not_owned_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        trend_label = tk.Label(self.filter_frame, text="Trend:",
                                 font=("Arial", 12), bg="black", fg="white")
        trend_label.pack(anchor="w", pady=(4, 0))

        self.trend_buttons_frame = tk.Frame(self.filter_frame, bg="black")
        self.trend_buttons_frame.pack(fill=tk.X, pady=2)

        self.all_trend_btn = tk.Button(self.trend_buttons_frame, text="All",
                                          font=("Arial", 10), bg="#333333", fg="white", relief=tk.SUNKEN,
                                          command=lambda: self.filter_by_trend("all"))
        self.all_trend_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.rising_btn = tk.Button(self.trend_buttons_frame, text="Rising",
                                  font=("Arial", 10), bg="#333333", fg="white",
                                  command=lambda: self.filter_by_trend("rising"))
        self.rising_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.falling_btn = tk.Button(self.trend_buttons_frame, text="Falling",
                                     font=("Arial", 10), bg="#333333", fg="white",
                                     command=lambda: self.filter_by_trend("falling"))
        self.falling_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.companies_listbox = tk.Listbox(self.left_content,
                                         font=("Arial", 12), bg="black", fg="white",
                                         selectbackground="#333333", selectforeground="white",
                                         width=30, height=8)
        self.companies_listbox.pack(pady=(4, 2), fill=tk.X)

        self.trade_frame = tk.Frame(self.left_content, bg="black")
        self.trade_frame.pack(fill=tk.X, pady=(4, 2))

        # Navigation under buy/sell so it stays on screen
        self.left_bottom_frame = tk.Frame(self.left_content, bg="black")
        self.left_bottom_frame.pack(fill=tk.X, pady=(2, 0))

        self.history_btn = tk.Button(self.left_bottom_frame, text="View Trade History",
                                   font=("Arial", 12), bg="#333333", fg="white",
                                   command=self.show_trade_history)
        self.history_btn.pack(pady=(2, 1), fill=tk.X)

        self.back_btn = tk.Button(self.left_bottom_frame, text="Back to Computer",
                                font=("Arial", 12), bg="#333333", fg="white",
                                command=self.on_closing)
        self.back_btn.pack(pady=(1, 2), fill=tk.X)

        self.fig = plt.Figure(figsize=(5, 3), dpi=100)
        self.fig.patch.set_facecolor('black')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('black')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.configure(bg="black", highlightbackground="black")
        # Less top padding so the plot sits higher; bottom margin keeps x-axis label visible
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.90, bottom=0.18)
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self._timer_after_id = None
        self._closed = False
        
        self.companies_listbox.bind('<<ListboxSelect>>', self.on_company_select)
        
        self.last_seen_cycle = cycle_number
        
        self.populate_companies_listbox()
        
        if self.companies_listbox.size() > 0:
            self.companies_listbox.selection_set(0)
            self.on_company_select(None)  # Trigger the selection handler
            
        self.update_timer()

    def _refresh_companies_from_player_data(self):
        """Apply saved company prices and ownership from player_data."""
        refresh_companies_from_player_data(self.companies, self.player_data)

    def _sync_cycle_from_player_data(self):
        """Update the cycle label from player_data if it changed."""
        market_data = self.player_data.get("stock_market", {})
        poll_cycle = market_data.get("cycle_number", 0)

        if poll_cycle != self.last_seen_cycle:
            self.cycle_number = poll_cycle
            self.last_seen_cycle = poll_cycle
            self.cycle_label.config(text=f"Cycle: {self.cycle_number}")
            return True

        return False
    
    def update_timer(self):
        """Update the countdown timer for next stock update"""
        if getattr(self, "_closed", False):
            return
        try:
            if not self.stock_window.winfo_exists():
                return
        except tk.TclError:
            return

        cycle_changed = self._sync_cycle_from_player_data()
        if cycle_changed:
            self._refresh_companies_from_player_data()
            self.populate_companies_listbox()

            if self.current_company:
                selected_name = self.current_company.name
                for i in range(self.companies_listbox.size()):
                    item_text = self.companies_listbox.get(i)
                    if item_text == selected_name:
                        self.companies_listbox.selection_clear(0, tk.END)
                        self.companies_listbox.selection_set(i)
                        self.companies_listbox.see(i)
                        self.on_company_select(None)
                        break

        elapsed_seconds = get_elapsed_seconds(self.player_data)
        remaining = get_seconds_until_next_cycle(elapsed_seconds)

        if remaining <= 0:
            self.timer_label.config(text="Updating Market...", fg="green")
        else:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            self.timer_label.config(
                text=f"Next Update: {minutes:02d}:{seconds:02d}",
                fg="yellow" if remaining > 15 else "orange" if remaining > 5 else "red",
            )

        self._timer_after_id = self.stock_window.after(1000, self.update_timer)
    
    def on_company_select(self, event):
        """Handle company selection from the listbox"""
        if not self.companies_listbox.curselection():
            return
        
        selection_idx = self.companies_listbox.curselection()[0]
        selected_company_name = self.companies_listbox.get(selection_idx)
        
        for company in self.companies:
            if company.name == selected_company_name:
                self.current_company = company
                break
        else:
            return
        
        for widget in self.company_info_frame.winfo_children():
            widget.destroy()
        
        for widget in self.trade_frame.winfo_children():
            widget.destroy()
        
        company_name = tk.Label(self.company_info_frame, text=self.current_company.name, 
                              font=("Arial", 18, "bold"), bg="black", fg="white")
        company_name.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        
        current_price = tk.Label(self.company_info_frame, text=f"Current Price: {self.current_company.current_value:.2f}", 
                               font=("Arial", 12), bg="black", fg="white")
        current_price.grid(row=1, column=0, sticky="w", pady=2)
        
        price_change = self.current_company.current_value - self.current_company.previous_value
        price_change_pct = (price_change / self.current_company.previous_value) * 100
        
        change_color = "green" if price_change >= 0 else "red"
        
        price_change_label = tk.Label(self.company_info_frame, 
                                    text=f"Change: {price_change:.2f} ({price_change_pct:.2f}%)", 
                                    font=("Arial", 12), bg="black", fg=change_color)
        price_change_label.grid(row=1, column=1, sticky="w", pady=2)
        
        shares_owned = tk.Label(self.company_info_frame, 
                              text=f"Shares Owned: {self.current_company.owned_shares}", 
                              font=("Arial", 12), bg="black", fg="white")
        shares_owned.grid(row=2, column=0, sticky="w", pady=2)
        
        total_value = self.current_company.owned_shares * self.current_company.current_value
        
        shares_value = tk.Label(self.company_info_frame, 
                              text=f"Total Value: {total_value:.2f}", 
                              font=("Arial", 12), bg="black", fg="white")
        shares_value.grid(row=2, column=1, sticky="w", pady=2)
        
        self.update_graph()
        
        self.create_trade_interface()
    
    def update_graph(self):
        """Update the price history graph for the selected company"""
        if not self.current_company:
            return
            
        self.ax.clear()
        
        self.ax.set_facecolor('black')
        self.ax.tick_params(colors='white')
        
        prices = self.current_company.price_history
        x = range(len(prices))
        
        if prices[-1] >= prices[0]:
            line_color = 'green'
        else:
            line_color = 'red'
            
        self.ax.plot(x, prices, color=line_color)
        
        self.ax.set_title(f"{self.current_company.name} Price History", color='white')
        self.ax.set_xlabel("Cycles", color='white')
        self.ax.set_ylabel("Price", color='white')
        
        self.ax.grid(False)
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.90, bottom=0.18)

        self.canvas.draw()
    
    def create_trade_interface(self):
        """Create the interface for buying and selling stocks"""
        shares_label = tk.Label(self.trade_frame, text="Shares:", 
                              font=("Arial", 12), bg="black", fg="white")
        shares_label.grid(row=0, column=0, padx=5, pady=(5, 2))
        
        share_options = [1, 5, 10, 25, 50, 100]
        self.shares_var = tk.StringVar(value="1")
        
        shares_dropdown = ttk.Combobox(self.trade_frame, textvariable=self.shares_var, 
                                     values=share_options, width=5)
        shares_dropdown.grid(row=0, column=1, padx=5, pady=(5, 2))
        
        shares_dropdown.config(state="normal")
        
        max_can_buy = int(self.player_data["credits"] / self.current_company.current_value)
        max_can_sell = self.current_company.owned_shares
        
        max_buy_btn = tk.Button(self.trade_frame, text=f"Max Buy ({max_can_buy})", 
                              font=("Arial", 10), bg="#333333", fg="white",
                              command=lambda: self.shares_var.set(str(max_can_buy)))
        max_buy_btn.grid(row=1, column=0, padx=5, pady=5)
        
        max_sell_btn = tk.Button(self.trade_frame, text=f"Max Sell ({max_can_sell})", 
                               font=("Arial", 10), bg="#333333", fg="white",
                               command=lambda: self.shares_var.set(str(max_can_sell)))
        max_sell_btn.grid(row=1, column=1, padx=5, pady=5)
        
        def update_total_cost(*args):
            try:
                shares = int(self.shares_var.get())
                total = shares * self.current_company.current_value
                total_label.config(text=f"Total: {total:.2f}")
                
                if shares > 0 and total <= self.player_data["credits"]:
                    buy_btn.config(state=tk.NORMAL)
                else:
                    buy_btn.config(state=tk.DISABLED)
                    
                if shares > 0 and shares <= self.current_company.owned_shares:
                    sell_btn.config(state=tk.NORMAL)
                else:
                    sell_btn.config(state=tk.DISABLED)
                    
            except ValueError:
                total_label.config(text="Total: 0.00")
                buy_btn.config(state=tk.DISABLED)
                sell_btn.config(state=tk.DISABLED)
        
        self.shares_var.trace("w", update_total_cost)
        
        total_label = tk.Label(self.trade_frame, text="Total: 0.00", 
                            font=("Arial", 12), bg="black", fg="white")
        total_label.grid(row=0, column=2, padx=20, pady=(5, 2))
        
        buy_btn = tk.Button(self.trade_frame, text="Buy", font=("Arial", 12), 
                         bg="green", fg="white", width=8,
                         command=self.buy_stock)
        buy_btn.grid(row=2, column=0, padx=10, pady=10)
        
        sell_btn = tk.Button(self.trade_frame, text="Sell", font=("Arial", 12), 
                          bg="red", fg="white", width=8,
                          command=self.sell_stock)
        sell_btn.grid(row=2, column=1, padx=10, pady=10)
        
        update_total_cost()
    
    def buy_stock(self):
        """Buy stock of the currently selected company"""
        try:
            shares = int(self.shares_var.get())
            
            total_cost = shares * self.current_company.current_value
            
            if total_cost > self.player_data["credits"]:
                messagebox.showerror("Transaction Failed", "Not enough credits for this purchase.")
                return
                
            self.player_data["credits"] -= total_cost
            self.player_data["credits"] = truncate_credits(self.player_data["credits"])
            
            self.current_company.owned_shares += shares
            
            if "stock_holdings" not in self.player_data:
                self.player_data["stock_holdings"] = {}
                
            if self.current_company.name not in self.player_data["stock_holdings"]:
                self.player_data["stock_holdings"][self.current_company.name] = shares
            else:
                self.player_data["stock_holdings"][self.current_company.name] += shares
            
            transaction = {
                "type": "buy",
                "company": self.current_company.name,
                "shares": shares,
                "price": self.current_company.current_value,
                "total": total_cost,
                "timestamp": datetime.datetime.now().isoformat()
            }
            self.stock_transactions.append(transaction)

            record_trade(
                self.player_data,
                self.cycle_number,
                "bought",
                self.current_company.name,
                shares,
                self.current_company.current_value,
                total_cost,
            )
            
            self.credits_label.config(text=f"Credits: {self.player_data['credits']:.2f}")
            
            max_can_buy = int(self.player_data["credits"] / self.current_company.current_value)
            
            messagebox.showinfo("Transaction Complete", 
                               f"Bought {shares} shares of {self.current_company.name} for {total_cost:.2f} credits.")
            
            self.on_company_select(None)
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number of shares.")
    
    def sell_stock(self):
        """Sell stock of the currently selected company"""
        try:
            shares = int(self.shares_var.get())
            
            if shares > self.current_company.owned_shares:
                messagebox.showerror("Transaction Failed", "You don't own that many shares.")
                return
                
            total_value = shares * self.current_company.current_value
            
            self.player_data["credits"] += total_value
            self.player_data["credits"] = truncate_credits(self.player_data["credits"])
            
            self.current_company.owned_shares -= shares
            
            if "stock_holdings" in self.player_data and self.current_company.name in self.player_data["stock_holdings"]:
                self.player_data["stock_holdings"][self.current_company.name] -= shares
                
                # Remove entry if no shares left
                if self.player_data["stock_holdings"][self.current_company.name] <= 0:
                    del self.player_data["stock_holdings"][self.current_company.name]
            
            # Calculate profit/loss if we have the purchase price history
            profit = 0
            if "stock_purchases" in self.player_data and self.current_company.name in self.player_data["stock_purchases"]:
                purchases = self.player_data["stock_purchases"][self.current_company.name]
                if len(purchases) > 0:
                    total_cost = sum(purchase["price"] * purchase["shares"] for purchase in purchases[:shares])
                    avg_price = total_cost / shares if shares > 0 else 0
                    
                    profit = total_value - (avg_price * shares)
            
            transaction = {
                "type": "sell",
                "company": self.current_company.name,
                "shares": shares,
                "price": self.current_company.current_value,
                "total": total_value,
                "profit": profit,
                "timestamp": datetime.datetime.now().isoformat()
            }
            self.stock_transactions.append(transaction)

            record_trade(
                self.player_data,
                self.cycle_number,
                "sold",
                self.current_company.name,
                shares,
                self.current_company.current_value,
                total_value,
            )
            
            self.credits_label.config(text=f"Credits: {self.player_data['credits']:.2f}")
            
            profit_text = ""
            if profit != 0:
                if profit > 0:
                    profit_text = f" (Profit: {profit:.2f} credits)"
                else:
                    profit_text = f" (Loss: {abs(profit):.2f} credits)"
                    
            messagebox.showinfo("Transaction Complete", 
                               f"Sold {shares} shares of {self.current_company.name} for {total_value:.2f} credits.{profit_text}")
            
            self.on_company_select(None)
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number of shares.")
    
    def show_trade_history(self):
        """Show the trade history log in a child window."""
        history_window = tk.Toplevel(self.stock_window)
        history_window.title("Trade History")
        history_window.geometry("650x550")
        history_window.configure(bg="black")
        history_window.minsize(500, 400)
        history_window.transient(self.stock_window)
        history_window.grab_set()

        title_label = tk.Label(history_window, text="Trade History",
                             font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        frame = tk.Frame(history_window, bg="black")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        trade_log = tk.Text(frame, font=("Arial", 12),
                          bg="black", fg="white", width=60, height=20,
                          yscrollcommand=scrollbar.set, wrap=tk.WORD)
        trade_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=trade_log.yview)

        trade_log.tag_configure("header", foreground="yellow", font=("Arial", 14, "bold"))
        trade_log.tag_configure("cycle", foreground="cyan", font=("Arial", 12, "bold"))
        trade_log.tag_configure("bought", foreground="green", font=("Arial", 12))
        trade_log.tag_configure("sold", foreground="red", font=("Arial", 12))
        trade_log.tag_configure("company", foreground="white", font=("Arial", 12))

        if "stock_market" in self.player_data and "trade_log" in self.player_data["stock_market"]:
            trade_log.insert(tk.END, "TRADE HISTORY\n\n", "header")

            for entry in reversed(self.player_data["stock_market"]["trade_log"]):
                cycle = entry.get("cycle", 0)
                trade_log.insert(tk.END, f"Cycle {cycle}:\n", "cycle")

                trades = entry.get("trades", {})

                if "bought" in trades and trades["bought"]:
                    trade_log.insert(tk.END, "  BOUGHT:\n", "bought")
                    for company, data in trades["bought"].items():
                        amount = data.get("amount", 0)
                        price = data.get("price", 0)
                        total = data.get("total", 0)
                        trade_log.insert(tk.END, f"    {company}: {amount} shares @ {price:.2f} cr each = {total:.2f} cr\n", "company")

                if "sold" in trades and trades["sold"]:
                    trade_log.insert(tk.END, "  SOLD:\n", "sold")
                    for company, data in trades["sold"].items():
                        amount = data.get("amount", 0)
                        price = data.get("price", 0)
                        total = data.get("total", 0)
                        trade_log.insert(tk.END, f"    {company}: {amount} shares @ {price:.2f} cr each = {total:.2f} cr\n", "company")

                trade_log.insert(tk.END, "\n")
        else:
            trade_log.insert(tk.END, "No trade history available.")

        trade_log.config(state=tk.DISABLED)

        def _on_trade_mousewheel(event):
            try:
                trade_log.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception:
                try:
                    if event.num == 4:
                        trade_log.yview_scroll(-1, "units")
                    elif event.num == 5:
                        trade_log.yview_scroll(1, "units")
                except Exception:
                    pass

        trade_log.bind("<MouseWheel>", _on_trade_mousewheel)
        trade_log.bind("<Button-4>", _on_trade_mousewheel)
        trade_log.bind("<Button-5>", _on_trade_mousewheel)
        frame.bind("<MouseWheel>", _on_trade_mousewheel)
        history_window.bind("<MouseWheel>", _on_trade_mousewheel)

        def _history_cleanup():
            history_window.unbind("<MouseWheel>")
            history_window.unbind("<Button-4>")
            history_window.unbind("<Button-5>")

        patch_destroy_cleanup(history_window, _history_cleanup)

        close_btn = tk.Button(history_window, text="Close",
                            font=("Arial", 12), bg="#333333", fg="white",
                            command=history_window.destroy)
        close_btn.pack(pady=10)

    def on_closing(self):
        """Handle closing the stock market window."""
        if getattr(self, "_closed", False):
            return
        self._closed = True

        if self.stock_transactions:
            self.player_data["stock_transactions"] = self.stock_transactions

        if getattr(self, "_timer_after_id", None) is not None:
            try:
                self.stock_window.after_cancel(self._timer_after_id)
            except (tk.TclError, ValueError):
                pass
            self._timer_after_id = None

        try:
            self.stock_window.grab_release()
        except tk.TclError:
            pass

        callback = self.return_callback
        self.return_callback = None

        try:
            self.canvas.get_tk_widget().destroy()
        except Exception:
            pass
        try:
            plt.close(self.fig)
        except Exception:
            pass

        try:
            self.stock_window.destroy()
        except tk.TclError:
            pass

        if callback:
            callback(self.player_data)
    def filter_companies(self, filter_type):
        """Filter companies based on selected filter"""
        self.current_filter = filter_type
        
        self.all_btn.config(relief=tk.RAISED)
        self.affordable_btn.config(relief=tk.RAISED)
        self.expensive_btn.config(relief=tk.RAISED)
        
        if filter_type == "All":
            self.all_btn.config(relief=tk.SUNKEN)
        elif filter_type == "Affordable":
            self.affordable_btn.config(relief=tk.SUNKEN)
        elif filter_type == "Expensive":
            self.expensive_btn.config(relief=tk.SUNKEN)
        
        selected_company = None
        if self.companies_listbox.curselection():
            selected_idx = self.companies_listbox.curselection()[0]
            if selected_idx < self.companies_listbox.size():
                selected_company = self.companies_listbox.get(selected_idx)
        
        self.populate_companies_listbox()
        
        if selected_company:
            for i in range(self.companies_listbox.size()):
                if self.companies_listbox.get(i) == selected_company:
                    self.companies_listbox.selection_set(i)
                    self.companies_listbox.see(i)
                    self.on_company_select(None)  # Explicitly call after selection is restored
                    return
        
        if self.companies_listbox.size() > 0:
            self.companies_listbox.selection_set(0)
            self.on_company_select(None)  # Explicitly call after selection is made
    
    def sort_companies(self, sort_order):
        """Sort companies by price; does not alter active filters."""
        self.sort_order = sort_order

        self.low_high_btn.config(relief=tk.RAISED)
        self.high_low_btn.config(relief=tk.RAISED)

        if sort_order == "price_asc":
            self.low_high_btn.config(relief=tk.SUNKEN)
        else:
            self.high_low_btn.config(relief=tk.SUNKEN)
        
        selected_company = None
        if self.companies_listbox.curselection():
            selected_idx = self.companies_listbox.curselection()[0]
            if selected_idx < self.companies_listbox.size():
                selected_company = self.companies_listbox.get(selected_idx)
        
        self.populate_companies_listbox()
        
        if selected_company:
            for i in range(self.companies_listbox.size()):
                if self.companies_listbox.get(i) == selected_company:
                    self.companies_listbox.selection_set(i)
                    self.companies_listbox.see(i)
                    self.on_company_select(None)  # Explicitly call after selection is restored
                    return
        
        if self.companies_listbox.size() > 0:
            self.companies_listbox.selection_set(0)
            self.on_company_select(None)  # Explicitly call after selection is made
    
    def filter_by_ownership(self, ownership_filter):
        """Filter companies based on ownership"""
        self.ownership_filter = ownership_filter
        
        self.all_ownership_btn.config(relief=tk.RAISED)
        self.owned_btn.config(relief=tk.RAISED)
        self.not_owned_btn.config(relief=tk.RAISED)
        
        if ownership_filter == "all":
            self.all_ownership_btn.config(relief=tk.SUNKEN)
        elif ownership_filter == "owned":
            self.owned_btn.config(relief=tk.SUNKEN)
        elif ownership_filter == "not_owned":
            self.not_owned_btn.config(relief=tk.SUNKEN)
        
        selected_company = None
        if self.companies_listbox.curselection():
            selected_idx = self.companies_listbox.curselection()[0]
            if selected_idx < self.companies_listbox.size():
                selected_company = self.companies_listbox.get(selected_idx)
        
        self.populate_companies_listbox()
        
        if selected_company:
            for i in range(self.companies_listbox.size()):
                if self.companies_listbox.get(i) == selected_company:
                    self.companies_listbox.selection_set(i)
                    self.companies_listbox.see(i)
                    self.on_company_select(None)  # Explicitly call after selection is restored
                    return
        
        if self.companies_listbox.size() > 0:
            self.companies_listbox.selection_set(0)
            self.on_company_select(None)  # Explicitly call after selection is made
    
    def filter_by_trend(self, trend_filter):
        """Filter companies by price trend; does not alter active sort order."""
        self.trend_filter = trend_filter

        self.all_trend_btn.config(relief=tk.RAISED)
        self.rising_btn.config(relief=tk.RAISED)
        self.falling_btn.config(relief=tk.RAISED)

        if trend_filter == "all":
            self.all_trend_btn.config(relief=tk.SUNKEN)
        elif trend_filter == "rising":
            self.rising_btn.config(relief=tk.SUNKEN)
        elif trend_filter == "falling":
            self.falling_btn.config(relief=tk.SUNKEN)

        selected_company = None
        if self.companies_listbox.curselection():
            selected_idx = self.companies_listbox.curselection()[0]
            if selected_idx < self.companies_listbox.size():
                selected_company = self.companies_listbox.get(selected_idx)

        self.populate_companies_listbox()

        if selected_company:
            for i in range(self.companies_listbox.size()):
                if self.companies_listbox.get(i) == selected_company:
                    self.companies_listbox.selection_set(i)
                    self.companies_listbox.see(i)
                    self.on_company_select(None)
                    return

        if self.companies_listbox.size() > 0:
            self.companies_listbox.selection_set(0)
            self.on_company_select(None)
    
    def populate_companies_listbox(self):
        """Populate the companies listbox based on current filter and sort order"""
        self.companies_listbox.delete(0, tk.END)
        
        player_credits = self.player_data["credits"]
        
        filtered_companies = []
        
        for company in self.companies:
            max_shares = player_credits // company.current_value  # Integer division to get whole shares
            can_afford = max_shares >= 1  # Can afford if at least 1 whole share can be bought
            
            passes_affordability = (
                self.current_filter == "All" or
                (self.current_filter == "Affordable" and can_afford) or
                (self.current_filter == "Expensive" and not can_afford)
            )
            
            is_owned = company.owned_shares > 0
            passes_ownership = (
                self.ownership_filter == "all" or
                (self.ownership_filter == "owned" and is_owned) or
                (self.ownership_filter == "not_owned" and not is_owned)
            )

            price_change = company.current_value - company.previous_value
            passes_trend = (
                self.trend_filter == "all"
                or (self.trend_filter == "rising" and price_change > 0)
                or (self.trend_filter == "falling" and price_change < 0)
            )
            
            if passes_affordability and passes_ownership and passes_trend:
                filtered_companies.append((company.name, company.current_value, price_change))
        
        if self.sort_order == "price_asc":
            filtered_companies.sort(key=lambda x: x[1])
        else:
            filtered_companies.sort(key=lambda x: x[1], reverse=True)
        
        for company_name, price, _price_change in filtered_companies:
            self.companies_listbox.insert(tk.END, company_name)
        
        # Do NOT automatically select a company here - that happens in __init__ or filter_companies
    
