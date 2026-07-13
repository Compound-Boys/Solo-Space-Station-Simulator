import datetime

import tkinter as tk
from tkinter import messagebox

from game.character_methods.character_sheet import render_character_sheet
from game.helper_methods.door_control import (
    can_control_door,
    is_door_locked,
    toggle_door_lock as toggle_room_door_lock,
)
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
from game.helper_methods.game_clock import get_elapsed_seconds
from game.helper_methods.ui_panels import bind_mousewheel, open_modal_panel, refocus_window, schedule_ui_tick
from game.objects.items import ItemInventoryMixin

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


def show_holdings_popup(parent_window, player_data):
    """Show stock holdings as an in-main-window overlay."""
    panel, popup = open_modal_panel(parent_window, title="Stock Holdings")

    tk.Label(
        popup,
        text="Stock Holdings",
        font=("Arial", 18),
        bg="black",
        fg="white",
    ).pack(pady=10)

    frame = tk.Frame(popup, bg="black")
    frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    holdings_list = tk.Listbox(
        frame,
        bg="black",
        fg="white",
        font=("Arial", 12),
        width=30,
        height=15,
        yscrollcommand=scrollbar.set,
    )
    holdings_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=holdings_list.yview)

    if not player_data.get("stock_holdings", {}):
        holdings_list.insert(tk.END, "You don't own any company stocks.")
    else:
        for company, shares in player_data["stock_holdings"].items():
            holdings_list.insert(tk.END, f"{company}: {shares} shares")

    tk.Button(
        popup,
        text="Close",
        font=("Arial", 12),
        width=10,
        command=panel.close,
    ).pack(pady=10)


def show_notes_popup(parent_window, player_data):
    """Show character notes as an in-main-window overlay."""
    panel, popup = open_modal_panel(parent_window, title="Character Notes")

    tk.Label(
        popup,
        text="Character Notes",
        font=("Arial", 18),
        bg="black",
        fg="white",
    ).pack(pady=10)

    frame = tk.Frame(popup, bg="black")
    frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    notes_text = tk.Text(
        frame,
        bg="black",
        fg="white",
        font=("Arial", 12),
        width=60,
        height=20,
        yscrollcommand=scrollbar.set,
        wrap=tk.WORD,
    )
    notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=notes_text.yview)
    notes_text.config(state=tk.DISABLED)

    if player_data.get("notes"):
        notes_text.config(state=tk.NORMAL)
        for note in reversed(player_data["notes"]):
            if "timestamp" in note and "text" in note:
                try:
                    dt = datetime.datetime.fromisoformat(note["timestamp"])
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    formatted_time = note["timestamp"]
                notes_text.insert(tk.END, f"{formatted_time}:\n{note['text']}\n\n")
            else:
                notes_text.insert(tk.END, f"{str(note)}\n\n")
        notes_text.config(state=tk.DISABLED)
    else:
        notes_text.config(state=tk.NORMAL)
        notes_text.insert(tk.END, "No notes recorded yet.")
        notes_text.config(state=tk.DISABLED)

    tk.Button(
        popup,
        text="Close",
        font=("Arial", 12),
        width=10,
        command=panel.close,
    ).pack(pady=10)


def show_character_sheet(parent_window, player_data, on_inventory, on_close=None):
    """Open the character sheet as an in-main-window overlay."""
    panel, sheet_window = open_modal_panel(
        parent_window, title="Character Sheet", on_close=on_close
    )

    def render_sheet():
        for widget in list(sheet_window.winfo_children()):
            widget.destroy()

        tk.Button(
            sheet_window,
            text="Close",
            font=("Arial", 14),
            width=15,
            command=panel.close,
        ).pack(side=tk.BOTTOM, pady=20)

        def open_inventory():
            on_inventory(on_close=refresh_sheet_if_open)

        render_character_sheet(
            sheet_window,
            player_data,
            on_inventory=open_inventory,
            on_holdings=lambda: show_holdings_popup(parent_window, player_data),
            on_notes=lambda: show_notes_popup(parent_window, player_data),
        )

    def refresh_sheet_if_open():
        try:
            if sheet_window.winfo_exists() and not panel._closed:
                render_sheet()
        except tk.TclError:
            pass

    render_sheet()


def pack_character_sheet_button(parent_window, player_data, inventory_host):
    """Pack a Character Sheet button that opens the shared sheet overlay."""
    def open_sheet():
        on_close = getattr(inventory_host, "reload", None)
        show_character_sheet(
            parent_window,
            player_data,
            inventory_host.show_inventory_popup,
            on_close=on_close,
        )

    tk.Button(
        parent_window,
        text="Character Sheet",
        font=("Arial", 14),
        width=15,
        command=open_sheet,
    ).pack(pady=10)


