import tkinter as tk
from tkinter import messagebox
import math

from game.helper_methods.door_control import can_control_door, toggle_door_lock as toggle_room_door_lock
from game.helper_methods.oxygen_helper import DOCTOR_REQUIRED_FLOOR
from game.helper_methods.alcohol_helper import DOCTOR_SOBER_FLOOR, sober_up_cost
from game.special_rooms.shared import (
    add_note,
    build_npc_contact_section,
    build_room_shell,
    open_room_in_main_window,
    try_leave_through_door,
    show_station_menu as render_station_menu,
)
from game.helper_methods.ui_panels import open_modal_panel
from game.maps.donut import MEDBAY_KEY as DOOR_KEY

# Cost multipliers: 1 credit per damage point, with type-based scaling
COST_MULTIPLIERS = {
    "blunt": 1,
    "poison": 2,
    "oxygen": 2,
    "burn": 3,
}

NON_LIMB_DAMAGE_TYPES = ("burn", "poison", "oxygen")


def _limb_status(health):
    if health > 75:
        return "Healthy"
    if health > 40:
        return "Injured"
    return "Critical"


def _non_limb_status(damage_val):
    if damage_val < 10:
        return "Clear"
    if damage_val < 30:
        return "Mild"
    if damage_val < 60:
        return "Moderate"
    return "Severe"


def assess_injuries(player_data):
    """Return limb/non-limb damage breakdown and treatment costs."""
    limbs = player_data.get("limbs", {}) or {}
    damage = player_data.get("damage", {}) or {}

    limb_details = []
    blunt_points = 0
    injured_limbs = []
    critical_limbs = []

    for limb, health in limbs.items():
        limb_name = limb.replace("_", " ").title()
        points = max(0, 100 - health)
        blunt_points += points
        status = _limb_status(health)
        limb_details.append({
            "key": limb,
            "name": limb_name,
            "health": health,
            "points": points,
            "status": status,
        })
        if status == "Injured":
            injured_limbs.append(limb_name)
        elif status == "Critical":
            critical_limbs.append(limb_name)

    non_limb = {}
    for dtype in NON_LIMB_DAMAGE_TYPES:
        value = damage.get(dtype, 0) or 0
        non_limb[dtype] = {
            "value": value,
            "status": _non_limb_status(value),
            "multiplier": COST_MULTIPLIERS[dtype],
            "cost": math.ceil(value * COST_MULTIPLIERS[dtype]) if value > 0 else 0,
        }

    blunt_cost = math.ceil(blunt_points * COST_MULTIPLIERS["blunt"]) if blunt_points > 0 else 0
    burn_cost = non_limb["burn"]["cost"]
    poison_cost = non_limb["poison"]["cost"]
    oxygen_cost = non_limb["oxygen"]["cost"]
    total_cost = blunt_cost + burn_cost + poison_cost + oxygen_cost

    overall_limb_health = 0.0
    if limbs:
        overall_limb_health = (sum(limbs.values()) / (len(limbs) * 100)) * 100

    active_damage_types = [
        dtype.title() for dtype in NON_LIMB_DAMAGE_TYPES if non_limb[dtype]["value"] > 0
    ]

    return {
        "limbs": limbs,
        "limb_details": limb_details,
        "injured_limbs": injured_limbs,
        "critical_limbs": critical_limbs,
        "overall_limb_health": overall_limb_health,
        "blunt_points": blunt_points,
        "blunt_cost": blunt_cost,
        "non_limb": non_limb,
        "active_damage_types": active_damage_types,
        "burn_cost": burn_cost,
        "poison_cost": poison_cost,
        "oxygen_cost": oxygen_cost,
        "total_cost": total_cost,
    }


def format_cost_breakdown(assessment):
    """Itemized treatment cost lines for popups."""
    lines = []
    if assessment["blunt_points"] > 0:
        lines.append(
            f"- Blunt: {assessment['blunt_points']:.0f} pts × {COST_MULTIPLIERS['blunt']} "
            f"= {assessment['blunt_cost']} credits"
        )
    for dtype in NON_LIMB_DAMAGE_TYPES:
        info = assessment["non_limb"][dtype]
        if info["value"] > 0:
            lines.append(
                f"- {dtype.title()}: {info['value']:.0f} pts × {info['multiplier']} "
                f"= {info['cost']} credits"
            )
    return lines


def format_damage_sections(assessment):
    """Limb and other-damage sections shared by health check and doctor dialogs."""
    sections = []

    if assessment["limb_details"]:
        limb_lines = ["Limb Status:"]
        for limb in assessment["limb_details"]:
            limb_lines.append(
                f"- {limb['name']}: {limb['health']}% ({limb['status']})"
            )
        sections.append("\n".join(limb_lines))
    else:
        sections.append("Limb Status:\nNo limb health data available.")

    damage_lines = ["Other Damage:"]
    for dtype in NON_LIMB_DAMAGE_TYPES:
        info = assessment["non_limb"][dtype]
        damage_lines.append(
            f"- {dtype.title()}: {info['value']:.1f}% ({info['status']})"
        )
    sections.append("\n".join(damage_lines))

    return "\n\n".join(sections)


