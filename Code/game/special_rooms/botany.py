import tkinter as tk
from tkinter import messagebox

from game.special_rooms.shared import (
    SpecialRoomBase,
    add_note,
    build_npc_contact_section,
    clear_button_frame,
)
from game.helper_methods.ui_panels import bind_mousewheel, open_modal_panel, refocus_window
from game.maps.donut import BOTANY_KEY


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
                "planters": [
                    {"occupied": False, "plant": None, "growth_stage": 0},
                    {"occupied": False, "plant": None, "growth_stage": 0},
                    {"occupied": False, "plant": None, "growth_stage": 0},
                    {"occupied": False, "plant": None, "growth_stage": 0},
                ],
                "seeds": [],
            }

        self.available_seeds = [
            {"name": "Tomato Seeds", "description": "Grows into juicy red tomatoes."},
            {"name": "Potato Seeds", "description": "Produces starchy potatoes."},
            {"name": "Wheat Seeds", "description": "Grows into tall wheat stalks."},
            {"name": "Carrot Seeds", "description": "Produces orange root vegetables."},
            {"name": "Apple Seeds", "description": "Grows into small apple trees."},
        ]

    def station_entries(self):
        return [{
            "label": "Enter Botany Station",
            "command": self.access_botany_station,
        }]

    def show_room_options(self):
        clear_button_frame(self.button_frame)

        view_plants_btn = tk.Button(
            self.button_frame, text="View Plants", font=("Arial", 14), width=20, command=self.view_plants
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

    def view_plants(self):
        """View the plants in the botany lab"""
        _panel, plants_window = open_modal_panel(self.botany_window, title="Viewing Plants")
        title_label = tk.Label(plants_window, text="Botany Lab Plants", font=("Arial", 18, "bold"), bg="black", fg="white")
        title_label.pack(pady=15)
        
        desc_text = "You observe the various plants growing in the hydroponic planters."
        desc_label = tk.Label(plants_window, text=desc_text, font=("Arial", 12), bg="black", fg="white", wraplength=500)
        desc_label.pack(pady=10)
        
        planters_frame = tk.Frame(plants_window, bg="black")
        planters_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        
        planters = self.player_data["botany"]["planters"]
        for i, planter in enumerate(planters):
            planter_frame = tk.Frame(planters_frame, bg="#222222", bd=2, relief=tk.RIDGE, width=500)
            planter_frame.pack(fill=tk.X, padx=20, pady=5)
            
            if planter["occupied"]:
                plant_name = planter["plant"]
                growth_stage = planter["growth_stage"]
                growth_text = "Seedling" if growth_stage < 3 else "Growing" if growth_stage < 6 else "Mature"
                
                name_label = tk.Label(planter_frame, text=f"Planter {i+1}: {plant_name}", 
                                    font=("Arial", 14, "bold"), bg="#222222", fg="light green")
                name_label.pack(anchor="w", padx=10, pady=5)
                
                stage_label = tk.Label(planter_frame, text=f"Stage: {growth_text} ({growth_stage}/10)", 
                                     font=("Arial", 12), bg="#222222", fg="white")
                stage_label.pack(anchor="w", padx=10, pady=5)
            else:
                name_label = tk.Label(planter_frame, text=f"Planter {i+1}: Empty", 
                                    font=("Arial", 14, "bold"), bg="#222222", fg="white")
                name_label.pack(anchor="w", padx=10, pady=5)
                
                empty_label = tk.Label(planter_frame, text="This planter is ready for seeds.", 
                                    font=("Arial", 12), bg="#222222", fg="white")
                empty_label.pack(anchor="w", padx=10, pady=5)
        
        close_btn = tk.Button(plants_window, text="Close", font=("Arial", 14), width=15, command=plants_window.destroy)
        close_btn.pack(pady=20)
    
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
            self.button_frame, text="View Plants", font=("Arial", 14), width=20, command=self.view_plants
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
        title_label = tk.Label(seed_window, text="Botanical Seed Dispenser", font=("Arial", 18, "bold"), bg="black", fg="white")
        title_label.pack(pady=15)
        
        desc_text = "This machine dispenses seeds for cultivation in the botany lab's planters."
        desc_label = tk.Label(seed_window, text=desc_text, font=("Arial", 12), bg="black", fg="white", wraplength=600)
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
        
        for i, seed in enumerate(self.available_seeds):
            seed_frame = tk.Frame(seeds_frame, bg="#1A3200", bd=1, relief=tk.RIDGE, width=300)
            seed_frame.pack(fill=tk.X, padx=10, pady=5)
            
            name_label = tk.Label(seed_frame, text=seed["name"], font=("Arial", 12, "bold"), bg="#1A3200", fg="#00FF00")
            name_label.pack(anchor="w", padx=10, pady=5)
            
            desc_label = tk.Label(seed_frame, text=seed["description"], font=("Arial", 10), bg="#1A3200", fg="white", wraplength=250)
            desc_label.pack(anchor="w", padx=10, pady=5)
            
            get_btn = tk.Button(seed_frame, text="Get Seeds", font=("Arial", 10), 
                             command=lambda s=seed: self.get_seeds(s, seed_window))
            get_btn.pack(anchor="e", padx=10, pady=5)
        
        if not self.player_data["botany"]["seeds"]:
            empty_label = tk.Label(your_seeds_frame, text="You don't have any seeds.", font=("Arial", 12), bg="black", fg="white")
            empty_label.pack(pady=20)
        else:
            for seed in self.player_data["botany"]["seeds"]:
                seed_frame = tk.Frame(your_seeds_frame, bg="#1A3200", bd=1, relief=tk.RIDGE, width=300)
                seed_frame.pack(fill=tk.X, padx=10, pady=5)
                
                name_label = tk.Label(seed_frame, text=seed["name"], font=("Arial", 12, "bold"), bg="#1A3200", fg="#00FF00")
                name_label.pack(anchor="w", padx=10, pady=5)
                
                desc_label = tk.Label(seed_frame, text=seed["description"], font=("Arial", 10), bg="#1A3200", fg="white", wraplength=250)
                desc_label.pack(anchor="w", padx=10, pady=5)
        
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
                elif widget == right_canvas:
                    right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return
                widget = widget.master
            
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        bind_mousewheel(seed_window, lambda e: on_mousewheel(e, left_canvas))

        close_btn = tk.Button(seed_window, text="Close", font=("Arial", 14), width=15, command=seed_window.destroy)
        close_btn.pack(side=tk.BOTTOM, pady=10)
    
    def get_seeds(self, seed, parent_window):
        """Get seeds from the seed machine"""
        self.player_data["botany"]["seeds"].append(seed)
        
        add_note(self.player_data, f"Acquired {seed['name']} from the botany seed dispenser.")
        
        parent_window.destroy()
        self.access_seed_machine()
    
    def plant_seeds(self):
        """Plant seeds in the planters"""
        if not self.player_data["botany"]["seeds"]:
            self.botany_window.after(10, lambda: messagebox.showinfo("No Seeds", 
                                                              "You don't have any seeds to plant. Get some from the seed machine first.", 
                                                              parent=self.botany_window))
            return
        
        _panel, plant_window = open_modal_panel(self.botany_window, title="Plant Seeds")
        main_canvas = tk.Canvas(plant_window, bg="black", highlightthickness=0)
        scrollbar = tk.Scrollbar(plant_window, orient="vertical", command=main_canvas.yview)
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        content_frame = tk.Frame(main_canvas, bg="black")
        canvas_frame = main_canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        title_label = tk.Label(content_frame, text="Plant Seeds", font=("Arial", 18, "bold"), bg="black", fg="white")
        title_label.pack(pady=15)
        
        desc_text = "Select a seed to plant and an empty planter to place it in."
        desc_label = tk.Label(content_frame, text=desc_text, font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        seeds_frame = tk.LabelFrame(content_frame, text="Your Seeds", font=("Arial", 14), bg="black", fg="white")
        seeds_frame.pack(padx=20, pady=10, fill=tk.X)
        
        selected_data = {"seed": None, "planter": None}
        
        def select_seed(seed, button):
            for btn in seed_buttons:
                btn.config(bg="#333333")
            
            button.config(bg="#006600")
            
            selected_data["seed"] = seed
            
            if selected_data["planter"] is not None:
                plant_btn.config(state=tk.NORMAL)
        
        def select_planter(index, button):
            if self.player_data["botany"]["planters"][index]["occupied"]:
                messagebox.showinfo("Planter Occupied", 
                                   f"Planter {index+1} already has a plant in it. Choose an empty planter.", 
                                   parent=plant_window)
                return
            
            for btn in planter_buttons:
                btn.config(bg="#333333")
            
            button.config(bg="#006600")
            
            selected_data["planter"] = index
            
            if selected_data["seed"] is not None:
                plant_btn.config(state=tk.NORMAL)
        
        seed_buttons = []
        for i, seed in enumerate(self.player_data["botany"]["seeds"]):
            seed_frame = tk.Frame(seeds_frame, bg="#1A3200", bd=1, relief=tk.RIDGE)
            seed_frame.pack(fill=tk.X, padx=10, pady=5)
            
            name_label = tk.Label(seed_frame, text=seed["name"], font=("Arial", 12, "bold"), bg="#1A3200", fg="#00FF00")
            name_label.pack(side=tk.LEFT, padx=10, pady=5)
            
            select_btn = tk.Button(seed_frame, text="Select", font=("Arial", 10), bg="#333333",
                                command=lambda s=seed, b=seed_frame: select_seed(s, b))
            select_btn.pack(side=tk.RIGHT, padx=10, pady=5)
            seed_buttons.append(seed_frame)
        
        planters_frame = tk.LabelFrame(content_frame, text="Available Planters", font=("Arial", 14), bg="black", fg="white")
        planters_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        planter_buttons = []
        for i, planter in enumerate(self.player_data["botany"]["planters"]):
            planter_frame = tk.Frame(planters_frame, bg="#222222", bd=2, relief=tk.RIDGE)
            planter_frame.pack(fill=tk.X, padx=20, pady=10)
            
            if planter["occupied"]:
                name_label = tk.Label(planter_frame, text=f"Planter {i+1}: {planter['plant']}", 
                                    font=("Arial", 14, "bold"), bg="#222222", fg="light green")
                name_label.pack(side=tk.LEFT, padx=10, pady=5)
                
                status_label = tk.Label(planter_frame, text="OCCUPIED", 
                                      font=("Arial", 12), bg="#222222", fg="red")
                status_label.pack(side=tk.RIGHT, padx=10, pady=5)
            else:
                name_label = tk.Label(planter_frame, text=f"Planter {i+1}: Empty", 
                                    font=("Arial", 14, "bold"), bg="#222222", fg="white")
                name_label.pack(side=tk.LEFT, padx=10, pady=5)
                
                select_btn = tk.Button(planter_frame, text="Select", font=("Arial", 10), bg="#333333",
                                    command=lambda idx=i, b=planter_frame: select_planter(idx, b))
                select_btn.pack(side=tk.RIGHT, padx=10, pady=5)
            planter_buttons.append(planter_frame)
        
        def do_planting():
            if selected_data["seed"] is None or selected_data["planter"] is None:
                return
            
            seed = selected_data["seed"]
            planter_index = selected_data["planter"]
            
            self.player_data["botany"]["planters"][planter_index] = {
                "occupied": True,
                "plant": seed["name"],
                "growth_stage": 1  # Start at stage 1
            }
            
            self.player_data["botany"]["seeds"].remove(seed)
            
            add_note(self.player_data, f"Planted {seed['name']} in planter {planter_index+1}.")
            
            for btn in seed_buttons:
                btn.destroy()
            
            for btn in planter_buttons:
                btn.destroy()
                
            seed_buttons.clear()
            planter_buttons.clear()
            selected_data["seed"] = None
            selected_data["planter"] = None
            
            for i, seed in enumerate(self.player_data["botany"]["seeds"]):
                seed_frame = tk.Frame(seeds_frame, bg="#1A3200", bd=1, relief=tk.RIDGE)
                seed_frame.pack(fill=tk.X, padx=10, pady=5)
                
                name_label = tk.Label(seed_frame, text=seed["name"], font=("Arial", 12, "bold"), bg="#1A3200", fg="#00FF00")
                name_label.pack(side=tk.LEFT, padx=10, pady=5)
                
                select_btn = tk.Button(seed_frame, text="Select", font=("Arial", 10), bg="#333333",
                                    command=lambda s=seed, b=seed_frame: select_seed(s, b))
                select_btn.pack(side=tk.RIGHT, padx=10, pady=5)
                seed_buttons.append(seed_frame)
            
            for i, planter in enumerate(self.player_data["botany"]["planters"]):
                planter_frame = tk.Frame(planters_frame, bg="#222222", bd=2, relief=tk.RIDGE)
                planter_frame.pack(fill=tk.X, padx=20, pady=10)
                
                if planter["occupied"]:
                    name_label = tk.Label(planter_frame, text=f"Planter {i+1}: {planter['plant']}", 
                                        font=("Arial", 14, "bold"), bg="#222222", fg="light green")
                    name_label.pack(side=tk.LEFT, padx=10, pady=5)
                    
                    status_label = tk.Label(planter_frame, text="OCCUPIED", 
                                          font=("Arial", 12), bg="#222222", fg="red")
                    status_label.pack(side=tk.RIGHT, padx=10, pady=5)
                else:
                    name_label = tk.Label(planter_frame, text=f"Planter {i+1}: Empty", 
                                        font=("Arial", 14, "bold"), bg="#222222", fg="white")
                    name_label.pack(side=tk.LEFT, padx=10, pady=5)
                    
                    select_btn = tk.Button(planter_frame, text="Select", font=("Arial", 10), bg="#333333",
                                        command=lambda idx=i, b=planter_frame: select_planter(idx, b))
                    select_btn.pack(side=tk.RIGHT, padx=10, pady=5)
                planter_buttons.append(planter_frame)
            
            content_frame.update_idletasks()
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            
            plant_btn.config(state=tk.DISABLED)
        
        button_frame = tk.Frame(content_frame, bg="black")
        button_frame.pack(pady=20)
        
        plant_btn = tk.Button(button_frame, text="Plant Seed", font=("Arial", 14), width=15, 
                           command=do_planting, state=tk.DISABLED)
        plant_btn.pack(side=tk.LEFT, padx=20)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", font=("Arial", 14), width=15, 
                            command=plant_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=20)
        
        def configure_scroll_region(event):
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            
        content_frame.bind("<Configure>", configure_scroll_region)
        
        def on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        main_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        content_frame.update_idletasks()
        main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        
        def adjust_canvas_frame(event):
            canvas_width = event.width
            main_canvas.itemconfig(canvas_frame, width=canvas_width)
            
        main_canvas.bind("<Configure>", adjust_canvas_frame)
