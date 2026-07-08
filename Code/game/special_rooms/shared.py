import datetime

from tkinter import messagebox

from game.door_control import is_door_locked

ROOM_GEOMETRY = "800x600"


def add_note(player_data, text):
    """Append a timestamped note to player_data['notes']."""
    if "notes" not in player_data:
        player_data["notes"] = []
    player_data["notes"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "text": text,
    })


def open_room_in_main_window(parent_window, title, on_close):
    """Clear the main window and prepare it for a special room."""
    for widget in parent_window.winfo_children():
        widget.destroy()
    parent_window.title(title)
    parent_window.geometry(ROOM_GEOMETRY)
    parent_window.configure(bg="black")
    parent_window.protocol("WM_DELETE_WINDOW", on_close)
    return parent_window


def leave_room(return_callback, player_data, station_crew):
    """Hand off to the game; main window is not destroyed."""
    return_callback(player_data, station_crew)


def try_leave_through_door(room_window, player_data, door_key, return_callback, station_crew):
    """Leave a special room unless its door is locked."""
    if is_door_locked(player_data, door_key):
        room_window.after(
            10,
            lambda: messagebox.showinfo(
                "Locked Door",
                "The door is locked. You must unlock it before leaving.",
                parent=room_window,
            ),
        )
        room_window.after(20, room_window.lift)
        room_window.focus_force()
        return False
    leave_room(return_callback, player_data, station_crew)
    return True
