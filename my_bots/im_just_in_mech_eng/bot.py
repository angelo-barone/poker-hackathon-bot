"""
Team im_just_in_mech_eng (bot version v2): heads-up No-Limit Hold'em tournament bot.

How it works, in plain words:

  1. SAFETY WRAPPER (decide, _legal). Every decision runs inside a try/except
     and its answer is checked against the rules before it is returned, so a
     bug can only ever produce a check or a fold, never a crash or an illegal
     move.
  2. PREFLOP TABLES (data/preflop.json, built offline by tools/build_preflop.py).
     For all 169 starting hands we know how often each one beats each other
     one. From that we get the equity of our hand against "the top X% of
     hands", and the all-in-or-fold ranges for short stacks.
  3. OPPONENT COUNTERS (_digest, _replay). Every time the opponent could bet,
     we count whether they did, and whether it was a normal bet or an overbet
     or shove. Counts are blended with a starting guess, so one or two hands
     never swing us.
  4. READING BETS (_looseness, _read_bets). A bet tells us more the less often
     that opponent makes it. Before we have evidence we assume a normal mix of
     strong hands and bluffs and continue often enough that bluffing us does
     not pay. Opponents who bet almost always get called by the price alone;
     opponents who rarely bet, and rare big bets, get credit for strong hands.
  5. POSTFLOP EQUITY (_equity). We deal the unknown cards many times and count
     how often we win, giving the opponent the best of several random hands:
     few when their betting says little, many when it says a lot.
  6. DECISION RULE. Compare equity to the price of continuing (pot odds):
     fold when it is too expensive, call when it is fair, bet or raise when we
     are well ahead. Putting a deep stack in needs a stronger hand than the
     price alone asks for.

Only eval7.Card and eval7.evaluate are used from eval7.
"""

import bisect
import itertools
import json
import os
import random
import time

import eval7

# ── limits ───────────────────────────────────────────────────────────────────
THINK_S = 0.170          # Monte Carlo stops here, so decide() returns before 200 ms
MAX_ITERS = 1500         # enough for about +/-1.3% on equity
PUSH_FOLD_BB = 12.0      # at or below this stack (in big blinds): all-in or fold
BIG_BET = 1.05           # a bet above this share of the pot is an overbet
LOOSE_MIN = 0.08         # the narrowest range we ever assign to a bet
MAX_K = 12               # ... which is "the best of 12 random hands"
DEFAULT_DEFENCE = 1.0    # 1.0 = defend at the minimum defence frequency before evidence
COMMIT_PREMIUM = 0.08    # most extra equity asked for when risking a deep stack

RANKS = "AKQJT98765432"
SUITS = "shdc"
ALL_CARDS = [r + s for r in RANKS for s in SUITS]
CARD = {c: eval7.Card(c) for c in ALL_CARDS}
VOLUNTARY = ("fold", "check", "call", "raise", "all_in")


# ── starting-hand classes and the preflop tables ─────────────────────────────

def _class_names():
    names = []
    for i, a in enumerate(RANKS):
        for j, b in enumerate(RANKS):
            if i == j:
                names.append(a + b)
            elif i < j:
                names.append(a + b + "s")
            else:
                names.append(b + a + "o")
    return names


NAMES = _class_names()
CLASS_INDEX = {n: k for k, n in enumerate(NAMES)}
COMBOS = [6 if len(n) == 2 else (4 if n[2] == "s" else 12) for n in NAMES]


def _hand_class(c1, c2):
    r1, r2 = c1[0], c2[0]
    if r1 == r2:
        return CLASS_INDEX[r1 + r2]
    if RANKS.index(r1) > RANKS.index(r2):
        r1, r2 = r2, r1
    return CLASS_INDEX[r1 + r2 + ("s" if c1[1] == c2[1] else "o")]


def _rough_score(name):
    """Fallback hand strength if the data file can't be read (Chen-style points)."""
    pts = {"A": 10, "K": 8, "Q": 7, "J": 6, "T": 5}
    hi, lo = name[0], name[1]
    p = pts.get(hi, int(hi) / 2.0) if hi not in pts else pts[hi]
    if hi == lo:
        return max(5.0, p * 2)
    gap = RANKS.index(lo) - RANKS.index(hi) - 1
    p -= (0, 1, 2, 4)[gap] if gap < 4 else 5
    if name.endswith("s"):
        p += 2
    return p


