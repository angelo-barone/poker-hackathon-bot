# Changelog

Results are match win rates over duplicate pairs (same cards, seats swapped), run with `arena.py`.

## v1 (Nov 21, 10:25)

What it is: safety wrapper, preflop tables (169 x 169 hand equities and all-in-or-fold ranges for
short stacks), opponent counters, postflop equity by simulation, equity against pot odds.

| Opponent | Pairs | Match win rate | 95% CI | Pairings W/D/L |
|---|---|---|---|---|
| caller (never folds) | 250 | 95.8% | 93.7-97.2% | 229/21/0 |
| all-in every hand | 250 | 65.2% | 60.9-69.2% | 105/116/29 |
| template | 250 | 100.0% | 99.2-100% | 250/0/0 |

Reliability over 64,182 decisions: 0 crashes, 0 timeouts, 0 actions corrected by the engine.
Slowest decision 79 ms (budget 200 ms, limit 2,000 ms). Validator: passed.

## Entry folder renamed (Nov 21, 10:48)

`my_bots/v1` is now `my_bots/im_just_in_mech_eng` (the team name on the submission form). No strategy
change; only `"data_ok"` was added to the debug output. New versions are developed elsewhere and copied
in only when they beat the current entry. `sparring/v1_frozen` is the benchmark copy.

## v2 promoted to the entry (Nov 21, 12:19)

What changed: how the bot reads bets. It counts every chance the opponent had to bet and whether they
took it (flop bets, turn/river bets, raises, and big bets separately). Ordinary bets start at the minimum
defence frequency; raises and big bets start narrow. Frequency and showdown evidence move the read.
A deep stack needs a stronger hand to go in, except against a proven maniac.

| Test | v1 | v2 |
|---|---|---|
| Full field, 24 opponents, 250 pairs: points per pairing | 0.800 | 0.813 |
| smallbet_trap | 55.4% | 83.8% |
| v2 against v1 head to head | - | 56.4% |
| Four new big-bet bots, 250 pairs: points per pairing | 0.604 | 0.622 |
| valueshover / slowplayer (honest big bets) | 51.8% / 59.8% | 62.2% / 64.2% |
| earlyshover / overbet_bluffer (big-bet bluffs) | 71.8% / 58.0% | 66.2% / 56.2% |

Reliability: 0 crashes, 0 timeouts, 0 corrected actions over 1,135,101 decisions. Slowest 95 ms.
Promoted by Angelo's decision: it did not pass the "target matchups must go up" test (threebettor +1.2,
stealer +0.6, maniac 0.0, gto_charts +3.8, all inside noise), but it scored higher overall and held up
on the robustness check.

## v3 promoted to the entry (Nov 21, 13:37)

What changed: how the bot bets. The bet size now comes from the situation (street, board texture,
who acted first, how often this opponent folds), never from how strong our hand is, and bluffs use the
same sizes as value bets. When the opponent checks, the bot often takes a small stab at the pot. It
sometimes checks a strong hand to a player who bets whenever checked to, and sometimes raises as a bluff
against a player who bets almost every time. Every rate follows the counters.

| Test (250 pairs, same seeds) | v2 | v3 |
|---|---|---|
| Full field, 33 opponents: points per pairing | 0.746 | 0.797 |
| mc_exploiter | 41.4% | 48.8% |
| classifier | 58.4% | 71.8% |
| donkbettor | 51.0% | 73.8% |
| v3 against v2 head to head | - | 57.4% |
| caller / trapper / chartbot / nit / smallbet_trap | 96.6 / 91.0 / 59.4 / 99.6 / 83.2 | 96.4 / 93.8 / 74.4 / 99.4 / 94.8 |

Nine matchups rose beyond noise, none fell beyond noise (largest drop: random -4.6, noise 5.2).
Reliability: 0 crashes, 0 timeouts, 0 corrected actions over 1,713,390 decisions. Slowest 80 ms.
Passed the standing rule. A first try with smaller bets scored 0.779 and lost 7 points to random and
6.4 to lateshover; bigger sizes against players who rarely fold fixed that.

