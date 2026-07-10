"""Drink definitions and bartender drink-mixing UI."""

import datetime
import tkinter as tk

from game.helper_methods.ui_panels import open_modal_panel

DRINKS_MENU = {
    "Beer": {"price": 10, "alcohol_content": 1, "desc": "A refreshing glass of regular beer."},
    "Whiskey": {"price": 20, "alcohol_content": 2, "desc": "A shot of strong whiskey."},
    "Wine": {"price": 15, "alcohol_content": 2, "desc": "A fine glass of red wine."},
    "Vodka": {"price": 15, "alcohol_content": 2, "desc": "A shot of clear, strong vodka."},
    "Gin": {"price": 15, "alcohol_content": 2, "desc": "A botanical spirit with a distinctive flavor."},
    "Rum": {"price": 15, "alcohol_content": 2, "desc": "A sweet spirit distilled from sugarcane."},
    "Tequila": {"price": 18, "alcohol_content": 2, "desc": "A spirit made from the blue agave plant."},
    "Brandy": {"price": 22, "alcohol_content": 2, "desc": "A spirit distilled from wine or fermented fruit juice."},
    "Scotch": {"price": 25, "alcohol_content": 2, "desc": "A smoky whisky from Scotland."},
    "Orange Juice": {"price": 5, "desc": "A glass of fresh orange juice."},
    "Cranberry Juice": {"price": 5, "desc": "Tart and refreshing red juice."},
    "Pineapple Juice": {"price": 6, "desc": "Sweet tropical juice."},
    "Tonic Water": {"price": 4, "desc": "Carbonated water with quinine."},
    "Soda Water": {"price": 3, "desc": "Simple carbonated water."},
    "Cola": {"price": 4, "desc": "A sweet carbonated soft drink."},
    "Lemon Juice": {"price": 4, "desc": "Fresh, sour citrus juice."},
    "Lime Juice": {"price": 4, "desc": "Zesty green citrus juice."},
    "Grenadine": {"price": 5, "desc": "Sweet red syrup made from pomegranate."},
    "Water": {"price": 1, "desc": "A glass of water. Refreshing and healthy."},
}

