"""NPC hallway movement: leaving/returning to post, calling NPCs back,
wandering, and hallway-passing detection.

Department-head NPCs (Captain, Head of Personnel, Security Guard, Doctor,
Engineer, Botanist, Bartender) are each tied to a "post" - the special room
for their job. They can randomly leave that post to wander the hallway ring,
and the player can "call" them back. Staff Assistants have no post; they
wander the ring continuously and can duck into special rooms for a few
rounds before popping back out.
"""

import random

from game.maps import donut

# Job -> the donut room key that job's NPC is posted at.
JOB_POST_KEY = {
    "Captain": donut.BRIDGE_KEY,
    "Head of Personnel": donut.BRIDGE_KEY,
    "Security Guard": donut.SECURITY_KEY,
    "Doctor": donut.MEDBAY_KEY,
    "Engineer": donut.ENGINEERING_KEY,
    "Botanist": donut.BOTANY_KEY,
    "Bartender": donut.BAR_KEY,
}

NPC_LEAVE_POST_CHANCE = 0.20
# Captain and Security Guard patrol more often (~25% higher leave chance).
PATROL_LEAVE_POST_CHANCE = 0.25
PATROL_JOBS = frozenset({"Captain", "Security Guard"})
NPC_CALL_SUCCESS_CHANCE = 0.75
NPC_AUTO_RETURN_CHANCE = 0.15
STAFF_ROOM_VISIT_CHANCE = 0.25
STAFF_ROOM_VISIT_ROUNDS = (2, 5)
NPC_EVENT_CHANCE = 0.15


def leave_post_chance_for(npc):
    """Return the per-round chance that this on-duty NPC leaves their post."""
    if npc.get("job") in PATROL_JOBS:
        return PATROL_LEAVE_POST_CHANCE
    return NPC_LEAVE_POST_CHANCE


# --- Lookups -----------------------------------------------------------

def has_post(npc):
    """Return True if this NPC's job is tied to a station post/room."""
    return npc.get("job") in JOB_POST_KEY


def post_key_for_job(job):
    """Return the donut room key for a job's post, or None if it has no post."""
    return JOB_POST_KEY.get(job)


def npcs_for_job(station_crew, job_name):
    """Return every NPC currently holding job_name."""
    return [npc for npc in station_crew if npc.get("job") == job_name]


def on_duty_npc_for_job(station_crew, job_name):
    """Return the first NPC holding job_name who is currently on duty, or None."""
    for npc in npcs_for_job(station_crew, job_name):
        if npc.get("on_duty", True):
            return npc
    return None


def any_npc_for_job(station_crew, job_name):
    """Return the first NPC holding job_name regardless of duty status, or None."""
    npcs = npcs_for_job(station_crew, job_name)
    return npcs[0] if npcs else None


# --- Location helpers ----------------------------------------------------

def _location_dict_from_key(key):
    x_str, y_str = key.split(",")
    return {"x": int(x_str), "y": int(y_str)}


def location_for_post(job):
    """Return the {'x','y'} location dict for a job's post, or None."""
    post_key = post_key_for_job(job)
    if post_key is None:
        return None
    return _location_dict_from_key(post_key)


def _hallway_tile_for_post(post_key):
    return donut.SPECIAL_ROOM_HALLWAY.get(post_key)


def _room_key_for_hallway_tile(tile):
    for room_key, hallway_tile in donut.SPECIAL_ROOM_HALLWAY.items():
        if hallway_tile == tile:
            return room_key
    return None


def _is_hallway_location(location):
    if not isinstance(location, dict) or "x" not in location or "y" not in location:
        return False
    key = f"{location.get('x')},{location.get('y')}"
    return key in donut.SHIP_MAP and key not in donut.SPECIAL_ROOM_TILES


def pick_random_hallway_location():
    """Return a random {'x','y'} location on a plain hallway tile (no special rooms)."""
    hallway_keys = [key for key in donut.SHIP_MAP if key not in donut.SPECIAL_ROOM_TILES]
    key = random.choice(hallway_keys)
    return _location_dict_from_key(key)


# --- Save/load migration --------------------------------------------------

