# game/objects/items.py

import tkinter as tk
from tkinter import messagebox

from game.helper_methods.ui_panels import open_modal_panel
from game.maps.donut import render_map_text

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

# Generated from the map's own coordinate data (see game/maps/donut.py) so it
# always matches the actual station layout.
STATION_MAP_CONTENT = render_map_text()

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
}

# --- Helper Functions ---
DEFAULT_LOCKER_ITEM_IDS = [
    "welcome_guide",
    "flashlight",
    "station_map",
    "emergency_rations",
    "basic_tools",
    "id_card_reader",
    "portable_scanner",
    "maintenance_manual",
    "emergency_beacon",
    "first_aid_kit",
]


def get_item_definition(item_id):
    """Returns a copy of the item definition from the master dictionary."""
    if item_id in ALL_ITEMS:
        return ALL_ITEMS[item_id].copy() # Return a copy to prevent modification of the original
    return None


def build_default_locker_inventory(exclude_item_ids=None):
    """Return default locker item dicts, optionally skipping IDs already held."""
    exclude = exclude_item_ids or set()
    items = []
    for item_id in DEFAULT_LOCKER_ITEM_IDS:
        if item_id in exclude:
            continue
        item_def = get_item_definition(item_id)
        if item_def:
            items.append(item_def)
    return items


def ensure_locker_inventory(player_data):
    """Return persistent locker inventory, seeding once for older saves."""
    if "locker_inventory" in player_data and isinstance(player_data["locker_inventory"], list):
        return player_data["locker_inventory"]

    player_inventory_ids = {
        item.get("id")
        for item in player_data.get("inventory", [])
        if isinstance(item, dict) and item.get("id")
    }
    player_data["locker_inventory"] = build_default_locker_inventory(player_inventory_ids)
    return player_data["locker_inventory"]


