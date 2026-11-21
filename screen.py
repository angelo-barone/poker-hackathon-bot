#!/usr/bin/env python3
"""Screen one bot against the whole sparring field, in parallel.

  python screen.py my_bots/im_just_in_mech_eng --pairs 100            # same pairs vs every bot
  python screen.py dev/v4 --alloc v3 --targets jam20,allin --tag v4   # tiered allocation (below)
  python screen.py dev/v4 --only allin,maniac --pairs 250

The field is bots/caller plus every folder in sparring/. Pair k uses the same
seed for every opponent and every version, so versions meet the same cards.
Prints one table, worst matchup first, and writes results/screen_<tag>.json.

Tiered allocation (--alloc REF): pairs per opponent are chosen from an earlier
result file results/screen_REF.json, so test time goes where it is needed:
  1,000 pairs  the stage's target bots (--targets), plus gto_charts and mc_exploiter
    500 pairs  the six opponents we did worst against in REF
     50 pairs  opponents we beat 90% or more in REF (a regression check)
    250 pairs  everyone else
The overall score is the average points per pairing over opponents, each
opponent counting once, as in the round robin.
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
ALWAYS_DEEP = {"gto_charts", "mc_exploiter"}


def field():
    bots = [str(Path("bots") / "caller")]
    for d in sorted((ROOT / "sparring").iterdir()):
        if (d / "bot.py").is_file():
            bots.append(str(Path("sparring") / d.name))
    return bots


def allocate(opponents, ref_tag, targets, tiers=(50, 250, 500, 1000)):
    """Pairs per opponent, from an earlier result file (see the module docstring)."""
    ref_rows = json.load(open(ROOT / "results" / f"screen_{ref_tag}.json"))["screen"]["rows"]
    ref = {r["name"]: r["match_win_rate"] for r in ref_rows}
    names = {o: Path(o).name for o in opponents}
    deep = set(targets) | ALWAYS_DEEP
    hardest = set(sorted((n for n in names.values() if n in ref), key=lambda n: ref[n])[:6])
    plan = {}
    for o, n in names.items():
        if n in deep:
            plan[o] = tiers[3]
        elif n in hardest:
            plan[o] = tiers[2]
        elif ref.get(n, 0.0) >= 0.90:
            plan[o] = tiers[0]
        else:
            plan[o] = tiers[1]
    return plan


def run(bot, plan, seed, workers, real):
    """plan: {opponent path: number of duplicate pairs}."""
    seeds = arena.pair_seeds(seed, max(plan.values()))
    jobs = [(bot, opp, seeds[k], real) for k in range(len(seeds)) for opp in plan if k < plan[opp]]
    by_opp = {opp: [] for opp in plan}
    t0 = time.time()
    with mp.Pool(workers) as pool:
        for opp, _, res in pool.imap_unordered(arena.play_pair, jobs):
            by_opp[opp].append(res)
    mode = "real" if real else "in-process"
    rows = [arena.summarise(bot, opp, by_opp[opp], mode) for opp in plan]
    rows.sort(key=lambda r: (r["match_win_rate"] if r["match_win_rate"] is not None else -1))
    return rows, round(time.time() - t0, 1)


def points(rows):
    """Average points per pairing over opponents (win 1, draw 0.5), each opponent once."""
    per = [(r["pairings"]["win"] + 0.5 * r["pairings"]["draw"]) / r["pairs"] for r in rows if r["pairs"]]
    return sum(per) / max(1, len(per))


def show(title, rows, seconds):
    print(f"\n{title}  ({seconds}s)")
    print(f"  {'opponent':<16}{'pairs':>6}{'win rate':>9}{'95% CI':>14}{'W/D/L':>14}{'adj chips/100':>15}"
          f"{'crash':>7}{'fixed':>7}{'slowest':>10}{'hands':>7}")
    for r in rows:
        p = r["pairings"]
        print(f"  {r['name']:<16}{r['pairs']:>6}{100 * r['match_win_rate']:>8.1f}%"
              f"{100 * r['ci95'][0]:>8.1f}-{100 * r['ci95'][1]:<5.1f}"
              f"{str(p['win']) + '/' + str(p['draw']) + '/' + str(p['loss']):>14}"
              f"{r['adj_chips_per_100']:>+15.0f}"
              f"{r['crashes'] + r['timeouts']:>7}{r['corrected_actions']:>7}"
              f"{r['slowest_ms']:>8.1f}ms{r['avg_hands']:>7.0f}")
    print(f"  all opponents: {sum(r['match_wins'] for r in rows)}/{sum(r['matches'] for r in rows)} matches, "
          f"{sum(r['decisions'] for r in rows):,} decisions, "
          f"{sum(r['crashes'] + r['timeouts'] for r in rows)} crashes/timeouts, "
          f"{sum(r['corrected_actions'] for r in rows)} corrected actions, "
          f"slowest {max(r['slowest_ms'] for r in rows)} ms")
    print(f"  points per pairing (average over {len(rows)} opponents): {points(rows):.4f}")
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

    def pct(wn):
        return f"{100 * wn[0] / wn[1]:.1f}% of {wn[1]}" if wn[1] else "none"
    print(f"  hands by effective stack: under 15 bb {100 * d['short_hands'] / hands:.1f}%, "
          f"15-40 bb {100 * d['zone_hands'] / hands:.1f}%, over 40 bb {100 * d['deep_hands'] / hands:.1f}%")
    print(f"  matches that reach 15-40 bb: we win {pct(d['reached'])}  "
          f"(entered ahead {pct(d['entered_ahead'])}, behind {pct(d['entered_behind'])}); "
          f"matches that never do: {pct(d['never_reached'])}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bot")
    ap.add_argument("--pairs", type=int, default=100, help="pairs vs every opponent (without --alloc)")
    ap.add_argument("--alloc", metavar="REF", help="tiered allocation from results/screen_REF.json")
    ap.add_argument("--targets", default="", help="with --alloc: comma-separated bots that get 1,000 pairs")
    ap.add_argument("--tiers", default="50,250,500,1000",
                    help="with --alloc: pairs for easy (90%%+), middle, six hardest, targets")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--only", help="comma-separated opponent names")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--tag", help="name for the results file (default: the bot folder's name)")
    args = ap.parse_args()

    opponents = field()
    if args.only:
        want = set(args.only.split(","))
        opponents = [o for o in opponents if Path(o).name in want]
    tag = args.tag or Path(args.bot).name
    if args.alloc:
        plan = allocate(opponents, args.alloc, [t for t in args.targets.split(",") if t],
                        tuple(int(x) for x in args.tiers.split(",")))
        how = f"tiered allocation from '{args.alloc}', {sum(plan.values()):,} pairs in total"
    else:
        plan = {o: args.pairs for o in opponents}
        how = f"{args.pairs} duplicate pairs each"

    rows, secs = run(args.bot, plan, args.seed, args.workers, args.real)
    show(f"SCREEN: {tag} vs {len(rows)} bots, {how}", rows, secs)
    out = {"bot": args.bot, "seed": args.seed,
           "screen": {"pairs": args.pairs if not args.alloc else None, "alloc": args.alloc,
                      "targets": args.targets, "plan": {Path(o).name: n for o, n in plan.items()},
                      "seconds": secs, "points_per_pairing": round(points(rows), 4), "rows": rows}}
    os.makedirs(ROOT / "results", exist_ok=True)
    path = ROOT / "results" / f"screen_{tag}.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\nsaved {path.relative_to(ROOT)}")
    arena.fail_loudly(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
