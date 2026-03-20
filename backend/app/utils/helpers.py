def action_to_string(action_id: int) -> str:
    mapping = {
        0: "call API",
        1: "retry",
        2: "skip",
        3: "switch API"
    }
    return mapping.get(action_id, "unknown")
