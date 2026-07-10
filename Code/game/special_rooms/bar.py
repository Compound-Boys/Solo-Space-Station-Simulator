import tkinter as tk
from tkinter import messagebox
import random

from game.objects.drinks import DRINKS_MENU, MIXED_DRINKS, DrinkMixer, is_drink_alcoholic
from game.objects.items import add_to_inventory
from game.special_rooms.shared import (
    SpecialRoomBase,
    add_note,
    build_npc_contact_section,
    clear_button_frame,
)
from game.helper_methods.ui_panels import open_modal_panel, refocus_window
from game.maps.donut import BAR_KEY


class Bar(SpecialRoomBase):
    ROOM_TITLE = "Bar"
    ROOM_HEADING = "Station Bar"
    ROOM_DESCRIPTION = (
        "The station's bar is lively and well-furnished. A long counter runs along one wall, "
        "with shelves of drinks behind it. Tables and chairs are scattered about, and soft music "
        "plays in the background."
    )
    DOOR_KEY = BAR_KEY
    WINDOW_ATTR = "bar_window"

    def _after_open(self):
        self.bartender_mode = False
        self.drink_mixer = DrinkMixer(self.bar_window, self.player_data)

    def _before_leave(self):
        self.bartender_mode = False

    def _station_menu_before_show(self):
        return lambda: setattr(self, "bartender_mode", False)

    def station_entries(self):
        return [{
            "label": "Enter Bartender Station",
            "command": self.access_bartender_station,
        }]

    def show_room_options(self):
        clear_button_frame(self.button_frame)

        build_npc_contact_section(
            self.button_frame,
            self.player_data,
            self.station_crew,
            "Bartender",
            self.bar_window,
            talk_label="Order Drinks",
            talk_command=self.show_drink_menu,
            refresh_callback=self.show_room_options,
            absent_flavor="The bartender is away from the bar.",
        )

        socialize_btn = tk.Button(
            self.button_frame, text="Socialize", font=("Arial", 14), width=20, command=self.socialize
        )
        socialize_btn.pack(pady=10)

        self.pack_back_to_station_menu()

    def show_drink_menu(self):
        """Show the menu of available drinks"""
        _panel, menu_popup = open_modal_panel(self.bar_window, title="Drink Menu")
        title_label = tk.Label(menu_popup, text="Drink Menu", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        credits_label = tk.Label(
            menu_popup,
            text=f"Your credits: {self.player_data['credits']}",
            font=("Arial", 14),
            bg="black",
            fg="white",
        )
        credits_label.pack(pady=5)

        tab_frame = tk.Frame(menu_popup, bg="black")
        tab_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        tab_inner = tk.Frame(tab_frame, bg="black")
        tab_inner.pack(anchor=tk.CENTER)

        btn_frame = tk.Frame(menu_popup, bg="black")
        btn_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.X)
        btn_inner = tk.Frame(btn_frame, bg="black")
        btn_inner.pack(anchor=tk.CENTER)

        menu_frame = tk.Frame(menu_popup, bg="black")
        menu_frame.pack(padx=20, pady=10, anchor=tk.CENTER)

        scrollbar = tk.Scrollbar(menu_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        drink_listbox = tk.Listbox(
            menu_frame,
            bg="black",
            fg="white",
            font=("Arial", 12),
            width=25,
            height=22,
            yscrollcommand=scrollbar.set,
        )
        drink_listbox.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.config(command=drink_listbox.yview)

        desc_frame = tk.Frame(menu_popup, bg="black")
        desc_frame.pack(padx=20, pady=5, fill=tk.X)

        desc_label = tk.Label(
            desc_frame,
            text="Select a drink to see its description",
            font=("Arial", 12),
            bg="black",
            fg="white",
            wraplength=600,
        )
        desc_label.pack()

        stock = self.player_data.setdefault("bar_mixed_stock", {})
        basic_drinks = dict(DRINKS_MENU)
        mixed_drinks = {
            name: MIXED_DRINKS[name]
            for name, qty in stock.items()
            if qty > 0 and name in MIXED_DRINKS
        }
        all_drinks = {**basic_drinks, **mixed_drinks}

        alcoholic_drinks = {
            name: details for name, details in all_drinks.items()
            if is_drink_alcoholic(name, details)
        }
        non_alcoholic_drinks = {
            name: details for name, details in all_drinks.items()
            if not is_drink_alcoholic(name, details)
        }

        categories = {
            "All Drinks": all_drinks,
            "Basic Drinks": basic_drinks,
            "Mixed Drinks": mixed_drinks,
            "Alcoholic": alcoholic_drinks,
            "Non-Alcoholic": non_alcoholic_drinks,
        }

        current_category = {"drinks": all_drinks, "name": "All Drinks"}
        selected_drink = {"name": "", "details": None}

        def rebuild_categories():
            stock = self.player_data.setdefault("bar_mixed_stock", {})
            categories["Basic Drinks"] = dict(DRINKS_MENU)
            categories["Mixed Drinks"] = {
                name: MIXED_DRINKS[name]
                for name, qty in stock.items()
                if qty > 0 and name in MIXED_DRINKS
            }
            categories["All Drinks"] = {**categories["Basic Drinks"], **categories["Mixed Drinks"]}
            categories["Alcoholic"] = {
                name: details for name, details in categories["All Drinks"].items()
                if is_drink_alcoholic(name, details)
            }
            categories["Non-Alcoholic"] = {
                name: details for name, details in categories["All Drinks"].items()
                if not is_drink_alcoholic(name, details)
            }

        def show_category(category_name):
            rebuild_categories()
            category_drinks = categories[category_name]

            drink_listbox.delete(0, tk.END)

            current_category["drinks"] = category_drinks
            current_category["name"] = category_name

            drink_listbox.insert(tk.END, f"--- {category_name} ---")

            stock = self.player_data.setdefault("bar_mixed_stock", {})
            for drink, details in category_drinks.items():
                if drink in MIXED_DRINKS:
                    qty = stock.get(drink, 0)
                    drink_listbox.insert(
                        tk.END, f"{drink} (Qty: {qty}) - {details['price']} credits"
                    )
                else:
                    drink_listbox.insert(tk.END, f"{drink} - {details['price']} credits")

            desc_label.config(text="Select a drink to see its description")
            selected_drink["name"] = ""
            selected_drink["details"] = None

        def refresh_menu():
            show_category(current_category["name"])

        all_btn = tk.Button(
            tab_inner, text="All Drinks", font=("Arial", 12), width=12,
            command=lambda: show_category("All Drinks"),
        )
        all_btn.pack(side=tk.LEFT, padx=15)

        basic_btn = tk.Button(
            tab_inner, text="Basic Drinks", font=("Arial", 12), width=12,
            command=lambda: show_category("Basic Drinks"),
        )
        basic_btn.pack(side=tk.LEFT, padx=15)

        mixed_btn = tk.Button(
            tab_inner, text="Mixed Drinks", font=("Arial", 12), width=12,
            command=lambda: show_category("Mixed Drinks"),
        )
        mixed_btn.pack(side=tk.LEFT, padx=15)

        alcoholic_btn = tk.Button(
            tab_inner, text="Alcoholic", font=("Arial", 12), width=12,
            command=lambda: show_category("Alcoholic"),
        )
        alcoholic_btn.pack(side=tk.LEFT, padx=15)

        non_alcoholic_btn = tk.Button(
            tab_inner, text="Non-Alcoholic", font=("Arial", 12), width=12,
            command=lambda: show_category("Non-Alcoholic"),
        )
        non_alcoholic_btn.pack(side=tk.LEFT, padx=15)

        show_category("All Drinks")

        def on_select(event):
            selection = drink_listbox.curselection()
            if not selection or selection[0] == 0:
                return

            index = selection[0]
            entry = drink_listbox.get(index)

            if " - " in entry:
                drink_name = entry.split(" - ")[0]
                if " (Qty:" in drink_name:
                    drink_name = drink_name.split(" (Qty:")[0].strip()

                if drink_name in current_category["drinks"]:
                    drink_details = current_category["drinks"][drink_name]
                    desc_label.config(text=drink_details['desc'])

                    selected_drink["name"] = drink_name
                    selected_drink["details"] = drink_details

        drink_listbox.bind('<<ListboxSelect>>', on_select)

        order_btn = tk.Button(
            btn_inner,
            text="Order Selected Drink",
            font=("Arial", 12),
            command=lambda: self.order_drink_from_menu(
                selected_drink, menu_popup, credits_label, refresh_menu
            ),
        )
        order_btn.pack(side=tk.LEFT, padx=10)

        close_btn = tk.Button(
            btn_inner, text="Close Menu", font=("Arial", 12), command=menu_popup.destroy
        )
        close_btn.pack(side=tk.LEFT, padx=10)

    def order_drink_from_menu(self, selected_drink, popup, credits_label, refresh_menu=None):
        """Process an order for a drink selected from the menu"""
        if not selected_drink["name"] or not selected_drink["details"]:
            tk.messagebox.showinfo("Selection Needed", "Please select a drink first", parent=popup)
            return

        drink_name = selected_drink["name"]
        drink_details = selected_drink["details"]

        if drink_name in MIXED_DRINKS:
            stock = self.player_data.setdefault("bar_mixed_stock", {})
            if stock.get(drink_name, 0) <= 0:
                tk.messagebox.showinfo(
                    "Out of Stock",
                    f"{drink_name} is not available. Mix one at the bartender station first.",
                    parent=popup,
                )
                return

        if self.player_data['credits'] < drink_details['price']:
            tk.messagebox.showinfo(
                "Insufficient Credits",
                f"You don't have enough credits to order {drink_name}.",
                parent=popup,
            )
            return

        if drink_name in MIXED_DRINKS:
            stock = self.player_data.setdefault("bar_mixed_stock", {})
            stock[drink_name] -= 1
            if stock[drink_name] <= 0:
                del stock[drink_name]

        self.player_data['credits'] -= drink_details['price']

        alcoholic = is_drink_alcoholic(drink_name, drink_details)
        drink_item = {
            "id": f"drink_{drink_name.lower().replace(' ', '_')}",
            "name": drink_name,
            "description": drink_details["desc"],
            "category": "Drink",
            "attributes": {
                "alcoholic": alcoholic,
                "alcohol_content": drink_details.get(
                    "alcohol_content",
                    2 if alcoholic else 0,
                ),
            },
            "actions": ["examine", "drink", "drop"],
        }
        add_to_inventory(self.player_data, drink_item)

        credits_label.config(text=f"Your credits: {self.player_data['credits']}")

        add_note(
            self.player_data,
            f"Purchased {drink_name} at the bar for {drink_details['price']} credits. Added to inventory.",
        )

        if refresh_menu:
            refresh_menu()

        tk.messagebox.showinfo(
            "Order Successful",
            f"You've ordered a {drink_name} for {drink_details['price']} credits. "
            f"It has been added to your inventory.",
            parent=popup,
        )

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

        conversation = random.choice(conversations)

        self.bar_window.after(
            10, lambda: tk.messagebox.showinfo("Socializing", conversation, parent=self.bar_window)
        )
        refocus_window(self.bar_window)

    def access_bartender_station(self):
        """Access the bartender station for mixing drinks"""
        clear_button_frame(self.button_frame)

        self.bartender_mode = True

        mix_btn = tk.Button(
            self.button_frame, text="Mix Drinks", font=("Arial", 14), width=20, command=self.show_drink_mixer
        )
        mix_btn.pack(pady=10)

        recipes_btn = tk.Button(
            self.button_frame, text="View Recipes", font=("Arial", 14), width=20, command=self.show_recipes
        )
        recipes_btn.pack(pady=10)

        serve_btn = tk.Button(
            self.button_frame,
            text="Serve Regular Drinks",
            font=("Arial", 14),
            width=20,
            command=self.show_drink_menu,
        )
        serve_btn.pack(pady=10)

        back_btn = tk.Button(
            self.button_frame,
            text="Back to Station Menu",
            font=("Arial", 14),
            width=20,
            command=self.show_station_menu,
        )
        back_btn.pack(pady=10)

    def show_drink_mixer(self):
        """Show interface for mixing custom drinks"""
        self.drink_mixer.show_mixer()

    def show_recipes(self):
        """Show a list of known drink recipes"""
        self.drink_mixer.show_recipes()
