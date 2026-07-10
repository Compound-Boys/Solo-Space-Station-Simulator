import tkinter as tk
from tkinter import messagebox

from game.helper_methods.game import Game
from game.helper_methods.ui_panels import open_modal_panel
from game.objects.items import (
    ItemInventoryMixin,
    add_to_inventory,
    ensure_locker_inventory,
    format_inventory_label,
    get_item_definition,
    remove_one_from_inventory,
)
from game.special_rooms.shared import (
    add_note,
    build_room_shell,
    leave_room,
    open_room_in_main_window,
    room_lighting_chrome,
    show_character_sheet,
)
from game.helper_methods.stock_market import StockMarket


class Quarters(ItemInventoryMixin):
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self.quarters_window = open_room_in_main_window(
            parent_window, "Your Quarters", player_data, station_crew, return_callback
        )
        self.root = self.quarters_window
        self._build_quarters_ui()

    def _build_quarters_ui(self):
        style, button_frame = build_room_shell(
            self.quarters_window,
            self.player_data,
            "Your Quarters",
            "A small living quarters with basic amenities.",
        )
        room_bg, room_fg = style["bg"], style["fg"]

        info_frame = tk.Frame(self.quarters_window, bg=room_bg)
        info_frame.pack(pady=10, before=button_frame)

        tk.Label(
            info_frame,
            text=f"Name: {self.player_data['name']}",
            font=("Arial", 12),
            bg=room_bg,
            fg=room_fg,
        ).pack(side=tk.LEFT, padx=20)

        tk.Label(
            info_frame,
            text=f"Job: {self.player_data['job']}",
            font=("Arial", 12),
            bg=room_bg,
            fg=room_fg,
        ).pack(side=tk.LEFT, padx=20)

        tk.Label(
            info_frame,
            text=f"Credits: {self.player_data['credits']:.2f}",
            font=("Arial", 12),
            bg=room_bg,
            fg=room_fg,
        ).pack(side=tk.LEFT, padx=20)

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

        save_frame = tk.Frame(self.quarters_window, bg=room_bg)
        save_frame.pack(pady=30)

        tk.Button(
            save_frame,
            text="Save and Exit",
            font=("Arial", 14),
            width=15,
            command=self.save_and_exit,
        ).pack()

    def reload(self):
        """Rebuild quarters chrome from current player_data."""
        for widget in list(self.quarters_window.winfo_children()):
            widget.destroy()
        style = room_lighting_chrome(self.player_data)
        self.quarters_window.configure(bg=style["bg"])
        self._build_quarters_ui()

    def add_note(self, text):
        add_note(self.player_data, text)

    def interact_with_bed(self):
        panel, save_window = open_modal_panel(self.quarters_window, title="Bed")

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
            command=lambda: self._save_game_and_close(panel),
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="No",
            font=("Arial", 12),
            command=panel.close,
        ).pack(side=tk.LEFT, padx=10)

    def _save_game_and_close(self, save_window):
        if Game.save_game(self.player_data):
            messagebox.showinfo(
                "Game Saved",
                "Your game has been saved successfully.",
                parent=self.quarters_window,
            )
        if hasattr(save_window, "close"):
            save_window.close()
        else:
            save_window.destroy()

    def show_storage(self):
        panel, storage_window = open_modal_panel(self.quarters_window, title="Storage Locker")
        # Keep a close handle for take/store refresh
        storage_window._panel = panel

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
                    name_text = format_inventory_label(item_def)
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
                    name_text = format_inventory_label(item_def)
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
            command=panel.close,
        ).pack(pady=20)

    def _close_storage_panel(self, storage_window):
        panel = getattr(storage_window, "_panel", None)
        if panel is not None:
            panel.close()
        else:
            storage_window.destroy()

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

        taken_item = locker_inventory.pop(locker_index)
        if isinstance(taken_item, dict):
            add_to_inventory(self.player_data, taken_item.copy())
        else:
            add_to_inventory(self.player_data, taken_item)

        note_text = f"Took {item_name}" + (f" ({item_id})" if item_id else "") + " from locker."
        add_note(self.player_data, note_text)
        self._close_storage_panel(storage_window)
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

        removed = remove_one_from_inventory(self.player_data, item_index)
        if removed is None:
            messagebox.showerror("Error", "Could not store the item.", parent=self.quarters_window)
            return

        if isinstance(removed, dict):
            locker_inventory.insert(0, removed.copy())
        else:
            locker_inventory.insert(0, removed)

        note_text = f"Stored {item_name}" + (f" ({item_id})" if item_id else "") + " in locker."
        add_note(self.player_data, note_text)

        self._close_storage_panel(storage_window)
        self.show_storage()

    def show_computer(self):
        panel, computer_window = open_modal_panel(self.quarters_window, title="Computer Terminal")
        computer_window._panel = panel

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
            command=panel.close,
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

        # Holdings are already on player_data; skip syncing onto serialized company dicts
        self.reload()

    def view_character_sheet(self):
        show_character_sheet(
            self.quarters_window,
            self.player_data,
            self.show_inventory_popup,
            on_close=self.reload,
        )

    def save_and_exit(self):
        self.player_data["_exit_to_menu"] = True
        self.on_closing()

    def on_closing(self):
        leave_room(self.return_callback, self.player_data, self.station_crew)
