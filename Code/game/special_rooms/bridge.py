import random
import tkinter as tk
from tkinter import messagebox

from game.character_methods.character_creation import JOBS, permissions_for_job
from game.helper_methods.npc_movement import reassign_npc_post
from game.helper_methods.random_events import ensure_job_event
from game.helper_methods.station_status import show_station_status as render_station_status
from game.helper_methods.ui_panels import open_modal_panel, refocus_window
from game.special_rooms.shared import (
    PLAYER_CREW_INDEX,
    SpecialRoomBase,
    build_labeled_listbox,
    build_npc_contact_section,
    clear_button_frame,
    member_for_crew_index,
    refresh_indexed_listbox,
    show_crew_manifest as render_crew_manifest,
)
from game.maps.donut import BRIDGE_KEY


class Bridge(SpecialRoomBase):
    ROOM_TITLE = "Bridge"
    ROOM_HEADING = "Station Bridge"
    ROOM_DESCRIPTION = (
        "The bridge is the command center of the station. Multiple workstations with monitors "
        "displaying various station systems are arranged around the room. This is where the Captain "
        "and Department Heads coordinate station operations."
    )
    DOOR_KEY = BRIDGE_KEY
    WINDOW_ATTR = "bridge_window"

    def station_entries(self):
        return [
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
        ]

    def show_room_options(self):
        clear_button_frame(self.button_frame)

        talk_btn = tk.Button(
            self.button_frame,
            text="Talk to Ship Leadership",
            font=("Arial", 14),
            width=20,
            command=self.talk_to_leadership,
        )
        talk_btn.pack(pady=10)

        self.pack_back_to_station_menu()
    
    def _leadership_present(self):
        """Return which leadership jobs exist on the station (player + NPCs)."""
        all_crew = [self.player_data] + self.station_crew
        jobs = {member.get("job") for member in all_crew}
        return {
            "captain": "Captain" in jobs,
            "hop": "Head of Personnel" in jobs,
        }

    def talk_to_leadership(self):
        """Show Captain/HoP talk options when leadership is present on the station."""
        present = self._leadership_present()
        if not present["captain"] and not present["hop"]:
            self.bridge_window.after(
                10,
                lambda: messagebox.showinfo(
                    "Bridge",
                    "Captain and Department Heads are not in.",
                    parent=self.bridge_window,
                ),
            )
            refocus_window(self.bridge_window)
            return

        clear_button_frame(self.button_frame)

        title = tk.Label(
            self.button_frame,
            text="Ship Leadership",
            font=("Arial", 16, "bold"),
            bg="black",
            fg="white",
        )
        title.pack(pady=10)

        if present["captain"]:
            build_npc_contact_section(
                self.button_frame,
                self.player_data,
                self.station_crew,
                "Captain",
                self.bridge_window,
                talk_label="Talk to Captain",
                talk_command=self.talk_to_captain,
                refresh_callback=self.talk_to_leadership,
                absent_flavor="The Captain is away from the bridge.",
            )

        if present["hop"]:
            build_npc_contact_section(
                self.button_frame,
                self.player_data,
                self.station_crew,
                "Head of Personnel",
                self.bridge_window,
                talk_label="Talk to HoP",
                talk_command=self.show_hop_talk_menu,
                refresh_callback=self.talk_to_leadership,
                absent_flavor="The Head of Personnel is away from the bridge.",
            )

        return_btn = tk.Button(
            self.button_frame,
            text="Return to Bridge",
            font=("Arial", 14),
            width=20,
            command=self.show_room_options,
        )
        return_btn.pack(pady=15)

    def talk_to_captain(self):
        """Captain is always too busy for casual conversation."""
        messagebox.showinfo(
            "Captain",
            "The Captain is too busy for your chats.",
            parent=self.bridge_window,
        )
        refocus_window(self.bridge_window)

    def show_hop_talk_menu(self):
        """HoP interaction menu for non-command crew."""
        clear_button_frame(self.button_frame)

        title = tk.Label(
            self.button_frame,
            text="Head of Personnel",
            font=("Arial", 16, "bold"),
            bg="black",
            fg="white",
        )
        title.pack(pady=10)

        access_btn = tk.Button(
            self.button_frame,
            text="Access Control",
            font=("Arial", 14),
            width=20,
            command=self.show_access_control,
        )
        access_btn.pack(pady=5)

        talk_btn = tk.Button(
            self.button_frame,
            text="Talk to HoP",
            font=("Arial", 14),
            width=20,
            command=self.resolve_hop_access_request,
        )
        talk_btn.pack(pady=5)

        return_btn = tk.Button(
            self.button_frame,
            text="Return to Bridge",
            font=("Arial", 14),
            width=20,
            command=self.show_room_options,
        )
        return_btn.pack(pady=15)

    def show_access_control(self):
        """Job request terminal: submit a non-Admin job request for HoP approval."""
        panel, popup = open_modal_panel(self.bridge_window, title="Access Control")
        popup.configure(bg="black")

        title_label = tk.Label(
            popup, text="Access Control", font=("Arial", 18, "bold"), bg="black", fg="white"
        )
        title_label.pack(pady=10)

        job_outer = tk.LabelFrame(
            popup, text="Requestable Jobs", font=("Arial", 12), bg="black", fg="white"
        )
        job_outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        job_scrollbar = tk.Scrollbar(job_outer, orient=tk.VERTICAL)
        job_listbox = tk.Listbox(
            job_outer,
            bg="black",
            fg="white",
            font=("Arial", 12),
            width=40,
            height=12,
            exportselection=False,
            yscrollcommand=job_scrollbar.set,
        )
        job_scrollbar.config(command=job_listbox.yview)
        job_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        job_listbox.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.BOTH, expand=True)

        requestable_jobs = [
            job_name
            for job_name, info in JOBS.items()
            if info.get("department") != "Administration"
        ]
        for job_name in requestable_jobs:
            job_listbox.insert(tk.END, job_name)

        selection = {"job": None}
        player_name = self.player_data.get("name", "Unknown")

        result_frame = tk.LabelFrame(
            popup, text="Result", font=("Arial", 12), bg="black", fg="white"
        )
        result_frame.pack(fill=tk.X, padx=20, pady=10)

        result_label = tk.Label(
            result_frame,
            text="Select a job to request.",
            font=("Arial", 12),
            bg="black",
            fg="cyan",
            wraplength=600,
        )
        result_label.pack(pady=10, padx=10)

        feedback_label = tk.Label(popup, text="", font=("Arial", 12), bg="black", fg="cyan")
        feedback_label.pack(pady=(0, 5))

        def update_result(_event=None):
            job_indices = job_listbox.curselection()
            if job_indices:
                selection["job"] = job_listbox.get(job_indices[0])
            job = selection["job"]
            if job:
                result_label.config(text=f"{player_name} → {job}", fg="white")
            else:
                result_label.config(text="Select a job to request.", fg="cyan")

        job_listbox.bind("<<ListboxSelect>>", update_result)

        def submit_request():
            job = selection["job"]
            if not job:
                feedback_label.config(text="Select a job first.", fg="orange")
                popup.after(3000, lambda: feedback_label.config(text=""))
                return
            if job not in JOBS or JOBS[job].get("department") == "Administration":
                feedback_label.config(text="That job cannot be requested here.", fg="red")
                popup.after(3000, lambda: feedback_label.config(text=""))
                return

            self.player_data["access_request"] = {
                "requested_job": job,
                "requester_name": player_name,
            }
            result_label.config(text=f"{player_name} → {job}", fg="light green")
            feedback_label.config(
                text=f"Request for {job} submitted for HoP approval.", fg="cyan"
            )
            popup.after(3000, lambda: feedback_label.config(text=""))

        button_frame = tk.Frame(popup, bg="black")
        button_frame.pack(pady=10)

        exit_btn = tk.Button(
            button_frame, text="Exit", font=("Arial", 12), width=12, command=panel.close
        )
        exit_btn.pack(side=tk.LEFT, padx=10)

        assign_btn = tk.Button(
            button_frame, text="Assign", font=("Arial", 12), width=12, command=submit_request
        )
        assign_btn.pack(side=tk.LEFT, padx=10)

    def _apply_access_request_job(self, job):
        """Apply a pending access request to the player or requesting NPC.

        Returns (ok, solar_activated, error_message).
        """
        job_info = JOBS.get(job)
        if not job_info or job_info.get("department") == "Administration":
            self.player_data.pop("access_request", None)
            return False, False, "Your access request was invalid and has been cleared."

        request = self.player_data.get("access_request") or {}
        requester_name = request.get("requester_name")
        player_name = self.player_data.get("name")

        solar_activated = False
        if job == "Engineer":
            power = self.player_data.setdefault("station_power", {})
            if not power.get("solar_charging"):
                power["solar_charging"] = True
                solar_activated = True

        # NPC-submitted request (HoP job event): update that crew member.
        if requester_name and requester_name != player_name:
            npc = next(
                (n for n in self.station_crew if n.get("name") == requester_name),
                None,
            )
            if npc is None:
                self.player_data.pop("access_request", None)
                return False, False, "The requester is no longer on the station. Request cleared."

            npc["job"] = job
            npc["department"] = job_info["department"]
            npc["subdepartment"] = job_info["subdepartment"]
            npc["permissions"] = permissions_for_job(job)
            reassign_npc_post(npc, job)
            self.player_data.pop("access_request", None)
            return True, solar_activated, None

        self.player_data["job"] = job
        self.player_data["department"] = job_info["department"]
        self.player_data["subdepartment"] = job_info["subdepartment"]
        self.player_data["permissions"] = permissions_for_job(job)
        ensure_job_event(self.player_data)

        self.player_data.pop("access_request", None)
        return True, solar_activated, None

    def _clear_access_request(self):
        self.player_data.pop("access_request", None)

    def resolve_hop_access_request(self):
        """Talk to HoP: resolve a pending access request with a 50/50 approve/deny."""
        request = self.player_data.get("access_request")
        if not request or not request.get("requested_job"):
            messagebox.showinfo(
                "Head of Personnel",
                "The HoP is busy. Use the Access Control terminal to put in a request.",
                parent=self.bridge_window,
            )
            refocus_window(self.bridge_window)
            return

        job = request["requested_job"]
        approved = random.random() < 0.5
        if approved:
            ok, solar_activated, error = self._apply_access_request_job(job)
            if not ok:
                messagebox.showinfo(
                    "Head of Personnel",
                    error,
                    parent=self.bridge_window,
                )
            else:
                message = f"The HoP approved your request. You are now {job}."
                if solar_activated:
                    message += " Solar arrays are now active."
                messagebox.showinfo("Head of Personnel", message, parent=self.bridge_window)
        else:
            self._clear_access_request()
            messagebox.showinfo(
                "Head of Personnel",
                f"The HoP denied your request for {job}.",
                parent=self.bridge_window,
            )

        refocus_window(self.bridge_window)

    def show_hop_access_control_console(self):
        """HoP station console: review and approve/deny pending access requests."""
        panel, popup = open_modal_panel(self.bridge_window, title="Access Control")
        popup.configure(bg="black")

        tk.Label(
            popup,
            text="Access Control",
            font=("Arial", 18, "bold"),
            bg="black",
            fg="white",
        ).pack(pady=10)

        request = self.player_data.get("access_request")
        has_request = bool(request and request.get("requested_job"))

        status_frame = tk.LabelFrame(
            popup, text="Pending Requests", font=("Arial", 12), bg="black", fg="white"
        )
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        if has_request:
            requester = request.get("requester_name", "Unknown")
            job = request["requested_job"]
            tk.Label(
                status_frame,
                text=f"{requester} → {job}",
                font=("Arial", 14),
                bg="black",
                fg="cyan",
                wraplength=600,
            ).pack(pady=20, padx=10)
        else:
            tk.Label(
                status_frame,
                text="No pending requests.",
                font=("Arial", 14),
                bg="black",
                fg="gray",
            ).pack(pady=20, padx=10)

        feedback_label = tk.Label(popup, text="", font=("Arial", 12), bg="black", fg="cyan")
        feedback_label.pack(pady=(0, 5))

        def approve_request():
            req = self.player_data.get("access_request")
            if not req or not req.get("requested_job"):
                feedback_label.config(text="No pending request to approve.", fg="orange")
                return
            job = req["requested_job"]
            ok, solar_activated, error = self._apply_access_request_job(job)
            if not ok:
                feedback_label.config(text=error, fg="red")
                return
            message = f"Approved. {req.get('requester_name', 'Crew')} is now {job}."
            if solar_activated:
                message += " Solar arrays are now active."
            panel.close()
            messagebox.showinfo("Access Control", message, parent=self.bridge_window)
            self.reload()

        def deny_request():
            req = self.player_data.get("access_request")
            if not req or not req.get("requested_job"):
                feedback_label.config(text="No pending request to deny.", fg="orange")
                return
            job = req["requested_job"]
            self._clear_access_request()
            panel.close()
            messagebox.showinfo(
                "Access Control",
                f"Denied request for {job}.",
                parent=self.bridge_window,
            )
            refocus_window(self.bridge_window)

        button_frame = tk.Frame(popup, bg="black")
        button_frame.pack(pady=10)

        tk.Button(
            button_frame, text="Close", font=("Arial", 12), width=12, command=panel.close
        ).pack(side=tk.LEFT, padx=10)

        if has_request:
            tk.Button(
                button_frame,
                text="Deny",
                font=("Arial", 12),
                width=12,
                command=deny_request,
            ).pack(side=tk.LEFT, padx=10)
            tk.Button(
                button_frame,
                text="Approve",
                font=("Arial", 12),
                width=12,
                command=approve_request,
            ).pack(side=tk.LEFT, padx=10)

    def access_captain_station(self):
        """Access the Captain's Station interface"""
        clear_button_frame(self.button_frame)

        station_label = tk.Label(
            self.button_frame, text="Captain's Station", font=("Arial", 16, "bold"), bg="black", fg="white"
        )
        station_label.pack(pady=10)

        status_btn = tk.Button(
            self.button_frame,
            text="Station Status",
            font=("Arial", 14),
            width=20,
            command=self.show_station_status,
        )
        status_btn.pack(pady=5)

        security_btn = tk.Button(
            self.button_frame,
            text="Security Alerts",
            font=("Arial", 14),
            width=20,
            command=lambda: messagebox.showinfo(
                "Security Alerts", "No security alerts reported.", parent=self.bridge_window
            ),
        )
        security_btn.pack(pady=5)

        manifest_btn = tk.Button(
            self.button_frame, text="Crew Manifest", font=("Arial", 14), width=20, command=self.show_crew_manifest
        )
        manifest_btn.pack(pady=5)

        emergency_btn = tk.Button(
            self.button_frame,
            text="Emergency Protocols",
            font=("Arial", 14),
            width=20,
            command=lambda: messagebox.showinfo(
                "Emergency Protocols",
                "Emergency protocols ready for activation if needed.",
                parent=self.bridge_window,
            ),
        )
        emergency_btn.pack(pady=5)

        back_btn = tk.Button(
            self.button_frame,
            text="Back to Bridge Menu",
            font=("Arial", 14),
            width=20,
            command=self.show_station_menu,
        )
        back_btn.pack(pady=15)

        refocus_window(self.bridge_window)

    def access_hop_station(self):
        """Access the Head of Personnel (HoP) Station interface"""
        clear_button_frame(self.button_frame)

        station_label = tk.Label(
            self.button_frame,
            text="Head of Personnel Station",
            font=("Arial", 16, "bold"),
            bg="black",
            fg="white",
        )
        station_label.pack(pady=10)

        manifest_btn = tk.Button(
            self.button_frame, text="Crew Manifest", font=("Arial", 14), width=20, command=self.show_crew_manifest
        )
        manifest_btn.pack(pady=5)

        assignments_btn = tk.Button(
            self.button_frame, text="Job Assignments", font=("Arial", 14), width=20, command=self.show_job_assignments
        )
        assignments_btn.pack(pady=5)

        access_btn = tk.Button(
            self.button_frame,
            text="Access Control",
            font=("Arial", 14),
            width=20,
            command=self.show_hop_access_control_console,
        )
        access_btn.pack(pady=5)

        back_btn = tk.Button(
            self.button_frame,
            text="Back to Bridge Menu",
            font=("Arial", 14),
            width=20,
            command=self.show_station_menu,
        )
        back_btn.pack(pady=15)

        refocus_window(self.bridge_window)
    
    def show_station_status(self):
        """Display the live Station Status briefing for the Captain."""
        render_station_status(self.bridge_window, self.player_data, self.station_crew)

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

        _, npc_listbox = build_labeled_listbox(
            main_frame,
            label="Station NPCs",
            width=28,
            side=tk.LEFT,
            padx=(0, 10),
        )
        _, job_listbox = build_labeled_listbox(
            main_frame,
            label="Assignable Jobs",
            width=28,
            side=tk.LEFT,
            padx=0,
        )

        player_is_captain = (
            self.player_data.get("job") == "Captain"
            or self.player_data.get("subdepartment") == "Captain"
        )
        for job_name in JOBS:
            if job_name == "Captain" and not player_is_captain:
                continue
            job_listbox.insert(tk.END, job_name)

        # Listbox rows: PLAYER_CREW_INDEX = player (Captain only); else station_crew index.
        # Captain NPCs are hidden for non-Captains.
        assignable_indices = []

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
            rows = []
            if player_is_captain:
                player_name = self.player_data.get("name", "Unknown")
                player_job = self.player_data.get("job", "Unknown")
                rows.append((PLAYER_CREW_INDEX, f"{player_name} ({player_job}) (YOU)"))

            for crew_index, npc in enumerate(self.station_crew):
                if not player_is_captain and npc.get("job") == "Captain":
                    continue
                name = npc.get("name", "Unknown")
                job = npc.get("job", "Unknown")
                rows.append((crew_index, f"{name} ({job})"))

            refresh_indexed_listbox(npc_listbox, assignable_indices, rows)

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
                member = member_for_crew_index(
                    crew_index, self.player_data, self.station_crew
                )
                result_label.config(text=f"{member.get('name', 'Unknown')} → {job}", fg="white")
            elif crew_index is not None:
                member = member_for_crew_index(
                    crew_index, self.player_data, self.station_crew
                )
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

            if crew_index != PLAYER_CREW_INDEX and (
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

            member = member_for_crew_index(
                crew_index, self.player_data, self.station_crew
            )
            if (
                not player_is_captain
                and crew_index != PLAYER_CREW_INDEX
                and member.get("job") == "Captain"
            ):
                feedback_label.config(
                    text="Only the Captain can reassign the current Captain.", fg="orange"
                )
                popup.after(3000, lambda: feedback_label.config(text=""))
                return

            # Warn if the player Captain is demoting themselves with no other Captain left
            if (
                crew_index == PLAYER_CREW_INDEX
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
            if crew_index == PLAYER_CREW_INDEX:
                ensure_job_event(self.player_data)

            # NPCs (not the player) immediately report to their new post
            # rather than lingering at their old one.
            if crew_index != PLAYER_CREW_INDEX:
                reassign_npc_post(member, job)

            solar_activated = False
            if job == "Engineer":
                power = self.player_data.setdefault("station_power", {})
                if not power.get("solar_charging"):
                    power["solar_charging"] = True
                    solar_activated = True

            if crew_index == PLAYER_CREW_INDEX:
                panel.close()
                self.reload()
                return

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
