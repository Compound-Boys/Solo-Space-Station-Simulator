"""Player hallway movement: directional travel and alcohol impairment checks."""

import random
from tkinter import messagebox

from game.helper_methods.alcohol_helper import stumble_chance, fall_chance
from game.helper_methods.jail import (
    format_jail_time,
    is_jailed,
    jail_seconds_remaining,
)
from game.helper_methods.npc_movement import (
    find_hall_passersby,
    roll_departures,
    step_wanderers,
)
from game.helper_methods.random_events import maybe_trigger_hallway_event


class PlayerMovementMixin:
    def _try_alcohol_movement_impairment(self):
        """Roll stumble (then optional fall) before moving. Return True if move is cancelled."""
        alcohol = self.player_data.get("alcohol_percent", 0) or 0
        s_chance = stumble_chance(alcohol)
        if s_chance <= 0 or random.random() >= (s_chance / 100.0):
            return False

        f_chance = fall_chance(alcohol)
        if f_chance > 0 and random.random() < (f_chance / 100.0):
            limbs = self.player_data.get("limbs") or {}
            if limbs:
                limb = random.choice(list(limbs.keys()))
                damage = random.randint(1, 5)
                original_health = limbs[limb]
                limbs[limb] = max(0, original_health - damage)
                limb_name = limb.replace("_", " ").title()
                messagebox.showinfo(
                    "You Fall",
                    f"You stumble and fall hard!\n\n"
                    f"Your {limb_name} took {damage}% blunt damage "
                    f"and is now at {limbs[limb]}%.",
                )
                self.add_note(
                    f"Fell while intoxicated ({alcohol:.1f}% alcohol). "
                    f"{limb_name} took {damage}% blunt damage "
                    f"(from {original_health}% to {limbs[limb]}%)."
                )
            else:
                messagebox.showinfo(
                    "You Fall",
                    "You stumble and fall hard!",
                )
                self.add_note(
                    f"Fell while intoxicated ({alcohol:.1f}% alcohol)."
                )
            return True

        messagebox.showinfo(
            "You Stumble",
            "You stumble and lose your footing. You stay where you are.",
        )
        self.add_note(
            f"Stumbled while intoxicated ({alcohol:.1f}% alcohol) and failed to move."
        )
        return True

    def move_direction(self, direction):
        """Move in the specified direction with random event chance"""
        if is_jailed(self.player_data):
            remaining = format_jail_time(jail_seconds_remaining(self.player_data))
            messagebox.showinfo(
                "In Jail",
                f"You are in jail. Time remaining: {remaining}.",
            )
            return

        if self._try_alcohol_movement_impairment():
            return

        x = self.player_data["location"]["x"]
        y = self.player_data["location"]["y"]

        if direction == "north":
            x += 1
        elif direction == "south":
            x -= 1
        elif direction == "east":
            y += 1
        elif direction == "west":
            y -= 1

        self.player_data["location"]["x"] = x
        self.player_data["location"]["y"] = y

        # Check if the destination exists in the ship map
        loc_key = f"{x},{y}"
        if loc_key not in self.ship_map:
            messagebox.showerror("Error", "You can't go that way!")
            self.player_data["location"]["x"] = x - (1 if direction == "north" else -1 if direction == "south" else 0)
            self.player_data["location"]["y"] = y - (1 if direction == "east" else -1 if direction == "west" else 0)

        # NPCs move independently of the player's own random hallway events:
        # posted NPCs may leave/return, and wandering NPCs take a step.
        roll_departures(self.station_crew)
        step_wanderers(
            self.station_crew,
            self.ship_map,
            game=self,
            player_data=self.player_data,
        )

        # If a room-entry warrant sweep just jailed the player, stop here.
        if is_jailed(self.player_data):
            return

        maybe_trigger_hallway_event(self)

        if is_jailed(self.player_data):
            return

        # Unconditional (not gated by the random-event roll above): if a
        # wandering NPC happens to be standing on the player's new tile,
        # they cross paths in the hallway — and security may arrest.
        for npc in find_hall_passersby(self.player_data, self.station_crew):
            if self._handle_hallway_security_encounter(npc):
                if is_jailed(self.player_data):
                    return
                continue
            messagebox.showinfo(
                "Crew Encounter",
                f"{npc.get('name', 'A crew member')} ({npc.get('job', 'Crew')}) passes you in the hall.",
            )

        # Refresh hallway view
        self.show_hallway()
