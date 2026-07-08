# game/items.py

import tkinter as tk
from tkinter import messagebox

# Base structure for items
# { 
#     "id": "unique_item_identifier", 
#     "name": "Display Name",               
#     "description": "Item description.",
#     "category": "Category",             # e.g., Tool, Book, Healing, Junk, Food, Drink, Special
#     "attributes": {                     # Optional: Specific data for the item
#         "content": "Text of the book...", # For books
#         "heal_amount": 25,               # For healing items
#         "skill_bonus": {"engineering": 5} # Example for tools
#     },
#     "actions": ["examine", "use", "read", "drop"] # List of possible actions
# }

# --- Define Book Content --- 
# Moved from main.py
WELCOME_GUIDE_CONTENT = """WELCOME TO SPACE STATION EXPLORER

Welcome to your new home among the stars! This guide will help you get acquainted with life aboard our station.

IMPORTANT TIPS:
- Always follow safety protocols
- Report any unusual activity to Security
- Keep your personal quarters clean and organized
- Get to know your fellow crew members
- Visit the Bar for social interactions
- Check the computer terminal for stock market opportunities

We hope you enjoy your stay and contribute to our thriving community!
"""

STATION_MAP_CONTENT = """SPACE STATION EXPLORER - STATION MAP

NORTH SECTION:
- Bridge (Command Center)
- North Hallway

EAST SECTION:
- Medical Bay
- East Hallway
- Bar

NORTHEAST SECTION:
- Security
- Engineering Bay

CENTRAL:
- Personal Quarters
- Hallway Junction

Remember to use navigation panels to move between sections.
"""

MAINTENANCE_MANUAL_CONTENT = """SPACE STATION MAINTENANCE MANUAL

BASIC TROUBLESHOOTING:
1. Power cycling is the first solution to try for most electronic issues
2. Check circuit breakers before reporting electrical failures
3. Small air leaks can be temporarily patched with emergency sealant
4. All maintenance tasks must be logged in the station computer

EMERGENCY PROCEDURES:
- Depressurization: Secure oxygen mask, move to nearest airlock
- Fire: Use extinguisher, then evacuate section
- Power failure: Emergency lighting will activate automatically

Contact Engineering for all major repair needs.
"""

