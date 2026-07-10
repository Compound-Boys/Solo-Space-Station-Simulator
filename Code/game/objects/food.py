"""Food item definitions."""

FOOD_ITEMS = {
    "snack": {
        "id": "snack",
        "name": "Snack",
        "description": "A packaged station snack from a vending machine.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
    "energy_bar": {  # From random event
        "id": "energy_bar",
        "name": "Energy Bar",
        "description": "A dense, nutrient-rich bar. Tastes like cardboard.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
    "emergency_rations": {  # From locker
        "id": "emergency_rations",
        "name": "Emergency Rations",
        "description": "Standard emergency food supply. Use only when necessary.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
}
