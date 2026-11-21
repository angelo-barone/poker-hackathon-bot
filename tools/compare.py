"""Old version vs new version, opponent by opponent, sorted by change.

Reads two files written by screen.py (same seeds) and prints the table used to
decide whether a version is kept. Only opponents present in both files count.

  python tools/compare.py v3_alloc v4          # results/screen_v3_alloc.json vs results/screen_v4.json

"noise" is two standard errors of the difference between two win rates
measured on this many matches. A change inside it proves nothing.
The overall score is the average points per pairing over opponents, each
opponent counting once.
"""

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(tag):
    d = json.load(open(os.path.join(ROOT, "results", f"screen_{tag}.json")))
    return {r["name"]: r for r in d["screen"]["rows"]}


def ppp(r):
    return (r["pairings"]["win"] + 0.5 * r["pairings"]["draw"]) / r["pairs"]


def main():
    old_tag, new_tag = sys.argv[1], sys.argv[2]
    old, new = load(old_tag), load(new_tag)
    rows = []
    for name in old:
        if name not in new:
            continue
        a, b = old[name], new[name]
        p1, p2 = a["match_win_rate"], b["match_win_rate"]
        noise = 2 * math.sqrt(p1 * (1 - p1) / a["matches"] + p2 * (1 - p2) / b["matches"])
        rows.append((p2 - p1, name, a, b, noise))
    rows.sort(key=lambda r: r[0])
    print(f"\n{old_tag} -> {new_tag}   ({len(rows)} opponents in both, same seeds)")
    print(f"  {'opponent':<16}{'pairs':>6}{'old':>7}{'new':>7}{'change':>8}{'noise':>7}  {'verdict':<8}"
          f"{'old W/D/L':>13}{'new W/D/L':>13}{'adj old':>9}{'adj new':>9}")
    for diff, name, a, b, noise in rows:
        verdict = "UP" if diff > noise else ("DOWN" if diff < -noise else "same")
        pa, pb = a["pairings"], b["pairings"]
        pairs = str(b["pairs"]) if a["pairs"] == b["pairs"] else f"{a['pairs']}/{b['pairs']}"
        print(f"  {name:<16}{pairs:>6}{100 * a['match_win_rate']:>6.1f}%{100 * b['match_win_rate']:>6.1f}%"
              f"{100 * diff:>+7.1f} {100 * noise:>5.1f}   {verdict:<8}"
              f"{str(pa['win']) + '/' + str(pa['draw']) + '/' + str(pa['loss']):>13}"
              f"{str(pb['win']) + '/' + str(pb['draw']) + '/' + str(pb['loss']):>13}"
              f"{a.get('adj_chips_per_100', 0):>+9.0f}{b.get('adj_chips_per_100', 0):>+9.0f}")
    for tag, table in ((old_tag, old), (new_tag, new)):
        rs = [table[name] for _, name, _, _, _ in rows]
        print(f"  {tag}: {sum(ppp(r) for r in rs) / len(rs):.4f} points per pairing (average over "
              f"{len(rs)} opponents), "
              f"{sum(r['crashes'] + r['timeouts'] for r in table.values())} crashes/timeouts, "
              f"{sum(r['corrected_actions'] for r in table.values())} corrected, "
              f"slowest {max(r['slowest_ms'] for r in table.values())} ms")


if __name__ == "__main__":
    main()
