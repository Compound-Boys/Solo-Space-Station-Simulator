import datetime

import tkinter as tk
from tkinter import messagebox

from game.helper_methods.door_control import can_control_door, is_door_locked
from game.helper_methods.lighting_helper import (
    ensure_station_power_lighting,
    lighting_style,
)
from game.helper_methods.npc_movement import any_npc_for_job, call_npc, on_duty_npc_for_job
from game.helper_methods.jail import (
    format_jail_time,
    is_jailed,
    jail_seconds_remaining,
    maybe_offer_arrest_after_call,
)
from game.helper_methods.ui_panels import open_modal_panel

ROOM_GEOMETRY = "1012x759"


def room_lighting_chrome(player_data):
    """Clamp lighting for battery and return style dict for a special room shell."""
    station_power = ensure_station_power_lighting(player_data)
    level = station_power["system_levels"].get("hallway_lighting", 5)
    return lighting_style(level, place="room")


def build_room_shell(room_window, player_data, title, description):
    """Title, lit description, and primary button_frame. Returns (style, button_frame)."""
    style = room_lighting_chrome(player_data)
    room_bg, room_fg = style["bg"], style["fg"]

    room_label = tk.Label(
        room_window,
        text=title,
        font=("Arial", 24),
        bg=room_bg,
        fg="white",
    )
    room_label.pack(pady=30)

    desc_label = tk.Label(
        room_window,
        text=description + style["power_desc"],
        font=("Arial", 12),
        bg=room_bg,
        fg=room_fg,
        wraplength=600,
    )
    desc_label.pack(pady=10)

    button_frame = tk.Frame(room_window, bg=room_bg)
    button_frame.pack(pady=20)
    return style, button_frame


def add_note(player_data, text):
    """Append a timestamped note to player_data['notes']."""
    if "notes" not in player_data:
        player_data["notes"] = []
    player_data["notes"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "text": text,
    })


def leave_room(return_callback, player_data, station_crew):
    """Hand off to the game; main window is not destroyed."""
    return_callback(player_data, station_crew)


def quit_without_save(return_callback, player_data, station_crew):
    """Window X: quit the app without persisting or returning to the hallway."""
    player_data["_quit_without_save"] = True
    leave_room(return_callback, player_data, station_crew)


def open_room_in_main_window(parent_window, title, player_data, station_crew, return_callback):
    """Clear the main window and prepare it for a special room.

    Window X quits without saving; Exit Room buttons use leave_room / try_leave_through_door.
    """
    for widget in parent_window.winfo_children():
        widget.destroy()
    parent_window.title(title)
    parent_window.geometry(ROOM_GEOMETRY)
    style = room_lighting_chrome(player_data)
    parent_window.configure(bg=style["bg"])
    parent_window.protocol(
        "WM_DELETE_WINDOW",
        lambda: quit_without_save(return_callback, player_data, station_crew),
    )
    return parent_window



def try_leave_through_door(room_window, player_data, door_key, return_callback, station_crew):
    """Leave a special room unless its door is locked or the player is jailed."""
    from game.helper_methods.jail import format_jail_time, is_jailed, jail_seconds_remaining
    from game.maps.donut import SECURITY_KEY

    if is_jailed(player_data) and door_key == SECURITY_KEY:
        remaining = format_jail_time(jail_seconds_remaining(player_data))
        room_window.after(
            10,
            lambda: messagebox.showinfo(
                "In Jail",
                f"You are in jail. Time remaining: {remaining}.",
                parent=room_window,
            ),
        )
        room_window.after(20, room_window.lift)
        room_window.focus_force()
        return False

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
                wanted_tag = " [WANTED]" if crew_member.get("warrant", False) else ""
                jailed_tag = " [JAILED]" if crew_member.get("in_jail", False) else ""
                manifest_text.insert(
                    tk.END,
                    f"- {job}: {name}{player_tag}{wanted_tag}{jailed_tag}\n",
                    tag,
                )

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


def is_players_own_job(player_data, job_name):
    """Return True if the player themself currently holds job_name.

    Shared by every "Talk to X" / NPC-contact button so nobody can talk to
    or call themselves (e.g. a Captain player never sees "Talk to Captain").
    """
    return player_data.get("job") == job_name


def build_npc_contact_section(
    button_frame,
    player_data,
    station_crew,
    job_name,
    room_window,
    *,
    talk_label,
    talk_command,
    refresh_callback,
    absent_flavor=None,
):
    """Pack an NPC-dependent action button, gated on that NPC being present.

    - If the player themself holds job_name, nothing is packed - there's no
      one to talk to/call, since the player fills that role themself.
    - If an on-duty NPC holds job_name, pack the normal action button.
    - If an NPC holds job_name but is off duty (away from their post), pack a
      status label plus a "Call {name}" button that rolls a chance to bring
      them back, then rebuilds the room via refresh_callback.
    - If nobody holds job_name at all, pack nothing.

    Returns True if something was packed, False otherwise.
    """
    if is_players_own_job(player_data, job_name):
        return False

    on_duty_npc = on_duty_npc_for_job(station_crew, job_name)
    if on_duty_npc is not None and not is_jailed(on_duty_npc):
        tk.Button(
            button_frame,
            text=talk_label,
            font=("Arial", 14),
            width=20,
            command=talk_command,
        ).pack(pady=10)
        return True

    away_npc = any_npc_for_job(station_crew, job_name)
    if away_npc is None:
        return False

    # Jailed crew cannot be called back to their post.
    if is_jailed(away_npc):
        remaining = format_jail_time(jail_seconds_remaining(away_npc))
        name = away_npc.get("name", "They")
        tk.Label(
            button_frame,
            text=f"{name} is in jail and will be released in {remaining}.",
            font=("Arial", 11, "italic"),
            bg=button_frame.cget("bg"),
            fg="orange",
            wraplength=300,
        ).pack(pady=10)
        return True

    flavor = absent_flavor or f"The {job_name} is away from their post."
    tk.Label(
        button_frame,
        text=flavor,
        font=("Arial", 11, "italic"),
        bg=button_frame.cget("bg"),
        fg="light gray",
        wraplength=300,
    ).pack(pady=(10, 2))

    def _call_and_refresh():
        if is_jailed(away_npc):
            remaining = format_jail_time(jail_seconds_remaining(away_npc))
            messagebox.showinfo(
                "In Jail",
                f"{away_npc.get('name', 'They')} is in jail and will be released in {remaining}.",
                parent=room_window,
            )
            refresh_callback()
            room_window.after(20, room_window.lift)
            room_window.focus_force()
            return

        success, message = call_npc(away_npc)
        title = "Call Successful" if success else "No Answer"
        messagebox.showinfo(title, message, parent=room_window)
        if success:
            # Security Guard players scan anyone they call back for warrants.
            maybe_offer_arrest_after_call(
                player_data,
                away_npc,
                parent=room_window,
            )
        refresh_callback()
        room_window.after(20, room_window.lift)
        room_window.focus_force()

    tk.Button(
        button_frame,
        text=f"Call {away_npc.get('name', job_name)}",
        font=("Arial", 14),
        width=20,
        command=_call_and_refresh,
    ).pack(pady=10)
    return True


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