def ensure_npc_movement_fields(station_crew):
    """Back-compat migration for saves made before NPC movement existed."""
    for npc in station_crew:
        npc.setdefault("in_jail", False)
        npc.setdefault("jail_release_at", None)
        npc.setdefault("warrant", False)
        npc.setdefault("warrant_reason", "")
        if npc.get("in_jail", False):
            npc["location"] = _location_dict_from_key(donut.SECURITY_KEY)
            npc["room_visit_remaining"] = 0
            if has_post(npc):
                npc["on_duty"] = False
            continue
        if has_post(npc):
            npc.setdefault("on_duty", True)
            if npc.get("on_duty", True):
                location = location_for_post(npc.get("job"))
                if location is not None:
                    npc["location"] = location
            npc.setdefault("room_visit_remaining", 0)
        else:
            npc.setdefault("room_visit_remaining", 0)
            if npc.get("room_visit_remaining", 0) <= 0 and not _is_hallway_location(
                npc.get("location")
            ):
                npc["location"] = pick_random_hallway_location()


# --- Leaving post ----------------------------------------------------------

def _send_npc_wandering(npc):
    """Mark a posted NPC as off duty and place them just outside their door."""
    npc["on_duty"] = False
    post_key = post_key_for_job(npc.get("job"))
    hallway_tile = _hallway_tile_for_post(post_key) if post_key else None
    if hallway_tile:
        npc["location"] = {"x": hallway_tile[0], "y": hallway_tile[1]}
    else:
        npc["location"] = pick_random_hallway_location()
    npc["room_visit_remaining"] = 0


def roll_departures(station_crew):
    """Randomly send on-duty posted NPCs away from their post."""
    for npc in station_crew:
        if npc.get("in_jail", False):
            continue
        if not has_post(npc):
            continue
        if not npc.get("on_duty", True):
            continue
        if random.random() < leave_post_chance_for(npc):
            _send_npc_wandering(npc)


# --- Returning to post -----------------------------------------------------

def _return_to_post(npc):
    npc["on_duty"] = True
    location = location_for_post(npc.get("job"))
    if location is not None:
        npc["location"] = location
    npc["room_visit_remaining"] = 0


def call_npc(npc):
    """Attempt to call an off-duty NPC back to their post.

    Returns (success, message).
    """
    name = npc.get("name", "They")
    if npc.get("on_duty", True):
        return True, f"{name} is already at their post."

    if random.random() < NPC_CALL_SUCCESS_CHANCE:
        _return_to_post(npc)
        return True, f"{name} answers the call and heads back to their post."

    return False, f"{name} doesn't answer. Maybe try calling again later."


def reassign_npc_post(npc, new_job):
    """Move an NPC to their new job's post right after their job changes.

    Call this after mutating npc["job"] = new_job. If the new job has a post,
    the NPC immediately reports there (on duty), even if they were away from
    their old post. If the new job has no post (e.g. Staff Assistant), they
    become a wanderer instead.
    """
    location = location_for_post(new_job)
    if location is not None:
        npc["on_duty"] = True
        npc["location"] = location
        npc["room_visit_remaining"] = 0
    else:
        npc.pop("on_duty", None)
        npc["room_visit_remaining"] = 0
        npc["location"] = pick_random_hallway_location()


# --- Wandering ---------------------------------------------------------

def _wander_one_step(npc, ship_map):
    """Move a wandering NPC one random valid step along the hallway ring."""
    location = npc.get("location")
    if not _is_hallway_location(location) or f"{location.get('x')},{location.get('y')}" not in ship_map:
        npc["location"] = pick_random_hallway_location()
        return

    x, y = location["x"], location["y"]
    directions = donut.get_available_directions(x, y)
    available = [direction for direction, ok in directions.items() if ok]
    if not available:
        return

    direction = random.choice(available)
    if direction == "north":
        x += 1
    elif direction == "south":
        x -= 1
    elif direction == "east":
        y += 1
    elif direction == "west":
        y -= 1

    key = f"{x},{y}"
    if key not in ship_map:
        return

    npc["location"] = {"x": x, "y": y}


def _apply_silent_npc_event(npc):
    """Apply a minor, silent stat change to a wandering NPC (no popup/log)."""
    limbs = npc.get("limbs")
    if not limbs:
        return

    outcome = random.choice(["minor_injury", "minor_heal", "nothing"])
    if outcome == "minor_injury":
        limb = random.choice(list(limbs.keys()))
        damage = random.randint(2, 8)
        limbs[limb] = max(0, limbs[limb] - damage)
    elif outcome == "minor_heal":
        injured = [limb for limb, health in limbs.items() if health < 100]
        if injured:
            limb = random.choice(injured)
            heal = random.randint(2, 8)
            limbs[limb] = min(100, limbs[limb] + heal)
    # "nothing" is intentionally a no-op so events don't always matter.


