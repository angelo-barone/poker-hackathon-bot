"""Experiment: against a bot that goes all-in every hand, how wide should we call?

Builds one tiny bot per calling range ("play the top X% of hands, fold the
rest") in experiments/allin_sweep/topXX/, then plays each against
sparring/allin on the same seeds. Against an always-all-in opponent the only
real choice each hand is "get the chips in or fold", so these bots cover the
whole space of fixed-range strategies.

  python tools/allin_sweep.py --pairs 1000
"""

import argparse
import json
import multiprocessing as mp
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import arena  # noqa: E402

BOT = '''"""Experiment bot: gets all-in with the top {pct}% of starting hands, folds the rest."""

RANKS = "AKQJT98765432"
PLAY = {play!r}


def decide(s):
    if s.get("type") == "warmup":
        return {{"action": "check"}}
    a, b = s["your_cards"]
    r1, r2 = sorted((a[0], b[0]), key=RANKS.index)
    name = r1 + r2 if r1 == r2 else r1 + r2 + ("s" if a[1] == b[1] else "o")
    if name in PLAY:
        return {{"action": "call"}} if s["amount_owed"] >= s["your_stack"] or any(
            p["is_all_in"] for p in s["players"]) else {{"action": "all_in"}}
    return {{"action": "check"}} if s["can_check"] else {{"action": "fold"}}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--tops", default="5,10,15,20,30,40,50,60,70,85,100")
    args = ap.parse_args()

    d = json.load(open(os.path.join(ROOT, "my_bots", "im_just_in_mech_eng", "data", "preflop.json")))
    names, order, combos = d["names"], d["order"], d["combos"]
    bots = []
    for pct in [int(x) for x in args.tops.split(",")]:
        play, total = [], 0
        for k in order:                               # strongest first, until X% of hands
            if total + combos[k] > pct / 100.0 * 1326 + 1e-9 and play:
                break
            play.append(names[k])
            total += combos[k]
        folder = os.path.join(ROOT, "experiments", "allin_sweep", "top%02d" % pct)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "bot.py"), "w", newline="\n") as f:
            f.write(BOT.format(pct=pct, play=sorted(play)))
        bots.append((pct, os.path.relpath(folder, ROOT), 100.0 * total / 1326, play[-1]))
    bots.append(("v1", os.path.join("my_bots", "im_just_in_mech_eng"), None, None))

    opp = os.path.join("sparring", "allin")
    seeds = arena.pair_seeds(args.seed, args.pairs)
    jobs = [(path, opp, s, False) for s in seeds for _, path, _, _ in bots]
    res = {path: [] for _, path, _, _ in bots}
    t0 = time.time()
    with mp.Pool(args.workers) as pool:
        # play_pair returns the opponent, not the bot, so run one bot per map call
        for _, path, _, _ in bots:
            for _, _, r in pool.imap_unordered(arena.play_pair, [j for j in jobs if j[0] == path],
                                               chunksize=8):
                res[path].append(r)
    rows = []
    print(f"\nCalling-range sweep vs always-all-in: {args.pairs} duplicate pairs each "
          f"({time.time() - t0:.0f}s)")
    print(f"  {'range':<10}{'weakest hand':>13}{'win rate':>10}{'95% CI':>14}{'W/D/L':>15}{'hands':>7}")
    for label, path, real_pct, last in bots:
        s = arena.summarise(path, opp, res[path], "in-process")
        p = s["pairings"]
        name = label if label == "v1" else "top %d%%" % label
        print(f"  {name:<10}{(last or '-'):>13}{100 * s['match_win_rate']:>9.1f}%"
              f"{100 * s['ci95'][0]:>8.1f}-{100 * s['ci95'][1]:<5.1f}"
              f"{str(p['win']) + '/' + str(p['draw']) + '/' + str(p['loss']):>15}{s['avg_hands']:>7.1f}")
        rows.append({"range": name, "weakest": last, "win_rate": s["match_win_rate"], "ci95": s["ci95"],
                     "pairings": p, "avg_hands": s["avg_hands"], "matches": s["matches"]})
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "allin_sweep.json"), "w") as f:
        json.dump({"pairs": args.pairs, "seed": args.seed, "rows": rows}, f, indent=1)


if __name__ == "__main__":
    main()