def _load_tables():
    """Returns (order, eq, pushfold, ok). eq[i][j] = chance class i beats class j."""
    try:
        folder = os.environ.get("BOT_DATA_DIR") or ""
        path = os.path.join(folder, "preflop.json")
        if not os.path.isfile(path):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "preflop.json")
        with open(path) as f:
            d = json.load(f)
        if d["names"] != NAMES:
            raise ValueError("class order mismatch")
        eq = [[v / 10000.0 for v in row] for row in d["eq"]]
        return list(d["order"]), eq, d["pushfold"], True
    except Exception:
        score = [_rough_score(n) for n in NAMES]
        order = sorted(range(169), key=lambda i: -score[i])
        eq = [[min(0.85, max(0.15, 0.5 + 0.03 * (score[i] - score[j]))) for j in range(169)]
              for i in range(169)]
        return order, eq, {}, False


ORDER, EQ, PUSHFOLD, DATA_OK = _load_tables()

# CUM_W[r] = number of hand combos in the strongest r classes; PREFIX[i][r] =
# class i's summed equity against those classes. Equity vs "top X%" is a lookup.
CUM_W = [0]
for _k in ORDER:
    CUM_W.append(CUM_W[-1] + COMBOS[_k])
PREFIX = []
for _i in range(169):
    _row, _acc = [0.0], 0.0
    for _k in ORDER:
        _acc += COMBOS[_k] * EQ[_i][_k]
        _row.append(_acc)
    PREFIX.append(_row)
RANK_END = [0.0] * 169          # share of all hands that are at least as strong as class i
for _r, _k in enumerate(ORDER):
    RANK_END[_k] = CUM_W[_r + 1] / 1326.0


def _eq_vs_top(i, x):
    """Equity of class i against the strongest fraction x of starting hands."""
    r = bisect.bisect_right(CUM_W, max(0.0, min(1.0, x)) * 1326.0) - 1
    r = max(1, min(169, r))
    return PREFIX[i][r] / CUM_W[r]


def _pushfold(kind, i, eff_bb, ante):
    """True if class i is in the all-in ('push') or calling ('call') range."""
    try:
        table = PUSHFOLD["0.1" if ante > 0 else "0"]
        depth = min(20.0, max(1.0, round(eff_bb * 2) / 2.0))
        return table["%g" % depth][kind][i] == "1"
    except Exception:
        if kind == "push":
            return RANK_END[i] <= max(0.30, 1.0 - 0.045 * eff_bb)
        return RANK_END[i] <= max(0.15, 0.85 - 0.05 * eff_bb)


def _push_fraction(eff_bb, ante):
    """Share of hands the equilibrium small blind shoves at this stack depth."""
    return sum(COMBOS[i] for i in range(169) if _pushfold("push", i, eff_bb, ante)) / 1326.0


# ── opponent counters (reset every match, because the process restarts) ──────

STATS = {
    "open_n": 0, "open_shove": 0, "open_raise": 0, "open_limp": 0, "open_fold": 0,
    "limp_n": 0, "limp_shove": 0, "limp_raise": 0,          # opponent in the BB after we limp
    "raise_n": 0, "raise_shove": 0, "raise_3bet": 0, "raise_fold": 0, "raise_call": 0,
    "shove_n": 0, "shove_call": 0,                          # opponent facing our preflop all-in
    "bet_faced_n": 0, "bet_fold": 0,                        # opponent facing our postflop bets
    # per opportunity, after the flop: could they bet / raise, and did they?
    "fbet_n": 0, "fbet": 0,                                 # flop, nothing to call: normal bets
    "lbet_n": 0, "lbet": 0,                                 # turn and river, nothing to call
    "rz_n": 0, "rz": 0,                                     # facing our bet: normal raises
    "big_n": 0, "big": 0,                                   # any spot: overbets and big shoves
    "agg_n": 0, "agg": 0,                                   # every decision, any street: did they raise?
    # bets that reached a showdown: how often was the hand behind them weak?
    "shown_flop_n": 0, "shown_flop_weak": 0, "shown_late_n": 0, "shown_late_weak": 0,
    "shown_big_n": 0, "shown_big_weak": 0,
}
_DONE_HANDS = set()
_BOARDS = {}                     # hand number -> the board as we last saw it


def _rate(hits, n, prior, strength):
    """Observed frequency blended with a starting guess worth `strength` hands."""
    return (hits + prior * strength) / (n + strength)


