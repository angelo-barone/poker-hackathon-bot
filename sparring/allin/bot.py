"""Sparring partner: goes all-in every time it acts."""


def decide(game_state: dict) -> dict:
    if game_state.get("type") == "warmup":
        return {"action": "check"}
    return {"action": "all_in"}