class ItemInventoryMixin:
    """Inventory UI and item action handlers. Requires host to provide root, player_data, and add_note()."""

    def show_inventory_popup(self):
        """Show inventory as an in-main-window overlay."""
        panel, popup = open_modal_panel(self.root, title="Inventory")

        title_label = tk.Label(popup, text="Inventory", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        list_frame = tk.Frame(popup, bg="black")
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        inventory_list = tk.Listbox(list_frame, bg="black", fg="white", font=("Arial", 12),
                                  width=40, height=30, yscrollcommand=scrollbar.set, exportselection=False)
        inventory_list.pack(side=tk.LEFT)
        scrollbar.config(command=inventory_list.yview)

        player_inventory = self.player_data.get('inventory', [])
        if not player_inventory:
            inventory_list.insert(tk.END, "Your inventory is empty.")
            inventory_list.itemconfig(tk.END, {'fg': "gray"})
        else:
            for item in player_inventory:
                if isinstance(item, dict) and 'name' in item:
                    inventory_list.insert(tk.END, item['name'])
                else:
                    inventory_list.insert(tk.END, str(item))
                    inventory_list.itemconfig(tk.END, {'fg': "red"})

        # Build buttons before packing so the frame has a real height
        button_frame = tk.Frame(popup, bg="black")
        button_frame.columnconfigure((0, 1, 2), weight=1)

        examine_btn = tk.Button(button_frame, text="Examine", font=("Arial", 12), width=10,
                            command=lambda: self.examine_item(inventory_list, popup),
                            state=tk.DISABLED)
        examine_btn.grid(row=0, column=0, padx=5, pady=5)

        actions_btn = tk.Button(button_frame, text="Actions", font=("Arial", 12), width=10,
                           command=lambda: self.show_item_actions_popup(inventory_list, panel),
                           state=tk.DISABLED)
        actions_btn.grid(row=0, column=1, padx=5, pady=5)

        close_btn = tk.Button(button_frame, text="Close", font=("Arial", 12), width=10, command=panel.close)
        close_btn.grid(row=0, column=2, padx=5, pady=5)

        # Pack buttons at bottom first, then list at its fixed size (no expand)
        button_frame.pack(side=tk.BOTTOM, pady=(5, 10), fill=tk.X, padx=20)
        list_frame.pack(padx=20, pady=10)

        def check_selection(event=None, ex_btn=examine_btn, act_btn=actions_btn):
            selection = inventory_list.curselection()
            if not selection:
                ex_btn.config(state=tk.DISABLED)
                act_btn.config(state=tk.DISABLED)
                return

            try:
                item, item_inventory_index = self._get_selected_item_from_inventory(inventory_list)

                if item is None:
                    raise IndexError("Failed to get selected item")

                if isinstance(item, dict):
                    actions = item.get('actions', [])
                    ex_btn.config(state=tk.NORMAL)
                    other_actions = [a for a in actions if a != 'examine']
                    act_btn.config(state=tk.NORMAL if other_actions else tk.DISABLED)
                else:
                    ex_btn.config(state=tk.DISABLED)
                    act_btn.config(state=tk.DISABLED)

            except (IndexError, ValueError, TypeError) as e:
                print(f"Error checking selection: {e}")
                ex_btn.config(state=tk.DISABLED)
                act_btn.config(state=tk.DISABLED)

        inventory_list.bind('<<ListboxSelect>>', check_selection)
        check_selection(ex_btn=examine_btn, act_btn=actions_btn)

        def _on_inventory_mousewheel(event):
            try:
                inventory_list.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass
        inventory_list.bind("<MouseWheel>", _on_inventory_mousewheel)

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

    def show_item_actions_popup(self, inventory_list, main_inventory_popup):
        """Shows an overlay with available actions for the selected item."""
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

        panel, actions_popup = open_modal_panel(self.root, title=f"Actions: {item_name}")

        action_frame = tk.Frame(actions_popup, bg="black", padx=15, pady=15)
        action_frame.pack(fill=tk.BOTH, expand=True)

        for action in available_actions:
            action_text = action.capitalize()
            callback = None

            if action == "read":
                callback = lambda i=item, p=panel: self.read_item_action(i, p)
            elif action == "drop":
                callback = lambda idx=item_inventory_index, ap=panel, mp=main_inventory_popup: self.drop_item_action(idx, ap, mp)
            elif action == "drink":
                callback = lambda idx=item_inventory_index, i=item, ap=panel, mp=main_inventory_popup: self.drink_item_action(i, idx, ap, mp)
            else:
                callback = lambda a=action: messagebox.showinfo("WIP", f"Action '{a}' not yet implemented.", parent=actions_popup)

            if callback:
                btn = tk.Button(action_frame, text=action_text, font=("Arial", 12), width=15, command=callback)
                btn.pack(pady=5)

        cancel_btn = tk.Button(action_frame, text="Cancel", font=("Arial", 12), width=15, command=panel.close)
        cancel_btn.pack(pady=(10,0))

    def read_item_action(self, item, actions_popup):
        """Action handler for reading an item. Displays content in an overlay."""
        if not isinstance(item, dict) or 'read' not in item.get('actions', []):
            messagebox.showwarning("Cannot Read", "This item cannot be read.", parent=actions_popup)
            return

        item_name = item.get('name', 'Readable Item')
        content = item.get('attributes', {}).get('content', '[No content found]')
        is_map = item.get('id') == 'station_map'

        panel, read_content_popup = open_modal_panel(self.root, title=f"Reading: {item_name}")

        title_label = tk.Label(read_content_popup, text=item_name, font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        content_frame = tk.Frame(read_content_popup, bg="black")
        content_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        content_scrollbar = tk.Scrollbar(content_frame)
        content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        content_font = ("Courier New", 11) if is_map else ("Arial", 12)
        content_wrap = tk.NONE if is_map else tk.WORD
        content_text = tk.Text(content_frame, bg="black", fg="white", font=content_font,
                             wrap=content_wrap, yscrollcommand=content_scrollbar.set)
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

        def _close_read():
            try:
                read_content_popup.unbind("<MouseWheel>")
            except tk.TclError:
                pass
            panel.close()

        close_read_btn = tk.Button(read_content_popup, text="Close", font=("Arial", 12), width=10, command=_close_read)
        close_read_btn.pack(pady=10)

    def drink_item_action(self, item, item_inventory_index, actions_popup, main_inventory_popup):
        """Action handler for drinking an item. Removes it and may raise alcohol_percent."""
        if not isinstance(item, dict) or 'drink' not in item.get('actions', []):
            messagebox.showwarning("Cannot Drink", "This item cannot be drunk.", parent=actions_popup)
            return

        if not (0 <= item_inventory_index < len(self.player_data['inventory'])):
            messagebox.showerror("Error", "Invalid item index provided for drink action.", parent=actions_popup)
            return

        item_name = item.get('name', 'drink')
        alcoholic = item.get('attributes', {}).get('alcoholic', False)

        try:
            del self.player_data['inventory'][item_inventory_index]

            if alcoholic:
                self.player_data.setdefault("alcohol_percent", 0)
                self.player_data["alcohol_percent"] += 2

            if hasattr(actions_popup, 'close'):
                actions_popup.close()
            else:
                actions_popup.destroy()
            if hasattr(main_inventory_popup, 'close'):
                main_inventory_popup.close()
            else:
                main_inventory_popup.destroy()
            self.show_inventory_popup()

            if alcoholic:
                alc = self.player_data["alcohol_percent"]
                self.add_note(f"Drank the {item_name}. Alcohol is now {alc:.1f}%.")
                messagebox.showinfo(
                    "Drink",
                    f"You finish the {item_name}.\nAlcohol: {alc:.1f}%",
                    parent=self.root,
                )
            else:
                self.add_note(f"Drank the {item_name}.")
                messagebox.showinfo("Drink", f"You finish the {item_name}.", parent=self.root)

        except (IndexError, ValueError, TypeError) as e:
            print(f"Error drinking item via action: {e}")
            messagebox.showerror("Error", "Could not drink the selected item.", parent=actions_popup)

    def drop_item_action(self, item_inventory_index, actions_popup, main_inventory_popup):
        """Action handler for dropping an item. Refreshes main inventory."""
        if not (0 <= item_inventory_index < len(self.player_data['inventory'])):
             messagebox.showerror("Error", "Invalid item index provided for drop action.", parent=actions_popup)
             return

        item = self.player_data['inventory'][item_inventory_index]
        item_name = item.get('name', str(item)) if isinstance(item, dict) else str(item)

        if not messagebox.askyesno("Confirm Drop",
                                f"Are you sure you want to drop the {item_name}? It will be gone forever!",
                                parent=self.root):
            return

        try:
            del self.player_data['inventory'][item_inventory_index]

            if hasattr(actions_popup, 'close'):
                actions_popup.close()
            else:
                actions_popup.destroy()
            if hasattr(main_inventory_popup, 'close'):
                main_inventory_popup.close()
            else:
                main_inventory_popup.destroy()
            self.show_inventory_popup()

            self.add_note(f"Dropped the {item_name}.")

        except (IndexError, ValueError, TypeError) as e:
            print(f"Error dropping item via action: {e}")
            messagebox.showerror("Error", "Could not drop the selected item.", parent=actions_popup)