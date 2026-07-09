import datetime

import tkinter as tk
from tkinter import messagebox

from game.helper_methods.door_control import can_control_door, is_door_locked
from game.helper_methods.ui_panels import open_modal_panel

ROOM_GEOMETRY = "1012x759"  # 920x690 + 10%


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


def player_has_subdepartment_access(player_data, allowed_subdepartments):
    """Return True if the player's subdepartment is in the allowed set."""
    return player_data.get("subdepartment", "") in allowed_subdepartments


def show_crew_manifest(parent_window, player_data, station_crew):
    """Display the crew manifest as an in-main-window overlay."""
    panel, manifest_window = open_modal_panel(parent_window, title="Crew Manifest")

    title_label = tk.Label(
        manifest_window,
        text="Station Crew Manifest",
        font=("Arial", 18, "bold"),
        bg="black",
        fg="white",
    )
    title_label.pack(pady=10)

    frame = tk.Frame(manifest_window, bg="black")
    frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    manifest_text = tk.Text(
        frame,
        bg="black",
        fg="white",
        font=("Arial", 12),
        width=50,
        height=20,
        yscrollcommand=scrollbar.set,
        wrap=tk.WORD,
    )
    manifest_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=manifest_text.yview)

    manifest_text.tag_configure("header", font=("Arial", 14, "bold"), foreground="yellow")
    manifest_text.tag_configure("department", font=("Arial", 12, "bold"), foreground="light blue")
    manifest_text.tag_configure("name", font=("Arial", 11))
    manifest_text.tag_configure("player", font=("Arial", 11, "bold"), foreground="light green")
    manifest_text.tag_configure("npc", font=("Arial", 11), foreground="cyan")

    manifest_text.insert(tk.END, "STATION CREW MANIFEST\n", "header")
    manifest_text.insert(tk.END, "====================\n\n", "header")

    player_name = player_data.get("name", "Unknown")
    player_job = player_data.get("job", "Unknown")
    all_crew = [player_data] + station_crew

    departments = {
        "COMMAND": ["Captain", "Head of Personnel"],
        "SECURITY": ["Security Guard"],
        "MEDICAL": ["Doctor"],
        "ENGINEERING": ["Engineer"],
        "BOTANY": ["Botanist"],
        "SERVICE": ["Bartender"],
        "CIVILIAN": ["Staff Assistant"],
    }

    for dept_name, jobs_in_dept in departments.items():
        manifest_text.insert(tk.END, f"{dept_name}:\n", "department")
        found_in_dept = False
        for crew_member in all_crew:
            job = crew_member.get("job")
            name = crew_member.get("name")
            if job in jobs_in_dept:
                found_in_dept = True
                is_player = name == player_name and job == player_job
                tag = "player" if is_player else "npc"
                player_tag = " (YOU)" if is_player else ""
                manifest_text.insert(tk.END, f"- {job}: {name}{player_tag}\n", tag)

        if not found_in_dept:
            manifest_text.insert(tk.END, "- (No personnel assigned)\n", "name")
        manifest_text.insert(tk.END, "\n")

    manifest_text.config(state=tk.DISABLED)

    def _on_manifest_mousewheel(event):
        try:
            manifest_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    manifest_window.bind("<MouseWheel>", _on_manifest_mousewheel)

    def _close():
        try:
            manifest_window.unbind("<MouseWheel>")
        except tk.TclError:
            pass
        panel.close()

    close_btn = tk.Button(
        manifest_window,
        text="Close",
        font=("Arial", 12),
        command=_close,
    )
    close_btn.pack(pady=10)


def show_station_menu(
    button_frame,
    player_data,
    *,
    door_key,
    stations,
    show_room_options,
    toggle_door_lock,
    before_show=None,
):
    """Build the authorized station menu or fall back to regular room options."""
    for widget in button_frame.winfo_children():
        widget.destroy()

    if before_show is not None:
        before_show()

    if not can_control_door(player_data, door_key):
        show_room_options()
        return

    for station in stations:
        subdepartments = station.get("subdepartments")
        if subdepartments is not None and not player_has_subdepartment_access(
            player_data, subdepartments
        ):
            continue
        tk.Button(
            button_frame,
            text=station["label"],
            font=("Arial", 14),
            width=20,
            command=station["command"],
        ).pack(pady=10)

    tk.Button(
        button_frame,
        text="Lock/Unlock Door",
        font=("Arial", 14),
        width=20,
        command=toggle_door_lock,
    ).pack(pady=10)

    tk.Button(
        button_frame,
        text="Room Options",
        font=("Arial", 14),
        width=20,
        command=show_room_options,
    ).pack(pady=10)