MIXED_DRINKS = {
    "Screwdriver": {
        "ingredients": ["Vodka", "Orange Juice"],
        "price": 25,
        "alcohol_content": 2,
        "desc": "A classic mix of vodka and orange juice.",
    },
    "Gin and Tonic": {
        "ingredients": ["Gin", "Tonic Water"],
        "price": 20,
        "alcohol_content": 2,
        "desc": "A refreshing mix of gin and tonic water.",
    },
    "Rum and Cola": {
        "ingredients": ["Rum", "Cola"],
        "price": 20,
        "alcohol_content": 2,
        "desc": "A sweet mix of rum and cola.",
    },
    "Whiskey Sour": {
        "ingredients": ["Whiskey", "Lemon Juice", "Sugar"],
        "price": 28,
        "alcohol_content": 2,
        "desc": "A perfect balance of sour and sweet with whiskey.",
    },
    "Margarita": {
        "ingredients": ["Tequila", "Lime Juice", "Triple Sec"],
        "price": 30,
        "alcohol_content": 2,
        "desc": "A tangy, refreshing cocktail with a salt rim.",
    },
    "Bloody Mary": {
        "ingredients": ["Vodka", "Tomato Juice", "Hot Sauce", "Worcestershire Sauce"],
        "price": 28,
        "alcohol_content": 2,
        "desc": "A savory, spicy morning cocktail.",
    },
    "Mojito": {
        "ingredients": ["Rum", "Lime Juice", "Mint", "Sugar", "Soda Water"],
        "price": 32,
        "alcohol_content": 2,
        "desc": "A refreshing minty cocktail from Cuba.",
    },
    "Piña Colada": {
        "ingredients": ["Rum", "Coconut Cream", "Pineapple Juice"],
        "price": 30,
        "alcohol_content": 2,
        "desc": "A tropical blend that tastes like vacation.",
    },
    "Cosmopolitan": {
        "ingredients": ["Vodka", "Triple Sec", "Cranberry Juice", "Lime Juice"],
        "price": 30,
        "alcohol_content": 2,
        "desc": "A sophisticated, slightly tart cocktail.",
    },
    "Old Fashioned": {
        "ingredients": ["Whiskey", "Bitters", "Sugar", "Water"],
        "price": 32,
        "alcohol_content": 4,
        "desc": "A timeless cocktail that never goes out of style.",
    },
    "Negroni": {
        "ingredients": ["Gin", "Vermouth", "Campari"],
        "price": 30,
        "alcohol_content": 4,
        "desc": "A perfectly balanced bitter and sweet aperitif.",
    },
    "Manhattan": {
        "ingredients": ["Whiskey", "Vermouth", "Bitters"],
        "price": 32,
        "alcohol_content": 4,
        "desc": "A sophisticated whiskey cocktail.",
    },
    "Mai Tai": {
        "ingredients": ["Rum", "Lime Juice", "Orange Curacao", "Orgeat Syrup"],
        "price": 35,
        "alcohol_content": 4,
        "desc": "A complex tropical rum cocktail.",
    },
    "Daiquiri": {
        "ingredients": ["Rum", "Lime Juice", "Sugar"],
        "price": 28,
        "alcohol_content": 2,
        "desc": "A simple, refreshing rum cocktail.",
    },
    "Tom Collins": {
        "ingredients": ["Gin", "Lemon Juice", "Sugar", "Soda Water"],
        "price": 28,
        "alcohol_content": 2,
        "desc": "A refreshing gin cocktail served in a tall glass.",
    },
    "Singapore Sling": {
        "ingredients": ["Gin", "Cherry Brandy", "Pineapple Juice", "Lime Juice", "Grenadine"],
        "price": 35,
        "alcohol_content": 4,
        "desc": "A complex, fruity gin cocktail.",
    },
    "Between the Sheets": {
        "ingredients": ["Brandy", "Rum", "Triple Sec", "Lemon Juice"],
        "price": 35,
        "alcohol_content": 3,
        "desc": "A potent classic blending brandy, rum, orange, and lemon.",
    },
    "Suffering Bastard": {
        "ingredients": ["Brandy", "Gin", "Lime Juice", "Bitters", "Ginger Ale"],
        "price": 34,
        "alcohol_content": 3,
        "desc": "A sharp brandy and gin cocktail softened with ginger ale.",
    },
    "Boston Sidecar": {
        "ingredients": ["Brandy", "Rum", "Triple Sec", "Lime Juice"],
        "price": 34,
        "alcohol_content": 3,
        "desc": "A rum and brandy variation on the citrus-forward Sidecar.",
    },
    "Brass Monkey": {
        "ingredients": ["Vodka", "Rum", "Orange Juice"],
        "price": 30,
        "alcohol_content": 3,
        "desc": "A retro mix of vodka, rum, and orange juice.",
    },
    "Long Island Iced Tea": {
        "ingredients": ["Vodka", "Gin", "Rum", "Tequila", "Triple Sec", "Lemon Juice", "Cola"],
        "price": 40,
        "alcohol_content": 5,
        "desc": "A potent mix of multiple spirits with a cola finish.",
    },
    "Space Blaster": {
        "ingredients": ["Vodka", "Blue Curacao", "Sprite", "Lemon Juice"],
        "price": 35,
        "alcohol_content": 2,
        "desc": "A station specialty with an electric blue color.",
    },
    "Quantum Fizz": {
        "ingredients": ["Gin", "Lime Juice", "Sugar", "Mint", "Helium Gas"],
        "price": 38,
        "alcohol_content": 2,
        "desc": "A unique drink that temporarily changes your voice.",
    },
    "Nebula Cloud": {
        "ingredients": ["Whiskey", "Honey", "Dry Ice", "Cinnamon"],
        "price": 42,
        "alcohol_content": 2,
        "desc": "A smoky cocktail that mimics a space nebula.",
    },
    "Solar Flare": {
        "ingredients": ["Tequila", "Rum", "Pineapple Juice", "Lime Juice", "Grenadine"],
        "price": 36,
        "alcohol_content": 3,
        "desc": "A fiery tropical station special with a bright red glow.",
    },
}

AVAILABLE_INGREDIENTS = [
    "Vodka", "Gin", "Rum", "Whiskey", "Tequila", "Brandy", "Scotch",
    "Orange Juice", "Cranberry Juice", "Pineapple Juice", "Tomato Juice",
    "Tonic Water", "Soda Water", "Water", "Cola", "Ginger Ale", "Sprite",
    "Lemon Juice", "Lime Juice", "Sugar", "Salt", "Honey",
    "Triple Sec", "Blue Curacao", "Orange Curacao", "Grenadine",
    "Bitters", "Vermouth", "Campari", "Cherry Brandy",
    "Mint", "Coconut Cream", "Hot Sauce", "Worcestershire Sauce",
    "Cinnamon", "Orgeat Syrup", "Dry Ice", "Helium Gas",
]

