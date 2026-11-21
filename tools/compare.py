"""Old version vs new version, opponent by opponent, sorted by change.

Reads two files written by screen.py (same seeds, same pairs) and prints the
table used to decide whether a version is kept.

  python tools/compare.py baseline v2          # results/screen_baseline.json vs results/screen_v2.json

"noise" is two standard errors of the difference between two win rates
measured on this many matches. A change inside it proves nothing.
"""

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(tag):
    d = json.load(open(os.path.join(ROOT, "results", f"screen_{tag}.json")))
    return {r["name"]: r for r in d["screen"]["rows"]}, d["screen"]


def main():
    old_tag, new_tag = sys.argv[1], sys.argv[2]
    old, old_meta = load(old_tag)
    new, new_meta = load(new_tag)
    rows = []
    for name in old:
        if name not in new:
            continue
        a, b = old[name], new[name]
        p1, p2, n = a["match_win_rate"], b["match_win_rate"], min(a["matches"], b["matches"])
        noise = 2 * math.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)
        rows.append((p2 - p1, name, a, b, noise))
    rows.sort(key=lambda r: r[0])
    print(f"\n{old_tag} -> {new_tag}   ({old_meta['pairs']} vs {new_meta['pairs']} pairs per opponent, same seeds)")
    print(f"  {'opponent':<14}{'old':>7}{'new':>7}{'change':>8}{'noise':>7}  {'verdict':<8}"
          f"{'old W/D/L':>12}{'new W/D/L':>12}{'adj old':>9}{'adj new':>9}")
    for diff, name, a, b, noise in rows:
        verdict = "UP" if diff > noise else ("DOWN" if diff < -noise else "same")
        pa, pb = a["pairings"], b["pairings"]
        print(f"  {name:<14}{100 * a['match_win_rate']:>6.1f}%{100 * b['match_win_rate']:>6.1f}%"
              f"{100 * diff:>+7.1f} {100 * noise:>5.1f}   {verdict:<8}"
              f"{str(pa['win']) + '/' + str(pa['draw']) + '/' + str(pa['loss']):>12}"
              f"{str(pb['win']) + '/' + str(pb['draw']) + '/' + str(pb['loss']):>12}"
              f"{a.get('adj_chips_per_100', 0):>+9.0f}{b.get('adj_chips_per_100', 0):>+9.0f}")
    for tag, table in ((old_tag, old), (new_tag, new)):
        rs = list(table.values())
        m, w = sum(r["matches"] for r in rs), sum(r["match_wins"] for r in rs)
        pts = sum(r["pairings"]["win"] + 0.5 * r["pairings"]["draw"] for r in rs)
        prs = sum(r["pairs"] for r in rs)
        print(f"  {tag}: {100 * w / m:.1f}% of {m} matches, {pts / prs:.3f} points per pairing, "
              f"{sum(r['crashes'] + r['timeouts'] for r in rs)} crashes/timeouts, "
              f"{sum(r['corrected_actions'] for r in rs)} corrected, slowest {max(r['slowest_ms'] for r in rs)} ms")


if __name__ == "__main__":
    main()
