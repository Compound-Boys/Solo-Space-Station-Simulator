import tkinter as tk
from tkinter import messagebox
import datetime
import math

from game.helper_methods.door_control import can_control_door, toggle_door_lock as toggle_room_door_lock
from game.special_rooms.shared import add_note, open_room_in_main_window, try_leave_through_door, show_station_menu as render_station_menu

DOOR_KEY = "0,6"

class MedBay:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self.medbay_window = open_room_in_main_window(parent_window, "MedBay", self.on_closing)
        
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

        self._build_station_menu()
        
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
        
        if can_control_door(self.player_data, DOOR_KEY):
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
            
            add_note(self.player_data, note_text)
        
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
            if had_injuries:
                note_text = f"Received advanced medical treatment at MedBay Station. Healed: {', '.join(injury_details)}"
                add_note(self.player_data, note_text)
                
        else:
            self.medbay_window.after(10, lambda: messagebox.showinfo("Medical Treatment", "No injuries to treat.", parent=self.medbay_window))
        
        # Make sure the window stays on top after dialog
        self.medbay_window.after(20, self.medbay_window.lift)
        self.medbay_window.focus_force()
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, DOOR_KEY, self.medbay_window)
    
    def on_closing(self):
        try_leave_through_door(
            self.medbay_window,
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
                "label": "Enter MedBay Station",
                "command": self.access_medbay_station,
            }],
            show_room_options=self.show_room_options,
            toggle_door_lock=self.toggle_door_lock,
            before_show=before_show,
        )

    def show_station_menu(self):
        """Return to main station menu options"""
        self._build_station_menu()

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

