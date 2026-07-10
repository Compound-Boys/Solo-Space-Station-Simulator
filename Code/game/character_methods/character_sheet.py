import tkinter as tk

from game.objects.items import inventory_item_count


def render_character_sheet(
    parent,
    player_data,
    *,
    on_inventory,
    on_holdings,
    on_notes,
    show_title=True,
):
    """Build character sheet widgets into parent. Returns the info frame."""
    if show_title:
        title_label = tk.Label(
            parent, text="Character Sheet", font=("Arial", 24), bg="black", fg="white"
        )
        title_label.pack(pady=20)

    info_frame = tk.Frame(parent, bg="black")
    info_frame.pack(pady=10)

    name_label = tk.Label(
        info_frame,
        text=f"Name: {player_data['name']}",
        font=("Arial", 14),
        bg="black",
        fg="white",
    )
    name_label.pack(anchor="w", padx=10, pady=5)

    job_label = tk.Label(
        info_frame,
        text=f"Job: {player_data['job']}",
        font=("Arial", 14),
        bg="black",
        fg="white",
    )
    job_label.pack(anchor="w", padx=10, pady=5)

    department = player_data.get("department", "Unknown")
    department_label = tk.Label(
        info_frame,
        text=f"Department: {department}",
        font=("Arial", 14),
        bg="black",
        fg="white",
    )
    department_label.pack(anchor="w", padx=10, pady=5)

    credits_label = tk.Label(
        info_frame,
        text=f"Credits: {player_data['credits']:.2f}",
        font=("Arial", 14),
        bg="black",
        fg="white",
    )
    credits_label.pack(anchor="w", padx=10, pady=5)

    alcohol_value = player_data.setdefault("alcohol_percent", 0)
    alcohol_color = (
        "green" if alcohol_value < 10
        else "yellow" if alcohol_value < 30
        else "orange" if alcohol_value < 60
        else "red"
    )
    alcohol_label = tk.Label(
        info_frame,
        text=f"Alcohol: {alcohol_value:.1f}%",
        font=("Arial", 14),
        bg="black",
        fg=alcohol_color,
    )
    alcohol_label.pack(anchor="w", padx=10, pady=5)

    if alcohol_value >= 25:
        alcohol_hint = tk.Label(
            info_frame,
            text="Seek medical treatment to sober up.",
            font=("Arial", 11),
            bg="black",
            fg="orange",
        )
        alcohol_hint.pack(anchor="w", padx=10, pady=(0, 5))

    button_frame = tk.Frame(info_frame, bg="black")
    button_frame.pack(anchor="w", padx=10, pady=5, fill=tk.X)

    inv_count = inventory_item_count(player_data)
    inv_btn = tk.Button(
        button_frame,
        text=f"View Inventory ({inv_count} items)",
        font=("Arial", 12),
        width=20,
        command=on_inventory,
    )
    inv_btn.pack(side=tk.LEFT, padx=5, pady=5)

    holdings_count = len(player_data.get("stock_holdings", {}))
    stock_btn = tk.Button(
        button_frame,
        text=f"View Stock Holdings ({holdings_count})",
        font=("Arial", 12),
        width=20,
        command=on_holdings,
    )
    stock_btn.pack(side=tk.LEFT, padx=5, pady=5)

    notes_count = len(player_data.get("notes", []))
    notes_btn = tk.Button(
        button_frame,
        text=f"View Notes ({notes_count})",
        font=("Arial", 12),
        width=15,
        command=on_notes,
    )
    notes_btn.pack(side=tk.LEFT, padx=5, pady=5)

    damage_label = tk.Label(
        info_frame, text="Overall Damage:", font=("Arial", 14), bg="black", fg="white"
    )
    damage_label.pack(anchor="w", padx=10, pady=5)

    damage_frame = tk.Frame(info_frame, bg="black")
    damage_frame.pack(fill=tk.X, padx=20, pady=5)

    damage_types = [
        {"name": "Burn", "key": "burn"},
        {"name": "Poison", "key": "poison"},
        {"name": "Oxygen", "key": "oxygen"},
    ]

    for damage_type in damage_types:
        damage_value = player_data["damage"].get(damage_type["key"], 0)

        color = (
            "green"
            if damage_value < 10
            else "yellow"
            if damage_value < 30
            else "orange"
            if damage_value < 60
            else "red"
        )

        type_frame = tk.Frame(damage_frame, bg="black")
        type_frame.pack(anchor="w", fill=tk.X, pady=2)

        type_label = tk.Label(
            type_frame,
            text=f"{damage_type['name']}:",
            font=("Arial", 12),
            bg="black",
            fg="white",
            width=10,
            anchor="w",
        )
        type_label.grid(row=0, column=0, sticky="w", padx=(5, 0))

        value_label = tk.Label(
            type_frame,
            text=f"{damage_value:.1f}%",
            font=("Arial", 12),
            bg="black",
            fg=color,
        )
        value_label.grid(row=0, column=1, sticky="w")

        if damage_value >= 30:
            effect_text = (
                "Severe"
                if damage_value >= 70
                else "Moderate"
                if damage_value >= 50
                else "Mild"
            )
            effect_label = tk.Label(
                type_frame,
                text=f" - {effect_text} effects",
                font=("Arial", 12, "italic"),
                bg="black",
                fg=color,
            )
            effect_label.grid(row=0, column=2, sticky="w", padx=5)

    limb_label = tk.Label(
        info_frame,
        text="Limb Health (Blunt Damage):",
        font=("Arial", 14),
        bg="black",
        fg="white",
    )
    limb_label.pack(anchor="w", padx=10, pady=5)

    limb_container = tk.Frame(info_frame, bg="black")
    limb_container.pack(fill=tk.X, padx=20, pady=5)
    for col in range(3):
        limb_container.columnconfigure(col, weight=1)

    limb_order = ["head", "chest", "left_arm", "right_arm", "left_leg", "right_leg"]

    for index, limb_name in enumerate(limb_order):
        if limb_name not in player_data["limbs"]:
            continue
        health = player_data["limbs"][limb_name]
        display_name = limb_name.replace("_", " ").title()
        color = "green" if health > 75 else "yellow" if health > 40 else "red"

        limb_health_label = tk.Label(
            limb_container,
            text=f"{display_name}: {health}%",
            font=("Arial", 12),
            bg="black",
            fg=color,
            anchor="center",
        )
        limb_health_label.grid(
            row=index // 3,
            column=index % 3,
            sticky="ew",
            pady=2,
        )

    limb_health = sum(player_data["limbs"].values()) / len(player_data["limbs"])
    damage_health = 100 - (
        sum(player_data["damage"].values()) / len(player_data["damage"])
    )

    def _health_color(value):
        return "green" if value > 75 else "yellow" if value > 40 else "red"

    totals_frame = tk.Frame(info_frame, bg="black")
    totals_frame.pack(anchor="w", fill=tk.X, padx=10, pady=5)

    non_limb_col = tk.Frame(totals_frame, bg="black")
    non_limb_col.pack(side=tk.LEFT, padx=(0, 40))

    non_limb_label = tk.Label(
        non_limb_col,
        text="Non-Limb Health:",
        font=("Arial", 14),
        bg="black",
        fg="white",
    )
    non_limb_label.pack(anchor="w")

    non_limb_health_label = tk.Label(
        non_limb_col,
        text=f"{damage_health:.1f}%",
        font=("Arial", 16, "bold"),
        bg="black",
        fg=_health_color(damage_health),
    )
    non_limb_health_label.pack(anchor="w", pady=5)

    limb_col = tk.Frame(totals_frame, bg="black")
    limb_col.pack(side=tk.LEFT)

    limb_total_label = tk.Label(
        limb_col,
        text="Limb Health:",
        font=("Arial", 14),
        bg="black",
        fg="white",
    )
    limb_total_label.pack(anchor="w")

    limb_health_total_label = tk.Label(
        limb_col,
        text=f"{limb_health:.1f}%",
        font=("Arial", 16, "bold"),
        bg="black",
        fg=_health_color(limb_health),
    )
    limb_health_total_label.pack(anchor="w", pady=5)

    return info_frame
