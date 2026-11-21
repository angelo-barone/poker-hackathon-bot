# Changelog

Results are match win rates over duplicate pairs (same cards, seats swapped), run with `arena.py`.

## v1 (Nov 21, 10:35)

What it is: safety wrapper, preflop tables (169 x 169 hand equities and all-in-or-fold ranges for
short stacks), opponent counters, postflop equity by simulation, equity against pot odds.

| Opponent | Pairs | Match win rate | 95% CI | Pairings W/D/L |
|---|---|---|---|---|
| caller (never folds) | 250 | 95.8% | 93.7-97.2% | 229/21/0 |
| all-in every hand | 250 | 65.2% | 60.9-69.2% | 105/116/29 |
| template | 250 | 100.0% | 99.2-100% | 250/0/0 |

Reliability over 64,182 decisions: 0 crashes, 0 timeouts, 0 actions corrected by the engine.
Slowest decision 79 ms (budget 200 ms, limit 2,000 ms). Validator: passed.
