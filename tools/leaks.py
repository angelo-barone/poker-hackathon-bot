"""Leak report: where do our chips go, spot by spot?

Plays duplicate pairs against each named opponent, keeps every event of every
match, and sorts each hand into a spot:

  - the preflop path (we open and get re-raised, our big blind faces a raise, ...)
  - how the hand ended after the flop (we folded to a bet, we called and lost, ...)
  - all-in showdowns, with the win rate our cards deserved

and reports each spot as: how often it happens, how often we fold in it, and
what it wins or loses per 100 hands (in chips and in big blinds).

It also reports when matches are decided and how duplicate pairs end up drawn.

  python tools/leaks.py chartbot,threebettor,stealer,gto_charts --pairs 250
"""

import argparse
import json
import multiprocessing as mp
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import arena  # noqa: E402

ENTRY = os.path.join("my_bots", "im_just_in_mech_eng")
RANKS = "AKQJT98765432"
_EQ = {}


def _eq_tables():
    if not _EQ:
        d = json.load(open(os.path.join(ROOT, ENTRY, "data", "preflop.json")))
        _EQ["idx"] = {n: k for k, n in enumerate(d["names"])}
        _EQ["eq"] = d["eq"]
    return _EQ


def _cls(cards):
    r1, r2 = sorted((cards[0][0], cards[1][0]), key=RANKS.index)
    return r1 + r2 if r1 == r2 else r1 + r2 + ("s" if cards[0][1] == cards[1][1] else "o")


def split_hands(events, me):
    hands, cur = [], None
    for e in events:
        t = e["type"]
        if t == "hand_start":
            sb_bot = next(n for n, seat in e["seats"].items() if seat == e["sb"])
            cur = {"n": e["hand"], "bb": e["blinds"]["bb"], "level": e["level"], "sb_bot": sb_bot,
                   "stacks": e["stacks"], "hole": e["hole"], "dec": [], "showdown": False, "delta": 0}
        elif t == "decision":
            a = e["applied"]
            cur["dec"].append((e["bot"], e["street"], a["action"], e["state"]["amount_owed"]))
        elif t == "showdown":
            cur["showdown"] = True
        elif t == "hand_end":
            cur["delta"] = e["deltas"][me]
            hands.append(cur)
    return hands


def classify(h, me):
    """Returns (preflop path, our response or None, postflop outcome or None, all-in kind or None)."""
    dec = h["dec"]
    pre = [d for d in dec if d[1] == "preflop"]
    post = [d for d in dec if d[1] != "preflop"]
    resp = None
    if not pre:
        path = "blinds force an all-in"
    elif h["sb_bot"] == me:
        a0 = pre[0][2]
        r = pre[1][2] if len(pre) > 1 else None
        if a0 == "fold":
            path = "SB: we fold"
        elif a0 == "all_in":
            path = "SB: we shove, they fold" if r == "fold" else "SB: we shove, they call"
        elif a0 == "raise":
            if r == "fold":
                path = "SB: we open, they fold"
            elif r == "call":
                path = "SB: we open, they call"
            elif r == "raise":
                path, resp = "SB: we open, they re-raise", (pre[2][2] if len(pre) > 2 else None)
            else:
                path, resp = "SB: we open, they shove", (pre[2][2] if len(pre) > 2 else None)
        else:
            path = "SB: we limp"
    else:
        a0 = pre[0][2]
        if a0 == "fold":
            path = "BB: they fold"
        elif a0 == "call":
            path = "BB: they limp"
        elif a0 == "raise":
            path, resp = "BB: we face a raise", (pre[1][2] if len(pre) > 1 else None)
        else:
            path, resp = "BB: we face a shove", (pre[1][2] if len(pre) > 1 else None)

    outcome = None
    if post:
        we_fold = any(d[0] == me and d[2] == "fold" for d in post)
        they_fold = any(d[0] != me and d[2] == "fold" for d in post)
        raises = [d[0] for d in post if d[2] in ("raise", "all_in")]
        last_aggr = raises[-1] if raises else None
        if we_fold:
            outcome = "we fold to a bet"
        elif they_fold:
            outcome = "they fold to our bet"
        elif h["showdown"]:
            res = "win" if h["delta"] > 0 else ("lose" if h["delta"] < 0 else "tie")
            if last_aggr is None:
                outcome = "checked down, " + res
            elif last_aggr != me:
                outcome = "we call their bet, " + res
            else:
                outcome = "they call our bet, " + res

    allin = None
    eff = min(h["stacks"].values())
    if h["showdown"] and abs(h["delta"]) >= eff and dec:
        allin = "preflop" if not post else "postflop"
    return path, resp, outcome, allin


