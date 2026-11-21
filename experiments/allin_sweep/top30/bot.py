"""Experiment bot: gets all-in with the top 30% of starting hands, folds the rest."""

RANKS = "AKQJT98765432"
PLAY = ['44', '55', '66', '77', '88', '99', 'A2s', 'A3o', 'A3s', 'A4o', 'A4s', 'A5o', 'A5s', 'A6o', 'A6s', 'A7o', 'A7s', 'A8o', 'A8s', 'A9o', 'A9s', 'AA', 'AJo', 'AJs', 'AKo', 'AKs', 'AQo', 'AQs', 'ATo', 'ATs', 'J9s', 'JJ', 'JTs', 'K5s', 'K6s', 'K7s', 'K8o', 'K8s', 'K9o', 'K9s', 'KJo', 'KJs', 'KK', 'KQo', 'KQs', 'KTo', 'KTs', 'Q8s', 'Q9s', 'QJo', 'QJs', 'QQ', 'QTo', 'QTs', 'TT']


def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    a, b = s["your_cards"]
    r1, r2 = sorted((a[0], b[0]), key=RANKS.index)
    name = r1 + r2 if r1 == r2 else r1 + r2 + ("s" if a[1] == b[1] else "o")
    if name in PLAY:
        return {"action": "call"} if s["amount_owed"] >= s["your_stack"] or any(
            p["is_all_in"] for p in s["players"]) else {"action": "all_in"}
    return {"action": "check"} if s["can_check"] else {"action": "fold"}
