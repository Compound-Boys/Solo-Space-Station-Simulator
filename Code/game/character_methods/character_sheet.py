import tkinter as tk


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

    button_frame = tk.Frame(info_frame, bg="black")
    button_frame.pack(anchor="w", padx=10, pady=5, fill=tk.X)

    inv_count = len(player_data.get("inventory", []))
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
        {"name": "Burn", "key": "burn", "icon": "🔥"},
        {"name": "Poison", "key": "poison", "icon": "☣️"},
        {"name": "Oxygen", "key": "oxygen", "icon": "💨"},
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
            text=f"{damage_type['icon']} {damage_type['name']}: ",
            font=("Arial", 12),
            bg="black",
            fg="white",
        )
        type_label.pack(side=tk.LEFT, padx=5)

        value_label = tk.Label(
            type_frame,
            text=f"{damage_value:.1f}%",
            font=("Arial", 12),
            bg="black",
            fg=color,
        )
        value_label.pack(side=tk.LEFT)

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
            effect_label.pack(side=tk.LEFT, padx=5)

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

    row1_frame = tk.Frame(limb_container, bg="black")
    row1_frame.pack(fill=tk.X, pady=2)

    row2_frame = tk.Frame(limb_container, bg="black")
    row2_frame.pack(fill=tk.X, pady=2)

    limb_order = ["head", "chest", "left_arm", "right_arm", "left_leg", "right_leg"]

    for limb_name in limb_order[:3]:
        if limb_name in player_data["limbs"]:
            health = player_data["limbs"][limb_name]
            display_name = limb_name.replace("_", " ").title()
            color = "green" if health > 75 else "yellow" if health > 40 else "red"

            cell = tk.Frame(row1_frame, bg="black", width=200)
            cell.pack(side=tk.LEFT, padx=10, expand=True)

            limb_health_label = tk.Label(
                cell,
                text=f"{display_name}: {health}%",
                font=("Arial", 12),
                bg="black",
                fg=color,
            )
            limb_health_label.pack(side=tk.LEFT)

    for limb_name in limb_order[3:]:
        if limb_name in player_data["limbs"]:
            health = player_data["limbs"][limb_name]
            display_name = limb_name.replace("_", " ").title()
            color = "green" if health > 75 else "yellow" if health > 40 else "red"

            cell = tk.Frame(row2_frame, bg="black", width=200)
            cell.pack(side=tk.LEFT, padx=10, expand=True)

            limb_health_label = tk.Label(
                cell,
                text=f"{display_name}: {health}%",
                font=("Arial", 12),
                bg="black",
                fg=color,
            )
            limb_health_label.pack(side=tk.LEFT)

    limb_health = sum(player_data["limbs"].values()) / len(player_data["limbs"])
    damage_health = 100 - (
        sum(player_data["damage"].values()) / len(player_data["damage"])
    )

    def _health_color(value):
        return "green" if value > 75 else "yellow" if value > 40 else "red"

    non_limb_label = tk.Label(
        info_frame,
        text="Non-Limb Health:",
        font=("Arial", 14),
        bg="black",
        fg="white",
    )
    non_limb_label.pack(anchor="w", padx=10, pady=5)

    non_limb_health_label = tk.Label(
        info_frame,
        text=f"{damage_health:.1f}%",
        font=("Arial", 16, "bold"),
        bg="black",
        fg=_health_color(damage_health),
    )
    non_limb_health_label.pack(anchor="w", padx=10, pady=5)

    limb_total_label = tk.Label(
        info_frame,
        text="Limb Health:",
        font=("Arial", 14),
        bg="black",
        fg="white",
    )
    limb_total_label.pack(anchor="w", padx=10, pady=5)

    limb_health_total_label = tk.Label(
        info_frame,
        text=f"{limb_health:.1f}%",
        font=("Arial", 16, "bold"),
        bg="black",
        fg=_health_color(limb_health),
    )
    limb_health_total_label.pack(anchor="w", padx=10, pady=5)

    return info_frame
