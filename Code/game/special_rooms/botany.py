import tkinter as tk
from tkinter import messagebox

from game.helper_methods.game_clock import format_elapsed, get_elapsed_seconds
from game.helper_methods.ui_panels import bind_mousewheel, open_modal_panel, refocus_window, schedule_ui_tick
from game.maps.donut import BOTANY_KEY
from game.objects.botany_items import (
    BOTANY_SEED_IDS,
    GROWTH_STAGES,
    growth_seconds_to_next_stage,
    growth_stage_label,
    refresh_planter_growth,
)
from game.objects.items import (
    add_to_inventory,
    format_inventory_label,
    get_item_definition,
    remove_one_from_inventory,
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


def _empty_planter():
    return {
        "occupied": False,
        "plant": None,
        "seed_id": None,
        "produces": None,
        "growth_class": None,
        "planted_at_seconds": None,
        "growth_stage": 0,
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

    def _inventory_seeds(self):
        """Return (inventory_index, item) pairs for botany seeds in inventory."""
        seeds = []
        for index, item in enumerate(self.player_data.get("inventory", []) or []):
            if isinstance(item, dict) and item.get("id") in BOTANY_SEED_IDS:
                seeds.append((index, item))
        return seeds

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
            font=("Arial", 18, "bold"),
            bg="black",
            fg="white",
        ).pack(pady=15)

        tk.Label(
            plants_window,
            text="You observe the plants growing in this hydroponic row.",
            font=("Arial", 12),
            bg="black",
            fg="white",
            wraplength=500,
        ).pack(pady=10)

        planters_frame = tk.Frame(plants_window, bg="black")
        planters_frame.pack(pady=20, fill=tk.BOTH, expand=True)

        # Live-updating widgets for occupied planters in this row.
        live_rows = []

        for i in range(start, end):
            planter = planters[i]
            planter_frame = tk.Frame(planters_frame, bg="#222222", bd=2, relief=tk.RIDGE, width=500)
            planter_frame.pack(fill=tk.X, padx=20, pady=5)

            if planter["occupied"]:
                tk.Label(
                    planter_frame,
                    text=f"Planter {i + 1}: {planter['plant']}",
                    font=("Arial", 14, "bold"),
                    bg="#222222",
                    fg="light green",
                ).pack(anchor="w", padx=10, pady=5)
                stage_label = tk.Label(
                    planter_frame,
                    text="",
                    font=("Arial", 12),
                    bg="#222222",
                    fg="white",
                )
                stage_label.pack(anchor="w", padx=10, pady=5)
                time_label = tk.Label(
                    planter_frame,
                    text="",
                    font=("Arial", 11),
                    bg="#222222",
                    fg="cyan",
                )
                time_label.pack(anchor="w", padx=10, pady=5)
                harvest_slot = tk.Frame(planter_frame, bg="#222222")
                harvest_slot.pack(anchor="e", padx=10, pady=5)
                live_rows.append(
                    {
                        "index": i,
                        "stage_label": stage_label,
                        "time_label": time_label,
                        "harvest_slot": harvest_slot,
                        "harvest_btn": None,
                    }
                )
            else:
                tk.Label(
                    planter_frame,
                    text=f"Planter {i + 1}: Empty",
                    font=("Arial", 14, "bold"),
                    bg="#222222",
                    fg="white",
                ).pack(anchor="w", padx=10, pady=5)
                tk.Label(
                    planter_frame,
                    text="This planter is ready for seeds.",
                    font=("Arial", 12),
                    bg="#222222",
                    fg="white",
                ).pack(anchor="w", padx=10, pady=5)

        def _ensure_harvest_button(row):
            if row["harvest_btn"] is not None:
                return
            idx = row["index"]
            btn = tk.Button(
                row["harvest_slot"],
                text="Harvest",
                font=("Arial", 11),
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

        def _refresh_live_labels():
            elapsed_seconds = get_elapsed_seconds(self.player_data)
            for row in live_rows:
                planter = planters[row["index"]]
                if not planter.get("occupied"):
                    row["stage_label"].config(text="Empty")
                    row["time_label"].config(text="", fg="gray")
                    _clear_harvest_button(row)
                    continue

                growth_stage = refresh_planter_growth(planter, elapsed_seconds)
                growth_text = growth_stage_label(growth_stage)
                row["stage_label"].config(
                    text=f"Stage: {growth_text} ({growth_stage}/{GROWTH_STAGES})"
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
                    )
                    row["time_label"].config(
                        text=f"Next stage in {format_elapsed(next_in)}",
                        fg="cyan",
                    )
                    _clear_harvest_button(row)

        _refresh_live_labels()
        cancel_tick["fn"] = schedule_ui_tick(plants_window, _refresh_live_labels)

        def back_to_row_picker():
            panel.close()
            self.view_plants(allow_harvest=allow_harvest)

        tk.Button(
            plants_window,
            text="Back",
            font=("Arial", 14),
            width=15,
            command=back_to_row_picker,
        ).pack(pady=20)

    def _harvest_planter(self, planter_index, plants_window, row_index, allow_harvest=True):
        """Harvest a mature planter into inventory and clear it (station View Plants only)."""
        if not allow_harvest:
            return

        planters = self.player_data["botany"]["planters"]
        if not (0 <= planter_index < len(planters)):
            return

        planter = planters[planter_index]
        if not planter.get("occupied"):
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

        add_to_inventory(self.player_data, produce)
        plant_name = planter.get("plant") or produce.get("name", "produce")
        planters[planter_index] = _empty_planter()
        add_note(
            self.player_data,
            f"Harvested {produce.get('name', plant_name)} from planter {planter_index + 1}.",
        )

        plants_window.destroy()
        self._view_plants_row(row_index, allow_harvest=True)

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

        seeds_btn = tk.Button(
            self.button_frame, text="Seed Machine", font=("Arial", 14), width=20, command=self.access_seed_machine
        )
        seeds_btn.pack(pady=10)

        view_btn = tk.Button(
            self.button_frame,
            text="View Plants",
            font=("Arial", 14),
            width=20,
            command=lambda: self.view_plants(allow_harvest=True),
        )
        view_btn.pack(pady=10)

        plant_btn = tk.Button(
            self.button_frame, text="Plant Seeds", font=("Arial", 14), width=20, command=self.plant_seeds
        )
        plant_btn.pack(pady=10)

        back_btn = tk.Button(
            self.button_frame,
            text="Back to Station Menu",
            font=("Arial", 14),
            width=20,
            command=self.show_station_menu,
        )
        back_btn.pack(pady=15)

        refocus_window(self.botany_window)

    def access_seed_machine(self):
        """Access the seed machine to get seeds"""
        _panel, seed_window = open_modal_panel(self.botany_window, title="Seed Machine")
        title_label = tk.Label(
            seed_window, text="Botanical Seed Dispenser", font=("Arial", 18, "bold"), bg="black", fg="white"
        )
        title_label.pack(pady=15)

        desc_text = "This machine dispenses seeds for cultivation in the botany lab's planters."
        desc_label = tk.Label(
            seed_window, text=desc_text, font=("Arial", 12), bg="black", fg="white", wraplength=600
        )
        desc_label.pack(pady=10)

        main_frame = tk.Frame(seed_window, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.LabelFrame(main_frame, text="Available Seeds", font=("Arial", 14), bg="black", fg="white")
        left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        left_canvas = tk.Canvas(left_frame, bg="black", highlightthickness=0)
        left_scrollbar = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        seeds_frame = tk.Frame(left_canvas, bg="black")
        left_canvas.create_window((0, 0), window=seeds_frame, anchor=tk.NW)

        right_frame = tk.LabelFrame(main_frame, text="Your Seeds", font=("Arial", 14), bg="black", fg="white")
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        right_canvas = tk.Canvas(right_frame, bg="black", highlightthickness=0)
        right_scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL, command=right_canvas.yview)
        right_canvas.configure(yscrollcommand=right_scrollbar.set)

        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        your_seeds_frame = tk.Frame(right_canvas, bg="black")
        right_canvas.create_window((0, 0), window=your_seeds_frame, anchor=tk.NW)

        for seed_id in BOTANY_SEED_IDS:
            seed = get_item_definition(seed_id)
            if not seed:
                continue
            seed_frame = tk.Frame(seeds_frame, bg="#1A3200", bd=1, relief=tk.RIDGE, width=300)
            seed_frame.pack(fill=tk.X, padx=10, pady=5)

            tk.Label(
                seed_frame, text=seed["name"], font=("Arial", 12, "bold"), bg="#1A3200", fg="#00FF00"
            ).pack(anchor="w", padx=10, pady=5)

            tk.Button(
                seed_frame,
                text="Get Seeds",
                font=("Arial", 10),
                command=lambda sid=seed_id: self.get_seeds(sid, seed_window),
            ).pack(anchor="e", padx=10, pady=5)

        inventory_seeds = self._inventory_seeds()
        if not inventory_seeds:
            tk.Label(
                your_seeds_frame,
                text="You don't have any seeds.",
                font=("Arial", 12),
                bg="black",
                fg="white",
            ).pack(pady=20)
        else:
            for _index, seed in inventory_seeds:
                seed_frame = tk.Frame(your_seeds_frame, bg="#1A3200", bd=1, relief=tk.RIDGE, width=300)
                seed_frame.pack(fill=tk.X, padx=10, pady=5)

                tk.Label(
                    seed_frame,
                    text=format_inventory_label(seed),
                    font=("Arial", 12, "bold"),
                    bg="#1A3200",
                    fg="#00FF00",
                ).pack(anchor="w", padx=10, pady=5)

        seeds_frame.update_idletasks()
        left_canvas.config(scrollregion=left_canvas.bbox("all"))

        your_seeds_frame.update_idletasks()
        right_canvas.config(scrollregion=right_canvas.bbox("all"))

        left_canvas.yview_moveto(0.0)

        def on_frame_configure(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        seeds_frame.bind("<Configure>", lambda e: on_frame_configure(left_canvas))
        your_seeds_frame.bind("<Configure>", lambda e: on_frame_configure(right_canvas))

        def on_mousewheel(event, canvas):
            widget = seed_window.winfo_containing(event.x_root, event.y_root)
            while widget is not None:
                if widget == left_canvas:
                    left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return
                if widget == right_canvas:
                    right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return
                widget = widget.master

            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        bind_mousewheel(seed_window, lambda e: on_mousewheel(e, left_canvas), recursive=True)

        close_btn = tk.Button(seed_window, text="Close", font=("Arial", 14), width=15, command=seed_window.destroy)
        close_btn.pack(side=tk.BOTTOM, pady=10)

    def get_seeds(self, seed_id, parent_window):
        """Get seeds from the seed machine into inventory."""
        seed = get_item_definition(seed_id)
        if not seed:
            return

        add_to_inventory(self.player_data, seed)
        add_note(self.player_data, f"Acquired {seed['name']} from the botany seed dispenser.")

        parent_window.destroy()
        self.access_seed_machine()

    def plant_seeds(self):
        """Pick a hydroponic row, then plant seeds into that row's planters."""
        self._show_row_picker("Plant Seeds", self._plant_seeds_row)

    def _plant_seeds_row(self, row_index):
        start = row_index * PLANTERS_PER_ROW
        end = start + PLANTERS_PER_ROW
        content_width = 600
        seeds_viewport_height = 250  # ~4–5 seed rows

        _panel, plant_window = open_modal_panel(
            self.botany_window, title=f"Plant Seeds — Row {row_index + 1}"
        )
        plant_window.configure(bg="black")

        # Centered column that fills the modal height.
        column = tk.Frame(plant_window, bg="black", width=content_width)
        column.place(relx=0.5, rely=0, relheight=1, anchor="n")
        column.place_configure(width=content_width)

        # --- Bottom chrome (pack first so it stays pinned) ---
        button_frame = tk.Frame(column, bg="black")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 20))

        planters_frame = tk.LabelFrame(
            column, text="Available Planters", font=("Arial", 14), bg="black", fg="white"
        )
        planters_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5, 5))

        # --- Top header ---
        tk.Label(
            column,
            text=f"Plant Seeds — Row {row_index + 1}",
            font=("Arial", 18, "bold"),
            bg="black",
            fg="white",
        ).pack(side=tk.TOP, pady=(15, 5))

        tk.Label(
            column,
            text="Select a seed to plant and an empty planter to place it in.",
            font=("Arial", 12),
            bg="black",
            fg="white",
            wraplength=content_width - 40,
            justify=tk.CENTER,
        ).pack(side=tk.TOP, pady=(0, 10))

        # --- Scrollable seeds (fills remaining space, fixed viewport height) ---
        seeds_outer = tk.LabelFrame(
            column, text="Your Seeds", font=("Arial", 14), bg="black", fg="white"
        )
        seeds_outer.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        seeds_canvas = tk.Canvas(
            seeds_outer,
            bg="black",
            highlightthickness=0,
            height=seeds_viewport_height,
        )
        seeds_scrollbar = tk.Scrollbar(
            seeds_outer, orient=tk.VERTICAL, command=seeds_canvas.yview
        )
        seeds_canvas.configure(yscrollcommand=seeds_scrollbar.set)
        seeds_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        seeds_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)

        seeds_list = tk.Frame(seeds_canvas, bg="black")
        seeds_canvas_window = seeds_canvas.create_window((0, 0), window=seeds_list, anchor="nw")

        def _sync_seeds_scroll(_event=None):
            seeds_canvas.configure(scrollregion=seeds_canvas.bbox("all"))
            canvas_width = seeds_canvas.winfo_width()
            if canvas_width > 1:
                seeds_canvas.itemconfig(seeds_canvas_window, width=canvas_width)

        seeds_list.bind("<Configure>", _sync_seeds_scroll)
        seeds_canvas.bind("<Configure>", _sync_seeds_scroll)

        selected_data = {"inv_index": None, "planter": None}
        seed_buttons = []
        planter_buttons = []

        def select_seed(inv_index, button):
            for btn in seed_buttons:
                btn.config(bg="#1A3200")
            button.config(bg="#006600")
            selected_data["inv_index"] = inv_index
            if selected_data["planter"] is not None:
                plant_btn.config(state=tk.NORMAL)

        def select_planter(index, button):
            if self.player_data["botany"]["planters"][index]["occupied"]:
                messagebox.showinfo(
                    "Planter Occupied",
                    f"Planter {index + 1} already has a plant in it. Choose an empty planter.",
                    parent=plant_window,
                )
                return

            for btn in planter_buttons:
                btn.config(bg="#222222")
            button.config(bg="#006600")
            selected_data["planter"] = index
            if selected_data["inv_index"] is not None:
                plant_btn.config(state=tk.NORMAL)

        def rebuild_seed_list():
            for widget in seeds_list.winfo_children():
                widget.destroy()
            seed_buttons.clear()
            selected_data["inv_index"] = None

            inventory_seeds = self._inventory_seeds()
            if not inventory_seeds:
                tk.Label(
                    seeds_list,
                    text="No seeds in inventory.",
                    font=("Arial", 12),
                    bg="black",
                    fg="gray",
                ).pack(pady=10)
                _sync_seeds_scroll()
                return

            for inv_index, seed in inventory_seeds:
                seed_frame = tk.Frame(seeds_list, bg="#1A3200", bd=1, relief=tk.RIDGE)
                seed_frame.pack(fill=tk.X, padx=10, pady=5)

                tk.Label(
                    seed_frame,
                    text=format_inventory_label(seed),
                    font=("Arial", 12, "bold"),
                    bg="#1A3200",
                    fg="#00FF00",
                ).pack(side=tk.LEFT, padx=10, pady=5)

                tk.Button(
                    seed_frame,
                    text="Select",
                    font=("Arial", 10),
                    bg="#333333",
                    command=lambda idx=inv_index, b=seed_frame: select_seed(idx, b),
                ).pack(side=tk.RIGHT, padx=10, pady=5)
                seed_buttons.append(seed_frame)

            _sync_seeds_scroll()
            seeds_canvas.yview_moveto(0.0)

        def rebuild_planter_list():
            for widget in planters_frame.winfo_children():
                widget.destroy()
            planter_buttons.clear()
            selected_data["planter"] = None

            planters = self.player_data["botany"]["planters"]
            for i in range(start, end):
                planter = planters[i]
                planter_frame = tk.Frame(planters_frame, bg="#222222", bd=2, relief=tk.RIDGE)
                planter_frame.pack(fill=tk.X, padx=10, pady=6)

                if planter["occupied"]:
                    tk.Label(
                        planter_frame,
                        text=f"Planter {i + 1}: {planter['plant']}",
                        font=("Arial", 14, "bold"),
                        bg="#222222",
                        fg="light green",
                    ).pack(side=tk.LEFT, padx=10, pady=5)
                    tk.Label(
                        planter_frame,
                        text="OCCUPIED",
                        font=("Arial", 12),
                        bg="#222222",
                        fg="red",
                    ).pack(side=tk.RIGHT, padx=10, pady=5)
                else:
                    tk.Label(
                        planter_frame,
                        text=f"Planter {i + 1}: Empty",
                        font=("Arial", 14, "bold"),
                        bg="#222222",
                        fg="white",
                    ).pack(side=tk.LEFT, padx=10, pady=5)
                    tk.Button(
                        planter_frame,
                        text="Select",
                        font=("Arial", 10),
                        bg="#333333",
                        command=lambda idx=i, b=planter_frame: select_planter(idx, b),
                    ).pack(side=tk.RIGHT, padx=10, pady=5)
                planter_buttons.append(planter_frame)

        def do_planting():
            if selected_data["inv_index"] is None or selected_data["planter"] is None:
                return

            inv_index = selected_data["inv_index"]
            planter_index = selected_data["planter"]
            inventory = self.player_data.get("inventory", [])
            if not (0 <= inv_index < len(inventory)):
                rebuild_seed_list()
                plant_btn.config(state=tk.DISABLED)
                return

            seed = inventory[inv_index]
            if not isinstance(seed, dict) or seed.get("id") not in BOTANY_SEED_IDS:
                rebuild_seed_list()
                plant_btn.config(state=tk.DISABLED)
                return

            attrs = seed.get("attributes") or {}
            plant_name = attrs.get("plant_name") or seed.get("name", "Plant")
            growth_class = attrs.get("growth_class") or "crop"
            produces = attrs.get("produces")

            self.player_data["botany"]["planters"][planter_index] = {
                "occupied": True,
                "plant": plant_name,
                "seed_id": seed.get("id"),
                "produces": produces,
                "growth_class": growth_class,
                "planted_at_seconds": get_elapsed_seconds(self.player_data),
                "growth_stage": 1,
            }

            remove_one_from_inventory(self.player_data, inv_index)
            add_note(
                self.player_data,
                f"Planted {seed.get('name', plant_name)} in planter {planter_index + 1}.",
            )

            rebuild_seed_list()
            rebuild_planter_list()
            plant_btn.config(state=tk.DISABLED)

        plant_btn = tk.Button(
            button_frame,
            text="Plant Seed",
            font=("Arial", 14),
            width=15,
            command=do_planting,
            state=tk.DISABLED,
        )
        plant_btn.pack(side=tk.LEFT, expand=True, padx=20)

        def cancel_to_row_picker():
            plant_window.destroy()
            self.plant_seeds()

        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 14),
            width=15,
            command=cancel_to_row_picker,
        )
        cancel_btn.pack(side=tk.LEFT, expand=True, padx=20)

        rebuild_seed_list()
        rebuild_planter_list()

        def on_seeds_mousewheel(event):
            seeds_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        bind_mousewheel(seeds_outer, on_seeds_mousewheel, recursive=True)
