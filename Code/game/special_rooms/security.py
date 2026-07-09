import tkinter as tk
from tkinter import messagebox

from game.helper_methods.door_control import can_control_door, toggle_door_lock as toggle_room_door_lock
from game.special_rooms.shared import (
    open_room_in_main_window,
    show_crew_manifest as render_crew_manifest,
    try_leave_through_door,
    show_station_menu as render_station_menu,
)

DOOR_KEY = "6,6"

class Security:
    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self.security_window = open_room_in_main_window(parent_window, "Security", self.on_closing)
        
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