## v4 promoted to the entry (Nov 21, 14:47)

What changed: preflop and short stacks. All-in-or-fold now starts at 15 big blinds (was 12). Facing an
open shove at 25 big blinds or less, the bot calls by the equilibrium table unless that opponent shoves
clearly more or less often than equilibrium. It shoves wider against players who fold to shoves more
than they should. Calling an all-in while the blinds are small needs extra equity, taken from the exact
all-in solve and scaled by how often the opponent shoves. Open-everything threshold 0.60 -> 0.50;
re-raise starting guess 12% -> 20%.

| Test (tiered allocation, same seeds) | v3 | v4 |
|---|---|---|
| Full field, 35 opponents: points per pairing | 0.7914 | 0.7965 |
| jam20 (1,000 pairs) | 59.7% | 63.0% |
| lateshover (1,000 pairs) | 67.5% | 70.8% |
| allin / gto_charts / stealer / threebettor (1,000 pairs each) | 65.2 / 57.9 / 71.4 / 69.3 | 66.2 / 59.2 / 72.1 / 68.8 |
| nashpush (250 pairs) | 88.6% | 86.2% |
| v4 against v3 head to head (300 pairs) | - | 51.0% |
| Behind/ahead test: from 4,000 / from 16,000 chips | 35.4% / 92.6% | 39.2% / 92.9% |

Two targets rose beyond noise, four did not move, nothing fell beyond noise. Reliability: 0 crashes,
0 timeouts, 0 corrected actions over 2,502,544 decisions; stress screen clean.
Cutoff test at 150 pairs on ten opponents: 12 -> 0.697, 15 -> 0.701, 20 -> 0.698 (20 cost 4 points
against nashpush).

## v5a promoted to the entry (Nov 21, 15:57)

Two bug fixes from the fresh-eyes audit, no other change.
- A1: with a tiny stack in the small blind, the plain big blind is no longer read as a shove; the
  all-in-or-fold table is used. (1.7 big blinds behind: v4 played 18% of hands, v5a plays 100%.)
- A2: when a bigger stack bets more than we have, odds and bet-size reads use the pot we can actually
  win. (4,000 chips facing a 16,000 open shove: v4 called with 82% of hands, v5a with 2%.)

Verdict, 9,350 pairs on the same seeds: v4 0.8008 -> v5a 0.8029 points per pairing; no matchup moved
beyond noise (largest: earlyshover +4.7, oddsizer -3.7). 0 crashes, 0 timeouts, 0 corrected actions.

## Final entry: v5a (Nov 21, 17:03)

Versions tried after v5a, all rejected by same-seed verdicts:

| Version | What it added to v5a | Points per pairing | Why rejected |
|---|---|---|---|
| v5b | forgetting counters, big-raise counting, overbet defence floor, traps in position | 0.8029 -> 0.7956 | valueshover -5.2, gto_charts -4.9, smallbet_trap -2.7, all beyond noise |
| v5d | forgetting counters only | 0.8029 -> 0.7976 | earlyshover -7.3 beyond noise; switcher only +1.3 |
| v5c | big-raise counting only | 0.8038 -> 0.8025 | no target improved; overall not up |
| v5y | floor on how far early shoves cut our opens | whitebox 73.6% -> 73.4% | whitebox did not improve |
| v5x | traps in position, overbets after our checks counted separately | whitebox 73.6% -> 74.4% | whitebox did not improve clearly |

`sparring/whitebox` attacks the three habits from the audit; the entry beats it 73.6% (250 pairs).
Final checks on the entry: validator passed; 6 matches in the Docker sandbox, 828 decisions, data_ok
true on every one, none without debug data, 0 errors, 0 timeouts, slowest 40 ms.