def _replay(entries, me):
    """Walk one hand's log entries and rebuild the pot, so that for each of the
    opponent's postflop actions we know: were they facing a bet, did they bet
    or raise, and how big was it compared with the pot."""
    pot = 0
    bets = {}
    street = "preflop"
    out = []
    for e in entries:
        act = e.get("action")
        st = e.get("street")
        if act == "show" or act is None:
            continue
        if st != street and st in ("flop", "turn", "river"):
            street, bets = st, {}
        who = e.get("bot_id")
        amount = int(e.get("amount") or 0)
        mine = bets.get(who, 0)
        if act == "ante":
            pot += amount
            continue
        if act in ("small_blind", "big_blind"):
            bets[who] = mine + amount
            pot += amount
            continue
        if act not in VOLUNTARY:
            continue
        top = max(bets.values()) if bets else 0
        to_call = max(0, top - mine)
        rec = {"street": street, "facing": to_call > 0, "kind": "none", "big": False,
               "size": 0.0, "action": act}
        if act == "call":
            bets[who] = mine + amount
            pot += amount
        elif act in ("raise", "all_in"):
            if amount > top:                              # a real bet or raise, not a call for less
                size = (amount - top) / float(max(1, pot + to_call))
                rec["kind"] = "raise" if to_call > 0 else "bet"
                rec["size"] = size
                rec["big"] = size > BIG_BET or (act == "all_in" and size > 0.75)
            pot += max(0, amount - mine)
            bets[who] = max(mine, amount)
        if who != me and street != "preflop":
            out.append(rec)
    return out


def _strength(cards, board):
    """Share of all other hands that these two cards beat on a finished board."""
    known = set(cards) | set(board)
    deck = [CARD[c] for c in ALL_CARDS if c not in known]
    brd = [CARD[c] for c in board]
    mine = eval7.evaluate([CARD[c] for c in cards] + brd)
    score = n = 0
    for pair in itertools.combinations(deck, 2):
        other = eval7.evaluate(list(pair) + brd)
        score += 1.0 if mine > other else (0.5 if mine == other else 0.0)
        n += 1
    return score / n


def _digest(entries, me, hand_num=None):
    """Update STATS from one finished hand's log entries."""
    sb_id = None
    for e in entries:
        if e.get("action") == "small_blind":
            sb_id = e.get("bot_id")
    if sb_id is None:
        return
    acts = [e for e in entries if e.get("action") in VOLUNTARY]
    pre = [e for e in acts if e.get("street") == "preflop"]
    s = STATS
    for e in pre:
        if e.get("bot_id") != me:
            s["agg_n"] += 1
            s["agg"] += e["action"] in ("raise", "all_in")
    if pre:
        first = pre[0]
        if sb_id != me and first.get("bot_id") != me:
            s["open_n"] += 1
            a = first["action"]
            if a == "all_in":
                s["open_shove"] += 1
            elif a == "raise":
                s["open_raise"] += 1
            elif a == "call":
                s["open_limp"] += 1
            elif a == "fold":
                s["open_fold"] += 1
        elif sb_id == me and first.get("bot_id") == me and len(pre) > 1 and pre[1].get("bot_id") != me:
            mine, theirs = first["action"], pre[1]["action"]
            if mine == "call":
                s["limp_n"] += 1
                if theirs == "all_in":
                    s["limp_shove"] += 1
                elif theirs == "raise":
                    s["limp_raise"] += 1
            elif mine == "raise":
                s["raise_n"] += 1
                if theirs == "all_in":
                    s["raise_shove"] += 1
                elif theirs == "raise":
                    s["raise_3bet"] += 1
                elif theirs == "fold":
                    s["raise_fold"] += 1
                elif theirs == "call":
                    s["raise_call"] += 1
            elif mine == "all_in":
                s["shove_n"] += 1
                if theirs in ("call", "all_in"):
                    s["shove_call"] += 1
    recs = _replay(entries, me)
    for rec in recs:
        s["agg_n"] += 1
        s["agg"] += rec["kind"] != "none"
        s["big_n"] += 1
        if rec["big"]:
            s["big"] += 1
        if rec["facing"]:
            s["rz_n"] += 1
            s["bet_faced_n"] += 1
            if rec["action"] == "fold":
                s["bet_fold"] += 1
            if rec["kind"] == "raise" and not rec["big"]:
                s["rz"] += 1
        else:
            key = "fbet" if rec["street"] == "flop" else "lbet"
            s[key + "_n"] += 1
            if rec["kind"] == "bet" and not rec["big"]:
                s[key] += 1
    # Showdown evidence: if they bet and then showed a weak hand, their bets are
    # not all strength; if they always show strong hands, their bets are honest.
    shown = None
    for e in entries:
        if e.get("action") == "show" and e.get("bot_id") != me:
            shown = e.get("cards")
    board = _BOARDS.get(hand_num)
    if shown and board and len(board) == 5:
        bet_flop = any(r["kind"] != "none" and r["street"] == "flop" for r in recs)
        bet_late = any(r["kind"] != "none" and r["street"] != "flop" for r in recs)
        if bet_flop or bet_late:
            weak = _strength(shown, board) < 0.40
            if bet_flop:
                s["shown_flop_n"] += 1
                s["shown_flop_weak"] += weak
            if bet_late:
                s["shown_late_n"] += 1
                s["shown_late_weak"] += weak
            if any(r["big"] for r in recs):
                s["shown_big_n"] += 1
                s["shown_big_weak"] += weak