def _maybe_trigger_silent_event(npc):
    if random.random() < NPC_EVENT_CHANCE:
        _apply_silent_npc_event(npc)


def _advance_room_visit(npc):
    """Tick down an in-progress room visit. Returns True if still inside."""
    remaining = npc.get("room_visit_remaining", 0)
    if remaining <= 0:
        return False
    npc["room_visit_remaining"] = remaining - 1
    if npc["room_visit_remaining"] <= 0:
        _exit_visited_room(npc)
    return True


def _maybe_enter_room(npc, game=None, player_data=None, station_crew=None):
    """If standing outside a door, maybe duck into that room. Returns True if entered."""
    location = npc.get("location") or {}
    tile = (location.get("x"), location.get("y"))
    room_key = _room_key_for_hallway_tile(tile)
    if room_key and random.random() < STAFF_ROOM_VISIT_CHANCE:
        _enter_room(npc, room_key, game=game, player_data=player_data, station_crew=station_crew)
        return True
    return False


def _step_off_duty_npc(npc, ship_map, game=None, player_data=None, station_crew=None):
    """Advance a wandering (off-duty) posted NPC by one round."""
    if _advance_room_visit(npc):
        return
    if random.random() < NPC_AUTO_RETURN_CHANCE:
        _return_to_post(npc)
        return
    _wander_one_step(npc, ship_map)
    if _maybe_enter_room(npc, game=game, player_data=player_data, station_crew=station_crew):
        return
    _maybe_trigger_silent_event(npc)


def _enter_room(npc, room_key, game=None, player_data=None, station_crew=None):
    npc["location"] = _location_dict_from_key(room_key)
    npc["room_visit_remaining"] = random.randint(*STAFF_ROOM_VISIT_ROUNDS)

    # Security Guards check warrants when they enter a room.
    if npc.get("job") == "Security Guard" and station_crew is not None:
        from game.helper_methods.jail import arrest_wanted_in_room

        arrest_wanted_in_room(
            room_key,
            player_data or {},
            station_crew,
            game=game,
            guard=npc,
        )


def _exit_visited_room(npc):
    location = npc.get("location") or {}
    room_key = f"{location.get('x')},{location.get('y')}"
    hallway_tile = donut.SPECIAL_ROOM_HALLWAY.get(room_key)
    if hallway_tile:
        npc["location"] = {"x": hallway_tile[0], "y": hallway_tile[1]}
    else:
        npc["location"] = pick_random_hallway_location()


def _step_staff_assistant(npc, ship_map, game=None, player_data=None, station_crew=None):
    """Advance a wandering Staff Assistant by one round.

    They may already be visiting a room (room_visit_remaining > 0), in which
    case they just wait out the visit; otherwise they take a hallway step and
    may duck into a room they're standing outside of.
    """
    if _advance_room_visit(npc):
        return

    _wander_one_step(npc, ship_map)

    if _maybe_enter_room(npc, game=game, player_data=player_data, station_crew=station_crew):
        return

    _maybe_trigger_silent_event(npc)


def step_wanderers(station_crew, ship_map, game=None, player_data=None):
    """Advance every wandering NPC (off-duty posted NPCs + Staff Assistants)."""
    for npc in station_crew:
        if npc.get("in_jail", False):
            continue
        if has_post(npc):
            if npc.get("on_duty", True):
                continue
            _step_off_duty_npc(
                npc, ship_map, game=game, player_data=player_data, station_crew=station_crew
            )
        else:
            _step_staff_assistant(
                npc, ship_map, game=game, player_data=player_data, station_crew=station_crew
            )


# --- Hallway encounters ----------------------------------------------------

def find_hall_passersby(player_data, station_crew):
    """Return wandering NPCs whose location matches the player's current tile."""
    location = player_data.get("location") or {}
    player_tile = (location.get("x"), location.get("y"))

    passersby = []
    for npc in station_crew:
        if npc.get("in_jail", False):
            continue
        if has_post(npc) and npc.get("on_duty", True):
            continue
        if npc.get("room_visit_remaining", 0) > 0:
            continue

        npc_location = npc.get("location") or {}
        npc_tile = (npc_location.get("x"), npc_location.get("y"))
        if npc_tile == player_tile:
            passersby.append(npc)

    return passersby