BASIC_RECIPES = ["Screwdriver", "Gin and Tonic", "Rum and Cola", "Whiskey Sour", "Daiquiri"]
SPECIAL_RECIPES = ["Space Blaster", "Quantum Fizz", "Nebula Cloud", "Solar Flare"]
SPIRITS = ["Vodka", "Gin", "Rum", "Whiskey", "Tequila", "Brandy", "Scotch"]
MODIFIERS = [
    "Lemon Juice", "Lime Juice", "Sugar", "Salt", "Honey", "Triple Sec",
    "Blue Curacao", "Orange Curacao", "Grenadine", "Bitters", "Vermouth",
    "Campari", "Cherry Brandy",
]
BASIC_ALCOHOLIC_DRINKS = frozenset(SPIRITS) | {"Beer", "Wine"}


def is_drink_alcoholic(name, details):
    """Return True if the drink contains alcohol."""
    if name in DRINKS_MENU:
        return name in BASIC_ALCOHOLIC_DRINKS
    return any(ing in SPIRITS for ing in details.get("ingredients", []))


def validate_mixed_drink_ingredients():
    """Return {drink_name: [missing_ingredients]} for invalid recipes."""
    available = set(AVAILABLE_INGREDIENTS)
    return {
        name: [i for i in data["ingredients"] if i not in available]
        for name, data in MIXED_DRINKS.items()
        if any(i not in available for i in data["ingredients"])
    }


def _apply_alcohol_flags():
    """Stamp alcohol metadata onto drink menu entries."""
    for name, details in DRINKS_MENU.items():
        details["alcoholic"] = is_drink_alcoholic(name, details)
    for name, details in MIXED_DRINKS.items():
        details["alcoholic"] = is_drink_alcoholic(name, details)
        if details["alcoholic"] and "alcohol_content" not in details:
            spirit_count = sum(ingredient in SPIRITS for ingredient in details["ingredients"])
            details["alcohol_content"] = 3 if spirit_count > 1 else 2


_apply_alcohol_flags()


def categorize_ingredients(ingredients=None):
    """Return (spirits, mixers, modifiers, specials) for the mixer UI."""
    ingredients = ingredients or AVAILABLE_INGREDIENTS
    spirits = [i for i in ingredients if i in SPIRITS]
    mixers = [
        i for i in ingredients
        if "Juice" in i or "Water" in i or "Cola" in i or "Ale" in i or "Sprite" in i
    ]
    modifiers = [i for i in ingredients if i in MODIFIERS]
    specials = [i for i in ingredients if i not in spirits and i not in mixers and i not in modifiers]
    return spirits, mixers, modifiers, specials


def categorize_ingredients_exclusive(ingredients=None):
    """Return mutually exclusive (spirits, mixers, modifiers, specials) for display."""
    ingredients = sorted(ingredients or AVAILABLE_INGREDIENTS)
    spirits = []
    mixers = []
    modifiers = []
    specials = []

    for ingredient in ingredients:
        if ingredient in SPIRITS:
            spirits.append(ingredient)
        elif "Juice" in ingredient or "Water" in ingredient or "Cola" in ingredient or "Ale" in ingredient or "Sprite" in ingredient:
            mixers.append(ingredient)
        elif ingredient in MODIFIERS:
            modifiers.append(ingredient)
        else:
            specials.append(ingredient)

    return spirits, mixers, modifiers, specials


def match_recipe(ingredients):
    """Return (drink_name, drink_data) if ingredients match a known recipe, else (None, None)."""
    sorted_ingredients = sorted(ingredients)
    for drink_name, drink_data in MIXED_DRINKS.items():
        if sorted_ingredients == sorted(drink_data["ingredients"]):
            return drink_name, drink_data
    return None, None


