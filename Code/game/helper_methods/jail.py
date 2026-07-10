"""Jail / arrest helpers: sentences, release, and prisoner lookups.

Sentences are tracked as absolute deadlines on the universal master game
clock (``jail_release_at_seconds``) rather than wall-clock timestamps.
Callers pass in the current ``elapsed_seconds`` (see ``game_clock.py``)
so this module never reads the wall clock itself.
"""

import datetime
import random
import tkinter as tk
from tkinter import messagebox

from game.maps import donut
from game.helper_methods.npc_movement import (
    has_post,
    location_for_post,
)

DEFAULT_SENTENCE_SECONDS = 5 * 60
ADD_TIME_SECONDS = 60
BRIBE_CHANCE = 0.35
BRIBE_MIN_CREDITS = 5
BRIBE_MAX_CREDITS = 50
FINE_REFUSE_CHANCE = 0.15


def _location_dict_from_key(key):
    x_str, y_str = key.split(",")
    return {"x": int(x_str), "y": int(y_str)}


def security_room_location():
    return _location_dict_from_key(donut.SECURITY_KEY)


def security_hallway_location():
    tile = donut.SPECIAL_ROOM_HALLWAY[donut.SECURITY_KEY]
    return {"x": tile[0], "y": tile[1]}


def _ensure_jail_fields(member):
    """Back-compat migration for saves made before jail existed."""
    member.setdefault("in_jail", False)
    member.setdefault("jail_release_at_seconds", None)
    # Drop the old wall-clock field from pre-refactor saves; it's unused now.
    member.pop("jail_release_at", None)
    member.setdefault("warrant", False)
    member.setdefault("warrant_reason", "")
    member.setdefault("fine_amount", 0)
    member.setdefault("fine_reason", "")


def warrant_reason_text(member, default="No reason on file"):
    """Return the warrant reason string, or default if missing/blank."""
    reason = (member.get("warrant_reason") or "").strip()
    return reason if reason else default


def has_fine(member):
    """Return True if the member has an unpaid fine."""
    try:
        return float(member.get("fine_amount", 0) or 0) > 0
    except (TypeError, ValueError):
        return False


def _fine_amount_value(member):
    try:
        return max(0, float(member.get("fine_amount", 0) or 0))
    except (TypeError, ValueError):
        return 0.0


def _fine_reason_text(member, default="No reason on file"):
    reason = (member.get("fine_reason") or "").strip()
    return reason if reason else default


def _clear_fine(member):
    member["fine_amount"] = 0
    member["fine_reason"] = ""


def _jail_for_fine(
    member,
    *,
    parent,
    game,
    is_player,
    guard_name,
    amount,
    reason,
    name,
    elapsed_seconds,
    refuse=False,
):
    """Arrest someone over an unpaid/refused fine. Returns 'jailed'."""
    if refuse:
        jail_message = (
            f"{guard_name} demands your unpaid fine of {amount:.0f} credits "
            f"({reason}), but you refuse to pay.\nYou are under arrest!"
            if is_player
            else (
                f"{name} refuses to pay their {amount:.0f}-credit fine ({reason}), "
                f"even though they have the credits.\n"
                f"{guard_name} arrests them."
            )
        )
        note = f"{name} was jailed for refusing to pay a {amount:.0f}-credit fine."
        player_note = f"Jailed for refusing to pay a {amount:.0f}-credit fine ({reason})."
    else:
        jail_message = (
            f"{guard_name} demands your unpaid fine of {amount:.0f} credits "
            f"({reason}), but you cannot pay.\nYou are under arrest for non-payment!"
            if is_player
            else (
                f"{name} cannot pay their {amount:.0f}-credit fine ({reason}).\n"
                f"{guard_name} arrests them for non-payment."
            )
        )
        note = f"{name} was jailed for failing to pay a {amount:.0f}-credit fine."
        player_note = f"Jailed for failing to pay a {amount:.0f}-credit fine ({reason})."

    arrest_member(
        member,
        reason=jail_message,
        game=game,
        is_player=is_player,
        show_message=bool(game),
        elapsed_seconds=elapsed_seconds,
    )
    if game is None:
        if parent is not None:
            messagebox.showinfo("Arrested", jail_message, parent=parent)
        else:
            messagebox.showinfo("Arrested", jail_message)
    if game is not None and hasattr(game, "add_note"):
        game.add_note(note)
    elif is_player:
        _add_player_note(member, None, player_note)
    return "jailed"


