import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import random
import math

# Import item definitions
from .items import get_item_definition, get_items_by_category
from .power_constants import SYSTEM_POWER_RATES
from .door_control import toggle_door_lock as toggle_room_door_lock, is_door_locked

class MedBay:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        # Create a new toplevel window
        self.medbay_window = tk.Toplevel(parent_window)
        self.medbay_window.title("MedBay")
        self.medbay_window.geometry("800x600")
        self.medbay_window.configure(bg="black")
        
        # Store references
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew # Store crew data
        self.return_callback = return_callback
        
        # Bind window closing
        self.medbay_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Ensure this window stays on top
        self.medbay_window.transient(parent_window)
        self.medbay_window.grab_set()
        self.medbay_window.focus_force()
        
        # Center window on screen after window is configured
        self.medbay_window.update_idletasks()
        width = 800
        height = 600
        x = (self.medbay_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.medbay_window.winfo_screenheight() // 2) - (height // 2)
        self.medbay_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        room_label = tk.Label(self.medbay_window, text="Station Medical Bay", font=("Arial", 24), bg="black", fg="white")
        room_label.pack(pady=30)
        
        # Description
        desc_label = tk.Label(self.medbay_window, 
                              text="The medical bay is clean and orderly. Various medical equipment lines the walls, and a few examination beds are visible. The station's medical staff handle everything from routine checkups to emergency trauma care.",
                              font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Room actions
        self.button_frame = tk.Frame(self.medbay_window, bg="black")
        self.button_frame.pack(pady=20)
        
        # Check if user has special access
        has_medbay_access = "permissions" in self.player_data and self.player_data["permissions"].get("medbay_station", False)
        
        if has_medbay_access:
            # Show station access button for authorized personnel
            station_btn = tk.Button(self.button_frame, text="Enter MedBay Station", font=("Arial", 14), width=20, command=self.access_medbay_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()
        
        # Exit button
        exit_btn = tk.Button(self.medbay_window, text="Exit Room", font=("Arial", 14), width=15, command=self.on_closing)
        exit_btn.pack(pady=20)
    
    def show_room_options(self):
        """Show regular room options that all players can access"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Health check option
        health_check_btn = tk.Button(self.button_frame, text="Request Health Check", font=("Arial", 14), width=20, command=self.health_check)
        health_check_btn.pack(pady=10)
        
        # Talk to doctor option
        talk_doctor_btn = tk.Button(self.button_frame, text="Talk to Doctor", font=("Arial", 14), width=20, command=self.talk_to_doctor)
        talk_doctor_btn.pack(pady=10)
        
        # Only show "Back to Station Menu" if player has access
        has_medbay_access = "permissions" in self.player_data and self.player_data["permissions"].get("medbay_station", False)
        if has_medbay_access:
            # Back to station menu button
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)
    
    def health_check(self):
        # Get the player's limb health data
        limbs = self.player_data.get("limbs", {})
        
        # Create health report
        health_report = "Health Check Results:\n\n"
        
        if not limbs:
            health_report += "No limb health data available."
        else:
            # Calculate overall health percentage
            total_health = sum(limbs.values())
            max_health = len(limbs) * 100
            overall_health = (total_health / max_health) * 100
            
            health_report += f"Overall Health: {overall_health:.1f}%\n\n"
            health_report += "Limb Status:\n"
            
            # Track issues for detailed notes
            injured_limbs = []
            critical_limbs = []
            
            # Add limb statuses
            for limb, health in limbs.items():
                limb_name = limb.replace('_', ' ').title()
                if health > 75:
                    status = "Healthy"
                elif health > 40:
                    status = "Injured"
                    injured_limbs.append(limb_name)
                else:
                    status = "Critical"
                    critical_limbs.append(limb_name)
                health_report += f"- {limb_name}: {health}% ({status})\n"
            
            health_report += "\nRecommendation: "
            if overall_health < 60:
                health_report += "Medical attention recommended."
            else:
                health_report += "No immediate medical attention required."
            
            # Add detailed notes if health is below 100%
            if overall_health < 100:
                health_report += "\n\nDetailed Notes:"
                
                if critical_limbs:
                    health_report += f"\n• Critical damage detected in {', '.join(critical_limbs)}. "
                    health_report += "Immediate treatment required."
                
                if injured_limbs:
                    health_report += f"\n• Moderate trauma detected in {', '.join(injured_limbs)}. "
                    health_report += "Rest and treatment advised."
                
                if overall_health < 75:
                    health_report += "\n• Movement and performance significantly impaired."
                elif overall_health < 90:
                    health_report += "\n• Some physical activities may be difficult."
                
                # Treatment options
                health_report += "\n\nTreatment Options:"
                health_report += "\n• Self-healing through rest"
                health_report += "\n• Medical treatment by qualified doctor (50 credits)"
                if "permissions" in self.player_data and self.player_data["permissions"].get("medbay_station", False):
                    health_report += "\n• Advanced treatment available at MedBay Station"
        
        # Show dialog with the room window as parent to keep focus within the room
        self.medbay_window.after(10, lambda: messagebox.showinfo("Medical Scan", health_report, parent=self.medbay_window))
        # Make sure the window stays on top after dialog
        self.medbay_window.after(20, self.medbay_window.lift)
        self.medbay_window.focus_force()
    
    def talk_to_doctor(self):
        """Talk to a doctor who can provide healing for a fee based on damage"""
        # Calculate total damage
        total_blunt_damage = 0
        if "limbs" in self.player_data:
            for limb_health in self.player_data["limbs"].values():
                total_blunt_damage += (100 - limb_health)
                
        burn_damage = self.player_data["damage"].get("burn", 0)
        poison_damage = self.player_data["damage"].get("poison", 0)
        oxygen_damage = self.player_data["damage"].get("oxygen", 0)
        
        # Calculate costs based on damage (rounding up)
        blunt_cost = math.ceil(total_blunt_damage / 3) if total_blunt_damage > 0 else 0
        burn_cost = math.ceil(burn_damage) if burn_damage > 0 else 0
        poison_cost = math.ceil(poison_damage / 3) * 2 if poison_damage > 0 else 0
        oxygen_cost = math.ceil(oxygen_damage) if oxygen_damage > 0 else 0
        
        total_cost = blunt_cost + burn_cost + poison_cost + oxygen_cost
        
        if total_cost == 0:
            # No injuries to heal
            message = "The doctor examines you. 'You're in perfect health! No treatment needed.'"
            self.medbay_window.after(10, lambda: messagebox.showinfo("Doctor", message, parent=self.medbay_window))
            return
            
        # Injuries need healing
        message = f"The doctor examines you. 'I can treat all your injuries for {total_cost} credits. Would you like to proceed?'"
        
        # Create a custom dialog with Yes/No buttons
        dialog = tk.Toplevel(self.medbay_window)
        dialog.title("Doctor")
        dialog.geometry("400x150")
        dialog.configure(bg="black")
        dialog.transient(self.medbay_window)
        dialog.grab_set()
        
        # Center the dialog relative to the parent window
        dialog.update_idletasks()
        width = 400
        height = 150
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Message label
        msg_label = tk.Label(dialog, text=message, font=("Arial", 12), bg="black", fg="white", wraplength=380)
        msg_label.pack(pady=20)
        
        # Buttons frame
        btn_frame = tk.Frame(dialog, bg="black")
        btn_frame.pack(pady=10)
        
        # Yes button - passes the calculated total_cost to pay_for_healing
        yes_btn = tk.Button(btn_frame, text=f"Yes ({total_cost} credits)", font=("Arial", 12),
                          command=lambda: self.pay_for_healing(dialog, total_cost))
        yes_btn.pack(side=tk.LEFT, padx=10)
        
        # No button
        no_btn = tk.Button(btn_frame, text="No", font=("Arial", 12),
                         command=dialog.destroy)
        no_btn.pack(side=tk.LEFT, padx=10)
    
    def pay_for_healing(self, dialog, total_cost):
        """Pay credits for healing based on the calculated cost"""
        # Check if player has enough credits
        if self.player_data["credits"] < total_cost:
            message = "You don't have enough credits for treatment. Come back when you can afford it."
            dialog.destroy()
            self.medbay_window.after(10, lambda: messagebox.showinfo("Doctor", message, parent=self.medbay_window))
            return
        
        # Deduct credits
        self.player_data["credits"] -= total_cost
        
        # Store original health values for report
        original_health = self.player_data["limbs"].copy()
        original_damage = self.player_data["damage"].copy()
        
        # Heal all limbs to 100%
        for limb in self.player_data["limbs"]:
            self.player_data["limbs"][limb] = 100
            
        # Heal all damage types to 0%
        for damage_type in self.player_data["damage"]:
            self.player_data["damage"][damage_type] = 0
        
        # Close the dialog
        dialog.destroy()
        
        # Show confirmation message
        message = f"You pay {total_cost} credits. The doctor treats your injuries. You feel much better now."
        self.medbay_window.after(10, lambda: messagebox.showinfo("Treatment Complete", message, parent=self.medbay_window))
        
        # Prepare healing report (optional, could be shown in notes)
        injured_limbs = [limb.replace('_', ' ').title() for limb, health in original_health.items() if health < 100]
        injured_damage = [dtype.title() for dtype, value in original_damage.items() if value > 0]
        has_injuries = bool(injured_limbs) or bool(injured_damage)
        
        # Add note about the healing transaction
        if "notes" in self.player_data:
            if has_injuries:
                healed_parts = []
                if injured_limbs:
                    healed_parts.append(f"Blunt Damage ({', '.join(injured_limbs)}) fully healed.")
                if injured_damage:
                    healed_parts.append(f"Other Damage ({', '.join(injured_damage)}) fully healed.")
                note_text = f"Paid {total_cost} credits for medical treatment. {'. '.join(healed_parts)}"
            else:
                note_text = f"Paid {total_cost} credits for medical examination. No injuries were found."
            
            self.add_note(note_text)
        
        # Make sure the window stays on top after dialog
        self.medbay_window.after(20, self.medbay_window.lift)
        self.medbay_window.focus_force()
    
    def access_medbay_station(self):
        # Show medbay station options for authorized personnel
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Add healing option
        heal_btn = tk.Button(self.button_frame, text="Heal Injuries", font=("Arial", 14), width=20, command=self.heal_player)
        heal_btn.pack(pady=10)
        
        # Add Crew Vitals Button
        vitals_btn = tk.Button(self.button_frame, text="Check Crew Vitals", font=("Arial", 14), width=20, command=self.show_crew_vitals)
        vitals_btn.pack(pady=10)
        
        # Back button
        back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                           command=self.show_station_menu)
        back_btn.pack(pady=10)
    
    def heal_player(self):
        """Heal the player's limbs to full health"""
        # Check if player has limb data
        if "limbs" in self.player_data:
            # Store original health values for report
            original_health = self.player_data["limbs"].copy()
            
            # Heal all limbs to 100%
            for limb in self.player_data["limbs"]:
                self.player_data["limbs"][limb] = 100
            
            # Create healing report
            healing_report = "Medical Treatment Results:\n\n"
            healing_report += "All limbs restored to full health.\n\n"
            healing_report += "Previous Status:\n"
            
            # Check if there were any injuries to track
            had_injuries = False
            injury_details = []
            
            # Show previous health values
            for limb, health in original_health.items():
                limb_name = limb.replace('_', ' ').title()
                healing_report += f"- {limb_name}: {health}% → 100%\n"
                
                # Track injuries for note
                if health < 100:
                    had_injuries = True
                    injury_details.append(f"{limb_name} ({health}% → 100%)")
            
            # Show dialog with healing results
            self.medbay_window.after(10, lambda: messagebox.showinfo("Medical Treatment", healing_report, parent=self.medbay_window))
            
            # Add note about healing if there were injuries
            if had_injuries and "notes" in self.player_data:
                note_text = f"Received advanced medical treatment at MedBay Station. Healed: {', '.join(injury_details)}"
                
                # Add note
                self.player_data["notes"].append({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "text": note_text
                })
                
        else:
            self.medbay_window.after(10, lambda: messagebox.showinfo("Medical Treatment", "No injuries to treat.", parent=self.medbay_window))
        
        # Make sure the window stays on top after dialog
        self.medbay_window.after(20, self.medbay_window.lift)
        self.medbay_window.focus_force()
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, "0,6", self.medbay_window)
    
    def on_closing(self):
        # Check if the door is locked
        door_key = "0,6"  # MedBay door
        if is_door_locked(self.player_data, door_key):
            self.medbay_window.after(10, lambda: messagebox.showinfo("Locked Door", "The door is locked. You must unlock it before leaving.", parent=self.medbay_window))
            # Make sure the window stays on top after dialog
            self.medbay_window.after(20, self.medbay_window.lift)
            self.medbay_window.focus_force()
            return
        
        # Release grab before closing
        self.medbay_window.grab_release()
        
        # Call return callback with player and crew data
        self.return_callback(self.player_data, self.station_crew)
        
        # Destroy the window
        self.medbay_window.destroy()

    def show_station_menu(self):
        """Return to main station menu options"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Check if user has special access
        has_medbay_access = "permissions" in self.player_data and self.player_data["permissions"].get("medbay_station", False)
        
        if has_medbay_access:
            # Show station access button for authorized personnel
            station_btn = tk.Button(self.button_frame, text="Enter MedBay Station", font=("Arial", 14), width=20, command=self.access_medbay_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()

    def show_crew_vitals(self):
        """Display a window showing the vitals of all crew members."""
        vitals_window = tk.Toplevel(self.medbay_window)
        vitals_window.title("Crew Vitals Monitor")
        vitals_window.geometry("900x700") # Wider window
        vitals_window.configure(bg="black")
        vitals_window.transient(self.medbay_window)
        vitals_window.grab_set()

        # Center the popup
        vitals_window.update_idletasks()
        width = 900
        height = 700
        x = (vitals_window.winfo_screenwidth() // 2) - (width // 2)
        y = (vitals_window.winfo_screenheight() // 2) - (height // 2)
        vitals_window.geometry(f"{width}x{height}+{x}+{y}")

        # --- Header ---
        header_frame = tk.Frame(vitals_window, bg="black")
        header_frame.pack(pady=10)
        title_label = tk.Label(header_frame, text="Crew Vitals Monitor", font=("Arial", 18, "bold"), bg="black", fg="white")
        title_label.pack(side=tk.LEFT, padx=10)

        # Toggle Details Button
        details_visible = tk.BooleanVar(value=False)
        details_button = tk.Button(header_frame, text="Show Details", font=("Arial", 10),
                                   command=lambda: toggle_details_view(details_visible, details_button, crew_frame))
        details_button.pack(side=tk.LEFT, padx=10)

        # --- Scrollable Crew Area ---
        canvas_frame = tk.Frame(vitals_window, bg="black")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(canvas_frame, bg="black", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        crew_frame = tk.Frame(canvas, bg="black") # Frame to hold crew info
        canvas_window = canvas.create_window((0, 0), window=crew_frame, anchor="nw")

        # --- Populate Crew Vitals ---
        all_crew = [self.player_data] + self.station_crew
        crew_widgets = {} # To store widgets for toggling details

        def update_crew_display(show_details):
            # Clear previous widgets
            for widget in crew_frame.winfo_children():
                widget.destroy()
            crew_widgets.clear()

            for i, crew_member in enumerate(all_crew):
                name = crew_member.get("name", "N/A")
                job = crew_member.get("job", "N/A")
                is_player = (name == self.player_data.get("name"))

                # Frame for each crew member
                member_frame = tk.Frame(crew_frame, bg="#111111" if i % 2 == 0 else "#222222", bd=1, relief=tk.SOLID)
                member_frame.pack(fill=tk.X, pady=2, padx=2)

                # --- Compact View Row ---
                compact_frame = tk.Frame(member_frame, bg=member_frame.cget("bg"))
                compact_frame.pack(fill=tk.X, pady=3, padx=5)

                name_job_text = f"{name} ({job})"
                name_label = tk.Label(compact_frame, text=name_job_text, font=("Arial", 11, "bold" if is_player else "normal"),
                                      bg=compact_frame.cget("bg"), fg="light green" if is_player else "white", anchor="w")
                name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

                # Calculate overall health status
                limbs = crew_member.get("limbs", {})
                damage = crew_member.get("damage", {})
                total_limb_health = sum(limbs.values())
                max_limb_health = len(limbs) * 100 if limbs else 1 # Avoid division by zero
                avg_limb_health = (total_limb_health / max_limb_health) * 100 if max_limb_health > 0 else 0

                total_damage_percent = sum(damage.values())
                max_damage_percent = len(damage) * 100 if damage else 1
                avg_damage_taken = (total_damage_percent / max_damage_percent) * 100 if max_damage_percent > 0 else 0
                # Simplified overall health metric
                overall_health = avg_limb_health * (1 - (avg_damage_taken / 100)) # Factor in damage

                status = "Healthy"
                status_color = "green"
                if overall_health < 40:
                    status = "Critical"
                    status_color = "red"
                elif overall_health < 75:
                    status = "Injured"
                    status_color = "yellow"

                status_label = tk.Label(compact_frame, text=status, font=("Arial", 11, "bold"),
                                        bg=status_color, fg="black", width=10)
                status_label.pack(side=tk.RIGHT, padx=5)

                # --- Detailed View Frame (Initially hidden) ---
                detail_frame = tk.Frame(member_frame, bg=member_frame.cget("bg"))
                # Packed later by toggle function if show_details is True

                # Limb Health Details
                limbs_title = tk.Label(detail_frame, text="Limb Health:", font=("Arial", 10, "bold"),
                                       bg=detail_frame.cget("bg"), fg="cyan")
                limbs_title.grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
                col_count = 0
                row_count = 1
                for limb, health in limbs.items():
                     limb_name = limb.replace('_', ' ').title()
                     color = "green" if health > 75 else "yellow" if health > 40 else "red"
                     limb_label = tk.Label(detail_frame, text=f"{limb_name}: {health}%", font=("Arial", 9),
                                           bg=detail_frame.cget("bg"), fg=color)
                     limb_label.grid(row=row_count, column=col_count, sticky="w", padx=10)
                     col_count += 1
                     if col_count >= 3: # 3 columns for limbs
                         col_count = 0
                         row_count += 1

                # Other Damage Details
                damage_title = tk.Label(detail_frame, text="Other Damage:", font=("Arial", 10, "bold"),
                                       bg=detail_frame.cget("bg"), fg="cyan")
                damage_title.grid(row=row_count, column=0, sticky="w", padx=10, pady=(5,0))
                row_count += 1
                col_count = 0
                damage_types = {"burn": "🔥", "poison": "☣️", "oxygen": "💨"}
                for dtype, icon in damage_types.items():
                     damage_val = damage.get(dtype, 0)
                     color = "green" if damage_val < 10 else "yellow" if damage_val < 30 else "orange" if damage_val < 60 else "red"
                     damage_label = tk.Label(detail_frame, text=f"{icon} {dtype.title()}: {damage_val:.1f}%", font=("Arial", 9),
                                            bg=detail_frame.cget("bg"), fg=color)
                     damage_label.grid(row=row_count, column=col_count, sticky="w", padx=10)
                     col_count += 1
                     if col_count >= 3:
                         col_count = 0
                         row_count += 1

                crew_widgets[i] = detail_frame # Store detail frame for toggling

                if show_details:
                    detail_frame.pack(fill=tk.X, pady=(0, 5), padx=5) # Show details

            # --- End Loop ---
            # Update scrollregion after populating
            crew_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.yview_moveto(0) # Scroll to top

        def toggle_details_view(var, button, frame):
            var.set(not var.get()) # Toggle the boolean
            if var.get():
                button.config(text="Hide Details")
                update_crew_display(show_details=True)
            else:
                button.config(text="Show Details")
                update_crew_display(show_details=False)

        # Initial population (compact view)
        update_crew_display(show_details=False)

        # --- Mousewheel Scrolling ---
        def _on_vitals_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        vitals_window.bind("<MouseWheel>", _on_vitals_mousewheel)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width)) # Adjust frame width

        # --- Close Button ---
        close_btn = tk.Button(vitals_window, text="Close", font=("Arial", 12), command=vitals_window.destroy)
        close_btn.pack(pady=10)

        # --- Cleanup on Close ---
        orig_destroy = vitals_window.destroy
        def _destroy_and_cleanup():
            try:
                vitals_window.unbind("<MouseWheel>")
            except:
                pass
            orig_destroy()
        vitals_window.destroy = _destroy_and_cleanup

    # Add add_note method to MedBay class if it doesn't exist
    # (Assuming it might be called from pay_for_healing or other future methods)
    def add_note(self, text):
        """Helper method to add notes to player_data"""
        if "notes" not in self.player_data:
            self.player_data["notes"] = []
        self.player_data["notes"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "text": text
        })

class Bridge:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        # Create a new toplevel window
        self.bridge_window = tk.Toplevel(parent_window)
        self.bridge_window.title("Bridge")
        self.bridge_window.geometry("800x600")
        self.bridge_window.configure(bg="black")
        
        # Store references
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew # Store crew data
        self.return_callback = return_callback
        
        # Bind window closing
        self.bridge_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Ensure this window stays on top
        self.bridge_window.transient(parent_window)
        self.bridge_window.grab_set()
        self.bridge_window.focus_force()
        
        # Center window on screen after window is configured
        self.bridge_window.update_idletasks()
        width = 800
        height = 600
        x = (self.bridge_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.bridge_window.winfo_screenheight() // 2) - (height // 2)
        self.bridge_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        room_label = tk.Label(self.bridge_window, text="Station Bridge", font=("Arial", 24), bg="black", fg="white")
        room_label.pack(pady=30)
        
        # Description
        desc_label = tk.Label(self.bridge_window, 
                              text="The bridge is the command center of the station. Multiple workstations with monitors displaying various station systems are arranged around the room. This is where the Captain and Department Heads coordinate station operations.",
                              font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Room actions
        self.button_frame = tk.Frame(self.bridge_window, bg="black")
        self.button_frame.pack(pady=20)
        
        # Check if user has special access (Captain or HoP)
        is_captain = self.player_data.get("job") == "Captain"
        is_hop = self.player_data.get("job") == "Head of Personnel"
        has_captain_access = is_captain or "permissions" in self.player_data and self.player_data["permissions"].get("bridge_station", False)
        has_hop_access = is_captain or is_hop or "permissions" in self.player_data and self.player_data["permissions"].get("hop_station", False)
        
        if has_captain_access or has_hop_access:
            # Show the appropriate station access buttons
            if has_captain_access:
                captain_btn = tk.Button(self.button_frame, text="Enter Captain's Station", font=("Arial", 14), width=20, command=self.access_captain_station)
                captain_btn.pack(pady=10)
            
            if has_hop_access:
                hop_btn = tk.Button(self.button_frame, text="Enter HoP's Station", font=("Arial", 14), width=20, command=self.access_hop_station)
                hop_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()
        
        # Exit button
        exit_btn = tk.Button(self.bridge_window, text="Exit Room", font=("Arial", 14), width=15, command=self.on_closing)
        exit_btn.pack(pady=20)
    
    def show_room_options(self):
        """Show regular room options that all players can access"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Talk to leadership option
        talk_btn = tk.Button(self.button_frame, text="Talk to Ship Leadership", font=("Arial", 14), width=20, command=self.talk_to_leadership)
        talk_btn.pack(pady=10)
        
        # Only show "Back to Station Menu" if player has special access
        is_captain = self.player_data.get("job") == "Captain"
        is_hop = self.player_data.get("job") == "Head of Personnel"
        has_captain_access = is_captain or "permissions" in self.player_data and self.player_data["permissions"].get("bridge_station", False)
        has_hop_access = is_captain or is_hop or "permissions" in self.player_data and self.player_data["permissions"].get("hop_station", False)
        
        if has_captain_access or has_hop_access:
            # Back to station menu button
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)
    
    def talk_to_leadership(self):
        # Show dialog with the room window as parent to keep focus within the room
        self.bridge_window.after(10, lambda: messagebox.showinfo("Bridge", "Captain and Department Heads are not in.", parent=self.bridge_window))
        # Make sure the window stays on top after dialog
        self.bridge_window.after(20, self.bridge_window.lift)
        self.bridge_window.focus_force()
    
    def access_captain_station(self):
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Add captain station options
        station_label = tk.Label(self.button_frame, text="Captain's Station", font=("Arial", 16, "bold"), bg="black", fg="white")
        station_label.pack(pady=10)
        
        # Add station control buttons
        status_btn = tk.Button(self.button_frame, text="Station Status", font=("Arial", 14), width=20, 
                             command=lambda: messagebox.showinfo("Station Status", "All systems nominal. No critical alerts.", parent=self.bridge_window))
        status_btn.pack(pady=5)
        
        security_btn = tk.Button(self.button_frame, text="Security Alerts", font=("Arial", 14), width=20, 
                               command=lambda: messagebox.showinfo("Security Alerts", "No security alerts reported.", parent=self.bridge_window))
        security_btn.pack(pady=5)
        
        manifest_btn = tk.Button(self.button_frame, text="Crew Manifest", font=("Arial", 14), width=20, command=self.show_crew_manifest)
        manifest_btn.pack(pady=5)
        
        emergency_btn = tk.Button(self.button_frame, text="Emergency Protocols", font=("Arial", 14), width=20, 
                                command=lambda: messagebox.showinfo("Emergency Protocols", "Emergency protocols ready for activation if needed.", parent=self.bridge_window))
        emergency_btn.pack(pady=5)
        
        # Back button
        back_btn = tk.Button(self.button_frame, text="Back to Bridge Menu", font=("Arial", 14), width=20, command=self.show_station_menu)
        back_btn.pack(pady=15)
        
        # Make sure the window stays on top after dialog
        self.bridge_window.after(20, self.bridge_window.lift)
        self.bridge_window.focus_force()
    
    def access_hop_station(self):
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Add HoP station options
        station_label = tk.Label(self.button_frame, text="Head of Personnel Station", font=("Arial", 16, "bold"), bg="black", fg="white")
        station_label.pack(pady=10)
        
        # Add station control buttons
        manifest_btn = tk.Button(self.button_frame, text="Crew Manifest", font=("Arial", 14), width=20, command=self.show_crew_manifest)
        manifest_btn.pack(pady=5)
        
        assignments_btn = tk.Button(self.button_frame, text="Job Assignments", font=("Arial", 14), width=20, 
                                  command=lambda: messagebox.showinfo("Job Assignments", "All current job positions are filled.", parent=self.bridge_window))
        assignments_btn.pack(pady=5)
        
        access_btn = tk.Button(self.button_frame, text="Access Control", font=("Arial", 14), width=20, 
                             command=lambda: messagebox.showinfo("Access Control", "Access control system ready. No pending requests.", parent=self.bridge_window))
        access_btn.pack(pady=5)
        
        records_btn = tk.Button(self.button_frame, text="Personnel Records", font=("Arial", 14), width=20, 
                              command=lambda: messagebox.showinfo("Personnel Records", "Personnel records database online. All records up to date.", parent=self.bridge_window))
        records_btn.pack(pady=5)
        
        # Back button
        back_btn = tk.Button(self.button_frame, text="Back to Bridge Menu", font=("Arial", 14), width=20, command=self.show_station_menu)
        back_btn.pack(pady=15)
        
        # Make sure the window stays on top after dialog
        self.bridge_window.after(20, self.bridge_window.lift)
        self.bridge_window.focus_force()
    
    def show_crew_manifest(self):
        """Display the crew manifest with department listings, including NPCs"""
        # Create a new toplevel window
        manifest_window = tk.Toplevel(self.bridge_window)
        manifest_window.title("Crew Manifest")
        manifest_window.geometry("600x500")
        manifest_window.configure(bg="black")
        manifest_window.transient(self.bridge_window)
        manifest_window.grab_set()
        
        # Center the popup
        manifest_window.update_idletasks()
        width = 600
        height = 500
        x = (manifest_window.winfo_screenwidth() // 2) - (width // 2)
        y = (manifest_window.winfo_screenheight() // 2) - (height // 2)
        manifest_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        title_label = tk.Label(manifest_window, text="Station Crew Manifest", font=("Arial", 18, "bold"), bg="black", fg="white")
        title_label.pack(pady=10)
        
        # Create scrollable frame for crew list
        frame = tk.Frame(manifest_window, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text widget for manifest
        manifest_text = tk.Text(frame, bg="black", fg="white", font=("Arial", 12),
                             width=50, height=20, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        manifest_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=manifest_text.yview)
        
        # Configure text tags
        manifest_text.tag_configure("header", font=("Arial", 14, "bold"), foreground="yellow")
        manifest_text.tag_configure("department", font=("Arial", 12, "bold"), foreground="light blue")
        manifest_text.tag_configure("name", font=("Arial", 11))
        manifest_text.tag_configure("player", font=("Arial", 11, "bold"), foreground="light green")
        manifest_text.tag_configure("npc", font=("Arial", 11), foreground="cyan") # Tag for NPCs

        manifest_text.insert(tk.END, "STATION CREW MANIFEST\n", "header")
        manifest_text.insert(tk.END, "====================\n\n", "header")

        # Get player info
        player_name = self.player_data.get("name", "Unknown")
        player_job = self.player_data.get("job", "Unknown")

        # Combine player and NPCs for easier iteration
        all_crew = [self.player_data] + self.station_crew

        # Group crew by job for display
        departments = {
            "COMMAND": ["Captain", "Head of Personnel"],
            "SECURITY": ["Security Guard"],
            "MEDICAL": ["Doctor"],
            "ENGINEERING": ["Engineer"],
            "BOTANY": ["Botanist"],
            "SERVICE": ["Bartender"],
            "CIVILIAN": ["Staff Assistant"]
        }

        # Iterate through departments and display crew
        for dept_name, jobs_in_dept in departments.items():
            manifest_text.insert(tk.END, f"{dept_name}:\n", "department")
            found_in_dept = False
            for crew_member in all_crew:
                job = crew_member.get("job")
                name = crew_member.get("name")
                if job in jobs_in_dept:
                    found_in_dept = True
                    is_player = (name == player_name and job == player_job)
                    tag = "player" if is_player else "npc"
                    player_tag = " (YOU)" if is_player else ""
                    manifest_text.insert(tk.END, f"- {job}: {name}{player_tag}\n", tag)

            if not found_in_dept:
                 manifest_text.insert(tk.END, "- (No personnel assigned)\n", "name")
            manifest_text.insert(tk.END, "\n") # Add space between departments

        # Make text widget read-only
        manifest_text.config(state=tk.DISABLED)
        
        # Mouse wheel binding for scrolling
        def _on_manifest_mousewheel(event):
            try:
                manifest_text.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Ignore errors if the text widget was destroyed
        
        # Bind mousewheel to manifest text
        manifest_window.bind("<MouseWheel>", _on_manifest_mousewheel)
        
        # Override destroy method to cleanup bindings
        orig_destroy = manifest_window.destroy
        def _destroy_and_cleanup():
            try:
                manifest_window.unbind("<MouseWheel>")
            except:
                pass
            orig_destroy()
        
        manifest_window.destroy = _destroy_and_cleanup
        
        # Close button
        close_btn = tk.Button(manifest_window, text="Close", font=("Arial", 12), command=manifest_window.destroy)
        close_btn.pack(pady=10)
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, "6,0", self.bridge_window)
    
    def on_closing(self):
        # Check if the door is locked
        door_key = "6,0"  # Bridge door
        if is_door_locked(self.player_data, door_key):
            self.bridge_window.after(10, lambda: messagebox.showinfo("Locked Door", "The door is locked. You must unlock it before leaving.", parent=self.bridge_window))
            # Make sure the window stays on top after dialog
            self.bridge_window.after(20, self.bridge_window.lift)
            self.bridge_window.focus_force()
            return
        
        # Release grab before closing
        self.bridge_window.grab_release()
        
        # Call return callback with player and crew data
        self.return_callback(self.player_data, self.station_crew)
        
        # Destroy the window
        self.bridge_window.destroy()

    def show_station_menu(self):
        """Return to main station menu options"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Check if user has special access
        is_captain = self.player_data.get("job") == "Captain"
        is_hop = self.player_data.get("job") == "Head of Personnel"
        has_captain_access = is_captain or "permissions" in self.player_data and self.player_data["permissions"].get("bridge_station", False)
        has_hop_access = is_captain or is_hop or "permissions" in self.player_data and self.player_data["permissions"].get("hop_station", False)
        
        if has_captain_access or has_hop_access:
            # Show the appropriate station access buttons
            if has_captain_access:
                captain_btn = tk.Button(self.button_frame, text="Enter Captain's Station", font=("Arial", 14), width=20, command=self.access_captain_station)
                captain_btn.pack(pady=10)
            
            if has_hop_access:
                hop_btn = tk.Button(self.button_frame, text="Enter HoP's Station", font=("Arial", 14), width=20, command=self.access_hop_station)
                hop_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()

class Security:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        # Create a new toplevel window
        self.security_window = tk.Toplevel(parent_window)
        self.security_window.title("Security")
        self.security_window.geometry("800x600")
        self.security_window.configure(bg="black")
        
        # Store references
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew # Store crew data
        self.return_callback = return_callback
        
        # Bind window closing
        self.security_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Ensure this window stays on top
        self.security_window.transient(parent_window)
        self.security_window.grab_set()
        self.security_window.focus_force()
        
        # Center window on screen after window is configured
        self.security_window.update_idletasks()
        width = 800
        height = 600
        x = (self.security_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.security_window.winfo_screenheight() // 2) - (height // 2)
        self.security_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        room_label = tk.Label(self.security_window, text="Station Security Office", font=("Arial", 24), bg="black", fg="white")
        room_label.pack(pady=30)
        
        # Description
        desc_label = tk.Label(self.security_window, 
                              text="The security office is filled with monitoring equipment. Screens showing various parts of the station line the walls. A few security officers monitor the feeds, while weapon lockers are secured along one wall.",
                              font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Room actions
        self.button_frame = tk.Frame(self.security_window, bg="black")
        self.button_frame.pack(pady=20)
        
        # Check if user has special access
        has_security_access = "permissions" in self.player_data and self.player_data["permissions"].get("security_station", False)
        
        if has_security_access:
            # Show station access button for authorized personnel
            station_btn = tk.Button(self.button_frame, text="Enter Security Station", font=("Arial", 14), width=20, command=self.access_security_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()
        
        # Exit button
        exit_btn = tk.Button(self.security_window, text="Exit Room", font=("Arial", 14), width=15, command=self.on_closing)
        exit_btn.pack(pady=20)
    
    def show_room_options(self):
        """Show regular room options that all players can access"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Talk to guard option
        guard_btn = tk.Button(self.button_frame, text="Talk to Security Guard", font=("Arial", 14), width=20, command=self.talk_to_guard)
        guard_btn.pack(pady=10)
        
        # Only show "Back to Station Menu" if player has access
        has_security_access = "permissions" in self.player_data and self.player_data["permissions"].get("security_station", False)
        if has_security_access:
            # Back to station menu button
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)
    
    def talk_to_guard(self):
        # Show dialog with the room window as parent to keep focus within the room
        self.security_window.after(10, lambda: messagebox.showinfo("Security Guard", "The security agent waves you away without looking up from the cameras.", parent=self.security_window))
        # Make sure the window stays on top after dialog
        self.security_window.after(20, self.security_window.lift)
        self.security_window.focus_force()
    
    def access_security_station(self):
       # Make sure the window stays on top after dialog
        self.security_window.after(20, self.security_window.lift)
        self.security_window.focus_force()
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, "6,6", self.security_window)
    
    def on_closing(self):
        # Check if the door is locked
        door_key = "6,6"  # Security door
        if is_door_locked(self.player_data, door_key):
            self.security_window.after(10, lambda: messagebox.showinfo("Locked Door", "The door is locked. You must unlock it before leaving.", parent=self.security_window))
            # Make sure the window stays on top after dialog
            self.security_window.after(20, self.security_window.lift)
            self.security_window.focus_force()
            return
        
        # Release grab before closing
        self.security_window.grab_release()
        
        # Call return callback with player and crew data
        self.return_callback(self.player_data, self.station_crew)
        
        # Destroy the window
        self.security_window.destroy()

    def show_station_menu(self):
        """Return to main station menu options"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Check if user has special access
        has_security_access = "permissions" in self.player_data and self.player_data["permissions"].get("security_station", False)
        
        if has_security_access:
            # Show station access button for authorized personnel
            station_btn = tk.Button(self.button_frame, text="Enter Security Station", font=("Arial", 14), width=20, command=self.access_security_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()

class Engineering:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        # Create a new toplevel window
        self.engineering_window = tk.Toplevel(parent_window)
        self.engineering_window.title("Engineering Bay")
        self.engineering_window.geometry("800x600")
        self.engineering_window.configure(bg="black")
        
        # Store references
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew # Store crew data
        self.return_callback = return_callback
        
        # Bind window closing
        self.engineering_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Ensure this window stays on top
        self.engineering_window.transient(parent_window)
        self.engineering_window.grab_set()
        self.engineering_window.focus_force()
        
        # Center window on screen after window is configured
        self.engineering_window.update_idletasks()
        width = 800
        height = 600
        x = (self.engineering_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.engineering_window.winfo_screenheight() // 2) - (height // 2)
        self.engineering_window.geometry(f"{width}x{height}+{x}+{y}")
        
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
        
        # Check if user has special access (Engineer or Captain)
        has_engineering_access = ("permissions" in self.player_data and self.player_data["permissions"].get("engineering_station", False)) or \
                                 (self.player_data.get("job") == "Engineer") or \
                                 (self.player_data.get("job") == "Captain")
        
        if has_engineering_access:
            # Show station access button for authorized personnel
            station_btn = tk.Button(self.button_frame, text="Enter Engineering Station", font=("Arial", 14), width=20, command=self.access_engineering_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()
        
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
        
        # Only show "Back to Station Menu" if player has access
        has_engineering_access = ("permissions" in self.player_data and self.player_data["permissions"].get("engineering_station", False)) or \
                                 (self.player_data.get("job") == "Engineer") or \
                                 (self.player_data.get("job") == "Captain")
        if has_engineering_access:
            # Back to station menu button
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)
    
    def access_fabricator(self):
        """Open the fabricator interface using the new item system"""
        fab_popup = tk.Toplevel(self.engineering_window)
        fab_popup.title("Fabricator")
        fab_popup.geometry("600x450") # Adjusted height slightly
        fab_popup.configure(bg="black")
        fab_popup.transient(self.engineering_window)
        fab_popup.grab_set()
        fab_popup.focus_force() # Ensure focus

        # Center the popup
        fab_popup.update_idletasks()
        width = 600
        height = 450
        x = (fab_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (fab_popup.winfo_screenheight() // 2) - (height // 2)
        fab_popup.geometry(f"{width}x{height}+{x}+{y}")

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
                self.add_note(f"Fabricated a {item_name} ({item_id}) in Engineering.")

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
            toolbox_window = tk.Toplevel(self.engineering_window)
            toolbox_window.title("Engineering Toolbox")
            toolbox_window.geometry("600x500")
            toolbox_window.configure(bg="black")
            
            # Ensure this window stays on top
            toolbox_window.transient(self.engineering_window)
            toolbox_window.grab_set()
            
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
            panel_window = tk.Toplevel(self.engineering_window)
            panel_window.title("Engineering Panel")
            panel_window.geometry("600x500")
            panel_window.configure(bg="black")
            
            # Ensure this window stays on top
            panel_window.transient(self.engineering_window)
            panel_window.grab_set()
            
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
            
            # Power consumption rates for each system at max level (see power_constants.py)
            system_power_rates = SYSTEM_POWER_RATES
            
            # Dictionary to store power draw labels
            power_draw_labels = {}
            
            # Function to update system levels when sliders change
            def update_system_level(system_name, value):
                value = int(value)  # Convert to integer
                system_key = system_name.lower().replace(" ", "_")
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
                "text": "CRITICAL ALERT: Life support systems offline! Oxygen levels dropping to critical levels. All crew are advised to evacuate or obtain emergency oxygen supplies immediately.",
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
            pa_window = tk.Toplevel(self.engineering_window)
            pa_window.title("STATION-WIDE EMERGENCY ANNOUNCEMENT")
            pa_window.geometry("700x600") 
            pa_window.configure(bg="#990000")  # Red background for emergency
            # Ensure this window stays on top
            pa_window.transient(self.engineering_window)
            pa_window.grab_set()
            
            # Handle closing properly
            def close_announcement(*args):
                # Destroy the window
                pa_window.destroy()
                
                # Make sure the engineering panel is visible and focused
                if hasattr(self, 'engineering_window') and self.engineering_window.winfo_exists():
                    self.engineering_window.lift()
                    self.engineering_window.focus_force()
                
                # Show follow-up warning
                messagebox.showwarning("CRITICAL SYSTEM ALERT", 
                                     "STATION ALERT: Life support systems have been deactivated!\n\nOxygen levels will rapidly deplete. All crew will begin to suffer oxygen damage in approximately 1 minute.", 
                                     parent=self.engineering_window)
            
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
                                  text="LIFE SUPPORT SYSTEMS OFFLINE!\n\nOxygen levels dropping to critical levels.\n\nAll crew are advised to evacuate or obtain emergency oxygen supplies immediately.",
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
            
            # Bind window close button
            pa_window.protocol("WM_DELETE_WINDOW", close_announcement)
            
            # Center the window
            pa_window.update_idletasks()
            width = 700  # Make sure this matches the new geometry width
            height = 500  # Make sure this matches the new geometry height
            x = (pa_window.winfo_screenwidth() // 2) - (width // 2)
            y = (pa_window.winfo_screenheight() // 2) - (height // 2)
            pa_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Start blinking effect
            pa_window.after(100, toggle_bg)
            
        except Exception as e:
            print(f"Error announcing oxygen depletion: {e}")
            # Reset flag if there's an error so it can try again
            self.announcement_active = False
            # Show a simple warning as fallback
            messagebox.showwarning("CRITICAL SYSTEM ALERT", 
                                 "STATION ALERT: Life support systems have been deactivated!\n\nOxygen levels will rapidly deplete. All crew will begin to suffer oxygen damage in approximately 1 minute.", 
                                 parent=self.engineering_window)
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, "6,3", self.engineering_window)
    
    def on_closing(self):
        # Check if the door is locked
        door_key = "6,3"  # Engineering door
        if is_door_locked(self.player_data, door_key):
            self.engineering_window.after(10, lambda: messagebox.showinfo("Locked Door", "The door is locked. You must unlock it before leaving.", parent=self.engineering_window))
            # Make sure the window stays on top after dialog
            self.engineering_window.after(20, self.engineering_window.lift)
            self.engineering_window.focus_force()
            return
        
        # Release grab before closing
        self.engineering_window.grab_release()
        
        # Call return callback with player and crew data
        self.return_callback(self.player_data, self.station_crew)
        
        # Destroy the window
        self.engineering_window.destroy()

    def show_station_menu(self):
        """Return to main station menu options"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Check if user has special access (Engineer or Captain)
        has_engineering_access = ("permissions" in self.player_data and self.player_data["permissions"].get("engineering_station", False)) or \
                                 (self.player_data.get("job") == "Engineer") or \
                                 (self.player_data.get("job") == "Captain")
        
        if has_engineering_access:
            # Show station access button for authorized personnel
            station_btn = tk.Button(self.button_frame, text="Enter Engineering Station", font=("Arial", 14), width=20, command=self.access_engineering_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()

    # --- Add the missing helper method here ---
    def add_note(self, text):
        """Helper method to add notes to player_data"""
        if "notes" not in self.player_data:
            self.player_data["notes"] = []
        self.player_data["notes"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "text": text
        })
    # --- End of added method ---

class Bar:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        # Create a new toplevel window
        self.bar_window = tk.Toplevel(parent_window)
        self.bar_window.title("Bar")
        self.bar_window.geometry("800x600")
        self.bar_window.configure(bg="black")
        
        # Store references
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew # Store crew data
        self.return_callback = return_callback
        
        # Define drinks available in the bar
        self.drinks_menu = {
            "Beer": {"price": 10, "desc": "A refreshing glass of regular beer."},
            "Whiskey": {"price": 20, "desc": "A shot of strong whiskey."},
            "Wine": {"price": 15, "desc": "A fine glass of red wine."},
            "Vodka": {"price": 15, "desc": "A shot of clear, strong vodka."},
            "Gin": {"price": 15, "desc": "A botanical spirit with a distinctive flavor."},
            "Rum": {"price": 15, "desc": "A sweet spirit distilled from sugarcane."},
            "Tequila": {"price": 18, "desc": "A spirit made from the blue agave plant."},
            "Brandy": {"price": 22, "desc": "A spirit distilled from wine or fermented fruit juice."},
            "Scotch": {"price": 25, "desc": "A smoky whisky from Scotland."},
            "Orange Juice": {"price": 5, "desc": "A glass of fresh orange juice."},
            "Cranberry Juice": {"price": 5, "desc": "Tart and refreshing red juice."},
            "Pineapple Juice": {"price": 6, "desc": "Sweet tropical juice."},
            "Tonic Water": {"price": 4, "desc": "Carbonated water with quinine."},
            "Soda Water": {"price": 3, "desc": "Simple carbonated water."},
            "Cola": {"price": 4, "desc": "A sweet carbonated soft drink."},
            "Lemon Juice": {"price": 4, "desc": "Fresh, sour citrus juice."},
            "Lime Juice": {"price": 4, "desc": "Zesty green citrus juice."},
            "Grenadine": {"price": 5, "desc": "Sweet red syrup made from pomegranate."},
            "Water": {"price": 1, "desc": "A glass of water. Refreshing and healthy."}
        }
        
        # Define mixed drinks that bartenders can make
        self.mixed_drinks = {
            "Screwdriver": {
                "ingredients": ["Vodka", "Orange Juice"],
                "price": 25,
                "desc": "A classic mix of vodka and orange juice."
            },
            "Gin and Tonic": {
                "ingredients": ["Gin", "Tonic Water"],
                "price": 20,
                "desc": "A refreshing mix of gin and tonic water."
            },
            "Rum and Cola": {
                "ingredients": ["Rum", "Cola"],
                "price": 20,
                "desc": "A sweet mix of rum and cola."
            },
            "Whiskey Sour": {
                "ingredients": ["Whiskey", "Lemon Juice", "Sugar"],
                "price": 28,
                "desc": "A perfect balance of sour and sweet with whiskey."
            },
            "Margarita": {
                "ingredients": ["Tequila", "Lime Juice", "Triple Sec"],
                "price": 30,
                "desc": "A tangy, refreshing cocktail with a salt rim."
            },
            "Bloody Mary": {
                "ingredients": ["Vodka", "Tomato Juice", "Hot Sauce", "Worcestershire Sauce"],
                "price": 28,
                "desc": "A savory, spicy morning cocktail."
            },
            "Mojito": {
                "ingredients": ["Rum", "Lime Juice", "Mint", "Sugar", "Soda Water"],
                "price": 32,
                "desc": "A refreshing minty cocktail from Cuba."
            },
            "Piña Colada": {
                "ingredients": ["Rum", "Coconut Cream", "Pineapple Juice"],
                "price": 30,
                "desc": "A tropical blend that tastes like vacation."
            },
            "Cosmopolitan": {
                "ingredients": ["Vodka", "Triple Sec", "Cranberry Juice", "Lime Juice"],
                "price": 30,
                "desc": "A sophisticated, slightly tart cocktail."
            },
            "Old Fashioned": {
                "ingredients": ["Whiskey", "Bitters", "Sugar", "Water"],
                "price": 32,
                "desc": "A timeless cocktail that never goes out of style."
            },
            "Negroni": {
                "ingredients": ["Gin", "Vermouth", "Campari"],
                "price": 30,
                "desc": "A perfectly balanced bitter and sweet aperitif."
            },
            "Manhattan": {
                "ingredients": ["Whiskey", "Vermouth", "Bitters"],
                "price": 32,
                "desc": "A sophisticated whiskey cocktail."
            },
            "Mai Tai": {
                "ingredients": ["Rum", "Lime Juice", "Orange Curacao", "Orgeat Syrup"],
                "price": 35,
                "desc": "A complex tropical rum cocktail."
            },
            "Daiquiri": {
                "ingredients": ["Rum", "Lime Juice", "Sugar"],
                "price": 28,
                "desc": "A simple, refreshing rum cocktail."
            },
            "Tom Collins": {
                "ingredients": ["Gin", "Lemon Juice", "Sugar", "Soda Water"],
                "price": 28,
                "desc": "A refreshing gin cocktail served in a tall glass."
            },
            "Singapore Sling": {
                "ingredients": ["Gin", "Cherry Brandy", "Pineapple Juice", "Lime Juice", "Grenadine"],
                "price": 35,
                "desc": "A complex, fruity gin cocktail."
            },
            "Long Island Iced Tea": {
                "ingredients": ["Vodka", "Gin", "Rum", "Tequila", "Triple Sec", "Lemon Juice", "Cola"],
                "price": 40,
                "desc": "A potent mix of multiple spirits with a cola finish."
            },
            "Space Blaster": {
                "ingredients": ["Vodka", "Blue Curacao", "Sprite", "Lemon Juice"],
                "price": 35,
                "desc": "A station specialty with an electric blue color."
            },
            "Quantum Fizz": {
                "ingredients": ["Gin", "Lime Juice", "Sugar", "Mint", "Helium Gas"],
                "price": 38,
                "desc": "A unique drink that temporarily changes your voice."
            },
            "Nebula Cloud": {
                "ingredients": ["Whiskey", "Honey", "Dry Ice", "Cinnamon"],
                "price": 42,
                "desc": "A smoky cocktail that mimics a space nebula."
            }
        }
        
        # Track bartender mode
        self.bartender_mode = False
        
        # Define ingredients available for bartending
        self.available_ingredients = [
            # Spirits
            "Vodka", "Gin", "Rum", "Whiskey", "Tequila", "Brandy", "Scotch", 
            # Mixers and Juices
            "Orange Juice", "Cranberry Juice", "Pineapple Juice", "Tomato Juice",
            "Tonic Water", "Soda Water", "Cola", "Ginger Ale", "Sprite",
            # Modifiers
            "Lemon Juice", "Lime Juice", "Sugar", "Salt", "Honey", 
            "Triple Sec", "Blue Curacao", "Orange Curacao", "Grenadine",
            "Bitters", "Vermouth", "Campari", "Cherry Brandy",
            # Special ingredients
            "Mint", "Coconut Cream", "Hot Sauce", "Worcestershire Sauce", 
            "Cinnamon", "Orgeat Syrup", "Dry Ice", "Helium Gas"
        ]
        
        # Bind window closing
        self.bar_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Ensure this window stays on top
        self.bar_window.transient(parent_window)
        self.bar_window.grab_set()
        self.bar_window.focus_force()
        
        # Center window on screen after window is configured
        self.bar_window.update_idletasks()
        width = 800
        height = 600
        x = (self.bar_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.bar_window.winfo_screenheight() // 2) - (height // 2)
        self.bar_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        room_label = tk.Label(self.bar_window, text="Station Bar", font=("Arial", 24), bg="black", fg="white")
        room_label.pack(pady=30)
        
        # Description
        desc_label = tk.Label(self.bar_window, 
                              text="The station's bar is lively and well-furnished. A long counter runs along one wall, with shelves of drinks behind it. Tables and chairs are scattered about, and soft music plays in the background.",
                              font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Room actions
        self.button_frame = tk.Frame(self.bar_window, bg="black")
        self.button_frame.pack(pady=20)
        
        # Check if user is a bartender or captain
        is_bartender = self.player_data.get("job") == "Bartender"
        is_captain = self.player_data.get("job") == "Captain"
        
        if is_bartender or is_captain:
            # Add bartender station access
            station_btn = tk.Button(self.button_frame, text="Enter Bartender Station", font=("Arial", 14), width=20, command=self.access_bartender_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for bartenders and captains
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for non-bartenders
            self.show_room_options()
        
        # Exit button
        exit_btn = tk.Button(self.bar_window, text="Exit Room", font=("Arial", 14), width=15, command=self.on_closing)
        exit_btn.pack(pady=20)
    
    def show_room_options(self):
        """Show regular room options that all players can access"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Order drinks button
        order_btn = tk.Button(self.button_frame, text="Order Drinks", font=("Arial", 14), width=20, command=self.show_drink_menu)
        order_btn.pack(pady=10)
        
        # Socialize option
        socialize_btn = tk.Button(self.button_frame, text="Socialize", font=("Arial", 14), width=20, command=self.socialize)
        socialize_btn.pack(pady=10)
        
        # Only show "Back to Station Menu" if player is a bartender
        is_bartender = self.player_data.get("job") == "Bartender"
        if is_bartender:
            # Back to station menu button
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)
    
    def show_drink_menu(self):
        """Show the menu of available drinks"""
        # Create a popup for the drink menu
        menu_popup = tk.Toplevel(self.bar_window)
        menu_popup.title("Drink Menu")
        menu_popup.configure(bg="black")
        menu_popup.transient(self.bar_window)
        menu_popup.grab_set()
        
        # Center the popup
        menu_popup.update_idletasks()
        width = 700
        height = 600
        x = (menu_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (menu_popup.winfo_screenheight() // 2) - (height // 2)
        menu_popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        title_label = tk.Label(menu_popup, text="Drink Menu", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)
        
        # Current credits
        credits_label = tk.Label(menu_popup, text=f"Your credits: {self.player_data['credits']}", 
                             font=("Arial", 14), bg="black", fg="white")
        credits_label.pack(pady=5)
        
        # Create menu tabs for different categories
        tab_frame = tk.Frame(menu_popup, bg="black")
        tab_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Pin action buttons to the bottom so they stay visible
        btn_frame = tk.Frame(menu_popup, bg="black")
        btn_frame.pack(side=tk.BOTTOM, pady=10)
        
        # Create frame for the menu
        menu_frame = tk.Frame(menu_popup, bg="black")
        menu_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(menu_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create listbox for the drinks
        drink_listbox = tk.Listbox(menu_frame, bg="black", fg="white", font=("Arial", 12),
                                width=50, height=15, yscrollcommand=scrollbar.set)
        drink_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=drink_listbox.yview)
        
        # Description frame
        desc_frame = tk.Frame(menu_popup, bg="black")
        desc_frame.pack(padx=20, pady=5, fill=tk.X)
        
        # Create description label - moved before the function that uses it
        desc_label = tk.Label(desc_frame, text="Select a drink to see its description", 
                          font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack()
        
        # Organize drinks into categories
        basic_drinks = {}
        mixed_drinks = {}
        all_drinks = {}
        
        # Copy the drinks to their respective categories
        for name, details in self.drinks_menu.items():
            basic_drinks[name] = details
            all_drinks[name] = details
            
        for name, details in self.mixed_drinks.items():
            mixed_drinks[name] = details
            all_drinks[name] = details
        
        # Track the current category and selected drink
        current_category = {"drinks": all_drinks, "name": "All Drinks"}
        selected_drink = {"name": "", "details": None}
        
        # Function to populate the listbox with a category
        def show_category(category_drinks, category_name):
            # Clear the listbox
            drink_listbox.delete(0, tk.END)
            
            # Update current category
            current_category["drinks"] = category_drinks
            current_category["name"] = category_name
            
            # Add header
            drink_listbox.insert(tk.END, f"--- {category_name} ---")
            
            # Add drinks to the listbox
            for drink, details in category_drinks.items():
                drink_listbox.insert(tk.END, f"{drink} - {details['price']} credits")
            
            # Reset the description
            desc_label.config(text="Select a drink to see its description")
        
        # Create the category buttons with more spacing
        all_btn = tk.Button(tab_frame, text="All Drinks", font=("Arial", 12), width=12,
                         command=lambda: show_category(all_drinks, "All Drinks"))
        all_btn.pack(side=tk.LEFT, padx=15)
        
        basic_btn = tk.Button(tab_frame, text="Basic Drinks", font=("Arial", 12), width=12,
                           command=lambda: show_category(basic_drinks, "Basic Drinks"))
        basic_btn.pack(side=tk.LEFT, padx=15)
        
        mixed_btn = tk.Button(tab_frame, text="Mixed Drinks", font=("Arial", 12), width=12,
                           command=lambda: show_category(mixed_drinks, "Mixed Drinks"))
        mixed_btn.pack(side=tk.LEFT, padx=15)
        
        # Show all drinks by default
        show_category(all_drinks, "All Drinks")
        
        # Update description when a drink is selected
        def on_select(event):
            selection = drink_listbox.curselection()
            if not selection or selection[0] == 0:  # Skip the header
                return
                
            # Get the selected drink name by parsing the listbox entry
            index = selection[0]
            entry = drink_listbox.get(index)
            
            # Parse the entry to get the drink name
            if " - " in entry:
                drink_name = entry.split(" - ")[0]
                
                # Find the drink details in the current category
                if drink_name in current_category["drinks"]:
                    drink_details = current_category["drinks"][drink_name]
                    desc_label.config(text=drink_details['desc'])
                    
                    # Update the selected drink
                    selected_drink["name"] = drink_name
                    selected_drink["details"] = drink_details
            
        drink_listbox.bind('<<ListboxSelect>>', on_select)
        
        # Order button
        order_btn = tk.Button(btn_frame, text="Order Selected Drink", font=("Arial", 12), 
                           command=lambda: self.order_drink_from_menu(selected_drink, menu_popup, credits_label))
        order_btn.pack(side=tk.LEFT, padx=10)
        
        # Close button
        close_btn = tk.Button(btn_frame, text="Close Menu", font=("Arial", 12), command=menu_popup.destroy)
        close_btn.pack(side=tk.LEFT, padx=10)
    
    def order_drink_from_menu(self, selected_drink, popup, credits_label):
        """Process an order for a drink selected from the menu"""
        # Check if a drink is selected
        if not selected_drink["name"] or not selected_drink["details"]:
            tk.messagebox.showinfo("Selection Needed", "Please select a drink first", parent=popup)
            return
        
        drink_name = selected_drink["name"]
        drink_details = selected_drink["details"]
        
        # Check if player has enough credits
        if self.player_data['credits'] < drink_details['price']:
            tk.messagebox.showinfo("Insufficient Credits", 
                               f"You don't have enough credits to order {drink_name}.", 
                               parent=popup)
            return
        
        # Process the order
        self.player_data['credits'] -= drink_details['price']
        
        # Update the credits display
        credits_label.config(text=f"Your credits: {self.player_data['credits']}")
        
        # Add a note about the purchase
        if "notes" not in self.player_data:
            self.player_data["notes"] = []
        
        self.player_data["notes"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "text": f"Purchased {drink_name} at the bar for {drink_details['price']} credits."
        })
        
        # Show confirmation message
        tk.messagebox.showinfo("Order Successful", 
                           f"You've ordered a {drink_name} for {drink_details['price']} credits. Enjoy!", 
                           parent=popup)
    
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
        
        # Select a random conversation
        conversation = random.choice(conversations)
        
        # Show the conversation result
        self.bar_window.after(10, lambda: tk.messagebox.showinfo("Socializing", conversation, parent=self.bar_window))
        
        # Make sure the window stays on top after dialog
        self.bar_window.after(20, self.bar_window.lift)
        self.bar_window.focus_force()
    
    def access_bartender_station(self):
        """Access the bartender station for mixing drinks"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Set bartender mode
        self.bartender_mode = True
        
        # Add drink mixing button
        mix_btn = tk.Button(self.button_frame, text="Mix Drinks", font=("Arial", 14), width=20, command=self.show_drink_mixer)
        mix_btn.pack(pady=10)
        
        # Add button to view list of recipes
        recipes_btn = tk.Button(self.button_frame, text="View Recipes", font=("Arial", 14), width=20, command=self.show_recipes)
        recipes_btn.pack(pady=10)
        
        # Add button to serve premade drinks (same as regular menu)
        serve_btn = tk.Button(self.button_frame, text="Serve Regular Drinks", font=("Arial", 14), width=20, command=self.show_drink_menu)
        serve_btn.pack(pady=10)
        
        # Back button
        back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                           command=self.show_station_menu)
        back_btn.pack(pady=10)
    
    def show_drink_mixer(self):
        """Show interface for mixing custom drinks"""
        # Create a popup for mixing drinks
        mixer_popup = tk.Toplevel(self.bar_window)
        mixer_popup.title("Bartender's Drink Mixer")
        mixer_popup.geometry("800x650")  # Made larger to accommodate all content
        mixer_popup.configure(bg="black")
        mixer_popup.transient(self.bar_window)
        mixer_popup.grab_set()
        
        # Center the popup
        mixer_popup.update_idletasks()
        width = 800
        height = 650
        x = (mixer_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (mixer_popup.winfo_screenheight() // 2) - (height // 2)
        mixer_popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create main canvas with scrollbar for the entire content
        main_canvas = tk.Canvas(mixer_popup, bg="black", highlightthickness=0)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar to the main canvas
        main_scrollbar = tk.Scrollbar(mixer_popup, orient=tk.VERTICAL, command=main_canvas.yview)
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Create a frame inside the canvas to hold all content
        content_frame = tk.Frame(main_canvas, bg="black")
        content_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)
        
        # Title
        title_label = tk.Label(content_frame, text="Bartender's Drink Mixer", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)
        
        # Main frame containing left and right sections
        main_frame = tk.Frame(content_frame, bg="black")
        main_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Left section: Ingredient selection
        left_frame = tk.Frame(main_frame, bg="black", width=375)
        left_frame.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        # Ingredient category frame
        category_frame = tk.Frame(left_frame, bg="black")
        category_frame.pack(fill=tk.X, pady=5)
        
        category_label = tk.Label(category_frame, text="Ingredient Categories:", font=("Arial", 14), bg="black", fg="white")
        category_label.pack(anchor=tk.W, pady=5)
        
        # Ingredient category buttons
        btn_frame = tk.Frame(category_frame, bg="black")
        btn_frame.pack(fill=tk.X)
        
        # Group ingredients by category
        spirits = [i for i in self.available_ingredients if i in ["Vodka", "Gin", "Rum", "Whiskey", "Tequila", "Brandy", "Scotch"]]
        mixers = [i for i in self.available_ingredients if "Juice" in i or "Water" in i or "Cola" in i or "Ale" in i or "Sprite" in i]
        modifiers = [i for i in self.available_ingredients if i in ["Lemon Juice", "Lime Juice", "Sugar", "Salt", "Honey", "Triple Sec", 
                                                            "Blue Curacao", "Orange Curacao", "Grenadine", "Bitters", "Vermouth", 
                                                            "Campari", "Cherry Brandy"]]
        specials = [i for i in self.available_ingredients if i not in spirits and i not in mixers and i not in modifiers]

        # Current category tracker
        current_category = {"items": self.available_ingredients}

        # Available ingredients frame with scrollbar
        ing_frame = tk.LabelFrame(left_frame, text="Available Ingredients", font=("Arial", 12), bg="black", fg="white")
        ing_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar for ingredients
        ing_scrollbar = tk.Scrollbar(ing_frame)
        ing_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox for ingredients
        ing_listbox = tk.Listbox(ing_frame, bg="black", fg="white", font=("Arial", 12),
                              width=20, height=12, yscrollcommand=ing_scrollbar.set)
        ing_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ing_scrollbar.config(command=ing_listbox.yview)
        
        # Function to update the ingredients listbox based on category
        def show_category(items, category_name):
            # Clear the listbox
            ing_listbox.delete(0, tk.END)
            
            # Update current category
            current_category["items"] = items
            
            # Add header
            ing_listbox.insert(tk.END, f"--- {category_name} ---")
            
            # Add sorted ingredients to the listbox
            for item in sorted(items):
                ing_listbox.insert(tk.END, item)
        
        # Create category buttons
        all_btn = tk.Button(btn_frame, text="All", font=("Arial", 10), 
                         command=lambda: show_category(self.available_ingredients, "All Ingredients"))
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
        
        # Show all ingredients by default
        show_category(self.available_ingredients, "All Ingredients")
        
        # Add ingredient button
        add_btn = tk.Button(left_frame, text="Add Ingredient →", font=("Arial", 12), 
                         command=lambda: self.add_to_mix(ing_listbox, mix_listbox, current_category["items"]))
        add_btn.pack(pady=10)
        
        # Right section: Mixing glass and results
        right_frame = tk.Frame(main_frame, bg="black", width=375)
        right_frame.pack(side=tk.RIGHT, padx=10, fill=tk.BOTH, expand=True)
        
        # Mixing glass frame with scrollbar
        mix_frame = tk.LabelFrame(right_frame, text="Mixing Glass", font=("Arial", 12), bg="black", fg="white")
        mix_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar for mixing glass
        mix_scrollbar = tk.Scrollbar(mix_frame)
        mix_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox for mixing glass ingredients
        mix_listbox = tk.Listbox(mix_frame, bg="black", fg="white", font=("Arial", 12),
                              width=20, height=12, yscrollcommand=mix_scrollbar.set)
        mix_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mix_scrollbar.config(command=mix_listbox.yview)
        
        # Button to remove ingredient
        remove_btn = tk.Button(right_frame, text="← Remove Ingredient", font=("Arial", 12), 
                            command=lambda: self.remove_from_mix(mix_listbox))
        remove_btn.pack(pady=5)
        
        # Clear glass button
        clear_btn = tk.Button(right_frame, text="Clear Glass", font=("Arial", 12), 
                           command=lambda: mix_listbox.delete(0, tk.END))
        clear_btn.pack(pady=5)
        
        # Result frame
        result_frame = tk.LabelFrame(content_frame, text="Mixing Result", font=("Arial", 12), bg="black", fg="white")
        result_frame.pack(padx=20, pady=10, fill=tk.X)
        
        # Result label
        result_label = tk.Label(result_frame, text="Mix ingredients to create a drink", 
                            font=("Arial", 12), bg="black", fg="white", wraplength=700)
        result_label.pack(pady=10, fill=tk.X)
        
        # Bottom buttons frame
        bottom_frame = tk.Frame(content_frame, bg="black")
        bottom_frame.pack(pady=10)
        
        # Mix button
        mix_btn = tk.Button(bottom_frame, text="Mix Drink", font=("Arial", 14), bg="dark blue", fg="white",
                         command=lambda: self.mix_drink(mix_listbox, result_label))
        mix_btn.pack(side=tk.LEFT, padx=20)
        
        # Recipe reference button
        recipe_btn = tk.Button(bottom_frame, text="Recipe Book", font=("Arial", 14),
                            command=self.show_recipes)
        recipe_btn.pack(side=tk.LEFT, padx=20)
        
        # Close button
        close_btn = tk.Button(bottom_frame, text="Close", font=("Arial", 14), 
                           command=mixer_popup.destroy)
        close_btn.pack(side=tk.LEFT, padx=20)

        # Function to handle mousewheel scrolling
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind mousewheel to the mixer popup window
        mixer_popup.bind("<MouseWheel>", _on_mousewheel)
        
        # Override the destroy method to unbind the mousewheel event
        orig_destroy = mixer_popup.destroy
        def _destroy_and_cleanup():
            mixer_popup.unbind("<MouseWheel>")
            orig_destroy()
        
        mixer_popup.destroy = _destroy_and_cleanup
        
        # Configure the window close action to call our custom destroy method
        mixer_popup.protocol("WM_DELETE_WINDOW", mixer_popup.destroy)
    
    def add_to_mix(self, ing_listbox, mix_listbox, available_items):
        """Add an ingredient to the mixing glass"""
        selection = ing_listbox.curselection()
        if not selection or selection[0] == 0:  # Skip header
            return
        
        index = selection[0]
        entry = ing_listbox.get(index)
        
        # Skip if it's a category header
        if entry.startswith("---"):
            return
            
        # Add to mixing glass
        mix_listbox.insert(tk.END, entry)
    
    def mix_drink(self, mix_listbox, result_label):
        """Mix ingredients and determine the result"""
        # Get all ingredients from the mixing glass
        ingredients = [mix_listbox.get(i) for i in range(mix_listbox.size())]
        
        if not ingredients:
            result_label.config(text="You need to add ingredients first!")
            return
        
        # Sort ingredients for consistent matching
        ingredients.sort()
        
        # Check if the mix matches any known recipes
        drink_match = None
        for drink_name, drink_data in self.mixed_drinks.items():
            recipe_ingredients = sorted(drink_data["ingredients"])
            if ingredients == recipe_ingredients:
                drink_match = drink_name
                break
        
        if drink_match:
            # Successfully mixed a known drink
            drink_data = self.mixed_drinks[drink_match]
            result_text = f"Success! You've mixed a {drink_match}.\n{drink_data['desc']}"
            result_label.config(text=result_text, fg="light green")
            
            # Add note about the successful mix
            if "notes" not in self.player_data:
                self.player_data["notes"] = []
            
            self.player_data["notes"].append({
                "timestamp": datetime.datetime.now().isoformat(),
                "text": f"Successfully mixed a {drink_match} at the bar."
            })
        else:
            # Define spirits for feedback
            spirits = ["Vodka", "Gin", "Rum", "Whiskey", "Tequila", "Brandy", "Scotch"]
            
            # Analyze the mix to give feedback
            if len(ingredients) > 5:
                feedback = "This has too many ingredients - most cocktails use 2-5 ingredients."
            elif not any(item in spirits for item in ingredients):
                feedback = "Most mixed drinks need a spirit as the base (like Vodka, Rum, or Whiskey)."
            elif all(item in spirits for item in ingredients):
                feedback = "This is just a mix of different spirits. Try adding some mixers or modifiers."
            else:
                feedback = "This combination doesn't match any known recipe. Try a different mix."
                
            # Unknown mixture
            result_text = f"You've created an unknown concoction. {feedback}"
            result_label.config(text=result_text, fg="red")
    
    def show_recipes(self):
        """Show a list of known drink recipes"""
        recipes_popup = tk.Toplevel(self.bar_window)
        recipes_popup.title("Drink Recipes")
        recipes_popup.geometry("700x600")  # Made larger for more recipes
        recipes_popup.configure(bg="black")
        recipes_popup.transient(self.bar_window)
        recipes_popup.grab_set()
        
        # Center the popup
        recipes_popup.update_idletasks()
        width = 700
        height = 600
        x = (recipes_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (recipes_popup.winfo_screenheight() // 2) - (height // 2)
        recipes_popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        title_label = tk.Label(recipes_popup, text="Bartender's Recipe Book", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)
        
        # Recipe navigation frame
        nav_frame = tk.Frame(recipes_popup, bg="black")
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Recipe category buttons
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
        
        # Recipe categories
        basic_recipes = ["Screwdriver", "Gin and Tonic", "Rum and Cola", "Whiskey Sour", "Daiquiri"]
        special_recipes = ["Space Blaster", "Quantum Fizz", "Nebula Cloud"]
        
        # Create scrollable frame for recipes
        frame = tk.Frame(recipes_popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text widget for recipes
        recipe_text = tk.Text(frame, bg="black", fg="white", font=("Arial", 12),
                           width=60, height=25, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        recipe_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=recipe_text.yview)
        
        # Mouse wheel binding for scrolling
        def _on_recipe_mousewheel(event):
            try:
                recipe_text.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Ignore errors if the text widget was destroyed
        
        # Bind mousewheel to recipe text
        recipes_popup.bind("<MouseWheel>", _on_recipe_mousewheel)
        
        # Override destroy method to cleanup bindings
        orig_destroy = recipes_popup.destroy
        def _destroy_and_cleanup():
            try:
                recipes_popup.unbind("<MouseWheel>")
            except:
                pass
            orig_destroy()
        
        recipes_popup.destroy = _destroy_and_cleanup
        
        # Format and display recipes by category
        def show_recipe_category(category):
            # Clear the text widget
            recipe_text.config(state=tk.NORMAL)
            recipe_text.delete(1.0, tk.END)
            
            # Add a header
            recipe_text.insert(tk.END, "BARTENDER'S RECIPE BOOK\n", "header")
            recipe_text.insert(tk.END, "------------------------\n\n", "header")
            
            # Create a sorted list of drink names
            sorted_drinks = sorted(self.mixed_drinks.keys())
            
            # Filter by category if needed
            if category == "basic":
                sorted_drinks = [drink for drink in sorted_drinks if drink in basic_recipes]
                recipe_text.insert(tk.END, "BASIC COCKTAILS\n\n", "category")
            elif category == "special":
                sorted_drinks = [drink for drink in sorted_drinks if drink in special_recipes]
                recipe_text.insert(tk.END, "STATION SPECIALTIES\n\n", "category")
            elif category == "advanced":
                sorted_drinks = [drink for drink in sorted_drinks if drink not in basic_recipes and drink not in special_recipes]
                recipe_text.insert(tk.END, "ADVANCED COCKTAILS\n\n", "category")
            else:
                # Add all categories with headers
                recipe_text.insert(tk.END, "BASIC COCKTAILS\n\n", "category")
                for drink in sorted(basic_recipes):
                    add_recipe(drink)
                
                recipe_text.insert(tk.END, "\nADVANCED COCKTAILS\n\n", "category")
                for drink in sorted([d for d in sorted_drinks if d not in basic_recipes and d not in special_recipes]):
                    add_recipe(drink)
                
                recipe_text.insert(tk.END, "\nSTATION SPECIALTIES\n\n", "category")
                for drink in sorted(special_recipes):
                    add_recipe(drink)
                
                # Make text widget read-only
                recipe_text.config(state=tk.DISABLED)
                return
            
            # Add recipes for the selected category
            for drink in sorted_drinks:
                add_recipe(drink)
            
            # Make text widget read-only
            recipe_text.config(state=tk.DISABLED)
        
        # Helper function to add a recipe
        def add_recipe(drink_name):
            if drink_name in self.mixed_drinks:
                drink_data = self.mixed_drinks[drink_name]
                
                # Add drink name
                recipe_text.insert(tk.END, f"{drink_name}:\n", "drink_name")
                
                # Add ingredients
                recipe_text.insert(tk.END, f"  Ingredients: ", "label")
                recipe_text.insert(tk.END, f"{', '.join(drink_data['ingredients'])}\n", "ingredients")
                
                # Add price
                recipe_text.insert(tk.END, f"  Price: ", "label")
                recipe_text.insert(tk.END, f"{drink_data['price']} credits\n", "value")
                
                # Add description
                recipe_text.insert(tk.END, f"  Description: ", "label")
                recipe_text.insert(tk.END, f"{drink_data['desc']}\n\n", "value")
        
        # Configure text tags for formatting
        recipe_text.tag_configure("header", font=("Arial", 14, "bold"))
        recipe_text.tag_configure("category", font=("Arial", 13, "bold"), foreground="yellow")
        recipe_text.tag_configure("drink_name", font=("Arial", 12, "bold"), foreground="light blue")
        recipe_text.tag_configure("label", font=("Arial", 11, "bold"))
        recipe_text.tag_configure("ingredients", font=("Arial", 11), foreground="light green")
        recipe_text.tag_configure("value", font=("Arial", 11))
        
        # Show all recipes by default
        show_recipe_category("all")
        
        # Search frame
        search_frame = tk.Frame(recipes_popup, bg="black")
        search_frame.pack(fill=tk.X, padx=20, pady=5)
        
        search_label = tk.Label(search_frame, text="Search: ", font=("Arial", 11), bg="black", fg="white")
        search_label.pack(side=tk.LEFT, padx=5)
        
        search_entry = tk.Entry(search_frame, bg="dark gray", fg="white", font=("Arial", 11), width=20)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Function to search recipes
        def search_recipes(event=None):
            query = search_entry.get().lower().strip()
            if not query:
                show_recipe_category("all")
                return
                
            # Clear the text widget
            recipe_text.config(state=tk.NORMAL)
            recipe_text.delete(1.0, tk.END)
            
            # Add a header
            recipe_text.insert(tk.END, f"SEARCH RESULTS FOR '{query}'\n", "header")
            recipe_text.insert(tk.END, "------------------------\n\n", "header")
            
            # Search through drinks and ingredients
            results_found = False
            for drink_name, drink_data in self.mixed_drinks.items():
                # Check if query matches drink name or ingredients
                if (query in drink_name.lower() or 
                    any(query in ingredient.lower() for ingredient in drink_data["ingredients"]) or
                    query in drink_data["desc"].lower()):
                    add_recipe(drink_name)
                    results_found = True
            
            if not results_found:
                recipe_text.insert(tk.END, "No recipes found matching your search.")
                
            # Make text widget read-only
            recipe_text.config(state=tk.DISABLED)
        
        # Bind search function to entry
        search_entry.bind("<Return>", search_recipes)
        
        search_btn = tk.Button(search_frame, text="Search", font=("Arial", 10), command=search_recipes)
        search_btn.pack(side=tk.LEFT, padx=5)
        
        # Ingredient list button
        ing_btn = tk.Button(search_frame, text="Ingredients List", font=("Arial", 10),
                         command=self.show_ingredients_list)
        ing_btn.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(recipes_popup, text="Close", font=("Arial", 12), command=recipes_popup.destroy)
        close_btn.pack(pady=10)
    
    def show_ingredients_list(self):
        """Show a list of all available ingredients"""
        ing_popup = tk.Toplevel(self.bar_window)
        ing_popup.title("Available Ingredients")
        ing_popup.geometry("400x500")
        ing_popup.configure(bg="black")
        ing_popup.transient(self.bar_window)
        ing_popup.grab_set()
        
        # Center the popup
        ing_popup.update_idletasks()
        width = 400
        height = 500
        x = (ing_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (ing_popup.winfo_screenheight() // 2) - (height // 2)
        ing_popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        title_label = tk.Label(ing_popup, text="Available Ingredients", font=("Arial", 18), bg="black", fg="white")
        title_label.pack(pady=10)
        
        # Group ingredients by category
        spirits = []
        mixers = []
        modifiers = []
        specials = []
        
        # Organize ingredients into categories
        for ingredient in sorted(self.available_ingredients):
            if ingredient in ["Vodka", "Gin", "Rum", "Whiskey", "Tequila", "Brandy", "Scotch"]:
                spirits.append(ingredient)
            elif "Juice" in ingredient or "Water" in ingredient or "Cola" in ingredient or "Ale" in ingredient or "Sprite" in ingredient:
                mixers.append(ingredient)
            elif ingredient in ["Lemon Juice", "Lime Juice", "Sugar", "Salt", "Honey", "Triple Sec", 
                              "Blue Curacao", "Orange Curacao", "Grenadine", "Bitters", "Vermouth", 
                              "Campari", "Cherry Brandy"]:
                modifiers.append(ingredient)
            else:
                specials.append(ingredient)
        
        # Create scrollable frame for ingredients
        frame = tk.Frame(ing_popup, bg="black")
        frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text widget for ingredients
        ing_text = tk.Text(frame, bg="black", fg="white", font=("Arial", 12),
                        width=40, height=20, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        ing_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=ing_text.yview)
        
        # Mouse wheel binding for scrolling
        def _on_ing_mousewheel(event):
            try:
                ing_text.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Ignore errors if the text widget was destroyed
        
        # Bind mousewheel to ingredients text
        ing_popup.bind("<MouseWheel>", _on_ing_mousewheel)
        
        # Override destroy method to cleanup bindings
        orig_destroy = ing_popup.destroy
        def _destroy_and_cleanup():
            try:
                ing_popup.unbind("<MouseWheel>")
            except:
                pass
            orig_destroy()
        
        ing_popup.destroy = _destroy_and_cleanup
        
        # Add ingredients by category
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
        
        # Configure text tags for formatting
        ing_text.tag_configure("header", font=("Arial", 14, "bold"))
        ing_text.tag_configure("ingredient", font=("Arial", 11))
        
        # Make text widget read-only
        ing_text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = tk.Button(ing_popup, text="Close", font=("Arial", 12), command=ing_popup.destroy)
        close_btn.pack(pady=10)
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, "0,-1", self.bar_window)
    
    def on_closing(self):
        """Handle window closing"""
        # Check if the door is locked
        door_key = "0,-1"  # Bar door
        if is_door_locked(self.player_data, door_key):
            self.bar_window.after(10, lambda: tk.messagebox.showinfo("Locked Door", "The door is locked. You must unlock it before leaving.", parent=self.bar_window))
            # Make sure the window stays on top after dialog
            self.bar_window.after(20, self.bar_window.lift)
            self.bar_window.focus_force()
            return
        
        # Reset bartender mode
        self.bartender_mode = False
        
        # Release grab before closing
        self.bar_window.grab_release()
        
        # Call return callback with player and crew data
        self.return_callback(self.player_data, self.station_crew)
        
        # Destroy the window
        self.bar_window.destroy()

    def show_station_menu(self):
        """Return to main station menu options"""
        # Reset bartender mode
        self.bartender_mode = False
        
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Check if user is a bartender or captain
        is_bartender = self.player_data.get("job") == "Bartender"
        is_captain = self.player_data.get("job") == "Captain"
        
        if is_bartender or is_captain:
            # Add bartender station access
            station_btn = tk.Button(self.button_frame, text="Enter Bartender Station", font=("Arial", 14), width=20, command=self.access_bartender_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for bartenders and captains
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options() 

    def remove_from_mix(self, mix_listbox):
        """Remove an ingredient from the mixing glass"""
        selection = mix_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        mix_listbox.delete(index)

class Botany:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        # Create a new toplevel window
        self.botany_window = tk.Toplevel(parent_window)
        self.botany_window.title("Botany Lab")
        self.botany_window.geometry("800x600")
        self.botany_window.configure(bg="black")
        
        # Store references
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew # Store crew data
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
        
        # Bind window closing
        self.botany_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Ensure this window stays on top
        self.botany_window.transient(parent_window)
        self.botany_window.grab_set()
        self.botany_window.focus_force()
        
        # Center window on screen after window is configured
        self.botany_window.update_idletasks()
        width = 800
        height = 600
        x = (self.botany_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.botany_window.winfo_screenheight() // 2) - (height // 2)
        self.botany_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        room_label = tk.Label(self.botany_window, text="Station Botany Lab", font=("Arial", 24), bg="black", fg="white")
        room_label.pack(pady=30)
        
        # Description
        desc_label = tk.Label(self.botany_window, 
                              text="The botany lab is filled with plants of all varieties. Hydroponic systems line the walls, and bright grow lights illuminate rows of planters. The air is humid and smells of fresh soil and vegetation.",
                              font=("Arial", 12), bg="black", fg="white", wraplength=600)
        desc_label.pack(pady=10)
        
        # Room actions
        self.button_frame = tk.Frame(self.botany_window, bg="black")
        self.button_frame.pack(pady=20)
        
        # Check if user has special access
        is_botanist = self.player_data.get("job") == "Botanist"
        is_captain = self.player_data.get("job") == "Captain"
        is_hop = self.player_data.get("job") == "Head of Personnel"
        has_botany_access = is_botanist or is_captain or is_hop or ("permissions" in self.player_data and self.player_data["permissions"].get("botany_station", False))
        
        if has_botany_access:
            # Show station access button for authorized personnel
            station_btn = tk.Button(self.button_frame, text="Enter Botany Station", font=("Arial", 14), width=20, command=self.access_botany_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()
        
        # Exit button
        exit_btn = tk.Button(self.botany_window, text="Exit Room", font=("Arial", 14), width=15, command=self.on_closing)
        exit_btn.pack(pady=20)
    
    def show_room_options(self):
        """Show regular room options that all players can access"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # View plants option
        view_plants_btn = tk.Button(self.button_frame, text="View Plants", font=("Arial", 14), width=20, command=self.view_plants)
        view_plants_btn.pack(pady=10)
        
        # Only show "Back to Station Menu" if player has access
        is_botanist = self.player_data.get("job") == "Botanist"
        is_captain = self.player_data.get("job") == "Captain"
        is_hop = self.player_data.get("job") == "Head of Personnel"
        has_botany_access = is_botanist or is_captain or is_hop or ("permissions" in self.player_data and self.player_data["permissions"].get("botany_station", False))
        
        if has_botany_access:
            # Back to station menu button
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)
    
    def view_plants(self):
        """View the plants in the botany lab"""
        # Create a new top-level window for viewing plants
        plants_window = tk.Toplevel(self.botany_window)
        plants_window.title("Viewing Plants")
        plants_window.geometry("600x500")
        plants_window.configure(bg="black")
        plants_window.transient(self.botany_window)
        plants_window.grab_set()
        
        # Center the window
        plants_window.update_idletasks()
        width = 600
        height = 500
        x = (plants_window.winfo_screenwidth() // 2) - (width // 2)
        y = (plants_window.winfo_screenheight() // 2) - (height // 2)
        plants_window.geometry(f"{width}x{height}+{x}+{y}")
        
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
        seed_window = tk.Toplevel(self.botany_window)
        seed_window.title("Seed Machine")
        seed_window.geometry("700x600")
        seed_window.configure(bg="black")
        seed_window.transient(self.botany_window)
        seed_window.grab_set()
        
        # Center the window
        seed_window.update_idletasks()
        width = 700
        height = 600
        x = (seed_window.winfo_screenwidth() // 2) - (width // 2)
        y = (seed_window.winfo_screenheight() // 2) - (height // 2)
        seed_window.geometry(f"{width}x{height}+{x}+{y}")
        
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
        if "notes" not in self.player_data:
            self.player_data["notes"] = []
        
        self.player_data["notes"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "text": f"Acquired {seed['name']} from the botany seed dispenser."
        })
        
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
        plant_window = tk.Toplevel(self.botany_window)
        plant_window.title("Plant Seeds")
        plant_window.geometry("800x600")
        plant_window.configure(bg="black")
        plant_window.transient(self.botany_window)
        plant_window.grab_set()
        
        # Center the window
        plant_window.update_idletasks()
        width = 800
        height = 600
        x = (plant_window.winfo_screenwidth() // 2) - (width // 2)
        y = (plant_window.winfo_screenheight() // 2) - (height // 2)
        plant_window.geometry(f"{width}x{height}+{x}+{y}")
        
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
            if "notes" not in self.player_data:
                self.player_data["notes"] = []
            
            self.player_data["notes"].append({
                "timestamp": datetime.datetime.now().isoformat(),
                "text": f"Planted {seed['name']} in planter {planter_index+1}."
            })
            
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
        toggle_room_door_lock(self.player_data, "3,-1", self.botany_window)
    
    def on_closing(self):
        """Handle window closing"""
        # Check if the door is locked
        door_key = "3,-1"  # Botany Lab door
        if is_door_locked(self.player_data, door_key):
            self.botany_window.after(10, lambda: messagebox.showinfo("Locked Door", "The door is locked. You must unlock it before leaving.", parent=self.botany_window))
            # Make sure the window stays on top after dialog
            self.botany_window.after(20, self.botany_window.lift)
            self.botany_window.focus_force()
            return
        
        # Release grab before closing
        self.botany_window.grab_release()
        
        # Call return callback with player and crew data
        self.return_callback(self.player_data, self.station_crew)
        
        # Destroy the window
        self.botany_window.destroy()
    
    def show_station_menu(self):
        """Return to main station menu options"""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Check if user has special access
        is_botanist = self.player_data.get("job") == "Botanist"
        is_captain = self.player_data.get("job") == "Captain"
        is_hop = self.player_data.get("job") == "Head of Personnel"
        has_botany_access = is_botanist or is_captain or is_hop or ("permissions" in self.player_data and self.player_data["permissions"].get("botany_station", False))
        
        if has_botany_access:
            # Show station access button for authorized personnel
            station_btn = tk.Button(self.button_frame, text="Enter Botany Station", font=("Arial", 14), width=20, command=self.access_botany_station)
            station_btn.pack(pady=10)
            
            # Add door lock/unlock button for authorized personnel
            door_btn = tk.Button(self.button_frame, text="Lock/Unlock Door", font=("Arial", 14), width=20, command=self.toggle_door_lock)
            door_btn.pack(pady=10)
            
            # Add "Room Options" button to show regular options
            options_btn = tk.Button(self.button_frame, text="Room Options", font=("Arial", 14), width=20, command=self.show_room_options)
            options_btn.pack(pady=10)
        else:
            # Show regular options for unauthorized personnel
            self.show_room_options()