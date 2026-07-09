import tkinter as tk
import math
import random
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox, ttk

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

UPDATE_INTERVAL_SECONDS = 60
CYCLES_PER_DAY = 5

class Company:
    def __init__(self, name, starting_value):
        self.name = name
        self.current_value = starting_value
        self.previous_value = starting_value
        self.price_history = [starting_value]
        self.owned_shares = 0
        
    def update_value(self):
        """Update the company's stock value"""
        # Store the previous value for reference
        self.previous_value = self.current_value
        
        # Random change between -10% and +10%
        change = random.uniform(-0.10, 0.10)
        
        # Apply change
        self.current_value = max(1.0, self.current_value * (1 + change))
        
        # Add to price history
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


def get_seconds_until_update(last_update_time, interval=UPDATE_INTERVAL_SECONDS):
    """Calculate seconds remaining until the next market update."""
    now = datetime.datetime.now()
    elapsed = (now - last_update_time).total_seconds()
    return int(max(0, interval - elapsed))


def default_stock_market_state():
    """Return a fresh stock_market block for player_data."""
    return {
        "cycle_number": 1,
        "day_number": 1,
        "companies": [],
        "last_update_time": datetime.datetime.now().isoformat(),
        "trade_log": [],
    }


def truncate_credits(value):
    """Truncate credits to 2 decimal places (toward zero, never round up)."""
    return math.trunc(value * 100) / 100