def _update_stats(state):
    me = state.get("your_bot_id")
    cur = state.get("hand_num", 0)
    groups = {}
    for e in state.get("match_action_log") or []:
        h = e.get("hand_num")
        if h is None or h >= cur or h in _DONE_HANDS:
            continue
        groups.setdefault(h, []).append(e)
    for h, entries in groups.items():
        # the log keeps only the last 200 entries: skip a hand whose start was cut off
        if entries[0].get("action") not in ("ante", "small_blind"):
            continue
        _DONE_HANDS.add(h)
        _digest(entries, me, h)


# ── postflop equity by simulation ────────────────────────────────────────────

def _equity(hole, board, k, deadline, max_iters=MAX_ITERS):
    """Chance of winning at showdown against the best of k random hands.
    k may be fractional: 1.4 means the best of 2 hands 40% of the time, else 1.
    hole/board are card strings. Returns (equity, samples)."""
    known = set(hole) | set(board)
    deck = [CARD[c] for c in ALL_CARDS if c not in known]
    mine = [CARD[c] for c in hole]
    brd = [CARD[c] for c in board]
    need = 5 - len(brd)
    ev = eval7.evaluate
    score = 0.0
    n = 0
    k_low = int(k)
    k_extra = k - k_low
    if need == 0 and k == 1:                       # river vs a random hand: count exactly
        a = ev(mine + brd)
        for pair in itertools.combinations(deck, 2):
            b = ev(list(pair) + brd)
            score += 1.0 if a > b else (0.5 if a == b else 0.0)
            n += 1
        return score / n, n
    sample = random.sample
    rnd = random.random
    clock = time.perf_counter
    fixed = mine + brd
    while n < max_iters:
        if n % 32 == 0 and n and clock() > deadline:
            break
        k = k_low + (1 if k_extra and rnd() < k_extra else 0)
        s = sample(deck, 2 * k + need)
        opp = s[0:2]
        if k > 1:
            best = ev(opp + brd)
            for j in range(1, k):
                cand = s[2 * j:2 * j + 2]
                v = ev(cand + brd)
                if v > best:
                    best, opp = v, cand
        runout = s[2 * k:]
        a = ev(fixed + runout)
        b = ev(opp + brd + runout)
        score += 1.0 if a > b else (0.5 if a == b else 0.0)
        n += 1
    return score / n, n


# ── helpers shared by the decision rules ─────────────────────────────────────

def _context(s):
    me = s["your_bot_id"]
    opp = None
    for p in s["players"]:
        if p.get("bot_id") != me:
            opp = p
            break
    bb = max(1, int(s["blinds"]["bb"]))
    my_total = s["your_stack"] + s["your_bet_this_street"]
    opp_total = opp["stack"] + opp["bet_this_street"]
    return {
        "me": me, "opp_id": opp["bot_id"], "bb": bb, "ante": s["blinds"].get("ante", 0),
        "stack": s["your_stack"], "my_bet": s["your_bet_this_street"],
        "owed": s["amount_owed"], "pot": s["pot"],
        "eff": min(my_total, opp_total),             # most either player can lose from here
        "opp_all_in": bool(opp.get("is_all_in")) or opp["stack"] <= 0,
    }


def _showdown_odds(c):
    """Equity needed to call (or shove over) a bet that puts us all-in."""
    risk = min(c["stack"], c["eff"] - c["my_bet"])
    if risk <= 0:
        return 0.0
    final_pot = c["pot"] + risk + max(0, risk - c["owed"])
    return risk / float(final_pot)


