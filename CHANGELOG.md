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