# --- Master Item Dictionary --- 
# Contains the base definitions for all items in the game.
# When an item is added to inventory, a copy of this definition should be used.
ALL_ITEMS = {
    # --- Tools --- 
    "wrench": {
        "id": "wrench",
        "name": "Wrench",
        "description": "Standard tool for fastening and unfastening bolts and nuts. Useful for basic engineering tasks.",
        "category": "Tool",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "screwdriver": {
        "id": "screwdriver",
        "name": "Screwdriver", 
        "description": "A multi-head screwdriver for various screw types. Essential for accessing panels and device internals.",
        "category": "Tool",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "wirecutters": {
        "id": "wirecutters",
        "name": "Wirecutters",
        "description": "Tool for cutting and stripping wires safely. Necessary for electrical work.",
        "category": "Tool",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "repair_tool": { # From random event
        "id": "repair_tool",
        "name": "Repair Tool",
        "description": "A generic multi-tool for basic repairs.",
        "category": "Tool",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
     "basic_tools": { # From locker
        "id": "basic_tools",
        "name": "Basic Tools",
        "description": "A set containing a small wrench, screwdriver, and pliers.",
        "category": "Tool",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "flashlight": { # From random event & locker
        "id": "flashlight",
        "name": "Flashlight",
        "description": "A standard issue flashlight. Useful in dark areas.",
        "category": "Tool", # Or maybe Utility?
        "attributes": {},
        "actions": ["examine", "use", "drop"] # 'Use' could toggle light?
    },
    "welding_tool": { # Mentioned before, adding definition
        "id": "welding_tool",
        "name": "Welding Tool",
        "description": "For joining metal components. Requires a power source.",
        "category": "Tool",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "multimeter": { # Mentioned before, adding definition
        "id": "multimeter",
        "name": "Multimeter",
        "description": "Device for measuring voltage, current, and resistance.",
        "category": "Tool",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "maintenance_tool": { # From random event
        "id": "maintenance_tool",
        "name": "Maintenance Tool",
        "description": "A generic tool used for station upkeep.",
        "category": "Tool",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "diagnostic_tool": { # From random event
        "id": "diagnostic_tool",
        "name": "Diagnostic Tool",
        "description": "A scanner used to identify issues in machinery.",
        "category": "Tool",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "portable_scanner": { # From locker
        "id": "portable_scanner",
        "name": "Portable Scanner",
        "description": "Handheld scanner for analyzing objects, environments, or life signs.",
        "category": "Tool", 
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },

    # --- Books --- 
    "welcome_guide": {
        "id": "welcome_guide",
        "name": "Welcome Guide",
        "description": "A standard issue guide for new arrivals to the station.",
        "category": "Book",
        "attributes": {
            "content": WELCOME_GUIDE_CONTENT
        },
        "actions": ["examine", "read", "drop"]
    },
    "station_map": {
        "id": "station_map",
        "name": "Station Map",
        "description": "A basic layout map of the Space Station Explorer.",
        "category": "Book",
        "attributes": {
            "content": STATION_MAP_CONTENT
        },
        "actions": ["examine", "read", "drop"]
    },
    "maintenance_manual": {
        "id": "maintenance_manual",
        "name": "Maintenance Manual",
        "description": "A technical manual covering basic maintenance and emergency procedures.",
        "category": "Book",
        "attributes": {
            "content": MAINTENANCE_MANUAL_CONTENT
        },
        "actions": ["examine", "read", "drop"]
    },
    "engineering_manual": { # From random event
        "id": "engineering_manual",
        "name": "Engineering Manual",
        "description": "A technical guide for station engineers.",
        "category": "Book",
        "attributes": {
            "content": "ENGINEERING MANUAL抜粋\nChapter 1: Power Systems - Ensure plasma flow is optimal.\nChapter 2: Atmospherics - Check filters regularly.\nChapter 3: Emergency Repairs - Use welding tool for hull breaches."
        },
        "actions": ["examine", "read", "drop"]
    },
    "navigation_chart": { # From random event
        "id": "navigation_chart",
        "name": "Navigation Chart",
        "description": "A star chart showing nearby systems.",
        "category": "Book", # Or maybe Special?
        "attributes": {
            "content": "STAR CHART - Sector 7G\nKnown Systems: Sol, Alpha Centauri, Proxima Centauri\nNebulae: Eagle Nebula\nAnomalies: Unidentified signal source near Proxima Centauri b."
        },
        "actions": ["examine", "read", "drop"]
    },
    
    # --- Healing Items ---
    "medkit": { # From random event
        "id": "medkit",
        "name": "Medkit",
        "description": "A standard first aid kit.",
        "category": "Healing",
        "attributes": {
             "heal_effect": "heal_all_limbs_full" # Placeholder logic
        },
        "actions": ["examine", "use", "drop"]
    },
    "first_aid_kit": { # From locker (same as medkit? let's alias for now)
        "id": "first_aid_kit",
        "name": "First Aid Kit",
        "description": "Basic medical supplies for minor injuries.",
        "category": "Healing",
        "attributes": {
             "heal_effect": "heal_all_limbs_full" # Placeholder logic
        },
        "actions": ["examine", "use", "drop"]
    },
    "stabilizing_agent": { # From random event
        "id": "stabilizing_agent",
        "name": "Stabilizing Agent",
        "description": "A chemical agent used to stabilize volatile reactions or patients.",
        "category": "Healing", # Or chemical?
        "attributes": {
            "heal_effect": "reduce_damage_types" # Placeholder
        },
        "actions": ["examine", "use", "drop"]
    },
    "medical_scanner": { # From random event
        "id": "medical_scanner",
        "name": "Medical Scanner",
        "description": "A handheld device for diagnosing injuries and conditions.",
        "category": "Tool", # Medical Tool
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
     "medical_supply_kit": { # From random event
        "id": "medical_supply_kit",
        "name": "Medical Supply Kit",
        "description": "A kit containing various medical supplies.",
        "category": "Healing", 
        "attributes": {
            "contains": ["medkit", "stabilizing_agent"] # Example attribute
        },
        "actions": ["examine", "use", "drop"] # Use could unpack?
    },

    # --- Utility/Misc Items ---
    "energy_bar": { # From random event
        "id": "energy_bar",
        "name": "Energy Bar",
        "description": "A dense, nutrient-rich bar. Tastes like cardboard.",
        "category": "Food",
        "attributes": {
             "hunger_restore": 30
        },
        "actions": ["examine", "eat", "drop"]
    },
    "emergency_rations": { # From locker
        "id": "emergency_rations",
        "name": "Emergency Rations",
        "description": "Standard emergency food supply. Use only when necessary.",
        "category": "Food",
        "attributes": {
             "hunger_restore": 50
        },
        "actions": ["examine", "eat", "drop"]
    },
    "circuit_board": { # From random event
        "id": "circuit_board",
        "name": "Circuit Board",
        "description": "A standard electronic circuit board. Might be useful for repairs.",
        "category": "Component",
        "attributes": {},
        "actions": ["examine", "drop"]
    },
    "battery_pack": { # From random event
        "id": "battery_pack",
        "name": "Battery Pack",
        "description": "A replaceable power pack for various devices.",
        "category": "Component", # Or Utility?
        "attributes": {},
        "actions": ["examine", "use", "drop"] # Use could recharge something?
    },
    "power_cell": { # From random event
        "id": "power_cell",
        "name": "Power Cell",
        "description": "A standard power cell. Looks charged.",
        "category": "Component",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
     "id_card": { # From random event
        "id": "id_card",
        "name": "ID Card",
        "description": "A standard crew identification card. The name is smudged.",
        "category": "Special",
        "attributes": {},
        "actions": ["examine", "drop"]
    },
    "id_card_reader": { # From locker
        "id": "id_card_reader",
        "name": "ID Card Reader",
        "description": "Device to read and potentially modify crew ID cards.",
        "category": "Tool", # Security Tool
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "data_pad": { # From random event
        "id": "data_pad",
        "name": "Data Pad",
        "description": "A portable electronic data storage device.",
        "category": "Special",
        "attributes": {},
        "actions": ["examine", "use", "drop"] # Use could view data?
    },
    "oxygen_canister": { # From random event
        "id": "oxygen_canister",
        "name": "Oxygen Canister",
        "description": "A small canister of breathable oxygen.",
        "category": "Utility",
        "attributes": {},
        "actions": ["examine", "use", "drop"] # Use could refill suit/mask?
    },
     "radiation_badge": { # From random event
        "id": "radiation_badge",
        "name": "Radiation Badge",
        "description": "Measures cumulative radiation exposure.",
        "category": "Utility",
        "attributes": {},
        "actions": ["examine", "drop"]
    },
    "security_pass": { # From random event
        "id": "security_pass",
        "name": "Security Pass",
        "description": "A temporary security pass. Seems expired.",
        "category": "Special",
        "attributes": {},
        "actions": ["examine", "drop"]
    },
    "security_keycard": { # From random event
        "id": "security_keycard",
        "name": "Security Keycard",
        "description": "A keycard for accessing secure areas.",
        "category": "Special", # Or Key?
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "communication_device": { # From random event
        "id": "communication_device",
        "name": "Communication Device",
        "description": "A standard handheld communicator.",
        "category": "Utility",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "emergency_flare": { # From random event
        "id": "emergency_flare",
        "name": "Emergency Flare",
        "description": "A high-intensity flare for signaling.",
        "category": "Utility",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "encrypted_data_drive": { # From random event
        "id": "encrypted_data_drive",
        "name": "Encrypted Data Drive",
        "description": "A data drive protected by strong encryption.",
        "category": "Special",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
    "emergency_beacon": { # From locker
        "id": "emergency_beacon",
        "name": "Emergency Beacon",
        "description": "Distress signal device for emergencies. Transmits on standard frequencies.",
        "category": "Utility",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },

    # --- Junk Items (Example) ---
    # "used_power_cell": {
    #     "id": "used_power_cell",
    #     "name": "Used Power Cell",
    #     "description": "A depleted power cell. Likely useless.",
    #     "category": "Junk",
    #     "attributes": {},
    #     "actions": ["examine", "drop"]
    # },
}

# --- Helper Functions --- 
def get_item_definition(item_id):
    """Returns a copy of the item definition from the master dictionary."""
    if item_id in ALL_ITEMS:
        return ALL_ITEMS[item_id].copy() # Return a copy to prevent modification of the original
    return None

def get_items_by_category(category_name):
    """Returns a list of item definitions for a given category."""
    return [item.copy() for item in ALL_ITEMS.values() if item["category"] == category_name]


class ItemInventoryMixin:
    """Inventory UI and item action handlers. Requires host to provide root, player_data, and add_note()."""

    def show_inventory_popup(self):
        """Show a popup window with the player's inventory, using item dictionaries"""
        popup = tk.Toplevel(self.root)
        popup.title("Inventory")
        popup.geometry("400x500") # Made taller to accommodate the read button
        popup.configure(bg="black")

        # Ensure this window stays on top
        popup.transient(self.root)
        popup.grab_set()

        # Center the popup window
        popup.update_idletasks()
        width = 400
        height = 500
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        # Title
        title_label = tk.Label(popup, text="Inventory", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        # --- Listbox Frame ---
        # Create a frame for the scrollable inventory (packs before buttons)
        list_frame = tk.Frame(popup, bg="black")
        list_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        # Add scrollbar to list_frame
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a listbox for inventory items
        inventory_list = tk.Listbox(list_frame, bg="black", fg="white", font=("Arial", 12),
                                  width=30, height=15, yscrollcommand=scrollbar.set, exportselection=False)
        inventory_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=inventory_list.yview)

        # --- Populate Listbox ---
        # Add items to the listbox (storing inventory index)
        player_inventory = self.player_data.get('inventory', [])
        listbox_indices = {} # Map listbox index to player inventory index
        current_listbox_index = 0
        if not player_inventory:
            inventory_list.insert(tk.END, "Your inventory is empty.")
            inventory_list.itemconfig(tk.END, {'fg': "gray"})
        else:
            for inv_index, item in enumerate(player_inventory):
                if isinstance(item, dict) and 'name' in item:
                    inventory_list.insert(tk.END, item['name'])
                    listbox_indices[current_listbox_index] = inv_index # Store mapping
                    current_listbox_index += 1
                else:
                    # Handle potential old string-based inventory items (or errors)
                    inventory_list.insert(tk.END, str(item))
                    inventory_list.itemconfig(tk.END, {'fg': "red"})
                    listbox_indices[current_listbox_index] = inv_index # Still store index for dropping legacy items
                    current_listbox_index += 1

        # --- Button Frame (Packed at the bottom) ---
        button_frame = tk.Frame(popup, bg="black")
        button_frame.pack(pady=(5, 10), fill=tk.X, padx=20)
        button_frame.columnconfigure((0, 1, 2), weight=1) # 3 columns now

        # --- Action Buttons (Examine, Actions, Close) ---
        examine_btn = tk.Button(button_frame, text="Examine", font=("Arial", 12), width=10,
                            command=lambda: self.examine_item(inventory_list, popup),
                            state=tk.DISABLED)
        examine_btn.grid(row=0, column=0, padx=5, pady=5)

        actions_btn = tk.Button(button_frame, text="Actions", font=("Arial", 12), width=10,
                           command=lambda: self.show_item_actions_popup(inventory_list, popup),
                           state=tk.DISABLED)
        actions_btn.grid(row=0, column=1, padx=5, pady=5)

        # Close button
        close_btn = tk.Button(button_frame, text="Close", font=("Arial", 12), width=10, command=popup.destroy)
        close_btn.grid(row=0, column=2, padx=5, pady=5)

        # --- Check Selection Function (Updates Examine and Actions buttons) ---
        # Pass actions_btn as well
        def check_selection(event=None, ex_btn=examine_btn, act_btn=actions_btn):
            selection = inventory_list.curselection()
            if not selection:
                ex_btn.config(state=tk.DISABLED)
                act_btn.config(state=tk.DISABLED)
                return

            # Use local variables (ex_btn, act_btn) passed as arguments
            try:
                # Get item using helper (no index needed here, just check validity)
                item, item_inventory_index = self._get_selected_item_from_inventory(inventory_list)

                if item is None:
                    raise IndexError("Failed to get selected item")

                if isinstance(item, dict):
                    actions = item.get('actions', [])
                    # Examine is always possible for dict items
                    ex_btn.config(state=tk.NORMAL)
                    # Enable Actions button if there are actions OTHER than just 'examine'
                    other_actions = [a for a in actions if a != 'examine']
                    act_btn.config(state=tk.NORMAL if other_actions else tk.DISABLED)
                else:
                    # Legacy item or error
                    ex_btn.config(state=tk.DISABLED)
                    act_btn.config(state=tk.DISABLED)

            except (IndexError, ValueError, TypeError) as e:
                print(f"Error checking selection: {e}")
                ex_btn.config(state=tk.DISABLED)
                act_btn.config(state=tk.DISABLED)

        # Bind event
        inventory_list.bind('<<ListboxSelect>>', check_selection)
        # Call once initially, passing the buttons
        check_selection(ex_btn=examine_btn, act_btn=actions_btn)

        # --- Mouse wheel binding (Specific to listbox) ---
        def _on_inventory_mousewheel(event):
            try:
                inventory_list.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass
        inventory_list.bind("<MouseWheel>", _on_inventory_mousewheel)
        # No need to bind the frame if scrollbar is correctly linked to listbox

    def _get_selected_item_from_inventory(self, inventory_list):
        """Helper to get the selected item dictionary and its index from the inventory list."""
        selection = inventory_list.curselection()
        if not selection:
            return None, -1 # No selection

        selected_listbox_index = selection[0]

        # Re-scan inventory and listbox to find the matching index reliably after potential deletes
        current_player_inventory = self.player_data.get("inventory", [])
        listbox_item_count = inventory_list.size()
        valid_item_count = 0
        inventory_index_map = [] # List to store inventory indices corresponding to listbox entries

        for inv_idx, item in enumerate(current_player_inventory):
            if isinstance(item, dict) and 'name' in item:
                inventory_index_map.append(inv_idx)
                valid_item_count += 1
            elif isinstance(item, str): # Handle legacy strings
                inventory_index_map.append(inv_idx)
                valid_item_count += 1

        # Check consistency
        if valid_item_count != listbox_item_count and listbox_item_count > 0 and inventory_list.get(0) != "Your inventory is empty.":
            print("Warning: Listbox count doesn't match inventory item count.")

        if 0 <= selected_listbox_index < len(inventory_index_map):
            item_inventory_index = inventory_index_map[selected_listbox_index]
            if 0 <= item_inventory_index < len(current_player_inventory):
                return current_player_inventory[item_inventory_index], item_inventory_index
            else:
                print(f"Error: Mapped inventory index {item_inventory_index} out of bounds.")
                return None, -1
        else:
            print(f"Error: Selected listbox index {selected_listbox_index} out of bounds for map.")
            return None, -1

    def examine_item(self, inventory_list, parent_popup):
        """Show the description of the selected item."""
        item, item_inventory_index = self._get_selected_item_from_inventory(inventory_list)

        if not item:
            messagebox.showerror("Error", "Could not identify the selected item.", parent=parent_popup)
            return

        if not isinstance(item, dict):
            messagebox.showinfo("Cannot Examine", "This item cannot be examined properly.", parent=parent_popup)
            return

        item_name = item.get('name', 'Unknown Item')
        description = item.get('description', 'No description available.')

        self.add_note(f"Examined the {item_name}.")

        messagebox.showinfo(f"Examine: {item_name}", description, parent=parent_popup)

    def drop_item(self, inventory_list, parent_popup):
        """Remove the selected item from inventory."""
        item, item_inventory_index = self._get_selected_item_from_inventory(inventory_list)

        if item is None or item_inventory_index == -1:
             messagebox.showerror("Error", "Could not identify the selected item to drop.", parent=parent_popup)
             return

        can_drop = False
        item_name = str(item)
        if isinstance(item, dict):
            if 'drop' in item.get('actions', []):
                can_drop = True
                item_name = item.get('name', 'Unknown Item')
        else:
            can_drop = True

        if not can_drop:
            messagebox.showwarning("Cannot Drop", "This item cannot be dropped.", parent=parent_popup)
            return

        if not messagebox.askyesno("Confirm Drop",
                                f"Are you sure you want to drop the {item_name}? It will be gone forever!",
                                parent=parent_popup):
            return

        try:
            del self.player_data['inventory'][item_inventory_index]

            parent_popup.destroy()
            self.show_inventory_popup()

            self.add_note(f"Dropped the {item_name}.")

        except (IndexError, ValueError, TypeError) as e:
            print(f"Error dropping item: {e}")
            messagebox.showerror("Error", "Could not drop the selected item.", parent=parent_popup)

    def read_item(self, inventory_list, parent_popup):
        """Display the contents of a readable item (book, note, etc.)"""
        item, item_inventory_index = self._get_selected_item_from_inventory(inventory_list)

        if not item:
            messagebox.showerror("Error", "Could not identify the selected item.", parent=parent_popup)
            return

        if not isinstance(item, dict) or 'read' not in item.get('actions', []):
            messagebox.showwarning("Cannot Read", "This item cannot be read.", parent=parent_popup)
            return

        item_name = item.get('name', 'Readable Item')
        content = item.get('attributes', {}).get('content', '[No content found]')

        read_popup = tk.Toplevel(parent_popup)
        read_popup.title(f"Reading: {item_name}")
        read_popup.geometry("600x500")
        read_popup.configure(bg="black")
        read_popup.transient(parent_popup)
        read_popup.grab_set()

        title_label = tk.Label(read_popup, text=item_name, font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        content_frame = tk.Frame(read_popup, bg="black")
        content_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        content_scrollbar = tk.Scrollbar(content_frame)
        content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        content_text = tk.Text(content_frame, bg="black", fg="white", font=("Arial", 12),
                             wrap=tk.WORD, yscrollcommand=content_scrollbar.set)
        content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content_scrollbar.config(command=content_text.yview)

        content_text.insert(tk.END, content)
        content_text.config(state=tk.DISABLED)

        self.add_note(f"Read the {item_name}.")

        close_btn = tk.Button(read_popup, text="Close", font=("Arial", 12), width=10, command=read_popup.destroy)
        close_btn.pack(pady=10)

    def show_item_actions_popup(self, inventory_list, main_inventory_popup):
        """Shows a popup with available actions for the selected item."""
        item, item_inventory_index = self._get_selected_item_from_inventory(inventory_list)

        if not isinstance(item, dict):
            messagebox.showerror("Error", "Cannot perform actions on this item.", parent=main_inventory_popup)
            return

        item_name = item.get('name', 'Item')
        actions = item.get('actions', [])
        available_actions = [a for a in actions if a != 'examine']

        if not available_actions:
            messagebox.showinfo("No Actions", f"No special actions available for {item_name}.", parent=main_inventory_popup)
            return

        actions_popup = tk.Toplevel(main_inventory_popup)
        actions_popup.title(f"Actions: {item_name}")
        actions_popup.configure(bg="black")
        actions_popup.transient(main_inventory_popup)
        actions_popup.grab_set()

        action_frame = tk.Frame(actions_popup, bg="black", padx=15, pady=15)
        action_frame.pack(fill=tk.BOTH, expand=True)

        for action in available_actions:
            action_text = action.capitalize()
            callback = None

            if action == "read":
                callback = lambda i=item, p=actions_popup: self.read_item_action(i, p)
            elif action == "drop":
                callback = lambda idx=item_inventory_index, ap=actions_popup, mp=main_inventory_popup: self.drop_item_action(idx, ap, mp)
            else:
                callback = lambda a=action: messagebox.showinfo("WIP", f"Action '{a}' not yet implemented.", parent=actions_popup)

            if callback:
                btn = tk.Button(action_frame, text=action_text, font=("Arial", 12), width=15, command=callback)
                btn.pack(pady=5)

        cancel_btn = tk.Button(action_frame, text="Cancel", font=("Arial", 12), width=15, command=actions_popup.destroy)
        cancel_btn.pack(pady=(10,0))

        num_buttons = len(available_actions) + 1
        height = num_buttons * 45 + 40
        actions_popup.geometry(f"250x{height}")

    def read_item_action(self, item, actions_popup):
        """Action handler for reading an item. Displays content in a new window."""
        if not isinstance(item, dict) or 'read' not in item.get('actions', []):
            messagebox.showwarning("Cannot Read", "This item cannot be read.", parent=actions_popup)
            return

        item_name = item.get('name', 'Readable Item')
        content = item.get('attributes', {}).get('content', '[No content found]')

        read_content_popup = tk.Toplevel(actions_popup)
        read_content_popup.title(f"Reading: {item_name}")
        read_content_popup.geometry("600x500")
        read_content_popup.configure(bg="black")
        read_content_popup.transient(actions_popup)
        read_content_popup.grab_set()

        read_content_popup.update_idletasks()
        width = 600
        height = 500
        x = (read_content_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (read_content_popup.winfo_screenheight() // 2) - (height // 2)
        read_content_popup.geometry(f"{width}x{height}+{x}+{y}")

        title_label = tk.Label(read_content_popup, text=item_name, font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        content_frame = tk.Frame(read_content_popup, bg="black")
        content_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        content_scrollbar = tk.Scrollbar(content_frame)
        content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        content_text = tk.Text(content_frame, bg="black", fg="white", font=("Arial", 12),
                             wrap=tk.WORD, yscrollcommand=content_scrollbar.set)
        content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content_scrollbar.config(command=content_text.yview)

        content_text.insert(tk.END, content)
        content_text.config(state=tk.DISABLED)

        self.add_note(f"Read the {item_name}.")

        def _on_read_content_mousewheel(event):
            try:
                content_text.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass
        read_content_popup.bind("<MouseWheel>", _on_read_content_mousewheel)

        orig_destroy = read_content_popup.destroy
        def _destroy_and_cleanup_read():
            try:
                read_content_popup.unbind("<MouseWheel>")
            except tk.TclError:
                pass
            orig_destroy()
        read_content_popup.destroy = _destroy_and_cleanup_read

        close_read_btn = tk.Button(read_content_popup, text="Close", font=("Arial", 12), width=10, command=read_content_popup.destroy)
        close_read_btn.pack(pady=10)

    def drop_item_action(self, item_inventory_index, actions_popup, main_inventory_popup):
        """Action handler for dropping an item. Refreshes main inventory."""
        if not (0 <= item_inventory_index < len(self.player_data['inventory'])):
             messagebox.showerror("Error", "Invalid item index provided for drop action.", parent=actions_popup)
             return

        item = self.player_data['inventory'][item_inventory_index]
        item_name = item.get('name', str(item)) if isinstance(item, dict) else str(item)

        if not messagebox.askyesno("Confirm Drop",
                                f"Are you sure you want to drop the {item_name}? It will be gone forever!",
                                parent=actions_popup):
            return

        try:
            del self.player_data['inventory'][item_inventory_index]

            actions_popup.destroy()
            main_inventory_popup.destroy()
            self.show_inventory_popup()

            self.add_note(f"Dropped the {item_name}.")

        except (IndexError, ValueError, TypeError) as e:
            print(f"Error dropping item via action: {e}")
            messagebox.showerror("Error", "Could not drop the selected item.", parent=actions_popup)

    def use_item_action(self, item, index, actions_popup, main_inventory_popup):
         messagebox.showinfo("WIP", f"Action 'use' for {item.get('name', 'item')} not yet implemented.", parent=actions_popup)

    def eat_item_action(self, item, index, actions_popup, main_inventory_popup):
         messagebox.showinfo("WIP", f"Action 'eat' for {item.get('name', 'item')} not yet implemented.", parent=actions_popup)