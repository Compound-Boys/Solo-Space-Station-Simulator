import tkinter as tk
from tkinter import messagebox

from game.helper_methods.door_control import can_control_door, toggle_door_lock as toggle_room_door_lock
from game.helper_methods.ui_panels import open_modal_panel
from game.special_rooms.shared import (
    build_room_shell,
    open_room_in_main_window,
    show_crew_manifest as render_crew_manifest,
    try_leave_through_door,
    show_station_menu as render_station_menu,
)
from game.maps.donut import SECURITY_KEY as DOOR_KEY

class Security:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self.security_window = open_room_in_main_window(
            parent_window, "Security", player_data, station_crew, return_callback
        )
        _, self.button_frame = build_room_shell(
            self.security_window,
            self.player_data,
            "Station Security Office",
            "The security office is filled with monitoring equipment. Screens showing various parts of the station line the walls. A few security officers monitor the feeds, while weapon lockers are secured along one wall.",
        )

        self._build_station_menu()
        
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
        
        if can_control_door(self.player_data, DOOR_KEY):
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
        """Show security station options for authorized personnel"""
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        manifest_btn = tk.Button(
            self.button_frame,
            text="View Crew Manifest",
            font=("Arial", 14),
            width=20,
            command=self.view_crew_manifest,
        )
        manifest_btn.pack(pady=10)

        warrant_btn = tk.Button(
            self.button_frame,
            text="Issue Warrant",
            font=("Arial", 14),
            width=20,
            command=self.show_issue_warrant,
        )
        warrant_btn.pack(pady=10)

        jail_btn = tk.Button(
            self.button_frame,
            text="View Jail",
            font=("Arial", 14),
            width=20,
            command=self.view_jail,
        )
        jail_btn.pack(pady=10)

        back_btn = tk.Button(
            self.button_frame,
            text="Back to Station Menu",
            font=("Arial", 14),
            width=20,
            command=self.show_station_menu,
        )
        back_btn.pack(pady=10)

        self.security_window.after(20, self.security_window.lift)
        self.security_window.focus_force()

    def view_crew_manifest(self):
        """Display the crew manifest (same logic as Bridge)"""
        render_crew_manifest(self.security_window, self.player_data, self.station_crew)

    def show_issue_warrant(self):
        """Open a warrant terminal listing the player and all station NPCs."""
        panel, popup = open_modal_panel(self.security_window, title="Issue Warrant")
        popup.configure(bg="black")

        title_label = tk.Label(
            popup, text="Issue Warrant", font=("Arial", 18, "bold"), bg="black", fg="white"
        )
        title_label.pack(pady=10)

        list_outer = tk.LabelFrame(
            popup, text="Crew", font=("Arial", 12), bg="black", fg="white"
        )
        list_outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(list_outer, orient=tk.VERTICAL)
        crew_listbox = tk.Listbox(
            list_outer,
            bg="black",
            fg="white",
            font=("Arial", 12),
            width=40,
            height=12,
            exportselection=False,
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=crew_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        crew_listbox.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.BOTH, expand=True)

        PLAYER_INDEX = -1
        member_indices = []

        def _member_for_index(crew_index):
            if crew_index == PLAYER_INDEX:
                return self.player_data
            return self.station_crew[crew_index]

        def _format_row(member, is_player=False):
            name = member.get("name", "Unknown")
            job = member.get("job", "Unknown")
            wanted = " [WANTED]" if member.get("warrant", False) else ""
            you = " (YOU)" if is_player else ""
            return f"{name} ({job}){you}{wanted}"

        def refresh_list(preserve_index=None):
            crew_listbox.delete(0, tk.END)
            member_indices.clear()

            member_indices.append(PLAYER_INDEX)
            crew_listbox.insert(tk.END, _format_row(self.player_data, is_player=True))

            for crew_index, npc in enumerate(self.station_crew):
                member_indices.append(crew_index)
                crew_listbox.insert(tk.END, _format_row(npc))

            if preserve_index is not None and 0 <= preserve_index < len(member_indices):
                crew_listbox.selection_set(preserve_index)
                crew_listbox.activate(preserve_index)

        def _selected_member():
            selection = crew_listbox.curselection()
            if not selection:
                messagebox.showwarning(
                    "No Selection",
                    "Select a crew member first.",
                    parent=popup,
                )
                return None, None
            list_index = selection[0]
            crew_index = member_indices[list_index]
            return list_index, _member_for_index(crew_index)

        def issue_warrant():
            list_index, member = _selected_member()
            if member is None:
                return
            if member.get("warrant", False):
                messagebox.showinfo(
                    "Warrant",
                    f"{member.get('name', 'That crew member')} already has an active warrant.",
                    parent=popup,
                )
                return
            member["warrant"] = True
            refresh_list(preserve_index=list_index)
            messagebox.showinfo(
                "Warrant Issued",
                f"Warrant issued for {member.get('name', 'Unknown')}.",
                parent=popup,
            )

        def clear_warrant():
            list_index, member = _selected_member()
            if member is None:
                return
            if not member.get("warrant", False):
                messagebox.showinfo(
                    "Warrant",
                    f"{member.get('name', 'That crew member')} does not have a warrant.",
                    parent=popup,
                )
                return
            member["warrant"] = False
            refresh_list(preserve_index=list_index)
            messagebox.showinfo(
                "Warrant Cleared",
                f"Warrant cleared for {member.get('name', 'Unknown')}.",
                parent=popup,
            )

        refresh_list()

        button_frame = tk.Frame(popup, bg="black")
        button_frame.pack(pady=10)

        issue_btn = tk.Button(
            button_frame, text="Issue Warrant", font=("Arial", 12), width=16, command=issue_warrant
        )
        issue_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(
            button_frame, text="Clear Warrant", font=("Arial", 12), width=16, command=clear_warrant
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        exit_btn = tk.Button(
            button_frame, text="Exit", font=("Arial", 12), width=10, command=panel.close
        )
        exit_btn.pack(side=tk.LEFT, padx=5)

    def view_jail(self):
        """Placeholder until the security guard / jail feature is implemented"""
        self.security_window.after(
            10,
            lambda: messagebox.showinfo(
                "Jail",
                "No prisoner in jail now.",
                parent=self.security_window,
            ),
        )
        self.security_window.after(20, self.security_window.lift)
        self.security_window.focus_force()
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, DOOR_KEY, self.security_window)
    
    def on_closing(self):
        try_leave_through_door(
            self.security_window,
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
                "label": "Enter Security Station",
                "command": self.access_security_station,
            }],
            show_room_options=self.show_room_options,
            toggle_door_lock=self.toggle_door_lock,
            before_show=before_show,
        )

    def show_station_menu(self):
        """Return to main station menu options"""
        self._build_station_menu()
