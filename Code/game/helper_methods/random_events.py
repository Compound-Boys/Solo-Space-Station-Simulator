"""Hallway random-event catalog, trigger, and effect helpers."""

import random
from tkinter import messagebox

from game.helper_methods.stock_market import generate_market_tip
from game.helper_methods.ui_panels import report_message
from game.objects.items import ALL_ITEMS, get_item_definition

HALLWAY_EVENT_CHANCE = 0.20

# Transient buffer used while an event effect runs; None when idle.
_event_effect_messages = None


def maybe_trigger_hallway_event(game):
    """Roll for a hallway event and trigger one on success."""
    if random.random() < HALLWAY_EVENT_CHANCE:
        trigger_random_event(game)


def trigger_random_event(game):
    """Pick and run a random hallway event, then show a combined popup."""
    global _event_effect_messages

    events = [
        # Good events
        {
            "type": "good",
            "title": "Found Credits",
            "desc": "You found some credits on the floor!",
            "effect": lambda: add_credits(game, random.randint(50, 200)),
        },
        {
            "type": "good",
            "title": "Supply Crate",
            "desc": "You found an unsealed supply crate with useful items.",
            "effect": lambda: add_random_item(game),
        },
        {
            "type": "good",
            "title": "Market Tip",
            "desc": "You overheard a reliable market tip.",
            "effect": lambda: add_market_knowledge(game),
        },
        # Neutral events
        {
            "type": "neutral",
            "title": "Crew Member",
            "desc": "You passed by a crew member who nodded at you.",
            "effect": lambda: None,
        },
        {
            "type": "neutral",
            "title": "Announcement",
            "desc": "The station PA system makes an announcement.",
            "effect": lambda: station_announcement(game),
        },
        {
            "type": "neutral",
            "title": "Maintenance",
            "desc": "A maintenance drone passes by, cleaning the hallway.",
            "effect": lambda: None,
        },
        # Bad events - now all include blunt damage
        {
            "type": "bad",
            "title": "Lost Credits",
            "desc": (
                "You dropped some credits and couldn't find them all. "
                "You bumped your head looking for them."
            ),
            "effect": lambda: combined_effect(
                [
                    lambda: lose_credits(game, random.randint(10, 50)),
                    lambda: damage_limb(game, "head", 5, 10),
                ]
            ),
        },
        {
            "type": "bad",
            "title": "Small Explosion",
            "desc": "A nearby conduit explodes, showering you with hot sparks and debris!",
            "effect": lambda: combined_effect(
                [
                    lambda: damage_random_limb(game, 10, 25),  # Blunt damage from impact
                    lambda: add_burn_damage(game, 5, 15),  # Burn damage from sparks
                ]
            ),
        },
        {
            "type": "bad",
            "title": "Slip and Fall",
            "desc": "You slipped on a wet floor and fell hard.",
            "effect": lambda: damage_random_limb(game, 10, 20),
        },
        {
            "type": "bad",
            "title": "Steam Leak",
            "desc": "A pipe bursts, releasing scalding steam that burns your arm!",
            "effect": lambda: combined_effect(
                [
                    lambda: damage_limb(game, "left_arm", 5, 10),  # Blunt damage from impact
                    lambda: add_burn_damage(game, 15, 30),  # Burn damage from steam
                ]
            ),
        },
        {
            "type": "bad",
            "title": "Falling Debris",
            "desc": "A ceiling panel breaks loose and hits your head!",
            "effect": lambda: damage_limb(game, "head", 15, 35),
        },
        {
            "type": "bad",
            "title": "Maintenance Accident",
            "desc": "Your leg gets caught in an open floor grate!",
            "effect": lambda: damage_limb(game, "right_leg", 10, 20),
        },
        {
            "type": "bad",
            "title": "Chemical Spill",
            "desc": "You walk through a chemical spill! Your leg is burned and you feel ill.",
            "effect": lambda: combined_effect(
                [
                    lambda: damage_limb(game, "left_leg", 5, 10),  # Blunt damage from slipping
                    lambda: add_burn_damage(game, 5, 15),  # Burn damage from chemicals
                    lambda: add_poison_damage(game, 10, 20),  # Poison damage from fumes
                ]
            ),
        },
    ]

    event = random.choice(events)

    _event_effect_messages = []
    try:
        event["effect"]()
        body = event["desc"]
        if _event_effect_messages:
            body = body + "\n\n" + "\n".join(_event_effect_messages)
        messagebox.showinfo(event["title"], body)
    finally:
        _event_effect_messages = None


def _report_effect(game, title, message):
    """Show an effect popup, or buffer the message during a random event."""
    if _event_effect_messages is not None:
        _event_effect_messages.append(message)
    else:
        report_message(title, message, kind="info", parent=game.root)


