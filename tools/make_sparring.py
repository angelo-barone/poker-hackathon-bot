"""Writes the sparring field into sparring/<name>/bot.py.

Each bot is a short, honest version of what a student team might submit.
They share a few helper lines (HELPERS), pasted into every file so each bot
stands alone, exactly like a real entry.

  python tools/make_sparring.py
"""

import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HELPERS = '''
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
'''

BOTS = {}

BOTS["random"] = ('Picks any legal action at random, with random raise sizes.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    r = random.random()
    if r < 0.05:
        return {"action": "all_in"}
    if r < 0.35:
        return passive(s)
    if r < 0.70:
        return cc(s)
    top = s["your_stack"] + s["your_bet_this_street"]
    lo = min(s["min_raise_to"], top)
    return {"action": "raise", "amount": random.randint(lo, max(lo, int(lo + (top - lo) * random.random() ** 3)))}
''')

BOTS["minraiser"] = ('Min-raises whenever it can, calls otherwise.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    if s["your_stack"] > s["amount_owed"]:
        return {"action": "raise", "amount": s["min_raise_to"]}
    return cc(s)
''')

BOTS["potbettor"] = ('Bets or raises the size of the pot every time.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    return bet(s, 1.0)
''')

BOTS["nit"] = ('Only plays premium hands, folds the rest.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    if s["street"] == "preflop":
        if pre(s["your_cards"]) >= 0.76:                    # 88+, AK, AQs
            return {"action": "raise", "amount": max(s["min_raise_to"], 3 * s["current_bet"])}
        return passive(s)
    m = made(s)
    if m >= 2:
        return bet(s, 1.0)
    if m == 1:
        if s["can_check"]:
            return bet(s, 0.5)
        return {"action": "call"} if s["amount_owed"] <= 0.5 * s["pot"] else {"action": "fold"}
    return passive(s)
''')

BOTS["potodds"] = ('Plain Monte Carlo equity against pot odds. No opponent tracking, no short-stack tables.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    eq = equity(s)
    owed, pot = s["amount_owed"], s["pot"]
    if eq > 0.65:
        return bet(s, 0.75)
    if owed == 0:
        return bet(s, 0.5) if eq > 0.55 else {"action": "check"}
    return {"action": "call"} if eq > owed / (pot + owed) else {"action": "fold"}
''')

BOTS["chartbot"] = ('Preflop hand chart, then bets by made-hand strength (pair, two pair, ...).', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    owed, pot, bb = s["amount_owed"], s["pot"], s["blinds"]["bb"]
    if s["street"] == "preflop":
        p = pre(s["your_cards"])
        if p >= 0.76:
            if owed >= 0.5 * s["your_stack"]:
                return {"action": "call"}
            return {"action": "raise", "amount": max(s["min_raise_to"], 3 * s["current_bet"])}
        if p >= 0.45:
            if s["current_bet"] <= bb and my_raises(s) == 0:
                return {"action": "raise", "amount": int(2.5 * bb)}
            return cc(s) if owed <= 4 * bb else {"action": "fold"}
        return passive(s)
    m = made(s)
    if m >= 2:
        return bet(s, 1.0)
    if m == 1:
        if s["can_check"]:
            return bet(s, 0.5)
        return {"action": "call"} if owed <= 0.6 * (pot - owed) else {"action": "fold"}
    return passive(s)
''')

BOTS["nashpush"] = ('All-in or fold from a chart, at every stack size.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    if s["street"] != "preflop":
        return {"action": "all_in"} if made(s) >= 1 else passive(s)
    depth = eff_bb(s)
    need = 0.38 if depth <= 10 else (0.48 if depth <= 20 else (0.62 if depth <= 50 else 0.74))
    p = pre(s["your_cards"])
    if s["current_bet"] > s["blinds"]["bb"]:                # facing a raise or a shove
        return {"action": "all_in"} if p >= need + 0.08 else {"action": "fold"}
    return {"action": "all_in"} if p >= need else passive(s)
''')

BOTS["maniac"] = ('Raises or bets big most of the time, not always all-in.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    r = random.random()
    if r < 0.70:
        return bet(s, random.uniform(0.75, 1.5))
    if r < 0.95:
        return cc(s)
    return passive(s)
''')

