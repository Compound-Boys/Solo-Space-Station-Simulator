import tkinter as tk
from tkinter import messagebox

from game.helper_methods.game_clock import format_elapsed, get_elapsed_seconds
from game.helper_methods.ui_panels import bind_mousewheel, open_modal_panel, refocus_window, schedule_ui_tick
from game.maps.donut import BOTANY_KEY
from game.objects.botany_items import (
    BOTANY_SEED_IDS,
    BOTANY_VEND_IDS,
    GROWTH_STAGES,
    MIRACLE_GROW_SPEED_BONUS,
    PLENTIFUL_HARVEST_YIELD_MULTIPLIER,
    growth_seconds_to_next_stage,
    growth_stage_label,
    refresh_planter_growth,
)
from game.objects.items import (
    add_to_inventory,
    ensure_hands,
    format_inventory_label,
    get_item_definition,
)
from game.special_rooms.shared import (
    SpecialRoomBase,
    add_note,
    build_npc_contact_section,
    clear_button_frame,
)

PLANTERS_PER_ROW = 4
PLANTER_ROWS = 4
TOTAL_PLANTERS = PLANTERS_PER_ROW * PLANTER_ROWS

# Consumed from the hand on a single successful application.
LIQUID_CONSUMABLE_IDS = {"miracle_grow", "plentiful_harvest", "the_ooze_mutagen"}

# Reusable tools that clear a planter; each maps to a growth_class predicate
# for which plants they're allowed to clear.
TOOL_GROWTH_CLASS_RULES = {
    "trowel": lambda growth_class: growth_class != "tree",
    "chainsaw": lambda growth_class: growth_class == "tree",
}


def _empty_planter():
    return {
        "occupied": False,
        "plant": None,
        "seed_id": None,
        "produces": None,
        "growth_class": None,
        "planted_at_seconds": None,
        "growth_stage": 0,
        "dead": False,
        "watered": False,
        "miracle_grow": 0.0,
        "yield_multiplier": 1,
        "ooze_applied": False,
    }