# ── preflop ──────────────────────────────────────────────────────────────────

def _preflop(s, c):
    i = _hand_class(s["your_cards"][0], s["your_cards"][1])
    st = STATS
    bb, owed, pot = c["bb"], c["owed"], c["pot"]
    eff_bb = c["eff"] / float(bb)
    ante = c["ante"]
    log = [a for a in s["action_log"] if a.get("action") in VOLUNTARY]
    mine = [a["action"] for a in log if a.get("bot_id") == c["me"]]
    theirs = [a["action"] for a in log if a.get("bot_id") != c["me"]]
    i_am_sb = s["sb_seat"] == s["seat_to_act"]
    dbg = {"hand": NAMES[i], "eff_bb": round(eff_bb, 1)}

    all_shoves = st["open_shove"] + st["limp_shove"] + st["raise_shove"]
    all_spots = st["open_n"] + st["limp_n"] + st["raise_n"]
    shove_overall = _rate(all_shoves, all_spots, 0.06, 4)

    # 1) Facing an all-in, or a raise so big that continuing commits our stack.
    if owed > 0 and (c["opp_all_in"] or owed >= 0.35 * c["stack"]):
        if not mine and not i_am_sb:                         # they open-shoved
            prior = _push_fraction(eff_bb, ante) if eff_bb <= 20 else 0.06
            x = _rate(st["open_shove"], st["open_n"], prior, 4)
        elif mine == ["call"]:                               # they shoved over our limp
            x = _rate(st["limp_shove"], st["limp_n"], 0.35 if eff_bb <= 12 else 0.08, 4)
        elif mine == ["raise"]:                              # they shoved over our raise
            prior = 0.25 if eff_bb <= 15 else (0.12 if eff_bb <= 30 else 0.04)
            x = _rate(st["raise_shove"], st["raise_n"], prior, 4)
        else:                                                # later in a raising war
            x = 0.10 if eff_bb <= 20 else 0.04
        x = max(x, 0.85 * shove_overall)
        need = _showdown_odds(c) + 0.05 * min(1.0, max(0.0, (eff_bb - 10) / 40.0))
        eq = _eq_vs_top(i, x)
        dbg.update(spot="vs_shove", range=round(x, 2), eq=round(eq, 3), need=round(need, 3))
        if eq >= need:
            return ({"action": "call"} if c["opp_all_in"] else {"action": "all_in"}), dbg
        return {"action": "fold"}, dbg

    # 2) We are the small blind and first to act.
    if i_am_sb and not mine and not theirs:
        jam_back = _rate(st["raise_shove"] + st["limp_shove"], st["raise_n"] + st["limp_n"], 0.05, 4)
        if eff_bb <= PUSH_FOLD_BB:
            dbg.update(spot="push_fold")
            if _pushfold("push", i, eff_bb, ante):
                return {"action": "all_in"}, dbg
            return {"action": "fold"}, dbg
        if jam_back > 0.5:                 # they shove over everything: enter only with hands that call
            eq = _eq_vs_top(i, max(jam_back, 0.85 * shove_overall))
            dbg.update(spot="vs_jammer", eq=round(eq, 3))
            if eq >= 0.5 + 0.05 * min(1.0, max(0.0, (eff_bb - 10) / 40.0)):
                return {"action": "raise", "amount": 2 * bb}, dbg
            return {"action": "fold"}, dbg
        fold_to_open = _rate(st["raise_fold"], st["raise_n"], 0.40, 6)
        open_share = 1.0 if fold_to_open > 0.60 else 0.80
        dbg.update(spot="open")
        if RANK_END[i] <= open_share:
            size = 2.5 if eff_bb >= 25 else (2.2 if eff_bb >= 18 else 2.0)
            return {"action": "raise", "amount": int(size * bb)}, dbg
        return {"action": "fold"}, dbg

    # 3) We are the big blind and the small blind just called.
    if owed == 0:
        dbg.update(spot="vs_limp")
        if eff_bb <= PUSH_FOLD_BB:
            if RANK_END[i] <= 0.35:
                return {"action": "all_in"}, dbg
        elif RANK_END[i] <= 0.30:
            return {"action": "raise", "amount": int(3.5 * bb)}, dbg
        return {"action": "check"}, dbg

    odds = owed / float(pot + owed)

    # 4) We are the big blind facing an opening raise.
    if not mine and theirs == ["raise"]:
        x = max(0.10, _rate(st["open_raise"] + st["open_shove"], st["open_n"], 0.70, 6))
        eq = _eq_vs_top(i, x)
        dbg.update(spot="vs_open", range=round(x, 2), eq=round(eq, 3), odds=round(odds, 3))
        if eff_bb <= 20:
            if eq >= 0.56:
                return {"action": "all_in"}, dbg
            if eq >= odds + 0.07:
                return {"action": "call"}, dbg
            return {"action": "fold"}, dbg
        if RANK_END[i] <= 0.09 or eq >= 0.64:
            return {"action": "raise", "amount": int(3.2 * s["current_bet"])}, dbg
        if eq >= odds + 0.06:
            return {"action": "call"}, dbg
        return {"action": "fold"}, dbg

    # 5) We opened and they re-raised.
    if mine == ["raise"]:
        x = max(0.03, _rate(st["raise_3bet"] + st["raise_shove"], st["raise_n"], 0.12, 6))
        eq = _eq_vs_top(i, x)
        dbg.update(spot="vs_3bet", range=round(x, 2), eq=round(eq, 3), odds=round(odds, 3))
        if eq >= 0.62:
            if eff_bb <= 50:
                return {"action": "all_in"}, dbg
            return {"action": "raise", "amount": int(2.4 * s["current_bet"])}, dbg
        if eq >= odds + 0.04:
            return {"action": "call"}, dbg
        return {"action": "fold"}, dbg

    # 6) Anything else (a long raising war): continue only with a strong hand.
    eq = _eq_vs_top(i, 0.05)
    dbg.update(spot="raise_war", eq=round(eq, 3), odds=round(odds, 3))
    if eq >= 0.60:
        return {"action": "all_in"}, dbg
    if eq >= odds + 0.05:
        return {"action": "call"}, dbg
    return {"action": "fold"}, dbg