def analyse_pair(args):
    opp_path, seed, me_path = args
    out = {"paths": {}, "post": {}, "allin": {}, "faced": [0, 0], "hands": 0, "chips": 0, "bbs": 0.0,
           "matches": []}
    t = _eq_tables()
    for first in (0, 1):
        r = arena.play_one(me_path, opp_path, seed, first, False, keep=True)
        me = r["names"][0]
        hands = split_hands(r["events"], me)
        big = None
        for h in hands:
            path, resp, outcome, allin = classify(h, me)
            bbs = h["delta"] / h["bb"]
            out["hands"] += 1
            out["chips"] += h["delta"]
            out["bbs"] += bbs
            p = out["paths"].setdefault(path, [0, 0, 0, 0, 0.0])        # n, answered, folds, chips, bbs
            p[0] += 1
            if resp is not None:
                p[1] += 1
                p[2] += resp == "fold"
            p[3] += h["delta"]
            p[4] += bbs
            if outcome:
                q = out["post"].setdefault(outcome, [0, 0, 0.0])
                q[0] += 1
                q[1] += h["delta"]
                q[2] += bbs
            for d in h["dec"]:
                if d[0] == me and d[1] != "preflop" and d[3] > 0:
                    out["faced"][0] += 1
                    out["faced"][1] += d[2] == "fold"
            if allin:
                opp = next(n for n in h["hole"] if n != me)
                exp = t["eq"][t["idx"][_cls(h["hole"][me])]][t["idx"][_cls(h["hole"][opp])]] / 10000.0
                a = out["allin"].setdefault(allin, [0, 0.0, 0, 0.0, 0.0])  # n, wins, chips, bbs, expected
                a[0] += 1
                a[1] += 1.0 if h["delta"] > 0 else (0.5 if h["delta"] == 0 else 0.0)
                a[2] += h["delta"]
                a[3] += bbs
                a[4] += exp
            if big is None or abs(h["delta"]) > abs(big[0]):
                big = (h["delta"], h["n"], h["level"], allin or "no all-in")
        last = hands[-1]
        out["matches"].append({
            "won": r["a_won"], "hands": len(hands), "end_level": last["level"],
            "end_allin": classify(last, me)[3] or "no all-in",
            "big_hand": big[1], "big_level": big[2], "big_kind": big[3],
        })
    return opp_path, out


def merge(total, part):
    for key in ("paths", "post", "allin"):
        for k, v in part[key].items():
            cur = total[key].setdefault(k, [0] * len(v))
            for i, x in enumerate(v):
                cur[i] += x
    total["faced"][0] += part["faced"][0]
    total["faced"][1] += part["faced"][1]
    for key in ("hands", "chips", "bbs"):
        total[key] += part[key]
    total["pairs"].append(part["matches"])


def report(name, t):
    H = t["hands"]
    per = 100.0 / H
    matches = [m for pair in t["pairs"] for m in pair]
    wins = sum(m["won"] for m in matches)
    print(f"\n=== vs {name}: {len(t['pairs'])} pairs, {len(matches)} matches, {H:,} hands, "
          f"match win rate {100 * wins / len(matches):.1f}% ===")
    print(f"  overall: {t['chips'] * per:+.0f} chips/100 hands, {t['bbs'] * per:+.1f} bb/100")
    print(f"\n  PREFLOP PATH                   per 100   we fold   chips/100    bb/100")
    for k, v in sorted(t["paths"].items(), key=lambda kv: kv[1][4]):
        fold = f"{100 * v[2] / v[1]:.0f}%" if v[1] else "-"
        print(f"  {k:<30}{v[0] * per:>8.1f}{fold:>10}{v[3] * per:>12.0f}{v[4] * per:>10.1f}")
    print(f"\n  AFTER THE FLOP                 per 100             chips/100    bb/100")
    for k, v in sorted(t["post"].items(), key=lambda kv: kv[1][2]):
        print(f"  {k:<30}{v[0] * per:>8.1f}{'':>10}{v[1] * per:>12.0f}{v[2] * per:>10.1f}")
    f = t["faced"]
    print(f"  postflop bets we faced: {f[0] * per:.1f} per 100 hands, we folded to {100 * f[1] / max(f[0], 1):.0f}%")
    print(f"\n  ALL-IN SHOWDOWNS               per 100   we win  deserved   chips/100    bb/100")
    for k, v in sorted(t["allin"].items()):
        deserved = f"{100 * v[4] / v[0]:.0f}%" if k == "preflop" else "-"
        print(f"  {k:<30}{v[0] * per:>8.2f}{100 * v[1] / v[0]:>8.0f}%{deserved:>10}{v[2] * per:>12.0f}{v[3] * per:>10.1f}")


