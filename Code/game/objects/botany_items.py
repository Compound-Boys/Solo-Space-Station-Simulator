"""Botany seed item definitions and growth-class timers."""

BOTANY_SEED_IDS = (
    "tomato_seeds",
    "potato_seeds",
    "wheat_seeds",
    "carrot_seeds",
    "apple_seeds",
)

GROWTH_STAGES = 5  # 1..5, mature at 5

GROWTH_CLASS_SECONDS = {
    "crop": 3 * 60,
    "fruiting": 5 * 60,
    "tree": 8 * 60,
}

GROWTH_STAGE_LABELS = {
    1: "Seedling",
    2: "Sprouting",
    3: "Growing",
    4: "Ripening",
    5: "Mature",
}

BOTANY_ITEMS = {
    "tomato_seeds": {
        "id": "tomato_seeds",
        "name": "Tomato Seeds",
        "description": "Grows into juicy red tomatoes.",
        "category": "Botany",
        "attributes": {
            "produces": "tomato",
            "plant_name": "Tomato",
            "growth_class": "fruiting",
        },
        "actions": ["examine", "drop"],
    },
    "potato_seeds": {
        "id": "potato_seeds",
        "name": "Potato Seeds",
        "description": "Produces starchy potatoes.",
        "category": "Botany",
        "attributes": {
            "produces": "potato",
            "plant_name": "Potato",
            "growth_class": "crop",
        },
        "actions": ["examine", "drop"],
    },
    "wheat_seeds": {
        "id": "wheat_seeds",
        "name": "Wheat Seeds",
        "description": "Grows into tall wheat stalks.",
        "category": "Botany",
        "attributes": {
            "produces": "wheat",
            "plant_name": "Wheat",
            "growth_class": "crop",
        },
        "actions": ["examine", "drop"],
    },
    "carrot_seeds": {
        "id": "carrot_seeds",
        "name": "Carrot Seeds",
        "description": "Produces orange root vegetables.",
        "category": "Botany",
        "attributes": {
            "produces": "carrot",
            "plant_name": "Carrot",
            "growth_class": "crop",
        },
        "actions": ["examine", "drop"],
    },
    "apple_seeds": {
        "id": "apple_seeds",
        "name": "Apple Seeds",
        "description": "Grows into small apple trees.",
        "category": "Botany",
        "attributes": {
            "produces": "apple",
            "plant_name": "Apple",
            "growth_class": "tree",
        },
        "actions": ["examine", "drop"],
    },
}


def growth_duration_seconds(growth_class):
    """Return seconds per stage advance for a growth class (defaults to crop)."""
    return GROWTH_CLASS_SECONDS.get(growth_class, GROWTH_CLASS_SECONDS["crop"])


def compute_growth_stage(planted_at_seconds, growth_class, elapsed_seconds):
    """Return growth stage 1..5 from planted time vs master clock.

    GROWTH_CLASS_SECONDS is time spent on each stage before advancing.
    Mature (stage 5) after (GROWTH_STAGES - 1) intervals.
    """
    if planted_at_seconds is None:
        return 1
    stage_len = growth_duration_seconds(growth_class)
    if stage_len <= 0:
        return GROWTH_STAGES
    elapsed = max(0.0, float(elapsed_seconds) - float(planted_at_seconds))
    return min(GROWTH_STAGES, 1 + int(elapsed / stage_len))


def growth_stage_label(stage):
    """Display label for a growth stage."""
    try:
        stage = int(stage)
    except (TypeError, ValueError):
        stage = 1
    return GROWTH_STAGE_LABELS.get(stage, "Growing")


def growth_seconds_remaining(planted_at_seconds, growth_class, elapsed_seconds):
    """Seconds until mature, or 0 if already mature / missing data."""
    if planted_at_seconds is None:
        return 0
    stage_len = growth_duration_seconds(growth_class)
    total = stage_len * (GROWTH_STAGES - 1)
    elapsed = max(0.0, float(elapsed_seconds) - float(planted_at_seconds))
    return max(0, int(total - elapsed))


def growth_seconds_to_next_stage(planted_at_seconds, growth_class, elapsed_seconds):
    """Seconds until the next stage advance, or 0 if mature / missing data."""
    if planted_at_seconds is None:
        return 0
    stage = compute_growth_stage(planted_at_seconds, growth_class, elapsed_seconds)
    if stage >= GROWTH_STAGES:
        return 0
    stage_len = growth_duration_seconds(growth_class)
    if stage_len <= 0:
        return 0
    elapsed = max(0.0, float(elapsed_seconds) - float(planted_at_seconds))
    next_at = stage * stage_len
    return max(0, int(next_at - elapsed))


def refresh_planter_growth(planter, elapsed_seconds):
    """Update an occupied planter's cached growth_stage from the game clock.

    Returns the current stage (0 if empty).
    """
    if not planter or not planter.get("occupied"):
        return 0
    stage = compute_growth_stage(
        planter.get("planted_at_seconds"),
        planter.get("growth_class"),
        elapsed_seconds,
    )
    planter["growth_stage"] = stage
    return stage


def refresh_all_planters_growth(player_data, elapsed_seconds=None):
    """Refresh growth_stage on all botany planters. Returns the planters list."""
    from game.helper_methods.game_clock import get_elapsed_seconds

    if elapsed_seconds is None:
        elapsed_seconds = get_elapsed_seconds(player_data)
    botany = player_data.get("botany") or {}
    planters = botany.get("planters") or []
    for planter in planters:
        refresh_planter_growth(planter, elapsed_seconds)
    return planters
