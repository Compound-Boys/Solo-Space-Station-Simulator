#!/usr/bin/env python3
"""
Linux / AppImage entry point for Space Station Explorer.

Identical in spirit to run_game.py, with one crucial difference: an AppImage
is mounted read-only, so the game cannot write saves next to its own
executable the way the Windows build does. Instead we point base_path at a
writable per-user data directory following the XDG Base Directory spec
(defaults to ~/.local/share/SpaceStationExplorer).

base_path is only ever used by the game for the "game/saves" folder (verified
across game/main.py), so redirecting it changes nothing but where saves live.
"""

import sys
import os


def get_data_path():
    """Writable per-user data directory for saves (XDG compliant)."""
    xdg = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    return os.path.join(xdg, "SpaceStationExplorer")


# Check Python version (matches run_game.py)
if sys.version_info < (3, 6):
    print("This game requires Python 3.6 or higher")
    sys.exit(1)

# Ensure required modules are present (bundled by PyInstaller when frozen)
try:
    import tkinter as tk
    import matplotlib
    matplotlib.use("TkAgg")
except ImportError as e:
    print(f"Error: Missing required module: {e}")
    print("Please install required modules with: pip install -r requirements.txt")
    sys.exit(1)


if __name__ == "__main__":
    base_path = get_data_path()

    # main.py writes to base_path/game/saves; game.py's on-close autosave writes
    # to a CWD-relative game/saves. Create both and cd into the data dir so every
    # save path resolves somewhere writable.
    os.makedirs(os.path.join(base_path, "game", "saves"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "saves"), exist_ok=True)
    os.chdir(base_path)

    try:
        from game.main import SpaceStationGame

        root = tk.Tk()
        app = SpaceStationGame(root, base_path)
        root.mainloop()
    except Exception as e:
        print(f"Error starting game: {e}")
        sys.exit(1)