class Botany(SpecialRoomBase):
    ROOM_TITLE = "Botany Lab"
    ROOM_HEADING = "Station Botany Lab"
    ROOM_DESCRIPTION = (
        "The botany lab is filled with plants of all varieties. Hydroponic systems line the walls, "
        "and bright grow lights illuminate rows of planters. The air is humid and smells of fresh "
        "soil and vegetation."
    )
    DOOR_KEY = BOTANY_KEY
    WINDOW_ATTR = "botany_window"

    def _before_open(self):
        if "botany" not in self.player_data:
            self.player_data["botany"] = {
                "planters": [_empty_planter() for _ in range(TOTAL_PLANTERS)],
            }

    def _inventory_vend_items(self):
        """Return (inventory_index, item) pairs for botany vending items in inventory."""
        items = []
        for index, item in enumerate(self.player_data.get("inventory", []) or []):
            if isinstance(item, dict) and item.get("id") in BOTANY_VEND_IDS:
                items.append((index, item))
        return items

    def station_entries(self):
        return [{
            "label": "Enter Botany Station",
            "command": self.access_botany_station,
        }]

    def show_room_options(self):
        clear_button_frame(self.button_frame)

        view_plants_btn = tk.Button(
            self.button_frame,
            text="View Plants",
            font=("Arial", 14),
            width=20,
            command=lambda: self.view_plants(allow_harvest=False),
        )
        view_plants_btn.pack(pady=10)

        build_npc_contact_section(
            self.button_frame,
            self.player_data,
            self.station_crew,
            "Botanist",
            self.botany_window,
            talk_label="Talk to Botanist",
            talk_command=self.talk_to_botanist,
            refresh_callback=self.show_room_options,
            absent_flavor="The botanist is away from the lab.",
        )

        self.pack_back_to_station_menu()

    def talk_to_botanist(self):
        self.botany_window.after(
            10,
            lambda: messagebox.showinfo(
                "Botanist",
                "The botanist continues tending to the plants without looking up.",
                parent=self.botany_window,
            ),
        )
        refocus_window(self.botany_window)

    def _show_row_picker(self, title, on_row_selected):
        """Open Hydroponic Rows picker; on_row_selected(row_index 0-3)."""
        panel, popup = open_modal_panel(self.botany_window, title=title)
        popup.configure(bg="black")

        tk.Label(
            popup,
            text="Hydroponic Rows",
            font=("Arial", 18, "bold"),
            bg="black",
            fg="white",
        ).pack(pady=15)

        tk.Label(
            popup,
            text="Select a row of planters to work with.",
            font=("Arial", 12),
            bg="black",
            fg="white",
            wraplength=500,
        ).pack(pady=10)

        button_frame = tk.Frame(popup, bg="black")
        button_frame.pack(pady=20)

        def choose_row(row_index):
            panel.close()
            on_row_selected(row_index)

        for row in range(PLANTER_ROWS):
            tk.Button(
                button_frame,
                text=f"Row {row + 1}",
                font=("Arial", 14),
                width=20,
                command=lambda r=row: choose_row(r),
            ).pack(pady=8)

        tk.Button(
            popup, text="Close", font=("Arial", 14), width=15, command=panel.close
        ).pack(pady=15)

    def view_plants(self, allow_harvest=False):
        """Pick a hydroponic row, then view that row's planters."""
        self._show_row_picker(
            "View Plants",
            lambda row_index: self._view_plants_row(row_index, allow_harvest=allow_harvest),
        )

    def _view_plants_row(self, row_index, allow_harvest=False):
        start = row_index * PLANTERS_PER_ROW
        end = start + PLANTERS_PER_ROW
        planters = self.player_data["botany"]["planters"]

        cancel_tick = {"fn": None}

        def _on_close():
            if cancel_tick["fn"] is not None:
                cancel_tick["fn"]()
                cancel_tick["fn"] = None

        panel, plants_window = open_modal_panel(
            self.botany_window,
            title=f"Viewing Plants — Row {row_index + 1}",
            on_close=_on_close,
        )
        tk.Label(
            plants_window,
            text=f"Botany Lab Plants — Row {row_index + 1}",
            font=("Arial", 16, "bold"),
            bg="black",
            fg="white",
        ).pack(pady=(8, 4))

        tk.Label(
            plants_window,
            text="You observe the plants growing in this hydroponic row.",
            font=("Arial", 11),
            bg="black",
            fg="white",
            wraplength=500,
        ).pack(pady=(0, 4))

        def back_to_row_picker():
            panel.close()
            self.view_plants(allow_harvest=allow_harvest)

        def open_hands_from_plants():
            """Open Hands, then return to this same planter row when closed."""
            def return_to_plants():
                self._view_plants_row(row_index, allow_harvest=allow_harvest)

            panel.close()
            self.show_hands_popup(on_close=return_to_plants)

        # Pack nav buttons at the bottom first so they keep their slice of the
        # fixed-size modal, even if the planter list below wants more room.
        nav_frame = tk.Frame(plants_window, bg="black")
        nav_frame.pack(side=tk.BOTTOM, pady=(4, 8))

        tk.Button(
            nav_frame,
            text="Back",
            font=("Arial", 14),
            width=15,
            command=back_to_row_picker,
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            nav_frame,
            text="Hands",
            font=("Arial", 14),
            width=15,
            command=open_hands_from_plants,
        ).pack(side=tk.LEFT, padx=8)

        planters_frame = tk.Frame(plants_window, bg="black")
        planters_frame.pack(pady=4, fill=tk.BOTH, expand=True)

        # Live-updating widgets for every planter in this row (empty or occupied).
        # Every card gets the exact same widgets so planting never changes its height.
        live_rows = []

        # Planter 3's current size is the preferred max; shrink only enough so all 4 fit.
        preferred_height = 190 if allow_harvest else 130
        plants_window.update_idletasks()
        parent_h = plants_window.winfo_height()
        if parent_h <= 1:
            parent_h = self.botany_window.winfo_height()
        if parent_h <= 1:
            parent_h = 759
        # Title + description + Back + paddings leave this much for the four cards.
        chrome = 120
        available = max(440, parent_h - chrome)
        card_gap = 4
        card_height = max(
            110,
            min(
                preferred_height,
                (available - card_gap * PLANTERS_PER_ROW) // PLANTERS_PER_ROW,
            ),
        )

        hands = ensure_hands(self.player_data) if allow_harvest else None

        for i in range(start, end):
            planter = planters[i]
            planter_frame = tk.Frame(
                planters_frame,
                bg="#222222",
                bd=2,
                relief=tk.RIDGE,
                width=500,
                height=card_height,
            )
            planter_frame.pack_propagate(False)
            planter_frame.pack(fill=tk.X, padx=20, pady=2)

            title_text = (
                f"Planter {i + 1}: {planter['plant']}"
                if planter["occupied"]
                else f"Planter {i + 1}: Empty"
            )
            tk.Label(
                planter_frame,
                text=title_text,
                font=("Arial", 13, "bold"),
                bg="#222222",
                fg="light green" if planter["occupied"] else "white",
            ).pack(anchor="w", padx=10, pady=(4, 2))
            stage_label = tk.Label(
                planter_frame,
                text="",
                font=("Arial", 11),
                bg="#222222",
                fg="white",
            )
            stage_label.pack(anchor="w", padx=10, pady=1)
            time_label = tk.Label(
                planter_frame,
                text="",
                font=("Arial", 10),
                bg="#222222",
                fg="cyan",
            )
            time_label.pack(anchor="w", padx=10, pady=1)

            # Applied products (Miracle Grow, Plentiful Harvest) — horizontal only.
            buffs_row = tk.Frame(planter_frame, bg="#222222")
            buffs_row.pack(anchor="w", padx=10, pady=1)

            # Harvest + hand buttons share one bottom row so card height stays stable.
            actions_row = tk.Frame(planter_frame, bg="#222222")
            actions_row.pack(anchor="e", padx=10, pady=(2, 4))
            harvest_slot = tk.Frame(actions_row, bg="#222222")
            harvest_slot.pack(side=tk.LEFT, padx=(0, 4))
            live_rows.append(
                {
                    "index": i,
                    "stage_label": stage_label,
                    "time_label": time_label,
                    "buffs_row": buffs_row,
                    "buff_key": None,
                    "harvest_slot": harvest_slot,
                    "harvest_btn": None,
                }
            )

            if allow_harvest:
                hand_slot = tk.Frame(actions_row, bg="#222222")
                hand_slot.pack(side=tk.LEFT)

                for side, default_label in (
                    ("left", "Use Left Hand"),
                    ("right", "Use Right Hand"),
                ):
                    held = hands.get(side)
                    label = (
                        f"Use {held.get('name', 'Item')}"
                        if isinstance(held, dict)
                        else default_label
                    )
                    tk.Button(
                        hand_slot,
                        text=label,
                        font=("Arial", 9),
                        command=lambda idx=i, s=side: self._use_hand_on_planter(
                            s, idx, plants_window, row_index
                        ),
                    ).pack(side=tk.LEFT, padx=2)

        def _ensure_harvest_button(row):
            if row["harvest_btn"] is not None:
                return
            idx = row["index"]
            btn = tk.Button(
                row["harvest_slot"],
                text="Harvest",
                font=("Arial", 10),
                command=lambda planter_idx=idx: self._harvest_planter(
                    planter_idx, plants_window, row_index, allow_harvest=True
                ),
            )
            btn.pack()
            row["harvest_btn"] = btn

        def _clear_harvest_button(row):
            btn = row["harvest_btn"]
            if btn is None:
                return
            try:
                btn.destroy()
            except tk.TclError:
                pass
            row["harvest_btn"] = None

        def _refresh_buffs_row(row, planter):
            has_miracle = bool(planter.get("occupied") and (planter.get("miracle_grow") or 0.0) > 0)
            has_plentiful = bool(
                planter.get("occupied") and int(planter.get("yield_multiplier") or 1) > 1
            )
            has_ooze = bool(planter.get("occupied") and planter.get("ooze_applied"))
            buff_key = (has_miracle, has_plentiful, has_ooze)
            if row.get("buff_key") == buff_key:
                return
            row["buff_key"] = buff_key

            buffs_row = row["buffs_row"]
            for child in buffs_row.winfo_children():
                child.destroy()

            if has_miracle:
                tk.Label(
                    buffs_row,
                    text="Miracle Grow",
                    font=("Arial", 9),
                    bg="#1A3200",
                    fg="#90EE90",
                    padx=4,
                    pady=1,
                ).pack(side=tk.LEFT, padx=(0, 6))

            if has_plentiful:
                tk.Label(
                    buffs_row,
                    text="Plentiful Harvest",
                    font=("Arial", 9),
                    bg="#1A3200",
                    fg="#FFD700",
                    padx=4,
                    pady=1,
                ).pack(side=tk.LEFT, padx=(0, 6))

            if has_ooze:
                tk.Label(
                    buffs_row,
                    text="The Ooze",
                    font=("Arial", 9),
                    bg="#1A3200",
                    fg="#7CFC00",
                    padx=4,
                    pady=1,
                ).pack(side=tk.LEFT, padx=(0, 6))

        def _refresh_live_labels():
            elapsed_seconds = get_elapsed_seconds(self.player_data)
            for row in live_rows:
                planter = planters[row["index"]]
                if not planter.get("occupied"):
                    row["stage_label"].config(text="Status: Empty", fg="white")
                    row["time_label"].config(
                        text="This planter is ready for seeds.", fg="gray"
                    )
                    _refresh_buffs_row(row, planter)
                    _clear_harvest_button(row)
                    continue

                growth_stage = refresh_planter_growth(planter, elapsed_seconds)
                _refresh_buffs_row(row, planter)

                if planter.get("dead"):
                    row["stage_label"].config(text="Status: Dead", fg="red")
                    row["time_label"].config(
                        text="Needs to be cleared with a Trowel or Chainsaw.",
                        fg="red",
                    )
                    _clear_harvest_button(row)
                    continue

                growth_text = growth_stage_label(growth_stage)
                needs_water = growth_stage < GROWTH_STAGES and not planter.get("watered")
                water_hint = " — needs water" if needs_water else ""
                row["stage_label"].config(
                    text=f"Stage: {growth_text} ({growth_stage}/{GROWTH_STAGES}){water_hint}",
                    fg="orange" if needs_water else "white",
                )

                if growth_stage >= GROWTH_STAGES:
                    row["time_label"].config(text="Ready to harvest", fg="light green")
                    if allow_harvest:
                        _ensure_harvest_button(row)
                    else:
                        _clear_harvest_button(row)
                else:
                    next_in = growth_seconds_to_next_stage(
                        planter.get("planted_at_seconds"),
                        planter.get("growth_class"),
                        elapsed_seconds,
                        planter.get("miracle_grow") or 0.0,
                    )
                    row["time_label"].config(
                        text=f"Next stage in {format_elapsed(next_in)}",
                        fg="cyan",
                    )
                    _clear_harvest_button(row)

        _refresh_live_labels()
        cancel_tick["fn"] = schedule_ui_tick(plants_window, _refresh_live_labels)

    def _harvest_planter(self, planter_index, plants_window, row_index, allow_harvest=True):
        """Harvest a mature planter into inventory and clear it (station View Plants only)."""
        if not allow_harvest:
            return

        planters = self.player_data["botany"]["planters"]
        if not (0 <= planter_index < len(planters)):
            return

        planter = planters[planter_index]
        if not planter.get("occupied") or planter.get("dead"):
            return

        elapsed_seconds = get_elapsed_seconds(self.player_data)
        growth_stage = refresh_planter_growth(planter, elapsed_seconds)
        if growth_stage < GROWTH_STAGES:
            messagebox.showinfo(
                "Not Ready",
                f"Planter {planter_index + 1} is not ready to harvest yet.",
                parent=plants_window,
            )
            return

        produces_id = planter.get("produces")
        if not produces_id and planter.get("seed_id"):
            seed_def = get_item_definition(planter["seed_id"])
            if seed_def:
                produces_id = (seed_def.get("attributes") or {}).get("produces")

        produce = get_item_definition(produces_id) if produces_id else None
        if not produce:
            messagebox.showerror(
                "Harvest Failed",
                "Could not resolve the produce for this plant.",
                parent=plants_window,
            )
            return

        yield_multiplier = max(1, int(planter.get("yield_multiplier") or 1))
        produce["quantity"] = yield_multiplier
        add_to_inventory(self.player_data, produce)
        plant_name = planter.get("plant") or produce.get("name", "produce")
        planters[planter_index] = _empty_planter()
        add_note(
            self.player_data,
            f"Harvested {yield_multiplier}x {produce.get('name', plant_name)} from planter {planter_index + 1}.",
        )

        plants_window.destroy()
        self._view_plants_row(row_index, allow_harvest=True)

    def _use_hand_on_planter(self, hand_side, planter_index, plants_window, row_index):
        """Apply whatever is held in hand_side ('left'/'right') to a planter."""
        hands = ensure_hands(self.player_data)
        item = hands.get(hand_side)
        if not isinstance(item, dict):
            messagebox.showinfo(
                "Empty Hand",
                f"Your {hand_side} hand is empty.",
                parent=plants_window,
            )
            return

        planters = self.player_data["botany"]["planters"]
        if not (0 <= planter_index < len(planters)):
            return
        planter = planters[planter_index]
        item_id = item.get("id")
        item_name = item.get("name", "item")

        def _refresh_and_reopen():
            plants_window.destroy()
            self._view_plants_row(row_index, allow_harvest=True)

        if item_id in BOTANY_SEED_IDS:
            if planter.get("occupied"):
                messagebox.showinfo(
                    "Planter Occupied",
                    f"Planter {planter_index + 1} already has a plant in it. Choose an empty planter.",
                    parent=plants_window,
                )
                return

            attrs = item.get("attributes") or {}
            plant_name = attrs.get("plant_name") or item_name
            growth_class = attrs.get("growth_class") or "crop"
            produces = attrs.get("produces")

            planters[planter_index] = {
                "occupied": True,
                "plant": plant_name,
                "seed_id": item_id,
                "produces": produces,
                "growth_class": growth_class,
                "planted_at_seconds": get_elapsed_seconds(self.player_data),
                "growth_stage": 1,
                "dead": False,
                "watered": False,
                "miracle_grow": 0.0,
                "yield_multiplier": 1,
                "ooze_applied": False,
            }
            hands[hand_side] = None
            add_note(
                self.player_data,
                f"Planted {item_name} in planter {planter_index + 1} using your {hand_side} hand.",
            )
            _refresh_and_reopen()
            return

        if not planter.get("occupied"):
            messagebox.showinfo(
                "Nothing Planted",
                "There is nothing planted in this planter.",
                parent=plants_window,
            )
            return

        if item_id == "watering_can":
            if planter.get("dead"):
                messagebox.showinfo(
                    "Plant Dead",
                    "This plant has died. It needs to be cleared with a Trowel or Chainsaw.",
                    parent=plants_window,
                )
                return
            planter["watered"] = True
            add_note(self.player_data, f"Watered planter {planter_index + 1}.")
            _refresh_and_reopen()
            return

        if item_id in LIQUID_CONSUMABLE_IDS:
            if planter.get("dead"):
                messagebox.showinfo(
                    "Plant Dead",
                    "This plant has died. It needs to be cleared with a Trowel or Chainsaw.",
                    parent=plants_window,
                )
                return

            if item_id == "miracle_grow":
                planter["miracle_grow"] = MIRACLE_GROW_SPEED_BONUS
                add_note(
                    self.player_data,
                    f"Applied Miracle Grow to planter {planter_index + 1}.",
                )
            elif item_id == "plentiful_harvest":
                planter["yield_multiplier"] = PLENTIFUL_HARVEST_YIELD_MULTIPLIER
                add_note(
                    self.player_data,
                    f"Applied Plentiful Harvest to planter {planter_index + 1}.",
                )
            elif item_id == "the_ooze_mutagen":
                planter["ooze_applied"] = True
                add_note(
                    self.player_data,
                    f'Applied "The Ooze" Mutagen to planter {planter_index + 1}.',
                )

            hands[hand_side] = None

            if item_id == "the_ooze_mutagen":
                plants_window.after(
                    10,
                    lambda: messagebox.showinfo(
                        "Mutation", "The Plant does not mutate.", parent=plants_window
                    ),
                )
            _refresh_and_reopen()
            return

        if item_id in TOOL_GROWTH_CLASS_RULES:
            growth_class = planter.get("growth_class")
            if not TOOL_GROWTH_CLASS_RULES[item_id](growth_class):
                wrong_hint = (
                    "Use a Chainsaw on trees."
                    if item_id == "trowel"
                    else "Use a Trowel on non-tree plants."
                )
                messagebox.showinfo(
                    "Wrong Tool",
                    f"The {item_name} can't clear this plant. {wrong_hint}",
                    parent=plants_window,
                )
                return

            if not messagebox.askyesno(
                "Clear Planter",
                f"Clear planter {planter_index + 1} with the {item_name}? "
                "The plant will be lost.",
                parent=plants_window,
            ):
                return

            planters[planter_index] = _empty_planter()
            add_note(
                self.player_data,
                f"Cleared planter {planter_index + 1} with the {item_name}.",
            )
            _refresh_and_reopen()
            return

        messagebox.showinfo(
            "Cannot Use",
            f"The {item_name} can't be used on planters.",
            parent=plants_window,
        )

    def access_botany_station(self):
        """Access the botany station for authorized personnel"""
        clear_button_frame(self.button_frame)

        station_label = tk.Label(
            self.button_frame,
            text="Botany Station Controls",
            font=("Arial", 16, "bold"),
            bg="black",
            fg="white",
        )
        station_label.pack(pady=10)

        vend_btn = tk.Button(
            self.button_frame,
            text="Botany Vending Machine",
            font=("Arial", 14),
            width=22,
            command=self.access_botany_vending,
        )
        vend_btn.pack(pady=10)

        view_btn = tk.Button(
            self.button_frame,
            text="View Plants",
            font=("Arial", 14),
            width=20,
            command=lambda: self.view_plants(allow_harvest=True),
        )
        view_btn.pack(pady=10)

        back_btn = tk.Button(
            self.button_frame,
            text="Back to Station Menu",
            font=("Arial", 14),
            width=20,
            command=self.show_station_menu,
        )
        back_btn.pack(pady=15)

        refocus_window(self.botany_window)

    def access_botany_vending(self, filter_kind="all"):
        """Access the botany vending machine for seeds, liquids, and tools."""
        _panel, vend_window = open_modal_panel(
            self.botany_window, title="Botany Vending Machine"
        )

        # Pack Close first so later content packing does not shift scroll.
        close_btn = tk.Button(
            vend_window,
            text="Close",
            font=("Arial", 14),
            width=15,
            command=vend_window.destroy,
        )
        close_btn.pack(side=tk.BOTTOM, pady=10)

        title_label = tk.Label(
            vend_window,
            text="Botany Vending Machine",
            font=("Arial", 18, "bold"),
            bg="black",
            fg="white",
        )
        title_label.pack(pady=15)

        desc_text = (
            "This machine dispenses seeds, liquids, and tools for the botany lab."
        )
        desc_label = tk.Label(
            vend_window,
            text=desc_text,
            font=("Arial", 12),
            bg="black",
            fg="white",
            wraplength=600,
        )
        desc_label.pack(pady=10)

        filter_frame = tk.Frame(vend_window, bg="black")
        filter_frame.pack(pady=5)

        filter_buttons = {}
        current_filter = {"kind": filter_kind}

        def set_filter(kind):
            current_filter["kind"] = kind
            for key, btn in filter_buttons.items():
                btn.config(relief=tk.SUNKEN if key == kind else tk.RAISED)
            rebuild_available_list(reset_scroll=True)

        for kind, label in (
            ("all", "All"),
            ("seed", "Seeds"),
            ("liquid", "Liquids"),
            ("tool", "Tools"),
        ):
            btn = tk.Button(
                filter_frame,
                text=label,
                font=("Arial", 12),
                width=10,
                command=lambda k=kind: set_filter(k),
            )
            btn.pack(side=tk.LEFT, padx=5)
            filter_buttons[kind] = btn

        filter_buttons[current_filter["kind"]].config(relief=tk.SUNKEN)

        main_frame = tk.Frame(vend_window, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.LabelFrame(
            main_frame, text="Available Items", font=("Arial", 14), bg="black", fg="white"
        )
        left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        left_canvas = tk.Canvas(left_frame, bg="black", highlightthickness=0)
        left_scrollbar = tk.Scrollbar(
            left_frame, orient=tk.VERTICAL, command=left_canvas.yview
        )
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        items_frame = tk.Frame(left_canvas, bg="black")
        left_canvas.create_window((0, 0), window=items_frame, anchor=tk.NW)

        right_frame = tk.LabelFrame(
            main_frame, text="Your Items", font=("Arial", 14), bg="black", fg="white"
        )
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        right_canvas = tk.Canvas(right_frame, bg="black", highlightthickness=0)
        right_scrollbar = tk.Scrollbar(
            right_frame, orient=tk.VERTICAL, command=right_canvas.yview
        )
        right_canvas.configure(yscrollcommand=right_scrollbar.set)

        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        your_items_frame = tk.Frame(right_canvas, bg="black")
        right_canvas.create_window((0, 0), window=your_items_frame, anchor=tk.NW)

        def rebuild_available_list(reset_scroll=False):
            for child in items_frame.winfo_children():
                child.destroy()

            kind = current_filter["kind"]
            for item_id in BOTANY_VEND_IDS:
                item = get_item_definition(item_id)
                if not item:
                    continue
                vend_kinds = (item.get("attributes") or {}).get("vend_kinds") or []
                if kind != "all" and kind not in vend_kinds:
                    continue

                item_frame = tk.Frame(
                    items_frame, bg="#1A3200", bd=1, relief=tk.RIDGE, width=300
                )
                item_frame.pack(fill=tk.X, padx=10, pady=5)

                tk.Label(
                    item_frame,
                    text=item["name"],
                    font=("Arial", 12, "bold"),
                    bg="#1A3200",
                    fg="#00FF00",
                ).pack(anchor="w", padx=10, pady=5)

                tk.Button(
                    item_frame,
                    text="Get Item",
                    font=("Arial", 10),
                    command=lambda iid=item_id: self.get_vending_item(iid, vend_window),
                ).pack(anchor="e", padx=10, pady=5)

            items_frame.update_idletasks()
            left_canvas.config(scrollregion=left_canvas.bbox("all"))
            if reset_scroll:
                left_canvas.yview_moveto(0.0)

        def rebuild_your_items():
            for child in your_items_frame.winfo_children():
                child.destroy()

            inventory_items = self._inventory_vend_items()
            if not inventory_items:
                tk.Label(
                    your_items_frame,
                    text="You don't have any botany items.",
                    font=("Arial", 12),
                    bg="black",
                    fg="white",
                ).pack(pady=20)
            else:
                for _index, inv_item in inventory_items:
                    item_frame = tk.Frame(
                        your_items_frame, bg="#1A3200", bd=1, relief=tk.RIDGE, width=300
                    )
                    item_frame.pack(fill=tk.X, padx=10, pady=5)

                    tk.Label(
                        item_frame,
                        text=format_inventory_label(inv_item),
                        font=("Arial", 12, "bold"),
                        bg="#1A3200",
                        fg="#00FF00",
                    ).pack(anchor="w", padx=10, pady=5)

            your_items_frame.update_idletasks()
            right_canvas.config(scrollregion=right_canvas.bbox("all"))

        # Keep left scroll locked: Get Item only refreshes the right list in place.
        vend_window._rebuild_your_items = rebuild_your_items

        rebuild_available_list(reset_scroll=True)
        rebuild_your_items()

        def on_frame_configure(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        items_frame.bind("<Configure>", lambda e: on_frame_configure(left_canvas))
        your_items_frame.bind("<Configure>", lambda e: on_frame_configure(right_canvas))

        def on_mousewheel(event, canvas):
            widget = vend_window.winfo_containing(event.x_root, event.y_root)
            while widget is not None:
                if widget == left_canvas:
                    left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return
                if widget == right_canvas:
                    right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return
                widget = widget.master

            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        bind_mousewheel(
            vend_window, lambda e: on_mousewheel(e, left_canvas), recursive=True
        )

    def get_vending_item(self, item_id, parent_window):
        """Get an item from the botany vending machine into inventory."""
        item = get_item_definition(item_id)
        if not item:
            return

        add_to_inventory(self.player_data, item)
        add_note(
            self.player_data,
            f"Acquired {item['name']} from the botany vending machine.",
        )

        rebuild_your_items = getattr(parent_window, "_rebuild_your_items", None)
        if callable(rebuild_your_items):
            rebuild_your_items()
            return

        # Fallback if the panel was rebuilt without an in-place refresher.
        parent_window.destroy()
        self.access_botany_vending()
