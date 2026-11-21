"""Final selection: combine several result files per candidate and rank the candidates.

  python tools/final_pick.py v4=v4_U,v4_X,v4_B2 v5a=v5a_U,v5a_X,v5a_B2

Each candidate is a list of screen result tags. Later files REPLACE an
opponent's row when they use the same seed (a longer run on the same cards),
and ADD to it when the seed differs (a second block of new cards). The score is
the average points per pairing over opponents, each opponent counting once.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(tags):
    rows = {}                                   # name -> {seed: row}
    for tag in tags:
        d = json.load(open(os.path.join(ROOT, "results", f"screen_{tag}.json")))
        for r in d["screen"]["rows"]:
            by_seed = rows.setdefault(r["name"], {})
            old = by_seed.get(d["seed"])
            if old is None or r["pairs"] >= old["pairs"]:
                by_seed[d["seed"]] = r
    out = {}
    for name, by_seed in rows.items():
        w = sum(r["pairings"]["win"] for r in by_seed.values())
        dr = sum(r["pairings"]["draw"] for r in by_seed.values())
        lo = sum(r["pairings"]["loss"] for r in by_seed.values())
        out[name] = {"pairs": w + dr + lo, "win": w, "draw": dr, "loss": lo,
                     "points": (w + 0.5 * dr) / max(1, w + dr + lo),
                     "problems": sum(r["crashes"] + r["timeouts"] + r["corrected_actions"] for r in by_seed.values()),
                     "slowest": max(r["slowest_ms"] for r in by_seed.values())}
    return out


def main():
    cands = {}
    for arg in sys.argv[1:]:
        name, tags = arg.split("=")
        cands[name] = load(tags.split(","))
    common = set.intersection(*(set(c) for c in cands.values()))
    names = list(cands)
    print(f"\nFINAL SELECTION over {len(common)} opponents (points per pairing, each opponent once)")
    print("  " + f"{'opponent':<16}" + "".join(f"{n:>9}" for n in names) + f"{'pairs':>8}")
    for opp in sorted(common, key=lambda o: cands[names[-1]][o]["points"]):
        print("  " + f"{opp:<16}" + "".join(f"{cands[n][opp]['points']:>9.3f}" for n in names)
              + f"{cands[names[-1]][opp]['pairs']:>8}")
    print("  " + "-" * (16 + 9 * len(names) + 8))
    score = {n: sum(cands[n][o]["points"] for o in common) / len(common) for n in names}
    print("  " + f"{'AVERAGE':<16}" + "".join(f"{score[n]:>9.4f}" for n in names))
    for n in names:
        tot = sum(cands[n][o]["pairs"] for o in common)
        print(f"  {n}: {score[n]:.4f} over {tot:,} pairs, problems {sum(cands[n][o]['problems'] for o in common)}, "
              f"slowest {max(cands[n][o]['slowest'] for o in common)} ms")
    best = max(names, key=lambda n: score[n])
    print(f"  BEST: {best}")


if __name__ == "__main__":
    main()