def decided(label, pairs):
    matches = [m for pair in pairs for m in pair]
    n = len(matches)
    q = statistics.quantiles([m["big_hand"] + 1 for m in matches], n=4)
    ends = statistics.quantiles([m["hands"] for m in matches], n=4)
    kinds = {}
    for m in matches:
        kinds[m["big_kind"]] = kinds.get(m["big_kind"], 0) + 1
    end_kinds = {}
    for m in matches:
        end_kinds[m["end_allin"]] = end_kinds.get(m["end_allin"], 0) + 1
    levels = {}
    for m in matches:
        levels[m["big_level"]] = levels.get(m["big_level"], 0) + 1
    w = sum(1 for p in pairs if p[0]["won"] and p[1]["won"])
    l = sum(1 for p in pairs if not p[0]["won"] and not p[1]["won"])
    draws = [p for p in pairs if p[0]["won"] != p[1]["won"]]
    same = sum(1 for p in draws if p[0]["big_hand"] == p[1]["big_hand"])
    same_pre = sum(1 for p in draws if p[0]["big_hand"] == p[1]["big_hand"]
                   and p[0]["big_kind"] == "preflop" and p[1]["big_kind"] == "preflop")
    both_pre = sum(1 for p in draws if p[0]["big_kind"] == "preflop" and p[1]["big_kind"] == "preflop")
    out = {
        "label": label, "matches": n, "pairs": len(pairs), "W": w, "D": len(draws), "L": l,
        "biggest_hand_quartiles": [round(x) for x in q], "match_length_quartiles": [round(x) for x in ends],
        "biggest_hand_kind": {k: round(100 * v / n, 1) for k, v in kinds.items()},
        "last_hand_kind": {k: round(100 * v / n, 1) for k, v in end_kinds.items()},
        "biggest_hand_level": {str(k): round(100 * v / n, 1) for k, v in sorted(levels.items())},
        "draws_same_deciding_hand": round(100 * same / max(len(draws), 1), 1),
        "draws_same_hand_preflop_allin": round(100 * same_pre / max(len(draws), 1), 1),
        "draws_both_decided_by_preflop_allin": round(100 * both_pre / max(len(draws), 1), 1),
    }
    print(f"\n--- when are matches decided: {label} ({n} matches) ---")
    print(f"  match length (hands), quartiles: {out['match_length_quartiles']}")
    print(f"  biggest hand of the match happens at hand (quartiles): {out['biggest_hand_quartiles']}")
    print(f"  blind level of the biggest hand (% of matches): {out['biggest_hand_level']}")
    print(f"  the biggest hand was: {out['biggest_hand_kind']}  (% of matches)")
    print(f"  the last hand was:    {out['last_hand_kind']}  (% of matches)")
    print(f"  pairings W/D/L {w}/{len(draws)}/{l}; of the draws: same deal was the biggest hand in both "
          f"matches {out['draws_same_deciding_hand']}%, and it was a preflop all-in both times "
          f"{out['draws_same_hand_preflop_allin']}%; biggest hand a preflop all-in in both matches "
          f"{out['draws_both_decided_by_preflop_allin']}%")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("opponents", help="comma-separated names in sparring/ (or bots/caller)")
    ap.add_argument("--pairs", type=int, default=250)
    ap.add_argument("--bot", default=ENTRY, help="the bot to analyse (default: the entry)")
    ap.add_argument("--out", default="leaks", help="results/<out>.json")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()

    names = args.opponents.split(",")
    paths = {n: (os.path.join("bots", n) if n == "caller" else os.path.join("sparring", n)) for n in names}
    seeds = arena.pair_seeds(args.seed, args.pairs)
    jobs = [(paths[n], s, args.bot) for s in seeds for n in names]
    totals = {p: {"paths": {}, "post": {}, "allin": {}, "faced": [0, 0], "hands": 0, "chips": 0,
                  "bbs": 0.0, "pairs": []} for p in paths.values()}
    t0 = time.time()
    with mp.Pool(args.workers) as pool:
        for opp, part in pool.imap_unordered(analyse_pair, jobs):
            merge(totals[opp], part)
    print(f"leak report: {args.pairs} pairs vs each of {len(names)} opponents ({time.time() - t0:.0f}s)")
    saved = {}
    for n in names:
        t = totals[paths[n]]
        report(n, t)
        d = decided(n, t["pairs"])
        saved[n] = {"hands": t["hands"], "chips": t["chips"], "bbs": t["bbs"], "paths": t["paths"],
                    "post": t["post"], "allin": t["allin"], "faced": t["faced"], "decided": d}
    saved["_all"] = decided("all of them together", [p for n in names for p in totals[paths[n]]["pairs"]])
    with open(os.path.join(ROOT, "results", args.out + ".json"), "w") as f:
        json.dump(saved, f, indent=1)


if __name__ == "__main__":
    main()
