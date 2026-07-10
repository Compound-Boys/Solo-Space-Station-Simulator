"""Jail / arrest helpers: sentences, release, and prisoner lookups."""

import datetime

from game.maps import donut
from game.helper_methods.npc_movement import (
    has_post,
    location_for_post,
)

DEFAULT_SENTENCE_SECONDS = 5 * 60
ADD_TIME_SECONDS = 60


def _location_dict_from_key(key):
    x_str, y_str = key.split(",")
    return {"x": int(x_str), "y": int(y_str)}


def security_room_location():
    return _location_dict_from_key(donut.SECURITY_KEY)


def security_hallway_location():
    tile = donut.SPECIAL_ROOM_HALLWAY[donut.SECURITY_KEY]
    return {"x": tile[0], "y": tile[1]}


def ensure_jail_fields(member):
    """Back-compat migration for saves made before jail existed."""
    member.setdefault("in_jail", False)
    member.setdefault("jail_release_at", None)
    member.setdefault("warrant", False)


def ensure_crew_jail_fields(player_data, station_crew):
    ensure_jail_fields(player_data)
    for npc in station_crew:
        ensure_jail_fields(npc)


def is_jailed(member):
    return bool(member.get("in_jail", False))


def jail_seconds_remaining(member):
    """Return whole seconds left on a sentence, or 0 if not jailed / expired."""
    if not is_jailed(member):
        return 0
    release_at = member.get("jail_release_at")
    if not release_at:
        return 0
    try:
        release_time = datetime.datetime.fromisoformat(release_at)
    except (TypeError, ValueError):
        return 0
    remaining = (release_time - datetime.datetime.now()).total_seconds()
    return max(0, int(remaining))


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


def arrest_member(member, *, reason="", game=None, is_player=False, show_message=True):
    """Send a crew member to jail for the default sentence.

    Returns True if the arrest was applied, False if they were already jailed.
    Warrant stays active until release.
    """
    ensure_jail_fields(member)
    if is_jailed(member):
        return False

    now = datetime.datetime.now()
    release_at = now + datetime.timedelta(seconds=DEFAULT_SENTENCE_SECONDS)
    member["in_jail"] = True
    member["jail_release_at"] = release_at.isoformat()
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
    ensure_jail_fields(member)
    if not is_jailed(member):
        return False

    name = member.get("name", "Someone")
    member["in_jail"] = False
    member["jail_release_at"] = None
    member["warrant"] = False
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


def add_jail_time(member, seconds=ADD_TIME_SECONDS):
    """Extend an active sentence. Returns True if time was added."""
    ensure_jail_fields(member)
    if not is_jailed(member):
        return False

    remaining = jail_seconds_remaining(member)
    new_release = datetime.datetime.now() + datetime.timedelta(seconds=remaining + seconds)
    member["jail_release_at"] = new_release.isoformat()
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
    released = []
    player_data = game.player_data
    station_crew = game.station_crew

    ensure_crew_jail_fields(player_data, station_crew)

    if is_jailed(player_data) and jail_seconds_remaining(player_data) <= 0:
        release_member(player_data, is_player=True, game=game, show_message=True)
        released.append(player_data.get("name", "You"))

    for npc in station_crew:
        if is_jailed(npc) and jail_seconds_remaining(npc) <= 0:
            name = npc.get("name", "A crew member")
            release_member(npc, is_player=False, game=game, show_message=False)
            released.append(name)

    return released


def arrest_wanted_in_room(room_key, player_data, station_crew, *, game=None, guard=None):
    """Arrest wanted NPCs (and player) currently in room_key. Returns arrest count."""
    arrested = 0

    for npc in members_in_room(station_crew, room_key, exclude=guard):
        if npc.get("warrant", False) and not is_jailed(npc):
            name = npc.get("name", "A crew member")
            if arrest_member(
                npc,
                reason=f"{name} was arrested by security and sent to jail.",
                game=game,
                is_player=False,
                show_message=bool(game),
            ):
                arrested += 1

    if (
        player_data.get("warrant", False)
        and not is_jailed(player_data)
        and _member_location_key(player_data) == room_key
    ):
        if arrest_member(
            player_data,
            reason="A security guard found you while you were wanted. You are under arrest!",
            game=game,
            is_player=True,
            show_message=True,
        ):
            arrested += 1

    return arrested