def get_mix_feedback(ingredients):
    """Return failure feedback for an unknown ingredient mix."""
    if len(ingredients) > 5:
        return "This has too many ingredients - most cocktails use 2-5 ingredients."
    if not any(item in SPIRITS for item in ingredients):
        return "Most mixed drinks need a spirit as the base (like Vodka, Rum, or Whiskey)."
    if all(item in SPIRITS for item in ingredients):
        return "This is just a mix of different spirits. Try adding some mixers or modifiers."
    return "This combination doesn't match any known recipe. Try a different mix."


class DrinkMixer:
    """Handles bartender drink creation UI."""

    def __init__(self, parent_window, player_data):
        self.parent_window = parent_window
        self.player_data = player_data

    def show_mixer(self):
        """Show interface for mixing custom drinks."""
        _panel, mixer_popup = open_modal_panel(self.parent_window, title="Bartender's Drink Mixer")
        main_canvas = tk.Canvas(mixer_popup, bg="black", highlightthickness=0)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        main_scrollbar = tk.Scrollbar(mixer_popup, orient=tk.VERTICAL, command=main_canvas.yview)
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        content_frame = tk.Frame(main_canvas, bg="black")
        content_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)

        title_label = tk.Label(content_frame, text="Bartender's Drink Mixer", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        main_frame = tk.Frame(content_frame, bg="black")
        main_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame, bg="black", width=375)
        left_frame.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        category_frame = tk.Frame(left_frame, bg="black")
        category_frame.pack(fill=tk.X, pady=5)

        category_label = tk.Label(category_frame, text="Ingredient Categories:", font=("Arial", 14), bg="black", fg="white")
        category_label.pack(anchor=tk.W, pady=5)

        btn_frame = tk.Frame(category_frame, bg="black")
        btn_frame.pack(fill=tk.X)

        spirits, mixers, modifiers, specials = categorize_ingredients()
        current_category = {"items": AVAILABLE_INGREDIENTS}

        ing_frame = tk.LabelFrame(left_frame, text="Available Ingredients", font=("Arial", 12), bg="black", fg="white")
        ing_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ing_scrollbar = tk.Scrollbar(ing_frame)
        ing_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ing_listbox = tk.Listbox(ing_frame, bg="black", fg="white", font=("Arial", 12),
                              width=20, height=12, yscrollcommand=ing_scrollbar.set)
        ing_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ing_scrollbar.config(command=ing_listbox.yview)

        def show_category(items, category_name):
            ing_listbox.delete(0, tk.END)
            current_category["items"] = items
            ing_listbox.insert(tk.END, f"--- {category_name} ---")
            for item in sorted(items):
                ing_listbox.insert(tk.END, item)

        all_btn = tk.Button(btn_frame, text="All", font=("Arial", 10),
                         command=lambda: show_category(AVAILABLE_INGREDIENTS, "All Ingredients"))
        all_btn.pack(side=tk.LEFT, padx=5, pady=5)

        spirits_btn = tk.Button(btn_frame, text="Spirits", font=("Arial", 10),
                             command=lambda: show_category(spirits, "Spirits"))
        spirits_btn.pack(side=tk.LEFT, padx=5, pady=5)

        mixers_btn = tk.Button(btn_frame, text="Mixers", font=("Arial", 10),
                            command=lambda: show_category(mixers, "Mixers"))
        mixers_btn.pack(side=tk.LEFT, padx=5, pady=5)

        modifiers_btn = tk.Button(btn_frame, text="Modifiers", font=("Arial", 10),
                               command=lambda: show_category(modifiers, "Modifiers"))
        modifiers_btn.pack(side=tk.LEFT, padx=5, pady=5)

        specials_btn = tk.Button(btn_frame, text="Specials", font=("Arial", 10),
                              command=lambda: show_category(specials, "Special Ingredients"))
        specials_btn.pack(side=tk.LEFT, padx=5, pady=5)

        show_category(AVAILABLE_INGREDIENTS, "All Ingredients")

        right_frame = tk.Frame(main_frame, bg="black", width=375)
        right_frame.pack(side=tk.RIGHT, padx=10, fill=tk.BOTH, expand=True)

        mix_frame = tk.LabelFrame(right_frame, text="Mixing Glass", font=("Arial", 12), bg="black", fg="white")
        mix_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        mix_scrollbar = tk.Scrollbar(mix_frame)
        mix_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        mix_listbox = tk.Listbox(mix_frame, bg="black", fg="white", font=("Arial", 12),
                              width=20, height=12, yscrollcommand=mix_scrollbar.set)
        mix_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mix_scrollbar.config(command=mix_listbox.yview)

        add_btn = tk.Button(left_frame, text="Add Ingredient →", font=("Arial", 12),
                         command=lambda: self._add_to_mix(ing_listbox, mix_listbox, current_category["items"]))
        add_btn.pack(pady=10)

        remove_btn = tk.Button(right_frame, text="← Remove Ingredient", font=("Arial", 12),
                            command=lambda: self._remove_from_mix(mix_listbox))
        remove_btn.pack(pady=5)

        clear_btn = tk.Button(right_frame, text="Clear Glass", font=("Arial", 12),
                           command=lambda: mix_listbox.delete(0, tk.END))
        clear_btn.pack(pady=5)

        result_frame = tk.LabelFrame(content_frame, text="Mixing Result", font=("Arial", 12), bg="black", fg="white")
        result_frame.pack(padx=20, pady=10, fill=tk.X)

        result_label = tk.Label(result_frame, text="Mix ingredients to create a drink",
                            font=("Arial", 12), bg="black", fg="white", wraplength=700)
        result_label.pack(pady=10, fill=tk.X)

        bottom_frame = tk.Frame(content_frame, bg="black")
        bottom_frame.pack(pady=10)

        mix_btn = tk.Button(bottom_frame, text="Mix Drink", font=("Arial", 14), bg="dark blue", fg="white",
                         command=lambda: self._mix_drink(mix_listbox, result_label))
        mix_btn.pack(side=tk.LEFT, padx=20)

        recipe_btn = tk.Button(bottom_frame, text="Recipe Book", font=("Arial", 14),
                            command=self.show_recipes)
        recipe_btn.pack(side=tk.LEFT, padx=20)

        close_btn = tk.Button(bottom_frame, text="Close", font=("Arial", 14),
                           command=mixer_popup.destroy)
        close_btn.pack(side=tk.LEFT, padx=20)

        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        mixer_popup.bind("<MouseWheel>", _on_mousewheel)

        orig_destroy = mixer_popup.destroy
        def _destroy_and_cleanup():
            mixer_popup.unbind("<MouseWheel>")
            orig_destroy()

        mixer_popup.destroy = _destroy_and_cleanup

    def _add_to_mix(self, ing_listbox, mix_listbox, available_items):
        """Add an ingredient to the mixing glass."""
        selection = ing_listbox.curselection()
        if not selection or selection[0] == 0:
            return

        index = selection[0]
        entry = ing_listbox.get(index)

        if entry.startswith("---"):
            return

        mix_listbox.insert(tk.END, entry)

    def _remove_from_mix(self, mix_listbox):
        """Remove an ingredient from the mixing glass."""
        selection = mix_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        mix_listbox.delete(index)

    def _mix_drink(self, mix_listbox, result_label):
        """Mix ingredients and determine the result."""
        ingredients = [mix_listbox.get(i) for i in range(mix_listbox.size())]

        if not ingredients:
            result_label.config(text="You need to add ingredients first!")
            return

        drink_match, drink_data = match_recipe(ingredients)

        if drink_match:
            stock = self.player_data.setdefault("bar_mixed_stock", {})
            stock[drink_match] = stock.get(drink_match, 0) + 1
            qty = stock[drink_match]

            result_text = (
                f"Success! You've mixed a {drink_match}.\n"
                f"{drink_data['desc']}\n"
                f"(Qty: {qty})"
            )
            result_label.config(text=result_text, fg="light green")

            if "notes" not in self.player_data:
                self.player_data["notes"] = []

            self.player_data["notes"].append({
                "timestamp": datetime.datetime.now().isoformat(),
                "text": f"Successfully mixed a {drink_match} at the bar.",
            })
        else:
            feedback = get_mix_feedback(ingredients)
            result_text = f"You've created an unknown concoction. {feedback}"
            result_label.config(text=result_text, fg="red")

        # Clear the glass so the next drink must be mixed from scratch
        mix_listbox.delete(0, tk.END)

    def show_recipes(self):
        """Show a list of known drink recipes."""
        _panel, recipes_popup = open_modal_panel(self.parent_window, title="Drink Recipes")
        title_label = tk.Label(recipes_popup, text="Bartender's Recipe Book", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        nav_frame = tk.Frame(recipes_popup, bg="black")
        nav_frame.pack(fill=tk.X, padx=10, pady=5)

        all_btn = tk.Button(nav_frame, text="All Recipes", font=("Arial", 10),
                         command=lambda: show_recipe_category("all"))
        all_btn.pack(side=tk.LEFT, padx=5)

        basic_btn = tk.Button(nav_frame, text="Basic Recipes", font=("Arial", 10),
                           command=lambda: show_recipe_category("basic"))
        basic_btn.pack(side=tk.LEFT, padx=5)

        advanced_btn = tk.Button(nav_frame, text="Advanced Recipes", font=("Arial", 10),
                          command=lambda: show_recipe_category("advanced"))
        advanced_btn.pack(side=tk.LEFT, padx=5)

        special_btn = tk.Button(nav_frame, text="Station Specials", font=("Arial", 10),
                         command=lambda: show_recipe_category("special"))
        special_btn.pack(side=tk.LEFT, padx=5)

        frame = tk.Frame(recipes_popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        recipe_text = tk.Text(frame, bg="black", fg="white", font=("Arial", 12),
                           width=60, height=25, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        recipe_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=recipe_text.yview)

        def _on_recipe_mousewheel(event):
            try:
                recipe_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass

        recipes_popup.bind("<MouseWheel>", _on_recipe_mousewheel)

        orig_destroy = recipes_popup.destroy
        def _destroy_and_cleanup():
            try:
                recipes_popup.unbind("<MouseWheel>")
            except Exception:
                pass
            orig_destroy()

        recipes_popup.destroy = _destroy_and_cleanup

        def add_recipe(drink_name):
            if drink_name in MIXED_DRINKS:
                drink_data = MIXED_DRINKS[drink_name]
                recipe_text.insert(tk.END, f"{drink_name}:\n", "drink_name")
                recipe_text.insert(tk.END, "  Ingredients: ", "label")
                recipe_text.insert(tk.END, f"{', '.join(drink_data['ingredients'])}\n", "ingredients")
                recipe_text.insert(tk.END, "  Price: ", "label")
                recipe_text.insert(tk.END, f"{drink_data['price']} credits\n", "value")
                recipe_text.insert(tk.END, "  Description: ", "label")
                recipe_text.insert(tk.END, f"{drink_data['desc']}\n\n", "value")

        def show_recipe_category(category):
            recipe_text.config(state=tk.NORMAL)
            recipe_text.delete(1.0, tk.END)

            recipe_text.insert(tk.END, "BARTENDER'S RECIPE BOOK\n", "header")
            recipe_text.insert(tk.END, "------------------------\n\n", "header")

            sorted_drinks = sorted(MIXED_DRINKS.keys())

            if category == "basic":
                sorted_drinks = [drink for drink in sorted_drinks if drink in BASIC_RECIPES]
                recipe_text.insert(tk.END, "BASIC COCKTAILS\n\n", "category")
            elif category == "special":
                sorted_drinks = [drink for drink in sorted_drinks if drink in SPECIAL_RECIPES]
                recipe_text.insert(tk.END, "STATION SPECIALTIES\n\n", "category")
            elif category == "advanced":
                sorted_drinks = [
                    drink for drink in sorted_drinks
                    if drink not in BASIC_RECIPES and drink not in SPECIAL_RECIPES
                ]
                recipe_text.insert(tk.END, "ADVANCED COCKTAILS\n\n", "category")
            else:
                recipe_text.insert(tk.END, "BASIC COCKTAILS\n\n", "category")
                for drink in sorted(BASIC_RECIPES):
                    add_recipe(drink)

                recipe_text.insert(tk.END, "\nADVANCED COCKTAILS\n\n", "category")
                for drink in sorted([d for d in sorted_drinks if d not in BASIC_RECIPES and d not in SPECIAL_RECIPES]):
                    add_recipe(drink)

                recipe_text.insert(tk.END, "\nSTATION SPECIALTIES\n\n", "category")
                for drink in sorted(SPECIAL_RECIPES):
                    add_recipe(drink)

                recipe_text.config(state=tk.DISABLED)
                return

            for drink in sorted_drinks:
                add_recipe(drink)

            recipe_text.config(state=tk.DISABLED)

        recipe_text.tag_configure("header", font=("Arial", 14, "bold"))
        recipe_text.tag_configure("category", font=("Arial", 13, "bold"), foreground="yellow")
        recipe_text.tag_configure("drink_name", font=("Arial", 12, "bold"), foreground="light blue")
        recipe_text.tag_configure("label", font=("Arial", 11, "bold"))
        recipe_text.tag_configure("ingredients", font=("Arial", 11), foreground="light green")
        recipe_text.tag_configure("value", font=("Arial", 11))

        show_recipe_category("all")

        search_frame = tk.Frame(recipes_popup, bg="black")
        search_frame.pack(fill=tk.X, padx=20, pady=5)

        search_label = tk.Label(search_frame, text="Search: ", font=("Arial", 11), bg="black", fg="white")
        search_label.pack(side=tk.LEFT, padx=5)

        search_entry = tk.Entry(search_frame, bg="dark gray", fg="white", font=("Arial", 11), width=20)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        def search_recipes(event=None):
            query = search_entry.get().lower().strip()
            if not query:
                show_recipe_category("all")
                return

            recipe_text.config(state=tk.NORMAL)
            recipe_text.delete(1.0, tk.END)

            recipe_text.insert(tk.END, f"SEARCH RESULTS FOR '{query}'\n", "header")
            recipe_text.insert(tk.END, "------------------------\n\n", "header")

            results_found = False
            for drink_name, drink_data in MIXED_DRINKS.items():
                if (query in drink_name.lower()
                        or any(query in ingredient.lower() for ingredient in drink_data["ingredients"])
                        or query in drink_data["desc"].lower()):
                    add_recipe(drink_name)
                    results_found = True

            if not results_found:
                recipe_text.insert(tk.END, "No recipes found matching your search.")

            recipe_text.config(state=tk.DISABLED)

        search_entry.bind("<Return>", search_recipes)

        search_btn = tk.Button(search_frame, text="Search", font=("Arial", 10), command=search_recipes)
        search_btn.pack(side=tk.LEFT, padx=5)

        ing_btn = tk.Button(search_frame, text="Ingredients List", font=("Arial", 10),
                         command=self.show_ingredients_list)
        ing_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(recipes_popup, text="Close", font=("Arial", 12), command=recipes_popup.destroy)
        close_btn.pack(pady=10)

    def show_ingredients_list(self):
        """Show a list of all available ingredients."""
        _panel, ing_popup = open_modal_panel(self.parent_window, title="Available Ingredients")
        title_label = tk.Label(ing_popup, text="Available Ingredients", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        spirits, mixers, modifiers, specials = categorize_ingredients_exclusive()

        frame = tk.Frame(ing_popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ing_text = tk.Text(frame, bg="black", fg="white", font=("Arial", 12),
                        width=40, height=20, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        ing_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=ing_text.yview)

        def _on_ing_mousewheel(event):
            try:
                ing_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass

        ing_popup.bind("<MouseWheel>", _on_ing_mousewheel)

        orig_destroy = ing_popup.destroy
        def _destroy_and_cleanup():
            try:
                ing_popup.unbind("<MouseWheel>")
            except Exception:
                pass
            orig_destroy()

        ing_popup.destroy = _destroy_and_cleanup

        ing_text.insert(tk.END, "SPIRITS\n", "header")
        ing_text.insert(tk.END, "-------\n", "header")
        for ingredient in spirits:
            ing_text.insert(tk.END, f"• {ingredient}\n", "ingredient")

        ing_text.insert(tk.END, "\nMIXERS\n", "header")
        ing_text.insert(tk.END, "------\n", "header")
        for ingredient in mixers:
            ing_text.insert(tk.END, f"• {ingredient}\n", "ingredient")

        ing_text.insert(tk.END, "\nMODIFIERS\n", "header")
        ing_text.insert(tk.END, "---------\n", "header")
        for ingredient in modifiers:
            ing_text.insert(tk.END, f"• {ingredient}\n", "ingredient")

        ing_text.insert(tk.END, "\nSPECIAL INGREDIENTS\n", "header")
        ing_text.insert(tk.END, "------------------\n", "header")
        for ingredient in specials:
            ing_text.insert(tk.END, f"• {ingredient}\n", "ingredient")

        ing_text.tag_configure("header", font=("Arial", 14, "bold"))
        ing_text.tag_configure("ingredient", font=("Arial", 11))

        ing_text.config(state=tk.DISABLED)

        close_btn = tk.Button(ing_popup, text="Close", font=("Arial", 12), command=ing_popup.destroy)
        close_btn.pack(pady=10)
