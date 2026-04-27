ABILITY_MAP = {
    "basic_collision": "state_management",
    "food_generation": "logic_planning",
    "speed_control": "timing_control",
    "obstacle_handling": "complex_rule_integration",
    "enemy_ai": "agent_behavior_modeling",
}


def map_features_to_abilities(feature_list: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for feature in feature_list:
        ability = ABILITY_MAP.get(feature, "unknown")
        result.setdefault(ability, []).append(feature)
    return result