def record_trade(player_data, cycle, day, side, company_name, shares, price, total):
    """Append or merge a buy/sell entry in the current cycle trade log."""
    if "stock_market" not in player_data:
        player_data["stock_market"] = {}

    if "trade_log" not in player_data["stock_market"]:
        player_data["stock_market"]["trade_log"] = []

    current_cycle_entry = None
    for entry in player_data["stock_market"]["trade_log"]:
        if entry.get("cycle") == cycle and entry.get("day") == day:
            current_cycle_entry = entry
            break

    if not current_cycle_entry:
        current_cycle_entry = {
            "cycle": cycle,
            "day": day,
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
    """Owns live market state and background tick logic."""

    def __init__(self, companies=None):
        self.companies = companies if companies is not None else create_default_companies()
        self.cycle_number = 1
        self.day_number = 1
        self.last_update_time = datetime.datetime.now()

    def tick_if_due(self):
        """Advance the market if the update interval has elapsed."""
        now = datetime.datetime.now()
        elapsed = (now - self.last_update_time).total_seconds()
        if elapsed < UPDATE_INTERVAL_SECONDS:
            return False

        for company in self.companies:
            company.update_value()

        self.cycle_number += 1
        if self.cycle_number > CYCLES_PER_DAY:
            self.cycle_number = 1
            self.day_number += 1

        self.last_update_time = now
        return True

    def sync_to_player_data(self, player_data):
        """Write current market state into player_data."""
        if "stock_market" not in player_data:
            player_data["stock_market"] = default_stock_market_state()

        sync_holdings_to_companies(self.companies, player_data.get("stock_holdings"))

        player_data["stock_market"].update({
            "cycle_number": self.cycle_number,
            "day_number": self.day_number,
            "companies": serialize_companies(self.companies),
            "last_update_time": self.last_update_time.isoformat(),
        })

        if "trade_log" not in player_data["stock_market"]:
            player_data["stock_market"]["trade_log"] = []

    def load_from_player_data(self, player_data):
        """Restore market state from player_data."""
        if "stock_market" not in player_data:
            return

        market_data = player_data["stock_market"]
        self.cycle_number = market_data.get("cycle_number", 0)
        self.day_number = market_data.get("day_number", 1)

        if "last_update_time" in market_data:
            try:
                self.last_update_time = datetime.datetime.fromisoformat(market_data["last_update_time"])
            except (ValueError, TypeError):
                self.last_update_time = datetime.datetime.now()
        else:
            self.last_update_time = datetime.datetime.now()

        migrate_stock_holdings_from_companies(player_data)

        if "companies" in market_data:
            refresh_companies_from_player_data(self.companies, player_data)


class StockMarket:
    def __init__(self, parent_window, player_data, companies, cycle_number, day_number, return_callback):
        # Create a new toplevel window
        self.stock_window = tk.Toplevel(parent_window)
        self.stock_window.title("Stock Market")
        self.stock_window.geometry("1000x850") 
        self.stock_window.configure(bg="black")
        
        # Set a minimum window size to prevent UI elements from getting cut off
        self.stock_window.minsize(900, 700)
        
        # Store references
        self.parent_window = parent_window
        self.player_data = player_data
        self.companies = companies
        self.cycle_number = cycle_number
        self.day_number = day_number
        self.return_callback = return_callback
        self.current_company = None
        
        # Track transactions for notes
        self.stock_transactions = []
        
        # Filter state
        self.current_filter = "All" # Default filter shows all stocks
        
        # Sort order: "price_asc" (low to high) or "price_desc" (high to low)
        self.sort_order = "price_asc"
        
        # Ownership filter: "all", "owned", "not_owned" 
        self.ownership_filter = "all"

        # Trend filter: "all", "rising", "falling"
        self.trend_filter = "all"
        
        # Bind window closing
        self.stock_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Ensure this window stays on top
        self.stock_window.transient(parent_window)
        self.stock_window.grab_set()
        
        # Load company owned shares from player data
        sync_holdings_to_companies(self.companies, player_data.get("stock_holdings"))
        
        # Create main frames
        self.left_frame = tk.Frame(self.stock_window, bg="black", width=300)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # Fixed bottom section for navigation buttons (aligns with trade controls)
        self.left_bottom_frame = tk.Frame(self.left_frame, bg="black")
        self.left_bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.history_btn = tk.Button(self.left_bottom_frame, text="View Trade History", 
                                   font=("Arial", 12), bg="#333333", fg="white",
                                   command=self.show_trade_history)
        self.history_btn.pack(pady=(5, 2), fill=tk.X)
        
        self.back_btn = tk.Button(self.left_bottom_frame, text="Back to Computer", 
                                font=("Arial", 12), bg="#333333", fg="white",
                                command=self.on_closing)
        self.back_btn.pack(pady=(2, 5), fill=tk.X)
        
        # Main content area above the fixed bottom buttons
        self.left_content = tk.Frame(self.left_frame, bg="black")
        self.left_content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.right_frame = tk.Frame(self.stock_window, bg="black")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info labels
        self.info_frame = tk.Frame(self.left_content, bg="black")
        self.info_frame.pack(fill=tk.X, pady=10)
        
        self.cycle_label = tk.Label(self.info_frame, text=f"Cycle: {self.cycle_number}", 
                                   font=("Arial", 12), bg="black", fg="white")
        self.cycle_label.grid(row=0, column=0, sticky="w", pady=2)
        
        self.day_label = tk.Label(self.info_frame, text=f"Day: {self.day_number}", 
                                 font=("Arial", 12), bg="black", fg="white")
        self.day_label.grid(row=1, column=0, sticky="w", pady=2)
        
        # Add timer for next update
        self.timer_label = tk.Label(self.info_frame, text="Next Update: Calculating...", 
                                  font=("Arial", 12), bg="black", fg="yellow")
        self.timer_label.grid(row=2, column=0, sticky="w", pady=2)
        
        self.credits_label = tk.Label(self.info_frame, text=f"Credits: {player_data['credits']:.2f}", 
                                    font=("Arial", 12), bg="black", fg="white")
        self.credits_label.grid(row=3, column=0, sticky="w", pady=2)
        
        # Sort and filter options
        self.filter_frame = tk.Frame(self.left_content, bg="black")
        self.filter_frame.pack(fill=tk.X, pady=5)
        
        filter_label = tk.Label(self.filter_frame, text="Filter Stocks:", 
                             font=("Arial", 12), bg="black", fg="white")
        filter_label.pack(anchor="w", pady=(5,0))
        
        # Filter buttons
        self.filter_buttons_frame = tk.Frame(self.filter_frame, bg="black")
        self.filter_buttons_frame.pack(fill=tk.X, pady=5)
        
        # Show All button
        self.all_btn = tk.Button(self.filter_buttons_frame, text="Show All", 
                            font=("Arial", 10), bg="#333333", fg="white", relief=tk.SUNKEN,
                            command=lambda: self.filter_companies("All"))
        self.all_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Affordable button (can buy at least 1 share)
        self.affordable_btn = tk.Button(self.filter_buttons_frame, text="Affordable", 
                                 font=("Arial", 10), bg="#333333", fg="white",
                                 command=lambda: self.filter_companies("Affordable"))
        self.affordable_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Expensive button (can't afford any shares)
        self.expensive_btn = tk.Button(self.filter_buttons_frame, text="Expensive", 
                                font=("Arial", 10), bg="#333333", fg="white",
                                command=lambda: self.filter_companies("Expensive"))
        self.expensive_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Sort options
        sort_label = tk.Label(self.filter_frame, text="Sort By Price:", 
                            font=("Arial", 12), bg="black", fg="white")
        sort_label.pack(anchor="w", pady=(10,0))
        
        # Sort buttons
        self.sort_buttons_frame = tk.Frame(self.filter_frame, bg="black")
        self.sort_buttons_frame.pack(fill=tk.X, pady=5)
        
        # Low to High button
        self.low_high_btn = tk.Button(self.sort_buttons_frame, text="Low to High", 
                                  font=("Arial", 10), bg="#333333", fg="white", relief=tk.SUNKEN,
                                  command=lambda: self.sort_companies("price_asc"))
        self.low_high_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # High to Low button
        self.high_low_btn = tk.Button(self.sort_buttons_frame, text="High to Low", 
                                  font=("Arial", 10), bg="#333333", fg="white",
                                  command=lambda: self.sort_companies("price_desc"))
        self.high_low_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Ownership filter options
        ownership_label = tk.Label(self.filter_frame, text="Ownership:", 
                                 font=("Arial", 12), bg="black", fg="white")
        ownership_label.pack(anchor="w", pady=(10,0))
        
        # Ownership filter buttons
        self.ownership_buttons_frame = tk.Frame(self.filter_frame, bg="black")
        self.ownership_buttons_frame.pack(fill=tk.X, pady=5)
        
        # All Stocks button
        self.all_ownership_btn = tk.Button(self.ownership_buttons_frame, text="All Stocks", 
                                          font=("Arial", 10), bg="#333333", fg="white", relief=tk.SUNKEN,
                                          command=lambda: self.filter_by_ownership("all"))
        self.all_ownership_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Owned Stocks button
        self.owned_btn = tk.Button(self.ownership_buttons_frame, text="Owned", 
                                  font=("Arial", 10), bg="#333333", fg="white",
                                  command=lambda: self.filter_by_ownership("owned"))
        self.owned_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Not Owned Stocks button
        self.not_owned_btn = tk.Button(self.ownership_buttons_frame, text="Not Owned", 
                                     font=("Arial", 10), bg="#333333", fg="white",
                                     command=lambda: self.filter_by_ownership("not_owned"))
        self.not_owned_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Trend filter options
        trend_label = tk.Label(self.filter_frame, text="Trend:",
                                 font=("Arial", 12), bg="black", fg="white")
        trend_label.pack(anchor="w", pady=(10, 0))

        self.trend_buttons_frame = tk.Frame(self.filter_frame, bg="black")
        self.trend_buttons_frame.pack(fill=tk.X, pady=5)

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
        
        # Companies list
        self.companies_listbox = tk.Listbox(self.left_content, 
                                         font=("Arial", 12), bg="black", fg="white",
                                         selectbackground="#333333", selectforeground="white",
                                         width=30)
        self.companies_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Right frame contents (will be populated when company is selected)
        self.trade_frame = tk.Frame(self.right_frame, bg="black")
        self.trade_frame.pack(side=tk.BOTTOM, pady=(5, 0))
        
        self.company_info_frame = tk.Frame(self.right_frame, bg="black")
        self.company_info_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        # Set up the figure for the graph
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
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind selection event for the listbox AFTER all frames are created
        self.companies_listbox.bind('<<ListboxSelect>>', self.on_company_select)
        
        # Add polling for player_data updates
        self.last_seen_cycle = cycle_number
        self.last_seen_day = day_number
        
        # Fill the companies listbox with all companies initially
        self.populate_companies_listbox()
        
        # Select first company by default AFTER everything is set up
        if self.companies_listbox.size() > 0:
            self.companies_listbox.selection_set(0)
            self.on_company_select(None)  # Trigger the selection handler
            
        # Start the timer
        self.update_timer()

    def _refresh_companies_from_player_data(self):
        """Apply saved company prices and ownership from player_data."""
        refresh_companies_from_player_data(self.companies, self.player_data)

    def _sync_cycle_day_from_player_data(self):
        """Update cycle/day labels from player_data if they changed."""
        market_data = self.player_data.get("stock_market", {})
        poll_cycle = market_data.get("cycle_number", 0)
        poll_day = market_data.get("day_number", 1)

        if poll_cycle != self.last_seen_cycle or poll_day != self.last_seen_day:
            self.cycle_number = poll_cycle
            self.day_number = poll_day
            self.last_seen_cycle = poll_cycle
            self.last_seen_day = poll_day
            self.cycle_label.config(text=f"Cycle: {self.cycle_number}")
            self.day_label.config(text=f"Day: {self.day_number}")
            return True

        return False
    
    def update_timer(self):
        """Update the countdown timer for next stock update"""
        cycle_day_changed = self._sync_cycle_day_from_player_data()
        if cycle_day_changed:
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

        if "stock_market" in self.player_data and "last_update_time" in self.player_data["stock_market"]:
            try:
                last_update = datetime.datetime.fromisoformat(self.player_data["stock_market"]["last_update_time"])
                remaining = get_seconds_until_update(last_update)

                if remaining <= 0:
                    self.timer_label.config(text="Updating Market...", fg="green")

                    if "stock_market" in self.player_data:
                        self.cycle_number = self.player_data["stock_market"].get("cycle_number", self.cycle_number)
                        self.day_number = self.player_data["stock_market"].get("day_number", self.day_number)
                        self.cycle_label.config(text=f"Cycle: {self.cycle_number}")
                        self.day_label.config(text=f"Day: {self.day_number}")
                        self._refresh_companies_from_player_data()

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
                                break
                        else:
                            if self.companies_listbox.size() > 0:
                                self.companies_listbox.selection_set(0)
                                self.on_company_select(None)
                    elif self.companies_listbox.size() > 0:
                        self.companies_listbox.selection_set(0)
                        self.on_company_select(None)

                    self.stock_window.after(1000, self.update_timer)
                    return

                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                self.timer_label.config(
                    text=f"Next Update: {minutes:02d}:{seconds:02d}",
                    fg="yellow" if remaining > 15 else "orange" if remaining > 5 else "red",
                )
            except (ValueError, TypeError):
                self.timer_label.config(text="Next Update: Unknown", fg="gray")
        else:
            self.timer_label.config(text="Next Update: Unknown", fg="gray")

        self.stock_window.after(1000, self.update_timer)
    
    def on_company_select(self, event):
        """Handle company selection from the listbox"""
        if not self.companies_listbox.curselection():
            return
        
        # Get the name of the selected company from the listbox
        selection_idx = self.companies_listbox.curselection()[0]
        selected_company_name = self.companies_listbox.get(selection_idx)
        
        # Find the actual company object by name
        for company in self.companies:
            if company.name == selected_company_name:
                self.current_company = company
                break
        else:
            # If company not found (should never happen), return
            return
        
        # Clear company info frame
        for widget in self.company_info_frame.winfo_children():
            widget.destroy()
        
        # Clear trade frame
        for widget in self.trade_frame.winfo_children():
            widget.destroy()
        
        # Add company information
        company_name = tk.Label(self.company_info_frame, text=self.current_company.name, 
                              font=("Arial", 18, "bold"), bg="black", fg="white")
        company_name.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        
        current_price = tk.Label(self.company_info_frame, text=f"Current Price: {self.current_company.current_value:.2f}", 
                               font=("Arial", 12), bg="black", fg="white")
        current_price.grid(row=1, column=0, sticky="w", pady=2)
        
        # Calculate price change
        price_change = self.current_company.current_value - self.current_company.previous_value
        price_change_pct = (price_change / self.current_company.previous_value) * 100
        
        # Choose color based on price change
        change_color = "green" if price_change >= 0 else "red"
        
        price_change_label = tk.Label(self.company_info_frame, 
                                    text=f"Change: {price_change:.2f} ({price_change_pct:.2f}%)", 
                                    font=("Arial", 12), bg="black", fg=change_color)
        price_change_label.grid(row=1, column=1, sticky="w", pady=2)
        
        shares_owned = tk.Label(self.company_info_frame, 
                              text=f"Shares Owned: {self.current_company.owned_shares}", 
                              font=("Arial", 12), bg="black", fg="white")
        shares_owned.grid(row=2, column=0, sticky="w", pady=2)
        
        # Calculate total value of owned shares
        total_value = self.current_company.owned_shares * self.current_company.current_value
        
        shares_value = tk.Label(self.company_info_frame, 
                              text=f"Total Value: {total_value:.2f}", 
                              font=("Arial", 12), bg="black", fg="white")
        shares_value.grid(row=2, column=1, sticky="w", pady=2)
        
        # Update the graph
        self.update_graph()
        
        # Add trade interface
        self.create_trade_interface()
    
    def update_graph(self):
        """Update the price history graph for the selected company"""
        if not self.current_company:
            return
            
        # Clear the axis
        self.ax.clear()
        
        # Set up the plot
        self.ax.set_facecolor('black')
        self.ax.tick_params(colors='white')
        
        # Plot the price history
        prices = self.current_company.price_history
        x = range(len(prices))
        
        # Determine plot color based on price trend
        if prices[-1] >= prices[0]:
            line_color = 'green'
        else:
            line_color = 'red'
            
        self.ax.plot(x, prices, color=line_color)
        
        # Set labels
        self.ax.set_title(f"{self.current_company.name} Price History", color='white')
        self.ax.set_xlabel("Cycles", color='white')
        self.ax.set_ylabel("Price", color='white')
        
        # Remove grid
        self.ax.grid(False)
        
        # Draw the canvas
        self.canvas.draw()
    
    def create_trade_interface(self):
        """Create the interface for buying and selling stocks"""
        # Shares to trade label and entry
        shares_label = tk.Label(self.trade_frame, text="Shares:", 
                              font=("Arial", 12), bg="black", fg="white")
        shares_label.grid(row=0, column=0, padx=5, pady=(5, 2))
        
        # Dropdown for predefined amounts
        share_options = [1, 5, 10, 25, 50, 100]
        self.shares_var = tk.StringVar(value="1")
        
        shares_dropdown = ttk.Combobox(self.trade_frame, textvariable=self.shares_var, 
                                     values=share_options, width=5)
        shares_dropdown.grid(row=0, column=1, padx=5, pady=(5, 2))
        
        # Make the dropdown user editable
        shares_dropdown.config(state="normal")
        
        # Calculate max shares that can be bought or sold
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
        
        # Calculate total cost
        def update_total_cost(*args):
            try:
                shares = int(self.shares_var.get())
                total = shares * self.current_company.current_value
                total_label.config(text=f"Total: {total:.2f}")
                
                # Update buy button state
                if shares > 0 and total <= self.player_data["credits"]:
                    buy_btn.config(state=tk.NORMAL)
                else:
                    buy_btn.config(state=tk.DISABLED)
                    
                # Update sell button state
                if shares > 0 and shares <= self.current_company.owned_shares:
                    sell_btn.config(state=tk.NORMAL)
                else:
                    sell_btn.config(state=tk.DISABLED)
                    
            except ValueError:
                total_label.config(text="Total: 0.00")
                buy_btn.config(state=tk.DISABLED)
                sell_btn.config(state=tk.DISABLED)
        
        # Register callback for share amount changes
        self.shares_var.trace("w", update_total_cost)
        
        # Total cost label
        total_label = tk.Label(self.trade_frame, text="Total: 0.00", 
                            font=("Arial", 12), bg="black", fg="white")
        total_label.grid(row=0, column=2, padx=20, pady=(5, 2))
        
        # Buy button
        buy_btn = tk.Button(self.trade_frame, text="Buy", font=("Arial", 12), 
                         bg="green", fg="white", width=8,
                         command=self.buy_stock)
        buy_btn.grid(row=2, column=0, padx=10, pady=10)
        
        # Sell button
        sell_btn = tk.Button(self.trade_frame, text="Sell", font=("Arial", 12), 
                          bg="red", fg="white", width=8,
                          command=self.sell_stock)
        sell_btn.grid(row=2, column=1, padx=10, pady=10)
        
        # Initialize button states
        update_total_cost()
    
    def buy_stock(self):
        """Buy stock of the currently selected company"""
        try:
            # Get share amount
            shares = int(self.shares_var.get())
            
            # Calculate total cost
            total_cost = shares * self.current_company.current_value
            
            # Check if player has enough credits
            if total_cost > self.player_data["credits"]:
                messagebox.showerror("Transaction Failed", "Not enough credits for this purchase.")
                return
                
            # Update player credits
            self.player_data["credits"] -= total_cost
            self.player_data["credits"] = truncate_credits(self.player_data["credits"])
            
            # Update company owned shares
            self.current_company.owned_shares += shares
            
            # Update stock holdings in player data
            if "stock_holdings" not in self.player_data:
                self.player_data["stock_holdings"] = {}
                
            if self.current_company.name not in self.player_data["stock_holdings"]:
                self.player_data["stock_holdings"][self.current_company.name] = shares
            else:
                self.player_data["stock_holdings"][self.current_company.name] += shares
            
            # Track transaction for notes
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
                self.day_number,
                "bought",
                self.current_company.name,
                shares,
                self.current_company.current_value,
                total_cost,
            )
            
            # Update display
            self.credits_label.config(text=f"Credits: {self.player_data['credits']:.2f}")
            
            # Recalculate max shares
            max_can_buy = int(self.player_data["credits"] / self.current_company.current_value)
            
            # Show success message
            messagebox.showinfo("Transaction Complete", 
                               f"Bought {shares} shares of {self.current_company.name} for {total_cost:.2f} credits.")
            
            # Refresh company info
            self.on_company_select(None)
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number of shares.")
    
    def sell_stock(self):
        """Sell stock of the currently selected company"""
        try:
            # Get share amount
            shares = int(self.shares_var.get())
            
            # Check if player owns enough shares
            if shares > self.current_company.owned_shares:
                messagebox.showerror("Transaction Failed", "You don't own that many shares.")
                return
                
            # Calculate total value
            total_value = shares * self.current_company.current_value
            
            # Update player credits
            self.player_data["credits"] += total_value
            self.player_data["credits"] = truncate_credits(self.player_data["credits"])
            
            # Update company owned shares
            self.current_company.owned_shares -= shares
            
            # Update stock holdings in player data
            if "stock_holdings" in self.player_data and self.current_company.name in self.player_data["stock_holdings"]:
                self.player_data["stock_holdings"][self.current_company.name] -= shares
                
                # Remove entry if no shares left
                if self.player_data["stock_holdings"][self.current_company.name] <= 0:
                    del self.player_data["stock_holdings"][self.current_company.name]
            
            # Calculate profit/loss if we have the purchase price history
            profit = 0
            if "stock_purchases" in self.player_data and self.current_company.name in self.player_data["stock_purchases"]:
                # Get the average purchase price of shares
                purchases = self.player_data["stock_purchases"][self.current_company.name]
                if len(purchases) > 0:
                    # Calculate average purchase price of shares being sold
                    total_cost = sum(purchase["price"] * purchase["shares"] for purchase in purchases[:shares])
                    avg_price = total_cost / shares if shares > 0 else 0
                    
                    # Calculate profit/loss
                    profit = total_value - (avg_price * shares)
            
            # Track transaction for notes
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
                self.day_number,
                "sold",
                self.current_company.name,
                shares,
                self.current_company.current_value,
                total_value,
            )
            
            # Update display
            self.credits_label.config(text=f"Credits: {self.player_data['credits']:.2f}")
            
            # Success message
            profit_text = ""
            if profit != 0:
                if profit > 0:
                    profit_text = f" (Profit: {profit:.2f} credits)"
                else:
                    profit_text = f" (Loss: {abs(profit):.2f} credits)"
                    
            messagebox.showinfo("Transaction Complete", 
                               f"Sold {shares} shares of {self.current_company.name} for {total_value:.2f} credits.{profit_text}")
            
            # Refresh company info
            self.on_company_select(None)
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number of shares.")
    
    def show_trade_history(self):
        """Show the trade history log"""
        # Create a new toplevel window
        history_window = tk.Toplevel(self.stock_window)
        history_window.title("Trade History")
        history_window.geometry("650x550")  # Increased size for better visibility
        history_window.configure(bg="black")
        
        # Set minimum size
        history_window.minsize(500, 400)
        
        # Ensure this window stays on top
        history_window.transient(self.stock_window)
        history_window.grab_set()
        
        # Title
        title_label = tk.Label(history_window, text="Trade History", 
                             font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)
        
        # Create frame with scrollbar
        frame = tk.Frame(history_window, bg="black")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Add a scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create the trade log text widget with tags for color formatting
        trade_log = tk.Text(frame, font=("Arial", 12), 
                          bg="black", fg="white", width=60, height=20,
                          yscrollcommand=scrollbar.set, wrap=tk.WORD)
        trade_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=trade_log.yview)
        
        # Create tags for colored text
        trade_log.tag_configure("header", foreground="yellow", font=("Arial", 14, "bold"))
        trade_log.tag_configure("cycle", foreground="cyan", font=("Arial", 12, "bold"))
        trade_log.tag_configure("bought", foreground="green", font=("Arial", 12))
        trade_log.tag_configure("sold", foreground="red", font=("Arial", 12))
        trade_log.tag_configure("company", foreground="white", font=("Arial", 12))
        
        # Populate the trade log
        if "stock_market" in self.player_data and "trade_log" in self.player_data["stock_market"]:
            trade_log.insert(tk.END, "TRADE HISTORY\n\n", "header")
            
            # Display trade log entries in reverse order (newest first)
            for entry in reversed(self.player_data["stock_market"]["trade_log"]):
                cycle = entry.get("cycle", 0)
                day = entry.get("day", 0)
                trade_log.insert(tk.END, f"Cycle {cycle} (Day {day}):\n", "cycle")
                
                trades = entry.get("trades", {})
                
                # Bought trades
                if "bought" in trades and trades["bought"]:
                    trade_log.insert(tk.END, "  BOUGHT:\n", "bought")
                    for company, data in trades["bought"].items():
                        amount = data.get("amount", 0)
                        price = data.get("price", 0)
                        total = data.get("total", 0)
                        trade_log.insert(tk.END, f"    {company}: {amount} shares @ {price:.2f} cr each = {total:.2f} cr\n", "company")
                
                # Sold trades
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
        
        # Make the text widget read-only
        trade_log.config(state=tk.DISABLED)
        
        # Mouse wheel binding for scrolling
        def _on_trade_mousewheel(event):
            try:
                # Windows style scrolling (positive or negative delta)
                trade_log.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception as e:
                try:
                    # Linux style scrolling (positive delta for scroll up, negative for down)
                    if event.num == 4:
                        trade_log.yview_scroll(-1, "units")
                    elif event.num == 5:
                        trade_log.yview_scroll(1, "units")
                except:
                    pass  # Ignore errors if the widget was destroyed
        
        # Bind mousewheel to trade log and all parent widgets to ensure it works everywhere
        trade_log.bind("<MouseWheel>", _on_trade_mousewheel)  # Windows
        trade_log.bind("<Button-4>", _on_trade_mousewheel)    # Linux scroll up
        trade_log.bind("<Button-5>", _on_trade_mousewheel)    # Linux scroll down
        
        frame.bind("<MouseWheel>", _on_trade_mousewheel)
        frame.bind("<Button-4>", _on_trade_mousewheel)
        frame.bind("<Button-5>", _on_trade_mousewheel)
        
        history_window.bind("<MouseWheel>", _on_trade_mousewheel)
        history_window.bind("<Button-4>", _on_trade_mousewheel)
        history_window.bind("<Button-5>", _on_trade_mousewheel)
        
        # Override destroy method to cleanup bindings
        orig_destroy = history_window.destroy
        def _destroy_and_cleanup():
            try:
                history_window.unbind("<MouseWheel>")
                history_window.unbind("<Button-4>")
                history_window.unbind("<Button-5>")
            except:
                pass
            orig_destroy()
        
        history_window.destroy = _destroy_and_cleanup
        
        # Close button
        close_btn = tk.Button(history_window, text="Close", 
                            font=("Arial", 12), bg="#333333", fg="white",
                            command=history_window.destroy)
        close_btn.pack(pady=10)
    
    def on_closing(self):
        """Handle window closing"""
        # Add the stock transactions to the player data to be logged as notes
        if self.stock_transactions:
            self.player_data["stock_transactions"] = self.stock_transactions
        
        # Release the grab and return control to the parent window
        self.stock_window.grab_release()
        
        # Return player data to the main game
        if self.return_callback:
            self.return_callback(self.player_data)
            
        # Destroy the window
        self.stock_window.destroy()
    
    def filter_companies(self, filter_type):
        """Filter companies based on selected filter"""
        # Update filter state
        self.current_filter = filter_type
        
        # Update button appearance
        self.all_btn.config(relief=tk.RAISED)
        self.affordable_btn.config(relief=tk.RAISED)
        self.expensive_btn.config(relief=tk.RAISED)
        
        if filter_type == "All":
            self.all_btn.config(relief=tk.SUNKEN)
        elif filter_type == "Affordable":
            self.affordable_btn.config(relief=tk.SUNKEN)
        elif filter_type == "Expensive":
            self.expensive_btn.config(relief=tk.SUNKEN)
        
        # Preserve selection if possible
        selected_company = None
        if self.companies_listbox.curselection():
            selected_idx = self.companies_listbox.curselection()[0]
            if selected_idx < self.companies_listbox.size():
                selected_company = self.companies_listbox.get(selected_idx)
        
        # Repopulate the listbox with filtered companies
        self.populate_companies_listbox()
        
        # Try to restore selection
        if selected_company:
            for i in range(self.companies_listbox.size()):
                if self.companies_listbox.get(i) == selected_company:
                    self.companies_listbox.selection_set(i)
                    self.companies_listbox.see(i)
                    self.on_company_select(None)  # Explicitly call after selection is restored
                    return
        
        # If previous selection not found, select the first item if any exist
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
        
        # Preserve selection if possible
        selected_company = None
        if self.companies_listbox.curselection():
            selected_idx = self.companies_listbox.curselection()[0]
            if selected_idx < self.companies_listbox.size():
                selected_company = self.companies_listbox.get(selected_idx)
        
        # Repopulate the listbox with sorted companies
        self.populate_companies_listbox()
        
        # Try to restore selection
        if selected_company:
            for i in range(self.companies_listbox.size()):
                if self.companies_listbox.get(i) == selected_company:
                    self.companies_listbox.selection_set(i)
                    self.companies_listbox.see(i)
                    self.on_company_select(None)  # Explicitly call after selection is restored
                    return
        
        # If previous selection not found, select the first item if any exist
        if self.companies_listbox.size() > 0:
            self.companies_listbox.selection_set(0)
            self.on_company_select(None)  # Explicitly call after selection is made
    
    def filter_by_ownership(self, ownership_filter):
        """Filter companies based on ownership"""
        # Update filter state
        self.ownership_filter = ownership_filter
        
        # Update button appearance
        self.all_ownership_btn.config(relief=tk.RAISED)
        self.owned_btn.config(relief=tk.RAISED)
        self.not_owned_btn.config(relief=tk.RAISED)
        
        if ownership_filter == "all":
            self.all_ownership_btn.config(relief=tk.SUNKEN)
        elif ownership_filter == "owned":
            self.owned_btn.config(relief=tk.SUNKEN)
        elif ownership_filter == "not_owned":
            self.not_owned_btn.config(relief=tk.SUNKEN)
        
        # Preserve selection if possible
        selected_company = None
        if self.companies_listbox.curselection():
            selected_idx = self.companies_listbox.curselection()[0]
            if selected_idx < self.companies_listbox.size():
                selected_company = self.companies_listbox.get(selected_idx)
        
        # Repopulate the listbox with filtered companies
        self.populate_companies_listbox()
        
        # Try to restore selection
        if selected_company:
            for i in range(self.companies_listbox.size()):
                if self.companies_listbox.get(i) == selected_company:
                    self.companies_listbox.selection_set(i)
                    self.companies_listbox.see(i)
                    self.on_company_select(None)  # Explicitly call after selection is restored
                    return
        
        # If previous selection not found, select the first item if any exist
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
        # Clear current contents
        self.companies_listbox.delete(0, tk.END)
        
        # Get player credits for affordability check
        player_credits = self.player_data["credits"]
        
        # Prepare filtered and sorted companies list
        filtered_companies = []
        
        for company in self.companies:
            # Calculate exactly how many shares can be bought
            max_shares = player_credits // company.current_value  # Integer division to get whole shares
            can_afford = max_shares >= 1  # Can afford if at least 1 whole share can be bought
            
            # Check if company passes the affordability filter
            passes_affordability = (
                self.current_filter == "All" or
                (self.current_filter == "Affordable" and can_afford) or
                (self.current_filter == "Expensive" and not can_afford)
            )
            
            # Check if company passes the ownership filter
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
            
            # Add to filtered list if it passes all filters
            if passes_affordability and passes_ownership and passes_trend:
                filtered_companies.append((company.name, company.current_value, price_change))
        
        # Sort the filtered companies
        if self.sort_order == "price_asc":
            filtered_companies.sort(key=lambda x: x[1])
        else:
            filtered_companies.sort(key=lambda x: x[1], reverse=True)
        
        # Add sorted companies to the listbox
        for company_name, price, _price_change in filtered_companies:
            # Add company to listbox
            self.companies_listbox.insert(tk.END, company_name)
        
        # Do NOT automatically select a company here - that happens in __init__ or filter_companies
    