BOTS["bluffer"] = ('Bets big after the flop with weak hands (chasing the bluff prize).', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    owed, bb = s["amount_owed"], s["blinds"]["bb"]
    if s["street"] == "preflop":
        p = pre(s["your_cards"])
        if s["current_bet"] <= bb and p >= 0.45:
            return {"action": "raise", "amount": int(2.5 * bb)}
        if owed <= 3 * bb or p >= 0.70:
            return cc(s)
        return {"action": "fold"}
    m = made(s)
    if m == 0:
        if s["can_check"]:
            return bet(s, random.uniform(1.0, 1.5)) if random.random() < 0.75 else {"action": "check"}
        return bet(s, 1.2) if random.random() < 0.25 else {"action": "fold"}
    if m >= 2 and owed > 0:
        return bet(s, 1.0)
    if s["can_check"]:
        return bet(s, 0.33) if random.random() < 0.5 else {"action": "check"}
    return {"action": "call"}
''')

BOTS["threebettor"] = ('Re-raises almost every time the opponent opens.', '''
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
''')

BOTS["stealer"] = ('Raises every hand preflop, gives up when it meets resistance.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    bb = s["blinds"]["bb"]
    if s["street"] == "preflop":
        if my_raises(s) == 0:
            return {"action": "raise", "amount": max(int(2.5 * bb), int(2.5 * s["current_bet"]))}
        p = pre(s["your_cards"])
        if p >= 0.85:
            return {"action": "all_in"}
        return {"action": "call"} if p >= 0.76 else passive(s)
    m = made(s)
    if s["street"] == "flop" and s["can_check"]:
        return bet(s, 0.5)
    if m >= 1:
        return bet(s, 0.5) if s["can_check"] else {"action": "call"}
    return passive(s)
''')

BOTS["trapper"] = ('Checks and calls with strong hands, then raises big on the river.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    owed, pot, bb = s["amount_owed"], s["pot"], s["blinds"]["bb"]
    if s["street"] == "preflop":
        p = pre(s["your_cards"])
        if p >= 0.85:
            return {"action": "raise", "amount": max(s["min_raise_to"], 3 * s["current_bet"])}
        if p >= 0.30 and owed <= 5 * bb:
            return cc(s)
        return passive(s)
    m = made(s)
    if m >= 2:
        if s["street"] == "river":
            return bet(s, 1.2 if s["can_check"] else 1.5)
        return cc(s)
    if m == 1:
        return cc(s) if owed <= 0.5 * (pot - owed) else {"action": "fold"}
    return passive(s)
''')

BOTS["oddsizer"] = ('Tiny bets and huge overbets, to test how the opponent reads bet sizes.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    owed, pot = s["amount_owed"], s["pot"]
    strong = pre(s["your_cards"]) >= 0.60 if s["street"] == "preflop" else made(s) >= 1
    r = random.random()
    if s["can_check"]:
        if r < 0.65:
            huge = random.random() < (0.5 if strong else 0.15)
            return bet(s, 2.5) if huge else {"action": "raise", "amount": s["min_raise_to"]}
        return {"action": "check"}
    if strong:
        return bet(s, 2.5) if r < 0.3 else {"action": "call"}
    return {"action": "call"} if owed <= 0.25 * (pot - owed) else {"action": "fold"}
''')

