# game/objects/items.py

import copy
import tkinter as tk
from tkinter import messagebox

from game.helper_methods.ui_panels import open_modal_panel
from game.maps.donut import render_map_text
from game.objects.food import FOOD_ITEMS

# Tool IDs that fit inside a Basic Tools set (one of each).
BASIC_TOOLKIT_TOOL_IDS = ("wrench", "screwdriver", "wirecutters")
NON_STACKABLE_ITEM_IDS = frozenset({"basic_tools"})
MEDKIT_DAMAGE_TYPES = (("burn", "Burn"), ("poison", "Poison"), ("oxygen", "Oxygen"))

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
        "description": "A set containing a small wrench, screwdriver, and wirecutters.",
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
    
    # --- Healing Items ---
    "medkit": { # From random event / locker
        "id": "medkit",
        "name": "Medkit",
        "description": "A standard first aid kit.",
        "category": "Healing",
        "attributes": {},
        "actions": ["examine", "use", "drop"]
    },
}

ALL_ITEMS.update(FOOD_ITEMS)

# --- Helper Functions ---
DEFAULT_LOCKER_ITEM_IDS = [
    "welcome_guide",
    "station_map",
    "emergency_rations",
    "basic_tools",
    "medkit",
]


def _default_basic_tools_contents():
    """Fresh copies of the tools that ship inside a Basic Tools set."""
    contents = []
    for tool_id in BASIC_TOOLKIT_TOOL_IDS:
        if tool_id in ALL_ITEMS:
            contents.append(copy.deepcopy(ALL_ITEMS[tool_id]))
    return contents


def get_item_definition(item_id):
    """Returns a deep copy of the item definition from the master dictionary."""
    if item_id not in ALL_ITEMS:
        return None
    item = copy.deepcopy(ALL_ITEMS[item_id])
    if item_id == "basic_tools":
        attrs = item.setdefault("attributes", {})
        if "contents" not in attrs:
            attrs["contents"] = _default_basic_tools_contents()
    return item


def item_quantity(item):
    """Return quantity for an inventory entry (missing quantity counts as 1)."""
    if not isinstance(item, dict):
        return 1
    qty = item.get("quantity", 1)
    try:
        qty = int(qty)
    except (TypeError, ValueError):
        qty = 1
    return max(1, qty)


def inventory_item_count(player_data):
    """Total number of items in inventory, summing stack quantities."""
    total = 0
    for item in player_data.get("inventory", []) or []:
        total += item_quantity(item)
    return total


def format_inventory_label(item):
    """Display name with optional ' x N' when stacked."""
    if isinstance(item, dict) and "name" in item:
        name = item["name"]
        qty = item_quantity(item)
        if qty > 1:
            return f"{name} x {qty}"
        return name
    return str(item)


def _is_non_stackable(item):
    """Container items must not stack — each has its own contents."""
    if not isinstance(item, dict):
        return False
    if item.get("id") in NON_STACKABLE_ITEM_IDS:
        return True
    attrs = item.get("attributes") or {}
    return "contents" in attrs


def add_to_inventory(player_data, item):
    """Add an item to inventory, stacking by id when possible.

    Returns the inventory entry that was updated or appended.
    """
    inventory = player_data.setdefault("inventory", [])
    if not isinstance(item, dict):
        return None

    item_copy = dict(item)
    if "attributes" in item and isinstance(item["attributes"], dict):
        item_copy["attributes"] = copy.deepcopy(item["attributes"])
    add_qty = item_quantity(item_copy)
    item_copy["quantity"] = add_qty
    item_id = item_copy.get("id")

    if item_id and not _is_non_stackable(item_copy):
        for existing in inventory:
            if isinstance(existing, dict) and existing.get("id") == item_id and not _is_non_stackable(existing):
                existing["quantity"] = item_quantity(existing) + add_qty
                return existing

    inventory.append(item_copy)
    return item_copy


def remove_one_from_inventory(player_data, index):
    """Remove one unit from inventory at index. Returns the removed unit dict or None."""
    inventory = player_data.get("inventory", [])
    if not (0 <= index < len(inventory)):
        return None

    entry = inventory[index]
    if not isinstance(entry, dict):
        return None

    qty = item_quantity(entry)
    if qty > 1:
        entry["quantity"] = qty - 1
        removed = dict(entry)
        removed["quantity"] = 1
        return removed

    return inventory.pop(index)


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
    """Return the player's persistent locker inventory."""
    return player_data["locker_inventory"]


