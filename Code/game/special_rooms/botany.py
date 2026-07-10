import tkinter as tk
from tkinter import messagebox
import random

from game.helper_methods.door_control import can_control_door, toggle_door_lock as toggle_room_door_lock
from game.objects.items import ItemInventoryMixin
from game.special_rooms.shared import (
    add_note,
    build_npc_contact_section,
    build_room_shell,
    open_room_in_main_window,
    pack_character_sheet_button,
    try_leave_through_door,
    show_station_menu as render_station_menu,
)
from game.helper_methods.ui_panels import open_modal_panel
from game.maps.donut import BOTANY_KEY as DOOR_KEY

class Botany(ItemInventoryMixin):
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        # Initialize botany data if it doesn't exist
        if "botany" not in self.player_data:
            self.player_data["botany"] = {
                "planters": [
                    {"occupied": False, "plant": None, "growth_stage": 0},
                    {"occupied": False, "plant": None, "growth_stage": 0},
                    {"occupied": False, "plant": None, "growth_stage": 0},
                    {"occupied": False, "plant": None, "growth_stage": 0}
                ],
                "seeds": []
            }

        # Available seeds in the seed machine
        self.available_seeds = [
            {"name": "Tomato Seeds", "description": "Grows into juicy red tomatoes."},
            {"name": "Potato Seeds", "description": "Produces starchy potatoes."},
            {"name": "Wheat Seeds", "description": "Grows into tall wheat stalks."},
            {"name": "Carrot Seeds", "description": "Produces orange root vegetables."},
            {"name": "Apple Seeds", "description": "Grows into small apple trees."}
        ]

        self.botany_window = open_room_in_main_window(
            parent_window, "Botany Lab", player_data, station_crew, return_callback
        )
        self.root = self.botany_window
        _, self.button_frame = build_room_shell(
            self.botany_window,
            self.player_data,
            "Station Botany Lab",
            "The botany lab is filled with plants of all varieties. Hydroponic systems line the walls, and bright grow lights illuminate rows of planters. The air is humid and smells of fresh soil and vegetation.",
        )

        self._build_station_menu()

        pack_character_sheet_button(self.botany_window, self.player_data, self)

        # Exit button
        exit_btn = tk.Button(self.botany_window, text="Exit Room", font=("Arial", 14), width=15, command=self.on_closing)
        exit_btn.pack(pady=20)

    def add_note(self, text):
        add_note(self.player_data, text)
    
    def show_room_options(self):
        """Show regular room options that all players can access"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # View plants option
        view_plants_btn = tk.Button(self.button_frame, text="View Plants", font=("Arial", 14), width=20, command=self.view_plants)
        view_plants_btn.pack(pady=10)

        # Talk to botanist option (or "Call" them if they've stepped away)
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

        if can_control_door(self.player_data, DOOR_KEY):
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)

    def talk_to_botanist(self):
        self.botany_window.after(
            10,
            lambda: messagebox.showinfo(
                "Botanist",
                "The botanist continues tending to the plants without looking up.",
                parent=self.botany_window,
            ),
        )
        self.botany_window.after(20, self.botany_window.lift)
        self.botany_window.focus_force()

    def view_plants(self):
        """View the plants in the botany lab"""
        # Create a new top-level window for viewing plants
        _panel, plants_window = open_modal_panel(self.botany_window, title="Viewing Plants")
        # Title
        title_label = tk.Label(plants_window, text="Botany Lab Plants", font=("Arial", 18, "bold"), bg="black", fg="white")
        title_label.pack(pady=15)
        
        # Description
        desc_text = "You observe the various plants growing in the hydroponic planters."
        desc_label = tk.Label(plants_window, text=desc_text, font=("Arial", 12), bg="black", fg="white", wraplength=500)
        desc_label.pack(pady=10)
        
        # Create a frame for the planters
        planters_frame = tk.Frame(plants_window, bg="black")
        planters_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        
        # Show the current state of each planter
        planters = self.player_data["botany"]["planters"]
        for i, planter in enumerate(planters):
            planter_frame = tk.Frame(planters_frame, bg="#222222", bd=2, relief=tk.RIDGE, width=500)
            planter_frame.pack(fill=tk.X, padx=20, pady=5)
            
            if planter["occupied"]:
                plant_name = planter["plant"]
                growth_stage = planter["growth_stage"]
                growth_text = "Seedling" if growth_stage < 3 else "Growing" if growth_stage < 6 else "Mature"
                
                # Plant name
                name_label = tk.Label(planter_frame, text=f"Planter {i+1}: {plant_name}", 
                                    font=("Arial", 14, "bold"), bg="#222222", fg="light green")
                name_label.pack(anchor="w", padx=10, pady=5)
                
                # Plant stage
                stage_label = tk.Label(planter_frame, text=f"Stage: {growth_text} ({growth_stage}/10)", 
                                     font=("Arial", 12), bg="#222222", fg="white")
                stage_label.pack(anchor="w", padx=10, pady=5)
            else:
                # Empty planter
                name_label = tk.Label(planter_frame, text=f"Planter {i+1}: Empty", 
                                    font=("Arial", 14, "bold"), bg="#222222", fg="white")
                name_label.pack(anchor="w", padx=10, pady=5)
                
                # Description
                empty_label = tk.Label(planter_frame, text="This planter is ready for seeds.", 
                                    font=("Arial", 12), bg="#222222", fg="white")
                empty_label.pack(anchor="w", padx=10, pady=5)
        
        # Close button
        close_btn = tk.Button(plants_window, text="Close", font=("Arial", 14), width=15, command=plants_window.destroy)
        close_btn.pack(pady=20)
    
    def access_botany_station(self):
        """Access the botany station for authorized personnel"""
        # Remove the access confirmation popup
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Title for the station
        station_label = tk.Label(self.button_frame, text="Botany Station Controls", font=("Arial", 16, "bold"), bg="black", fg="white")
        station_label.pack(pady=10)
        
        # Get seeds button
        seeds_btn = tk.Button(self.button_frame, text="Seed Machine", font=("Arial", 14), width=20, command=self.access_seed_machine)
        seeds_btn.pack(pady=10)
        
        # View plants button
        view_btn = tk.Button(self.button_frame, text="View Plants", font=("Arial", 14), width=20, command=self.view_plants)
        view_btn.pack(pady=10)
        
        # Plant seeds button
        plant_btn = tk.Button(self.button_frame, text="Plant Seeds", font=("Arial", 14), width=20, command=self.plant_seeds)
        plant_btn.pack(pady=10)
        
        # Back button
        back_btn = tk.Button(self.button_frame, text="Back to Main Menu", font=("Arial", 14), width=20, command=self.show_station_menu)
        back_btn.pack(pady=15)
        
        # Make sure the window stays on top after dialog
        self.botany_window.after(20, self.botany_window.lift)
        self.botany_window.focus_force()
    
    def access_seed_machine(self):
        """Access the seed machine to get seeds"""
        # Create a new toplevel window for the seed machine
        _panel, seed_window = open_modal_panel(self.botany_window, title="Seed Machine")
        # Title
        title_label = tk.Label(seed_window, text="Botanical Seed Dispenser", font=("Arial", 18, "bold"), bg="black", fg="white")
        title_label.pack(pady=15)
        
        # Description
        desc_text = "This machine dispenses seeds for cultivation in the botany lab's planters."
        desc_label = tk.Label(seed_window, text=desc_text, font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Main frame to contain both left and right sides
        main_frame = tk.Frame(seed_window, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame for available seeds
        left_frame = tk.LabelFrame(main_frame, text="Available Seeds", font=("Arial", 14), bg="black", fg="white")
        left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar for available seeds
        left_canvas = tk.Canvas(left_frame, bg="black", highlightthickness=0)
        left_scrollbar = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        # Pack canvas and scrollbar
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create frame inside canvas to hold seed items
        seeds_frame = tk.Frame(left_canvas, bg="black")
        left_canvas.create_window((0, 0), window=seeds_frame, anchor=tk.NW)
        
        # Right frame for your seeds
        right_frame = tk.LabelFrame(main_frame, text="Your Seeds", font=("Arial", 14), bg="black", fg="white")
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar for your seeds
        right_canvas = tk.Canvas(right_frame, bg="black", highlightthickness=0)
        right_scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL, command=right_canvas.yview)
        right_canvas.configure(yscrollcommand=right_scrollbar.set)
        
        # Pack canvas and scrollbar
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create frame inside canvas to hold your seed items
        your_seeds_frame = tk.Frame(right_canvas, bg="black")
        right_canvas.create_window((0, 0), window=your_seeds_frame, anchor=tk.NW)
        
        # Left frame contents: available seeds
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
        
        # Right frame contents: your seeds
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
        
        # Update scroll regions after all widgets are added
        seeds_frame.update_idletasks()
        left_canvas.config(scrollregion=left_canvas.bbox("all"))
        
        your_seeds_frame.update_idletasks()
        right_canvas.config(scrollregion=right_canvas.bbox("all"))
        
        # Make the main seeds panel visible by moving the scrollbar to the top
        left_canvas.yview_moveto(0.0)
        
        # Configure canvas resizing when window is resized
        def on_frame_configure(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        seeds_frame.bind("<Configure>", lambda e: on_frame_configure(left_canvas))
        your_seeds_frame.bind("<Configure>", lambda e: on_frame_configure(right_canvas))
        
        # Mouse wheel scrolling with focus handling
        def on_mousewheel(event, canvas):
            widget = seed_window.winfo_containing(event.x_root, event.y_root)
            # Check which canvas the mouse is over
            while widget is not None:
                if widget == left_canvas:
                    left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return
                elif widget == right_canvas:
                    right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return
                widget = widget.master
            
            # Default to left canvas if we couldn't determine
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Bind mousewheel to the window so it works anywhere
        seed_window.bind("<MouseWheel>", lambda e: on_mousewheel(e, left_canvas))
        
        # Override destroy method to cleanup bindings
        orig_destroy = seed_window.destroy
        def _destroy_and_cleanup():
            try:
                seed_window.unbind("<MouseWheel>")
            except:
                pass
            orig_destroy()
        
        seed_window.destroy = _destroy_and_cleanup
        
        # Close button
        close_btn = tk.Button(seed_window, text="Close", font=("Arial", 14), width=15, command=seed_window.destroy)
        close_btn.pack(side=tk.BOTTOM, pady=10)
    
    def get_seeds(self, seed, parent_window):
        """Get seeds from the seed machine"""
        self.player_data["botany"]["seeds"].append(seed)
        
        # Add note about getting seeds
        add_note(self.player_data, f"Acquired {seed['name']} from the botany seed dispenser.")
        
        # Refresh the seed window
        parent_window.destroy()
        self.access_seed_machine()
    
    def plant_seeds(self):
        """Plant seeds in the planters"""
        # Check if player has any seeds
        if not self.player_data["botany"]["seeds"]:
            self.botany_window.after(10, lambda: messagebox.showinfo("No Seeds", 
                                                              "You don't have any seeds to plant. Get some from the seed machine first.", 
                                                              parent=self.botany_window))
            return
        
        # Create a new toplevel window for planting
        _panel, plant_window = open_modal_panel(self.botany_window, title="Plant Seeds")
        # Create main canvas with scrollbar
        main_canvas = tk.Canvas(plant_window, bg="black", highlightthickness=0)
        scrollbar = tk.Scrollbar(plant_window, orient="vertical", command=main_canvas.yview)
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame inside canvas to hold all content
        content_frame = tk.Frame(main_canvas, bg="black")
        canvas_frame = main_canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Title
        title_label = tk.Label(content_frame, text="Plant Seeds", font=("Arial", 18, "bold"), bg="black", fg="white")
        title_label.pack(pady=15)
        
        # Description
        desc_text = "Select a seed to plant and an empty planter to place it in."
        desc_label = tk.Label(content_frame, text=desc_text, font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Top frame for seeds
        seeds_frame = tk.LabelFrame(content_frame, text="Your Seeds", font=("Arial", 14), bg="black", fg="white")
        seeds_frame.pack(padx=20, pady=10, fill=tk.X)
        
        # Keep track of the selected seed and planter
        selected_data = {"seed": None, "planter": None}
        
        # Function to select a seed
        def select_seed(seed, button):
            # Reset all seed buttons
            for btn in seed_buttons:
                btn.config(bg="#333333")
            
            # Highlight the selected button
            button.config(bg="#006600")
            
            # Update selected seed
            selected_data["seed"] = seed
            
            # Enable plant button if both seed and planter are selected
            if selected_data["planter"] is not None:
                plant_btn.config(state=tk.NORMAL)
        
        # Function to select a planter
        def select_planter(index, button):
            # Check if planter is already occupied
            if self.player_data["botany"]["planters"][index]["occupied"]:
                messagebox.showinfo("Planter Occupied", 
                                   f"Planter {index+1} already has a plant in it. Choose an empty planter.", 
                                   parent=plant_window)
                return
            
            # Reset all planter buttons
            for btn in planter_buttons:
                btn.config(bg="#333333")
            
            # Highlight the selected button
            button.config(bg="#006600")
            
            # Update selected planter
            selected_data["planter"] = index
            
            # Enable plant button if both seed and planter are selected
            if selected_data["seed"] is not None:
                plant_btn.config(state=tk.NORMAL)
        
        # Add seed options
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
        
        # Planter selection frame
        planters_frame = tk.LabelFrame(content_frame, text="Available Planters", font=("Arial", 14), bg="black", fg="white")
        planters_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Add planter options
        planter_buttons = []
        for i, planter in enumerate(self.player_data["botany"]["planters"]):
            planter_frame = tk.Frame(planters_frame, bg="#222222", bd=2, relief=tk.RIDGE)
            planter_frame.pack(fill=tk.X, padx=20, pady=10)
            
            if planter["occupied"]:
                # Show occupied planter
                name_label = tk.Label(planter_frame, text=f"Planter {i+1}: {planter['plant']}", 
                                    font=("Arial", 14, "bold"), bg="#222222", fg="light green")
                name_label.pack(side=tk.LEFT, padx=10, pady=5)
                
                status_label = tk.Label(planter_frame, text="OCCUPIED", 
                                      font=("Arial", 12), bg="#222222", fg="red")
                status_label.pack(side=tk.RIGHT, padx=10, pady=5)
            else:
                # Show empty planter
                name_label = tk.Label(planter_frame, text=f"Planter {i+1}: Empty", 
                                    font=("Arial", 14, "bold"), bg="#222222", fg="white")
                name_label.pack(side=tk.LEFT, padx=10, pady=5)
                
                select_btn = tk.Button(planter_frame, text="Select", font=("Arial", 10), bg="#333333",
                                    command=lambda idx=i, b=planter_frame: select_planter(idx, b))
                select_btn.pack(side=tk.RIGHT, padx=10, pady=5)
            planter_buttons.append(planter_frame)
        
        # Function to plant the seed
        def do_planting():
            if selected_data["seed"] is None or selected_data["planter"] is None:
                return
            
            seed = selected_data["seed"]
            planter_index = selected_data["planter"]
            
            # Update the planter data
            self.player_data["botany"]["planters"][planter_index] = {
                "occupied": True,
                "plant": seed["name"],
                "growth_stage": 1  # Start at stage 1
            }
            
            # Remove the seed from inventory
            self.player_data["botany"]["seeds"].remove(seed)
            
            # Add note about planting
            add_note(self.player_data, f"Planted {seed['name']} in planter {planter_index+1}.")
            
            # Refresh the planters display (but don't close the window)
            for btn in seed_buttons:
                btn.destroy()
            
            for btn in planter_buttons:
                btn.destroy()
                
            # Reset buttons and selection
            seed_buttons.clear()
            planter_buttons.clear()
            selected_data["seed"] = None
            selected_data["planter"] = None
            
            # Recreate the seed and planter options
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
                    # Show occupied planter
                    name_label = tk.Label(planter_frame, text=f"Planter {i+1}: {planter['plant']}", 
                                        font=("Arial", 14, "bold"), bg="#222222", fg="light green")
                    name_label.pack(side=tk.LEFT, padx=10, pady=5)
                    
                    status_label = tk.Label(planter_frame, text="OCCUPIED", 
                                          font=("Arial", 12), bg="#222222", fg="red")
                    status_label.pack(side=tk.RIGHT, padx=10, pady=5)
                else:
                    # Show empty planter
                    name_label = tk.Label(planter_frame, text=f"Planter {i+1}: Empty", 
                                        font=("Arial", 14, "bold"), bg="#222222", fg="white")
                    name_label.pack(side=tk.LEFT, padx=10, pady=5)
                    
                    select_btn = tk.Button(planter_frame, text="Select", font=("Arial", 10), bg="#333333",
                                        command=lambda idx=i, b=planter_frame: select_planter(idx, b))
                    select_btn.pack(side=tk.RIGHT, padx=10, pady=5)
                planter_buttons.append(planter_frame)
            
            # Update canvas scroll region
            content_frame.update_idletasks()
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            
            # Disable the plant button again
            plant_btn.config(state=tk.DISABLED)
        
        # Bottom buttons
        button_frame = tk.Frame(content_frame, bg="black")
        button_frame.pack(pady=20)
        
        # Plant button (disabled until both seed and planter are selected)
        plant_btn = tk.Button(button_frame, text="Plant Seed", font=("Arial", 14), width=15, 
                           command=do_planting, state=tk.DISABLED)
        plant_btn.pack(side=tk.LEFT, padx=20)
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", font=("Arial", 14), width=15, 
                            command=plant_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=20)
        
        # Configure canvas scrolling
        def configure_scroll_region(event):
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            
        content_frame.bind("<Configure>", configure_scroll_region)
        
        # Configure mouse wheel scrolling
        def on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        main_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Update the canvas when all widgets are packed
        content_frame.update_idletasks()
        main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        
        # Make sure canvas width matches the window width
        def adjust_canvas_frame(event):
            canvas_width = event.width
            main_canvas.itemconfig(canvas_frame, width=canvas_width)
            
        main_canvas.bind("<Configure>", adjust_canvas_frame)
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, DOOR_KEY, self.botany_window)
    
    def on_closing(self):
        """Handle Exit Room (return to hallway)."""
        try_leave_through_door(
            self.botany_window,
            self.player_data,
            DOOR_KEY,
            self.return_callback,
            self.station_crew,
        )
    
    def _build_station_menu(self, before_show=None):
        render_station_menu(
            self.button_frame,
            self.player_data,
            door_key=DOOR_KEY,
            stations=[{
                "label": "Enter Botany Station",
                "command": self.access_botany_station,
            }],
            show_room_options=self.show_room_options,
            toggle_door_lock=self.toggle_door_lock,
            before_show=before_show,
        )

    def show_station_menu(self):
        """Return to main station menu options"""
        self._build_station_menu()
