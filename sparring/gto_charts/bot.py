"""Sparring partner: what a poker-savvy upper-year would build.

Preflop: ranges by stack depth (open, re-raise, call, shove), read from a
hand ranking. Short stacks play all-in or fold close to the equilibrium
frequencies. After the flop: bets with strong hands plus a fixed share of
bluffs, and defends against bets often enough that bluffing it does not pay.
It does not track or adapt to its opponent.
"""

import random

import eval7

ORDER = ("AA KK QQ JJ TT 99 88 AKs AQs 77 AJs AKo ATs AQo AJo KQs 66 A9s ATo KJs A8s KTs KQo A7s "
         "A9o KJo 55 QJs K9s A5s A8o A6s KTo QTs A4s A7o K8s A3s QJo K9o A6o A5o Q9s JTs K7s QTo "
         "A2s 44 A4o K6s K8o Q8s A3o K5s J9s Q9o JTo K7o A2o K4s K6o Q7s T9s K3s J8s 33 Q6s Q8o "
         "K5o J9o K2s Q5s J7s K4o T8s Q4s Q7o J8o T9o K3o Q6o Q3s J6s T7s 98s K2o 22 Q2s Q5o J5s "
         "T8o J7o 97s Q4o J4s T6s J3s Q3o 98o 87s T7o J6o 96s T5s Q2o J2s J5o T4s 97o 86s J4o T6o "
         "T3s 95s 76s J3o 87o T2s 85s 96o J2o T5o 94s 75s T4o 93s 86o 65s 95o 84s T3o 92s 76o 74s "
         "T2o 85o 54s 64s 83s 94o 75o 82s 73s 65o 93o 53s 63s 84o 92o 74o 43s 72s 54o 64o 52s 62s "
         "83o 82o 42s 73o 53o 63o 32s 43o 72o 52o 62o 42o 32o").split()
RANKS = "AKQJT98765432"

# PCT[hand] = share of all hands that are at least as strong (0.005 for AA ... 1.0 for 32o)
PCT, _seen = {}, 0
for _h in ORDER:
    _seen += 6 if len(_h) == 2 else (4 if _h[2] == "s" else 12)
    PCT[_h] = _seen / 1326.0

# all-in-or-fold frequencies by stack depth in big blinds: (max depth, shove top, call top)
SHORT = [(3, 0.85, 0.80), (5, 0.72, 0.60), (7, 0.65, 0.48), (9, 0.60, 0.40), (11, 0.55, 0.35),
         (13, 0.50, 0.31)]


def pct(cards):
    r1, r2 = sorted((cards[0][0], cards[1][0]), key=RANKS.index)
    name = r1 + r2 if r1 == r2 else r1 + r2 + ("s" if cards[0][1] == cards[1][1] else "o")
    return PCT[name]


def equity(s, n=250):
    known = s["your_cards"] + s["community_cards"]
    deck = [eval7.Card(r + u) for r in RANKS for u in "shdc" if r + u not in known]
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


def preflop(s):
    bb = s["blinds"]["bb"]
    p = pct(s["your_cards"])
    owed = s["amount_owed"]
    totals = [q["stack"] + q["bet_this_street"] for q in s["players"]]
    depth = min(totals) / max(1, bb)
    raises = [a for a in s["action_log"] if a["action"] in ("raise", "all_in")]
    mine = sum(1 for a in raises if a["bot_id"] == s["your_bot_id"])
    theirs = len(raises) - mine
    facing_all_in = any(q["is_all_in"] for q in s["players"]) or owed >= 0.4 * s["your_stack"]

    if depth <= 13:                                      # all-in or fold
        shove, call = next((sh, ca) for d, sh, ca in SHORT if depth <= d)
        if theirs:
            return {"action": "all_in"} if p <= call else {"action": "fold"}
        return {"action": "all_in"} if p <= shove else passive(s)

    if depth <= 25:                                      # small raises, re-shoves
        if theirs == 0:
            if owed > 0:
                return {"action": "raise", "amount": 2 * bb} if p <= 0.70 else {"action": "fold"}
            return {"action": "all_in"} if p <= 0.25 else {"action": "check"}
        if mine == 0 and not facing_all_in:
            if p <= 0.18:
                return {"action": "all_in"}
            return {"action": "call"} if p <= 0.50 else {"action": "fold"}
        return {"action": "all_in"} if p <= 0.22 else {"action": "fold"}

    # deep stacks
    if theirs == 0:
        if owed > 0:                                     # small blind, first in
            return {"action": "raise", "amount": int(2.5 * bb)} if p <= 0.80 else {"action": "fold"}
        return {"action": "raise", "amount": int(3.5 * bb)} if p <= 0.30 else {"action": "check"}
    if facing_all_in:
        return {"action": "call"} if p <= (0.06 if depth > 40 else 0.14) else {"action": "fold"}
    if theirs == 1 and mine == 0:                        # big blind facing an open
        if p <= 0.12 or 0.50 < p <= 0.56:                # value re-raises plus a band of bluffs
            return {"action": "raise", "amount": int(3.3 * s["current_bet"])}
        return {"action": "call"} if p <= 0.68 else {"action": "fold"}
    if theirs == 1 and mine == 1:                        # we opened, they re-raised
        if p <= 0.04:
            if depth <= 50:
                return {"action": "all_in"}
            return {"action": "raise", "amount": int(2.3 * s["current_bet"])}
        return {"action": "call"} if p <= 0.32 else {"action": "fold"}
    if p <= 0.03:
        return {"action": "all_in"}
    return {"action": "call"} if p <= 0.08 else {"action": "fold"}


def decide(s):
    if s.get("type") == "warmup":
        return {"action": "check"}
    if s["street"] == "preflop":
        return preflop(s)
    eq = equity(s)
    owed, pot = s["amount_owed"], s["pot"]
    r = random.random()
    if s["can_check"]:
        if eq >= 0.68:
            return bet(s, 0.66)                          # value
        if eq <= 0.36 and r < 0.40:
            return bet(s, 0.66)                          # bluffs, about 2 for every 5 value bets
        return {"action": "check"}
    size = owed / max(1, pot - owed)                     # their bet as a share of the pot
    if eq >= 0.85 or (eq <= 0.30 and r < 0.06):
        return bet(s, 1.0)                               # raise for value, rarely as a bluff
    if eq >= 0.42 + 0.22 * min(size, 1.5):               # bigger bets need a stronger hand
        return {"action": "call"}
    return {"action": "fold"}
