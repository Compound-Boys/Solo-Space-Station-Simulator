import tkinter as tk
from tkinter import messagebox
import datetime

from game.helper_methods.door_control import can_control_door, toggle_door_lock as toggle_room_door_lock
from game.objects.items import get_item_definition
from game.helper_methods.power_constants import SYSTEM_POWER_RATES
from game.helper_methods.oxygen_helper import (
    LIFE_SUPPORT_DAMAGE_BEGIN_TITLE,
    LIFE_SUPPORT_DAMAGE_BEGIN_MESSAGE,
    OXYGEN_DEPLETION_ANNOUNCEMENT_TEXT,
    OXYGEN_DEPLETION_MODAL_BODY,
    OXYGEN_DEPLETION_FOLLOWUP_TITLE,
    OXYGEN_DEPLETION_FOLLOWUP_MESSAGE,
    life_support_entering_damage_range,
)
from game.special_rooms.shared import add_note, open_room_in_main_window, try_leave_through_door, show_station_menu as render_station_menu
from game.helper_methods.ui_panels import open_modal_panel, report_message
from game.maps.donut import ENGINEERING_KEY as DOOR_KEY

class Engineering:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self.engineering_window = open_room_in_main_window(parent_window, "Engineering Bay", self.on_closing)
        
        # Title
        room_label = tk.Label(self.engineering_window, text="Station Engineering Bay", font=("Arial", 24), bg="black", fg="white")
        room_label.pack(pady=30)
        
        # Description
        desc_label = tk.Label(self.engineering_window, 
                              text="The engineering bay is filled with equipment and tools. Various machines hum with power, and spare parts are organized on shelves. This is where the station's systems are maintained and repaired.",
                              font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Room actions
        self.button_frame = tk.Frame(self.engineering_window, bg="black")
        self.button_frame.pack(pady=20)

        self._build_station_menu()
        
        # Exit button
        exit_btn = tk.Button(self.engineering_window, text="Exit Room", font=("Arial", 14), width=15, command=self.on_closing)
        exit_btn.pack(pady=20)
    
    def show_room_options(self):
        """Show regular room options that all players can access"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Engineering options - Changed "Examine Tools" to "Access Fabricator"
        fabricator_btn = tk.Button(self.button_frame, text="Access Fabricator", font=("Arial", 14), width=20, command=self.access_fabricator)
        fabricator_btn.pack(pady=10)
        
        if can_control_door(self.player_data, DOOR_KEY):
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)
    
    def access_fabricator(self):
        """Open the fabricator interface using the new item system"""
        _panel, fab_popup = open_modal_panel(self.engineering_window, title="Fabricator")
        fab_popup.configure(bg="black")


        # Title
        title_label = tk.Label(fab_popup, text="Station Fabricator", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)

        # Main frame for layout
        main_frame = tk.Frame(fab_popup, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left frame for categories
        category_outer_frame = tk.LabelFrame(main_frame, text="Categories", font=("Arial", 12), bg="black", fg="white")
        category_outer_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        category_scrollbar = tk.Scrollbar(category_outer_frame, orient=tk.VERTICAL)
        category_listbox = tk.Listbox(category_outer_frame, bg="black", fg="white", font=("Arial", 12),
                                     width=15, exportselection=False,
                                     yscrollcommand=category_scrollbar.set)
        category_scrollbar.config(command=category_listbox.yview)
        category_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        category_listbox.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.Y, expand=True)


        # Right frame for items
        item_outer_frame = tk.LabelFrame(main_frame, text="Items", font=("Arial", 12), bg="black", fg="white")
        item_outer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        item_scrollbar = tk.Scrollbar(item_outer_frame, orient=tk.VERTICAL)
        item_listbox = tk.Listbox(item_outer_frame, bg="black", fg="white", font=("Arial", 12),
                                width=30, exportselection=False,
                                yscrollcommand=item_scrollbar.set)
        item_scrollbar.config(command=item_listbox.yview)
        item_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        item_listbox.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.BOTH, expand=True)


        # Feedback label
        feedback_label = tk.Label(fab_popup, text="", font=("Arial", 12), bg="black", fg="cyan")
        feedback_label.pack(pady=(5, 0))

        # Button frame
        button_frame = tk.Frame(fab_popup, bg="black")
        button_frame.pack(pady=10)

        # --- Fabricatable items data (Now uses item definitions) ---
        # Define which item IDs can be fabricated
        fabricatable_item_ids = {
            "Tool": ["wrench", "screwdriver", "wirecutters", "flashlight", "basic_tools"],
            "Book": ["welcome_guide", "station_map", "maintenance_manual"],
            "Component": ["circuit_board", "battery_pack", "power_cell"] # Example addition
            # Add more categories and item IDs here later
        }

        # Store item definitions for easy access
        fabricatable_items_data = {}
        valid_categories = [] # Keep track of categories with valid items
        for category, item_ids in fabricatable_item_ids.items():
            items_in_category = []
            for item_id in item_ids:
                item_def = get_item_definition(item_id) # Fetch from items.py
                if item_def:
                    items_in_category.append(item_def)
            if items_in_category: # Only add category if it has items
                fabricatable_items_data[category] = items_in_category
                valid_categories.append(category)


        # Populate categories
        category_listbox.delete(0, tk.END) # Clear previous entries
        for category in valid_categories:
            category_listbox.insert(tk.END, category)

        # Function to update items based on selected category
        def update_items(event=None):
            selected_category_indices = category_listbox.curselection()
            item_listbox.delete(0, tk.END) # Clear items listbox

            if not selected_category_indices:
                return # No category selected

            try:
                selected_category_index = selected_category_indices[0]
                selected_category = category_listbox.get(selected_category_index)
            except tk.TclError:
                 # Handle potential error if listbox is modified during event
                 return

            if selected_category in fabricatable_items_data:
                for item_def in fabricatable_items_data[selected_category]:
                    # Store the item_id with the listbox item
                    item_listbox.insert(tk.END, item_def['name'])
                    # Use itemcget/itemconfig to associate data; simpler way is often a parallel list or dict
                    # Let's use a dictionary to map listbox index to item_id for robustness
                    current_index = item_listbox.size() - 1
                    item_listbox.itemconfig(current_index, {'fg': 'white'}) # Example: Reset color if needed

            # Store mapping from listbox index to item_id for the current view
            # Need a way to map listbox selection back to item_id
            # Option 1: Rebuild a mapping whenever category changes
            # Option 2: Store ID directly in listbox (less reliable across Tk versions/platforms)
            # Let's stick to mapping via index lookup in the current category's item list
            # (This is handled implicitly when retrieving selection in create_item)


        category_listbox.bind('<<ListboxSelect>>', update_items)

        # Select the first category by default if available
        if valid_categories:
             category_listbox.selection_set(0)
             update_items() # Manually call once to populate items initially

        # Create button function
        def create_item():
            selected_category_indices = category_listbox.curselection()
            selected_item_indices = item_listbox.curselection()

            if not selected_category_indices or not selected_item_indices:
                feedback_label.config(text="Please select a category and an item.", fg="orange")
                fab_popup.after(3000, lambda: feedback_label.config(text="")) # Clear message
                return

            try:
                selected_category = category_listbox.get(selected_category_indices[0])
                selected_item_index = selected_item_indices[0]
            except tk.TclError:
                feedback_label.config(text="Selection error. Please try again.", fg="red")
                fab_popup.after(3000, lambda: feedback_label.config(text="")) # Clear message
                return


            # Retrieve the item definition based on the selection
            if selected_category in fabricatable_items_data and selected_item_index < len(fabricatable_items_data[selected_category]):
                item_def_selected = fabricatable_items_data[selected_category][selected_item_index]
                item_id = item_def_selected['id']
                item_name = item_def_selected['name'] # Get name directly from the definition

                # Get a *fresh copy* of the item definition using the helper function
                item_definition_copy = get_item_definition(item_id)
                if not item_definition_copy:
                     feedback_label.config(text=f"Error: Item definition for '{item_id}' not found.", fg="red")
                     fab_popup.after(3000, lambda: feedback_label.config(text="")) # Clear message
                     return

                # Ensure inventory list exists
                self.player_data.setdefault("inventory", [])

                # Add the full item dictionary copy to inventory
                self.player_data["inventory"].append(item_definition_copy)

                # Show confirmation message
                feedback_label.config(text=f"'{item_name}' created successfully.", fg="cyan")

                # Add note about fabrication
                add_note(self.player_data, f"Fabricated a {item_name} ({item_id}) in Engineering.")

            else:
                 feedback_label.config(text="Error retrieving selected item data.", fg="red")


            # Clear message after a delay
            fab_popup.after(3000, lambda: feedback_label.config(text=""))


        create_btn = tk.Button(button_frame, text="Create", font=("Arial", 12), width=10, command=create_item)
        create_btn.pack(side=tk.LEFT, padx=10)

        # Add Examine button
        examine_btn = tk.Button(button_frame, text="Examine", font=("Arial", 12), width=10, command=lambda: examine_item(category_listbox, item_listbox, feedback_label, fabricatable_items_data))
        examine_btn.pack(side=tk.LEFT, padx=10)

        close_btn = tk.Button(button_frame, text="Close", font=("Arial", 12), width=10, command=fab_popup.destroy)
        close_btn.pack(side=tk.LEFT, padx=10)

        # Function to examine the selected item
        def examine_item(cat_listbox, itm_listbox, feedback_lbl, items_data):
            selected_category_indices = cat_listbox.curselection()
            selected_item_indices = itm_listbox.curselection()

            if not selected_category_indices or not selected_item_indices:
                feedback_lbl.config(text="Please select a category and an item to examine.", fg="orange")
                fab_popup.after(4000, lambda: feedback_lbl.config(text="")) # Clear message longer
                return

            try:
                selected_category = cat_listbox.get(selected_category_indices[0])
                selected_item_index = selected_item_indices[0]
            except tk.TclError:
                feedback_lbl.config(text="Selection error. Please try again.", fg="red")
                fab_popup.after(3000, lambda: feedback_lbl.config(text="")) # Clear message
                return

            # Retrieve the item definition based on the selection
            if selected_category in items_data and selected_item_index < len(items_data[selected_category]):
                item_def_selected = items_data[selected_category][selected_item_index]
                item_description = item_def_selected.get('description', "No description available.")

                # Display the description
                feedback_lbl.config(text=f"Examine: {item_description}", fg="yellow") # Use yellow for examine
                # Don't auto-clear examine message, let user read it
                # fab_popup.after(5000, lambda: feedback_lbl.config(text=""))
            else:
                 feedback_lbl.config(text="Error retrieving selected item data for examination.", fg="red")
                 fab_popup.after(3000, lambda: feedback_lbl.config(text="")) # Clear error message

        # Mouse wheel binding for listboxes (bind to the window, check focus)
        def _on_mousewheel(event):
            widget = fab_popup.focus_get()
            if widget == category_listbox:
                 category_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
            elif widget == item_listbox:
                 item_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
            # Optionally, could check if mouse is *over* a listbox if focus isn't reliable
            # else:
            #     x, y = fab_popup.winfo_pointerxy()
            #     widget_under_mouse = fab_popup.winfo_containing(x, y)
            #     if widget_under_mouse == category_listbox:
            #          category_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
            #     elif widget_under_mouse == item_listbox:
            #          item_listbox.yview_scroll(int(-1*(event.delta/120)), "units")


        fab_popup.bind("<MouseWheel>", _on_mousewheel)

        # Cleanup binding on close
        orig_destroy = fab_popup.destroy
        def _destroy_and_cleanup():
            try:
                fab_popup.unbind("<MouseWheel>")
            except tk.TclError:
                pass # Ignore if already unbound or window destroyed
            orig_destroy()
        fab_popup.destroy = _destroy_and_cleanup
    
    def access_engineering_station(self):
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Add engineering station options
        station_label = tk.Label(self.button_frame, text="Engineering Station Controls", font=("Arial", 16, "bold"), bg="black", fg="white")
        station_label.pack(pady=10)
        
        # Direct access to Engineering Panel without the power management and atmosphere buttons
        engineering_panel_btn = tk.Button(self.button_frame, text="Engineering Panel", font=("Arial", 14), width=20, command=self.access_engineering_panel)
        engineering_panel_btn.pack(pady=5)
        
        back_btn = tk.Button(self.button_frame, text="Back to Main Menu", font=("Arial", 14), width=20, command=self.show_station_menu)
        back_btn.pack(pady=15)
    
    def access_toolbox(self):
        """Access the engineering toolbox with specialized tools"""
        # Check if user has special access (Engineer or Captain)
        has_engineering_access = ("permissions" in self.player_data and self.player_data["permissions"].get("engineering_station", False)) or \
                                (self.player_data.get("job") == "Engineer") or \
                                (self.player_data.get("job") == "Captain")
        
        if has_engineering_access:
            # Show specialized toolbox for authorized personnel
            _panel, toolbox_window = open_modal_panel(self.engineering_window, title="Engineering Toolbox")
            
            # Title
            title_label = tk.Label(toolbox_window, text="Specialized Engineering Tools", font=("Arial", 18, "bold"), bg="black", fg="white")
            title_label.pack(pady=15)
            
            # Description
            desc_label = tk.Label(toolbox_window, text="This secure toolbox contains specialized equipment for station maintenance and emergency repairs.", 
                                 font=("Arial", 12), bg="black", fg="white", wraplength=500)
            desc_label.pack(pady=10)
            
            # Create a frame for the scrollable content
            tools_outer_frame = tk.Frame(toolbox_window, bg="black")
            tools_outer_frame.pack(pady=10, fill=tk.BOTH, expand=True)
            
            # Add scrollbar to the frame
            scrollbar = tk.Scrollbar(tools_outer_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Create canvas for scrolling
            tools_canvas = tk.Canvas(tools_outer_frame, bg="black", highlightthickness=0)
            tools_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Configure scrollbar to work with canvas
            scrollbar.config(command=tools_canvas.yview)
            tools_canvas.configure(yscrollcommand=scrollbar.set)
            
            # Create inner frame for tools
            tools_frame = tk.Frame(tools_canvas, bg="black")
            
            # Add the inner frame to the canvas
            canvas_window = tools_canvas.create_window((0, 0), window=tools_frame, anchor=tk.NW)
            
            # Specialized tools list
            specialized_tools = [
                {"name": "Power Coupling Optimizer", "description": "Balances load across power distribution networks."},
                {"name": "Quantum Harmonizer", "description": "Aligns phase shifts in sensitive equipment."},
                {"name": "Plasma Flow Regulator", "description": "Controls plasma injection rates in the reactor core."},
                {"name": "Singularity Containment Monitor", "description": "Monitors field stability in high-energy systems."},
                {"name": "Thermal Dampening Coils", "description": "Reduces heat signatures in sensitive areas."},
                {"name": "Antimatter Containment Field", "description": "Maintains the integrity of antimatter storage units."},
                {"name": "Subspace Field Modulator", "description": "Calibrates subspace field generators for communications."},
                {"name": "Graviton Pulse Emitter", "description": "Creates localized gravity fields for specialized repairs."},
                {"name": "Tachyon Detection Grid", "description": "Scans for tachyon particles that may indicate temporal anomalies."},
                {"name": "Neural Interface Adapter", "description": "Allows direct neural connection to station systems for diagnostics."}
            ]
            
            # Add tools to frame
            for i, tool in enumerate(specialized_tools):
                tool_frame = tk.Frame(tools_frame, bg="#222222", bd=1, relief=tk.RIDGE)
                tool_frame.pack(fill=tk.X, padx=20, pady=5)
                
                name_label = tk.Label(tool_frame, text=tool["name"], font=("Arial", 14, "bold"), bg="#222222", fg="#00CCFF")
                name_label.pack(anchor="w", padx=10, pady=5)
                
                desc_label = tk.Label(tool_frame, text=tool["description"], font=("Arial", 12), bg="#222222", fg="white", wraplength=500)
                desc_label.pack(anchor="w", padx=10, pady=5)
                
                use_btn = tk.Button(tool_frame, text="Use Tool", font=("Arial", 12), bg="#555555", fg="white", 
                                command=lambda t=tool["name"]: messagebox.showinfo("Tool Usage", f"You used the {t} to optimize station systems.", parent=toolbox_window))
                use_btn.pack(anchor="e", padx=10, pady=5)
            
            # Update scrollregion when the frame changes size
            def configure_scroll_region(event):
                tools_canvas.configure(scrollregion=tools_canvas.bbox("all"))
                tools_canvas.itemconfig(canvas_window, width=tools_canvas.winfo_width())
            
            tools_frame.bind("<Configure>", configure_scroll_region)
            tools_canvas.bind("<Configure>", lambda e: tools_canvas.itemconfig(canvas_window, width=e.width))
            
            # Function to handle mousewheel scrolling
            def on_mousewheel(event):
                try:
                    # Windows style scrolling
                    tools_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                except Exception as e:
                    try:
                        # Linux style scrolling
                        if event.num == 4:
                            tools_canvas.yview_scroll(-1, "units")
                        elif event.num == 5:
                            tools_canvas.yview_scroll(1, "units")
                    except:
                        pass  # Ignore errors if the canvas was destroyed
            
            # Bind the mousewheel event to the canvas and window
            tools_canvas.bind("<MouseWheel>", on_mousewheel)
            tools_canvas.bind("<Button-4>", on_mousewheel)
            tools_canvas.bind("<Button-5>", on_mousewheel)
            
            toolbox_window.bind("<MouseWheel>", on_mousewheel)
            toolbox_window.bind("<Button-4>", on_mousewheel)
            toolbox_window.bind("<Button-5>", on_mousewheel)
            
            # Close button
            close_btn = tk.Button(toolbox_window, text="Close Toolbox", font=("Arial", 14), bg="#333333", fg="white",
                                command=toolbox_window.destroy)
            close_btn.pack(pady=15)
            
            # Make sure to unbind events when window is closed
            orig_destroy = toolbox_window.destroy
            def _destroy_and_cleanup():
                try:
                    toolbox_window.unbind("<MouseWheel>")
                    toolbox_window.unbind("<Button-4>")
                    toolbox_window.unbind("<Button-5>")
                except:
                    pass
                orig_destroy()
            
            toolbox_window.destroy = _destroy_and_cleanup
            
        else:
            # Warning for unauthorized personnel
            warning_message = "WARNING: These specialized engineering tools should only be handled by trained personnel. Improper use could result in station damage, injury, or death. Access restricted to Engineering staff and Command personnel only."
            messagebox.showwarning("Access Restricted", warning_message, parent=self.engineering_window)
            
        # Make sure the window stays on top after dialog
        self.engineering_window.after(20, self.engineering_window.lift)
        self.engineering_window.focus_force()
    
    def access_engineering_panel(self):
        """Access the engineering panel with power controls and station systems"""
        # Check if user has special access (Engineer or Captain)
        has_engineering_access = ("permissions" in self.player_data and self.player_data["permissions"].get("engineering_station", False)) or \
                                (self.player_data.get("job") == "Engineer") or \
                                (self.player_data.get("job") == "Captain")
        
        if has_engineering_access:
            # Show specialized engineering panel for authorized personnel
            _panel, panel_window = open_modal_panel(self.engineering_window, title="Engineering Panel")
            
            # Create main frame for the entire content
            main_frame = tk.Frame(panel_window, bg="black")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Add a canvas with scrollbar
            canvas = tk.Canvas(main_frame, bg="black", highlightthickness=0)
            scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="black")
            
            # Configure scrolling
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack the scrollbar and canvas
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Title
            title_label = tk.Label(scrollable_frame, text="Station Engineering Panel", font=("Arial", 18, "bold"), bg="black", fg="white")
            title_label.pack(pady=15)
            
            # Description
            desc_label = tk.Label(scrollable_frame, text="This panel controls the station's power systems and engineering functions.", 
                                 font=("Arial", 12), bg="black", fg="white", wraplength=500)
            desc_label.pack(pady=10)
            
            # Battery status section
            battery_frame = tk.Frame(scrollable_frame, bg="#222222", bd=1, relief=tk.RIDGE)
            battery_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # Initialize battery level in player_data if not present
            if "station_power" not in self.player_data:
                self.player_data["station_power"] = {
                    "battery_level": 25.0,
                    "solar_charging": False,
                    "last_update_time": datetime.datetime.now().isoformat()
                }
            
            # Initialize system levels for the sliders if not present
            if "system_levels" not in self.player_data["station_power"]:
                self.player_data["station_power"]["system_levels"] = {
                    "life_support": 10,
                    "hallway_lighting": 5,
                    "security_systems": 7,
                    "communication_array": 5
                }
            
            # Initialize power mode if not present
            if "power_mode" not in self.player_data["station_power"]:
                self.player_data["station_power"]["power_mode"] = "balanced"
            
            # Battery level display
            battery_level = self.player_data["station_power"]["battery_level"]
            battery_label = tk.Label(battery_frame, text="Main Battery Status", font=("Arial", 14, "bold"), 
                                   bg="#222222", fg="#FFFF00")
            battery_label.pack(anchor="w", padx=10, pady=5)
            
            # Create a frame for the battery bar
            bar_frame = tk.Frame(battery_frame, bg="#222222")
            bar_frame.pack(fill=tk.X, padx=10, pady=5)
            
            battery_bar_frame = tk.Frame(bar_frame, bg="#333333", height=25, width=300)
            battery_bar_frame.pack(side=tk.LEFT, padx=5)
            battery_bar_frame.pack_propagate(False)
            
            battery_fill = tk.Frame(battery_bar_frame, bg="#00FF00" if battery_level > 50 else "#FFFF00" if battery_level > 20 else "#FF0000", 
                                  height=25, width=int(300 * battery_level / 100))
            battery_fill.place(x=0, y=0)
            
            battery_percent = tk.Label(bar_frame, text=f"{battery_level:.1f}%", font=("Arial", 12, "bold"), 
                                     bg="#222222", fg="white")
            battery_percent.pack(side=tk.LEFT, padx=10)
            
            # Battery status info
            status_text = "Normal operation" if battery_level > 50 else "Low power mode" if battery_level > 10 else "Critical power level"
            status_label = tk.Label(battery_frame, text=f"Status: {status_text}", font=("Arial", 12), 
                                  bg="#222222", fg="white")
            status_label.pack(anchor="w", padx=10, pady=5)
            
            # Show whether solar panels are charging
            solar_status = "ACTIVE" if self.player_data["station_power"]["solar_charging"] else "INACTIVE"
            solar_color = "#00FF00" if self.player_data["station_power"]["solar_charging"] else "#FF0000"
            solar_label = tk.Label(battery_frame, text=f"Solar Charging: {solar_status}", font=("Arial", 12), 
                                 bg="#222222", fg=solar_color)
            solar_label.pack(anchor="w", padx=10, pady=5)
            
            # Solar panel control section
            solar_frame = tk.Frame(scrollable_frame, bg="#222222", bd=1, relief=tk.RIDGE)
            solar_frame.pack(fill=tk.X, padx=20, pady=10)
            
            solar_title = tk.Label(solar_frame, text="Solar Panel Control", font=("Arial", 14, "bold"), 
                                 bg="#222222", fg="#00CCFF")
            solar_title.pack(anchor="w", padx=10, pady=5)
            
            solar_desc = tk.Label(solar_frame, text="Control the deployment and charging state of the station's solar array.", 
                                font=("Arial", 12), bg="#222222", fg="white", wraplength=500)
            solar_desc.pack(anchor="w", padx=10, pady=5)
            
            # Function to update battery display
            def update_battery_display():
                # Get current battery level
                battery_level = self.player_data["station_power"]["battery_level"]
                
                # Update battery fill and percentage
                battery_fill.configure(width=int(300 * battery_level / 100))
                battery_fill.configure(bg="#00FF00" if battery_level > 50 else "#FFFF00" if battery_level > 20 else "#FF0000")
                battery_percent.config(text=f"{battery_level:.1f}%")
                
                # Update status text
                status_text = "Normal operation" if battery_level > 50 else "Low power mode" if battery_level > 10 else "Critical power level"
                status_label.config(text=f"Status: {status_text}")
                
                # Update battery icons for connected systems
                for system in systems:
                    if system.get("connected_to_battery", False):
                        # Find and update the system's frame
                        for widget in systems_list_frame.winfo_children():
                            if isinstance(widget, tk.Frame):
                                # Look for the battery icon in this system's frame
                                for child in widget.winfo_children():
                                    if isinstance(child, tk.Label) and "🔋" in child.cget("text") or "⚠️" in child.cget("text"):
                                        # Update the battery icon
                                        battery_icon = "🔋" if battery_level > 10 else "⚠️"
                                        child.config(text=battery_icon, fg="#00FF00" if battery_level > 20 else "#FF0000")
                                        break

            # Toggle button for solar panels
            def toggle_solar_panels():
                # Toggle the solar charging state
                self.player_data["station_power"]["solar_charging"] = not self.player_data["station_power"]["solar_charging"]
                
                # Update the button text
                new_state = "ACTIVE" if self.player_data["station_power"]["solar_charging"] else "INACTIVE"
                solar_toggle_btn.config(text=f"Solar Array: {new_state}")
                
                # Update solar status label
                solar_status = "ACTIVE" if self.player_data["station_power"]["solar_charging"] else "INACTIVE"
                solar_color = "#00FF00" if self.player_data["station_power"]["solar_charging"] else "#FF0000"
                solar_label.config(text=f"Solar Charging: {solar_status}", fg=solar_color)
                
                # Also update the button color to match the status
                solar_toggle_btn.config(fg=solar_color)
                
                # Update the battery display to reflect changes
                update_battery_display()
                
                # Show message about the change
                message = "Solar arrays activated. Batteries now charging from solar power." if self.player_data["station_power"]["solar_charging"] else "Solar arrays deactivated. Battery charging stopped."
                panel_window.after(10, lambda: messagebox.showinfo("Solar Control", message, parent=panel_window))
            
            solar_toggle_btn = tk.Button(solar_frame, text=f"Solar Array: {solar_status}", 
                                      font=("Arial", 12), bg="#333333", fg=solar_color,
                                      command=toggle_solar_panels)
            solar_toggle_btn.pack(pady=10)
            
            # Station systems section
            systems_frame = tk.Frame(scrollable_frame, bg="#222222", bd=1, relief=tk.RIDGE)
            systems_frame.pack(fill=tk.X, padx=20, pady=10)
            
            systems_title = tk.Label(systems_frame, text="Station Power Systems", font=("Arial", 14, "bold"), 
                                   bg="#222222", fg="#00CCFF")
            systems_title.pack(anchor="w", padx=10, pady=5)
            
            # Create a frame for system statuses
            systems_list_frame = tk.Frame(systems_frame, bg="#222222")
            systems_list_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Get system levels from player data
            system_levels = self.player_data["station_power"]["system_levels"]
            
            # List of station systems with power status
            systems = [
                {"name": "Life Support", "status": "Online" if system_levels.get("life_support", 10) > 0 else "Offline", "power_draw": "High", "connected_to_battery": True},
                {"name": "Hallway Lighting", "status": "Online" if system_levels.get("hallway_lighting", 5) > 0 else "Offline", "power_draw": "Medium", "connected_to_battery": True},
                {"name": "Security Systems", "status": "Online" if system_levels.get("security_systems", 7) > 0 else "Offline", "power_draw": "Medium"},
                {"name": "Communication Array", "status": "Online" if system_levels.get("communication_array", 5) > 0 else "Offline", "power_draw": "Low"}
            ]
            
            for system in systems:
                system_frame = tk.Frame(systems_list_frame, bg="#333333", bd=1, relief=tk.RIDGE)
                system_frame.pack(fill=tk.X, padx=5, pady=3)
                
                name_label = tk.Label(system_frame, text=system["name"], font=("Arial", 12, "bold"), 
                                    bg="#333333", fg="white")
                name_label.pack(side=tk.LEFT, padx=10, pady=3)
                
                status_color = "#00FF00" if system["status"] == "Online" else "#FFFF00" if system["status"] == "Standby" else "#FF0000"
                status_label = tk.Label(system_frame, text=system["status"], font=("Arial", 12), 
                                      bg="#333333", fg=status_color)
                status_label.pack(side=tk.RIGHT, padx=10, pady=3)
                
                # Add battery icon for systems connected to the battery
                if system.get("connected_to_battery", False):
                    battery_icon = "🔋" if battery_level > 10 else "⚠️"
                    battery_label = tk.Label(system_frame, text=battery_icon, font=("Arial", 14), 
                                           bg="#333333", fg="#00FF00" if battery_level > 20 else "#FF0000")
                    battery_label.pack(side=tk.RIGHT, padx=5, pady=3)
            
            # Advanced power control section with functional sliders
            advanced_frame = tk.Frame(scrollable_frame, bg="#222222", bd=1, relief=tk.RIDGE)
            advanced_frame.pack(fill=tk.X, padx=20, pady=10)
            
            advanced_title = tk.Label(advanced_frame, text="Advanced Power Controls", font=("Arial", 14, "bold"), 
                                    bg="#222222", fg="#00CCFF")
            advanced_title.pack(anchor="w", padx=10, pady=5)
            
            advanced_desc = tk.Label(advanced_frame, text="Configure power distribution and manage system priority.", 
                                   font=("Arial", 12), bg="#222222", fg="white", wraplength=500)
            advanced_desc.pack(anchor="w", padx=10, pady=5)
            
            # Create dictionary to store slider objects
            system_sliders = {}
            
            # Add warning label about system settings
            warning_label = tk.Label(advanced_frame, text="Warning: Setting systems to 0 may have harmful effects on the station's environment and crew.", 
                                    font=("Arial", 12, "italic"), bg="#222222", fg="#FF9900", wraplength=500)
            warning_label.pack(anchor="w", padx=10, pady=5)
            
            # Add some dummy controls
            priority_frame = tk.Frame(advanced_frame, bg="#222222")
            priority_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # System priority sliders
            priority_label = tk.Label(priority_frame, text="System Power Priority", font=("Arial", 12, "bold"), 
                                    bg="#222222", fg="white")
            priority_label.pack(anchor="w", pady=5)
            
            # Add power draw explanation
            power_draw_info = tk.Label(priority_frame, text="Higher settings increase power consumption. Setting systems to 0 turns them off completely.", 
                                     font=("Arial", 10, "italic"), bg="#222222", fg="#AAAAAA", wraplength=500)
            power_draw_info.pack(anchor="w", pady=5)
            
            # Power consumption rates for each system at max level (see helper_methods/power_constants.py)
            system_power_rates = SYSTEM_POWER_RATES
            
            # Dictionary to store power draw labels
            power_draw_labels = {}
            
            # Function to update system levels when sliders change
            def update_system_level(system_name, value):
                value = int(value)  # Convert to integer
                system_key = system_name.lower().replace(" ", "_")
                previous_value = self.player_data["station_power"]["system_levels"].get(system_key, 10)
                self.player_data["station_power"]["system_levels"][system_key] = value
                
                # Update power draw label for this system
                if system_key in power_draw_labels:
                    if value == 0:
                        power_text = "Power draw: None (System OFF)"
                        power_draw_labels[system_key].config(text=power_text, fg="#FF0000")
                    else:
                        # Calculate relative power draw based on slider value
                        max_rate = system_power_rates.get(system_key, 0.3)
                        current_rate = max_rate * value / 10.0
                        power_text = f"Power draw: {current_rate:.2f}% per minute"
                        
                        # Color code based on power draw
                        if value <= 3:
                            color = "#00FF00"  # Green for low power draw
                        elif value <= 7:
                            color = "#FFAA00"  # Orange for medium power draw
                        else:
                            color = "#FF5500"  # Red-orange for high power draw
                            
                        power_draw_labels[system_key].config(text=power_text, fg=color)
                
                # Find and update only the specific system that's changing
                for i, system in enumerate(systems):
                    if system["name"].lower().replace(" ", "_") == system_name.lower().replace(" ", "_"):
                        # Update status text and color in the UI for this system only
                        new_status = "Online" if value > 0 else "Offline"
                        system["status"] = new_status
                        
                        # Find this system's frame in the systems_list_frame
                        for widget in systems_list_frame.winfo_children():
                            if isinstance(widget, tk.Frame):
                                # Check if this is the frame for our system
                                system_label = widget.winfo_children()[0]  # First child should be the name label
                                if system_label.cget("text") == system["name"]:
                                    # Look for the status label in this system's frame
                                    for child in widget.winfo_children():
                                        if isinstance(child, tk.Label) and child != system_label:
                                            # This should be the status label - update it
                                            status_color = "#00FF00" if new_status == "Online" else "#FF0000"
                                            child.config(text=new_status, fg=status_color)
                                            break
                                    break
                        break
                
                # Handle life support system specifically
                if system_name == "life_support":
                    if value == 0:
                        # If life support is set to 0, announce oxygen depletion
                        self.announce_oxygen_depletion()
                    elif life_support_entering_damage_range(previous_value, value):
                        # Entering the damage range (levels 4–0)
                        report_message(
                            LIFE_SUPPORT_DAMAGE_BEGIN_TITLE,
                            LIFE_SUPPORT_DAMAGE_BEGIN_MESSAGE,
                            kind="warning",
                            parent=self.engineering_window,
                        )
                        self.announcement_active = False
                    else:
                        # If life support is greater than 0, reset the flag so another
                        # announcement can happen if it drops to 0 again
                        self.announcement_active = False
                
                # Update the power display after any system changes
                update_battery_display()
            
            # Add sliders for different systems
            systems_priority = [
                {"name": "Life Support", "key": "life_support", "default": system_levels.get("life_support", 10)},
                {"name": "Hallway Lighting", "key": "hallway_lighting", "default": system_levels.get("hallway_lighting", 5)},
                {"name": "Security Systems", "key": "security_systems", "default": system_levels.get("security_systems", 7)},
                {"name": "Communication Array", "key": "communication_array", "default": system_levels.get("communication_array", 5)}
            ]
            
            for system in systems_priority:
                system_priority_frame = tk.Frame(priority_frame, bg="#222222")
                system_priority_frame.pack(fill=tk.X, pady=2)
                
                system_name = system["name"]
                system_key = system["key"]
                default_value = system["default"]
                
                system_label = tk.Label(system_priority_frame, text=system_name, font=("Arial", 12), 
                                      bg="#222222", fg="white", width=15, anchor="w")
                system_label.pack(side=tk.LEFT, padx=5)
                
                # Add a slider with current value
                slider = tk.Scale(system_priority_frame, from_=0, to=10, orient=tk.HORIZONTAL, 
                               length=200, bg="#333333", fg="white", troughcolor="#444444",
                               highlightthickness=0, command=lambda v, name=system_key: update_system_level(name, v))
                slider.set(default_value)
                slider.pack(side=tk.LEFT, padx=10)
                
                # Create power draw label with current rate
                power_frame = tk.Frame(system_priority_frame, bg="#222222")
                power_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                current_rate = system_power_rates.get(system_key, 0.3) * default_value / 10.0
                if default_value == 0:
                    power_text = "Power draw: None (System OFF)"
                    power_color = "#FF0000"
                else:
                    power_text = f"Power draw: {current_rate:.2f}% per minute"
                    if default_value <= 3:
                        power_color = "#00FF00"  # Green for low power draw
                    elif default_value <= 7:
                        power_color = "#FFAA00"  # Orange for medium power draw
                    else:
                        power_color = "#FF5500"  # Red-orange for high power draw
                
                power_label = tk.Label(power_frame, text=power_text, font=("Arial", 10), 
                                     bg="#222222", fg=power_color)
                power_label.pack(anchor="w")
                
                # Store label reference for updating later
                power_draw_labels[system_key] = power_label
                
                # Store slider reference for later use
                system_sliders[system_key] = slider
            
            # Power mode selection with functional radio buttons
            power_mode_frame = tk.Frame(advanced_frame, bg="#222222")
            power_mode_frame.pack(fill=tk.X, padx=10, pady=10)
            
            power_mode_label = tk.Label(power_mode_frame, text="Power Management Mode", font=("Arial", 12, "bold"), 
                                      bg="#222222", fg="white")
            power_mode_label.pack(anchor="w", pady=5)
            
            # Function to apply power mode settings to sliders
            def set_power_mode(mode):
                self.player_data["station_power"]["power_mode"] = mode
                
                # Set slider values based on mode
                if mode == "balanced":
                    # Balanced mode - default values
                    system_sliders["life_support"].set(10)
                    system_sliders["hallway_lighting"].set(5)
                    system_sliders["security_systems"].set(7)
                    system_sliders["communication_array"].set(5)
                elif mode == "high":
                    # High performance - max values
                    system_sliders["life_support"].set(10)
                    system_sliders["hallway_lighting"].set(10)
                    system_sliders["security_systems"].set(10)
                    system_sliders["communication_array"].set(10)
                elif mode == "low":
                    # Power saving - minimal values
                    system_sliders["life_support"].set(7)
                    system_sliders["hallway_lighting"].set(3)
                    system_sliders["security_systems"].set(5)
                    system_sliders["communication_array"].set(2)
                elif mode == "emergency":
                    # Emergency - critical systems only
                    system_sliders["life_support"].set(10)
                    system_sliders["hallway_lighting"].set(1)
                    system_sliders["security_systems"].set(3)
                    system_sliders["communication_array"].set(1)
                
                # Update power displays to show the changes
                update_battery_display()
            
            # Radio buttons for power modes
            power_var = tk.StringVar(
                panel_window,
                value=self.player_data["station_power"]["power_mode"],
            )
            panel_window._power_mode_var = power_var
            modes = [
                ("Balanced (Standard Operation)", "balanced"),
                ("High Performance (Increased Draw)", "high"),
                ("Power Saving (Limited Functionality)", "low"),
                ("Emergency Only (Critical Systems)", "emergency")
            ]
            power_mode_radios = []

            def _sync_power_mode_radios(_event=None):
                selected = power_var.get()
                for rb in power_mode_radios:
                    if rb.cget("value") == selected:
                        rb.select()
                    else:
                        rb.deselect()

            for text, mode in modes:
                mode_radio = tk.Radiobutton(power_mode_frame, text=text, variable=power_var, value=mode,
                                          bg="#222222", fg="white", selectcolor="#222222",
                                          activebackground="#222222", activeforeground="white",
                                          highlightthickness=0, takefocus=0,
                                          command=lambda m=mode: set_power_mode(m))
                mode_radio.pack(anchor="w", padx=20, pady=2)
                mode_radio.bind("<Leave>", _sync_power_mode_radios)
                power_mode_radios.append(mode_radio)
            
            # Function to handle mousewheel scrolling
            def on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            # Bind the mousewheel event for scrolling
            panel_window.bind("<MouseWheel>", on_mousewheel)
            
            # Configure the canvas to scroll properly
            scrollable_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))
            
            # Store references to UI elements that need updates
            self.battery_update_refs = {
                "battery_fill": battery_fill,
                "battery_percent": battery_percent,
                "status_label": status_label,
                "solar_label": solar_label,
                "systems_list_frame": systems_list_frame,
                "systems": systems
            }
            
            # Function to periodically update the battery display
            def update_battery_display_timer():
                # Force an immediate battery update from player_data values
                update_battery_display()
                
                # Schedule the next update - update more frequently (500ms instead of 2000ms)
                self.battery_display_timer = panel_window.after(500, update_battery_display_timer)
            
            # Start a repeating timer to update the battery display more frequently
            self.battery_display_timer = panel_window.after(500, update_battery_display_timer)
            
            # Function to handle mousewheel scrolling
            def on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            # Bind the mousewheel event for scrolling
            panel_window.bind("<MouseWheel>", on_mousewheel)
            
            # Close button at the bottom of the scrollable content
            close_btn = tk.Button(scrollable_frame, text="Close Panel", font=("Arial", 14), bg="#333333", fg="white",
                                command=panel_window.destroy)
            close_btn.pack(pady=15)
            
            # Override destroy method to clean up bindings when the window is closed
            orig_destroy = panel_window.destroy
            def _destroy_and_cleanup():
                try:
                    panel_window.unbind("<MouseWheel>")
                    # Cancel the battery display timer
                    if hasattr(self, 'battery_display_timer'):
                        panel_window.after_cancel(self.battery_display_timer)
                except:
                    pass
                orig_destroy()
            
            panel_window.destroy = _destroy_and_cleanup
            
        else:
            # Show unauthorized access message for non-engineers
            self.engineering_window.after(10, lambda: messagebox.showwarning("Unauthorized Access", 
                                                                           "You do not have authorization to access the Engineering Panel. Engineering or Captain clearance required.", 
                                                                           parent=self.engineering_window))
            # Make sure the window stays on top after dialog
            self.engineering_window.after(20, self.engineering_window.lift)
            self.engineering_window.focus_force()
    
    def announce_oxygen_depletion(self):
        """Announce oxygen depletion to all crew when life support is set to 0"""
        try:
            # Check if an announcement is already active - don't show another one
            if hasattr(self, 'announcement_active') and self.announcement_active:
                return
                
            # Add an announcement to player data
            if "announcements" not in self.player_data:
                self.player_data["announcements"] = []
                
            announcement = {
                "timestamp": datetime.datetime.now().isoformat(),
                "text": OXYGEN_DEPLETION_ANNOUNCEMENT_TEXT,
                "type": "emergency",
                "seen": False
            }
            
            self.player_data["announcements"].append(announcement)
            
            # Set an oxygen depletion timer
            if "damage_timers" not in self.player_data:
                self.player_data["damage_timers"] = {}
                
            self.player_data["damage_timers"]["oxygen_depletion"] = {
                "active": True,
                "start_time": datetime.datetime.now().isoformat(),
                "warning_shown": False
            }
            
            # Mark announcement as active so we don't show multiple popups
            self.announcement_active = True
            
            # Create the emergency announcement window
            _panel, pa_window = open_modal_panel(self.engineering_window, title="STATION-WIDE EMERGENCY ANNOUNCEMENT")
            pa_window.configure(bg="#990000")  # Red background for emergency
            # Handle closing properly
            def close_announcement(*args):
                self.announcement_active = False
                pa_window.destroy()

                if hasattr(self, 'engineering_window') and self.engineering_window.winfo_exists():
                    self.engineering_window.focus_force()

                report_message(
                    OXYGEN_DEPLETION_FOLLOWUP_TITLE,
                    OXYGEN_DEPLETION_FOLLOWUP_MESSAGE,
                    kind="warning",
                    parent=self.engineering_window,
                )
            
            # Function for blinking effect
            def toggle_bg():
                if not pa_window.winfo_exists():
                    return
                    
                current_color = pa_window.cget("bg")
                new_color = "#660000" if current_color == "#990000" else "#990000"
                pa_window.configure(bg=new_color)
                
                # Update any frames and labels with the new color
                for widget in pa_window.winfo_children():
                    if isinstance(widget, tk.Frame):
                        widget.configure(bg=new_color)
                        for subwidget in widget.winfo_children():
                            if isinstance(subwidget, tk.Label):
                                subwidget.configure(bg=new_color)
                
                # Continue blinking only if window still exists
                if pa_window.winfo_exists():
                    pa_window.after(500, toggle_bg)
            
            # Set up the content frame
            content_frame = tk.Frame(pa_window, bg="#990000", padx=30, pady=30)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # Warning icon and title
            warning_icon = tk.Label(content_frame, text="⚠️", font=("Arial", 64), bg="#990000", fg="#FFFF00")
            warning_icon.pack(pady=(20, 10))
            
            title_label = tk.Label(content_frame, text="CRITICAL ALERT", font=("Arial", 24, "bold"), bg="#990000", fg="white")
            title_label.pack(pady=(0, 20))
            
            # Alert message
            message_text = tk.Label(content_frame, 
                                  text=OXYGEN_DEPLETION_MODAL_BODY,
                                  font=("Arial", 14), bg="#990000", fg="white", justify=tk.CENTER, wraplength=500)
            message_text.pack(pady=20)
            
            # Acknowledge button - extra large and prominent
            acknowledge_button = tk.Button(content_frame, text="ACKNOWLEDGE", font=("Arial", 24, "bold"), 
                                         bg="#FFFF00", fg="#FF0000", padx=40, pady=20,
                                         width=20, height=10,
                                         command=close_announcement)
            acknowledge_button.pack(pady=10)
            
            # Bind keyboard events
            pa_window.bind("<Escape>", close_announcement)
            pa_window.bind("<Return>", close_announcement)

            # Start blinking effect
            pa_window.after(100, toggle_bg)
            
        except Exception as e:
            print(f"Error announcing oxygen depletion: {e}")
            # Reset flag if there's an error so it can try again
            self.announcement_active = False
            # Show a simple warning as fallback
            messagebox.showwarning(
                OXYGEN_DEPLETION_FOLLOWUP_TITLE,
                OXYGEN_DEPLETION_FOLLOWUP_MESSAGE,
                parent=self.engineering_window,
            )
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, DOOR_KEY, self.engineering_window)
    
    def on_closing(self):
        try_leave_through_door(
            self.engineering_window,
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
                "label": "Enter Engineering Station",
                "command": self.access_engineering_station,
            }],
            show_room_options=self.show_room_options,
            toggle_door_lock=self.toggle_door_lock,
            before_show=before_show,
        )

    def show_station_menu(self):
        """Return to main station menu options"""
        self._build_station_menu()