def pack_hands_button(parent_window, inventory_host):
    """Pack a Hands button that opens the hands popup directly, without
    needing to go through Character Sheet > Inventory to equip items."""

    def open_hands():
        on_close = getattr(inventory_host, "reload", None)
        inventory_host.show_hands_popup(on_close=on_close)

    tk.Button(
        parent_window,
        text="Hands",
        font=("Arial", 14),
        width=15,
        command=open_hands,
    ).pack(pady=10)


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



def try_leave_through_door(
    room_window,
    player_data,
    door_key,
    return_callback,
    station_crew,
    *,
    before_leave=None,
):
    """Leave a special room unless its door is locked or the player is jailed."""
    from game.maps.donut import SECURITY_KEY

    if is_jailed(player_data) and door_key == SECURITY_KEY:
        remaining = format_jail_time(
            jail_seconds_remaining(player_data, get_elapsed_seconds(player_data))
        )
        room_window.after(
            10,
            lambda: messagebox.showinfo(
                "In Jail",
                f"You are in jail. Time remaining: {remaining}.",
                parent=room_window,
            ),
        )
        refocus_window(room_window)
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
        refocus_window(room_window)
        return False
    if before_leave is not None:
        before_leave()
    leave_room(return_callback, player_data, station_crew)
    return True


def clear_button_frame(button_frame):
    for widget in button_frame.winfo_children():
        widget.destroy()


def pack_station_back_button(button_frame, player_data, door_key, command):
    """Pack 'Back to Station Menu' when the player can control the room door."""
    if can_control_door(player_data, door_key):
        tk.Button(
            button_frame,
            text="Back to Station Menu",
            font=("Arial", 14),
            width=20,
            command=command,
        ).pack(pady=10)


PLAYER_CREW_INDEX = -1


def member_for_crew_index(crew_index, player_data, station_crew):
    if crew_index == PLAYER_CREW_INDEX:
        return player_data
    return station_crew[crew_index]


def build_labeled_listbox(parent, *, label, width=48, height=12, side=None, expand=True, padx=20, pady=10):
    """LabelFrame + Listbox + Scrollbar. Returns (outer, listbox)."""
    outer = tk.LabelFrame(
        parent, text=label, font=("Arial", 12), bg="black", fg="white"
    )
    if side is None:
        outer.pack(fill=tk.BOTH, expand=expand, padx=padx, pady=pady)
    else:
        outer.pack(side=side, fill=tk.BOTH, expand=expand, padx=padx)

    scrollbar = tk.Scrollbar(outer, orient=tk.VERTICAL)
    listbox = tk.Listbox(
        outer,
        bg="black",
        fg="white",
        font=("Arial", 12),
        width=width,
        height=height,
        exportselection=False,
        yscrollcommand=scrollbar.set,
    )
    scrollbar.config(command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.BOTH, expand=True)
    return outer, listbox


def refresh_indexed_listbox(listbox, member_indices, rows, *, preserve_index=None):
    """
    Clear listbox and member_indices, then for each (crew_index, row_text) in rows:
      append crew_index to member_indices and insert row_text.
    Optionally restore selection to preserve_index.
    """
    listbox.delete(0, tk.END)
    member_indices.clear()
    for crew_index, row_text in rows:
        member_indices.append(crew_index)
        listbox.insert(tk.END, row_text)
    if preserve_index is not None and 0 <= preserve_index < len(member_indices):
        listbox.selection_set(preserve_index)
        listbox.activate(preserve_index)


