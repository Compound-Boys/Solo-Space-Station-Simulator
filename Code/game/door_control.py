from tkinter import messagebox

SPECIAL_ROOM_DOORS = {
    "6,0": {
        "room_name": "Bridge",
        "desc_base": "The control center of the station.",
        "permission": "bridge_station",
        "extra_jobs": frozenset({"Head of Personnel"}),
    },
    "0,6": {
        "room_name": "MedBay",
        "desc_base": "The medical facility of the station.",
        "permission": "medbay_station",
        "extra_jobs": frozenset(),
    },
    "6,6": {
        "room_name": "Security",
        "desc_base": "The security center of the station.",
        "permission": "security_station",
        "extra_jobs": frozenset(),
    },
    "6,3": {
        "room_name": "Engineering Bay",
        "desc_base": "The station's engineering and maintenance center.",
        "permission": "engineering_station",
        "extra_jobs": frozenset(),
    },
    "0,-1": {
        "room_name": "Bar",
        "desc_base": "The station's social hub where crew members can relax and enjoy drinks.",
        "permission": "bar_station",
        "extra_jobs": frozenset(),
    },
    "3,-1": {
        "room_name": "Botany Lab",
        "desc_base": "The station's plant cultivation and research facility.",
        "permission": "botany_station",
        "extra_jobs": frozenset({"Head of Personnel"}),
    },
}

ACCESS_ERROR = "Unable to access door control system."


def can_control_door(player_data, door_key):
    if player_data.get("job") == "Captain":
        return True

    door = SPECIAL_ROOM_DOORS.get(door_key)
    if not door:
        return False

    if player_data.get("permissions", {}).get(door["permission"], False):
        return True

    return player_data.get("job") in door.get("extra_jobs", frozenset())


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
