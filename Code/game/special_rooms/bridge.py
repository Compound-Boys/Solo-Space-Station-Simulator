import tkinter as tk
from tkinter import messagebox

from game.character_methods.character_creation import JOBS, permissions_for_job
from game.helper_methods.door_control import can_control_door, toggle_door_lock as toggle_room_door_lock
from game.helper_methods.ui_panels import open_modal_panel
from game.special_rooms.shared import (
    open_room_in_main_window,
    show_crew_manifest as render_crew_manifest,
    try_leave_through_door,
    show_station_menu as render_station_menu,
)
from game.maps.donut import BRIDGE_KEY as DOOR_KEY

class Bridge:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self.bridge_window = open_room_in_main_window(parent_window, "Bridge", self.on_closing)
        
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

        self._build_station_menu()
        
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
        
        if can_control_door(self.player_data, DOOR_KEY):
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
        """Access the Captain's Station interface"""      
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
        """Access the Head of Personnel (HoP) Station interface"""
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
                                  command=self.show_job_assignments)
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
        render_crew_manifest(self.bridge_window, self.player_data, self.station_crew)

    def show_job_assignments(self):
        """Open the HoP Job Assignment screen to assign jobs to station NPCs."""
        panel, popup = open_modal_panel(self.bridge_window, title="Job Assignment")
        popup.configure(bg="black")

        title_label = tk.Label(
            popup, text="Job Assignment", font=("Arial", 18, "bold"), bg="black", fg="white"
        )
        title_label.pack(pady=10)

        main_frame = tk.Frame(popup, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left: NPC list
        npc_outer = tk.LabelFrame(
            main_frame, text="Station NPCs", font=("Arial", 12), bg="black", fg="white"
        )
        npc_outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        npc_scrollbar = tk.Scrollbar(npc_outer, orient=tk.VERTICAL)
        npc_listbox = tk.Listbox(
            npc_outer,
            bg="black",
            fg="white",
            font=("Arial", 12),
            width=28,
            height=12,
            exportselection=False,
            yscrollcommand=npc_scrollbar.set,
        )
        npc_scrollbar.config(command=npc_listbox.yview)
        npc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        npc_listbox.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.BOTH, expand=True)

        # Right: Job list
        job_outer = tk.LabelFrame(
            main_frame, text="Assignable Jobs", font=("Arial", 12), bg="black", fg="white"
        )
        job_outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        job_scrollbar = tk.Scrollbar(job_outer, orient=tk.VERTICAL)
        job_listbox = tk.Listbox(
            job_outer,
            bg="black",
            fg="white",
            font=("Arial", 12),
            width=28,
            height=12,
            exportselection=False,
            yscrollcommand=job_scrollbar.set,
        )
        job_scrollbar.config(command=job_listbox.yview)
        job_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        job_listbox.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.BOTH, expand=True)

        player_is_captain = (
            self.player_data.get("job") == "Captain"
            or self.player_data.get("subdepartment") == "Captain"
        )
        for job_name in JOBS:
            if job_name == "Captain" and not player_is_captain:
                continue
            job_listbox.insert(tk.END, job_name)

        # Listbox rows: -1 = player (Captain only); else station_crew index.
        # Captain NPCs are hidden for non-Captains.
        PLAYER_INDEX = -1
        assignable_indices = []

        def _member_for_index(crew_index):
            if crew_index == PLAYER_INDEX:
                return self.player_data
            return self.station_crew[crew_index]

        def _station_has_other_captain(exclude_player=False, exclude_crew_index=None):
            if not exclude_player and self.player_data.get("job") == "Captain":
                return True
            for i, npc in enumerate(self.station_crew):
                if exclude_crew_index is not None and i == exclude_crew_index:
                    continue
                if npc.get("job") == "Captain":
                    return True
            return False

        def refresh_npc_list(preserve_crew_index=None):
            npc_listbox.delete(0, tk.END)
            assignable_indices.clear()

            if player_is_captain:
                assignable_indices.append(PLAYER_INDEX)
                player_name = self.player_data.get("name", "Unknown")
                player_job = self.player_data.get("job", "Unknown")
                npc_listbox.insert(tk.END, f"{player_name} ({player_job}) (YOU)")

            for crew_index, npc in enumerate(self.station_crew):
                if not player_is_captain and npc.get("job") == "Captain":
                    continue
                assignable_indices.append(crew_index)
                name = npc.get("name", "Unknown")
                job = npc.get("job", "Unknown")
                npc_listbox.insert(tk.END, f"{name} ({job})")

            if preserve_crew_index is not None and preserve_crew_index in assignable_indices:
                list_index = assignable_indices.index(preserve_crew_index)
                npc_listbox.selection_set(list_index)
                npc_listbox.see(list_index)

        refresh_npc_list()

        selection = {"list_index": None, "job": None}

        result_frame = tk.LabelFrame(
            popup, text="Result", font=("Arial", 12), bg="black", fg="white"
        )
        result_frame.pack(fill=tk.X, padx=20, pady=10)

        result_label = tk.Label(
            result_frame,
            text="Select an NPC and a job to confirm.",
            font=("Arial", 12),
            bg="black",
            fg="cyan",
            wraplength=600,
        )
        result_label.pack(pady=10, padx=10)

        feedback_label = tk.Label(popup, text="", font=("Arial", 12), bg="black", fg="cyan")
        feedback_label.pack(pady=(0, 5))

        def _crew_index_from_selection():
            list_index = selection["list_index"]
            if list_index is None or list_index < 0 or list_index >= len(assignable_indices):
                return None
            return assignable_indices[list_index]

        def update_result(_event=None):
            npc_indices = npc_listbox.curselection()
            job_indices = job_listbox.curselection()

            if npc_indices:
                selection["list_index"] = npc_indices[0]
            if job_indices:
                selection["job"] = job_listbox.get(job_indices[0])

            crew_index = _crew_index_from_selection()
            job = selection["job"]

            if crew_index is not None and job:
                member = _member_for_index(crew_index)
                result_label.config(text=f"{member.get('name', 'Unknown')} → {job}", fg="white")
            elif crew_index is not None:
                member = _member_for_index(crew_index)
                result_label.config(
                    text=f"{member.get('name', 'Unknown')} — select a job.", fg="cyan"
                )
            elif job:
                result_label.config(text=f"Select an NPC for {job}.", fg="cyan")
            else:
                result_label.config(text="Select an NPC and a job to confirm.", fg="cyan")

        npc_listbox.bind("<<ListboxSelect>>", update_result)
        job_listbox.bind("<<ListboxSelect>>", update_result)

        def assign_role():
            crew_index = _crew_index_from_selection()
            job = selection["job"]

            if crew_index is None or not job:
                feedback_label.config(text="Select both an NPC and a job first.", fg="orange")
                popup.after(3000, lambda: feedback_label.config(text=""))
                return

            if crew_index != PLAYER_INDEX and (
                crew_index < 0 or crew_index >= len(self.station_crew)
            ):
                feedback_label.config(text="Invalid NPC selection.", fg="red")
                popup.after(3000, lambda: feedback_label.config(text=""))
                return

            job_info = JOBS.get(job)
            if not job_info:
                feedback_label.config(text="Invalid job selection.", fg="red")
                popup.after(3000, lambda: feedback_label.config(text=""))
                return

            if job == "Captain" and not player_is_captain:
                feedback_label.config(
                    text="Only the Captain can assign the Captain role.", fg="orange"
                )
                popup.after(3000, lambda: feedback_label.config(text=""))
                return

            member = _member_for_index(crew_index)
            if (
                not player_is_captain
                and crew_index != PLAYER_INDEX
                and member.get("job") == "Captain"
            ):
                feedback_label.config(
                    text="Only the Captain can reassign the current Captain.", fg="orange"
                )
                popup.after(3000, lambda: feedback_label.config(text=""))
                return

            # Warn if the player Captain is demoting themselves with no other Captain left
            if (
                crew_index == PLAYER_INDEX
                and member.get("job") == "Captain"
                and job != "Captain"
                and not _station_has_other_captain(exclude_player=True)
            ):
                confirmed = messagebox.askyesno(
                    "Confirm Reassignment",
                    "You are about to give up captain access with no captain. Continue?",
                    parent=popup,
                )
                if not confirmed:
                    return

            member["job"] = job
            member["department"] = job_info["department"]
            member["subdepartment"] = job_info["subdepartment"]
            member["permissions"] = permissions_for_job(job)

            solar_activated = False
            if job == "Engineer":
                power = self.player_data.setdefault("station_power", {})
                if not power.get("solar_charging"):
                    power["solar_charging"] = True
                    solar_activated = True

            refresh_npc_list(preserve_crew_index=crew_index)

            result_label.config(text=f"{member.get('name', 'Unknown')} → {job}", fg="light green")
            feedback = f"Assigned {member.get('name', 'Unknown')} as {job}."
            if solar_activated:
                feedback += " Solar arrays are now active."
            feedback_label.config(text=feedback, fg="cyan")
            popup.after(3000, lambda: feedback_label.config(text=""))

        button_frame = tk.Frame(popup, bg="black")
        button_frame.pack(pady=10)

        exit_btn = tk.Button(
            button_frame, text="Exit", font=("Arial", 12), width=12, command=panel.close
        )
        exit_btn.pack(side=tk.LEFT, padx=10)

        assign_btn = tk.Button(
            button_frame, text="Assign Role", font=("Arial", 12), width=12, command=assign_role
        )
        assign_btn.pack(side=tk.LEFT, padx=10)

    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, DOOR_KEY, self.bridge_window)
    
    def on_closing(self):
        try_leave_through_door(
            self.bridge_window,
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
            stations=[
                {
                    "label": "Enter Captain's Station",
                    "command": self.access_captain_station,
                    "subdepartments": {"Captain"},
                },
                {
                    "label": "Enter HoP's Station",
                    "command": self.access_hop_station,
                    "subdepartments": {"Captain", "HoP"},
                },
            ],
            show_room_options=self.show_room_options,
            toggle_door_lock=self.toggle_door_lock,
            before_show=before_show,
        )

    def show_station_menu(self):
        """Return to main station menu options"""
        self._build_station_menu()
