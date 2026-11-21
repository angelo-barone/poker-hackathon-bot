"""Exact ceiling against an always-all-in opponent.

Against a bot that shoves every hand, each hand is one choice: get all the
chips in, or fold and pay the blind. That is small enough to solve exactly by
working backwards from the end of the match (dynamic programming): for every
stack size and hand number we compute the best possible chance of winning the
match, and the weakest hand worth playing there.

Simplification: ties at showdown are counted as half a win (they are 2-4% of deals).

  python tools/allin_ceiling.py
"""

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pokercore import structures  # noqa: E402

TOTAL, GRID, HANDS = 20_000, 5, 400


def main():
    d = json.load(open(os.path.join(ROOT, "my_bots", "im_just_in_mech_eng", "data", "preflop.json")))
    eq = np.array(d["vs_random"])[:, None]                 # each class's equity vs a random hand
    w = np.array(d["combos"], dtype=float)[:, None] / 1326.0
    order = np.argsort(-eq[:, 0])
    cum = np.cumsum(w[order, 0])                           # share of hands at least this strong
    struct = structures.parse("standard", 10_000)

    n = TOTAL // GRID + 1
    x = np.arange(n) * GRID
    e = np.minimum(x, TOTAL - x)                           # chips at risk in an all-in
    up, dn = (x + e) // GRID, (x - e) // GRID
    nxt = [x / TOTAL, x / TOTAL]                           # [we are SB next hand, we are BB next hand]
    policy = {}
    for h in reversed(range(HANDS)):
        lvl = struct.level(h)
        cur = []
        for pos in (0, 1):                                 # 0: we post the small blind, 1: the big blind
            cost = (lvl.sb if pos == 0 else lvl.bb) + lvl.ante
            v = nxt[1 - pos]
            play = eq * v[up][None, :] + (1 - eq) * v[dn][None, :]          # (169, n)
            can_fold = x > cost
            fold = np.where(can_fold, v[np.maximum(x - cost, 0) // GRID], -1.0)[None, :]
            best = np.maximum(play, fold)
            val = (w * best).sum(axis=0)
            val[0], val[-1] = 0.0, 1.0
            cur.append(val)
            if h % 20 == 0:
                plays = (play >= fold)                                       # which classes play
                share = (w * plays).sum(axis=0)
                policy[(h, pos)] = share
        nxt = cur

    start = TOTAL // 2 // GRID
    ceiling = 0.5 * (nxt[0][start] + nxt[1][start])
    print(f"Best possible match win rate vs always-all-in: {100 * ceiling:.1f}%")
    print("\nShare of hands worth playing (top X%), by blind level and our share of the chips:")
    shares = [0.15, 0.25, 0.35, 0.50, 0.65, 0.80]
    print("  level  blinds      " + "".join(f"{int(100 * s):>5}% " for s in shares) + " (our chips)")
    for h in range(0, 240, 20):
        lvl = struct.level(h)
        row = [0.5 * (policy[(h, 0)][int(s * TOTAL) // GRID] + policy[(h, 1)][int(s * TOTAL) // GRID])
               for s in shares]
        print(f"  {h // 20 + 1:>5}  {str(lvl.sb) + '/' + str(lvl.bb):<10}  "
              + "".join(f"{100 * r:>5.0f}% " for r in row))
    out = {"ceiling": round(float(ceiling), 4),
           "start_range_level1": round(float(0.5 * (policy[(0, 0)][start] + policy[(0, 1)][start])), 3)}
    with open(os.path.join(ROOT, "results", "allin_ceiling.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
