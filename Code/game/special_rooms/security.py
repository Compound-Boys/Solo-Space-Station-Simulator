import tkinter as tk
from tkinter import messagebox

from game.door_control import toggle_door_lock as toggle_room_door_lock
from game.special_rooms.shared import open_room_in_main_window, try_leave_through_door

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
        # Show access confirmation for authorized personnel
        self.security_window.after(10, lambda: messagebox.showinfo("Security Station", "Access granted. Welcome to the Security Station.", parent=self.security_window))
        # Make sure the window stays on top after dialog
        self.security_window.after(20, self.security_window.lift)
        self.security_window.focus_force()
    
    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, "6,6", self.security_window)
    
    def on_closing(self):
        try_leave_through_door(
            self.security_window,
            self.player_data,
            "6,6",
            self.return_callback,
            self.station_crew,
        )

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