# ── postflop ─────────────────────────────────────────────────────────────────

def _looseness(kind, big, street, size):
    """How wide is the range behind this bet? 1.0 = it could be any hand,
    small = only their best hands.

    Before evidence: the minimum defence frequency for the bet size, which
    assumes a normal mix of strong hands and bluffs. Then it moves with how
    often this opponent makes this kind of bet: towards 1.0 if they make it
    almost every time, towards a narrow range if they rarely do. Raises and
    big bets start out narrow, because most players make them rarely."""
    st = STATS
    size = max(0.1, size)
    base = min(1.0, DEFAULT_DEFENCE * (1 + 2 * size) / ((1 + size) ** 2))
    # An opponent who raises a lot everywhere (preflop included) starts with
    # looser guesses in every bucket; a passive one with tighter guesses.
    overall = _rate(st["agg"], st["agg_n"], 0.30, 6)
    boost = min(3.0, max(0.6, overall / 0.30))
    if big:
        # Overbets and big shoves: narrow unless they make them often, or have
        # been caught making one with a weak hand.
        f = _rate(st["big"], st["big_n"], min(0.60, 0.10 * boost), 5)
        if f >= 0.20:
            loose = base + (1.0 - base) * min(1.0, (f - 0.20) / 0.40)
        else:
            loose = base * max(0.25, f / 0.20)
        weak_share = _rate(st["shown_big_weak"], st["shown_big_n"], 0.20, 3)
        if weak_share > 0.20:
            target = max(base, 0.80)
            if target > loose:
                loose += (target - loose) * min(1.0, (weak_share - 0.20) / 0.30)
        else:
            honest = max(LOOSE_MIN, f)
            if loose > honest:
                loose = honest + (loose - honest) * weak_share / 0.20
        return loose
    if kind == "raise":
        f, usual = _rate(st["rz"], st["rz_n"], min(0.60, 0.12 * boost), 6), 0.30
    elif street == "flop":
        f, usual = _rate(st["fbet"], st["fbet_n"], min(0.90, 0.50 * boost ** 0.5), 6), 0.50
    else:
        f, usual = _rate(st["lbet"], st["lbet_n"], min(0.90, 0.40 * boost ** 0.5), 6), 0.40
    if f >= usual:
        loose = base + (1.0 - base) * min(1.0, (f - usual) / (0.85 - usual))
    else:
        loose = base * max(0.25, f / usual)
    # If their bets keep showing up strong at showdown, they bet honestly: read
    # the bet as "the top f of their hands" (no bluffs in it) instead.
    if street == "flop" and kind == "bet" and not big:
        weak_share = _rate(st["shown_flop_weak"], st["shown_flop_n"], 0.30, 2)
    else:
        weak_share = _rate(st["shown_late_weak"], st["shown_late_n"], 0.30, 2)
    honest = max(LOOSE_MIN, f)
    if loose > honest:
        loose = honest + (loose - honest) * min(1.0, weak_share / 0.30)
    return loose


