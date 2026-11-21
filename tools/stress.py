"""Stress screen: short runs under odd conditions, checking only that the bot
never crashes, never times out and never has an action corrected by the engine.
Win rates are not the point here.

  python tools/stress.py                       # the entry
  python tools/stress.py --bot dev/v4 --pairs 5
"""

import argparse
import multiprocessing as mp
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import arena  # noqa: E402

CONDITIONS = [
    ("turbo blinds (10 hands a level)", {"blinds": "turbo"}),
    ("slow blinds (40 hands a level)", {"blinds": "slow"}),
    ("very short: 3 big blinds each", {"stack": 150}),
    ("short: 10 big blinds each", {"stack": 500}),
    ("very deep: 2,000 big blinds each", {"stack": 100_000}),
    ("flat 500/1000 blinds with a 100 ante", {"blinds": "500/1000/100"}),
    ("odd chip counts: 10,037 each", {"stack": 10_037}),
    ("uneven: we start with 300 of 20,000", {"stacks": (300, 19_700)}),
    ("uneven: we start with 19,700 of 20,000", {"stacks": (19_700, 300)}),
]
OPPONENTS = ["random", "allin", "maniac", "aggressor", "minraiser", "potbettor", "mc_exploiter",
             "jam20", "earlyshover", "oddsizer", "nashpush", "switcher"]


def job(args):
    label, pair_args = args
    return label, arena.play_pair(pair_args)[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", default=os.path.join("my_bots", "im_just_in_mech_eng"))
    ap.add_argument("--pairs", type=int, default=5)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()

    opps = [os.path.join("sparring", o) for o in OPPONENTS] + [os.path.join("bots", "caller")]
    seeds = arena.pair_seeds(args.seed, args.pairs)
    jobs = [(label, (args.bot, opp, s, False, cfg)) for label, cfg in CONDITIONS for opp in opps for s in seeds]
    res = {label: [] for label, _ in CONDITIONS}
    t0 = time.time()
    with mp.Pool(args.workers) as pool:
        for label, r in pool.imap_unordered(job, jobs):
            res[label].append(r)
    print(f"\nSTRESS SCREEN: {args.bot} vs {len(opps)} opponents, {args.pairs} pairs each per condition "
          f"({time.time() - t0:.0f}s)")
    print(f"  {'condition':<42}{'matches':>8}{'decisions':>11}{'crashes':>9}{'timeouts':>9}{'corrected':>10}"
          f"{'no data':>8}{'slowest':>10}{'hand cap':>9}")
    bad = 0
    for label, _ in CONDITIONS:
        s = arena.summarise(args.bot, "mixed", res[label], "in-process")
        problems = s["crashes"] + s["timeouts"] + s["corrected_actions"] + s["data_bad"] + s["runner_crashes"]
        bad += problems
        print(f"  {label:<42}{s['matches']:>8}{s['decisions']:>11,}{s['crashes']:>9}{s['timeouts']:>9}"
              f"{s['corrected_actions']:>10}{s['data_bad']:>8}{s['slowest_ms']:>8.1f}ms"
              f"{s['hand_limit_matches']:>9}")
        for e in s["examples"][:3]:
            print("      problem:", e)
        for tb in s["runner_crash_text"]:
            print("      RUNNER CRASH:", tb)
    print("  RESULT:", "clean" if bad == 0 else f"{bad} PROBLEMS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