def resolve_fine_with_guard(
    member,
    *,
    parent,
    game=None,
    is_player=False,
    guard_name="Security",
    elapsed_seconds=0.0,
):
    """Collect an unpaid fine when the member meets a security guard.

    Pays if they can afford it (85% of the time); 15% chance they refuse and
    go to jail even with enough credits. Cannot afford -> jail.
    Returns 'paid', 'jailed', or None if there was no fine.
    """
    _ensure_jail_fields(member)
    if not has_fine(member) or is_jailed(member):
        return None

    amount = _fine_amount_value(member)
    reason = _fine_reason_text(member)
    name = member.get("name", "Someone")
    credits = float(member.get("credits", 0) or 0)

    if credits >= amount:
        # Even with enough money, they may stubbornly refuse to pay.
        if random.random() < FINE_REFUSE_CHANCE:
            return _jail_for_fine(
                member,
                parent=parent,
                game=game,
                is_player=is_player,
                guard_name=guard_name,
                amount=amount,
                reason=reason,
                name=name,
                elapsed_seconds=elapsed_seconds,
                refuse=True,
            )

        member["credits"] = credits - amount
        _clear_fine(member)
        message = (
            f"{guard_name} collects your unpaid fine of {amount:.0f} credits.\n"
            f"Reason: {reason}"
            if is_player
            else (
                f"{guard_name} collects {name}'s unpaid fine of {amount:.0f} credits.\n"
                f"Reason: {reason}"
            )
        )
        if parent is not None:
            messagebox.showinfo("Fine Paid", message, parent=parent)
        else:
            messagebox.showinfo("Fine Paid", message)
        if game is not None and hasattr(game, "add_note"):
            game.add_note(f"{name} paid a {amount:.0f}-credit fine ({reason}).")
        elif is_player:
            _add_player_note(
                member, None, f"Paid a {amount:.0f}-credit fine ({reason})."
            )
        return "paid"

    return _jail_for_fine(
        member,
        parent=parent,
        game=game,
        is_player=is_player,
        guard_name=guard_name,
        amount=amount,
        reason=reason,
        name=name,
        elapsed_seconds=elapsed_seconds,
        refuse=False,
    )


def ensure_crew_jail_fields(player_data, station_crew):
    _ensure_jail_fields(player_data)
    for npc in station_crew:
        _ensure_jail_fields(npc)


def is_jailed(member):
    return bool(member.get("in_jail", False))


def jail_seconds_remaining(member, elapsed_seconds=0.0):
    """Return whole seconds left on a sentence, or 0 if not jailed / expired.

    ``elapsed_seconds`` is the current master game clock value (see
    ``game_clock.get_elapsed_seconds``).
    """
    if not is_jailed(member):
        return 0
    release_at = member.get("jail_release_at_seconds")
    if release_at is None:
        return 0
    return max(0, int(release_at - elapsed_seconds))


def format_jail_time(seconds):
    """Format remaining seconds as 'Xm Ys' (or 'Ys' if under a minute)."""
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _member_location_key(member):
    location = member.get("location") or {}
    if "x" not in location or "y" not in location:
        return None
    return f"{location.get('x')},{location.get('y')}"


def member_location_key(member):
    """Return 'x,y' location key for a crew member, or None."""
    return _member_location_key(member)


def members_in_room(station_crew, room_key, *, exclude=None):
    """Return non-jailed NPCs whose location matches room_key."""
    found = []
    for npc in station_crew:
        if exclude is not None and npc is exclude:
            continue
        if is_jailed(npc):
            continue
        if _member_location_key(npc) == room_key:
            found.append(npc)
    return found