def _read_bets(s, c):
    """Combine everything the opponent did this hand into one number: how wide
    their range still is (1.0 = any hand). Also says whether we were the last
    raiser before the flop."""
    st = STATS
    me = c["me"]
    loose = 1.0
    was_aggressor = False
    my_raise_seen = False
    pre_freq = None
    for a in s["action_log"]:
        if a.get("street") != "preflop" or a.get("action") not in ("raise", "all_in"):
            continue
        if a.get("bot_id") == me:
            was_aggressor = my_raise_seen = True
            continue
        was_aggressor = False
        if my_raise_seen:                                 # they re-raised us
            f = _rate(st["raise_3bet"] + st["raise_shove"], st["raise_n"], 0.12, 6)
        elif s["sb_seat"] != s["seat_to_act"]:            # they opened from the small blind
            f = _rate(st["open_raise"] + st["open_shove"], st["open_n"], 0.70, 6)
        else:
            f = 0.30
        pre_freq = f if pre_freq is None else min(pre_freq, f)
    if pre_freq is not None:                              # preflop strength carries over only partly
        loose *= max(0.5, pre_freq ** 0.25)

    recs = [r for r in _replay(s["action_log"], me) if r["kind"] != "none"]
    for idx, r in enumerate(recs):
        pending = c["owed"] > 0 and idx == len(recs) - 1 and r["street"] == s["street"]
        size, big = r["size"], r["big"]
        if pending:                                       # the bet in front of us: use the live numbers
            size = c["owed"] / float(max(1, c["pot"] - c["owed"]))
            big = size > BIG_BET or (c["opp_all_in"] and size > 0.75)
        li = _looseness(r["kind"], big, r["street"], size)
        loose *= li if pending else li ** 0.5             # earlier streets count for less
    return max(LOOSE_MIN, min(1.0, loose)), was_aggressor


def _commit_premium(c, risk):
    """Extra equity asked for when a lot of big blinds go in compared with the
    pot. Zero for small bets and short stacks, at most COMMIT_PREMIUM. It fades
    against an opponent who has proven to raise all the time: their big bets
    are not strength, and waiting only gives them free cards."""
    before = max(1, c["pot"] - c["owed"])
    overall = _rate(STATS["agg"], STATS["agg_n"], 0.30, 6)
    fade = min(1.0, max(0.0, 1.0 - (overall - 0.30) / 0.30))
    return (COMMIT_PREMIUM * fade * min(1.0, (risk / float(c["bb"])) / 80.0)
            * min(1.0, (risk / float(before)) / 1.5))


