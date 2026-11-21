"""Sparring partner: Re-raises almost every time the opponent opens."""

import random

import eval7

R = "23456789TJQKA"


def pre(c):
    """Rough preflop strength, 0..1 (AA = 1.0, 72o = 0.19)."""
    a, b = sorted((R.index(c[0][0]), R.index(c[1][0])), reverse=True)
    if a == b:
        return 0.55 + 0.45 * a / 12
    s = (2 * a + b) / 36 * 0.7
    if c[0][1] == c[1][1]:
        s += 0.06
    if a - b == 1:
        s += 0.03
    if a == 12:
        s += 0.05
    return s


def made(s):
    """0 high card, 1 pair, 2 two pair, 3 trips, 4 straight, 5 flush, 6 full house, 7 quads."""
    return eval7.evaluate([eval7.Card(x) for x in s["your_cards"] + s["community_cards"]]) >> 24


def equity(s, n=250):
    """Monte Carlo chance of beating one random hand."""
    known = s["your_cards"] + s["community_cards"]
    deck = [eval7.Card(r + u) for r in R for u in "shdc" if r + u not in known]
    hole = [eval7.Card(x) for x in s["your_cards"]]
    board = [eval7.Card(x) for x in s["community_cards"]]
    need = 5 - len(board)
    win = 0.0
    for _ in range(n):
        d = random.sample(deck, 2 + need)
        a = eval7.evaluate(hole + board + d[2:])
        b = eval7.evaluate(d[:2] + board + d[2:])
        win += 1 if a > b else (0.5 if a == b else 0)
    return win / n


def bet(s, frac):
    return {"action": "raise", "amount": max(s["min_raise_to"], int(s["current_bet"] + frac * s["pot"]))}


def passive(s):
    return {"action": "check"} if s["can_check"] else {"action": "fold"}


def cc(s):
    return {"action": "check"} if s["can_check"] else {"action": "call"}


def my_raises(s):
    return sum(1 for a in s["action_log"] if a["bot_id"] == s["your_bot_id"]
               and a["street"] == s["street"] and a["action"] in ("raise", "all_in"))


def eff_bb(s):
    totals = [p["stack"] + p["bet_this_street"] for p in s["players"]]
    return min(totals) / max(1, s["blinds"]["bb"])


def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    bb = s["blinds"]["bb"]
    if s["street"] == "preflop":
        p = pre(s["your_cards"])
        if s["current_bet"] > bb:                           # facing a raise
            if my_raises(s) == 0:
                if random.random() < 0.90:
                    return {"action": "raise", "amount": 3 * s["current_bet"]}
                return {"action": "call"}
            if p >= 0.85:
                return {"action": "all_in"}
            return {"action": "call"} if p >= 0.70 else {"action": "fold"}
        if s["amount_owed"] > 0:
            return {"action": "raise", "amount": 2 * bb} if random.random() < 0.6 else {"action": "call"}
        return {"action": "check"}
    if s["street"] == "flop" and s["can_check"]:
        return bet(s, 0.66)
    if made(s) >= 1:
        return bet(s, 0.5) if s["can_check"] else {"action": "call"}
    return passive(s)
