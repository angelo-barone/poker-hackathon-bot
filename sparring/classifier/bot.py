"""Sparring partner: After 15 hands it sorts the opponent into a type and switches to a counter-strategy."""

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

DONE = set()
C = {"fold": 0, "call": 0, "check": 0, "raise": 0, "pre_n": 0, "pre_fold": 0}


def learn(s):
    me, cur = s["your_bot_id"], s["hand_num"]
    groups = {}
    for e in s.get("match_action_log") or []:
        h = e.get("hand_num")
        if h is None or h >= cur or h in DONE:
            continue
        groups.setdefault(h, []).append(e)
    for h, entries in groups.items():
        if entries[0].get("action") not in ("ante", "small_blind"):
            continue                                        # start of the hand fell out of the log
        DONE.add(h)
        first = True
        for e in entries:
            a = e.get("action")
            if e.get("bot_id") == me or a not in ("fold", "call", "check", "raise", "all_in"):
                continue
            C["raise" if a in ("raise", "all_in") else a] += 1
            if first and e.get("street") == "preflop":
                first = False
                C["pre_n"] += 1
                C["pre_fold"] += a == "fold"


def opponent_type():
    n = C["fold"] + C["call"] + C["check"] + C["raise"]
    if len(DONE) < 15 or n < 20:
        return "unknown"
    answers = max(1, C["fold"] + C["call"] + C["raise"])
    if C["raise"] / n > 0.45:
        return "aggressive"
    if C["fold"] / answers > 0.45:
        return "folder"
    if C["call"] / answers > 0.55:
        return "caller"
    if C["pre_fold"] / max(1, C["pre_n"]) > 0.40:
        return "tight"
    return "unknown"


def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    learn(s)
    kind = opponent_type()
    pre_flop = s["street"] == "preflop"
    owed, pot, bb = s["amount_owed"], s["pot"], s["blinds"]["bb"]
    big_price = any(q["is_all_in"] for q in s["players"]) or owed >= 0.35 * s["your_stack"]

    if kind == "folder":                    # bet and raise with anything, back off when raised
        if pre_flop:
            if my_raises(s) == 0 and not big_price:
                return {"action": "raise", "amount": max(int(2.5 * bb), int(2.5 * s["current_bet"]))}
            return normal_pre(s)
        return bet(s, 0.6) if s["can_check"] else normal_post(s)

    if kind == "caller":                    # never bluff, bet every pair for full value
        if pre_flop:
            return normal_pre(s)
        m = made(s)
        if m >= 2 or (m == 1 and s["can_check"]):
            return bet(s, 1.0)
        return {"action": "call"} if m == 1 and owed <= pot - owed else passive(s)

    if kind == "aggressive":                # wait for a hand and let them bet into it
        p = pre(s["your_cards"])
        if pre_flop:
            if p >= (0.65 if big_price else 0.50):
                return cc(s)
            return passive(s)
        m = made(s)
        if m >= 2 and s["street"] == "river":
            return {"action": "all_in"}
        return cc(s) if m >= 1 else passive(s)

    if kind == "tight":                     # take the blinds, respect their bets
        if pre_flop:
            if my_raises(s) == 0 and s["current_bet"] <= bb:
                return {"action": "raise", "amount": int(2.5 * bb)}
            return normal_pre(s)
        if s["can_check"]:
            return bet(s, 0.5) if (s["street"] == "flop" or made(s) >= 1) else {"action": "check"}
        return {"action": "call"} if tpgk(s) else {"action": "fold"}

    return normal_pre(s) if pre_flop else normal_post(s)
