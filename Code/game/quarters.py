import tkinter as tk
from tkinter import ttk

class Quarters:
    def __init__(self, parent_window, player_data, return_callback):
        # Create a new toplevel window
        self.quarters_window = tk.Toplevel(parent_window)
        self.quarters_window.title("Your Quarters")
        self.quarters_window.geometry("800x600")
        
        # Store references
        self.parent_window = parent_window
        self.player_data = player_data
        self.return_callback = return_callback
        
        # Bind window closing
        self.quarters_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(self.quarters_window, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome message
        welcome_label = ttk.Label(
            self.main_frame,
            text=f"Welcome to your quarters, {player_data['name']}",
            font=("Arial", 16, "bold")
        )
        welcome_label.pack(pady=10)
        
        # Description
        description = "Your small but functional living space aboard the station. " + \
                      "All crew members get standard-issue quarters."
        desc_label = ttk.Label(
            self.main_frame,
            text=description,
            font=("Arial", 12),
            wraplength=600
        )
        desc_label.pack(pady=10)
        
        # Create interactive objects frame
        self.objects_frame = ttk.LabelFrame(
            self.main_frame,
            text="Interactive Objects",
            padding="10"
        )
        self.objects_frame.pack(fill=tk.X, pady=20)
        
        # Add interactive objects
        self.create_interactive_objects()
        
        # Character sheet button
        character_button = ttk.Button(
            self.main_frame,
            text="View Character Sheet",
            command=self.view_character_sheet
        )
        character_button.pack(pady=5)
        
        # Exit button
        exit_button = ttk.Button(
            self.main_frame,
            text="Exit Room",
            command=self.on_closing
        )
        exit_button.pack(pady=5) 

    def create_interactive_objects(self):
        """Create interactive objects in the quarters"""
        # Create a grid of interactive objects
        ttk.Button(
            self.objects_frame,
            text="Bed",
            command=self.interact_with_bed
        ).grid(row=0, column=0, padx=10, pady=10)
        
        ttk.Button(
            self.objects_frame,
            text="Personal Storage Locker",
            command=self.interact_with_locker
        ).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Button(
            self.objects_frame,
            text="Computer Terminal",
            command=self.interact_with_computer
        ).grid(row=0, column=2, padx=10, pady=10)
        
        ttk.Button(
            self.objects_frame,
            text="Door",
            command=self.on_closing
        ).grid(row=0, column=3, padx=10, pady=10)
    
    def interact_with_bed(self):
        """Show save game dialog when interacting with bed"""
        save_window = tk.Toplevel(self.quarters_window)
        save_window.title("Bed")
        save_window.geometry("300x150")
        save_window.transient(self.quarters_window)
        save_window.grab_set()
        
        # Center the window
        save_window.geometry("+%d+%d" % (self.quarters_window.winfo_rootx() + 250,
                                         self.quarters_window.winfo_rooty() + 200))
        
        # Create frame with padding
        save_frame = ttk.Frame(save_window, padding="20")
        save_frame.pack(fill=tk.BOTH, expand=True)
        
        # Message
        ttk.Label(
            save_frame,
            text="Would you like to save your game?",
            font=("Arial", 12)
        ).pack(pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(save_frame)
        buttons_frame.pack(pady=10)
        
        # Yes button
        ttk.Button(
            buttons_frame,
            text="Yes",
            command=lambda: self.save_game_and_close(save_window)
        ).pack(side=tk.LEFT, padx=10)
        
        # No button
        ttk.Button(
            buttons_frame,
            text="No",
            command=save_window.destroy
        ).pack(side=tk.LEFT, padx=10)
    
    def save_game_and_close(self, save_window):
        """Save the game and close the save dialog"""
        # Save game using Game's save_game method
        from game.game import Game
        Game.save_game(self.player_data)
        
        # Show confirmation
        tk.messagebox.showinfo("Game Saved", "Your game has been saved successfully.")
        
        # Close the save dialog
        save_window.destroy()
    
    def interact_with_locker(self):
        """Open the inventory when interacting with the locker"""
        from game.inventory import Inventory
        
        # Ensure inventory exists in player data
        if "inventory" not in self.player_data:
            self.player_data["inventory"] = []
        
        # Open inventory
        inv = Inventory(self.quarters_window, self.player_data, self.update_player_data)
    
    def interact_with_computer(self):
        """Open the computer when interacting with the terminal"""
        from game.computer import Computer
        
        # Open computer
        comp = Computer(self.quarters_window, self.player_data, self.update_player_data)
    
    def update_player_data(self, updated_data):
        """Update player data from child windows"""
        self.player_data = updated_data
    
    def view_character_sheet(self):
        """Open the character sheet"""
        from game.character_sheet import CharacterSheet
        
        # Open character sheet
        cs = CharacterSheet(self.quarters_window, self.player_data)
    
    def on_closing(self):
        """Handle window closing"""
        self.return_callback(self.player_data)
        
        # Destroy the window
        self.quarters_window.destroy() 