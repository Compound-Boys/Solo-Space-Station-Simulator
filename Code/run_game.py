#!/usr/bin/env python3
"""
Run script for Space Station Explorer game
"""

import sys
import os

# Function to determine the base path for resources and saves
def get_base_path():
    """Get the base path for the application in both exe and script modes"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (pyinstaller)
        base_path = os.path.dirname(sys.executable)
    else:
        # If run as a normal Python script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return base_path

# Check Python version
if sys.version_info < (3, 6):
    print("This game requires Python 3.6 or higher")
    sys.exit(1)

# Try to import required modules
try:
    import tkinter as tk
    import matplotlib
except ImportError as e:
    print(f"Error: Missing required module: {e}")
    print("Please install required modules with: pip install -r requirements.txt")
    sys.exit(1)

# Run the game
if __name__ == "__main__":
    base_path = get_base_path()
    
    # Import and run the game
    try:
        from game.main import SpaceStationGame
        
        root = tk.Tk()
        app = SpaceStationGame(root, base_path)
        root.mainloop()
    except Exception as e:
        print(f"Error starting game: {e}")
        sys.exit(1)