def _add_damage_type(game, damage_key, label, min_damage, max_damage):
    """Apply incremental damage of a given type to the player."""
    damage = random.randint(min_damage, max_damage)
    original_damage = game.player_data["damage"].get(damage_key, 0)
    game.player_data["damage"][damage_key] = min(100, original_damage + damage)
    total = game.player_data["damage"][damage_key]
    _report_effect(
        game,
        f"{label} Damage",
        f"You suffered {damage}% {label.lower()} damage! Total {label.lower()} damage: {total}%.",
    )
    game.add_note(
        f"Suffered {label.lower()} damage: Took {damage}% damage (total now {total}%)"
    )


def add_burn_damage(game, min_damage, max_damage):
    """Apply burn damage to the player."""
    _add_damage_type(game, "burn", "Burn", min_damage, max_damage)


def add_poison_damage(game, min_damage, max_damage):
    """Apply poison damage to the player."""
    _add_damage_type(game, "poison", "Poison", min_damage, max_damage)


def combined_effect(effect_functions):
    """Apply multiple effects in sequence."""
    for effect_fn in effect_functions:
        effect_fn()


def damage_random_limb(game, min_damage, max_damage):
    """Damage a random limb by a random amount."""
    limb = random.choice(list(game.player_data["limbs"].keys()))
    damage_limb(game, limb, min_damage, max_damage)


def damage_limb(game, limb, min_damage, max_damage):
    """Damage a specific limb by a random amount within range (blunt damage)."""
    if limb in game.player_data["limbs"]:
        damage = random.randint(min_damage, max_damage)

        original_health = game.player_data["limbs"][limb]
        game.player_data["limbs"][limb] = max(0, original_health - damage)

        limb_name = limb.replace("_", " ").title()

        _report_effect(
            game,
            "Blunt Injury",
            f"Your {limb_name} took {damage}% blunt damage and is now at {game.player_data['limbs'][limb]}%.",
        )

        game.add_note(
            f"Suffered blunt damage to {limb_name}: Took {damage}% damage "
            f"(from {original_health}% to {game.player_data['limbs'][limb]}%)"
        )


def add_credits(game, amount):
    """Add credits to the player."""
    game.player_data["credits"] += amount
    _report_effect(game, "Credits Added", f"You gained {amount} credits.")
    game.add_note(
        f"Found {amount} credits. New balance: {game.player_data['credits']} credits."
    )


def lose_credits(game, amount):
    """Subtract credits from the player (min 0)."""
    old_credits = game.player_data["credits"]
    game.player_data["credits"] = max(0, old_credits - amount)
    _report_effect(game, "Credits Lost", f"You lost {amount} credits.")
    game.add_note(
        f"Lost {amount} credits. New balance: {game.player_data['credits']} credits."
    )


def add_random_item(game):
    """Add a random item (using item definitions) to the player's inventory."""
    available_item_ids = list(ALL_ITEMS.keys())

    if not available_item_ids:
        messagebox.showwarning("Error", "No items defined to be found.")
        return

    item_id = random.choice(available_item_ids)

    item_def = get_item_definition(item_id)

    if not item_def:
        messagebox.showerror("Error", f"Could not find definition for random item ID: {item_id}")
        return

    game.player_data.setdefault("inventory", [])

    game.player_data["inventory"].append(item_def)
    item_name = item_def.get("name", "an item")
    _report_effect(
        game,
        "Item Found",
        f"You found {item_name} and added it to your inventory.",
    )

    game.add_note(f"Found {item_name} ({item_id}) and added it to inventory.")


def add_market_knowledge(game):
    """Add market knowledge to the player - reveals a tip about a stock."""
    message = generate_market_tip(game.player_data["stock_market"].get("companies", []))
    if message is None:
        _report_effect(
            game,
            "Market Tip",
            "You heard a stock tip, but don't understand the market yet.",
        )
        return

    _report_effect(game, "Market Tip", message)
    game.add_note(f"Market Tip: {message}")


def station_announcement(game):
    """Display a random station announcement."""
    announcements = [
        "Reminder to all crew: safety protocols must be followed at all times.",
        "The cafeteria will be serving special meal rations today.",
        "Maintenance is scheduled in Sector 7 tomorrow.",
        "All personnel are reminded to report suspicious activity to security.",
        "Weekly crew meeting is postponed until further notice.",
        "Environmental controls are being recalibrated. Expect minor temperature fluctuations.",
    ]

    announcement = random.choice(announcements)
    _report_effect(
        game,
        "Station Announcement",
        f"The PA system crackles: '{announcement}'",
    )
