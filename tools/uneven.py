"""Behind/ahead test: start matches at 4,000 vs 16,000 chips, both ways.

With equal skill the chance of winning a heads-up freezeout is roughly your
share of the chips (20% from behind, 80% from ahead), so the question is how
far above those two numbers we finish.

  python tools/uneven.py --pairs 100
  python tools/uneven.py --bot dev/v4 --bots textbook_tag,lateshover
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

DEFAULT = "textbook_tag,lateshover,threebettor,adaptive,classifier,chartbot"


def job(args):
    label, pair_args = args
    return label, pair_args[1], arena.play_pair(pair_args)[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", default=os.path.join("my_bots", "im_just_in_mech_eng"))
    ap.add_argument("--bots", default=DEFAULT)
    ap.add_argument("--pairs", type=int, default=100)
    ap.add_argument("--short", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--out", default="uneven")
    args = ap.parse_args()

    big = 20_000 - args.short
    opps = [os.path.join("sparring", o) for o in args.bots.split(",")]
    seeds = arena.pair_seeds(args.seed, args.pairs)
    setups = {"behind": {"stacks": (args.short, big)}, "ahead": {"stacks": (big, args.short)}}
    jobs = [(label, (args.bot, opp, s, False, cfg)) for label, cfg in setups.items() for opp in opps for s in seeds]
    res = {(label, opp): [] for label in setups for opp in opps}
    t0 = time.time()
    with mp.Pool(args.workers) as pool:
        for label, opp, r in pool.imap_unordered(job, jobs):
            res[(label, opp)].append(r)
    share = args.short / 20_000.0
    print(f"\nBEHIND/AHEAD TEST: {args.bot}, {args.pairs} duplicate pairs each way ({time.time() - t0:.0f}s)")
    print(f"  chip share alone would give {100 * share:.0f}% from behind and {100 * (1 - share):.0f}% from ahead")
    print(f"  {'opponent':<16}{'from ' + f'{args.short:,}':>14}{'95% CI':>14}{'from ' + f'{big:,}':>14}{'95% CI':>14}")
    saved, tot = {}, {"behind": [0, 0], "ahead": [0, 0]}
    for opp in opps:
        row = {}
        for label in setups:
            s = arena.summarise(args.bot, opp, res[(label, opp)], "in-process")
            row[label] = s
            tot[label][0] += s["match_wins"]
            tot[label][1] += s["matches"]
        b, a = row["behind"], row["ahead"]
        print(f"  {b['name']:<16}{100 * b['match_win_rate']:>13.1f}%"
              f"{100 * b['ci95'][0]:>8.1f}-{100 * b['ci95'][1]:<5.1f}{100 * a['match_win_rate']:>13.1f}%"
              f"{100 * a['ci95'][0]:>8.1f}-{100 * a['ci95'][1]:<5.1f}")
        saved[b["name"]] = {"behind": b["match_win_rate"], "ahead": a["match_win_rate"],
                            "matches_each": b["matches"],
                            "problems": b["crashes"] + b["timeouts"] + b["corrected_actions"]
                            + a["crashes"] + a["timeouts"] + a["corrected_actions"]}
    lo_b, hi_b = arena.wilson(*tot["behind"])
    lo_a, hi_a = arena.wilson(*tot["ahead"])
    print(f"  {'ALL':<16}{100 * tot['behind'][0] / tot['behind'][1]:>13.1f}%{100 * lo_b:>8.1f}-{100 * hi_b:<5.1f}"
          f"{100 * tot['ahead'][0] / tot['ahead'][1]:>13.1f}%{100 * lo_a:>8.1f}-{100 * hi_a:<5.1f}")
    saved["_all"] = {"behind": tot["behind"][0] / tot["behind"][1], "ahead": tot["ahead"][0] / tot["ahead"][1],
                     "matches_each": tot["behind"][1]}
    with open(os.path.join(ROOT, "results", args.out + ".json"), "w") as f:
        json.dump(saved, f, indent=1)


if __name__ == "__main__":
    main()
