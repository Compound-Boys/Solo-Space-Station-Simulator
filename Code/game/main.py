import tkinter as tk
import os
import sys
import time
import copy
import threading
import datetime
import random
from tkinter import messagebox

from game.maps import donut
from game.helper_methods.stock_market import (
    StockMarketEngine,
    default_stock_market_state,
    generate_market_tip,
)
from game.helper_methods.game import Game
from game.special_rooms import MedBay, Bridge, Security, Engineering, Bar, Botany, Quarters
from game.objects.items import get_item_definition, ALL_ITEMS, ItemInventoryMixin
from game.character_methods.character_creation import CharacterCreation
from game.character_methods.character_sheet import render_character_sheet
from game.helper_methods.power_constants import (
    LOW_POWER_SYSTEM_LEVELS,
    HIGH_MODE_SOLAR_DRAIN,
    calculate_discharge,
    calculate_solar_charge,
    default_station_power,
)
from game.helper_methods.ui_panels import (
    open_modal_panel,
    configure_message_buffer,
    report_message,
)

SPECIAL_ROOM_CLASSES = {
    "Bridge": Bridge,
    "MedBay": MedBay,
    "Security": Security,
    "Engineering": Engineering,
    "Bar": Bar,
    "Botany": Botany,
    "Quarters": Quarters,
}

SPECIAL_ROOM_TILES = donut.SPECIAL_ROOM_TILES
SPECIAL_ROOM_HALLWAY = donut.SPECIAL_ROOM_HALLWAY

