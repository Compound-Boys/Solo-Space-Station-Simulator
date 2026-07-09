from tkinter import messagebox

from game.maps.donut import (
    BRIDGE_KEY,
    MEDBAY_KEY,
    SECURITY_KEY,
    ENGINEERING_KEY,
    BAR_KEY,
    BOTANY_KEY,
)

SPECIAL_ROOM_DOORS = {
    BRIDGE_KEY: {
        "room_name": "Bridge",
        "desc_base": "The control center of the station.",
        "permission": frozenset({"Captain", "HoP"}),
    },
    MEDBAY_KEY: {
        "room_name": "MedBay",
        "desc_base": "The medical facility of the station.",
        "permission": frozenset({"Captain", "HoP", "Doctor"}),
    },
    SECURITY_KEY: {
        "room_name": "Security",
        "desc_base": "The security center of the station.",
        "permission": frozenset({"Captain", "Security"}),
    },
    ENGINEERING_KEY: {
        "room_name": "Engineering Bay",
        "desc_base": "The station's engineering and maintenance center.",
        "permission": frozenset({"Captain", "HoP", "Engineer"}),
    },
    BAR_KEY: {
        "room_name": "Bar",
        "desc_base": "The station's social hub where crew members can relax and enjoy drinks.",
        "permission": frozenset({"Captain", "HoP", "Bar"}),
    },
    BOTANY_KEY: {
        "room_name": "Botany Lab",
        "desc_base": "The station's plant cultivation and research facility.",
        "permission": frozenset({"Captain", "HoP", "Botany"}),
    },
}

ACCESS_ERROR = "Unable to access door control system."


def can_control_door(player_data, door_key):
    door = SPECIAL_ROOM_DOORS.get(door_key)
    if not door:
        return False
    return player_data.get("subdepartment", "") in door.get("permission", frozenset())


def is_door_locked(player_data, door_key):
    return player_data.get("ship_map", {}).get(door_key, {}).get("locked", False)


def _show_access_error(parent_window):
    parent_window.after(
        10,
        lambda: messagebox.showinfo("Door Control", ACCESS_ERROR, parent=parent_window),
    )
    parent_window.after(20, parent_window.lift)
    parent_window.focus_force()


def toggle_door_lock(player_data, door_key, parent_window):
    if not can_control_door(player_data, door_key):
        _show_access_error(parent_window)
        return False

    door = SPECIAL_ROOM_DOORS.get(door_key)
    if "ship_map" not in player_data:
        _show_access_error(parent_window)
        return False

    ship_map = player_data["ship_map"]
    if door_key not in ship_map:
        _show_access_error(parent_window)
        return False

    room_name = door["room_name"] if door else ship_map[door_key].get("name", "Room")
    desc_base = door["desc_base"] if door else ship_map[door_key].get("desc", "")

    if ship_map[door_key].get("locked", False):
        ship_map[door_key]["locked"] = False
        ship_map[door_key]["desc"] = f"{desc_base} The door is unlocked."
        message = f"The {room_name} door has been unlocked."
    else:
        ship_map[door_key]["locked"] = True
        ship_map[door_key]["desc"] = f"{desc_base} The door is locked."
        message = f"The {room_name} door has been locked."

    player_data["ship_map"] = ship_map

    parent_window.after(
        10,
        lambda: messagebox.showinfo("Door Control", message, parent=parent_window),
    )
    parent_window.after(20, parent_window.lift)
    parent_window.focus_force()
    return True
