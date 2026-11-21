#!/usr/bin/env python3
"""Screen one bot against the whole sparring field, in parallel.

  python screen.py my_bots/im_just_in_mech_eng --pairs 100                 # quick screen vs every bot
  python screen.py my_bots/im_just_in_mech_eng --pairs 100 --deep 4        # then 250 pairs on the 4 worst
  python screen.py my_bots/im_just_in_mech_eng --only allin,maniac --pairs 250

The field is bots/caller plus every folder in sparring/. Pair k uses the same
seed for every opponent and every version, so versions meet the same cards.
Prints one table, worst matchup first, and writes results/screen_<tag>.json.
"""

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import arena

ROOT = Path(__file__).resolve().parent


def field():
    bots = [str(Path("bots") / "caller")]
    for d in sorted((ROOT / "sparring").iterdir()):
        if (d / "bot.py").is_file():
            bots.append(str(Path("sparring") / d.name))
    return bots


def run(bot, opponents, pairs, seed, workers, real):
    seeds = arena.pair_seeds(seed, pairs)
    jobs = [(bot, opp, s, real) for s in seeds for opp in opponents]     # interleaved by opponent
    by_opp = {opp: [] for opp in opponents}
    t0 = time.time()
    with mp.Pool(workers) as pool:
        for opp, _, res in pool.imap_unordered(arena.play_pair, jobs):
            by_opp[opp].append(res)
    mode = "real" if real else "in-process"
    rows = [arena.summarise(bot, opp, by_opp[opp], mode) for opp in opponents]
    rows.sort(key=lambda r: (r["match_win_rate"] if r["match_win_rate"] is not None else -1))
    return rows, round(time.time() - t0, 1)


def show(title, rows, seconds):
    print(f"\n{title}  ({seconds}s)")
    print(f"  {'opponent':<14}{'win rate':>9}{'95% CI':>14}{'W/D/L':>13}{'adj chips/100':>15}{'crash':>7}"
          f"{'fixed':>7}{'slowest':>10}{'hands':>7}")
    for r in rows:
        p = r["pairings"]
        print(f"  {r['name']:<14}{100 * r['match_win_rate']:>8.1f}%"
              f"{100 * r['ci95'][0]:>8.1f}-{100 * r['ci95'][1]:<5.1f}"
              f"{str(p['win']) + '/' + str(p['draw']) + '/' + str(p['loss']):>13}"
              f"{r['adj_chips_per_100']:>+15.0f}"
              f"{r['crashes'] + r['timeouts']:>7}{r['corrected_actions']:>7}"
              f"{r['slowest_ms']:>8.1f}ms{r['avg_hands']:>7.0f}")
    tot_m = sum(r["matches"] for r in rows)
    tot_w = sum(r["match_wins"] for r in rows)
    print(f"  all opponents: {tot_w}/{tot_m} matches = {100 * tot_w / max(tot_m, 1):.1f}%, "
          f"{sum(r['decisions'] for r in rows):,} decisions, "
          f"{sum(r['crashes'] + r['timeouts'] for r in rows)} crashes/timeouts, "
          f"{sum(r['corrected_actions'] for r in rows)} corrected actions, "
          f"slowest {max(r['slowest_ms'] for r in rows)} ms")
    pts = sum(r["pairings"]["win"] + 0.5 * r["pairings"]["draw"] for r in rows)
    print(f"  points per pairing: {pts / max(1, sum(r['pairs'] for r in rows)):.4f}")
    d = {}
    for r in rows:
        for k, v in r["depth"].items():
            if isinstance(v, list):
                cur = d.setdefault(k, [0, 0])
                cur[0] += v[0]
                cur[1] += v[1]
            else:
                d[k] = d.get(k, 0) + v
    hands = max(1, d["short_hands"] + d["zone_hands"] + d["deep_hands"])
    pct = lambda wn: f"{100 * wn[0] / wn[1]:.1f}% of {wn[1]}" if wn[1] else "none"
    print(f"  hands by effective stack: under 15 bb {100 * d['short_hands'] / hands:.1f}%, "
          f"15-40 bb {100 * d['zone_hands'] / hands:.1f}%, over 40 bb {100 * d['deep_hands'] / hands:.1f}%")
    print(f"  matches that reach 15-40 bb: we win {pct(d['reached'])}  "
          f"(entered ahead {pct(d['entered_ahead'])}, even {pct(d['entered_even'])}, "
          f"behind {pct(d['entered_behind'])}); matches that never do: {pct(d['never_reached'])}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bot")
    ap.add_argument("--pairs", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--only", help="comma-separated opponent names")
    ap.add_argument("--deep", type=int, default=0, help="then rerun this many worst matchups")
    ap.add_argument("--deep-pairs", type=int, default=250)
    ap.add_argument("--skip-deep", default="v1_frozen",
                    help="names left out of the deep rerun (a mirror match is ~50% by design)")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--tag", help="name for the results file (default: the bot folder's name)")
    args = ap.parse_args()

    opponents = field()
    if args.only:
        want = set(args.only.split(","))
        opponents = [o for o in opponents if Path(o).name in want]
    tag = args.tag or Path(args.bot).name
    out = {"bot": args.bot, "seed": args.seed}

    rows, secs = run(args.bot, opponents, args.pairs, args.seed, args.workers, args.real)
    show(f"SCREEN: {tag} vs {len(rows)} bots, {args.pairs} duplicate pairs each", rows, secs)
    out["screen"] = {"pairs": args.pairs, "seconds": secs, "rows": rows}
    all_rows = list(rows)

    if args.deep:
        skip = set(args.skip_deep.split(","))
        worst = [r["opponent"] for r in rows if r["name"] not in skip][:args.deep]
        rows2, secs2 = run(args.bot, worst, args.deep_pairs, args.seed, args.workers, args.real)
        show(f"DEEP: {tag} vs its {len(worst)} worst matchups, {args.deep_pairs} pairs each", rows2, secs2)
        out["deep"] = {"pairs": args.deep_pairs, "seconds": secs2, "rows": rows2}
        all_rows += rows2

    os.makedirs(ROOT / "results", exist_ok=True)
    path = ROOT / "results" / f"screen_{tag}.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\nsaved {path.relative_to(ROOT)}")
    arena.fail_loudly(all_rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
