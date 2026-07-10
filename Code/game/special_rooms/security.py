import tkinter as tk
from tkinter import messagebox

from game.helper_methods.ui_panels import open_modal_panel, refocus_window, schedule_ui_tick
from game.helper_methods.jail import (
    add_jail_time,
    format_jail_time,
    jail_seconds_remaining,
    list_prisoners,
    release_member,
    warrant_reason_text,
)
from game.helper_methods.game_clock import get_elapsed_seconds
from game.special_rooms.shared import (
    PLAYER_CREW_INDEX,
    SpecialRoomBase,
    build_labeled_listbox,
    build_npc_contact_section,
    clear_button_frame,
    leave_room,
    member_for_crew_index,
    refresh_indexed_listbox,
    show_crew_manifest as render_crew_manifest,
)
from game.maps.donut import SECURITY_KEY


class Security(SpecialRoomBase):
    ROOM_TITLE = "Security"
    ROOM_HEADING = "Station Security Office"
    ROOM_DESCRIPTION = (
        "The security office is filled with monitoring equipment. Screens showing various parts of "
        "the station line the walls. A few security officers monitor the feeds, while weapon lockers "
        "are secured along one wall."
    )
    DOOR_KEY = SECURITY_KEY
    WINDOW_ATTR = "security_window"

    def station_entries(self):
        return [{
            "label": "Enter Security Station",
            "command": self.access_security_station,
        }]

    def show_room_options(self):
        clear_button_frame(self.button_frame)

        build_npc_contact_section(
            self.button_frame,
            self.player_data,
            self.station_crew,
            "Security Guard",
            self.security_window,
            talk_label="Talk to Security Guard",
            talk_command=self.talk_to_guard,
            refresh_callback=self.show_room_options,
            absent_flavor="The security guard has stepped away from the office.",
        )

        self.pack_back_to_station_menu()

    def talk_to_guard(self):
        from game.helper_methods.jail import has_fine, is_jailed, resolve_fine_with_guard

        if has_fine(self.player_data) and not is_jailed(self.player_data):
            result = resolve_fine_with_guard(
                self.player_data,
                parent=self.security_window,
                game=None,
                is_player=True,
                guard_name="The security guard",
                elapsed_seconds=get_elapsed_seconds(self.player_data),
            )
            if result == "jailed":
                self.show_room_options()
            refocus_window(self.security_window)
            return

        self.security_window.after(
            10,
            lambda: messagebox.showinfo(
                "Security Guard",
                "The security agent waves you away without looking up from the cameras.",
                parent=self.security_window,
            ),
        )
        refocus_window(self.security_window)

    def access_security_station(self):
        """Show security station options for authorized personnel"""
        clear_button_frame(self.button_frame)

        manifest_btn = tk.Button(
            self.button_frame,
            text="View Crew Manifest",
            font=("Arial", 14),
            width=20,
            command=self.view_crew_manifest,
        )
        manifest_btn.pack(pady=10)

        warrant_btn = tk.Button(
            self.button_frame,
            text="Issue Warrant/Fine",
            font=("Arial", 14),
            width=20,
            command=self.show_issue_warrant,
        )
        warrant_btn.pack(pady=10)

        jail_btn = tk.Button(
            self.button_frame,
            text="View Jail",
            font=("Arial", 14),
            width=20,
            command=self.view_jail,
        )
        jail_btn.pack(pady=10)

        back_btn = tk.Button(
            self.button_frame,
            text="Back to Station Menu",
            font=("Arial", 14),
            width=20,
            command=self.show_station_menu,
        )
        back_btn.pack(pady=10)

        refocus_window(self.security_window)

    def view_crew_manifest(self):
        render_crew_manifest(self.security_window, self.player_data, self.station_crew)

    def show_issue_warrant(self):
        """Open a warrant/fine terminal listing the player and all station NPCs."""
        panel, popup = open_modal_panel(self.security_window, title="Issue Warrant/Fine")
        popup.configure(bg="black")

        title_label = tk.Label(
            popup, text="Issue Warrant/Fine", font=("Arial", 18, "bold"), bg="black", fg="white"
        )
        title_label.pack(pady=10)

        _, crew_listbox = build_labeled_listbox(popup, label="Crew")

        member_indices = []

        def _format_row(member, is_player=False):
            name = member.get("name", "Unknown")
            job = member.get("job", "Unknown")
            wanted = " [WANTED]" if member.get("warrant", False) else ""
            try:
                fine_amt = float(member.get("fine_amount", 0) or 0)
            except (TypeError, ValueError):
                fine_amt = 0
            fined = f" [FINE: {fine_amt:.0f}]" if fine_amt > 0 else ""
            you = " (YOU)" if is_player else ""
            return f"{name} ({job}){you}{wanted}{fined}"

        def refresh_list(preserve_index=None):
            rows = [
                (PLAYER_CREW_INDEX, _format_row(self.player_data, is_player=True)),
            ]
            for crew_index, npc in enumerate(self.station_crew):
                rows.append((crew_index, _format_row(npc)))
            refresh_indexed_listbox(
                crew_listbox, member_indices, rows, preserve_index=preserve_index
            )

        def _selected_member():
            selection = crew_listbox.curselection()
            if not selection:
                messagebox.showwarning(
                    "No Selection",
                    "Select a crew member first.",
                    parent=popup,
                )
                return None, None
            list_index = selection[0]
            crew_index = member_indices[list_index]
            return list_index, member_for_crew_index(
                crew_index, self.player_data, self.station_crew
            )

        def issue_warrant():
            list_index, member = _selected_member()
            if member is None:
                return
            if member.get("warrant", False):
                messagebox.showinfo(
                    "Warrant",
                    f"{member.get('name', 'That crew member')} already has an active warrant.",
                    parent=popup,
                )
                return

            reason = _prompt_warrant_reason(member)
            if reason is None:
                return

            member["warrant"] = True
            member["warrant_reason"] = reason
            refresh_list(preserve_index=list_index)
            messagebox.showinfo(
                "Warrant Issued",
                f"Warrant issued for {member.get('name', 'Unknown')}.\nReason: {reason}",
                parent=popup,
            )

        def _prompt_warrant_reason(member):
            """Ask for a warrant reason. Returns stripped text, or None if cancelled."""
            name = member.get("name", "Unknown")
            result = {"value": None, "confirmed": False}

            dialog = tk.Toplevel(popup)
            dialog.title("Warrant Reason")
            dialog.configure(bg="black")
            dialog.transient(popup)
            dialog.grab_set()
            dialog.resizable(False, False)

            tk.Label(
                dialog,
                text=f"Enter the reason for {name}'s warrant:",
                font=("Arial", 12),
                bg="black",
                fg="white",
                wraplength=360,
                justify=tk.LEFT,
            ).pack(padx=20, pady=(16, 8))

            entry = tk.Entry(dialog, font=("Arial", 12), width=40)
            entry.pack(padx=20, pady=8)
            entry.focus_set()

            button_row = tk.Frame(dialog, bg="black")
            button_row.pack(pady=(8, 16))

            def confirm():
                text = entry.get().strip()
                if not text:
                    messagebox.showwarning(
                        "Reason Required",
                        "Enter a reason for the warrant.",
                        parent=dialog,
                    )
                    return
                result["value"] = text
                result["confirmed"] = True
                dialog.destroy()

            def cancel():
                dialog.destroy()

            tk.Button(
                button_row, text="Confirm", font=("Arial", 12), width=12, command=confirm
            ).pack(side=tk.LEFT, padx=8)
            tk.Button(
                button_row, text="Cancel", font=("Arial", 12), width=12, command=cancel
            ).pack(side=tk.LEFT, padx=8)

            dialog.bind("<Return>", lambda _event: confirm())
            dialog.protocol("WM_DELETE_WINDOW", cancel)
            dialog.update_idletasks()
            width = dialog.winfo_reqwidth()
            height = dialog.winfo_reqheight()
            try:
                x = popup.winfo_rootx() + (popup.winfo_width() - width) // 2
                y = popup.winfo_rooty() + (popup.winfo_height() - height) // 2
                dialog.geometry(f"+{x}+{y}")
            except tk.TclError:
                pass
            popup.wait_window(dialog)

            if result["confirmed"]:
                return result["value"]
            return None

        def issue_fine():
            list_index, member = _selected_member()
            if member is None:
                return

            fine_data = _prompt_fine_details(member)
            if fine_data is None:
                return

            reason, amount = fine_data
            # Stack additional fines onto any existing unpaid amount.
            try:
                existing = float(member.get("fine_amount", 0) or 0)
            except (TypeError, ValueError):
                existing = 0
            member["fine_amount"] = existing + amount
            if existing > 0 and (member.get("fine_reason") or "").strip():
                member["fine_reason"] = (
                    f"{member.get('fine_reason').strip()}; {reason}"
                )
            else:
                member["fine_reason"] = reason

            refresh_list(preserve_index=list_index)
            messagebox.showinfo(
                "Fine Issued",
                f"Fine issued for {member.get('name', 'Unknown')}.\n"
                f"Amount: {amount:.0f} credits\nReason: {reason}\n"
                f"Total owed: {member['fine_amount']:.0f} credits",
                parent=popup,
            )

        def _prompt_fine_details(member):
            """Ask for fine reason and amount. Returns (reason, amount) or None."""
            name = member.get("name", "Unknown")
            result = {"reason": None, "amount": None, "confirmed": False}

            dialog = tk.Toplevel(popup)
            dialog.title("Issue Fine")
            dialog.configure(bg="black")
            dialog.transient(popup)
            dialog.grab_set()
            dialog.resizable(False, False)

            tk.Label(
                dialog,
                text=f"Issue a fine to {name}:",
                font=("Arial", 12),
                bg="black",
                fg="white",
                wraplength=360,
                justify=tk.LEFT,
            ).pack(padx=20, pady=(16, 8))

            tk.Label(
                dialog, text="Reason:", font=("Arial", 11), bg="black", fg="white"
            ).pack(anchor="w", padx=20)
            reason_entry = tk.Entry(dialog, font=("Arial", 12), width=40)
            reason_entry.pack(padx=20, pady=(2, 8))
            reason_entry.focus_set()

            tk.Label(
                dialog,
                text="Amount (credits):",
                font=("Arial", 11),
                bg="black",
                fg="white",
            ).pack(anchor="w", padx=20)
            amount_entry = tk.Entry(dialog, font=("Arial", 12), width=40)
            amount_entry.pack(padx=20, pady=(2, 8))

            button_row = tk.Frame(dialog, bg="black")
            button_row.pack(pady=(8, 16))

            def confirm():
                reason = reason_entry.get().strip()
                if not reason:
                    messagebox.showwarning(
                        "Reason Required",
                        "Enter a reason for the fine.",
                        parent=dialog,
                    )
                    return
                raw_amount = amount_entry.get().strip()
                try:
                    amount = float(raw_amount)
                except (TypeError, ValueError):
                    messagebox.showwarning(
                        "Invalid Amount",
                        "Enter a valid credit amount.",
                        parent=dialog,
                    )
                    return
                if amount <= 0:
                    messagebox.showwarning(
                        "Invalid Amount",
                        "Fine amount must be greater than zero.",
                        parent=dialog,
                    )
                    return
                result["reason"] = reason
                result["amount"] = amount
                result["confirmed"] = True
                dialog.destroy()

            def cancel():
                dialog.destroy()

            tk.Button(
                button_row, text="Confirm", font=("Arial", 12), width=12, command=confirm
            ).pack(side=tk.LEFT, padx=8)
            tk.Button(
                button_row, text="Cancel", font=("Arial", 12), width=12, command=cancel
            ).pack(side=tk.LEFT, padx=8)

            dialog.bind("<Return>", lambda _event: confirm())
            dialog.protocol("WM_DELETE_WINDOW", cancel)
            dialog.update_idletasks()
            width = dialog.winfo_reqwidth()
            height = dialog.winfo_reqheight()
            try:
                x = popup.winfo_rootx() + (popup.winfo_width() - width) // 2
                y = popup.winfo_rooty() + (popup.winfo_height() - height) // 2
                dialog.geometry(f"+{x}+{y}")
            except tk.TclError:
                pass
            popup.wait_window(dialog)

            if result["confirmed"]:
                return result["reason"], result["amount"]
            return None

        def clear_warrant():
            list_index, member = _selected_member()
            if member is None:
                return
            if not member.get("warrant", False):
                messagebox.showinfo(
                    "Warrant",
                    f"{member.get('name', 'That crew member')} does not have a warrant.",
                    parent=popup,
                )
                return
            member["warrant"] = False
            member["warrant_reason"] = ""
            refresh_list(preserve_index=list_index)
            messagebox.showinfo(
                "Warrant Cleared",
                f"Warrant cleared for {member.get('name', 'Unknown')}.",
                parent=popup,
            )

        refresh_list()

        button_frame = tk.Frame(popup, bg="black")
        button_frame.pack(pady=10)

        issue_btn = tk.Button(
            button_frame, text="Issue Warrant", font=("Arial", 12), width=14, command=issue_warrant
        )
        issue_btn.pack(side=tk.LEFT, padx=5)

        fine_btn = tk.Button(
            button_frame, text="Issue Fine", font=("Arial", 12), width=12, command=issue_fine
        )
        fine_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(
            button_frame, text="Clear Warrant", font=("Arial", 12), width=14, command=clear_warrant
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        exit_btn = tk.Button(
            button_frame, text="Exit", font=("Arial", 12), width=10, command=panel.close
        )
        exit_btn.pack(side=tk.LEFT, padx=5)

    def view_jail(self):
        """Open the Jail menu listing prisoners and sentence controls."""
        cancel_tick = {"fn": None}

        def _on_close():
            if cancel_tick["fn"] is not None:
                cancel_tick["fn"]()
                cancel_tick["fn"] = None

        panel, popup = open_modal_panel(self.security_window, title="Jail", on_close=_on_close)
        popup.configure(bg="black")

        title_label = tk.Label(
            popup, text="Jail", font=("Arial", 18, "bold"), bg="black", fg="white"
        )
        title_label.pack(pady=10)

        _, prisoner_listbox = build_labeled_listbox(popup, label="Prisoners")

        # Parallel to listbox rows: crew index (PLAYER_CREW_INDEX for the player)
        member_indices = []

        def _format_row(member, is_player=False):
            name = member.get("name", "Unknown")
            job = member.get("job", "Unknown")
            remaining = format_jail_time(
                jail_seconds_remaining(member, get_elapsed_seconds(self.player_data))
            )
            charge = warrant_reason_text(member)
            you = " (YOU)" if is_player else ""
            return f"{name} ({job}){you} — {remaining} remaining | Charge: {charge}"

        def refresh_list(preserve_index=None):
            if preserve_index is None:
                selection = prisoner_listbox.curselection()
                if selection:
                    preserve_index = selection[0]
            prisoners = list_prisoners(self.player_data, self.station_crew)
            if not prisoners:
                prisoner_listbox.delete(0, tk.END)
                member_indices.clear()
                prisoner_listbox.insert(tk.END, "No prisoners in jail.")
                return

            rows = []
            for member, is_player in prisoners:
                if is_player:
                    crew_index = PLAYER_CREW_INDEX
                else:
                    crew_index = self.station_crew.index(member)
                rows.append((crew_index, _format_row(member, is_player=is_player)))
            refresh_indexed_listbox(
                prisoner_listbox, member_indices, rows, preserve_index=preserve_index
            )

        def _selected_prisoner():
            selection = prisoner_listbox.curselection()
            if not selection or not member_indices:
                messagebox.showwarning(
                    "No Selection",
                    "Select a prisoner first.",
                    parent=popup,
                )
                return None, None, None
            list_index = selection[0]
            if list_index >= len(member_indices):
                messagebox.showwarning(
                    "No Selection",
                    "Select a prisoner first.",
                    parent=popup,
                )
                return None, None, None
            crew_index = member_indices[list_index]
            member = member_for_crew_index(
                crew_index, self.player_data, self.station_crew
            )
            is_player = crew_index == PLAYER_CREW_INDEX
            return list_index, member, is_player

        def pardon_prisoner():
            list_index, member, is_player = _selected_prisoner()
            if member is None:
                return
            name = member.get("name", "Unknown")
            release_member(member, is_player=is_player, game=None, show_message=False)
            if is_player:
                from game.helper_methods.jail import security_hallway_location

                member["location"] = security_hallway_location()
                messagebox.showinfo(
                    "Pardon",
                    f"{name} has been pardoned and released from jail.",
                    parent=popup,
                )
                panel.close()
                # Player is no longer jailed; leave Security into the hallway.
                leave_room(self.return_callback, self.player_data, self.station_crew)
                return

            refresh_list()
            messagebox.showinfo(
                "Pardon",
                f"{name} has been pardoned and released from jail.",
                parent=popup,
            )

        def add_time():
            list_index, member, is_player = _selected_prisoner()
            if member is None:
                return
            if not add_jail_time(member, get_elapsed_seconds(self.player_data)):
                messagebox.showinfo(
                    "Add Time",
                    "Could not add time to that sentence.",
                    parent=popup,
                )
                return
            refresh_list(preserve_index=list_index)
            messagebox.showinfo(
                "Add Time",
                f"Added 1 minute to {member.get('name', 'the prisoner')}'s sentence.",
                parent=popup,
            )

        refresh_list()
        cancel_tick["fn"] = schedule_ui_tick(popup, refresh_list)

        button_frame = tk.Frame(popup, bg="black")
        button_frame.pack(pady=10)

        pardon_btn = tk.Button(
            button_frame, text="Pardon", font=("Arial", 12), width=14, command=pardon_prisoner
        )
        pardon_btn.pack(side=tk.LEFT, padx=5)

        add_time_btn = tk.Button(
            button_frame, text="Add Time", font=("Arial", 12), width=14, command=add_time
        )
        add_time_btn.pack(side=tk.LEFT, padx=5)

        return_btn = tk.Button(
            button_frame,
            text="Return to security",
            font=("Arial", 12),
            width=18,
            command=panel.close,
        )
        return_btn.pack(side=tk.LEFT, padx=5)