class ItemInventoryMixin:
    """Inventory UI and item action handlers. Requires host to provide root, player_data, and add_note()."""

    def show_inventory_popup(self, on_close=None):
        """Show inventory as an in-main-window overlay."""
        if on_close is not None:
            self._inventory_on_close = on_close
        on_close_cb = getattr(self, "_inventory_on_close", None)

        panel, popup = open_modal_panel(
            self.root, title="Inventory", on_close=on_close_cb
        )

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
                    inventory_list.insert(tk.END, format_inventory_label(item))

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
        item, _ = self._get_selected_item_from_inventory(inventory_list)

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
            elif action == "eat":
                callback = lambda idx=item_inventory_index, i=item, ap=panel, mp=main_inventory_popup: self.eat_item_action(i, idx, ap, mp)
            elif action == "use":
                callback = lambda idx=item_inventory_index, i=item, ap=panel, mp=main_inventory_popup: self.use_item_action(i, idx, ap, mp)
            else:
                callback = lambda a=action: messagebox.showinfo("WIP", f"Action '{a}' not yet implemented.", parent=actions_popup)

            if callback:
                btn = tk.Button(action_frame, text=action_text, font=("Arial", 12), width=15, command=callback)
                btn.pack(pady=5)

        cancel_btn = tk.Button(action_frame, text="Cancel", font=("Arial", 12), width=15, command=panel.close)
        cancel_btn.pack(pady=(10,0))

    def use_item_action(self, item, item_inventory_index, actions_popup, main_inventory_popup):
        """Dispatch Use by item id (medkit heal, basic_tools container, else WIP)."""
        if not isinstance(item, dict) or "use" not in item.get("actions", []):
            messagebox.showwarning("Cannot Use", "This item cannot be used.", parent=actions_popup)
            return

        item_id = item.get("id")
        if item_id == "medkit":
            self._use_medkit(item_inventory_index, actions_popup, main_inventory_popup)
        elif item_id == "basic_tools":
            self._use_basic_tools(item, actions_popup, main_inventory_popup)
        else:
            messagebox.showinfo(
                "WIP",
                f"Action 'use' not yet implemented for {item.get('name', 'this item')}.",
                parent=actions_popup,
            )

    def _use_medkit(self, item_inventory_index, actions_popup, main_inventory_popup):
        """Heal injured limbs (+10%) and positive burn/poison/oxygen (-10%); consume on success."""
        if not (0 <= item_inventory_index < len(self.player_data.get("inventory", []))):
            messagebox.showerror("Error", "Invalid item index for medkit use.", parent=actions_popup)
            return

        limbs = self.player_data.setdefault("limbs", {})
        damage = self.player_data.setdefault("damage", {})

        injured_limbs = [limb for limb, health in limbs.items() if health < 100]
        injured_damage = [
            key for key, _label in MEDKIT_DAMAGE_TYPES if damage.get(key, 0) > 0
        ]

        if not injured_limbs and not injured_damage:
            messagebox.showinfo(
                "Medkit",
                "You are already at full health. The medkit is not needed.",
                parent=actions_popup,
            )
            return

        summary_lines = []
        for limb in injured_limbs:
            original = limbs[limb]
            limbs[limb] = min(100, original + 10)
            limb_name = limb.replace("_", " ").title()
            summary_lines.append(f"{limb_name}: {original}% → {limbs[limb]}%")

        for key, label in MEDKIT_DAMAGE_TYPES:
            if key not in injured_damage:
                continue
            original = damage.get(key, 0)
            damage[key] = max(0, original - 10)
            summary_lines.append(f"{label}: {original}% → {damage[key]}%")

        remove_one_from_inventory(self.player_data, item_inventory_index)

        if hasattr(actions_popup, "close"):
            actions_popup.close()
        else:
            actions_popup.destroy()
        if hasattr(main_inventory_popup, "close"):
            main_inventory_popup.close()
        else:
            main_inventory_popup.destroy()
        self.show_inventory_popup()

        report = "You use the medkit:\n\n" + "\n".join(summary_lines)
        self.add_note("Used a medkit.")
        messagebox.showinfo("Medkit", report, parent=self.root)

    def _ensure_basic_tools_contents(self, item):
        """Return the mutable contents list on a basic_tools inventory entry."""
        attrs = item.setdefault("attributes", {})
        if "contents" not in attrs or not isinstance(attrs["contents"], list):
            attrs["contents"] = _default_basic_tools_contents()
        return attrs["contents"]

    def _use_basic_tools(self, item, actions_popup, main_inventory_popup):
        """Open the Basic Tools contents panel (pull out / put back / close)."""
        if hasattr(actions_popup, "close"):
            actions_popup.close()
        else:
            actions_popup.destroy()

        self._show_basic_tools_panel(item, main_inventory_popup)

    def _show_basic_tools_panel(self, toolkit_item, main_inventory_popup):
        """UI for viewing and moving tools in/out of a Basic Tools set."""
        contents = self._ensure_basic_tools_contents(toolkit_item)

        panel, popup = open_modal_panel(self.root, title="Basic Tools")

        title_label = tk.Label(
            popup, text="Basic Tools", font=("Arial", 18), bg="black", fg="white"
        )
        title_label.pack(pady=10)

        hint = tk.Label(
            popup,
            text="Tools inside the set:",
            font=("Arial", 12),
            bg="black",
            fg="white",
        )
        hint.pack(pady=(0, 5))

        list_frame = tk.Frame(popup, bg="black")
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        contents_list = tk.Listbox(
            list_frame,
            bg="black",
            fg="white",
            font=("Arial", 12),
            width=36,
            height=10,
            yscrollcommand=scrollbar.set,
            exportselection=False,
        )
        contents_list.pack(side=tk.LEFT)
        scrollbar.config(command=contents_list.yview)
        list_frame.pack(padx=20, pady=5)

        def refresh_contents_list():
            contents_list.delete(0, tk.END)
            if not contents:
                contents_list.insert(tk.END, "(empty)")
                contents_list.itemconfig(tk.END, {"fg": "gray"})
            else:
                for tool in contents:
                    name = tool.get("name", tool.get("id", "Tool")) if isinstance(tool, dict) else str(tool)
                    contents_list.insert(tk.END, name)

        refresh_contents_list()

        button_frame = tk.Frame(popup, bg="black")
        button_frame.pack(pady=10)

        def pull_out():
            if not contents:
                messagebox.showinfo("Basic Tools", "The set is empty.", parent=popup)
                return
            selection = contents_list.curselection()
            if not selection or contents_list.get(0) == "(empty)":
                messagebox.showinfo("Basic Tools", "Select a tool to pull out.", parent=popup)
                return
            idx = selection[0]
            if not (0 <= idx < len(contents)):
                return
            tool = contents.pop(idx)
            add_to_inventory(self.player_data, tool)
            tool_name = tool.get("name", "tool") if isinstance(tool, dict) else str(tool)
            self.add_note(f"Pulled the {tool_name} out of the Basic Tools set.")
            refresh_contents_list()

        def put_back():
            self._show_put_back_tools_panel(contents, refresh_contents_list, popup)

        def close_box():
            panel.close()
            # Refresh inventory so pulled-out tools appear
            if hasattr(main_inventory_popup, "close"):
                main_inventory_popup.close()
            else:
                try:
                    main_inventory_popup.destroy()
                except tk.TclError:
                    pass
            self.show_inventory_popup()

        tk.Button(
            button_frame, text="Pull Out", font=("Arial", 12), width=12, command=pull_out
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            button_frame, text="Put Back", font=("Arial", 12), width=12, command=put_back
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            button_frame, text="Close", font=("Arial", 12), width=12, command=close_box
        ).pack(side=tk.LEFT, padx=5)

    def _show_put_back_tools_panel(self, contents, refresh_contents_list, parent_popup):
        """List inventory tools that can be returned to the Basic Tools set."""
        present_ids = {
            tool.get("id")
            for tool in contents
            if isinstance(tool, dict) and tool.get("id")
        }
        eligible = []
        inventory = self.player_data.get("inventory", [])
        for inv_idx, inv_item in enumerate(inventory):
            if not isinstance(inv_item, dict):
                continue
            item_id = inv_item.get("id")
            if item_id in BASIC_TOOLKIT_TOOL_IDS and item_id not in present_ids:
                eligible.append((inv_idx, inv_item))

        if not eligible:
            messagebox.showinfo(
                "Put Back",
                "No matching tools in your inventory to put back\n"
                "(or those slots are already filled).",
                parent=parent_popup,
            )
            return

        panel, popup = open_modal_panel(self.root, title="Put Back Tool")

        tk.Label(
            popup,
            text="Select a tool to put back:",
            font=("Arial", 14),
            bg="black",
            fg="white",
        ).pack(pady=10)

        list_frame = tk.Frame(popup, bg="black")
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tool_list = tk.Listbox(
            list_frame,
            bg="black",
            fg="white",
            font=("Arial", 12),
            width=36,
            height=8,
            yscrollcommand=scrollbar.set,
            exportselection=False,
        )
        tool_list.pack(side=tk.LEFT)
        scrollbar.config(command=tool_list.yview)
        list_frame.pack(padx=20, pady=5)

        for _inv_idx, inv_item in eligible:
            tool_list.insert(tk.END, format_inventory_label(inv_item))

        def confirm_put_back():
            selection = tool_list.curselection()
            if not selection:
                messagebox.showinfo("Put Back", "Select a tool first.", parent=popup)
                return
            chosen_idx = selection[0]
            if not (0 <= chosen_idx < len(eligible)):
                return
            inv_idx, inv_item = eligible[chosen_idx]
            # Re-validate slot still free and inventory index still valid
            present_now = {
                tool.get("id")
                for tool in contents
                if isinstance(tool, dict) and tool.get("id")
            }
            item_id = inv_item.get("id")
            if item_id in present_now:
                messagebox.showinfo(
                    "Put Back",
                    "That tool slot is already filled.",
                    parent=popup,
                )
                panel.close()
                return
            if not (0 <= inv_idx < len(self.player_data.get("inventory", []))):
                messagebox.showerror("Error", "Item no longer in inventory.", parent=popup)
                panel.close()
                return
            current = self.player_data["inventory"][inv_idx]
            if not isinstance(current, dict) or current.get("id") != item_id:
                messagebox.showerror("Error", "Inventory changed. Try again.", parent=popup)
                panel.close()
                return

            removed = remove_one_from_inventory(self.player_data, inv_idx)
            if removed is None:
                messagebox.showerror("Error", "Could not remove tool from inventory.", parent=popup)
                panel.close()
                return
            # Store a clean single tool dict in the box (no stack quantity)
            tool_entry = copy.deepcopy(removed) if isinstance(removed, dict) else removed
            if isinstance(tool_entry, dict):
                tool_entry.pop("quantity", None)
            contents.append(tool_entry)
            tool_name = tool_entry.get("name", "tool") if isinstance(tool_entry, dict) else str(tool_entry)
            self.add_note(f"Put the {tool_name} back into the Basic Tools set.")
            panel.close()
            refresh_contents_list()

        btn_frame = tk.Frame(popup, bg="black")
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame, text="Put Back", font=("Arial", 12), width=12, command=confirm_put_back
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame, text="Cancel", font=("Arial", 12), width=12, command=panel.close
        ).pack(side=tk.LEFT, padx=5)

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
        attributes = item.get('attributes', {})
        alcoholic = attributes.get('alcoholic', False)
        alcohol_content = attributes.get('alcohol_content', 2 if alcoholic else 0)

        try:
            remove_one_from_inventory(self.player_data, item_inventory_index)

            if alcoholic:
                self.player_data.setdefault("alcohol_percent", 0)
                self.player_data["alcohol_percent"] += alcohol_content

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

    def eat_item_action(self, item, item_inventory_index, actions_popup, main_inventory_popup):
        """Action handler for eating an item. Removes it from inventory."""
        if not isinstance(item, dict) or 'eat' not in item.get('actions', []):
            messagebox.showwarning("Cannot Eat", "This item cannot be eaten.", parent=actions_popup)
            return

        if not (0 <= item_inventory_index < len(self.player_data['inventory'])):
            messagebox.showerror("Error", "Invalid item index provided for eat action.", parent=actions_popup)
            return

        item_name = item.get('name', 'food')

        try:
            remove_one_from_inventory(self.player_data, item_inventory_index)

            if hasattr(actions_popup, 'close'):
                actions_popup.close()
            else:
                actions_popup.destroy()
            if hasattr(main_inventory_popup, 'close'):
                main_inventory_popup.close()
            else:
                main_inventory_popup.destroy()
            self.show_inventory_popup()

            self.add_note(f"Ate the {item_name}.")
            messagebox.showinfo("Eat", f"You eat the {item_name}.", parent=self.root)

        except (IndexError, ValueError, TypeError) as e:
            print(f"Error eating item via action: {e}")
            messagebox.showerror("Error", "Could not eat the selected item.", parent=actions_popup)

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
            remove_one_from_inventory(self.player_data, item_inventory_index)

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