class MedBay:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self.medbay_window = open_room_in_main_window(
            parent_window, "MedBay", player_data, station_crew, return_callback
        )
        _, self.button_frame = build_room_shell(
            self.medbay_window,
            self.player_data,
            "Station Medical Bay",
            "The medical bay is clean and orderly. Various medical equipment lines the walls, and a few examination beds are visible. The station's medical staff handle everything from routine checkups to emergency trauma care.",
        )

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
        
        # Talk to doctor option (or "Call" them if they've stepped away)
        build_npc_contact_section(
            self.button_frame,
            self.player_data,
            self.station_crew,
            "Doctor",
            self.medbay_window,
            talk_label="Talk to Doctor",
            talk_command=self.talk_to_doctor,
            refresh_callback=self.show_room_options,
            absent_flavor="The doctor is currently away from MedBay.",
        )

        if can_control_door(self.player_data, DOOR_KEY):
            back_btn = tk.Button(self.button_frame, text="Back to Station Menu", font=("Arial", 14), width=20, 
                               command=self.show_station_menu)
            back_btn.pack(pady=10)
    
    def health_check(self):
        assessment = assess_injuries(self.player_data)
        overall_health = assessment["overall_limb_health"]
        has_non_limb = bool(assessment["active_damage_types"])
        alcohol = self.player_data.get("alcohol_percent", 0) or 0
        sober_cost = sober_up_cost(alcohol)

        health_report = "Health Check Results:\n\n"
        if assessment["limbs"]:
            health_report += f"Overall Limb Health: {overall_health:.1f}%\n\n"
        health_report += format_damage_sections(assessment)

        if alcohol > 0:
            health_report += f"\n\nBlood Alcohol: {alcohol:.1f}%"
            if alcohol >= DOCTOR_SOBER_FLOOR:
                health_report += (
                    f"\n• Intoxication is at or above {DOCTOR_SOBER_FLOOR}%. "
                    f"Doctor treatment is required to sober up "
                    f"({sober_cost} credits)."
                )
            else:
                health_report += (
                    "\n• Alcohol will metabolize over time "
                    "(about 5% every 2 minutes)."
                )

        needs_attention = overall_health < 60 or has_non_limb or alcohol >= DOCTOR_SOBER_FLOOR
        health_report += "\n\nRecommendation: "
        if needs_attention:
            health_report += "Medical attention recommended."
        else:
            health_report += "No immediate medical attention required."

        if overall_health < 100 or has_non_limb:
            health_report += "\n\nDetailed Notes:"

            if assessment["critical_limbs"]:
                health_report += f"\n• Critical damage detected in {', '.join(assessment['critical_limbs'])}. "
                health_report += "Immediate treatment required."

            if assessment["injured_limbs"]:
                health_report += f"\n• Moderate trauma detected in {', '.join(assessment['injured_limbs'])}. "
                health_report += "Rest and treatment advised."

            if has_non_limb:
                health_report += (
                    f"\n• Non-limb damage detected: {', '.join(assessment['active_damage_types'])}."
                )

            oxygen_damage = assessment["non_limb"]["oxygen"]["value"]
            if oxygen_damage > 0:
                if oxygen_damage >= DOCTOR_REQUIRED_FLOOR:
                    health_report += (
                        f"\n• Oxygen damage is at {oxygen_damage:.0f}% "
                        f"(at or above {DOCTOR_REQUIRED_FLOOR}%). "
                        "You must be healed by the doctor to fully recover."
                    )
                else:
                    health_report += (
                        f"\n• Oxygen damage is at {oxygen_damage:.0f}% "
                        f"(below {DOCTOR_REQUIRED_FLOOR}%). "
                        "You can rest to restore yourself while life support is functional."
                    )

            if overall_health < 75:
                health_report += "\n• Movement and performance significantly impaired."
            elif overall_health < 90 and assessment["limbs"]:
                health_report += "\n• Some physical activities may be difficult."

        injury_cost = assessment["total_cost"]
        combined_cost = injury_cost + sober_cost
        if combined_cost > 0:
            health_report += "\n\nEstimated Treatment Cost:"
            for line in format_cost_breakdown(assessment):
                health_report += f"\n{line}"
            if sober_cost > 0:
                health_report += f"\n- Sober up: {sober_cost} credits"
            health_report += f"\nTotal: {combined_cost} credits"
            health_report += "\n(Talk to Doctor to receive treatment)"
        else:
            health_report += "\n\nNo treatment needed."

        self.medbay_window.after(
            10,
            lambda: messagebox.showinfo("Medical Scan", health_report, parent=self.medbay_window),
        )
        self.medbay_window.after(20, self.medbay_window.lift)
        self.medbay_window.focus_force()

    def talk_to_doctor(self):
        """Talk to a doctor who can provide healing for a fee based on damage"""
        assessment = assess_injuries(self.player_data)
        injury_cost = assessment["total_cost"]
        alcohol = self.player_data.get("alcohol_percent", 0) or 0
        sober_cost = sober_up_cost(alcohol)
        total_cost = injury_cost + sober_cost

        if total_cost == 0:
            message = "The doctor examines you. 'You're in perfect health! No treatment needed.'"
            self.medbay_window.after(
                10,
                lambda: messagebox.showinfo("Doctor", message, parent=self.medbay_window),
            )
            return

        message = "The doctor examines you.\n\n"
        message += format_damage_sections(assessment)
        if alcohol > 0:
            message += f"\n\nBlood Alcohol: {alcohol:.1f}%"
        message += "\n\nTreatment Cost:"
        for line in format_cost_breakdown(assessment):
            message += f"\n{line}"
        if sober_cost > 0:
            message += f"\n- Sober up: {sober_cost} credits"
        message += f"\nTotal: {total_cost} credits"
        message += "\n\nWould you like to proceed with treatment?"

        _panel, dialog = open_modal_panel(self.medbay_window, title="Doctor")
        msg_label = tk.Label(
            dialog, text=message, font=("Arial", 12), bg="black", fg="white",
            wraplength=420, justify=tk.LEFT,
        )
        msg_label.pack(pady=20, padx=10)

        btn_frame = tk.Frame(dialog, bg="black")
        btn_frame.pack(pady=10)

        yes_btn = tk.Button(
            btn_frame,
            text=f"Yes ({total_cost} credits)",
            font=("Arial", 12),
            command=lambda: self.pay_for_healing(dialog, total_cost, sober_cost),
        )
        yes_btn.pack(side=tk.LEFT, padx=10)

        no_btn = tk.Button(btn_frame, text="No", font=("Arial", 12), command=dialog.destroy)
        no_btn.pack(side=tk.LEFT, padx=10)

    def pay_for_healing(self, dialog, total_cost, sober_cost=0):
        """Pay credits for healing based on the calculated cost"""
        if self.player_data["credits"] < total_cost:
            message = "You don't have enough credits for treatment. Come back when you can afford it."
            dialog.destroy()
            self.medbay_window.after(
                10,
                lambda: messagebox.showinfo("Doctor", message, parent=self.medbay_window),
            )
            return

        self.player_data["credits"] -= total_cost

        original_health = self.player_data["limbs"].copy()
        original_damage = self.player_data["damage"].copy()
        original_alcohol = self.player_data.get("alcohol_percent", 0) or 0

        for limb in self.player_data["limbs"]:
            self.player_data["limbs"][limb] = 100

        for damage_type in self.player_data["damage"]:
            self.player_data["damage"][damage_type] = 0

        sobered = False
        if sober_cost > 0:
            self.player_data["alcohol_percent"] = 0
            timers = self.player_data.setdefault("damage_timers", {})
            timers["alcohol_decay_acc"] = 0.0
            sobered = True

        dialog.destroy()

        injured_limbs = [
            limb.replace("_", " ").title()
            for limb, health in original_health.items()
            if health < 100
        ]
        injured_damage = [
            dtype.title() for dtype, value in original_damage.items() if value > 0
        ]
        has_injuries = bool(injured_limbs) or bool(injured_damage)

        message = f"You pay {total_cost} credits. The doctor treats you.\n\n"
        if has_injuries:
            message += "Healed:\n"
            if injured_limbs:
                message += f"- Blunt damage: {', '.join(injured_limbs)}\n"
            if injured_damage:
                message += f"- Other damage: {', '.join(injured_damage)}\n"
        if sobered:
            message += f"- Intoxication cleared (was {original_alcohol:.1f}%).\n"
        if has_injuries or sobered:
            message += "\nYou feel much better now."
        else:
            message += "No injuries were found."

        self.medbay_window.after(
            10,
            lambda: messagebox.showinfo("Treatment Complete", message, parent=self.medbay_window),
        )

        if "notes" in self.player_data:
            if has_injuries or sobered:
                healed_parts = []
                if injured_limbs:
                    healed_parts.append(
                        f"Blunt Damage ({', '.join(injured_limbs)}) fully healed."
                    )
                if injured_damage:
                    healed_parts.append(
                        f"Other Damage ({', '.join(injured_damage)}) fully healed."
                    )
                if sobered:
                    healed_parts.append(
                        f"Sobered up from {original_alcohol:.1f}% alcohol."
                    )
                note_text = (
                    f"Paid {total_cost} credits for medical treatment. "
                    f"{'. '.join(healed_parts)}"
                )
            else:
                note_text = (
                    f"Paid {total_cost} credits for medical examination. "
                    "No injuries were found."
                )

            add_note(self.player_data, note_text)

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
        _panel, vitals_window = open_modal_panel(self.medbay_window, title="Crew Vitals Monitor")
        vitals_window.configure(bg="black")


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