def wanted_in_room(room_key, player_data, station_crew, *, exclude=None):
    """Return wanted, non-jailed NPCs currently in room_key (excludes player)."""
    wanted = []
    for npc in members_in_room(station_crew, room_key, exclude=exclude):
        if npc.get("warrant", False):
            wanted.append(npc)
    return wanted


def fined_in_room(room_key, player_data, station_crew, *, exclude=None):
    """Return non-jailed NPCs in room_key who have an unpaid fine."""
    fined = []
    for npc in members_in_room(station_crew, room_key, exclude=exclude):
        if has_fine(npc):
            fined.append(npc)
    return fined


def arrest_member(
    member, *, reason="", game=None, is_player=False, show_message=True, elapsed_seconds=0.0
):
    """Send a crew member to jail for the default sentence.

    Returns True if the arrest was applied, False if they were already jailed.
    Warrant stays active until release. ``elapsed_seconds`` is the current
    master game clock value; the release deadline is scheduled relative to it.
    """
    _ensure_jail_fields(member)
    if is_jailed(member):
        return False

    member["in_jail"] = True
    member["jail_release_at_seconds"] = elapsed_seconds + DEFAULT_SENTENCE_SECONDS
    member["location"] = security_room_location()
    member["room_visit_remaining"] = 0
    if has_post(member):
        member["on_duty"] = False

    name = member.get("name", "Someone")
    if game is not None and hasattr(game, "add_note"):
        game.add_note(f"{name} was arrested and sent to jail.")

    if is_player and game is not None:
        message = reason or (
            f"You have been arrested and sent to jail for "
            f"{format_jail_time(DEFAULT_SENTENCE_SECONDS)}."
        )
        if hasattr(game, "handle_player_arrest"):
            game.handle_player_arrest(message, show_message=show_message)
        elif show_message:
            from tkinter import messagebox

            messagebox.showinfo("Arrested", message, parent=getattr(game, "root", None))
    elif show_message and reason and game is not None:
        from game.helper_methods.ui_panels import report_message

        report_message("Arrest", reason, kind="info", parent=getattr(game, "root", None))

    return True


def release_member(member, *, is_player=False, game=None, show_message=True):
    """Release a prisoner: clear jail state and warrant, place them outside Security."""
    _ensure_jail_fields(member)
    if not is_jailed(member):
        return False

    name = member.get("name", "Someone")
    member["in_jail"] = False
    member["jail_release_at_seconds"] = None
    member["warrant"] = False
    member["warrant_reason"] = ""
    member["room_visit_remaining"] = 0

    if is_player:
        member["location"] = security_hallway_location()
    elif has_post(member):
        # Posted NPCs return to their job post after release.
        location = location_for_post(member.get("job"))
        if location is not None:
            member["on_duty"] = True
            member["location"] = location
        else:
            member["location"] = security_hallway_location()
    else:
        member["location"] = security_hallway_location()

    if game is not None and hasattr(game, "add_note"):
        game.add_note(f"{name} was released from jail.")

    if is_player and game is not None and show_message:
        if hasattr(game, "handle_player_release"):
            game.handle_player_release()
        else:
            from tkinter import messagebox

            messagebox.showinfo(
                "Released",
                "Your sentence is over. You are free to go.",
                parent=getattr(game, "root", None),
            )

    return True


def add_jail_time(member, elapsed_seconds=0.0, seconds=ADD_TIME_SECONDS):
    """Extend an active sentence. Returns True if time was added."""
    _ensure_jail_fields(member)
    if not is_jailed(member):
        return False

    remaining = jail_seconds_remaining(member, elapsed_seconds)
    member["jail_release_at_seconds"] = elapsed_seconds + remaining + seconds
    return True


