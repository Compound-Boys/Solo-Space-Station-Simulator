import tkinter as tk
import json
import os
import time
import threading
import datetime
import random
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk, PhotoImage

# Add the stock market imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Import the StockMarket class
from game.stock_market import StockMarket
from game.stock_market import Company

# Import the Game class correctly
from game.game import Game

# Import special room classes
from game.special_rooms import MedBay, Bridge, Security, Engineering, Bar, Botany

# Import item helper
from game.items import get_item_definition, ALL_ITEMS, ItemInventoryMixin

# Import the character creation screen
from game.character_creation import CharacterCreation

# Import shared power constants
from game.power_constants import (
    SYSTEM_POWER_RATES,
    LOW_POWER_SYSTEM_LEVELS,
    HIGH_MODE_SOLAR_DRAIN,
    calculate_discharge,
    calculate_solar_charge,
)

class SpaceStationGame(ItemInventoryMixin):
    def __init__(self, root, base_path):
        self.root = root
        self.base_path = base_path
        self.root.title("Space Station 13 Text Clone")
        self.root.geometry("800x600")
        self.root.configure(bg="black")
        
        # Initialize variables
        self.previous_position = None
        self.market_running = False
        self.market_thread = None
        self.last_update_time = datetime.datetime.now()
        self.station_crew = [] # Initialize crew list here
        
        # Initialize battery timer
        self.battery_timer_running = False
        self.battery_timer_id = None
        
        # Store base path for file operations
        self.base_path = base_path
        
        # Stock market background tracking
        self.companies = [
            Company("TechCorp", random.uniform(10, 1000)),
            Company("GlobalBank", random.uniform(10, 1000)),
            Company("HealthCare Plus", random.uniform(10, 1000)),
            Company("EnergyCo", random.uniform(10, 1000)),
            Company("FoodChain", random.uniform(10, 1000)),
            Company("AutoMakers", random.uniform(10, 1000)),
            Company("RetailGiant", random.uniform(10, 1000)),
            Company("PharmaTech", random.uniform(10, 1000)),
            Company("RealEstate Co", random.uniform(10, 1000)),
            Company("MediaGroup", random.uniform(10, 1000)),
            Company("Aerospace Inc", random.uniform(10, 1000)),
            Company("TechStart", random.uniform(10, 1000)),
            Company("GreenEnergy", random.uniform(10, 1000)),
            Company("DigitalBank", random.uniform(10, 1000)),
            Company("SmartHome", random.uniform(10, 1000))
        ]

        # Generate 5 cycles of history for each company
        for _ in range(5):
            for company in self.companies:
                company.update_value()

        self.stock_cycle_number = 1
        self.stock_day_number = 1
        
        self.player_data = {
            "name": "",
            "job": "",
            "department": "",
            "subdepartment": "",
            "inventory": [],
            "credits": 1000,  # Add credits to player data
            "location": {"x": 0, "y": 0},  # Add location data for hallway navigation
            "stock_holdings": {},  # Add stock holdings data
            "stock_market": {
                "cycle_number": 1,
                "day_number": 1,
                "companies": [],
                "last_update_time": datetime.datetime.now().isoformat(),
                "trade_log": []  # Add trade log to persist between sessions
            },
            "limbs": {
                "left_arm": 100,
                "right_arm": 100,
                "left_leg": 100,
                "right_leg": 100,
                "chest": 100,
                "head": 100
            },
            "damage": {
                "burn": 0,
                "poison": 0,
                "oxygen": 0
            },
            "station_power": {
                "battery_level": 25.0,
                "solar_charging": False,
                "last_update_time": datetime.datetime.now().isoformat(),
                "system_levels": {
                    "life_support": 10,
                    "hallway_lighting": 5,
                    "security_systems": 7,
                    "communication_array": 5
                },
                "power_mode": "balanced"
            },
            "notes": []  # Add notes array to track important events
        }
        
        # Ship map configuration - Updated to include Botany Lab
        self.ship_map = {
            "-1,0": {"name": "Quarters", "desc": "Your personal quarters on the station."},
            "0,0": {"name": "Hallway Junction", "desc": "A junction in the hallway. Your quarters are nearby."},
            "1,0": {"name": "North Hallway", "desc": "A long hallway stretching north."},
            "2,0": {"name": "North Hallway", "desc": "A long hallway stretching north."},
            "3,0": {"name": "North Hallway", "desc": "A long hallway stretching north. You notice a door labeled 'Botany Lab' on the west wall."},
            "4,0": {"name": "North Hallway", "desc": "A long hallway stretching north."},
            "5,0": {"name": "North End", "desc": "The northern end of the hallway. The bridge is nearby."},
            "0,1": {"name": "East Hallway", "desc": "A long hallway stretching east."},
            "0,2": {"name": "East Hallway", "desc": "A long hallway stretching east."},
            "0,3": {"name": "Bar Entrance", "desc": "This hallway leads to the station Bar. Soft music can be heard from inside."},
            "0,4": {"name": "East Hallway", "desc": "A long hallway stretching east."},
            "0,5": {"name": "East End", "desc": "The eastern end of the hallway. The medbay is nearby."},
            
            # Northeast Corridors
            "5,1": {"name": "Northeast Hallway", "desc": "A hallway connecting the north and east corridors."},
            "5,2": {"name": "Northeast Hallway", "desc": "A hallway connecting the north and east corridors."},
            "5,3": {"name": "Engineering Bay Entrance", "desc": "This hallway leads to the Engineering Bay."},
            "5,4": {"name": "Northeast Hallway", "desc": "A hallway connecting the north and east corridors."},
            "5,5": {"name": "Northeast Corner", "desc": "The far corner of the station. Security is nearby."},
            
            # East Section
            "4,5": {"name": "East Section", "desc": "A hallway along the eastern side of the station."},
            "3,5": {"name": "East Section", "desc": "A hallway along the eastern side of the station."},
            "2,5": {"name": "East Section", "desc": "A hallway along the eastern side of the station."},
            "1,5": {"name": "East Section", "desc": "A hallway connecting back to the main hallways."},
            
            # Special Rooms (Locked)
            "6,0": {"name": "Bridge", "desc": "The control center of the station. The door is unlocked.", "locked": False},
            "0,6": {"name": "MedBay", "desc": "The medical facility of the station. The door is unlocked.", "locked": False},
            "6,6": {"name": "Security", "desc": "The security center of the station. The door is unlocked.", "locked": False},
            "6,3": {"name": "Engineering Bay", "desc": "The station's engineering and maintenance center. The door is unlocked.", "locked": False},
            "0,-1": {"name": "Bar", "desc": "The station's social hub where crew members can relax and enjoy drinks. The door is unlocked.", "locked": False},
            "3,-1": {"name": "Botany Lab", "desc": "The station's plant cultivation and research facility. The door is unlocked.", "locked": False}
        }
        
        # Bind the window close event to stop the market thread
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.show_main_menu()
    
    def on_closing(self):
        """Handle application closing"""
        # Stop the market thread
        self.stop_market_thread()
        
        # Stop the battery timer
        self.stop_battery_timer()
        
        # Save the game before closing if a game is in progress
        if self.player_data and self.player_data.get("name"):
            # Update market data one last time
            self.update_market_data()
            
            # Save the game
            Game.save_game(self.player_data)
        
        # Destroy the window
        self.root.destroy()
    
    def start_market_thread(self):
        if not self.market_running:
            self.market_running = True
            self.market_thread = threading.Thread(target=self.run_stock_market, daemon=True)
            self.market_thread.start()
    
    def stop_market_thread(self):
        self.market_running = False
        if self.market_thread and self.market_thread.is_alive():
            self.market_thread.join(1)  # Give it 1 second to finish
            
    def stop_battery_timer(self):
        """Stop the battery timer if it's running"""
        self.battery_timer_running = False
        if self.battery_timer_id:
            self.root.after_cancel(self.battery_timer_id)
            self.battery_timer_id = None
            
    def start_battery_timer(self):
        """Start the timer that handles battery discharge and charging"""
        if not self.battery_timer_running:
            print("Starting battery timer...")
            self.battery_timer_running = True
            self.update_battery()
        else:
            print("Battery timer already running")
    
    def update_battery(self):
        """Update the battery level - discharge based on system power levels, charge based on solar panel status"""
        if not self.battery_timer_running:
            return
            
        # Ensure station_power exists in player data
        if "station_power" not in self.player_data:
            self.player_data["station_power"] = {
                "battery_level": 25.0,
                "solar_charging": False,
                "last_update_time": datetime.datetime.now().isoformat(),
                "system_levels": {
                    "life_support": 10,
                    "hallway_lighting": 5,
                    "security_systems": 7,
                    "communication_array": 5
                },
                "power_mode": "balanced"
            }
        
        try:
            # Get the last update time
            last_update = datetime.datetime.fromisoformat(self.player_data["station_power"]["last_update_time"])
            now = datetime.datetime.now()
            elapsed_seconds = (now - last_update).total_seconds()
            
            # Get system power levels from player data
            system_levels = self.player_data["station_power"]["system_levels"]
            total_discharge_rate = calculate_discharge(system_levels, elapsed_seconds)
                    
            # Debug print
            # print(f"Power draw - Life support: {system_levels.get('life_support', 0)}/10, "
            #       f"Lighting: {system_levels.get('hallway_lighting', 0)}/10, "
            #       f"Security: {system_levels.get('security_systems', 0)}/10, "
            #       f"Comms: {system_levels.get('communication_array', 0)}/10")
            
            # If solar charging is active, apply a flat charge rate
            solar_charging = self.player_data["station_power"]["solar_charging"]
            charge_rate = calculate_solar_charge(elapsed_seconds, solar_charging)
            
            # Net change to battery level (power mode adjusts behavior when solar is on)
            power_mode = self.player_data["station_power"].get("power_mode", "balanced")
            if solar_charging:
                if power_mode == "high":
                    net_change = -(elapsed_seconds / 60) * HIGH_MODE_SOLAR_DRAIN
                elif power_mode == "balanced":
                    net_change = 0
                elif power_mode == "low":
                    net_change = charge_rate - total_discharge_rate
                elif power_mode == "emergency":
                    low_discharge = calculate_discharge(LOW_POWER_SYSTEM_LEVELS, elapsed_seconds)
                    low_net = charge_rate - low_discharge
                    net_change = 1.5 * low_net
                else:
                    net_change = charge_rate - total_discharge_rate
            else:
                net_change = charge_rate - total_discharge_rate
            
            # Update battery level
            current_level = self.player_data["station_power"]["battery_level"]
            new_level = max(0, min(100, current_level + net_change))
            
            # Debug print for battery changes
            # print(f"Battery update: {current_level:.2f}% -> {new_level:.2f}%, Solar: {self.player_data['station_power']['solar_charging']}, Net Change: {net_change:.4f}% (Charge: {charge_rate:.4f}%, Discharge: {total_discharge_rate:.4f}%)")
            
            # Update player data with new battery level
            self.player_data["station_power"]["battery_level"] = new_level
            self.player_data["station_power"]["last_update_time"] = now.isoformat()
            
            # Check oxygen levels based on life support setting
            self.check_life_support_status(elapsed_seconds)
            
            # If battery level reaches critical point, trigger effects
            if 0 < new_level <= 10:
                # Flash warning messages occasionally when battery is low
                if random.random() < 0.2:  # 20% chance on each check
                    self.show_low_power_warning()
            elif new_level <= 0:
                # Battery completely drained - trigger power outage
                self.trigger_power_outage()
            
            # Lights are affected when battery level is low
            if current_level > 10 and new_level <= 10:
                # Transition to low power lighting
                self.update_corridor_lighting(low_power=True)
            elif current_level <= 10 and new_level > 10:
                # Transition back to normal lighting
                self.update_corridor_lighting(low_power=False)
        except Exception as e:
            print(f"Error updating battery: {e}")
            # Reset the timer in case of error
            self.player_data["station_power"]["last_update_time"] = datetime.datetime.now().isoformat()
        
        # Schedule next update in 2 seconds (was 5 seconds) to make changes more apparent
        self.battery_timer_id = self.root.after(2000, self.update_battery)
    
    def check_life_support_status(self, elapsed_seconds):
        """Check life support status and apply oxygen damage to player and NPCs if necessary"""
        try:
            # Get life support level
            life_support_level = self.player_data["station_power"]["system_levels"].get("life_support", 10)
            
            # Combine player and NPCs for processing
            all_crew = [self.player_data] + self.station_crew
            
            # Determine damage or recovery rates based on life support level
            oxygen_damage_rate = 0
            recovery_rate_per_second = 0
            apply_damage = False
            apply_recovery = False
            
            if life_support_level == 0:
                # Life support OFF: High oxygen damage rate (10% per minute)
                oxygen_damage_rate = (elapsed_seconds * (10 / 60.0))
                max_damage_per_update = 10.0  # Limit max damage per update
                oxygen_damage_rate = min(oxygen_damage_rate, max_damage_per_update)
                apply_damage = True
            elif life_support_level < 5:
                # Life support LOW: Slow oxygen damage rate (5% per minute)
                oxygen_damage_rate = (elapsed_seconds * (5 / 60.0))
                max_damage_per_update = 5.0 # Limit max damage per update
                oxygen_damage_rate = min(oxygen_damage_rate, max_damage_per_update)
                apply_damage = True
            else:
                # Life support FUNCTIONAL: Recover oxygen damage (1% per 30 seconds)
                recovery_rate_per_second = 1 / 30.0
                apply_recovery = True
                
            # Apply damage or recovery to all crew members
            for crew_member in all_crew:
                is_player = (crew_member == self.player_data)
                current_oxygen_damage = crew_member["damage"].get("oxygen", 0)
                
                if apply_damage and oxygen_damage_rate > 0:
                    new_oxygen_damage = min(100, current_oxygen_damage + oxygen_damage_rate)
                    crew_member["damage"]["oxygen"] = new_oxygen_damage
                    
                    # Show warnings/handle death only for the player for now
                    if is_player:
                        print(f"Player Oxygen damage: Current={current_oxygen_damage:.1f}%, Adding={oxygen_damage_rate:.1f}% -> New={new_oxygen_damage:.1f}% (elapsed={elapsed_seconds:.1f}s)")
                        if current_oxygen_damage < 30 and new_oxygen_damage >= 30:
                            self.show_oxygen_warning(30)
                        elif current_oxygen_damage < 60 and new_oxygen_damage >= 60:
                            self.show_oxygen_warning(60)
                        elif current_oxygen_damage < 90 and new_oxygen_damage >= 90:
                            self.show_oxygen_warning(90)
                        if new_oxygen_damage >= 100:
                            self.handle_oxygen_death()
                    else:
                        # Optional: Add logic here if NPCs should react to low oxygen (e.g., log event, change behavior)
                        pass
                        
                elif apply_recovery and current_oxygen_damage > 0:
                    recovery_amount = min(current_oxygen_damage, elapsed_seconds * recovery_rate_per_second)
                    new_oxygen_damage = max(0, current_oxygen_damage - recovery_amount)
                    crew_member["damage"]["oxygen"] = new_oxygen_damage
                    
                    if is_player:
                         print(f"Player Oxygen recovery: Current={current_oxygen_damage:.1f}%, Recovered={recovery_amount:.1f}% -> New={new_oxygen_damage:.1f}% (elapsed={elapsed_seconds:.1f}s)")
                    else:
                        # Optional: Log NPC recovery
                        pass
                        
        except Exception as e:
            print(f"Error checking life support status for crew: {e}")
    
    def show_oxygen_warning(self, threshold):
        """Show a warning about oxygen levels"""
        warnings = {
            30: "You're feeling light-headed and having difficulty breathing. Oxygen levels are dropping.",
            60: "Your vision is beginning to blur and you're experiencing severe difficulty breathing. Oxygen deprivation is worsening.",
            90: "You're on the verge of losing consciousness. Severe oxygen deprivation detected. Immediate action required."
        }
        
        try:
            window = self.root.focus_get()
            if window:
                messagebox.showwarning("Oxygen Warning", warnings[threshold], parent=window)
            else:
                messagebox.showwarning("Oxygen Warning", warnings[threshold], parent=self.root)
                
            # Add note about oxygen damage
            self.add_note(f"Suffered {threshold}% oxygen damage due to life support failure.")
        except Exception as e:
            print(f"Error showing oxygen warning: {e}")
            
    def handle_oxygen_death(self):
        """Handle player death from oxygen deprivation"""
        try:
            # Show death message
            messagebox.showerror("CRITICAL: Oxygen Depleted", 
                              "You have succumbed to oxygen deprivation. Emergency medical protocols have been activated, and you have been revived at minimal health levels.",
                              parent=self.root)
            
            # Reset oxygen damage
            self.player_data["damage"]["oxygen"] = 50
            
            # Set all limbs to critical levels
            for limb in self.player_data["limbs"]:
                self.player_data["limbs"][limb] = 20
                
            # Add note about near-death
            self.add_note("CRITICAL EVENT: Nearly died from oxygen deprivation. Emergency medical systems intervened.")
            
            # Return player to quarters
            self.player_data["location"] = {"x": 0, "y": 0}
            self.show_room()
        except Exception as e:
            print(f"Error handling oxygen death: {e}")
    
    def show_low_power_warning(self):
        """Show warning about low battery power"""
        try:
            window = self.root.focus_get()
            if window:
                messagebox.showwarning("Low Power Warning", 
                                     "Warning: Station battery power low. Emergency lighting active. Please activate solar panels.",
                                     parent=window)
        except:
            # Fall back to main window if there's an error
            messagebox.showwarning("Low Power Warning", 
                                 "Warning: Station battery power low. Emergency lighting active. Please activate solar panels.",
                                 parent=self.root)
    
    def trigger_power_outage(self):
        """Trigger effects of a complete power outage"""
        try:
            # Set battery to minimum level to prevent multiple outage triggers
            self.player_data["station_power"]["battery_level"] = 0.1
            
            window = self.root.focus_get()
            if window:
                messagebox.showerror("Power Outage", 
                                   "CRITICAL: Station power failure! Emergency systems active. Activate solar arrays immediately!",
                                   parent=window)
            else:
                messagebox.showerror("Power Outage", 
                                   "CRITICAL: Station power failure! Emergency systems active. Activate solar arrays immediately!",
                                   parent=self.root)
            
            # Update corridor lighting to emergency mode
            self.update_corridor_lighting(emergency=True)
            
            # Add a note about the power failure
            self.add_note("CRITICAL: Station suffered complete power failure. Emergency systems active.")
            
        except Exception as e:
            print(f"Error handling power outage: {e}")
    
    def update_corridor_lighting(self, low_power=False, emergency=False):
        """Update the lighting in corridors based on power status"""
        # This would update the visual appearance of hallways 
        # For now we'll just print a message to see the feature working
        if emergency:
            print("Station lighting switched to emergency backup power - red emergency lights only")
            # In a real implementation, you would change the background color to dark red
            # You could also modify the description of hallways
        elif low_power:
            print("Station lighting dimmed to conserve power")
            # In a real implementation, you would change the hallway background to a darker shade
        else:
            print("Station lighting restored to normal levels")
            # In a real implementation, you would restore normal hallway appearance
    
    def run_stock_market(self):
        """Run the stock market in the background"""
        while self.market_running:
            # Calculate time until next update
            now = datetime.datetime.now()
            elapsed = (now - self.last_update_time).total_seconds()
            
            # If 60 seconds have passed since last update
            if elapsed >= 60:
                # Update all companies
                for company in self.companies:
                    company.update_value()
                
                # Update cycle and day numbers
                self.stock_cycle_number += 1
                
                # Check if we completed a full cycle (1-5)
                if self.stock_cycle_number > 5:
                    # Reset cycle to 1 and increment day
                    self.stock_cycle_number = 1
                    self.stock_day_number += 1
                
                # Update last update time
                self.last_update_time = now
                
                # Immediately update player data with new market state
                # This ensures all UI windows have access to the latest data
                self.update_market_data()
                
                # Process any pending trades if any
                self.process_pending_trades()
                
                # Log market update
                # print(f"Market updated: Cycle {self.stock_cycle_number}, Day {self.stock_day_number}")
            
            # Sleep for 1 second before checking again
            time.sleep(1)
    
    def process_pending_trades(self):
        """Process any pending trades in the player data"""
        if "pending_trades" in self.player_data["stock_market"]:
            pending = self.player_data["stock_market"]["pending_trades"]
            if pending and (pending.get('bought') or pending.get('sold')):
                # Check if we already have a trade log for this cycle
                if "trade_log" not in self.player_data["stock_market"]:
                    self.player_data["stock_market"]["trade_log"] = []
                
                # Check if there's already an entry for the current cycle
                current_cycle_log = None
                for entry in self.player_data["stock_market"]["trade_log"]:
                    if entry.get("cycle") == self.stock_cycle_number and entry.get("day") == self.stock_day_number:
                        current_cycle_log = entry
                        break
                
                # Only create an entry if there are actual trades
                has_trades = False
                if pending.get('bought'):
                    has_trades = any(trade.get('amount', 0) > 0 for trade in pending['bought'].values())
                if not has_trades and pending.get('sold'):
                    has_trades = any(trade.get('amount', 0) > 0 for trade in pending['sold'].values())
                
                if current_cycle_log and has_trades:
                    # Update existing entry for this cycle
                    trades = current_cycle_log.get("trades", {})
                    
                    # Update bought trades
                    if 'bought' in pending:
                        if 'bought' not in trades:
                            trades['bought'] = {}
                        for company, trade_data in pending['bought'].items():
                            amount = trade_data.get('amount', 0)
                            if amount > 0:  # Only process trades with non-zero amounts
                                if company in trades['bought']:
                                    # Merge the trades
                                    trades['bought'][company]['amount'] += amount
                                    trades['bought'][company]['total'] += trade_data.get('total', 0)
                                else:
                                    # Add new company trades
                                    trades['bought'][company] = trade_data
                    
                    # Update sold trades
                    if 'sold' in pending:
                        if 'sold' not in trades:
                            trades['sold'] = {}
                        for company, trade_data in pending['sold'].items():
                            amount = trade_data.get('amount', 0)
                            if amount > 0:  # Only process trades with non-zero amounts
                                if company in trades['sold']:
                                    # Merge the trades
                                    trades['sold'][company]['amount'] += amount
                                    trades['sold'][company]['total'] += trade_data.get('total', 0)
                                else:
                                    # Add new company trades
                                    trades['sold'][company] = trade_data
                    
                    # Update the trades in the current cycle log
                    current_cycle_log["trades"] = trades
                    
                elif has_trades:
                    # Add new trade entry for this cycle
                    trade_entry = {
                        "cycle": self.stock_cycle_number,
                        "day": self.stock_day_number,
                        "trades": pending
                    }
                    self.player_data["stock_market"]["trade_log"].append(trade_entry)
                
                # Clear pending trades
                self.player_data["stock_market"]["pending_trades"] = {}
    
    def update_market_data(self):
        """Update player data with current market state"""
        # Store company data
        company_data = []
        for company in self.companies:
            company_data.append({
                "name": company.name,
                "current_value": company.current_value,
                "previous_value": company.previous_value,
                "price_history": company.price_history,
                "owned_shares": company.owned_shares if hasattr(company, "owned_shares") else 0
            })
        
        # Update player data
        self.player_data["stock_market"].update({
            "cycle_number": self.stock_cycle_number,
            "day_number": self.stock_day_number,
            "companies": company_data,
            "last_update_time": self.last_update_time.isoformat()
        })
        
        # Ensure trade log exists
        if "trade_log" not in self.player_data["stock_market"]:
            self.player_data["stock_market"]["trade_log"] = []
    
    def load_market_data(self):
        """Load market data from player data"""
        if "stock_market" in self.player_data:
            market_data = self.player_data["stock_market"]
            
            # Load cycle and day numbers
            self.stock_cycle_number = market_data.get("cycle_number", 0)
            self.stock_day_number = market_data.get("day_number", 1)
            
            # Load last update time
            if "last_update_time" in market_data:
                try:
                    self.last_update_time = datetime.datetime.fromisoformat(market_data["last_update_time"])
                except (ValueError, TypeError):
                    # If there's an error parsing the time, use current time
                    self.last_update_time = datetime.datetime.now()
            else:
                self.last_update_time = datetime.datetime.now()
            
            # Load company data
            if "companies" in market_data and len(market_data["companies"]) == len(self.companies):
                for i, company_data in enumerate(market_data["companies"]):
                    self.companies[i].name = company_data["name"]
                    self.companies[i].current_value = company_data["current_value"]
                    self.companies[i].previous_value = company_data["previous_value"]
                    self.companies[i].price_history = company_data["price_history"]
                    self.companies[i].owned_shares = company_data.get("owned_shares", 0)
    
    def get_time_until_next_update(self):
        """Calculate the time in seconds until the next market update"""
        now = datetime.datetime.now()
        elapsed = (now - self.last_update_time).total_seconds()
        remaining = max(0, 60 - elapsed)
        return int(remaining)
    
    def show_main_menu(self):
        # Unbind mousewheel if it was bound
        if hasattr(self.root, 'mousewheel_bound') and self.root.mousewheel_bound:
            self.root.unbind_all("<MouseWheel>")
            self.root.mousewheel_bound = False
        
        # Stop the market thread when returning to main menu
        self.stop_market_thread()
        
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.root, text="Space Station Explorer", font=("Arial", 24), bg="black", fg="white")
        title_label.pack(pady=50)
        
        # Buttons
        button_frame = tk.Frame(self.root, bg="black")
        button_frame.pack(pady=20)
        
        new_game_btn = tk.Button(button_frame, text="New Game", font=("Arial", 14), width=15, command=self.show_character_creation)
        new_game_btn.pack(pady=10)
        
        load_game_btn = tk.Button(button_frame, text="Load Game", font=("Arial", 14), width=15, command=self.show_load_game)
        load_game_btn.pack(pady=10)
        
        quit_btn = tk.Button(button_frame, text="Quit", font=("Arial", 14), width=15, command=self.on_closing)
        quit_btn.pack(pady=10)
    
    def show_character_creation(self):
        CharacterCreation(
            self.root,
            self.player_data,
            self.companies,
            on_back=self.show_main_menu,
            on_complete=self._on_character_created
        )
    
    def _on_character_created(self, player_data, station_crew):
        """Receive the finished character and NPC crew from character creation"""
        self.player_data = player_data
        self.station_crew = station_crew
        self.save_and_start()
    
    def save_and_start(self):
       
        """Save the character and start the game"""
        Game.save_game(self.player_data)
        
        # Initialize stock market data
        self.update_market_data()
        
        # Start the market thread
        self.start_market_thread()
        
        # Start the battery timer
        self.start_battery_timer()
        
        # Show room
        self.show_room()
    
    def show_room(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ensure market thread is running
        if not self.market_running:
            self.start_market_thread()
        
        # Title
        room_label = tk.Label(self.root, text="Your Quarters", font=("Arial", 24), bg="black", fg="white")
        room_label.pack(pady=30)
        
        # Description
        desc_label = tk.Label(self.root, text="A small living quarters with basic amenities.", 
                             font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Player info
        info_frame = tk.Frame(self.root, bg="black")
        info_frame.pack(pady=10)
        
        name_label = tk.Label(info_frame, text=f"Name: {self.player_data['name']}", font=("Arial", 12), bg="black", fg="white")
        name_label.pack(side=tk.LEFT, padx=20)
        
        job_label = tk.Label(info_frame, text=f"Job: {self.player_data['job']}", font=("Arial", 12), bg="black", fg="white")
        job_label.pack(side=tk.LEFT, padx=20)
        
        credits_label = tk.Label(info_frame, text=f"Credits: {self.player_data['credits']:.2f}", font=("Arial", 12), bg="black", fg="white")
        credits_label.pack(side=tk.LEFT, padx=20)
        
        # Room items
        button_frame = tk.Frame(self.root, bg="black")
        button_frame.pack(pady=20)
        
        bed_btn = tk.Button(button_frame, text="Bed", font=("Arial", 14), width=15, command=self.interact_bed)
        bed_btn.grid(row=0, column=0, padx=10, pady=10)
        
        locker_btn = tk.Button(button_frame, text="Storage Locker", font=("Arial", 14), width=15, command=self.show_storage)
        locker_btn.grid(row=0, column=1, padx=10, pady=10)
        
        computer_btn = tk.Button(button_frame, text="Computer", font=("Arial", 14), width=15, command=self.show_computer)
        computer_btn.grid(row=1, column=0, padx=10, pady=10)
        
        door_btn = tk.Button(button_frame, text="Door", font=("Arial", 14), width=15, command=self.use_door)
        door_btn.grid(row=1, column=1, padx=10, pady=10)
        
        # Character sheet button 
        character_btn = tk.Button(button_frame, text="Character Sheet", font=("Arial", 14), width=15, command=self.show_character_sheet)
        character_btn.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
        
        # Save and exit button
        save_frame = tk.Frame(self.root, bg="black")
        save_frame.pack(pady=30)
        
        save_btn = tk.Button(save_frame, text="Save and Exit", font=("Arial", 14), width=15, command=self.save_and_exit)
        save_btn.pack()
    
    def show_character_sheet(self):
        """Show the character sheet window"""
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ensure market thread is running
        if not self.market_running:
            self.start_market_thread()
        
        # Configure window size
        self.root.geometry("800x700")  # Increased height to accommodate all content
        
        # Title
        title_label = tk.Label(self.root, text="Character Sheet", font=("Arial", 24), bg="black", fg="white")
        title_label.pack(pady=20)
        
        # Character info
        info_frame = tk.Frame(self.root, bg="black")
        info_frame.pack(pady=10)
        
        # Name and job
        name_label = tk.Label(info_frame, text=f"Name: {self.player_data['name']}", font=("Arial", 14), bg="black", fg="white")
        name_label.pack(anchor="w", padx=10, pady=5)
        
        job_label = tk.Label(info_frame, text=f"Job: {self.player_data['job']}", font=("Arial", 14), bg="black", fg="white")
        job_label.pack(anchor="w", padx=10, pady=5)

        department = self.player_data.get("department", "Unknown")
        department_label = tk.Label(info_frame, text=f"Department: {department}", font=("Arial", 14), bg="black", fg="white")
        department_label.pack(anchor="w", padx=10, pady=5)
        
        # Credits (displayed to 2 decimal places)
        credits_label = tk.Label(info_frame, text=f"Credits: {self.player_data['credits']:.2f}", font=("Arial", 14), bg="black", fg="white")
        credits_label.pack(anchor="w", padx=10, pady=5)
        
        # Buttons for inventory, stock holdings, and notes
        button_frame = tk.Frame(info_frame, bg="black")
        button_frame.pack(anchor="w", padx=10, pady=5, fill=tk.X)
        
        # Inventory button
        inv_count = len(self.player_data.get('inventory', []))
        inv_btn = tk.Button(button_frame, text=f"View Inventory ({inv_count} items)", 
                          font=("Arial", 12), width=20, command=self.show_inventory_popup)
        inv_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Stock holdings button
        holdings_count = len(self.player_data.get('stock_holdings', {}))
        stock_btn = tk.Button(button_frame, text=f"View Stock Holdings ({holdings_count})", 
                            font=("Arial", 12), width=20, command=self.show_holdings_popup)
        stock_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Notes button
        notes_count = len(self.player_data.get('notes', []))
        notes_btn = tk.Button(button_frame, text=f"View Notes ({notes_count})", 
                            font=("Arial", 12), width=15, command=self.show_notes_popup)
        notes_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Damage section - for non-limb specific damage
        damage_label = tk.Label(info_frame, text="Overall Damage:", font=("Arial", 14), bg="black", fg="white")
        damage_label.pack(anchor="w", padx=10, pady=5)
        
        # Create a frame for overall damage types
        damage_frame = tk.Frame(info_frame, bg="black")
        damage_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Show overall damage types
        damage_types = [
            {"name": "Burn", "key": "burn", "icon": "🔥"},
            {"name": "Poison", "key": "poison", "icon": "☣️"},
            {"name": "Oxygen", "key": "oxygen", "icon": "💨"}
        ]
        
        for damage_type in damage_types:
            damage_value = self.player_data["damage"].get(damage_type["key"], 0)
            
            # Color based on damage level
            color = "green" if damage_value < 10 else "yellow" if damage_value < 30 else "orange" if damage_value < 60 else "red"
            
            # Create frame for this damage type
            type_frame = tk.Frame(damage_frame, bg="black")
            type_frame.pack(anchor="w", fill=tk.X, pady=2)
            
            # Icon and name
            type_label = tk.Label(type_frame, text=f"{damage_type['icon']} {damage_type['name']}: ", 
                               font=("Arial", 12), bg="black", fg="white")
            type_label.pack(side=tk.LEFT, padx=5)
            
            # Damage value with color
            value_label = tk.Label(type_frame, text=f"{damage_value:.1f}%", 
                                font=("Arial", 12), bg="black", fg=color)
            value_label.pack(side=tk.LEFT)
            
            # Description of effects
            if damage_value >= 30:
                effect_text = "Severe" if damage_value >= 70 else "Moderate" if damage_value >= 50 else "Mild"
                effect_label = tk.Label(type_frame, text=f" - {effect_text} effects", 
                                     font=("Arial", 12, "italic"), bg="black", fg=color)
                effect_label.pack(side=tk.LEFT, padx=5)
        
        # Limb health - horizontal layout
        limb_label = tk.Label(info_frame, text="Limb Health (Blunt Damage):", font=("Arial", 14), bg="black", fg="white")
        limb_label.pack(anchor="w", padx=10, pady=5)
        
        # Create a frame for the horizontal limb health display
        limb_frame = tk.Frame(info_frame, bg="black")
        limb_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Create a 2x3 grid for the 6 limbs
        row1_frame = tk.Frame(limb_frame, bg="black")
        row1_frame.pack(fill=tk.X, pady=2)
        
        row2_frame = tk.Frame(limb_frame, bg="black")
        row2_frame.pack(fill=tk.X, pady=2)
        
        # Sort limbs into logical order
        limb_order = ["head", "chest", "left_arm", "right_arm", "left_leg", "right_leg"]
        
        # First row: Head, Chest, Left Arm
        for i, limb_name in enumerate(limb_order[:3]):
            if limb_name in self.player_data['limbs']:
                health = self.player_data['limbs'][limb_name]
                display_name = limb_name.replace('_', ' ').title()
                
                # Change color based on health
                color = "green" if health > 75 else "yellow" if health > 40 else "red"
                
                limb_frame = tk.Frame(row1_frame, bg="black", width=200)
                limb_frame.pack(side=tk.LEFT, padx=10, expand=True)
                
                limb_health_label = tk.Label(limb_frame, text=f"{display_name}: {health}%", 
                                         font=("Arial", 12), bg="black", fg=color)
                limb_health_label.pack(side=tk.LEFT)
        
        # Second row: Right Arm, Left Leg, Right Leg
        for i, limb_name in enumerate(limb_order[3:]):
            if limb_name in self.player_data['limbs']:
                health = self.player_data['limbs'][limb_name]
                display_name = limb_name.replace('_', ' ').title()
                
                # Change color based on health
                color = "green" if health > 75 else "yellow" if health > 40 else "red"
                
                limb_frame = tk.Frame(row2_frame, bg="black", width=200)
                limb_frame.pack(side=tk.LEFT, padx=10, expand=True)
                
                limb_health_label = tk.Label(limb_frame, text=f"{display_name}: {health}%", 
                                         font=("Arial", 12), bg="black", fg=color)
                limb_health_label.pack(side=tk.LEFT)
        
        # Overall health calculation
        overall_label = tk.Label(info_frame, text="Overall Health:", font=("Arial", 14), bg="black", fg="white")
        overall_label.pack(anchor="w", padx=10, pady=5)
        
        # Calculate overall health as an average of limb health and damage types
        limb_health = sum(self.player_data["limbs"].values()) / len(self.player_data["limbs"])
        damage_health = 100 - (sum(self.player_data["damage"].values()) / len(self.player_data["damage"]))
        overall_health = (limb_health + damage_health) / 2
        
        # Color based on overall health
        overall_color = "green" if overall_health > 75 else "yellow" if overall_health > 40 else "red"
        
        overall_health_label = tk.Label(info_frame, text=f"{overall_health:.1f}%", 
                                     font=("Arial", 16, "bold"), bg="black", fg=overall_color)
        overall_health_label.pack(anchor="w", padx=10, pady=5)
        
        # Store the previous screen to return to
        self.previous_screen = getattr(self, 'previous_screen', 'show_room')
        
        # Return button that goes back to the previous screen
        return_btn = tk.Button(self.root, text="Return", font=("Arial", 14), width=15, 
                             command=lambda: getattr(self, self.previous_screen)())
        return_btn.pack(pady=30)  # Increased padding to ensure button is visible
    
    def show_notes_popup(self):
        """Show a popup window with the player's notes"""
        popup = tk.Toplevel(self.root)
        popup.title("Character Notes")
        popup.geometry("600x500")
        popup.configure(bg="black")
        
        # Ensure this window stays on top
        popup.transient(self.root)
        popup.grab_set()
        
        # Center the popup window
        popup.update_idletasks()
        width = 600
        height = 500
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        title_label = tk.Label(popup, text="Character Notes", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)
        
        # Create a frame for the scrollable notes
        frame = tk.Frame(popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Add a scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a text widget for notes
        notes_text = tk.Text(frame, bg="black", fg="white", font=("Arial", 12),
                           width=60, height=20, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=notes_text.yview)
        
        # Disable editing
        notes_text.config(state=tk.DISABLED)
        
        # Load notes
        if "notes" in self.player_data and self.player_data["notes"]:
            # Re-enable text widget temporarily to insert text
            notes_text.config(state=tk.NORMAL)
            
            # Insert notes in reverse order (newest first)
            for note in reversed(self.player_data["notes"]):
                # Format the note
                if "timestamp" in note and "text" in note:
                    timestamp = note["timestamp"]
                    text = note["text"]
                    
                    # Format the timestamp for display
                    try:
                        # Parse ISO format timestamp
                        dt = datetime.datetime.fromisoformat(timestamp)
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        # If timestamp format is invalid, use it as is
                        formatted_time = timestamp
                    
                    # Insert the formatted note
                    notes_text.insert(tk.END, f"{formatted_time}:\n{text}\n\n")
                else:
                    # If note doesn't have proper structure, just insert the text
                    notes_text.insert(tk.END, f"{str(note)}\n\n")
            
            # Disable editing again
            notes_text.config(state=tk.DISABLED)
        else:
            # If no notes, show a message
            notes_text.config(state=tk.NORMAL)
            notes_text.insert(tk.END, "No notes recorded yet.")
            notes_text.config(state=tk.DISABLED)
        
        # Mouse wheel binding for scrolling
        def _on_notes_mousewheel(event):
            try:
                notes_text.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Ignore errors if the text widget was destroyed
        
        # Bind mousewheel to notes text widget
        popup.bind("<MouseWheel>", _on_notes_mousewheel)
        
        # Override destroy method to cleanup bindings
        orig_destroy = popup.destroy
        def _destroy_and_cleanup():
            try:
                popup.unbind("<MouseWheel>")
            except:
                pass
            orig_destroy()
        
        popup.destroy = _destroy_and_cleanup
        
        # Close button
        close_btn = tk.Button(popup, text="Close", font=("Arial", 12), width=10, command=popup.destroy)
        close_btn.pack(pady=10)
    
    def add_note(self, text):
        """Add a note to the player's notes"""
        if "notes" not in self.player_data:
            self.player_data["notes"] = []
        
        # Create a new note with timestamp
        note = {
            "timestamp": datetime.datetime.now().isoformat(),
            "text": text
        }
        
        # Add the note to the player's notes
        self.player_data["notes"].append(note)
    
    def show_holdings_popup(self):
        """Show a popup window with the player's stock holdings"""
        popup = tk.Toplevel(self.root)
        popup.title("Stock Holdings")
        popup.geometry("400x400")
        popup.configure(bg="black")
        
        # Ensure this window stays on top
        popup.transient(self.root)
        popup.grab_set()
        
        # Center the popup window
        popup.update_idletasks()
        width = 400
        height = 400
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        title_label = tk.Label(popup, text="Stock Holdings", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)
        
        # Create a frame for the scrollable holdings list
        frame = tk.Frame(popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Add a scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a listbox for holdings
        holdings_list = tk.Listbox(frame, bg="black", fg="white", font=("Arial", 12),
                                 width=30, height=15, yscrollcommand=scrollbar.set)
        holdings_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=holdings_list.yview)
        
        # Add holdings to the listbox
        if not self.player_data.get('stock_holdings', {}):
            holdings_list.insert(tk.END, "You don't own any company stocks.")
        else:
            for company, shares in self.player_data['stock_holdings'].items():
                holdings_list.insert(tk.END, f"{company}: {shares} shares")
        
        # Mouse wheel binding for scrolling
        def _on_holdings_mousewheel(event):
            try:
                holdings_list.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Ignore errors if the widget was destroyed
        
        # Bind mousewheel to holdings list
        popup.bind("<MouseWheel>", _on_holdings_mousewheel)
        
        # Override destroy method to cleanup bindings
        orig_destroy = popup.destroy
        def _destroy_and_cleanup():
            try:
                popup.unbind("<MouseWheel>")
            except:
                pass
            orig_destroy()
        
        popup.destroy = _destroy_and_cleanup
        
        # Close button
        close_btn = tk.Button(popup, text="Close", font=("Arial", 12), width=10, command=popup.destroy)
        close_btn.pack(pady=10)
    
    def interact_bed(self):
        # Create a new top-level window for save dialog
        save_window = tk.Toplevel(self.root)
        save_window.title("Bed")
        save_window.geometry("300x150")
        save_window.transient(self.root)
        save_window.grab_set()
        
        # Center the window
        save_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 250,
                                        self.root.winfo_rooty() + 200))
        
        # Create frame with padding
        save_frame = tk.Frame(save_window, bg="black")
        save_frame.pack(fill=tk.BOTH, expand=True)
        
        # Message
        tk.Label(
            save_frame,
            text="Would you like to save your game?",
            font=("Arial", 12),
            bg="black",
            fg="white"
        ).pack(pady=10)
        
        # Buttons frame
        buttons_frame = tk.Frame(save_frame, bg="black")
        buttons_frame.pack(pady=10)
        
        # Yes button
        tk.Button(
            buttons_frame,
            text="Yes",
            font=("Arial", 12),
            command=lambda: self.save_game_and_close(save_window)
        ).pack(side=tk.LEFT, padx=10)
        
        # No button
        tk.Button(
            buttons_frame,
            text="No",
            font=("Arial", 12),
            command=save_window.destroy
        ).pack(side=tk.LEFT, padx=10)
    
    def save_game_and_close(self, save_window):
        """Save the game and close the save dialog"""
        # Update market data before saving
        self.update_market_data()
        
        Game.save_game(self.player_data)
        
        # Close the save dialog without showing a confirmation
        save_window.destroy()
    
    def show_storage(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Title
        storage_label = tk.Label(self.root, text="Storage Locker", font=("Arial", 24), bg="black", fg="white")
        storage_label.pack(pady=20)
        
        # Container for locker and inventory sections
        main_container = tk.Frame(self.root, bg="black")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left frame for locker items
        locker_frame = tk.LabelFrame(main_container, text="Locker Items", font=("Arial", 14), bg="black", fg="white", bd=2)
        locker_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Right frame for player inventory
        inventory_frame = tk.LabelFrame(main_container, text="Your Inventory", font=("Arial", 14), bg="black", fg="white", bd=2)
        inventory_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # --- Locker items data (Uses ALL_ITEMS definitions) ---
        # Define the IDs of items initially in the locker
        initial_locker_item_ids = [
            "welcome_guide", "flashlight", "station_map", "emergency_rations", 
            "basic_tools", "id_card_reader", "portable_scanner", 
            "maintenance_manual", "emergency_beacon", "first_aid_kit"
        ]
        
        # Get full definitions for locker items
        locker_item_defs = [get_item_definition(item_id) for item_id in initial_locker_item_ids if get_item_definition(item_id)]

        # Filter out items the player already has (compare by ID)
        player_inventory_ids = {item.get('id') for item in self.player_data.get("inventory", []) if isinstance(item, dict)}
        filtered_items = [item_def for item_def in locker_item_defs if item_def.get('id') not in player_inventory_ids]
        
        # --- Create scrollable canvas for locker items ---
        locker_canvas = tk.Canvas(locker_frame, bg="black", highlightthickness=0)
        locker_scrollbar = tk.Scrollbar(locker_frame, orient="vertical", command=locker_canvas.yview)
        locker_canvas.configure(yscrollcommand=locker_scrollbar.set)
        
        # Pack canvas first, then scrollbar conditionally
        locker_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Scrollbar packed later if needed
        
        locker_items_frame = tk.Frame(locker_canvas, bg="black")
        locker_canvas.create_window((0, 0), window=locker_items_frame, anchor="nw")
        
        # --- Populate locker items frame (using item dictionaries) ---
        if not filtered_items:
            empty_label = tk.Label(locker_items_frame, text="The storage locker is empty.", font=("Arial", 12), bg="black", fg="white")
            empty_label.pack(pady=10, padx=10, anchor="w")
        else:
            for i, item_def in enumerate(filtered_items):
                item_frame = tk.Frame(locker_items_frame, bg="dark gray", bd=2, relief=tk.RAISED, width=300)
                item_frame.pack(fill=tk.X, pady=5, padx=5)
                
                info_frame = tk.Frame(item_frame, bg="dark gray")
                info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor="w")
                
                item_name_label = tk.Label(info_frame, text=item_def.get('name', 'Unknown Item'), font=("Arial", 12, "bold"), bg="dark gray")
                item_name_label.pack(anchor="w", padx=10, pady=(5, 0))
                
                item_desc_label = tk.Label(info_frame, text=item_def.get('description', ''), font=("Arial", 10), bg="dark gray", wraplength=200)
                item_desc_label.pack(anchor="w", padx=10, pady=(0, 5))
                
                button_frame = tk.Frame(item_frame, bg="dark gray")
                button_frame.pack(side=tk.RIGHT, padx=10, pady=5)
                
                # Pass the item ID to take_item
                take_btn = tk.Button(button_frame, text="Take", font=("Arial", 10),
                                    command=lambda item_id=item_def.get('id'): self.take_item(item_id))
                take_btn.pack()
        
        # --- Create scrollable canvas for inventory items ---
        inventory_canvas = tk.Canvas(inventory_frame, bg="black", highlightthickness=0)
        inventory_scrollbar = tk.Scrollbar(inventory_frame, orient="vertical", command=inventory_canvas.yview)
        inventory_canvas.configure(yscrollcommand=inventory_scrollbar.set)
        
        # Pack canvas first, then scrollbar conditionally
        inventory_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Scrollbar packed later if needed

        inventory_items_frame = tk.Frame(inventory_canvas, bg="black")
        inventory_canvas.create_window((0, 0), window=inventory_items_frame, anchor="nw")
        
        # --- Populate inventory items (using item dictionaries) ---
        player_inventory = self.player_data.get("inventory", [])
        if not player_inventory:
            empty_label = tk.Label(inventory_items_frame, text="Your inventory is empty.", font=("Arial", 12), bg="black", fg="white")
            empty_label.pack(pady=10, padx=10, anchor="w")
        else:
            for i, item_def in enumerate(player_inventory):
                item_frame = tk.Frame(inventory_items_frame, bg="dark gray", bd=2, relief=tk.RAISED, width=300)
                item_frame.pack(fill=tk.X, pady=5, padx=5)
                
                # Display item name
                name_text = str(item_def) # Fallback for non-dict items
                item_color = "red"        # Default color for errors/legacy
                if isinstance(item_def, dict) and 'name' in item_def:
                    name_text = item_def['name']
                    item_color = "white" # Normal color for dict items
                
                name_label = tk.Label(item_frame, text=name_text, font=("Arial", 12, "bold"), bg="dark gray", fg=item_color)
                name_label.pack(side=tk.LEFT, padx=10, pady=5, anchor="w")
                
                # Pass the index to store_item
                store_btn = tk.Button(item_frame, text="Store in Locker", font=("Arial", 10),
                                    command=lambda index=i: self.store_item(index)) # Pass index
                store_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # --- Configure canvas scrolling and back button --- 
        
        # Function to configure scroll region and show/hide scrollbar
        def configure_scroll(canvas, scrollbar, items_frame):
            canvas.update_idletasks() # Ensure frame size is calculated
            canvas.config(scrollregion=canvas.bbox("all"))
            # Check if content height exceeds canvas height
            if items_frame.winfo_reqheight() > canvas.winfo_reqheight():
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y) # Show scrollbar
            else:
                scrollbar.pack_forget() # Hide scrollbar
        
        # Configure scroll regions initially
        configure_scroll(locker_canvas, locker_scrollbar, locker_items_frame)
        configure_scroll(inventory_canvas, inventory_scrollbar, inventory_items_frame)

        # Mousewheel scrolling - bind directly to each canvas
        def _on_locker_mousewheel(event):
            locker_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def _on_inventory_mousewheel(event):
            inventory_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        locker_canvas.bind("<MouseWheel>", _on_locker_mousewheel)
        locker_items_frame.bind("<MouseWheel>", _on_locker_mousewheel) # Bind frame too
        inventory_canvas.bind("<MouseWheel>", _on_inventory_mousewheel)
        inventory_items_frame.bind("<MouseWheel>", _on_inventory_mousewheel) # Bind frame too

        # Back button (needs to unbind events)
        back_btn = tk.Button(self.root, text="Back to Room", font=("Arial", 14), width=15, 
                           command=lambda lc=locker_canvas, ic=inventory_canvas: self._exit_storage(lc, ic))
        back_btn.pack(pady=20)
    
    def _exit_storage(self, locker_canvas, inventory_canvas):
        """Clean up bindings before exiting storage view"""
        # Unbind specific mouse wheel handlers
        try:
            locker_canvas.unbind("<MouseWheel>")
            # Find the frame inside the canvas to unbind it too (more robust needed if structure changes)
            locker_items_frame = locker_canvas.winfo_children()[0] 
            locker_items_frame.unbind("<MouseWheel>")
        except Exception as e:
            print(f"Error unbinding locker scroll: {e}")
            pass
        try:
            inventory_canvas.unbind("<MouseWheel>")
            inventory_items_frame = inventory_canvas.winfo_children()[0]
            inventory_items_frame.unbind("<MouseWheel>")
        except Exception as e:
            print(f"Error unbinding inventory scroll: {e}")
            pass
        # Return to room view
        self.show_room()
    
    def take_item(self, item_id):
        """Takes an item from the locker based on its ID."""
        if not item_id:
            messagebox.showerror("Error", "Invalid item ID provided.")
            return

        # Get the item definition
        item_def = get_item_definition(item_id)
        if not item_def:
            messagebox.showerror("Error", f"Could not find definition for item ID: {item_id}.")
            return

        item_name = item_def.get("name", "Unknown Item")

        # Check if player already has this item ID
        player_inventory = self.player_data.setdefault("inventory", [])
        has_item = any(isinstance(inv_item, dict) and inv_item.get('id') == item_id for inv_item in player_inventory)
        
        if not has_item:
            player_inventory.append(item_def) # Add the dictionary
            messagebox.showinfo("Item Taken", f"You took the {item_name}.")
            # Add note
            self.add_note(f"Took {item_name} ({item_id}) from locker.")
            self.show_storage()  # Refresh the storage view
        else:
             messagebox.showinfo("Already Have It", f"You already have a {item_name}.")

    def store_item(self, item_index):
        """Stores an item from the inventory into the locker, using the item's index."""
        player_inventory = self.player_data.get("inventory", [])
        
        if not (0 <= item_index < len(player_inventory)):
             messagebox.showerror("Error", f"Invalid item index.")
             return

        # Get the item dictionary using the index
        item_to_store = player_inventory[item_index]
        
        # Prefer name from dict if available
        item_name = str(item_to_store) # Fallback
        item_id = None
        if isinstance(item_to_store, dict):
            item_name = item_to_store.get('name', 'Unknown Item')
            item_id = item_to_store.get('id')

        # Remove item from player data by index
        del player_inventory[item_index]
        messagebox.showinfo("Item Stored", f"You placed the {item_name} in the storage locker.")
        
        # Add note
        note_text = f"Stored {item_name}" + (f" ({item_id})" if item_id else "") + " in locker."
        self.add_note(note_text)

        self.show_storage() # Refresh the storage view

    def show_computer(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ensure market thread is running
        if not self.market_running:
            self.start_market_thread()
        
        # Title
        computer_label = tk.Label(self.root, text="Computer Terminal", font=("Arial", 24), bg="black", fg="white")
        computer_label.pack(pady=30)
        
        # Computer options
        options_frame = tk.Frame(self.root, bg="black")
        options_frame.pack(pady=20)
        
        stock_btn = tk.Button(options_frame, text="Stock Market", font=("Arial", 14), width=15,
                             command=self.open_stock_market)
        stock_btn.pack(pady=10)
        
        turnoff_btn = tk.Button(options_frame, text="Turn Off Computer", font=("Arial", 14), width=15, command=self.show_room)
        turnoff_btn.pack(pady=10)
    
    def open_stock_market(self):
        # Calculate time until next update
        time_until_update = self.get_time_until_next_update()
        
        # Pass the current market state to the stock market window
        market = StockMarket(self.root, self.player_data, self.companies, 
                           self.stock_cycle_number, self.stock_day_number, self.update_player_data)
    
    def update_player_data(self, updated_data):
        # Update player data when returning from stock market
        
        # Check if there were any stock transactions
        if "stock_transactions" in updated_data:
            transactions = updated_data.pop("stock_transactions")
            
            # Log notes for significant transactions
            for transaction in transactions:
                if transaction["type"] == "buy":
                    self.add_note(f"Bought {transaction['shares']} shares of {transaction['company']} at {transaction['price']:.2f} cr/share (Total: {transaction['total']:.2f} cr)")
                elif transaction["type"] == "sell":
                    profit = transaction.get("profit", 0)
                    if profit != 0:
                        profit_text = f" (Profit: {profit:.2f} cr)" if profit > 0 else f" (Loss: {abs(profit):.2f} cr)"
                    else:
                        profit_text = ""
                    
                    self.add_note(f"Sold {transaction['shares']} shares of {transaction['company']} at {transaction['price']:.2f} cr/share (Total: {transaction['total']:.2f} cr){profit_text}")
        
        self.player_data = updated_data
        
        # Update owned shares in the companies list
        if "stock_holdings" in updated_data:
            for company in self.companies:
                company.owned_shares = updated_data["stock_holdings"].get(company.name, 0)
        
        # Return to computer menu instead of room view
        self.show_computer()
    
    def use_door(self):
        # Get current location
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        
        if x == -1 and y == 0:  # In quarters, move to hallway
            self.player_data["location"] = {"x": 0, "y": 0}
            self.show_hallway()
        else:  # In hallway, move to quarters
            self.player_data["location"] = {"x": -1, "y": 0}
            self.show_room()
    
    def get_location_key(self):
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        return f"{x},{y}"
    
    def show_hallway(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Ensure market thread is running
        if not self.market_running:
            self.start_market_thread()
        
        # Get current location
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        
        # Store previous position for backtracking
        self.previous_position = (x, y)
        
        loc_key = self.get_location_key()
        
        if loc_key not in self.ship_map:
            messagebox.showerror("Error", "Invalid location!")
            self.player_data["location"] = {"x": 0, "y": 0}
            loc_key = "0,0"
        
        # Check if we're at a special room that can be entered
        if self.check_special_room():
            return
        
        location = self.ship_map[loc_key]
        
        # Check if room is locked
        if location.get("locked", False):
            messagebox.showinfo("Locked Door", f"The door to the {location['name']} is locked. You need proper authorization to enter.")
            # Return to previous position
            prev_x, prev_y = self.get_previous_position()
            self.player_data["location"]["x"] = prev_x
            self.player_data["location"]["y"] = prev_y
            # Show hallway again with updated position
            self.show_hallway()
            return
        
        # Get battery level for lighting effects
        battery_level = 100.0  # Default to full power
        if "station_power" in self.player_data:
            battery_level = self.player_data["station_power"].get("battery_level", 100.0)
        
        # Set background color based on battery level
        hallway_bg = "black"  # Default
        desc_fg = "white"     # Default text color
        
        if battery_level <= 5:
            # Critical - emergency red lighting only
            hallway_bg = "#220000"  # Very dark red
            desc_fg = "#FF5555"     # Bright red text
        elif battery_level <= 15:
            # Low power - dim lighting
            hallway_bg = "#111111"  # Very dark gray
            desc_fg = "#BBBBBB"     # Light gray text
        
        # Set window background
        self.root.configure(bg=hallway_bg)
        
        # Title
        hallway_label = tk.Label(self.root, text=location["name"], font=("Arial", 24), bg=hallway_bg, fg="white")
        hallway_label.pack(pady=30)
        
        # Description with power status info
        base_desc = location["desc"]
        
        # Add lighting condition to the description
        if battery_level <= 5:
            power_desc = "\n\nEmergency lighting casts an eerie red glow. Most systems are offline."
        elif battery_level <= 15:
            power_desc = "\n\nThe lights are dimmed to conserve power."
        else:
            power_desc = ""
            
        full_desc = base_desc + power_desc
        
        desc_label = tk.Label(self.root, text=full_desc, font=("Arial", 12), 
                           bg=hallway_bg, fg=desc_fg, wraplength=600)
        desc_label.pack(pady=10)
        
        # Location info
        coords_label = tk.Label(self.root, text=f"Location: {self.player_data['location']['x']} North, {self.player_data['location']['y']} East", 
                               font=("Arial", 10), bg=hallway_bg, fg=desc_fg)
        coords_label.pack(pady=5)
        
        # Navigation controls
        nav_frame = tk.Frame(self.root, bg=hallway_bg)
        nav_frame.pack(pady=20)
        
        # Determine available directions
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        
        # Add an unlock door button if appropriate
        if self.is_near_special_room():
            unlock_btn = tk.Button(self.root, text="Unlock Door", font=("Arial", 14), width=15,
                               command=self.unlock_door)
            unlock_btn.pack(pady=10)
        
        # Updated movement logic for circuit and locked rooms:
        north_available = False
        south_available = False
        east_available = False
        west_available = False
        
        # Standard hallway directions
        # North hallway section (0-5, 0)
        if y == 0 and x < 5:
            north_available = True
        if y == 0 and x > 0:
            south_available = True
            
        # East hallway section (0, 0-5)
        if x == 0 and y < 5:
            east_available = True
        if x == 0 and y > 0:
            west_available = True
            
        # North end - can go east
        if x == 5 and y < 5:
            east_available = True
        if x == 5 and y > 0:
            west_available = True
            
        # East end - can go north
        if y == 5 and x < 5:
            north_available = True
        if y == 5 and x > 0:
            south_available = True
        
        # Special cases for room access points
        is_special_location = False
        
        # Bridge access from north end
        if x == 5 and y == 0:
            is_special_location = True
            # Add the Bridge access button
            bridge_btn = tk.Button(nav_frame, text="Bridge", font=("Arial", 14), width=15,
                                command=lambda: self.enter_special_room_at("Bridge", "6,0"))
            bridge_btn.grid(row=0, column=1, padx=10, pady=10)
            
            # Also add regular east button for the corridor
            if east_available:
                east_btn = tk.Button(nav_frame, text="Go East", font=("Arial", 14), width=15,
                                   command=lambda: self.move_direction("east"))
                east_btn.grid(row=1, column=2, padx=10, pady=10)
                
            # Add south button for returning to the corridor
            if south_available:
                south_btn = tk.Button(nav_frame, text="Go South", font=("Arial", 14), width=15,
                                    command=lambda: self.move_direction("south"))
                south_btn.grid(row=2, column=1, padx=10, pady=10)
            
        # MedBay access from east end
        elif x == 0 and y == 5:
            is_special_location = True
            # Add MedBay access button
            medbay_btn = tk.Button(nav_frame, text="MedBay", font=("Arial", 14), width=15,
                              command=lambda: self.enter_special_room_at("MedBay", "0,6"))
            medbay_btn.grid(row=1, column=2, padx=10, pady=10)
            
            # Add north button for the corridor
            if north_available:
                north_btn = tk.Button(nav_frame, text="Go North", font=("Arial", 14), width=15,
                                    command=lambda: self.move_direction("north"))
                north_btn.grid(row=0, column=1, padx=10, pady=10)
                
            # Add west button for returning to the corridor
            if west_available:
                west_btn = tk.Button(nav_frame, text="Go West", font=("Arial", 14), width=15,
                                   command=lambda: self.move_direction("west"))
                west_btn.grid(row=1, column=0, padx=10, pady=10)
            
        # Security access from northeast corner
        elif x == 5 and y == 5:
            is_special_location = True
            # Just one button for Security access
            security_btn = tk.Button(nav_frame, text="Security", font=("Arial", 14), width=15,
                                 command=lambda: self.enter_special_room_at("Security", "6,6"))
            security_btn.grid(row=0, column=1, padx=10, pady=10)
            
            # Add west and south buttons for the corridors
            west_btn = tk.Button(nav_frame, text="Go West", font=("Arial", 14), width=15,
                               command=lambda: self.move_direction("west"))
            west_btn.grid(row=1, column=0, padx=10, pady=10)
            
            south_btn = tk.Button(nav_frame, text="Go South", font=("Arial", 14), width=15,
                                command=lambda: self.move_direction("south"))
            south_btn.grid(row=2, column=1, padx=10, pady=10)

        # Engineering Bay access from engineering hallway
        elif x == 5 and y == 3:
            is_special_location = True
            # Add Engineering Bay access button
            eng_bay_btn = tk.Button(nav_frame, text="Engineering Bay", font=("Arial", 14), width=15,
                                command=lambda: self.enter_special_room_at("Engineering", "6,3"))
            eng_bay_btn.grid(row=0, column=1, padx=10, pady=10)
            
            # Add west and east buttons for the corridors
            west_btn = tk.Button(nav_frame, text="Go West", font=("Arial", 14), width=15,
                               command=lambda: self.move_direction("west"))
            west_btn.grid(row=1, column=0, padx=10, pady=10)
            
            east_btn = tk.Button(nav_frame, text="Go East", font=("Arial", 14), width=15,
                               command=lambda: self.move_direction("east"))
            east_btn.grid(row=1, column=2, padx=10, pady=10)
        
        # Bar access from bar entrance
        elif x == 0 and y == 3:
            is_special_location = True
            # Add Bar access button
            bar_btn = tk.Button(nav_frame, text="Bar", font=("Arial", 14), width=15,
                             command=lambda: self.enter_special_room_at("Bar", "0,-1"))
            bar_btn.grid(row=0, column=1, padx=10, pady=10)
            
            # Add west and east buttons for the corridors
            west_btn = tk.Button(nav_frame, text="Go West", font=("Arial", 14), width=15,
                               command=lambda: self.move_direction("west"))
            west_btn.grid(row=1, column=0, padx=10, pady=10)
            
            east_btn = tk.Button(nav_frame, text="Go East", font=("Arial", 14), width=15,
                               command=lambda: self.move_direction("east"))
            east_btn.grid(row=1, column=2, padx=10, pady=10)
        
        # Regular directional buttons for other hallway positions
        if not is_special_location:
            if north_available:
                north_btn = tk.Button(nav_frame, text="Go North", font=("Arial", 14), width=15,
                                    command=lambda: self.move_direction("north"))
                north_btn.grid(row=0, column=1, padx=10, pady=10)
                
            if south_available:
                south_btn = tk.Button(nav_frame, text="Go South", font=("Arial", 14), width=15,
                                    command=lambda: self.move_direction("south"))
                south_btn.grid(row=2, column=1, padx=10, pady=10)
                
            if east_available:
                east_btn = tk.Button(nav_frame, text="Go East", font=("Arial", 14), width=15,
                                   command=lambda: self.move_direction("east"))
                east_btn.grid(row=1, column=2, padx=10, pady=10)
                
            if west_available:
                west_btn = tk.Button(nav_frame, text="Go West", font=("Arial", 14), width=15,
                                   command=lambda: self.move_direction("west"))
                west_btn.grid(row=1, column=0, padx=10, pady=10)
            
            # Special case for the Botany Lab entrance at (3,0)
            if x == 3 and y == 0:
                botany_btn = tk.Button(nav_frame, text="Botany Lab", font=("Arial", 14), width=15,
                                     command=lambda: self.enter_special_room_at("Botany", "3,-1"))
                botany_btn.grid(row=1, column=0, padx=10, pady=10)
        
        # Only show return to quarters at the starting junction
        if x == 0 and y == 0:
            quarters_btn = tk.Button(nav_frame, text="Quarters", font=("Arial", 14), width=15,
                                   command=self.use_door)
            quarters_btn.grid(row=3, column=1, columnspan=1, padx=10, pady=20)
        
        # Character sheet button
        character_btn = tk.Button(self.root, text="Character Sheet", font=("Arial", 14), width=15, 
                                command=self.show_character_sheet_hallway)
        character_btn.pack(pady=10)
        
        # Save button
        save_btn = tk.Button(self.root, text="Save and Exit", font=("Arial", 14), width=15,
                          command=self.save_and_exit)
        save_btn.pack(pady=10)
    
    def show_character_sheet_hallway(self):
        # Save the current location so we can return to it later
        self.before_character_sheet_location = {
            "x": self.player_data["location"]["x"],
            "y": self.player_data["location"]["y"]
        }
        
        # Set the previous screen to hallway before showing character sheet
        self.previous_screen = "return_to_hallway"
        
        # Show character sheet
        self.show_character_sheet()
        
    def return_to_hallway(self):
        """Return to the hallway from character sheet at the original location"""
        # Restore the original location before showing hallway
        if hasattr(self, 'before_character_sheet_location'):
            self.player_data["location"]["x"] = self.before_character_sheet_location["x"]
            self.player_data["location"]["y"] = self.before_character_sheet_location["y"]
        
        # Show the hallway
        self.show_hallway()
    
    def move_direction(self, direction):
        """Move in the specified direction with random event chance"""
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        
        if direction == "north":
            x += 1
        elif direction == "south":
            x -= 1
        elif direction == "east":
            y += 1
        elif direction == "west":
            y -= 1
        
        # Update location
        self.player_data["location"]["x"] = x
        self.player_data["location"]["y"] = y
        
        # Log for debugging
        print(f"Moving to location: {x},{y}")
        
        # Check if the destination exists in the ship map
        loc_key = f"{x},{y}"
        if loc_key not in self.ship_map:
            # For Security specifically, it needs a different handling from Northeast Corner
            if x == 6 and y == 5 and self.ship_map.get("6,6", {}).get("name") == "Security":
                # For the Security special case, jump directly to the security location
                self.player_data["location"]["x"] = 6
                self.player_data["location"]["y"] = 6
            # Special case for Engineering Bay entrance
            elif x == 5 and y == 3:
                # This is handled by the check_special_room method
                pass
            else:
                # Otherwise, revert to previous location for invalid moves
                messagebox.showerror("Error", "You can't go that way!")
                self.player_data["location"]["x"] = x - (1 if direction == "north" else -1 if direction == "south" else 0)
                self.player_data["location"]["y"] = y - (1 if direction == "east" else -1 if direction == "west" else 0)
        
        # Random event check (40% chance) when moving through hallways
        if random.random() < 0.20:  # Changed from 0.40 to 0.20 (20% chance)
            self.trigger_random_event()
        
        # Refresh hallway view
        self.show_hallway()
    
    def trigger_random_event(self):
        """Trigger a random event"""
        # List of possible events with good, bad, and neutral outcomes
        events = [
            # Good events
            {"type": "good", "title": "Found Credits", "desc": "You found some credits on the floor!", "effect": lambda: self.add_credits(random.randint(50, 200))},
            {"type": "good", "title": "Supply Crate", "desc": "You found an unsealed supply crate with useful items.", "effect": lambda: self.add_random_item()},
            {"type": "good", "title": "Market Tip", "desc": "You overheard a reliable market tip.", "effect": lambda: self.add_market_knowledge()},
            
            # Neutral events
            {"type": "neutral", "title": "Crew Member", "desc": "You passed by a crew member who nodded at you.", "effect": lambda: None},
            {"type": "neutral", "title": "Announcement", "desc": "The station PA system makes an announcement.", "effect": lambda: self.station_announcement()},
            {"type": "neutral", "title": "Maintenance", "desc": "A maintenance drone passes by, cleaning the hallway.", "effect": lambda: None},
            
            # Bad events - now all include blunt damage
            {"type": "bad", "title": "Lost Credits", "desc": "You dropped some credits and couldn't find them all. You bumped your head looking for them.", 
              "effect": lambda: self.combined_effect([
                  lambda: self.lose_credits(random.randint(10, 50)),
                  lambda: self.damage_limb("head", 5, 10)
              ])},
            {"type": "bad", "title": "Small Explosion", "desc": "A nearby conduit explodes, showering you with hot sparks and debris!", 
              "effect": lambda: self.combined_effect([
                  lambda: self.damage_random_limb(10, 25),  # Blunt damage from impact
                  lambda: self.add_burn_damage(5, 15)       # Burn damage from sparks
              ])},
            {"type": "bad", "title": "Slip and Fall", "desc": "You slipped on a wet floor and fell hard.", 
              "effect": lambda: self.damage_random_limb(10, 20)},
            {"type": "bad", "title": "Steam Leak", "desc": "A pipe bursts, releasing scalding steam that burns your arm!", 
              "effect": lambda: self.combined_effect([
                  lambda: self.damage_limb("left_arm", 5, 10),  # Blunt damage from impact
                  lambda: self.add_burn_damage(15, 30)          # Burn damage from steam
              ])},
            {"type": "bad", "title": "Falling Debris", "desc": "A ceiling panel breaks loose and hits your head!", 
              "effect": lambda: self.damage_limb("head", 15, 35)},
            {"type": "bad", "title": "Maintenance Accident", "desc": "Your leg gets caught in an open floor grate!", 
              "effect": lambda: self.damage_limb("right_leg", 10, 20)},
            {"type": "bad", "title": "Chemical Spill", "desc": "You walk through a chemical spill! Your leg is burned and you feel ill.", 
              "effect": lambda: self.combined_effect([
                  lambda: self.damage_limb("left_leg", 5, 10),    # Blunt damage from slipping
                  lambda: self.add_burn_damage(5, 15),            # Burn damage from chemicals
                  lambda: self.add_poison_damage(10, 20)          # Poison damage from fumes
              ])}
        ]
        
        # Pick a random event
        event = random.choice(events)
        
        # Show the event
        messagebox.showinfo(event["title"], event["desc"])
        
        # Apply the effect
        event["effect"]()
    
    def combined_effect(self, effect_functions):
        """Apply multiple effects in sequence"""
        for effect_fn in effect_functions:
            effect_fn()
    
    def damage_random_limb(self, min_damage, max_damage):
        """Damage a random limb by a random amount"""
        # Get a random limb
        limb = random.choice(list(self.player_data["limbs"].keys()))
        self.damage_limb(limb, min_damage, max_damage)
    
    def damage_limb(self, limb, min_damage, max_damage):
        """Damage a specific limb by a random amount within range (blunt damage)"""
        if limb in self.player_data["limbs"]:
            # Calculate damage
            damage = random.randint(min_damage, max_damage)
            
            # Apply damage
            original_health = self.player_data["limbs"][limb]
            self.player_data["limbs"][limb] = max(0, original_health - damage)
            
            # Format the limb name for display
            limb_name = limb.replace('_', ' ').title()
            
            # Show damage message
            messagebox.showinfo("Blunt Injury", f"Your {limb_name} took {damage}% blunt damage and is now at {self.player_data['limbs'][limb]}%.")
            
            # Add note about the injury
            self.add_note(f"Suffered blunt damage to {limb_name}: Took {damage}% damage (from {original_health}% to {self.player_data['limbs'][limb]}%)")
    
    def add_credits(self, amount):
        """Add credits to the player"""
        self.player_data["credits"] += amount
        messagebox.showinfo("Credits Added", f"You gained {amount} credits.")
        
        # Add note about credits gained
        self.add_note(f"Found {amount} credits. New balance: {self.player_data['credits']} credits.")
    
    def lose_credits(self, amount):
        """Subtract credits from the player (min 0)"""
        old_credits = self.player_data["credits"]
        self.player_data["credits"] = max(0, old_credits - amount)
        messagebox.showinfo("Credits Lost", f"You lost {amount} credits.")
        
        # Add note about credits lost
        self.add_note(f"Lost {amount} credits. New balance: {self.player_data['credits']} credits.")
    
    def show_load_game(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Title
        load_label = tk.Label(self.root, text="Load Game", font=("Arial", 24), bg="black", fg="white")
        load_label.pack(pady=30)
        
        # Check if saves directory exists
        saves_path = os.path.join(self.base_path, "saves") # Updated path
        os.makedirs(saves_path, exist_ok=True)
        
        # Get save files
        save_files = [f for f in os.listdir(saves_path) if f.endswith(".json")]
        
        if not save_files:
            no_saves_label = tk.Label(self.root, text="No saved games found.", font=("Arial", 14), bg="black", fg="white")
            no_saves_label.pack(pady=20)
        else:
            # Create a frame to hold the canvas and scrollbar
            container_frame = tk.Frame(self.root, bg="black")
            container_frame.pack(pady=20, fill=tk.BOTH, expand=True)
            
            # Create a canvas to make the content scrollable
            canvas = tk.Canvas(container_frame, bg="black", highlightthickness=0)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Add a scrollbar to the container
            scrollbar = tk.Scrollbar(container_frame, orient=tk.VERTICAL, command=canvas.yview)
            # Scrollbar initially packed, will be unpacked if not needed
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Configure the canvas to use the scrollbar
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Create a frame inside the canvas to hold the save buttons
            saves_frame = tk.Frame(canvas, bg="black")
            
            # Add the saves_frame to the canvas
            canvas_frame = canvas.create_window((0, 0), window=saves_frame, anchor="nw")
            
            # Add save buttons to the saves_frame
            for save_file in save_files:
                # Strip .json extension for display and passing to load function
                player_name = save_file[:-5]
                
                save_btn = tk.Button(saves_frame, text=player_name, font=("Arial", 14), width=20,
                                     command=lambda name=player_name: self.load_game_file(name))
                save_btn.pack(pady=5)
            
            # Update the scrollregion when the size of saves_frame changes
            def configure_scroll_region(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
                
                # Check if scrolling is needed and enable/disable the scrollbar
                if saves_frame.winfo_height() > canvas.winfo_height():
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)  # Ensure scrollbar is visible
                    # Enable scrolling if not already bound
                    if not hasattr(self.root, 'mousewheel_bound') or not self.root.mousewheel_bound:
                        canvas.bind_all("<MouseWheel>", on_mousewheel)
                        self.root.mousewheel_bound = True
                else:
                    scrollbar.pack_forget()  # Hide scrollbar
                    # Disable scrolling if bound
                    if hasattr(self.root, 'mousewheel_bound') and self.root.mousewheel_bound:
                        self.root.unbind_all("<MouseWheel>")
                        self.root.mousewheel_bound = False
            
            saves_frame.bind("<Configure>", configure_scroll_region)
            
            # Make sure canvas width matches container width
            def set_canvas_width(event):
                canvas_width = event.width
                canvas.itemconfig(canvas_frame, width=canvas_width)
            
            canvas.bind("<Configure>", set_canvas_width)
            
            # Bind mousewheel to scroll
            def on_mousewheel(event):
                # Only scroll if there's content that requires scrolling
                if saves_frame.winfo_height() > canvas.winfo_height():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            # Initialize mousewheel state
            self.root.mousewheel_bound = False
            # Configure scroll region initially to determine if scrollbar/binding is needed
            saves_frame.update_idletasks() 
            configure_scroll_region(None) # Manually call once to set initial state
        
        # Back button
        back_btn = tk.Button(self.root, text="Back", font=("Arial", 14), width=15, command=self.show_main_menu)
        back_btn.pack(pady=20)
    
    def load_game_file(self, filename):
        """Load a saved game from file"""
        # Remove .json extension if present (though it should be passed without it now)
        if filename.endswith(".json"):
            filename = filename[:-5]

        # Load the saved data. Game.load_game opens "saves/{filename}", so the
        # .json extension must be re-added here for the file to be found.
        loaded_data = Game.load_game(f"{filename}.json")

        if loaded_data is None:
            messagebox.showerror("Load Error", f"Could not load save file for '{filename}'.")
            self.show_main_menu()
            return False

        # Apply the loaded data so all downstream logic (market, location, etc.)
        # reads the restored save rather than the default player state.
        self.player_data = loaded_data

        # Update company data from saved game
        self.load_market_data()
        
        # Start the market thread
        self.start_market_thread()
        
        # Start the battery timer
        self.start_battery_timer()
        
        # Determine where to show the player based on saved location
        if "location" in self.player_data:
            x = self.player_data["location"].get("x", 0)
            y = self.player_data["location"].get("y", 0)
            
            # Check if player is in a special room or hallway
            if (x == 6 and y == 0) or (x == 0 and y == 6) or (x == 6 and y == 6) or (x == 6 and y == 3) or (x == 0 and y == -1) or (x == 3 and y == -1):
                # Player was in a special room, return to hallway entrance
                self.update_player_data_from_room(self.player_data) # Use the callback logic to place player correctly
            elif x == -1 and y == 0:
                # Player was in quarters
                self.show_room()
            else:
                # Player was in a hallway
                self.show_hallway()
        else:
            # Default to quarters if location is missing
            self.player_data["location"] = {"x": -1, "y": 0}
            self.show_room()
        
        return True

    def add_burn_damage(self, min_damage, max_damage):
        """Apply burn damage to the player"""
        # Calculate damage
        damage = random.randint(min_damage, max_damage)
        
        # Apply damage
        original_damage = self.player_data["damage"].get("burn", 0)
        self.player_data["damage"]["burn"] = min(100, original_damage + damage)
        
        # Show damage message
        messagebox.showinfo("Burn Damage", f"You suffered {damage}% burn damage! Total burn damage: {self.player_data['damage']['burn']}%.")
        
        # Add note about the injury
        self.add_note(f"Suffered burn damage: Took {damage}% damage (total now {self.player_data['damage']['burn']}%)")
    
    def add_poison_damage(self, min_damage, max_damage):
        """Apply poison damage to the player"""
        # Calculate damage
        damage = random.randint(min_damage, max_damage)
        
        # Apply damage
        original_damage = self.player_data["damage"].get("poison", 0)
        self.player_data["damage"]["poison"] = min(100, original_damage + damage)
        
        # Show damage message
        messagebox.showinfo("Poison Damage", f"You suffered {damage}% poison damage! Total poison damage: {self.player_data['damage']['poison']}%.")
        
        # Add note about the injury
        self.add_note(f"Suffered poison damage: Took {damage}% damage (total now {self.player_data['damage']['poison']}%)")

    def enter_special_room(self, room_name):
        """Enter a special room on the station"""
        # Import special room classes
        from game.special_rooms import MedBay, Bridge, Security, Engineering, Bar, Botany
        from game.quarters import Quarters

        # Add the ship_map to player_data temporarily for special rooms to access
        self.player_data["ship_map"] = self.ship_map
        
        room_instance = None
        if room_name == "MedBay":
            # Pass station_crew as a separate argument
            room_instance = MedBay(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Bridge":
            room_instance = Bridge(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Security":
            room_instance = Security(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Engineering":
            room_instance = Engineering(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Bar":
            room_instance = Bar(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Botany":
            room_instance = Botany(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Quarters": # Quarters might not need crew data, adjust if needed
            room_instance = Quarters(self.root, self.player_data, self.update_player_data_from_room) # Assuming Quarters doesn't need crew

    def enter_special_room_at(self, room_name, target_key):
        """Enter a special room at a specified target location"""
        # Get room details
        room_details = self.ship_map.get(target_key)
        if not room_details:
            return # Invalid target key
        
        # Check if room is locked
        if room_details.get("locked", False):
            messagebox.showinfo("Locked", f"The {room_name} door is locked.")
            return
        
        # Update player location to the special room's coordinates
        self.player_data["location"] = {"x": int(target_key.split(',')[0]), "y": int(target_key.split(',')[1])}
        
        # Add ship_map temporarily
        self.player_data["ship_map"] = self.ship_map

        # Import special room classes
        from game.special_rooms import MedBay, Bridge, Security, Engineering, Bar, Botany
        from game.quarters import Quarters

        room_instance = None
        # Create room instance (passing player_data and station_crew)
        if room_name == "MedBay":
            room_instance = MedBay(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Bridge":
             room_instance = Bridge(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Security":
            room_instance = Security(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Engineering":
            room_instance = Engineering(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Bar":
             room_instance = Bar(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Botany":
             room_instance = Botany(self.root, self.player_data, self.station_crew, self.update_player_data_from_room)
        elif room_name == "Quarters": # Quarters might not need crew data
             room_instance = Quarters(self.root, self.player_data, self.update_player_data_from_room)

    def update_player_data_from_room(self, updated_player_data, updated_station_crew=None):
        """Update player and crew data when returning from a room"""
        # Remove temporary keys from player data if they exist
        ship_map_from_room = updated_player_data.pop("ship_map", None)

        # Update player data
        self.player_data = updated_player_data

        # Update station_crew ONLY if it was passed back
        if updated_station_crew is not None:
             self.station_crew = updated_station_crew

        # Update ship_map if it was modified in the special room
        if ship_map_from_room:
            self.ship_map = ship_map_from_room
            
        # Ensure market thread is running
        if not self.market_running:
            self.start_market_thread()
            
        # Ensure battery timer is running
        if not self.battery_timer_running:
            self.start_battery_timer()
        
        # Determine the correct hallway position based on the room exited
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        
        # Determine correct hallway return position
        return_x, return_y = x, y # Default to current if not a special room exit
        if x == 6 and y == 0: # Exited Bridge
            return_x, return_y = 5, 0
        elif x == 0 and y == 6: # Exited MedBay
            return_x, return_y = 0, 5
        elif x == 6 and y == 6: # Exited Security
            return_x, return_y = 5, 5
        elif x == 6 and y == 3: # Exited Engineering
            return_x, return_y = 5, 3
        elif x == 0 and y == -1: # Exited Bar
            return_x, return_y = 0, 3
        elif x == 3 and y == -1: # Exited Botany
            return_x, return_y = 3, 0
        elif x == -1 and y == 0: # Exited Quarters
            return_x, return_y = 0, 0
        
        # Set the player's location to the correct adjacent hallway tile
        self.player_data["location"]["x"] = return_x
        self.player_data["location"]["y"] = return_y
        
        # Show hallway screen at the new position
        self.show_hallway()

    def unlock_door(self):
        """Attempt to unlock a special room door"""
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        location_key = f"{x},{y}"
        
        # Check if there's an adjacent special room to unlock
        special_rooms = {
            "5,0": "Bridge",     # Adjacent to Bridge
            "0,5": "MedBay",     # Adjacent to MedBay
            "5,5": "Security",   # Adjacent to Security
            "5,3": "Engineering", # Adjacent to Engineering
            "0,3": "Bar"         # Adjacent to Bar
        }
        
        if location_key in special_rooms:
            room_name = special_rooms[location_key]
            room_coords = {
                "Bridge": "6,0", 
                "MedBay": "0,6", 
                "Security": "6,6",
                "Engineering": "6,3",
                "Bar": "0,-1"
            }
            room_key = room_coords[room_name]
            
            # Check if room is locked
            if self.ship_map[room_key].get("locked", False):
                # Unlock the room
                self.ship_map[room_key]["locked"] = False
                self.ship_map[room_key]["desc"] = f"The {room_name}. The door is unlocked."
                
                # Don't change the player's location, just open the room
                self.enter_special_room(room_name)
            else:
                # Room is already unlocked, just enter it
                self.enter_special_room(room_name)
        else:
            messagebox.showinfo("No Door Nearby", "There's no special room door nearby to unlock.")

    def check_special_room(self):
        """Check if we're at a special room and can enter it"""
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        location_key = f"{x},{y}"
        
        # Define special room coordinates and their names
        special_rooms = {
            "6,0": "Bridge",
            "0,6": "MedBay",
            "6,6": "Security"
        }
        
        if location_key in special_rooms:
            room_name = special_rooms[location_key]
            
            # If room is not locked, allow entry
            if not self.ship_map[location_key].get("locked", False):
                # Enter the special room
                self.enter_special_room(room_name)
                return True
            else:
                messagebox.showinfo("Locked Door", f"The {room_name} door is locked.")
        
        return False

    def is_near_special_room(self):
        """Check if we're near a special room that can be unlocked"""
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        location_key = f"{x},{y}"
        
        # Adjacent locations to special rooms
        special_room_adjacents = {
            "5,0": "Bridge",     # Adjacent to Bridge
            "0,5": "MedBay",     # Adjacent to MedBay
            "5,5": "Security",   # Adjacent to Security
            "5,3": "Engineering", # Adjacent to Engineering Bay
            "0,3": "Bar"         # Adjacent to Bar
        }
        
        # Check if we're near a special room and if that room is locked
        if location_key in special_room_adjacents:
            room_name = special_room_adjacents[location_key]
            room_coords = {
                "Bridge": "6,0", 
                "MedBay": "0,6", 
                "Security": "6,6",
                "Engineering": "6,3",
                "Bar": "0,-1"
            }
            room_key = room_coords[room_name]
            
            # Only return True if the room is actually locked
            return self.ship_map[room_key].get("locked", False)
            
        return False

    def save_and_exit(self):
        """Save the game and exit to main menu"""
        # Update market data before saving
        self.update_market_data()
        
        Game.save_game(self.player_data)
        
        # Stop the battery timer before returning to menu
        self.stop_battery_timer()
        
        # Return to main menu
        self.show_main_menu()

    def add_random_item(self):
        """Add a random item (using item definitions) to the player's inventory"""
        # Get all available item IDs from the master list
        available_item_ids = list(ALL_ITEMS.keys())
        
        if not available_item_ids:
            messagebox.showwarning("Error", "No items defined to be found.")
            return
            
        # Choose a random item ID
        item_id = random.choice(available_item_ids)
        
        # Get a copy of the item definition
        item_def = get_item_definition(item_id)
        
        if not item_def:
            messagebox.showerror("Error", f"Could not find definition for random item ID: {item_id}")
            return

        # Ensure inventory list exists
        self.player_data.setdefault("inventory", [])
            
        # Add the item dictionary to inventory
        self.player_data["inventory"].append(item_def)
        item_name = item_def.get("name", "an item")
        messagebox.showinfo("Item Found", f"You found {item_name} and added it to your inventory.")
        
        # Add note about the item found
        self.add_note(f"Found {item_name} ({item_id}) and added it to inventory.")
    
    def add_market_knowledge(self):
        """Add market knowledge to the player - reveals a tip about a stock"""
        if not self.player_data["stock_market"]["companies"]:
            messagebox.showinfo("Market Tip", "You heard a stock tip, but don't understand the market yet.")
            return
            
        company = random.choice(self.player_data["stock_market"]["companies"])
        direction = random.choice(["rise", "fall"])
        
        message = ""
        if direction == "rise":
            message = f"Overheard that {company['name']} stock is expected to rise soon!"
            messagebox.showinfo("Market Tip", message)
        else:
            message = f"Overheard that {company['name']} stock might be dropping in value soon!"
            messagebox.showinfo("Market Tip", message)
        
        # Add note about the market tip
        self.add_note(f"Market Tip: {message}")
    
    def station_announcement(self):
        """Display a random station announcement"""
        announcements = [
            "Reminder to all crew: safety protocols must be followed at all times.",
            "The cafeteria will be serving special meal rations today.",
            "Maintenance is scheduled in Sector 7 tomorrow.",
            "All personnel are reminded to report suspicious activity to security.",
            "Weekly crew meeting is postponed until further notice.",
            "Environmental controls are being recalibrated. Expect minor temperature fluctuations."
        ]
        
        announcement = random.choice(announcements)
        messagebox.showinfo("Station Announcement", f"The PA system crackles: '{announcement}'")

if __name__ == "__main__":
    root = tk.Tk()
    app = SpaceStationGame(root)
    root.mainloop() 