BOTS["lateshover"] = ('Tight early, then shoves wide once the blinds are high.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    owed, bb = s["amount_owed"], s["blinds"]["bb"]
    p = pre(s["your_cards"])
    if bb >= 300 or eff_bb(s) <= 15:
        if s["street"] != "preflop":
            return {"action": "all_in"} if made(s) >= 1 else passive(s)
        if s["current_bet"] > bb:
            return {"action": "all_in"} if p >= 0.50 else {"action": "fold"}
        return {"action": "all_in"} if p >= 0.40 else passive(s)
    if s["street"] == "preflop":
        if p >= 0.76:
            return {"action": "raise", "amount": max(s["min_raise_to"], 3 * s["current_bet"])}
        if p >= 0.50 and owed <= 3 * bb:
            return cc(s)
        return passive(s)
    if made(s) >= 1:
        if s["can_check"]:
            return bet(s, 0.5)
        return {"action": "call"} if owed <= 0.5 * s["pot"] else {"action": "fold"}
    return passive(s)
''')

BOTS["smallbet_trap"] = ('Bets a third of the pot on every street, shoves only with two pair or better.', '''
def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    owed, pot, bb = s["amount_owed"], s["pot"], s["blinds"]["bb"]
    if s["street"] == "preflop":
        if any(p["is_all_in"] for p in s["players"]) or owed >= 0.35 * s["your_stack"]:
            return {"action": "call"} if pre(s["your_cards"]) >= 0.76 else {"action": "fold"}
        if my_raises(s) == 0 and s["current_bet"] <= bb:
            return {"action": "raise", "amount": 2 * bb}
        return cc(s)
    if made(s) >= 2:
        return {"action": "all_in"}
    if s["can_check"]:
        return bet(s, 0.33)
    return {"action": "call"} if owed <= 0.5 * (pot - owed) else {"action": "fold"}
''')

BOTS["adaptive"] = ('Tracks how often the opponent folds and bluffs more when they fold a lot.', '''
SEEN, FOLDED = set(), set()


def fold_rate(s):
    for e in s.get("match_action_log") or []:
        if e.get("bot_id") != s["your_bot_id"]:
            SEEN.add(e["hand_num"])
            if e.get("action") == "fold":
                FOLDED.add(e["hand_num"])
    return (len(FOLDED) + 2) / (len(SEEN) + 6)


def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    rate = fold_rate(s)
    owed, pot, bb = s["amount_owed"], s["pot"], s["blinds"]["bb"]
    r = random.random()
    if s["street"] == "preflop":
        p = pre(s["your_cards"])
        if p >= 0.60 or (my_raises(s) == 0 and r < rate * 1.5):
            if my_raises(s) >= 2:
                return cc(s)
            return {"action": "raise", "amount": max(int(2.5 * bb), int(2.8 * s["current_bet"]))}
        if p >= 0.40 and owed <= 4 * bb:
            return cc(s)
        return passive(s)
    eq = equity(s, 200)
    if eq > 0.60:
        return bet(s, 0.7)
    if s["can_check"]:
        return bet(s, 0.75) if (eq < 0.5 and r < min(0.85, rate * 1.5)) else {"action": "check"}
    if eq > owed / (pot + owed):
        return {"action": "call"}
    if rate > 0.5 and r < 0.25:
        return bet(s, 1.0)
    return {"action": "fold"}
''')


def main():
    base = os.path.join(ROOT, "sparring")
    for name, (doc, body) in BOTS.items():
        folder = os.path.join(base, name)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "bot.py"), "w", newline="\n") as f:
            f.write('"""Sparring partner: ' + doc + '"""\n' + HELPERS + "\n" + body)
    # the benchmark every new version must beat: an untouched copy of v1
    frozen = os.path.join(base, "v1_frozen")
    if not os.path.isdir(frozen):
        shutil.copytree(os.path.join(ROOT, "my_bots", "im_just_in_mech_eng"), frozen,
                        ignore=shutil.ignore_patterns("__pycache__"))
    print("wrote", len(BOTS), "bots to sparring/ (+ v1_frozen)")


if __name__ == "__main__":
    main()