def list_prisoners(player_data, station_crew):
    """Return (member, is_player) pairs currently in jail."""
    prisoners = []
    if is_jailed(player_data):
        prisoners.append((player_data, True))
    for npc in station_crew:
        if is_jailed(npc):
            prisoners.append((npc, False))
    return prisoners


def tick_jail_releases(game):
    """Release anyone whose sentence has expired. Returns list of released names."""
    from game.helper_methods.game_clock import get_elapsed_seconds

    released = []
    player_data = game.player_data
    station_crew = game.station_crew
    elapsed_seconds = get_elapsed_seconds(player_data)

    ensure_crew_jail_fields(player_data, station_crew)

    if is_jailed(player_data) and jail_seconds_remaining(player_data, elapsed_seconds) <= 0:
        release_member(player_data, is_player=True, game=game, show_message=True)
        released.append(player_data.get("name", "You"))

    for npc in station_crew:
        if is_jailed(npc) and jail_seconds_remaining(npc, elapsed_seconds) <= 0:
            name = npc.get("name", "A crew member")
            release_member(npc, is_player=False, game=game, show_message=False)
            released.append(name)

    return released


def arrest_wanted_in_room(
    room_key, player_data, station_crew, *, game=None, guard=None, elapsed_seconds=0.0
):
    """Arrest wanted NPCs (and player) currently in room_key. Returns arrest count."""
    arrested = 0

    for npc in members_in_room(station_crew, room_key, exclude=guard):
        if npc.get("warrant", False) and not is_jailed(npc):
            name = npc.get("name", "A crew member")
            charge = warrant_reason_text(npc)
            if arrest_member(
                npc,
                reason=(
                    f"{name} was arrested by security and sent to jail.\n"
                    f"Charge: {charge}"
                ),
                game=game,
                is_player=False,
                show_message=bool(game),
                elapsed_seconds=elapsed_seconds,
            ):
                arrested += 1

    if (
        player_data.get("warrant", False)
        and not is_jailed(player_data)
        and _member_location_key(player_data) == room_key
    ):
        charge = warrant_reason_text(player_data)
        if arrest_member(
            player_data,
            reason=(
                "A security guard found you while you were wanted. You are under arrest!\n"
                f"Charge: {charge}"
            ),
            game=game,
            is_player=True,
            show_message=True,
            elapsed_seconds=elapsed_seconds,
        ):
            arrested += 1

    return arrested


def _ask_arrest_or_let_go(parent, message):
    """Modal with Arrest / Let Go. Returns 'arrest' or 'let_go'."""
    result = {"choice": "let_go"}

    dialog = tk.Toplevel(parent)
    dialog.title("Wanted Crew")
    dialog.configure(bg="black")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)

    label = tk.Label(
        dialog,
        text=message,
        font=("Arial", 12),
        bg="black",
        fg="white",
        justify=tk.LEFT,
        wraplength=420,
    )
    label.pack(padx=20, pady=20)

    button_frame = tk.Frame(dialog, bg="black")
    button_frame.pack(pady=(0, 16))

    def choose(choice):
        result["choice"] = choice
        dialog.destroy()

    tk.Button(
        button_frame,
        text="Arrest",
        font=("Arial", 12),
        width=12,
        command=lambda: choose("arrest"),
    ).pack(side=tk.LEFT, padx=8)

    tk.Button(
        button_frame,
        text="Let Go",
        font=("Arial", 12),
        width=12,
        command=lambda: choose("let_go"),
    ).pack(side=tk.LEFT, padx=8)

    dialog.update_idletasks()
    width = dialog.winfo_reqwidth()
    height = dialog.winfo_reqheight()
    try:
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        dialog.geometry(f"+{x}+{y}")
    except tk.TclError:
        pass

    dialog.protocol("WM_DELETE_WINDOW", lambda: choose("let_go"))
    parent.wait_window(dialog)
    return result["choice"]