class SpecialRoomBase(ItemInventoryMixin):
    """Shared shell for door-keyed special rooms (not Quarters)."""

    ROOM_TITLE = ""
    ROOM_HEADING = ""
    ROOM_DESCRIPTION = ""
    DOOR_KEY = None
    WINDOW_ATTR = "room_window"

    def __init__(self, parent_window, player_data, station_crew, return_callback):
        self.parent_window = parent_window
        self.player_data = player_data
        self.station_crew = station_crew
        self.return_callback = return_callback

        self._before_open()

        room_window = open_room_in_main_window(
            parent_window,
            self.ROOM_TITLE,
            player_data,
            station_crew,
            return_callback,
        )
        setattr(self, self.WINDOW_ATTR, room_window)
        self.room_window = room_window
        self.root = room_window

        self._after_open()

        _, self.button_frame = build_room_shell(
            room_window,
            player_data,
            self.ROOM_HEADING,
            self.ROOM_DESCRIPTION,
        )
        self._build_station_menu()
        pack_character_sheet_button(room_window, player_data, self)
        pack_hands_button(room_window, self)
        tk.Button(
            room_window,
            text="Exit Room",
            font=("Arial", 14),
            width=15,
            command=self.on_closing,
        ).pack(pady=20)

    def reload(self):
        """Rebuild room chrome and menus from current player_data."""
        for widget in list(self.room_window.winfo_children()):
            widget.destroy()
        style = room_lighting_chrome(self.player_data)
        self.room_window.configure(bg=style["bg"])
        _, self.button_frame = build_room_shell(
            self.room_window,
            self.player_data,
            self.ROOM_HEADING,
            self.ROOM_DESCRIPTION,
        )
        self._build_station_menu()
        pack_character_sheet_button(self.room_window, self.player_data, self)
        pack_hands_button(self.room_window, self)
        tk.Button(
            self.room_window,
            text="Exit Room",
            font=("Arial", 14),
            width=15,
            command=self.on_closing,
        ).pack(pady=20)

    def _before_open(self):
        """Hook for setup that does not need the room window."""

    def _after_open(self):
        """Hook for setup that needs the room window."""

    def add_note(self, text):
        add_note(self.player_data, text)

    def toggle_door_lock(self):
        toggle_room_door_lock(self.player_data, self.DOOR_KEY, self.room_window)

    def _before_leave(self):
        """Hook called just before leaving through an unlocked door."""

    def on_closing(self):
        try_leave_through_door(
            self.room_window,
            self.player_data,
            self.DOOR_KEY,
            self.return_callback,
            self.station_crew,
            before_leave=self._before_leave,
        )

    def station_entries(self):
        """Return station menu entries: list of {label, command, subdepartments?}."""
        return []

    def _station_menu_before_show(self):
        """Optional callback passed to render_station_menu as before_show."""
        return None

    def _build_station_menu(self, before_show=None):
        if before_show is None:
            before_show = self._station_menu_before_show()
        show_station_menu(
            self.button_frame,
            self.player_data,
            door_key=self.DOOR_KEY,
            stations=self.station_entries(),
            show_room_options=self.show_room_options,
            toggle_door_lock=self.toggle_door_lock,
            before_show=before_show,
        )

    def show_station_menu(self):
        self._build_station_menu()

    def pack_back_to_station_menu(self):
        pack_station_back_button(
            self.button_frame,
            self.player_data,
            self.DOOR_KEY,
            self.show_station_menu,
        )


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

    bind_mousewheel(manifest_window, _on_manifest_mousewheel)

    close_btn = tk.Button(
        manifest_window,
        text="Close",
        font=("Arial", 12),
        command=manifest_window.destroy,
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
        name = away_npc.get("name", "They")

        def _jail_label_text():
            remaining = format_jail_time(
                jail_seconds_remaining(away_npc, get_elapsed_seconds(player_data))
            )
            return f"{name} is in jail and will be released in {remaining}."

        jail_label = tk.Label(
            button_frame,
            text=_jail_label_text(),
            font=("Arial", 11, "italic"),
            bg=button_frame.cget("bg"),
            fg="orange",
            wraplength=300,
        )
        jail_label.pack(pady=10)

        def _update_jail_label():
            if not is_jailed(away_npc):
                refresh_callback()
                return
            jail_label.config(text=_jail_label_text())

        schedule_ui_tick(jail_label, _update_jail_label)
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
            remaining = format_jail_time(
                jail_seconds_remaining(away_npc, get_elapsed_seconds(player_data))
            )
            messagebox.showinfo(
                "In Jail",
                f"{away_npc.get('name', 'They')} is in jail and will be released in {remaining}.",
                parent=room_window,
            )
            refresh_callback()
            refocus_window(room_window)
            return

        success, message = call_npc(away_npc, get_elapsed_seconds(player_data))
        title = "Call Successful" if success else "No Answer"
        messagebox.showinfo(title, message, parent=room_window)
        if success:
            # Security Guard / Captain players scan anyone they call back for warrants.
            maybe_offer_arrest_after_call(
                player_data,
                away_npc,
                parent=room_window,
                elapsed_seconds=get_elapsed_seconds(player_data),
            )
        refresh_callback()
        refocus_window(room_window)

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
    clear_button_frame(button_frame)

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
