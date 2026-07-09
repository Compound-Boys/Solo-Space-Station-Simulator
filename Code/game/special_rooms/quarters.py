import datetime
import tkinter as tk
from tkinter import messagebox

from game.game import Game
from game.items import ItemInventoryMixin, get_item_definition
from game.special_rooms.shared import add_note, leave_room, open_room_in_main_window
from game.stock_market import StockMarket, sync_holdings_to_companies

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


class Quarters(ItemInventoryMixin):
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self.quarters_window = open_room_in_main_window(parent_window, "Your Quarters", self.on_closing)
        self.root = self.quarters_window

        room_label = tk.Label(
            self.quarters_window,
            text="Your Quarters",
            font=("Arial", 24),
            bg="black",
            fg="white",
        )
        room_label.pack(pady=30)

        desc_label = tk.Label(
            self.quarters_window,
            text="A small living quarters with basic amenities.",
            font=("Arial", 12),
            bg="black",
            fg="white",
            wraplength=600,
        )
        desc_label.pack(pady=10)

        info_frame = tk.Frame(self.quarters_window, bg="black")
        info_frame.pack(pady=10)

        tk.Label(
            info_frame,
            text=f"Name: {self.player_data['name']}",
            font=("Arial", 12),
            bg="black",
            fg="white",
        ).pack(side=tk.LEFT, padx=20)

        tk.Label(
            info_frame,
            text=f"Job: {self.player_data['job']}",
            font=("Arial", 12),
            bg="black",
            fg="white",
        ).pack(side=tk.LEFT, padx=20)

        tk.Label(
            info_frame,
            text=f"Credits: {self.player_data['credits']:.2f}",
            font=("Arial", 12),
            bg="black",
            fg="white",
        ).pack(side=tk.LEFT, padx=20)

        button_frame = tk.Frame(self.quarters_window, bg="black")
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="Bed",
            font=("Arial", 14),
            width=15,
            command=self.interact_with_bed,
        ).grid(row=0, column=0, padx=10, pady=10)

        tk.Button(
            button_frame,
            text="Storage Locker",
            font=("Arial", 14),
            width=15,
            command=self.show_storage,
        ).grid(row=0, column=1, padx=10, pady=10)

        tk.Button(
            button_frame,
            text="Computer",
            font=("Arial", 14),
            width=15,
            command=self.show_computer,
        ).grid(row=1, column=0, padx=10, pady=10)

        tk.Button(
            button_frame,
            text="Door",
            font=("Arial", 14),
            width=15,
            command=self.on_closing,
        ).grid(row=1, column=1, padx=10, pady=10)

        tk.Button(
            button_frame,
            text="Character Sheet",
            font=("Arial", 14),
            width=15,
            command=self.view_character_sheet,
        ).grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        save_frame = tk.Frame(self.quarters_window, bg="black")
        save_frame.pack(pady=30)

        tk.Button(
            save_frame,
            text="Save and Exit",
            font=("Arial", 14),
            width=15,
            command=self.save_and_exit,
        ).pack()

    def add_note(self, text):
        add_note(self.player_data, text)

    def interact_with_bed(self):
        save_window = tk.Toplevel(self.quarters_window)
        save_window.title("Bed")
        save_window.geometry("300x150")
        save_window.configure(bg="black")
        save_window.transient(self.quarters_window)
        save_window.grab_set()
        save_window.geometry(
            "+%d+%d"
            % (
                self.quarters_window.winfo_rootx() + 250,
                self.quarters_window.winfo_rooty() + 200,
            )
        )

        save_frame = tk.Frame(save_window, bg="black")
        save_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            save_frame,
            text="Would you like to save your game?",
            font=("Arial", 12),
            bg="black",
            fg="white",
        ).pack(pady=10)

        buttons_frame = tk.Frame(save_frame, bg="black")
        buttons_frame.pack(pady=10)

        tk.Button(
            buttons_frame,
            text="Yes",
            font=("Arial", 12),
            command=lambda: self._save_game_and_close(save_window),
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="No",
            font=("Arial", 12),
            command=save_window.destroy,
        ).pack(side=tk.LEFT, padx=10)

    def _save_game_and_close(self, save_window):
        if Game.save_game(self.player_data):
            messagebox.showinfo(
                "Game Saved",
                "Your game has been saved successfully.",
                parent=self.quarters_window,
            )
        save_window.destroy()

    def show_storage(self):
        storage_window = tk.Toplevel(self.quarters_window)
        storage_window.title("Storage Locker")
        storage_window.geometry("800x600")
        storage_window.configure(bg="black")
        storage_window.transient(self.quarters_window)
        storage_window.grab_set()

        storage_window.update_idletasks()
        width = 800
        height = 600
        x = (storage_window.winfo_screenwidth() // 2) - (width // 2)
        y = (storage_window.winfo_screenheight() // 2) - (height // 2)
        storage_window.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(
            storage_window,
            text="Storage Locker",
            font=("Arial", 24),
            bg="black",
            fg="white",
        ).pack(pady=20)

        main_container = tk.Frame(storage_window, bg="black")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        locker_frame = tk.LabelFrame(
            main_container,
            text="Locker Items",
            font=("Arial", 14),
            bg="black",
            fg="white",
            bd=2,
        )
        locker_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        inventory_frame = tk.LabelFrame(
            main_container,
            text="Your Inventory",
            font=("Arial", 14),
            bg="black",
            fg="white",
            bd=2,
        )
        inventory_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        locker_inventory = ensure_locker_inventory(self.player_data)

        locker_canvas = tk.Canvas(locker_frame, bg="black", highlightthickness=0)
        locker_scrollbar = tk.Scrollbar(locker_frame, orient="vertical", command=locker_canvas.yview)
        locker_canvas.configure(yscrollcommand=locker_scrollbar.set)
        locker_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        locker_items_frame = tk.Frame(locker_canvas, bg="black")
        locker_canvas.create_window((0, 0), window=locker_items_frame, anchor="nw")

        if not locker_inventory:
            tk.Label(
                locker_items_frame,
                text="The storage locker is empty.",
                font=("Arial", 12),
                bg="black",
                fg="white",
            ).pack(pady=10, padx=10, anchor="w")
        else:
            for locker_index, item_def in enumerate(locker_inventory):
                item_frame = tk.Frame(
                    locker_items_frame,
                    bg="dark gray",
                    bd=2,
                    relief=tk.RAISED,
                    width=300,
                )
                item_frame.pack(fill=tk.X, pady=5, padx=5)

                info_frame = tk.Frame(item_frame, bg="dark gray")
                info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor="w")

                name_text = str(item_def)
                description = ""
                if isinstance(item_def, dict):
                    name_text = item_def.get("name", "Unknown Item")
                    description = item_def.get("description", "")

                tk.Label(
                    info_frame,
                    text=name_text,
                    font=("Arial", 12, "bold"),
                    bg="dark gray",
                ).pack(anchor="w", padx=10, pady=(5, 0))

                tk.Label(
                    info_frame,
                    text=description,
                    font=("Arial", 10),
                    bg="dark gray",
                    wraplength=200,
                ).pack(anchor="w", padx=10, pady=(0, 5))

                button_frame = tk.Frame(item_frame, bg="dark gray")
                button_frame.pack(side=tk.RIGHT, padx=10, pady=5)

                tk.Button(
                    button_frame,
                    text="Take",
                    font=("Arial", 10),
                    command=lambda index=locker_index, sw=storage_window: self._take_item(
                        index, sw
                    ),
                ).pack()

        inventory_canvas = tk.Canvas(inventory_frame, bg="black", highlightthickness=0)
        inventory_scrollbar = tk.Scrollbar(
            inventory_frame, orient="vertical", command=inventory_canvas.yview
        )
        inventory_canvas.configure(yscrollcommand=inventory_scrollbar.set)
        inventory_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inventory_items_frame = tk.Frame(inventory_canvas, bg="black")
        inventory_canvas.create_window((0, 0), window=inventory_items_frame, anchor="nw")

        player_inventory = self.player_data.get("inventory", [])
        if not player_inventory:
            tk.Label(
                inventory_items_frame,
                text="Your inventory is empty.",
                font=("Arial", 12),
                bg="black",
                fg="white",
            ).pack(pady=10, padx=10, anchor="w")
        else:
            for i, item_def in enumerate(player_inventory):
                item_frame = tk.Frame(
                    inventory_items_frame,
                    bg="dark gray",
                    bd=2,
                    relief=tk.RAISED,
                    width=300,
                )
                item_frame.pack(fill=tk.X, pady=5, padx=5)

                name_text = str(item_def)
                item_color = "red"
                if isinstance(item_def, dict) and "name" in item_def:
                    name_text = item_def["name"]
                    item_color = "white"

                tk.Label(
                    item_frame,
                    text=name_text,
                    font=("Arial", 12, "bold"),
                    bg="dark gray",
                    fg=item_color,
                ).pack(side=tk.LEFT, padx=10, pady=5, anchor="w")

                tk.Button(
                    item_frame,
                    text="Store in Locker",
                    font=("Arial", 10),
                    command=lambda index=i, sw=storage_window: self._store_item(index, sw),
                ).pack(side=tk.RIGHT, padx=10, pady=5)

        def configure_scroll(canvas, scrollbar, items_frame):
            canvas.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))
            if items_frame.winfo_reqheight() > canvas.winfo_reqheight():
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            else:
                scrollbar.pack_forget()

        configure_scroll(locker_canvas, locker_scrollbar, locker_items_frame)
        configure_scroll(inventory_canvas, inventory_scrollbar, inventory_items_frame)

        def _on_locker_mousewheel(event):
            locker_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_inventory_mousewheel(event):
            inventory_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        locker_canvas.bind("<MouseWheel>", _on_locker_mousewheel)
        locker_items_frame.bind("<MouseWheel>", _on_locker_mousewheel)
        inventory_canvas.bind("<MouseWheel>", _on_inventory_mousewheel)
        inventory_items_frame.bind("<MouseWheel>", _on_inventory_mousewheel)

        tk.Button(
            storage_window,
            text="Close",
            font=("Arial", 14),
            width=15,
            command=storage_window.destroy,
        ).pack(pady=20)

    def _take_item(self, locker_index, storage_window):
        locker_inventory = ensure_locker_inventory(self.player_data)

        if not (0 <= locker_index < len(locker_inventory)):
            messagebox.showerror("Error", "Invalid locker item.", parent=self.quarters_window)
            return

        item_def = locker_inventory[locker_index]
        item_name = str(item_def)
        item_id = None
        if isinstance(item_def, dict):
            item_name = item_def.get("name", "Unknown Item")
            item_id = item_def.get("id")

        player_inventory = self.player_data.setdefault("inventory", [])
        if item_id:
            has_item = any(
                isinstance(inv_item, dict) and inv_item.get("id") == item_id
                for inv_item in player_inventory
            )
            if has_item:
                messagebox.showinfo(
                    "Already Have It",
                    f"You already have a {item_name}.",
                    parent=self.quarters_window,
                )
                return

        taken_item = locker_inventory.pop(locker_index)
        if isinstance(taken_item, dict):
            player_inventory.append(taken_item.copy())
        else:
            player_inventory.append(taken_item)

        messagebox.showinfo(
            "Item Taken",
            f"You took the {item_name}.",
            parent=self.quarters_window,
        )
        note_text = f"Took {item_name}" + (f" ({item_id})" if item_id else "") + " from locker."
        add_note(self.player_data, note_text)
        storage_window.destroy()
        self.show_storage()

    def _store_item(self, item_index, storage_window):
        player_inventory = self.player_data.get("inventory", [])
        locker_inventory = ensure_locker_inventory(self.player_data)

        if not (0 <= item_index < len(player_inventory)):
            messagebox.showerror("Error", "Invalid item index.", parent=self.quarters_window)
            return

        item_to_store = player_inventory[item_index]
        item_name = str(item_to_store)
        item_id = None
        if isinstance(item_to_store, dict):
            item_name = item_to_store.get("name", "Unknown Item")
            item_id = item_to_store.get("id")

        del player_inventory[item_index]
        if isinstance(item_to_store, dict):
            locker_inventory.append(item_to_store.copy())
        else:
            locker_inventory.append(item_to_store)

        messagebox.showinfo(
            "Item Stored",
            f"You placed the {item_name} in the storage locker.",
            parent=self.quarters_window,
        )

        note_text = f"Stored {item_name}" + (f" ({item_id})" if item_id else "") + " in locker."
        add_note(self.player_data, note_text)

        storage_window.destroy()
        self.show_storage()

    def show_computer(self):
        computer_window = tk.Toplevel(self.quarters_window)
        computer_window.title("Computer Terminal")
        computer_window.geometry("400x300")
        computer_window.configure(bg="black")
        computer_window.transient(self.quarters_window)
        computer_window.grab_set()

        computer_window.update_idletasks()
        width = 400
        height = 300
        x = (computer_window.winfo_screenwidth() // 2) - (width // 2)
        y = (computer_window.winfo_screenheight() // 2) - (height // 2)
        computer_window.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(
            computer_window,
            text="Computer Terminal",
            font=("Arial", 24),
            bg="black",
            fg="white",
        ).pack(pady=30)

        options_frame = tk.Frame(computer_window, bg="black")
        options_frame.pack(pady=20)

        tk.Button(
            options_frame,
            text="Stock Market",
            font=("Arial", 14),
            width=15,
            command=lambda: self._open_stock_market(computer_window),
        ).pack(pady=10)

        tk.Button(
            options_frame,
            text="Turn Off Computer",
            font=("Arial", 14),
            width=15,
            command=computer_window.destroy,
        ).pack(pady=10)

    def _open_stock_market(self, computer_window):
        market_data = self.player_data.get("stock_market", {})
        companies = market_data.get("companies", [])
        cycle_number = market_data.get("cycle_number", 1)
        day_number = market_data.get("day_number", 1)

        StockMarket(
            self.quarters_window,
            self.player_data,
            companies,
            cycle_number,
            day_number,
            lambda updated_data: self._stock_market_return(updated_data, computer_window),
        )

    def _stock_market_return(self, updated_data, computer_window):
        if "stock_transactions" in updated_data:
            transactions = updated_data.pop("stock_transactions")
            for transaction in transactions:
                if transaction["type"] == "buy":
                    add_note(
                        self.player_data,
                        f"Bought {transaction['shares']} shares of {transaction['company']} "
                        f"at {transaction['price']:.2f} cr/share (Total: {transaction['total']:.2f} cr)",
                    )
                elif transaction["type"] == "sell":
                    profit = transaction.get("profit", 0)
                    if profit != 0:
                        profit_text = (
                            f" (Profit: {profit:.2f} cr)"
                            if profit > 0
                            else f" (Loss: {abs(profit):.2f} cr)"
                        )
                    else:
                        profit_text = ""
                    add_note(
                        self.player_data,
                        f"Sold {transaction['shares']} shares of {transaction['company']} "
                        f"at {transaction['price']:.2f} cr/share (Total: {transaction['total']:.2f} cr){profit_text}",
                    )

        self.player_data = updated_data

        if "stock_holdings" in updated_data:
            companies = self.player_data.get("stock_market", {}).get("companies", [])
            sync_holdings_to_companies(companies, updated_data["stock_holdings"])

        if computer_window.winfo_exists():
            computer_window.lift()

    def view_character_sheet(self):
        sheet_window = tk.Toplevel(self.quarters_window)
        sheet_window.title("Character Sheet")
        sheet_window.geometry("800x700")
        sheet_window.configure(bg="black")
        sheet_window.transient(self.quarters_window)
        sheet_window.grab_set()

        sheet_window.update_idletasks()
        width = 800
        height = 700
        x = (sheet_window.winfo_screenwidth() // 2) - (width // 2)
        y = (sheet_window.winfo_screenheight() // 2) - (height // 2)
        sheet_window.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(
            sheet_window,
            text="Character Sheet",
            font=("Arial", 24),
            bg="black",
            fg="white",
        ).pack(pady=20)

        info_frame = tk.Frame(sheet_window, bg="black")
        info_frame.pack(pady=10)

        tk.Label(
            info_frame,
            text=f"Name: {self.player_data['name']}",
            font=("Arial", 14),
            bg="black",
            fg="white",
        ).pack(anchor="w", padx=10, pady=5)

        tk.Label(
            info_frame,
            text=f"Job: {self.player_data['job']}",
            font=("Arial", 14),
            bg="black",
            fg="white",
        ).pack(anchor="w", padx=10, pady=5)

        department = self.player_data.get("department", "Unknown")
        tk.Label(
            info_frame,
            text=f"Department: {department}",
            font=("Arial", 14),
            bg="black",
            fg="white",
        ).pack(anchor="w", padx=10, pady=5)

        tk.Label(
            info_frame,
            text=f"Credits: {self.player_data['credits']:.2f}",
            font=("Arial", 14),
            bg="black",
            fg="white",
        ).pack(anchor="w", padx=10, pady=5)

        button_frame = tk.Frame(info_frame, bg="black")
        button_frame.pack(anchor="w", padx=10, pady=5, fill=tk.X)

        inv_count = len(self.player_data.get("inventory", []))
        tk.Button(
            button_frame,
            text=f"View Inventory ({inv_count} items)",
            font=("Arial", 12),
            width=20,
            command=self.show_inventory_popup,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        holdings_count = len(self.player_data.get("stock_holdings", {}))
        tk.Button(
            button_frame,
            text=f"View Stock Holdings ({holdings_count})",
            font=("Arial", 12),
            width=20,
            command=self.show_holdings_popup,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        notes_count = len(self.player_data.get("notes", []))
        tk.Button(
            button_frame,
            text=f"View Notes ({notes_count})",
            font=("Arial", 12),
            width=15,
            command=self._show_notes_popup,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        tk.Label(
            info_frame,
            text="Overall Damage:",
            font=("Arial", 14),
            bg="black",
            fg="white",
        ).pack(anchor="w", padx=10, pady=5)

        damage_frame = tk.Frame(info_frame, bg="black")
        damage_frame.pack(fill=tk.X, padx=20, pady=5)

        damage_types = [
            {"name": "Burn", "key": "burn", "icon": "Fire"},
            {"name": "Poison", "key": "poison", "icon": "Toxin"},
            {"name": "Oxygen", "key": "oxygen", "icon": "Air"},
        ]

        for damage_type in damage_types:
            damage_value = self.player_data["damage"].get(damage_type["key"], 0)
            color = (
                "green"
                if damage_value < 10
                else "yellow"
                if damage_value < 30
                else "orange"
                if damage_value < 60
                else "red"
            )

            type_frame = tk.Frame(damage_frame, bg="black")
            type_frame.pack(anchor="w", fill=tk.X, pady=2)

            tk.Label(
                type_frame,
                text=f"{damage_type['icon']} {damage_type['name']}: ",
                font=("Arial", 12),
                bg="black",
                fg="white",
            ).pack(side=tk.LEFT, padx=5)

            tk.Label(
                type_frame,
                text=f"{damage_value:.1f}%",
                font=("Arial", 12),
                bg="black",
                fg=color,
            ).pack(side=tk.LEFT)

        tk.Label(
            info_frame,
            text="Limb Health (Blunt Damage):",
            font=("Arial", 14),
            bg="black",
            fg="white",
        ).pack(anchor="w", padx=10, pady=5)

        limb_frame = tk.Frame(info_frame, bg="black")
        limb_frame.pack(fill=tk.X, padx=20, pady=5)

        limb_order = ["head", "chest", "left_arm", "right_arm", "left_leg", "right_leg"]
        for limb_name in limb_order:
            if limb_name in self.player_data["limbs"]:
                health = self.player_data["limbs"][limb_name]
                display_name = limb_name.replace("_", " ").title()
                color = "green" if health > 75 else "yellow" if health > 40 else "red"
                tk.Label(
                    limb_frame,
                    text=f"{display_name}: {health}%",
                    font=("Arial", 12),
                    bg="black",
                    fg=color,
                ).pack(anchor="w", pady=2)

        limb_health = sum(self.player_data["limbs"].values()) / len(self.player_data["limbs"])
        damage_health = 100 - (
            sum(self.player_data["damage"].values()) / len(self.player_data["damage"])
        )
        overall_health = (limb_health + damage_health) / 2
        overall_color = (
            "green" if overall_health > 75 else "yellow" if overall_health > 40 else "red"
        )

        tk.Label(
            info_frame,
            text="Overall Health:",
            font=("Arial", 14),
            bg="black",
            fg="white",
        ).pack(anchor="w", padx=10, pady=5)

        tk.Label(
            info_frame,
            text=f"{overall_health:.1f}%",
            font=("Arial", 16, "bold"),
            bg="black",
            fg=overall_color,
        ).pack(anchor="w", padx=10, pady=5)

        tk.Button(
            sheet_window,
            text="Close",
            font=("Arial", 14),
            width=15,
            command=sheet_window.destroy,
        ).pack(pady=30)

    def show_holdings_popup(self):
        popup = tk.Toplevel(self.quarters_window)
        popup.title("Stock Holdings")
        popup.geometry("400x400")
        popup.configure(bg="black")
        popup.transient(self.quarters_window)
        popup.grab_set()

        popup.update_idletasks()
        width = 400
        height = 400
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(
            popup,
            text="Stock Holdings",
            font=("Arial", 18),
            bg="black",
            fg="white",
        ).pack(pady=10)

        frame = tk.Frame(popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        holdings_list = tk.Listbox(
            frame,
            bg="black",
            fg="white",
            font=("Arial", 12),
            width=30,
            height=15,
            yscrollcommand=scrollbar.set,
        )
        holdings_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=holdings_list.yview)

        if not self.player_data.get("stock_holdings", {}):
            holdings_list.insert(tk.END, "You don't own any company stocks.")
        else:
            for company, shares in self.player_data["stock_holdings"].items():
                holdings_list.insert(tk.END, f"{company}: {shares} shares")

        tk.Button(
            popup,
            text="Close",
            font=("Arial", 12),
            width=10,
            command=popup.destroy,
        ).pack(pady=10)

    def _show_notes_popup(self):
        popup = tk.Toplevel(self.quarters_window)
        popup.title("Character Notes")
        popup.geometry("600x500")
        popup.configure(bg="black")
        popup.transient(self.quarters_window)
        popup.grab_set()

        popup.update_idletasks()
        width = 600
        height = 500
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(
            popup,
            text="Character Notes",
            font=("Arial", 18),
            bg="black",
            fg="white",
        ).pack(pady=10)

        frame = tk.Frame(popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        notes_text = tk.Text(
            frame,
            bg="black",
            fg="white",
            font=("Arial", 12),
            width=60,
            height=20,
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD,
        )
        notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=notes_text.yview)
        notes_text.config(state=tk.DISABLED)

        if self.player_data.get("notes"):
            notes_text.config(state=tk.NORMAL)
            for note in reversed(self.player_data["notes"]):
                if "timestamp" in note and "text" in note:
                    try:
                        dt = datetime.datetime.fromisoformat(note["timestamp"])
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        formatted_time = note["timestamp"]
                    notes_text.insert(tk.END, f"{formatted_time}:\n{note['text']}\n\n")
                else:
                    notes_text.insert(tk.END, f"{str(note)}\n\n")
            notes_text.config(state=tk.DISABLED)
        else:
            notes_text.config(state=tk.NORMAL)
            notes_text.insert(tk.END, "No notes recorded yet.")
            notes_text.config(state=tk.DISABLED)

        tk.Button(
            popup,
            text="Close",
            font=("Arial", 12),
            width=10,
            command=popup.destroy,
        ).pack(pady=10)

    def save_and_exit(self):
        self.player_data["_exit_to_menu"] = True
        self.on_closing()

    def on_closing(self):
        leave_room(self.return_callback, self.player_data, self.station_crew)
