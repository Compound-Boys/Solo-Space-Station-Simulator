import tkinter as tk
from tkinter import messagebox

from game.door_control import can_control_door, toggle_door_lock as toggle_room_door_lock
from game.special_rooms.shared import open_room_in_main_window, try_leave_through_door, show_station_menu as render_station_menu

DOOR_KEY = "6,0"

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