def _postflop(s, c, deadline):
    st = STATS
    pot, owed, stack = c["pot"], c["owed"], c["stack"]
    street = s["street"]

    loose, was_aggressor = _read_bets(s, c)
    k = min(float(MAX_K), (2.0 - loose) / loose)      # range width -> "best of k hands"
    eq, n = _equity(s["your_cards"], s["community_cards"], k, deadline)
    fold_to_bet = _rate(st["bet_fold"], st["bet_faced_n"], 0.40, 6)
    dbg = {"eq": round(eq, 3), "loose": round(loose, 2), "k": round(k, 1), "n": n,
           "ftb": round(fold_to_bet, 2)}
    deep = stack / float(c["bb"]) > 40

    if owed == 0:
        if c["opp_all_in"]:
            return {"action": "check"}, dbg
        value_at = 0.54 + 0.12 * fold_to_bet          # callers get value-bet thinner
        if eq >= value_at:
            frac = min(1.0, max(0.5, 0.55 + 1.5 * (eq - value_at)))
            if fold_to_bet < 0.20:
                frac += 0.25
            bet = int(frac * pot)
            if bet >= 0.6 * stack and (not deep or eq >= value_at + 2 * _commit_premium(c, stack)):
                return {"action": "all_in"}, dbg
            return {"action": "raise", "amount": s["current_bet"] + bet}, dbg
        # Bluffs only where the counters say they fold often enough to pay for it.
        r = random.random()
        if street == "flop" and was_aggressor and fold_to_bet >= 0.33 and r < 0.5:
            dbg["bluff"] = 1
            return {"action": "raise", "amount": s["current_bet"] + int(0.5 * pot)}, dbg
        if street != "flop" and fold_to_bet > 0.50 and eq < 0.40 and r < 0.4:
            dbg["bluff"] = 1
            return {"action": "raise", "amount": s["current_bet"] + int(0.6 * pot)}, dbg
        return {"action": "check"}, dbg

    odds = owed / float(pot + owed)
    premium = _commit_premium(c, min(owed, stack))
    dbg["odds"] = round(odds, 3)
    dbg["prem"] = round(premium, 3)
    if c["opp_all_in"] or owed >= stack:
        return ({"action": "call"} if eq >= odds + 0.02 + premium else {"action": "fold"}), dbg
    if eq >= 0.78:
        raise_to = s["current_bet"] + int(0.75 * (pot + owed))
        if raise_to - c["my_bet"] >= 0.5 * stack:
            # a deep stack goes in only well ahead; otherwise keep the pot smaller
            if not deep or eq >= 0.78 + _commit_premium(c, stack):
                return {"action": "all_in"}, dbg
            return {"action": "call"}, dbg
        return {"action": "raise", "amount": raise_to}, dbg
    margin = 0.0 if street == "river" else 0.02
    if eq >= odds + margin + premium:
        return {"action": "call"}, dbg
    return {"action": "fold"}, dbg


# ── the safety wrapper ───────────────────────────────────────────────────────

def _legal(act, s):
    """Turn whatever the strategy produced into an action the engine will apply
    exactly as written. In particular: never 'check' when chips are owed."""
    owed = int(s.get("amount_owed") or 0)
    stack = int(s.get("your_stack") or 0)
    my_bet = int(s.get("your_bet_this_street") or 0)
    passive = {"action": "check"} if owed == 0 else {"action": "fold"}
    if not isinstance(act, dict):
        return passive
    a = act.get("action")
    out = None
    if a == "fold":
        out = passive                                   # never fold for free
    elif a == "check":
        out = passive                                   # owed > 0 -> fold, not an accidental call
    elif a == "call":
        out = {"action": "call"} if owed > 0 else {"action": "check"}
    elif a in ("raise", "all_in"):
        me = s.get("your_bot_id")
        opp = next((p for p in s.get("players", []) if p.get("bot_id") != me), None)
        opp_total = (opp["stack"] + opp["bet_this_street"]) if opp else 0
        opp_done = (opp is None) or opp.get("is_all_in") or opp["stack"] <= 0
        if opp_done or stack <= owed:                   # nobody left to raise against
            out = {"action": "call"} if owed > 0 else {"action": "check"}
        elif a == "all_in":
            out = {"action": "all_in"}
        else:
            amount = int(act.get("amount") or 0)
            amount = max(int(s.get("min_raise_to") or 0), min(amount, opp_total))
            if amount - my_bet >= stack:
                out = {"action": "all_in"}
            else:
                out = {"action": "raise", "amount": amount}
    if out is None:
        return passive
    if "debug" in act:
        out["debug"] = act["debug"]
    return out


def _think(s, t0):
    try:
        _update_stats(s)
    except Exception:
        pass                                            # counters are optional; decisions are not
    c = _context(s)
    _BOARDS[s["hand_num"]] = list(s["community_cards"])
    if s["street"] == "preflop":
        act, dbg = _preflop(s, c)
    else:
        act, dbg = _postflop(s, c, t0 + THINK_S)
    dbg["data_ok"] = DATA_OK                          # False = the tables failed to load
    dbg["ms"] = round((time.perf_counter() - t0) * 1000, 1)
    act["debug"] = dbg
    return act


def decide(game_state: dict) -> dict:
    t0 = time.perf_counter()
    try:
        if game_state.get("type") == "warmup":
            _equity(["As", "Kd"], ["7c", "8d", "2h"], 2, t0 + 0.05, 200)   # warm the caches
            return {"action": "check"}
        act = _think(game_state, t0)
    except Exception:
        act = None
    try:
        return _legal(act, game_state)
    except Exception:
        try:
            return {"action": "check"} if int(game_state.get("amount_owed") or 0) == 0 else {"action": "fold"}
        except Exception:
            return {"action": "fold"}