class SpaceStationGame(ItemInventoryMixin):
    def __init__(self, root, base_path):
        self.root = root
        self.base_path = base_path
        self.root.title("Space Station 13 Text Clone")
        self.root.geometry("920x690")
        self.root.configure(bg="black")
        configure_message_buffer(self.root)

        self.market_running = False
        self.market_thread = None
        self.station_crew = []

        self.battery_timer_running = False
        self.battery_timer_id = None
        self._event_effect_messages = None

        # Stock market background tracking
        self.market_engine = StockMarketEngine()
        
        self.player_data = {
            "name": "",
            "job": "",
            "department": "",
            "subdepartment": "",
            "inventory": [],
            "credits": 1000,
            "location": {"x": 0, "y": 0},
            "stock_holdings": {},
            "station_crew": [],
            "stock_market": default_stock_market_state(),
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
            "station_power": default_station_power(),
            "notes": []
        }

        # Ship map configuration (see game/maps/donut.py for the layout data)
        self.ship_map = copy.deepcopy(donut.SHIP_MAP)
        
        # Bind the window close event to stop the market thread
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.show_main_menu()

    def _sync_crew_to_player_data(self):
        """Write in-memory crew list into player_data before saving."""
        self.player_data["station_crew"] = self.station_crew

    def _load_crew_from_player_data(self):
        """Restore crew list from loaded player_data."""
        self.station_crew = self.player_data.get("station_crew", [])

    def _save_game(self):
        """Update market state, sync crew, and persist the save file."""
        self.market_engine.sync_to_player_data(self.player_data)
        self._sync_crew_to_player_data()
        Game.save_game(self.player_data)

    def _ensure_game_running(self):
        """Start background market and battery timers if they are not running."""
        if not self.market_running:
            self.start_market_thread()
        if not self.battery_timer_running:
            self.start_battery_timer()

    def _report_effect(self, title, message):
        """Show an effect popup, or buffer the message during a random event."""
        if self._event_effect_messages is not None:
            self._event_effect_messages.append(message)
        else:
            report_message(title, message, kind="info", parent=self.root)

    def _add_damage_type(self, damage_key, label, min_damage, max_damage):
        """Apply incremental damage of a given type to the player."""
        damage = random.randint(min_damage, max_damage)
        original_damage = self.player_data["damage"].get(damage_key, 0)
        self.player_data["damage"][damage_key] = min(100, original_damage + damage)
        total = self.player_data["damage"][damage_key]
        self._report_effect(
            f"{label} Damage",
            f"You suffered {damage}% {label.lower()} damage! Total {label.lower()} damage: {total}%.",
        )
        self.add_note(f"Suffered {label.lower()} damage: Took {damage}% damage (total now {total}%)")

    def _enter_special_room(self, room_class):
        """Create a special room UI instance from a room class."""
        self.player_data["ship_map"] = self.ship_map
        self.current_room = room_class(
            self.root, self.player_data, self.station_crew, self.update_player_data_from_room
        )

    def _instantiate_special_room(self, room_name):
        """Create a special room UI instance by name."""
        room_class = SPECIAL_ROOM_CLASSES.get(room_name)
        if room_class is None:
            return
        self._enter_special_room(room_class)

    def on_closing(self):
        """Handle application closing"""
        self.stop_market_thread()
        self.stop_battery_timer()

        if self.player_data and self.player_data.get("name"):
            self._save_game()

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
            
        if "station_power" not in self.player_data:
            self.player_data["station_power"] = default_station_power()

        try:
            # Get the last update time
            last_update = datetime.datetime.fromisoformat(self.player_data["station_power"]["last_update_time"])
            now = datetime.datetime.now()
            elapsed_seconds = (now - last_update).total_seconds()
            
            # Get system power levels from player data
            system_levels = self.player_data["station_power"]["system_levels"]
            total_discharge_rate = calculate_discharge(system_levels, elapsed_seconds)

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
                self.trigger_power_outage()
        except Exception as e:
            print(f"Error updating battery: {e}")
            self.player_data["station_power"]["last_update_time"] = datetime.datetime.now().isoformat()

        # Poll every 2 seconds
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

                elif apply_recovery and current_oxygen_damage > 0:
                    recovery_amount = min(current_oxygen_damage, elapsed_seconds * recovery_rate_per_second)
                    new_oxygen_damage = max(0, current_oxygen_damage - recovery_amount)
                    crew_member["damage"]["oxygen"] = new_oxygen_damage
                    
                    if is_player:
                         print(f"Player Oxygen recovery: Current={current_oxygen_damage:.1f}%, Recovered={recovery_amount:.1f}% -> New={new_oxygen_damage:.1f}% (elapsed={elapsed_seconds:.1f}s)")

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
            report_message("Oxygen Warning", warnings[threshold], kind="warning", parent=self.root)
            self.add_note(f"Suffered {threshold}% oxygen damage due to life support failure.")
        except Exception as e:
            print(f"Error showing oxygen warning: {e}")
            
    def handle_oxygen_death(self):
        """Handle player death from oxygen deprivation"""
        try:
            report_message(
                "CRITICAL: Oxygen Depleted",
                "You have succumbed to oxygen deprivation. Emergency medical protocols have been activated, and you have been revived at minimal health levels.",
                kind="error",
                parent=self.root,
            )
            
            # Reset oxygen damage
            self.player_data["damage"]["oxygen"] = 50
            
            # Set all limbs to critical levels
            for limb in self.player_data["limbs"]:
                self.player_data["limbs"][limb] = 20
                
            # Add note about near-death
            self.add_note("CRITICAL EVENT: Nearly died from oxygen deprivation. Emergency medical systems intervened.")
            
            # Return player to quarters
            self.player_data["location"] = dict(donut.QUARTERS_LOCATION)
            self.show_hallway()
        except Exception as e:
            print(f"Error handling oxygen death: {e}")
    
    def show_low_power_warning(self):
        """Show warning about low battery power"""
        report_message(
            "Low Power Warning",
            "Warning: Station battery power low. Emergency lighting active. Please activate solar panels.",
            kind="warning",
            parent=self.root,
        )
    
    def trigger_power_outage(self):
        """Trigger effects of a complete power outage"""
        try:
            # Set battery to minimum level to prevent multiple outage triggers
            self.player_data["station_power"]["battery_level"] = 0.1
            report_message(
                "Power Outage",
                "CRITICAL: Station power failure! Emergency systems active. Activate solar arrays immediately!",
                kind="error",
                parent=self.root,
            )
            self.add_note("CRITICAL: Station suffered complete power failure. Emergency systems active.")

        except Exception as e:
            print(f"Error handling power outage: {e}")

    def run_stock_market(self):
        """Run the stock market in the background"""
        while self.market_running:
            if self.market_engine.tick_if_due():
                self.market_engine.sync_to_player_data(self.player_data)

            time.sleep(1)
    
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

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
            self.market_engine.companies,
            on_back=self.show_main_menu,
            on_complete=self._on_character_created
        )
    
    def _on_character_created(self, player_data, station_crew):
        """Receive the finished character and NPC crew from character creation"""
        self.player_data = player_data
        self.station_crew = station_crew
        self._sync_crew_to_player_data()
        self.save_and_start()

    def save_and_start(self):
        """Save the character and start the game in quarters."""
        self.player_data["location"] = dict(donut.QUARTERS_LOCATION)
        self._save_game()
        self.start_market_thread()
        self.start_battery_timer()
        self.enter_special_room_at("Quarters", donut.QUARTERS_KEY)
    
    def show_character_sheet(self):
        """Show the character sheet window"""
        for widget in self.root.winfo_children():
            widget.destroy()

        self._ensure_game_running()

        # Configure window size
        self.root.geometry("920x805")  # Increased height to accommodate all content

        # Store the previous screen to return to
        self.previous_screen = getattr(self, 'previous_screen', 'show_hallway')

        # Pack Return at the bottom first so it stays visible above tall sheet content
        return_btn = tk.Button(self.root, text="Return", font=("Arial", 14), width=15,
                             command=lambda: getattr(self, self.previous_screen)())
        return_btn.pack(side=tk.BOTTOM, pady=20)

        render_character_sheet(
            self.root,
            self.player_data,
            on_inventory=self.show_inventory_popup,
            on_holdings=self.show_holdings_popup,
            on_notes=self.show_notes_popup,
        )
    
    def show_notes_popup(self):
        """Show character notes as an in-main-window overlay."""
        panel, popup = open_modal_panel(self.root, title="Character Notes")

        title_label = tk.Label(popup, text="Character Notes", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        frame = tk.Frame(popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        notes_text = tk.Text(frame, bg="black", fg="white", font=("Arial", 12),
                           width=60, height=20, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=notes_text.yview)

        notes_text.config(state=tk.DISABLED)

        if "notes" in self.player_data and self.player_data["notes"]:
            notes_text.config(state=tk.NORMAL)

            for note in reversed(self.player_data["notes"]):
                if "timestamp" in note and "text" in note:
                    timestamp = note["timestamp"]
                    text = note["text"]

                    try:
                        dt = datetime.datetime.fromisoformat(timestamp)
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        formatted_time = timestamp

                    notes_text.insert(tk.END, f"{formatted_time}:\n{text}\n\n")
                else:
                    notes_text.insert(tk.END, f"{str(note)}\n\n")

            notes_text.config(state=tk.DISABLED)
        else:
            notes_text.config(state=tk.NORMAL)
            notes_text.insert(tk.END, "No notes recorded yet.")
            notes_text.config(state=tk.DISABLED)

        def _on_notes_mousewheel(event):
            try:
                notes_text.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass

        popup.bind("<MouseWheel>", _on_notes_mousewheel)

        def _close():
            try:
                popup.unbind("<MouseWheel>")
            except tk.TclError:
                pass
            panel.close()

        close_btn = tk.Button(popup, text="Close", font=("Arial", 12), width=10, command=_close)
        close_btn.pack(pady=10)

    def add_note(self, text):
        """Add a note to the player's notes"""
        if "notes" not in self.player_data:
            self.player_data["notes"] = []

        note = {
            "timestamp": datetime.datetime.now().isoformat(),
            "text": text
        }

        self.player_data["notes"].append(note)

    def show_holdings_popup(self):
        """Show stock holdings as an in-main-window overlay."""
        panel, popup = open_modal_panel(self.root, title="Stock Holdings")

        title_label = tk.Label(popup, text="Stock Holdings", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        frame = tk.Frame(popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        holdings_list = tk.Listbox(frame, bg="black", fg="white", font=("Arial", 12),
                                 width=30, height=15, yscrollcommand=scrollbar.set)
        holdings_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=holdings_list.yview)

        if not self.player_data.get('stock_holdings', {}):
            holdings_list.insert(tk.END, "You don't own any company stocks.")
        else:
            for company, shares in self.player_data['stock_holdings'].items():
                holdings_list.insert(tk.END, f"{company}: {shares} shares")

        def _on_holdings_mousewheel(event):
            try:
                holdings_list.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass

        popup.bind("<MouseWheel>", _on_holdings_mousewheel)

        def _close():
            try:
                popup.unbind("<MouseWheel>")
            except tk.TclError:
                pass
            panel.close()

        close_btn = tk.Button(popup, text="Close", font=("Arial", 12), width=10, command=_close)
        close_btn.pack(pady=10)
    
    def use_door(self):
        # Get current location
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        
        if x == -1 and y == 0:  # In quarters, move to hallway
            hallway_x, hallway_y = donut.SPECIAL_ROOM_HALLWAY[donut.QUARTERS_KEY]
            self.player_data["location"] = {"x": hallway_x, "y": hallway_y}
            self.show_hallway()
        else:  # In hallway, move to quarters
            self.enter_special_room_at("Quarters", donut.QUARTERS_KEY)
    
    def get_location_key(self):
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]
        return f"{x},{y}"
    
    def show_hallway(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._ensure_game_running()

        loc_key = self.get_location_key()

        if loc_key not in self.ship_map:
            messagebox.showerror("Error", "Invalid location!")
            self.player_data["location"] = {"x": 0, "y": 0}
            loc_key = "0,0"

        if loc_key in SPECIAL_ROOM_TILES:
            room_name = SPECIAL_ROOM_TILES[loc_key]
            location = self.ship_map[loc_key]
            if location.get("locked", False):
                messagebox.showinfo("Locked Door", f"The {room_name} door is locked.")
                hallway_x, hallway_y = SPECIAL_ROOM_HALLWAY[loc_key]
                self.player_data["location"]["x"] = hallway_x
                self.player_data["location"]["y"] = hallway_y
                loc_key = self.get_location_key()
            else:
                self._instantiate_special_room(room_name)
                return

        location = self.ship_map[loc_key]
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
        
        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]

        directions = donut.get_available_directions(x, y)
        north_available = directions["north"]
        south_available = directions["south"]
        east_available = directions["east"]
        west_available = directions["west"]

        # Special cases for room access points
        is_special_location = False
        
        # Bridge access from north end
        if (x, y) == SPECIAL_ROOM_HALLWAY[donut.BRIDGE_KEY]:
            is_special_location = True
            # Add the Bridge access button
            bridge_btn = tk.Button(nav_frame, text="Bridge", font=("Arial", 14), width=15,
                                command=lambda: self.enter_special_room_at("Bridge", donut.BRIDGE_KEY))
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
        elif (x, y) == SPECIAL_ROOM_HALLWAY[donut.MEDBAY_KEY]:
            is_special_location = True
            # Add MedBay access button
            medbay_btn = tk.Button(nav_frame, text="MedBay", font=("Arial", 14), width=15,
                              command=lambda: self.enter_special_room_at("MedBay", donut.MEDBAY_KEY))
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
        elif (x, y) == SPECIAL_ROOM_HALLWAY[donut.SECURITY_KEY]:
            is_special_location = True
            # Just one button for Security access
            security_btn = tk.Button(nav_frame, text="Security", font=("Arial", 14), width=15,
                                 command=lambda: self.enter_special_room_at("Security", donut.SECURITY_KEY))
            security_btn.grid(row=0, column=1, padx=10, pady=10)
            
            # Add west and south buttons for the corridors
            west_btn = tk.Button(nav_frame, text="Go West", font=("Arial", 14), width=15,
                               command=lambda: self.move_direction("west"))
            west_btn.grid(row=1, column=0, padx=10, pady=10)
            
            south_btn = tk.Button(nav_frame, text="Go South", font=("Arial", 14), width=15,
                                command=lambda: self.move_direction("south"))
            south_btn.grid(row=2, column=1, padx=10, pady=10)

        # Engineering Bay access from engineering hallway
        elif (x, y) == SPECIAL_ROOM_HALLWAY[donut.ENGINEERING_KEY]:
            is_special_location = True
            # Add Engineering Bay access button
            eng_bay_btn = tk.Button(nav_frame, text="Engineering Bay", font=("Arial", 14), width=15,
                                command=lambda: self.enter_special_room_at("Engineering", donut.ENGINEERING_KEY))
            eng_bay_btn.grid(row=0, column=1, padx=10, pady=10)
            
            # Add west and east buttons for the corridors
            west_btn = tk.Button(nav_frame, text="Go West", font=("Arial", 14), width=15,
                               command=lambda: self.move_direction("west"))
            west_btn.grid(row=1, column=0, padx=10, pady=10)
            
            east_btn = tk.Button(nav_frame, text="Go East", font=("Arial", 14), width=15,
                               command=lambda: self.move_direction("east"))
            east_btn.grid(row=1, column=2, padx=10, pady=10)
        
        # Bar access from bar entrance
        elif (x, y) == SPECIAL_ROOM_HALLWAY[donut.BAR_KEY]:
            is_special_location = True
            # Add Bar access button
            bar_btn = tk.Button(nav_frame, text="Bar", font=("Arial", 14), width=15,
                             command=lambda: self.enter_special_room_at("Bar", donut.BAR_KEY))
            bar_btn.grid(row=2, column=1, padx=10, pady=10)
            
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
            
            # Special case for the Botany Lab entrance
            if (x, y) == SPECIAL_ROOM_HALLWAY[donut.BOTANY_KEY]:
                botany_btn = tk.Button(nav_frame, text="Botany Lab", font=("Arial", 14), width=15,
                                     command=lambda: self.enter_special_room_at("Botany", donut.BOTANY_KEY))
                botany_btn.grid(row=1, column=0, padx=10, pady=10)
        
        # Only show return to quarters at the starting junction
        if (x, y) == SPECIAL_ROOM_HALLWAY[donut.QUARTERS_KEY]:
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
            messagebox.showerror("Error", "You can't go that way!")
            self.player_data["location"]["x"] = x - (1 if direction == "north" else -1 if direction == "south" else 0)
            self.player_data["location"]["y"] = y - (1 if direction == "east" else -1 if direction == "west" else 0)

        # 20% chance of a random hallway event
        if random.random() < 0.20:
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

        self._event_effect_messages = []
        try:
            event["effect"]()
            body = event["desc"]
            if self._event_effect_messages:
                body = body + "\n\n" + "\n".join(self._event_effect_messages)
            messagebox.showinfo(event["title"], body)
        finally:
            self._event_effect_messages = None
    
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
            self._report_effect(
                "Blunt Injury",
                f"Your {limb_name} took {damage}% blunt damage and is now at {self.player_data['limbs'][limb]}%.",
            )
            
            # Add note about the injury
            self.add_note(f"Suffered blunt damage to {limb_name}: Took {damage}% damage (from {original_health}% to {self.player_data['limbs'][limb]}%)")
    
    def add_credits(self, amount):
        """Add credits to the player"""
        self.player_data["credits"] += amount
        self._report_effect("Credits Added", f"You gained {amount} credits.")
        
        # Add note about credits gained
        self.add_note(f"Found {amount} credits. New balance: {self.player_data['credits']} credits.")
    
    def lose_credits(self, amount):
        """Subtract credits from the player (min 0)"""
        old_credits = self.player_data["credits"]
        self.player_data["credits"] = max(0, old_credits - amount)
        self._report_effect("Credits Lost", f"You lost {amount} credits.")
        
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
        self._load_crew_from_player_data()

        self.market_engine.load_from_player_data(self.player_data)
        self._ensure_game_running()
        
        # Determine where to show the player based on saved location
        if "location" in self.player_data:
            x = self.player_data["location"].get("x", 0)
            y = self.player_data["location"].get("y", 0)
            
            # Check if player is in a special room or hallway
            loc_key = f"{x},{y}"
            if loc_key in SPECIAL_ROOM_TILES and loc_key != donut.QUARTERS_KEY:
                # Player was in a special room, return to hallway entrance
                self.update_player_data_from_room(self.player_data)
            elif x == -1 and y == 0:
                # Player was in quarters — open the quarters room UI
                self.enter_special_room_at("Quarters", donut.QUARTERS_KEY)
            else:
                # Player was in a hallway
                self.show_hallway()
        else:
            # Default to quarters if location is missing
            self.player_data["location"] = dict(donut.QUARTERS_LOCATION)
            self.enter_special_room_at("Quarters", donut.QUARTERS_KEY)
        
        return True

    def add_burn_damage(self, min_damage, max_damage):
        """Apply burn damage to the player"""
        self._add_damage_type("burn", "Burn", min_damage, max_damage)

    def add_poison_damage(self, min_damage, max_damage):
        """Apply poison damage to the player"""
        self._add_damage_type("poison", "Poison", min_damage, max_damage)

    def enter_special_room_at(self, room_name, target_key):
        """Enter a special room at a specified target location"""
        room_details = self.ship_map.get(target_key)
        if not room_details:
            return

        if room_details.get("locked", False):
            messagebox.showinfo("Locked", f"The {room_name} door is locked.")
            return

        x_str, y_str = target_key.split(",")
        self.player_data["location"] = {"x": int(x_str), "y": int(y_str)}
        self._instantiate_special_room(room_name)

    def update_player_data_from_room(self, updated_player_data, updated_station_crew=None):
        """Update player and crew data when returning from a room"""
        # Remove temporary keys from player data if they exist
        ship_map_from_room = updated_player_data.pop("ship_map", None)
        exit_to_menu = updated_player_data.pop("_exit_to_menu", False)
        quit_without_save = updated_player_data.pop("_quit_without_save", False)

        # Update player data
        self.player_data = updated_player_data

        # Update station_crew ONLY if it was passed back
        if updated_station_crew is not None:
            self.station_crew = updated_station_crew
        self._sync_crew_to_player_data()

        if ship_map_from_room:
            self.ship_map = ship_map_from_room

        self._ensure_game_running()

        if quit_without_save:
            self.stop_market_thread()
            self.stop_battery_timer()
            self.root.destroy()
            return

        if exit_to_menu:
            self._save_game()
            self.stop_battery_timer()
            self.show_main_menu()
            return

        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]

        return_x, return_y = x, y
        loc_key = f"{x},{y}"
        if loc_key in SPECIAL_ROOM_HALLWAY:
            return_x, return_y = SPECIAL_ROOM_HALLWAY[loc_key]

        self.player_data["location"]["x"] = return_x
        self.player_data["location"]["y"] = return_y

        self.show_hallway()

    def save_and_exit(self):
        """Save the game and exit to main menu"""
        self._save_game()
        self.stop_battery_timer()
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
        self._report_effect("Item Found", f"You found {item_name} and added it to your inventory.")
        
        # Add note about the item found
        self.add_note(f"Found {item_name} ({item_id}) and added it to inventory.")
    
    def add_market_knowledge(self):
        """Add market knowledge to the player - reveals a tip about a stock"""
        message = generate_market_tip(self.player_data["stock_market"].get("companies", []))
        if message is None:
            self._report_effect("Market Tip", "You heard a stock tip, but don't understand the market yet.")
            return

        self._report_effect("Market Tip", message)
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
        self._report_effect("Station Announcement", f"The PA system crackles: '{announcement}'")

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    root = tk.Tk()
    app = SpaceStationGame(root, base_path)
    root.mainloop()