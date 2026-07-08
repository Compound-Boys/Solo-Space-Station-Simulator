import tkinter as tk
from tkinter import messagebox
import random

from game.door_control import toggle_door_lock as toggle_room_door_lock, is_door_locked
from game.drinks import DRINKS_MENU, MIXED_DRINKS, DrinkMixer, is_drink_alcoholic
from game.special_rooms.shared import add_note, leave_room, open_room_in_main_window

class Bar:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self.bar_window = open_room_in_main_window(parent_window, "Bar", self.on_closing)

        # Track bartender mode
        self.bartender_mode = False
        self.drink_mixer = DrinkMixer(self.bar_window, self.player_data)
        
        # Title
        room_label = tk.Label(self.bar_window, text="Station Bar", font=("Arial", 24), bg="black", fg="white")
        room_label.pack(pady=30)
        
        # Description
        desc_label = tk.Label(self.bar_window, 
                              text="The station's bar is lively and well-furnished. A long counter runs along one wall, with shelves of drinks behind it. Tables and chairs are scattered about, and soft music plays in the background.",
                              font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Room actions
        self.button_frame = tk.Frame(self.bar_window, bg="black")
        self.button_frame.pack(pady=20)
        
        # Check if user is a bartender or captain
        is_bartender = self.player_data.get("job") == "Bartender"
        is_captain = self.player_data.get("job") == "Captain"
        
        if is_bartender or is_captain:
            # Add bartender station access
            station_btn = tk.Button(self.button_frame, text="Enter Bartender Station", font=("Arial", 14), width=20, command=self.access_bartender_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for bartenders and captains
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for non-bartenders
            self.show_room_options()
        
        # Exit button
        exit_btn = tk.Button(self.bar_window, text="Exit Room", font=("Arial", 14), width=15, command=self.on_closing)
        exit_btn.pack(pady=20)
    
    def show_room_options(self):
        """Show regular room options that all players can access"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Order drinks button
        order_btn = tk.Button(self.button_frame, text="Order Drinks", font=("Arial", 14), width=20, command=self.show_drink_menu)
        order_btn.pack(pady=10)
        
        # Socialize option
        socialize_btn = tk.Button(self.button_frame, text="Socialize", font=("Arial", 14), width=20, command=self.socialize)
        socialize_btn.pack(pady=10)
        
        # Only show "Back to Station Menu" if player is a bartender
        is_bartender = self.player_data.get("job") == "Bartender"
        if is_bartender:
            # Back to station menu button
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)
    
    def show_drink_menu(self):
        """Show the menu of available drinks"""
        # Create a popup for the drink menu
        menu_popup = tk.Toplevel(self.bar_window)
        menu_popup.title("Drink Menu")
        menu_popup.configure(bg="black")
        menu_popup.transient(self.bar_window)
        menu_popup.grab_set()
        
        # Center the popup
        menu_popup.update_idletasks()
        width = 700
        height = 600
        x = (menu_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (menu_popup.winfo_screenheight() // 2) - (height // 2)
        menu_popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        title_label = tk.Label(menu_popup, text="Drink Menu", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)
        
        # Current credits
        credits_label = tk.Label(menu_popup, text=f"Your credits: {self.player_data['credits']}", 
                             font=("Arial", 14), bg="black", fg="white")
        credits_label.pack(pady=5)
        
        # Create menu tabs for different categories
        tab_frame = tk.Frame(menu_popup, bg="black")
        tab_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        alcohol_tab_frame = tk.Frame(menu_popup, bg="black")
        alcohol_tab_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Pin action buttons to the bottom so they stay visible
        btn_frame = tk.Frame(menu_popup, bg="black")
        btn_frame.pack(side=tk.BOTTOM, pady=10)
        
        # Create frame for the menu
        menu_frame = tk.Frame(menu_popup, bg="black")
        menu_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(menu_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create listbox for the drinks
        drink_listbox = tk.Listbox(menu_frame, bg="black", fg="white", font=("Arial", 12),
                                width=50, height=15, yscrollcommand=scrollbar.set)
        drink_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=drink_listbox.yview)
        
        # Description frame
        desc_frame = tk.Frame(menu_popup, bg="black")
        desc_frame.pack(padx=20, pady=5, fill=tk.X)
        
        # Create description label - moved before the function that uses it
        desc_label = tk.Label(desc_frame, text="Select a drink to see its description", 
                          font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack()
        
        # Organize drinks into categories
        basic_drinks = {}
        mixed_drinks = {}
        all_drinks = {}
        
        # Copy the drinks to their respective categories
        for name, details in DRINKS_MENU.items():
            basic_drinks[name] = details
            all_drinks[name] = details
            
        for name, details in MIXED_DRINKS.items():
            mixed_drinks[name] = details
            all_drinks[name] = details

        alcoholic_drinks = {
            name: details for name, details in all_drinks.items()
            if is_drink_alcoholic(name, details)
        }
        non_alcoholic_drinks = {
            name: details for name, details in all_drinks.items()
            if not is_drink_alcoholic(name, details)
        }
        
        # Track the current category and selected drink
        current_category = {"drinks": all_drinks, "name": "All Drinks"}
        selected_drink = {"name": "", "details": None}
        
        # Function to populate the listbox with a category
        def show_category(category_drinks, category_name):
            # Clear the listbox
            drink_listbox.delete(0, tk.END)
            
            # Update current category
            current_category["drinks"] = category_drinks
            current_category["name"] = category_name
            
            # Add header
            drink_listbox.insert(tk.END, f"--- {category_name} ---")
            
            # Add drinks to the listbox
            for drink, details in category_drinks.items():
                drink_listbox.insert(tk.END, f"{drink} - {details['price']} credits")
            
            # Reset the description
            desc_label.config(text="Select a drink to see its description")
        
        # Create the category buttons with more spacing
        all_btn = tk.Button(tab_frame, text="All Drinks", font=("Arial", 12), width=12,
                         command=lambda: show_category(all_drinks, "All Drinks"))
        all_btn.pack(side=tk.LEFT, padx=15)
        
        basic_btn = tk.Button(tab_frame, text="Basic Drinks", font=("Arial", 12), width=12,
                           command=lambda: show_category(basic_drinks, "Basic Drinks"))
        basic_btn.pack(side=tk.LEFT, padx=15)
        
        mixed_btn = tk.Button(tab_frame, text="Mixed Drinks", font=("Arial", 12), width=12,
                           command=lambda: show_category(mixed_drinks, "Mixed Drinks"))
        mixed_btn.pack(side=tk.LEFT, padx=15)

        alcoholic_btn = tk.Button(tab_frame, text="Alcoholic", font=("Arial", 12), width=12,
                               command=lambda: show_category(alcoholic_drinks, "Alcoholic"))
        alcoholic_btn.pack(side=tk.LEFT, padx=15)

        non_alcoholic_btn = tk.Button(tab_frame, text="Non-Alcoholic", font=("Arial", 12), width=12,
                                   command=lambda: show_category(non_alcoholic_drinks, "Non-Alcoholic"))
        non_alcoholic_btn.pack(side=tk.LEFT, padx=15)
        
        # Show all drinks by default
        show_category(all_drinks, "All Drinks")
        
        # Update description when a drink is selected
        def on_select(event):
            selection = drink_listbox.curselection()
            if not selection or selection[0] == 0:  # Skip the header
                return
                
            # Get the selected drink name by parsing the listbox entry
            index = selection[0]
            entry = drink_listbox.get(index)
            
            # Parse the entry to get the drink name
            if " - " in entry:
                drink_name = entry.split(" - ")[0]
                
                # Find the drink details in the current category
                if drink_name in current_category["drinks"]:
                    drink_details = current_category["drinks"][drink_name]
                    desc_label.config(text=drink_details['desc'])
                    
                    # Update the selected drink
                    selected_drink["name"] = drink_name
                    selected_drink["details"] = drink_details
            
        drink_listbox.bind('<<ListboxSelect>>', on_select)
        
        # Order button
        order_btn = tk.Button(btn_frame, text="Order Selected Drink", font=("Arial", 12), 
                           command=lambda: self.order_drink_from_menu(selected_drink, menu_popup, credits_label))
        order_btn.pack(side=tk.LEFT, padx=10)
        
        # Close button
        close_btn = tk.Button(btn_frame, text="Close Menu", font=("Arial", 12), command=menu_popup.destroy)
        close_btn.pack(side=tk.LEFT, padx=10)
    
    def order_drink_from_menu(self, selected_drink, popup, credits_label):
        """Process an order for a drink selected from the menu"""
        # Check if a drink is selected
        if not selected_drink["name"] or not selected_drink["details"]:
            tk.messagebox.showinfo("Selection Needed", "Please select a drink first", parent=popup)
            return
        
        drink_name = selected_drink["name"]
        drink_details = selected_drink["details"]
        
        # Check if player has enough credits
        if self.player_data['credits'] < drink_details['price']:
            tk.messagebox.showinfo("Insufficient Credits", 
                               f"You don't have enough credits to order {drink_name}.", 
                               parent=popup)
            return
        
        # Process the order
        self.player_data['credits'] -= drink_details['price']
        
        # Update the credits display
        credits_label.config(text=f"Your credits: {self.player_data['credits']}")
        
        # Add a note about the purchase
        add_note(self.player_data, f"Purchased {drink_name} at the bar for {drink_details['price']} credits.")
        
        # Show confirmation message
        tk.messagebox.showinfo("Order Successful", 
                           f"You've ordered a {drink_name} for {drink_details['price']} credits. Enjoy!", 
                           parent=popup)
    
    def socialize(self):
        """Interact with other crew members in the bar"""
        conversations = [
            "You chat with a group of engineers about the latest station upgrades.",
            "A security officer shares stories about past incidents on the station.",
            "You overhear some interesting gossip about the captain's leadership style.",
            "A doctor tells you about a strange medical case they recently handled.",
            "Several crew members are discussing the latest sports match from Earth.",
            "You find yourself in a philosophical debate about space exploration with a scientist."
        ]
        
        # Select a random conversation
        conversation = random.choice(conversations)
        
        # Show the conversation result
        self.bar_window.after(10, lambda: tk.messagebox.showinfo("Socializing", conversation, parent=self.bar_window))
        
        # Make sure the window stays on top after dialog
        self.bar_window.after(20, self.bar_window.lift)
        self.bar_window.focus_force()
    
    def access_bartender_station(self):
        """Access the bartender station for mixing drinks"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Set bartender mode
        self.bartender_mode = True
        
        # Add drink mixing button
        mix_btn = tk.Button(self.button_frame, text="Mix Drinks", font=("Arial", 14), width=20, command=self.show_drink_mixer)
        mix_btn.pack(pady=10)
        
        # Add button to view list of recipes
        recipes_btn = tk.Button(self.button_frame, text="View Recipes", font=("Arial", 14), width=20, command=self.show_recipes)
        recipes_btn.pack(pady=10)
        
        # Add button to serve premade drinks (same as regular menu)
        serve_btn = tk.Button(self.button_frame, text="Serve Regular Drinks", font=("Arial", 14), width=20, command=self.show_drink_menu)
        serve_btn.pack(pady=10)
        
        # Back button
        back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                           command=self.show_station_menu)
        back_btn.pack(pady=10)
    
    def show_drink_mixer(self):
        """Show interface for mixing custom drinks"""
        self.drink_mixer.show_mixer()

    def show_recipes(self):
        """Show a list of known drink recipes"""
        self.drink_mixer.show_recipes()

    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, "0,-1", self.bar_window)
    
    def on_closing(self):
        """Handle window closing"""
        if is_door_locked(self.player_data, "0,-1"):
            self.bar_window.after(
                10,
                lambda: tk.messagebox.showinfo(
                    "Locked Door",
                    "The door is locked. You must unlock it before leaving.",
                    parent=self.bar_window,
                ),
            )
            self.bar_window.after(20, self.bar_window.lift)
            self.bar_window.focus_force()
            return

        self.bartender_mode = False
        leave_room(self.return_callback, self.player_data, self.station_crew)

    def show_station_menu(self):
        """Return to main station menu options"""
        # Reset bartender mode
        self.bartender_mode = False
        
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Check if user is a bartender or captain
        is_bartender = self.player_data.get("job") == "Bartender"
        is_captain = self.player_data.get("job") == "Captain"
        
        if is_bartender or is_captain:
            # Add bartender station access
            station_btn = tk.Button(self.button_frame, text="Enter Bartender Station", font=("Arial", 14), width=20, command=self.access_bartender_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for bartenders and captains
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()