def offer_player_arrest_choice(
    player_data, npc, *, parent, game=None, place="hall", elapsed_seconds=0.0
):
    """Let a Security Guard player Arrest or Let Go a wanted crew member.

    place: 'hall', 'room', or 'call'
    Returns 'arrest', 'let_go', or None if the NPC was not eligible.
    """
    if player_data.get("job") != "Security Guard":
        return None
    if is_jailed(player_data) or is_jailed(npc) or not npc.get("warrant", False):
        return None

    name = npc.get("name", "A crew member")
    job = npc.get("job", "Crew")
    charge = warrant_reason_text(npc)
    bribe_amount = None
    if random.random() < BRIBE_CHANCE:
        bribe_amount = random.randint(BRIBE_MIN_CREDITS, BRIBE_MAX_CREDITS)

    if place == "room":
        lines = [
            f"You scan the room and spot {name} ({job}).",
            f"They have an active warrant.\nCharge: {charge}",
        ]
        arrest_reason = (
            f"You arrest {name} in the room and send them to jail.\nCharge: {charge}"
        )
        let_go_note = f"Let wanted crew member {name} go after scanning a room."
        let_go_plain = f"You look the other way. {name} stays in the room."
    elif place == "call":
        lines = [
            f"{name} ({job}) answers your call and arrives.",
            f"Your scan shows they have an active warrant.\nCharge: {charge}",
        ]
        arrest_reason = (
            f"You arrest {name} after calling them back and send them to jail.\n"
            f"Charge: {charge}"
        )
        let_go_note = f"Let wanted crew member {name} go after calling them back."
        let_go_plain = f"You look the other way. {name} remains at their post."
    else:
        lines = [
            f"You stop {name} ({job}) in the hall.",
            f"They have an active warrant.\nCharge: {charge}",
        ]
        arrest_reason = (
            f"You arrest {name} in the hallway and send them to jail.\nCharge: {charge}"
        )
        let_go_note = f"Let wanted crew member {name} go in the hallway."
        let_go_plain = f"You wave {name} on. They disappear down the hallway."

    if bribe_amount is not None:
        lines.append(
            f'{name} leans in and whispers, "Look the other way and I\'ll make it '
            f'worth your while — {bribe_amount} credits."'
        )
    lines.append("\nWhat do you do?")

    choice = _ask_arrest_or_let_go(parent, "\n".join(lines))
    if choice == "arrest":
        arrest_member(
            npc,
            reason=arrest_reason,
            game=game,
            is_player=False,
            show_message=bool(game),
            elapsed_seconds=elapsed_seconds,
        )
        if game is None:
            messagebox.showinfo("Arrested", arrest_reason, parent=parent)
            _add_player_note(player_data, None, f"{name} was arrested and sent to jail.")
        return "arrest"

    if bribe_amount is not None:
        player_data["credits"] = player_data.get("credits", 0) + bribe_amount
        npc["warrant"] = False
        npc["warrant_reason"] = ""
        messagebox.showinfo(
            "Let Go",
            f"You look the other way. {name} slips you {bribe_amount} credits and hurries off.\n"
            "Their warrant has been quietly cleared.",
            parent=parent,
        )
        _add_player_note(
            player_data,
            game,
            f"Accepted a {bribe_amount}-credit bribe from {name}, "
            "cleared their warrant, and let them go.",
        )
    else:
        messagebox.showinfo("Let Go", let_go_plain, parent=parent)
        _add_player_note(player_data, game, let_go_note)

    return "let_go"


def _add_player_note(player_data, game, text):
    """Record a note via the game helper when available, else on player_data."""
    if game is not None and hasattr(game, "add_note"):
        game.add_note(text)
        return
    if "notes" not in player_data:
        player_data["notes"] = []
    player_data["notes"].append(
        {"timestamp": datetime.datetime.now().isoformat(), "text": text}
    )


def maybe_offer_arrest_after_call(player_data, npc, *, parent, game=None, elapsed_seconds=0.0):
    """If the player is Security and the called NPC is wanted, offer Arrest/Let Go."""
    return offer_player_arrest_choice(
        player_data, npc, parent=parent, game=game, place="call", elapsed_seconds=elapsed_seconds
    )
