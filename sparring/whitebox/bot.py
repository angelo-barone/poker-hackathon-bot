"""Sparring partner: An attacker written from the audit of our own bot: its three most exploitable habits."""

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


def tpgk(s):
    """Top pair with a good kicker (jack or better), an overpair, or anything stronger."""
    m = made(s)
    if m >= 2:
        return True
    if m == 1:
        hole = [R.index(c[0]) for c in s["your_cards"]]
        top = max(R.index(c[0]) for c in s["community_cards"])
        if hole[0] == hole[1]:
            return hole[0] > top
        return (hole[0] == top and hole[1] >= 9) or (hole[1] == top and hole[0] >= 9)
    return False


def normal_pre(s):
    """A plain, honest preflop game."""
    p = pre(s["your_cards"])
    owed, bb = s["amount_owed"], s["blinds"]["bb"]
    if any(q["is_all_in"] for q in s["players"]) or owed >= 0.35 * s["your_stack"]:
        return {"action": "call"} if p >= 0.76 else passive(s)
    if p >= 0.80:
        return {"action": "raise", "amount": max(s["min_raise_to"], 3 * s["current_bet"])}
    if s["current_bet"] <= bb and my_raises(s) == 0 and p >= 0.45:
        return {"action": "raise", "amount": int(2.5 * bb)}
    if p >= 0.35 and owed <= 4 * bb:
        return cc(s)
    return passive(s)


def normal_post(s):
    """Honest play after the flop: bet a pair or better, give up with nothing."""
    m = made(s)
    owed, pot = s["amount_owed"], s["pot"]
    if m >= 2:
        return bet(s, 0.75)
    if m == 1:
        if s["can_check"]:
            return bet(s, 0.5)
        return {"action": "call"} if owed <= 0.6 * (pot - owed) else {"action": "fold"}
    return passive(s)

SHOVED = {"count": 0}


def big_raise(s):
    """A raise to 35-45% of the opponent's stack that is not all-in, or None if that is impossible."""
    me = s["your_bot_id"]
    opp = next(q for q in s["players"] if q["bot_id"] != me)
    target = int(random.uniform(0.35, 0.45) * (opp["stack"] + opp["bet_this_street"]))
    top = s["your_stack"] + s["your_bet_this_street"] - s["blinds"]["bb"]
    amount = min(target, top)
    return {"action": "raise", "amount": amount} if amount >= s["min_raise_to"] else None


def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    me = s["your_bot_id"]
    owed, pot, bb = s["amount_owed"], s["pot"], s["blinds"]["bb"]
    if s["street"] == "preflop":
        p = pre(s["your_cards"])
        they_raised = any(a["bot_id"] != me and a["action"] in ("raise", "all_in") for a in s["action_log"])
        if any(q["is_all_in"] for q in s["players"]) or (my_raises(s) >= 1 and they_raised):
            return {"action": "call"} if p >= 0.76 else passive(s)      # they shoved back: fold most
        if they_raised:                                     # they opened
            if SHOVED["count"] < 4:                         # habit 3: shove over their first four opens
                SHOVED["count"] += 1
                return {"action": "all_in"}
            if p >= 0.55:                                   # habit 1: a huge re-raise that is not all-in
                return big_raise(s) or {"action": "all_in"}
            return {"action": "call"} if p >= 0.40 and owed <= 4 * bb else {"action": "fold"}
        if owed > 0:                                        # small blind, first in: habit 1 as an open
            if p >= 0.42:
                return big_raise(s) or {"action": "all_in"}
            return {"action": "fold"}
        return {"action": "check"}
    m = made(s)
    last_theirs = None
    for a in s["action_log"]:
        if a["bot_id"] != me and a["street"] != "preflop" and a["action"] in ("check", "call", "raise", "all_in"):
            last_theirs = a["action"]
    if s["can_check"]:
        if last_theirs == "check":                          # habit 2: overbet whenever they check
            return bet(s, random.uniform(1.1, 1.3))
        return bet(s, 0.66) if m >= 1 else {"action": "check"}
    if m >= 2:
        return bet(s, 1.0)
    return {"action": "call"} if m == 1 and owed <= pot - owed else {"action": "fold"}
