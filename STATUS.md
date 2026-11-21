# STATUS (newest at the top)

**Standing rule for every change:** keep it only if it improves the target matchups over 250 pairs on the
same seeds and no other matchup in the full field drops by more than noise.

**Scoring confirmed by the organisers (12:00):** a pairing is worth 2 for a win, 1 for a draw, 0 for a loss.
Our "points per pairing" (1 / 0.5 / 0) is the same metric at half scale, and stays the deciding number.

## 17:49 — FINAL STATE after the last test round

- 17:46 commit `59352a3` pushed to main: the eight hybrid sparring bots, frozen v3 and v4, the results of this round, and this STATUS.md (copied into the repo as `STATUS.md`). Working tree clean, 0 uncommitted files, 0 unpushed commits.
- The entry has 0 differences from the tag `safe-v5a`. No code in `my_bots/` was touched in this round. No further code commits are planned; only STATUS.md may still be updated.

**Final state in one paragraph**
The submitted bot is v5a in `my_bots/im_just_in_mech_eng`, public on GitHub at commit `59352a3` and marked by the tag `safe-v5a`. It is the last version that passed a same-seed verdict: v4's strategy (reading bets by how often an opponent makes them, bet sizes set by the situation, small stabs, all-in-or-fold from 15 big blinds, caution with early all-ins) plus two bug fixes from an independent audit. It scores 0.803 points per pairing against 35 sparring bots, wins 88% and 96% of matches against two real bots from the London event, 74% against an attacker written from its own audit, and at least 62% against each of eight further hybrid styles tested in the last round. Across more than 14 million test decisions and 36 Docker sandbox matches it has never crashed, timed out, sent an action the engine had to correct, or lost its data tables, and its slowest decision on half a CPU core was 48 ms against a 2,000 ms limit. A second independent safety audit found no bug the tournament can reach. Six later candidates (v5b, v5d, v5c, Fix Y, Fix X, v5e) were tested and rejected. Its weakest known matchups are bots that play like itself (a coin flip), mc_exploiter (about 51%), jam20, gto_charts and stack_bully (about 60 to 62%), and the all-in bot (about 66%).

## 17:46 — Last test round (coach, 17:38): hybrids and frozen versions. Test only, entry unchanged

- 17:42 eight hybrid sparring bots built with `tools/make_sparring.py` and validated: limp_trapper, delayed, min_better, checkraiser, phase_shifter, rare_overbet_bluffer, stack_bully, math_maniac. phase_shifter is close to the existing switcher but switches at hand 40 instead of 15, so it was kept. Frozen copies `sparring/v3_frozen` and `sparring/v4_frozen` added next to `v2_frozen`.
- 17:42 to 17:45 entry (v5a) against all eleven, 100 duplicate pairs each (156 s).

| Opponent | Match win rate | 95% CI | Pairings W/D/L | Luck-adjusted bb/100 |
|---|---|---|---|---|
| v4_frozen | 46.0% | 39.2-52.9 | 11/70/19 | -6.8 |
| v3_frozen | 53.5% | 46.6-60.3 | 17/73/10 | +7.3 |
| v2_frozen | 60.0% | 53.1-66.5 | 28/64/8 | +16.4 |
| stack_bully | 62.5% | 55.6-68.9 | 36/53/11 | +95.4 |
| delayed | 64.0% | 57.1-70.3 | 38/52/10 | +63.7 |
| phase_shifter | 66.5% | 59.7-72.7 | 45/43/12 | +60.4 |
| rare_overbet_bluffer | 76.5% | 70.2-81.8 | 57/39/4 | +57.4 |
| checkraiser | 80.5% | 74.5-85.4 | 62/37/1 | +180.7 |
| limp_trapper | 80.5% | 74.5-85.4 | 62/37/1 | +67.3 |
| math_maniac | 89.5% | 84.5-93.0 | 79/21/0 | +730.7 |
| min_better | 90.0% | 85.1-93.4 | 80/20/0 | +667.6 |

- **Reliability: 0 crashes, 0 timeouts, 0 corrected actions, 0 decisions without debug data** over 249,807 decisions. Slowest decision 44 ms.
- No hybrid is under 60%. The bot built on our known blind spot, rare_overbet_bluffer, loses to us 76.5% to 23.5%: one bluff in eight rivers is too rare to pay for the rest of its game.
- Under 60%, where the chips go (17:45, 100 more pairs each):
  - v4_frozen (46.0%): a near mirror, since v5a is v4 plus two bug fixes. Everything is symmetric: we lose 115 bb/100 folding to its bets and win 111 from its folds to ours; all-ins split 49% and 51%. The gap from 50% is inside the noise of 200 matches (the full-field verdict had v5a ahead of v4, 0.8029 to 0.8008).
  - v3_frozen (53.5%): the same picture, +8.6 bb/100 overall; the largest single cost is our big blind facing its raises (-17.9 bb/100).
- Nothing was fixed or changed. The entry is still v5a.

### For the live round and next build
Matchups under 55%, from this round and from the 500-pair verdict runs:
- **Our own earlier versions** (v4_frozen 46.0%, v3_frozen 53.5% at 100 pairs): against a bot that plays like us we are a coin flip. Any other team that built a similar "read the frequencies, stab small, all-in-or-fold when short" bot will be a coin flip too, and the live bracket is single matches.
- **mc_exploiter** (51.0% over 500 pairs): a bot that reads our bet size and folds to big bets while calling small ones. If a live opponent folds to every big bet and calls every small one, expect a long, even match.
- Close to the line, for awareness: gto_charts about 61%, jam20 about 62%, stack_bully 62.5%, delayed 64.0%, all-in bot about 66%.
- Ideas for a next build, none tested: bet-size choice that keeps big bets for value (v5e's version failed), a wider calling range against proven all-in bots (the solver's ceiling is 69.8%), and a way to tell an honest overbet from a bluffed one without a blanket rule.

## 17:35 — FINAL STATE: v5a is the entry. Job 3 (v5e) failed and is not promoted

**Job 3 verdict (finished 17:32, same seeds and the same 35 opponents as the v5a run)**
- v5a 0.8029 -> **v5e 0.7766 points per pairing** (-0.026). The bar was +0.005. 0 crashes, 0 timeouts, 0 corrected actions, no decision without debug data, slowest 123 ms.
- Seven matchups fell beyond noise: slowplayer 96.0% -> 78.0% (-18.0), overbet_bluffer 83.6% -> 66.3% (-17.3), donkbettor 79.0% -> 66.0% (-13.0), trapper 94.0% -> 82.0% (-12.0), smallbet_trap 94.1% -> 85.8% (-8.3), valueshover 79.9% -> 72.1% (-7.8), jam20 61.9% -> 56.8% (-5.1).
- mc_exploiter 51.0% -> 55.2% (+4.2, noise 4.5): the target moved the right way but inside noise. gto_charts +1.5.
- Reading: the one-step calculation almost always chose half pot. Against opponents who call or trap with strong hands, that gave up the value of the bigger turn and river bets and made bluffs cheaper but more frequent. It is rejected. Its run against the London bots was skipped because the verdict had already failed.

**Final checks, 17:33**
- `my_bots/im_just_in_mech_eng/bot.py` is byte-for-byte `dev/v5a/bot.py` and has 0 differences from the tag `safe-v5a`. Validator: passed.
- The entry has not changed since its Docker sandbox check at 17:01 (6 matches, 828 decisions, `data_ok` true on all, slowest 40 ms), so that check still stands and was not repeated.
- Git: commit `7a52873` (17:33) pushed to main; working tree clean, 0 uncommitted files, 0 unpushed commits; tag `safe-v5a` is on GitHub. `sparring/london_bouillie` is excluded from git (no licence).
- No code edits were made to the entry in this stretch. Edits stop at 17:55 and none are planned.

**Final state in one paragraph**
The submitted bot is v5a in `my_bots/im_just_in_mech_eng`, public on GitHub at commit `7a52873` with the tag `safe-v5a`. It is the last version that passed a same-seed verdict: v4's strategy (reading bets by how often an opponent makes them, bet sizes set by the situation, small stabs, all-in-or-fold from 15 big blinds, and caution with early all-ins) plus two bug fixes from an independent audit. It scores 0.803 points per pairing against 35 sparring bots, beats two real bots from the London event 88% and 96% of the time, and beats an attacker written from its own audit 74% of the time. Over more than 14 million test decisions and 36 sandbox matches it has not crashed, timed out, or had an action corrected, and its slowest decision on half a CPU core was 48 ms against a 2,000 ms limit. Six later candidates (v5b, v5d, v5c, Fix Y, Fix X, v5e) were tested and rejected. Its weakest known matchups are mc_exploiter (about 51%), jam20 and gto_charts (about 60%), and the all-in bot (about 66%).

## 17:24 — Job 2 result: the entry beats both London bots clearly

Entry (v5a), 250 duplicate pairs each (finished 17:22, 334 s on 3 cores, 0 crashes):

| Opponent | Match win rate | Hands | Overall |
|---|---|---|---|
| london_lucashsu (their final bot, 5th at the London finals) | **88.4%** | 43,031 | +56 bb/100 |
| london_bouillie (their final candidate, adapted for rising blinds) | **96.2%** | 46,771 | +62 bb/100 |

Where the chips go (big blinds per 100 hands):
- vs london_lucashsu: our opens that they fold to +29.5 (29 hands per 100); their folds to our bets after the flop +56.4; their folded small blinds +6.0. We give back -30.6 folding to their bets (we fold to 64% of the bets we face) and -3.6 when they re-raise our opens (we fold 94%). Preflop all-ins: we win 44% against a deserved 45%, about level.
- vs london_bouillie: it folds its small blind 44 times per 100 hands (+22.1) and folds to our opens 26 times per 100 (+26.1); our bets after the flop +28.4. We give back -24.0 folding to its bets.
- Reading: both were built for a 6-player event. Heads-up they fold far too many blinds, and our stealing and stabbing take those pots. They are useful as a check that nothing surprises us, not as a measure of how strong the heads-up field here is.

## 17:22 — Job 1 done (safety audit: 0 reachable bugs). Job 2: both London bots usable, matches running

**Job 1: fresh safety audit of the final bot.py (v5a), unedited**

> **Result: no bug found that the tournament can reach, as the README describes the game state.** Two failures reproduced, both only in states the README rules out. One point could not be checked without reading the engine.
>
> **Needs one look at the engine (read, not run)**
> - Lines 945-946 (also 559, 893): when our stack is at or below `amount_owed`, the bot sends `call`, never `all_in`. Example: we are small blind at 50/100 with 20 chips behind, owed 50; the push/fold branch says shove and `_legal` turns it into `call`. The README only says a short `all_in` is a call for all our chips; it does not say what a short `call` does. Probably fine, but confirm the engine does not treat it as a fold.
>
> **Reproduced only in out-of-spec states (ran it)**
> - Lines 461-467: if both seats carry the same `bot_id` (self-play), `opp` is None, `_context` raises TypeError and every decision becomes check/fold. Ran it: AA in the small blind folded. This cannot happen between two different bots; it only matters if the organisers' post-deadline sandbox match pits the bot against itself.
> - Lines 476 and 888: if `pot` did not include the opponent's current bet, the adjusted pot goes negative.
>   - Flop, pot 7000, opponent all-in 9000, our stack 1000: adjusted pot -1000, ZeroDivisionError, fold.
>   - Same spot with pot 500: adjusted pot -7500, negative odds, calls with 72o.
>   - The README says `pot` includes the current street's bets. Then the adjusted pot is at least 2 × our bet + our stack, so always positive.
>
> **(a) `_context`: tested, fine**
> - Opponent all-in for more than our stack, preflop and flop (shove 9000 into 1000, we hold 500: pot 1500, owed 500, odds 0.25): fine.
> - Opponent raises above our stack without being all-in: fine.
> - Our stack exactly equal to owed: fine.
> - Our stack 1 chip: fine.
> - Our stack 0: returns call, harmless.
> - Opponent all-in for less than our bet: check.
> - Antes in the pot: fine.
> - Every division by `c["pot"]` or `c["owed"]` is guarded or provably positive. The raise and bet sizing branches are only reached when nothing is unmatched.
>
> **(b) `_preflop`: tested, fine**
> - Opponent all-in from posting the big blind (exactly 100, short 60, short 30), under both possible `amount_owed` conventions: `vs_blind_all_in` calls, never crashes. The price never exceeds 0.25 and the worst hand has 0.323 equity, so it never folds there.
> - Opponent all-in from the ante with a zero blind: call or check.
> - Opponent all-in posting the small blind while we are big blind: check.
> - We are small blind with stack below owed, opponent not all-in (stacks 20, 1, 50, and 10 at 1000/2000 with ante 200): goes to push/fold, no exception.
> - Depths below 1 big blind clamp to table key "1", which exists; "0.5" does not and is never requested.
>
> **Fuzz (ran it)**
> - 14,000 hand-built states: 7,000 preflop, 7,000 postflop, stacks from 1 to 19,999 chips, five blind levels with and without antes, randomised opponent counters.
> - 0 exceptions inside `_think`, and every reply carried `debug`.
> - 0 illegal replies: no check when owed, no fold or call when free, every raise at or above `min_raise_to` and affordable, no raise into an all-in opponent, all JSON-serialisable.
>
> **Time (ran it)**
> - Worst decision was 45 ms on a full core, with the tightest read (best of 12 hands, 1,500 samples). The simulation stops on a 170 ms wall-clock deadline.
> - Warmup 1 ms; one showdown digest 0.4 ms.
> - The venv runs Python 3.10.22.
>
> **README rules (read, validator not run)**
> - No eval/exec/compile/`__import__`, no file writes, no subprocess, threads or network.
> - The data file is read once at import. Imports are stdlib plus eval7.
>
> CONFIRMED BUGS: 0 reachable under the README's rules (2 reproduced only in out-of-spec states: same bot_id on both seats; pot excluding the opponent's bet)

**My notes on it (separate from the report)**
- The one open point is settled by the engine code read this morning: a `call` with fewer chips than owed is played as a call for everything we have (the engine pays `min(owed, stack)` and marks us all-in). It is not a fold. No action of ours has been corrected in over 14 million test decisions.
- Same `bot_id` on both seats: the kit's own `play.py` renames a second copy (`name_2`), so two seats never share an id there, and in the round robin every team has its own name. Even if it happened the bot would check or fold, not crash.
- **Decision:** nothing is a confirmed reachable bug, so by the coach's rule nothing is changed. v5a stays as it is.

**Job 2: the two London repos (17:11 to 17:17)**
- A subagent inspected both read-only; I then checked both bot files myself for imports and risky calls (none: no file access, network, subprocess, eval, threads). Nothing from those repos was run except through our confined validator and confined bot processes.
- lucashsu: the checkout has no files on Windows (file names Windows cannot create), so the bot was read out of git. Final submitted bot per its README: `hero_bots/bot_v16_squeeze_C_metacap/bot.py` (5th at their finals), 3,528 lines, imports math/random/time/zlib/eval7, no data folder. Licence MIT. Added unmodified as `sparring/london_lucashsu` with `sparring/LONDON_LUCASHSU_NOTICE.txt`.
- bouillie: final candidate per its README: `mybot_13_25_fold_to_raise_v1/bot.py`, 1,106 lines, imports eval7 only. Built for 6 players and fixed 50/100 blinds. Two small adaptations applied to our copy (opening size uses the current big blind; antes are not counted as actions). **No licence in the repo for the author's bots**, so it is kept as `sparring/london_bouillie` on this laptop only and excluded from git; it is not redistributed.
- Both passed our validator and played 4 confined matches each with 0 crashes, 0 timeouts, 0 corrected actions (their think time: 4.7 ms and 0.3 ms a decision).
- The subagent's own attempt to run the validator was refused by the permission check; it reported that and stopped. I ran the validator myself, as the coach's instruction asks for it.
- 17:17 entry (v5a) vs both, 250 pairs each with the chip breakdown, running on 3 cores beside the v5e verdict.

## 17:15 — Last stretch started (coach, 17:10): safe tag pushed, three jobs running

- 17:11 `git tag safe-v5a` on commit `c859a9e` and pushed; `git ls-remote` confirms the tag on GitHub. v5a ships unless a new version passes.
- Clock for this stretch: code edits stop 17:55, last push 18:15, no commits after 18:30.
- **Job 1 (safety audit of v5a):** fresh subagent with no context started 17:12. It reads only the README and the entry, and looks only for crash, timeout, illegal-action and rule risks, hardest at the A1 and A2 lines.
- **Job 2 (London bots):** both repos cloned at 17:11 into a scratch folder outside the repo (lucashsu 3 MB, bouillie 530 MB). A second subagent is inspecting them read-only (it may only run our confined validator) and will say whether each has a usable `bot.py`, whether anything in it is unsafe, and what licence it carries. Their code is untrusted: nothing from those folders is executed directly.
- **Job 3 (v5e):** built in `dev/v5e`, validator passed. Once we have seen the opponent face a size at least 6 times, that size can replace the situation's size when it is worth more for the hand, by a one-step calculation (they fold with their observed frequency, otherwise call with the better part of their hands). A size not yet seen 6 times is never chosen this way; before that the sizes are exactly v5a's.
- **Decision:** my first reading required 6 observations of both the small and the normal size before any switch. In 4 test matches that never triggered, so the candidate would have been identical to v5a. I changed it to "6 observations of the size being chosen", which is what the instruction says; the situation's own size is still valued with v5a's existing estimate. In 40 test matches it now switches often against mc_exploiter, gto_charts and chartbot, almost always to half pot, and never against maniac.
- v5e verdict run started 17:14 on the same seeds and the same 35 opponents as the v5a run; expected about 17:33. The bar: overall up by at least 0.005, mc_exploiter not down, nothing beyond noise.

## 17:03 — FINAL: entry is v5a, validated, sandbox-checked, committed and pushed

**State of the submission**
- Entry: `my_bots/im_just_in_mech_eng/bot.py` = v5a (v4 plus the two audit bug fixes), with `data/preflop.json`. It is the last version that passed a same-seed verdict.
- Git: working tree clean, 0 uncommitted files, 0 unpushed commits. Latest commit on main: `c859a9e` (17:01). The entry itself has not changed since `a97eac2` (15:55).
- Validator: passed.
- Docker sandbox, 6 matches (whitebox, gto_charts, mc_exploiter, allin, smallbet_trap, jam20): all finished, 828 decisions, `data_ok` true on every one, none without debug data, 0 errors, 0 timeouts, 0 restarts. Think time: average 2.3 ms, 95th percentile 5.2 ms, slowest 39.6 ms. Load 347 ms. Docker Desktop is quit.
- Remaining clock: edits allowed until 17:45, last push 18:05, no commits after 18:30. Nothing further is needed for the entry.

**Coach's 16:58 plan, step by step**
1. 16:58 the separate final-selection run was stopped (the entry is simply the last version that passed).
2. 17:00 `sparring/whitebox` built from the audit's three habits: raises to 35 to 45% of our stack without going all-in (as an open with decent hands and as a re-raise over our opens), overbets 1.1 to 1.3 pot whenever we check, shoves over our first four opens and then plays tight-aggressive.
3. 17:00 entry vs whitebox, 250 pairs: **73.6% match win rate** (95% CI 69.6-77.3), pairings 131/106/13, +103 bb/100, 0 crashes.
4. Where the chips go against whitebox (per 100 hands): we fold 91% of our big blinds to its huge raises and still make +30 bb/100 in that spot, because the hands we continue with win its whole raise; our opens that it shoves over: we fold 92%, +29 bb/100; we fold our small blind 17 times per 100 hands instead of the usual 10 (-9 bb/100), which is the audit's B3 effect and is small; its overbets after our checks cost almost nothing (we face 8.6 postflop bets per 100 hands, fold to 29%, and the bet-facing lines net about -1 bb/100). The three habits are real but an attacker built on them loses, because risking 35 to 45% of a stack to steal blinds is too expensive when we do wake up with a hand.
5. 17:00 Fix Y (never open fewer than the better half of small blinds unless 5 of our last 10 opens and 2 of the last 3 were shoved on): whitebox 73.6% -> 73.4%. Not a clear improvement, so it is dropped; its tiered verdict run was stopped at 17:00 to save the clock.
6. 17:00 Fix X (check behind in position with a strong hand 12% of the time; overbets right after our checks counted separately and read as bluff-heavy above 40%): whitebox 73.6% -> 74.4% (noise about 5.5). Not a clear improvement, so it is dropped without a tiered verdict.
7. 17:01 final checks and push, as above.

**Decision log for this stretch**
- Stopping two test runs early (final-selection block and Fix Y verdict) was deliberate: the coach's rule needs whitebox to improve clearly first, and neither fix did.
- A blanket "stop every python process" command was refused by the safety check; only this project's test workers were stopped instead (there were none left).
- Item (g), the bigger simulation budget, was never applied: no test slot, and it is not needed (slowest sandbox decision 40 ms, no decision anywhere near the limit).

**What the day produced**

| Version | Change | Points per pairing vs previous | Kept |
|---|---|---|---|
| v1 | wrapper, preflop tables, equity vs pot odds | first baseline | yes |
| v2 | read bets by frequency and size | 0.800 -> 0.813 (24 opponents) | yes |
| v3 | bet sizes from the situation, stabs, traps | 0.746 -> 0.797 (33 opponents) | yes |
| v4 | preflop and short stacks, all-in premium | 0.7914 -> 0.7965 (35 opponents) | yes |
| v5a | audit fixes A1 and A2 | 0.8008 -> 0.8029 | yes, final |
| v5b, v5d, v5c, v5y, v5x | robustness ideas | lower or no gain | no |

**Known weak spots of the final entry** (for Angelo's explanation, not to be changed now)
- mc_exploiter about 51 to 53%, gto_charts about 60%, allin about 66% (ceiling 69.8%), jam20 about 62%.
- Counters never forget, so an opponent who changes style mid-match is read slowly (switcher 72.5% against 84% for the plain maniac it becomes). Forgetting was tested and cost more than it gained.
- Bets just over the pot from an opponent who rarely makes them are believed. A blanket defence against that was tested and lost to honest big-bettors.

## 16:57 — v5c verdict: no gain, not promoted. Strategy work stopped. Final selection started

- v5c = v5a + audit B1 fix only (verdict in at 16:55, inside the 17:05 limit): v5a 0.8038 vs **v5c 0.8025** points per pairing over the same 10,400 pairs. 0 crashes, 0 timeouts, 0 corrected actions.
- The three targets at 500 pairs each: threebettor 70.3% -> 71.3% (+1.0), stealer 72.8% -> 71.1% (-1.7), textbook_tag 70.9% -> 69.6% (-1.3); noise is about 4 on each. No matchup anywhere moved beyond noise (largest: slowplayer -5.0 at 50 pairs, potbettor +2.0, mc_exploiter +1.7).
- It does not pass the standing rule (targets did not improve, overall did not rise), so it is not promoted. The audit's B1 exploit needs an opponent built to use it; none of the 35 sparring bots does.
- **All strategy work is stopped.** Versions tried today after v4: v5a (kept), v5b, v5d, v5c (all rejected).
- **Final selection, started 16:56:** candidates are v4 and v5a (v3 dropped on the coach's instruction; no newer version passed). Each gets a second block of new cards (seed 2) at the full tiered allocation (9,350 pairs), so each is judged on 18,700 pairs with the same seeds. v5a runs first, then v4; expected end about 17:33. The 500-pair extras for threebettor, stealer and textbook_tag are left out of the ranking because only v5a has them.

## 16:34 — Decay-only verdict: v5d FAILED, not promoted. v5c run started (coach's 16:25 instructions)

- v5d = v5a + counter forgetting only (finished 16:31): **0.8029 -> 0.7976 points per pairing**. 0 crashes, 0 timeouts, 0 corrected actions.
- earlyshover fell beyond noise: 77.7% -> 70.3% (-7.3, noise 7.1). The target barely moved: switcher 72.5% -> 73.8% (+1.3, noise 4.0). Others inside noise: gto_charts -2.8, smallbet_trap -2.1, stealer +2.3.
- Forgetting costs more than it gains: against steady opponents it throws away good evidence, and it did not fix the switcher matchup. The entry stays v5a.
- **Coach's instructions received at 16:25 and applied:** (1) the queued v3 run was stopped and v3 is out of the final selection; (2) v5c = v5a + audit B1 fix only (a preflop raise to 35% or more of our stack counts as a shove in the counters); no forgetting, because decay-only failed; no overbet floor; no bigger simulation budget. Validator passed.
- v5c verdict run started 16:33 on the same seeds, with threebettor, stealer and textbook_tag raised to 500 pairs, plus a 3-minute v5a run on those three at 500 pairs so the comparison is like for like. Expected about 16:56, inside the 17:05 limit.
- **Plan for the final selection (must be pushed by 17:50):** a second block of new cards (seed 2) for every candidate. With two candidates (v4, v5a) the block is the full allocation; if v5c passes there are three candidates and the block is reduced (50/100/300/300 pairs) so all three get the same extra cards and it still ends by about 17:30.

## 16:14 — Batch 2 verdict: v5b FAILED, not promoted. Decay-only fallback started

- v5b on the same seeds as v5a (finished 16:12): **0.8029 -> 0.7956 points per pairing**. 0 crashes, 0 timeouts, 0 corrected actions, slowest 65 ms.
- Three matchups fell beyond noise: valueshover 79.9% -> 74.7% (-5.2, noise 3.7), gto_charts 61.1% -> 56.2% (-4.9, noise 4.4), smallbet_trap 94.1% -> 91.4% (-2.7, noise 2.3). Also down inside noise: trapper -6.0, slowplayer -5.0, v1_frozen -3.8, v2_frozen -3.1.
- The targets barely moved: switcher 72.5% -> 73.3% (+0.8), classifier -0.8, adaptive +1.2, mc_exploiter +1.6, overbet_bluffer -0.4.
- Reading: the losses are against bots whose big bets are honest, which is what the audit B2 change (never read a 1 to 1.5 pot bet much narrower than the minimum defence frequency) gives up. The entry stays v5a.
- **Decision:** as instructed, test (d) counter forgetting alone (`dev/v5d`). Run started 16:13, verdict about 16:31.
- **Decision:** Batch 3 (bet size by expected value) is skipped. The Batch 2 verdict came at 16:12, but the fallback run takes the rest of the time before the 16:40 stop.
- **Decision:** item (g) (5,000 deals, 400 ms budget) is not applied. There is no run slot left to test it before 16:40, and an untested change does not ship.
- The v3 run for the final selection is queued right after the fallback (about 16:31 to 16:49).

## 15:57 — Batch 1 verdict: v5a (audit bug fixes) PASSED and promoted

- v4 baseline on the new allocation (finished 15:36, 1,091 s): 0.8008 points per pairing, 0 crashes, slowest 85 ms.
- v5a on the same seeds (finished 15:55): **0.8029 points per pairing**. 0 crashes, 0 timeouts, 0 corrected actions, no decision without debug data, slowest 114 ms.
- No matchup moved beyond noise. Largest moves: earlyshover +4.7 (noise 7.0), oddsizer -3.7 (noise 6.0), classifier -2.6 (noise 3.9), switcher +1.7, maniac +1.7, gto_charts +1.4, allin +1.0, mc_exploiter -1.7, jam20 -1.6.
- Rule for bug fixes (overall does not drop, nothing falls beyond noise): met. v5a copied into `my_bots/im_just_in_mech_eng`, validator passed, one real match vs jam20 had `data_ok` true on 43 of 43 decisions, 0 without debug data. Pushed as `a97eac2` at 15:55.
- The v5b verdict run started at 15:55 and should finish about 16:13.

## 15:22 — Autonomous run started (coach's instructions): v5a and v5b built, verdict runs queued

**Decisions taken so far, with reasons**
1. One allocation for every verdict run from now on, so runs can be reused for the final selection: 50 pairs against bots we beat 90%+, 150 for the middle, 500 for the six hardest plus allin, jam20, lateshover, nashpush, switcher, classifier, adaptive, overbet_bluffer, valueshover, smallbet_trap (and gto_charts, mc_exploiter). 9,350 pairs, about 17 minutes a run. This covers both the Batch 1 and the Batch 2 lists, so v5a needs only one run.
2. Runs are queued back to back (v4 baseline, v5a, v5b) because the CPU is the bottleneck: 15:19 v4, about 15:37 v5a, about 15:55 v5b.
3. Item (g), 5,000 deals and a 400 ms budget, is NOT in v5b. It would make every test run about twice as slow and push the Batch 2 verdict past 16:40. It will be considered after the strategy verdicts, as its own small change.
4. Counter forgetting (d) is done per hand, not per opportunity: every counter loses half its weight every 20 hands. Per-opportunity decay alone cannot fix audit B3, because once we stop opening there are no new opportunities to decay with.
5. A decay-only version (`dev/v5d`) is already built as the fallback if v5b fails.

**Runner (c):** `arena.py` and `screen.py` now fail loudly if a bot that normally reports debug data sends a decision without it (a swallowed exception).

**v5a = v4 + two audit fixes** (`dev/v5a`, validator passed)
- A1: in the small blind, first to act, the plain big blind is no longer read as a shove. Check on 4,000 random hands with 1.7 big blinds behind at 500/1000: v4 played 18.3% of hands, v5a plays 100% (the all-in-or-fold table).
- A2: odds and bet-size reads use the pot we can actually win and the price we can actually pay. Check: big blind with 4,000 chips facing a 16,000 open shove at 25/50: v4 thought it needed 23% equity and called with 81.6% of hands; v5a needs 52.6% and calls with 2.1%.

**v5b = v5a + robustness** (`dev/v5b`, validator passed, short crash test clean)
- (d) counters forget (half-life 20 hands).
- (e) audit B1: a preflop raise to 35% or more of our stack counts as a shove in the counters, so such raises widen our read instead of tightening it. The reply stays shove-or-fold by price.
- (f) audit B2: no cliff at 1.05 pot. The normal read and the big-bet read are blended by size (pure normal at one pot, pure big-bet at 1.5 pots; shoves count as big sooner). Until the opponent shows a strong hand after an overbet, bets of 1 to 1.5 pots are never read much narrower than the minimum defence frequency. Showdown evidence now also comes from hands that were all-in before the river. We also check behind in position with a strong hand 12% of the time on the flop and turn.

## 15:10 — Step E done: fresh-eyes audit (nothing acted on yet)

A subagent with no context read only the kit README and `my_bots/im_just_in_mech_eng/bot.py` (v4). Its report, unedited:

> File audited: C:\Users\angel\Downloads\poker-hackathon\poker-hackathon-kit\my_bots\im_just_in_mech_eng\bot.py. Numbers below come from calling `decide` on hand-built states; nothing in the repository was changed.
>
> **A. RELIABILITY AND RULES**
>
> No crash, timeout or illegal action found. Real or possible problems:
>
> 1. **Line 549 (then 571-572). Sure, ran it.** Bot is small blind, first to act, with about 2 big blinds or less (owed 0.5 bb >= 0.35 x remaining stack). Branch 1 fires before the push/fold branch (582) and treats the plain big blind as a shove from the top 10% of hands. At 500/1000 ante 100 it plays 23% of hands with 1,700 chips and 14% with 2,000; with 2,400 (push/fold table) it plays 87%. It folds itself out when crippled.
> 2. **Lines 483, 749, 875. Unsure, engine-dependent.** When a bigger stack shoves on the bot, if `pot` includes chips the bot cannot match, 483 never removes them (one test state: calls 12.8% of hands instead of 5.9%), 875 gives wrong postflop odds, and 749 reads the shove as a giant overbet. Settle: log one such hand (`play.py --log`) and read `pot` and `amount_owed`.
> 3. **Line 402. Unsure.** A hand is counted only if its first log entry is `ante` or `small_blind`. If the engine logs the big blind first, no hand is ever counted and every read silently stays at its starting guess. Settle: check that debug `range`/`ftb` move during a logged match.
> 4. **Lines 976-977.** Any exception in `_think` becomes a silent check/fold. Known trigger: line 467 when both players share a `bot_id` (bot against its own copy; not a tournament state). Confirm logged decisions carry `debug.ms`.
> 5. **Lines 550, 880, 933** return `call` when owed >= stack; the README only documents `all_in` for that. Probably fine.
>
> Checked, fine: nothing escapes `decide` (971-984); warmup (972-974); division by zero (215, 280, 430, 453, 484, 617, 875); time (1,500 deals at k=12 took 13 ms, slowest decision 14 ms, cap 170 ms); module state (`_DONE_HANDS`, `_BOARDS`, `_DEPTH`: one small entry per hand); 200-entry cap (398-403); hands not acted in (307-310); all-in or zero-stack opponent (931-933); check while owing (916-924); raise below minimum or above stack (938-942); antes (238, 469); imports, file read at import only (127), no threads, eval or exec. Validator not run: run `make validate`.
>
> **B. THREE MOST EXPLOITABLE HABITS**
>
> 1. **Big preflop raise that is not all-in (549-577, 312-315).** Opponent raises to 35%+ of the bot's remaining stack using `raise`. The bot treats it as a shove, but the shove range comes from counters that count only `all_in`, so every such raise tightens the estimate. At 100 bb it continues with JJ+ (1.8%) at first and AA only (0.5%) after ten. Works as an open and as a 3-bet over the bot's 2.5 bb open (it opens 80%). The bot's only reply is all-in (550), so the raiser just folds. Worth about +0.3 bb per open and +1.6 bb per 3-bet immediately, then more.
> 2. **Bets just over the pot (line 59; 677-694, 750).** Flop bet of 1.04 pot: bot folds 46%. 1.10 pot: 79%. 1.5 pot: 86%. A pure bluff needs 52-60%. This holds while overbets stay under about 20% of the opponent's postflop actions (`big_n`, 348, counts every action; 3 in 30 still gets 82-86%), and folded hands show nothing. Worst after the bot checks behind: line 830 traps only when acting first, so an in-position check never holds a value hand, and a 1.2-pot turn bet gets 92% folds (87% against a proven frequent bettor).
> 3. **Shove over its first four opens, then stop (581, 593-598).** `jam_back` passes 0.5 and the bot opens 5% of small blinds at 25/50, 10% at 100/200, 19% at 300/600, instead of 80%. `raise_n` grows only when the bot opens, so it barely unlearns: after six shoves and 30 quiet hands it still opens 16-26%. It gives away half a big blind on most buttons for free. Root cause throughout: no counter decays, so cheap early behaviour sets reads used at expensive blinds.
>
> Also: its raises are value-only (881) unless the opponent bets 70%+ (895), never a river bluff (894); fresh, it folds about 74% of its opens to a normal 3-bet (adapts in about five).
>
> **C. DEAD CODE AND UNUSED COUNTERS**
>
> - Written, never read: `open_limp` (319), `open_fold` (321), `limp_raise` (329), `raise_call` (339).
> - Always zero because the bot never limps: `limp_n`, `limp_shove` (325-327; read at 543, 544, 567, 581). Branch 566-567 is unreachable.
> - `shown_*` (375-388) move only when the bot acted on the river (`_BOARDS` is the board at its last decision); all-in hands before the river teach nothing.
> - `c["opp_id"]` (469) never read. `fold_to_bet` (865) is debug only, and `dbg["ftb"]` is overwritten at 821.
> - `DEFAULT_DEFENCE` (62, 672) is a no-op and the `min(1.0, ...)` at 672 never binds.
> - 707 `and not big` always true. 510 `base = 0.0` redundant. 555 repeats the clamp at 171. `hand_num=None` (283) and the test at 308 never needed.
> - 921-924: `fold` and `check` branches identical. 871-872 likely never reached. The deadline check at 436 never binds.
> - Fallback path (106-117, 133-138, 174-176) runs only if the data file is missing.

**My notes on the audit (separate from its report; nothing changed)**
- A1 is a real bug: with about 2 big blinds or less in the small blind, the bot treats the big blind as a shove and folds most hands instead of shoving.
- A2 is a real bug, and I can settle its "unsure" from the engine code already read: `pot` does include the full shove, including chips we cannot match. So when a bigger stack shoves on our shorter stack before the flop, the bot thinks the price is much better than it is and calls too wide (in the auditor's test state, 12.8% of hands instead of 5.9%). After the flop the same error goes the other way and makes us fold slightly too often. This has been in every version since v1.
- A3 is fine: the engine posts antes, then the small blind, then the big blind, in that order, and the counters visibly move in the leak reports.
- A4: in every match I inspected by hand (for example all 2,607 sandbox decisions) each decision carried its debug data, so no silent exception happened there. The big test runs only fail on `data_ok` false, not on missing debug data; that check should be added.
- A5 is fine: the engine plays `call` for the chips we have, and 0 actions have been corrected in over 10 million decisions.
- B3 matches what the switcher bot showed: the counters never forget.

## 15:05 — Sandbox run done: the entry works in the tournament's Docker container

- WSL 2 and Docker Desktop work after the restart (Docker 29.9.3; nothing had to be clicked).
- Image built exactly as the Makefile does: `docker build -t fullhouse-sandbox:latest pokercore/sandbox` (598 MB). `pokercore` untouched. `play.py --docker` worked on Windows with no path workaround.
- Sandbox contents: Python 3.10.22, **eval7 0.1.7**, numpy 1.26.4, scipy 1.13.0, scikit-learn 1.5.2, treys 0.1.8. The laptop has eval7 0.1.10.

| Match (same seed in both) | Finished | Crashes / timeouts / restarts | Decisions | data_ok true | Sandbox avg / p95 / max | Laptop avg / p95 / max |
|---|---|---|---|---|---|---|
| vs caller (`sandbox_caller.jsonl`) | yes, 7 hands, we won | 0 / 0 / 0 | 22 | 22 | 1.4 / 3.2 / 3.3 ms | 1.5 / 3.4 / 3.8 ms |
| vs mc_exploiter (`sandbox_mc_exploiter.jsonl`) | yes, 37 hands, we won | 0 / 0 / 0 | 77 | 77 | 1.9 / 4.5 / 5.6 ms | 1.7 / 4.5 / 4.9 ms |
| 28 more matches vs 14 opponents | yes, all | 0 / 0 / 0 | 2,508 | 2,508 | 2.1 / 5.6 / 48.3 ms | 1.9 / 5.4 / 16.1 ms |
| First test match vs gto_charts | yes, 65 hands | 0 / 0 / 0 | 144 | 144 | max 11.5 ms | - |

- The bot made exactly the same decisions in the sandbox as on the laptop in all 30 seeded matches, so eval7 0.1.7 and 0.1.10 behave identically for what we use.
- Loading the bot and its tables in the container took at most 381 ms (the warmup allowance is 30 s).
- Slowest decision on half a CPU core: 48 ms, against a 2,000 ms limit. No change to the think-time budget is needed.
- I added `--seed` to the two requested commands so the sandbox and laptop runs play the same cards.
- Docker Desktop is quit again (engine stopped) so it does not slow test runs.

## 14:54 — Before the restart (WSL install for Docker)

- Everything is committed and pushed: working tree clean, 0 unpushed commits, latest commit `49ab50d` (v4 promoted).
- `wsl --status` before the install: "The Windows Subsystem for Linux is not installed."
- The entry is `my_bots/im_just_in_mech_eng` = v4. Previous versions: `dev/v3`, `dev/v2`, `sparring/v2_frozen`, `sparring/v1_frozen`.
- **To resume after the restart:** open Claude Code on `Downloads\poker-hackathon`, say "back". Next in order:
  1. `wsl --status`, start Docker Desktop, build the sandbox image (`docker build -t fullhouse-sandbox:latest pokercore/sandbox` from `poker-hackathon-kit`), then one match with `--docker` to measure decision times on half a CPU core.
  2. Step E: fresh-eyes audit of the entry `bot.py` by a subagent that sees only the kit README and the bot.
  3. Step F (all-in bots) only if time allows before 16:00. Freeze is 17:00, final push by 18:00, deadline 18:30.
- Python environment: `poker-hackathon-kit\.venv` (Python 3.10). Run tools with `.venv\Scripts\python.exe`.

## 14:47 — Step D done: v4 (preflop and short stack) promoted

**What v4 changes**
- All-in-or-fold cutoff 12 -> 15 big blinds (chosen from the test below).
- Facing an open shove at 25 big blinds or less: call by the equilibrium table. Leave the table only when that opponent's shoving frequency at short stacks is 15 points wider or tighter than equilibrium; then call by equity against the range they actually shove. New counters count their shoves at 25 big blinds or less separately from deep play.
- Shove wider than equilibrium against players who call our shoves less than equilibrium says (the fold-to-our-shove counter is now used).
- Whole-match premium: extra equity to call an all-in while blinds are small, read from the exact all-in solve by big blinds in play (+22 points at 25/50 with even stacks, +10 at 150/300, zero from 500/1000), reduced when stacks are uneven and scaled by how often the opponent shoves (25% of it against a player who rarely shoves).
- Open-everything threshold 0.60 -> 0.50. Re-raise starting guess 12% -> 20%.

**Cutoff test (150 pairs, ten opponents, same seeds)**

| Opponent | v3 | cutoff 12 | cutoff 15 | cutoff 20 |
|---|---|---|---|---|
| mc_exploiter | 52.7% | 51.7% | 53.3% | 56.0% |
| gto_charts | 59.3% | 61.3% | 61.7% | 61.0% |
| jam20 | 63.7% | 68.0% | 63.7% | 65.3% |
| allin | 67.0% | 68.7% | 68.7% | 68.7% |
| textbook_tag | 67.7% | 69.3% | 72.3% | 72.7% |
| threebettor | 70.3% | 68.0% | 70.7% | 67.3% |
| stealer | 71.3% | 72.3% | 72.3% | 72.7% |
| lateshover | 72.0% | 73.3% | 74.3% | 71.3% |
| chartbot | 78.3% | 75.7% | 77.7% | 80.0% |
| nashpush | 86.7% | 88.3% | 86.0% | 82.7% |
| Points per pairing | 0.689 | 0.697 | 0.701 | 0.698 |

The three cutoffs are within noise of each other. 15 scored highest; 20 cost 4 points against nashpush.

**Final verdict: v3 vs v4, tiered allocation, 12,700 pairs, same seeds (1,414 s)**

| Opponent | Pairs | v3 | v4 | Change | Noise | Verdict |
|---|---|---|---|---|---|---|
| nashpush | 250 | 88.6% | 86.2% | -2.4 | 4.2 | same |
| adaptive | 250 | 71.8% | 69.8% | -2.0 | 5.7 | same |
| oddsizer | 250 | 88.2% | 86.2% | -2.0 | 4.2 | same |
| trapper | 50 | 95.0% | 94.0% | -1.0 | 6.4 | same |
| switcher | 250 | 70.8% | 70.0% | -0.8 | 5.8 | same |
| bluffer | 250 | 81.2% | 80.6% | -0.6 | 5.0 | same |
| threebettor | 1,000 | 69.3% | 68.8% | -0.4 | 2.9 | same |
| overbet_bluffer | 250 | 83.0% | 83.0% | 0.0 | 4.8 | same |
| slowplayer | 50 | 95.0% | 95.0% | 0.0 | 6.2 | same |
| caller | 50 | 99.0% | 99.0% | 0.0 | 2.8 | same |
| mathematician, nit, ref_bot_2, shark | 50 each | 100% | 100% | 0.0 | 0.0 | same |
| v2_frozen | 500 | 57.5% | 57.6% | +0.1 | 4.4 | same |
| maniac | 250 | 82.2% | 82.4% | +0.2 | 4.8 | same |
| aggressor | 250 | 84.8% | 85.0% | +0.2 | 4.5 | same |
| chartbot | 250 | 74.0% | 74.4% | +0.4 | 5.5 | same |
| random | 250 | 77.8% | 78.2% | +0.4 | 5.2 | same |
| mc_exploiter | 1,000 | 52.0% | 52.5% | +0.5 | 3.2 | same |
| earlyshover | 250 | 72.2% | 72.8% | +0.6 | 5.6 | same |
| potodds | 250 | 87.6% | 88.2% | +0.6 | 4.1 | same |
| stealer | 1,000 | 71.4% | 72.1% | +0.7 | 2.8 | same |
| classifier | 250 | 73.2% | 74.0% | +0.8 | 5.6 | same |
| minraiser | 50 | 96.0% | 97.0% | +1.0 | 5.2 | same |
| allin | 1,000 | 65.2% | 66.2% | +1.0 | 3.0 | same |
| potbettor | 250 | 76.8% | 78.0% | +1.2 | 5.3 | same |
| gto_charts | 1,000 | 57.9% | 59.2% | +1.3 | 3.1 | same |
| v1_frozen | 500 | 59.0% | 60.3% | +1.3 | 4.4 | same |
| valueshover | 250 | 79.8% | 81.2% | +1.4 | 5.0 | same |
| textbook_tag | 250 | 67.8% | 69.8% | +2.0 | 5.9 | same |
| donkbettor | 250 | 72.8% | 75.2% | +2.4 | 5.5 | same |
| lateshover | 1,000 | 67.5% | 70.8% | +3.3 | 2.9 | UP |
| jam20 | 1,000 | 59.7% | 63.0% | +3.4 | 3.1 | UP |
| smallbet_trap | 50 | 93.0% | 97.0% | +4.0 | 6.1 | same |

- Overall: **0.7914 -> 0.7965 points per pairing** (average over 35 opponents).
- Reliability: 0 crashes, 0 timeouts, 0 corrected actions over 2,502,544 decisions.
- v4 against v3 head to head, 300 pairs: 51.0% (95% CI 47.0-55.0), pairings 42/222/36. Not a proven edge.
- Stress screen on v4: clean, 9 conditions, 50,680 decisions.
- Behind/ahead test: from 4,000 chips 35.4% -> 39.2%; from 16,000 chips 92.6% -> 92.9%.

**Verdict against the rules**
- Targets: jam20 and lateshover up beyond noise. allin +1.0, gto_charts +1.3, stealer +0.7, threebettor -0.4 did not move. The six targets together average +1.6 points over 6,000 pairs.
- nashpush "must not drop": -2.4, inside noise (4.2) at 250 pairs. The cutoff test also showed 15 slightly lower than 12 against it, so this is probably a small real cost.
- No matchup dropped beyond noise. Overall score up.
- Judged as passing (targets improved in aggregate, two of them clearly, nothing fell beyond noise) and copied into the entry. Validator passed. One real match vs jam20: 224 of 224 decisions with `data_ok` true, 0 errors, slowest 14 ms; the new code paths (`vs_short_shove`, `push_wide`) were exercised. Pushed as `49ab50d` at 14:45.
- If the stricter reading is wanted (every target must rise), v4 fails it; `dev/v3/bot.py` is the previous entry and can be copied back.

**Findings on the side**
- switcher: we win 70.8% against it, but 82.2% against the plain maniac it turns into. The fake tight start does fool the counters for a while (they treat all hands of a match equally).
- Timing: some runs recorded single decisions of 200 to 630 ms. A check with real bot processes gave a slowest of 55 ms and a single unloaded process had none over 40 ms, so these were stalls of the laptop during long parallel runs, not the bot. No decision has ever reached the 2,000 ms limit. Half a CPU core in the sandbox is still untested.
- The preflop constants (open threshold, re-raise guess) produced no measurable change against threebettor or stealer.
- allin at 66.2% is still 3.6 points under the exact ceiling of 69.8%.

**Open problems**
1. mc_exploiter 52.5%, v2-level bots and gto_charts 59.2% remain the lowest matchups.
2. threebettor and stealer have not improved since v1.
3. switcher shows the counters can be misled by an early fake style.

## 13:45 — Testing changes before Step D (no strategy change)

**Test allocation from now on** (`screen.py --alloc REF --targets ...`)
- 1,000 pairs on the stage's target bots, always including gto_charts and mc_exploiter.
- 500 pairs on the six opponents we did worst against in the reference run.
- 50 pairs on opponents we beat 90% or more (regression check only).
- 250 pairs on everyone else.
- The overall score is now the average points per pairing over opponents, each opponent counting once (the same as before when every opponent had the same number of pairs).

**Stress screen** (`tools/stress.py`, entry v3, 13 opponents, 5 pairs each per condition, 26 s)

| Condition | Matches | Decisions | Crashes | Timeouts | Corrected | Slowest |
|---|---|---|---|---|---|---|
| Turbo blinds (10 hands a level) | 130 | 6,503 | 0 | 0 | 0 | 23 ms |
| Slow blinds (40 hands a level) | 130 | 9,973 | 0 | 0 | 0 | 26 ms |
| Very short: 3 big blinds each | 130 | 238 | 0 | 0 | 0 | 6 ms |
| Short: 10 big blinds each | 130 | 872 | 0 | 0 | 0 | 20 ms |
| Very deep: 2,000 big blinds each | 130 | 18,951 | 0 | 0 | 0 | 33 ms |
| Flat 500/1000 blinds with a 100 ante | 130 | 934 | 0 | 0 | 0 | 21 ms |
| Odd chip counts: 10,037 each | 130 | 8,504 | 0 | 0 | 0 | 26 ms |
| Uneven: we start with 300 of 20,000 | 130 | 3,064 | 0 | 0 | 0 | 63 ms |
| Uneven: we start with 19,700 of 20,000 | 130 | 1,582 | 0 | 0 | 0 | 23 ms |

Clean: 1,170 matches, 50,621 decisions, no crash, no timeout, no corrected action, tables always loaded.

**Behind/ahead test** (`tools/uneven.py`, entry v3, 100 duplicate pairs each way, 130 s)
The engine allows uneven stacks without editing pokercore: the runner drives the organisers' `Table` class directly.
Chip share alone would give 20% from behind and 80% from ahead.

| Opponent | From 4,000 chips | 95% CI | From 16,000 chips | 95% CI |
|---|---|---|---|---|
| textbook_tag | 34.0% | 27.8-40.8 | 91.0% | 86.2-94.2 |
| lateshover | 33.0% | 26.9-39.8 | 92.0% | 87.4-95.0 |
| threebettor | 33.5% | 27.3-40.3 | 91.5% | 86.8-94.6 |
| adaptive | 33.0% | 26.9-39.8 | 90.5% | 85.6-93.8 |
| classifier | 39.5% | 33.0-46.4 | 94.0% | 89.8-96.5 |
| chartbot | 39.5% | 33.0-46.4 | 96.5% | 93.0-98.3 |
| All six | 35.4% | 32.8-38.2 | 92.6% | 91.0-93.9 |

We beat the chip-share line by about 15 points from behind and 13 from ahead.

**New sparring bot:** `switcher` plays tight for 15 hands, then turns into a maniac. The field is 35 opponents.

## 13:37 — Step C done: v3 (not readable, win small pots) PASSED and promoted

**What v3 changes**
- Bet size comes from the situation, never from hand strength: about a third of the pot when a flop is checked to us, half when we act first on a flop, more on boards with draws, two thirds on the turn, three quarters on the river, and up to 1.6 times bigger against a player who rarely folds. Bluffs use the same sizes.
- Stab: when the opponent checks (and in some spots when we act first) a non-value hand bets at a base rate of 50% on the flop, 45% on the turn, 30% on the river, scaled by how often they fold to that size, and never when their folding does not pay for the bet.
- Trap: acting first with a strong hand we sometimes check (about 10%, up to 45% against a player who bets whenever checked to).
- Bluff-raise: against a player who bets at least 70% of the time nobody has bet, weak hands sometimes raise at the value-raise size, until they show they do not fold to raises.
- New counters: their folds to our small bets, normal bets and raises separately, plus an overall fold rate (preflop included) used as the starting guess.
- `sparring/v2_frozen` added as the head-to-head benchmark. The field is 34 with it.

**How it got here**
- 12:48 first 100-pair screen: mc_exploiter 43 -> 57.5, overall 0.723 -> 0.769, maniac -7. Added the overall fold-rate prior.
- 13:08 first full run (kept as `results/screen_v3_first_try.json`): 0.746 -> 0.779, but random -7.0 and lateshover -6.4 were beyond noise, so it failed the standing rule. The leak report showed the cause: smaller bets won less from players who call.
- 13:20 sizes raised on later streets and against players who rarely fold; stabs only when their folding pays for the size. Tuning screen: v2 0.744, first try 0.778, adjusted 0.797.
- 13:35 final full run below.

**Final: v2 baseline vs v3, 33 opponents, 250 pairs each, same seeds (874 s)**

| Opponent | v2 | v3 | Change | Noise | Verdict | v2 W/D/L | v3 W/D/L |
|---|---|---|---|---|---|---|---|
| random | 81.2% | 76.6% | -4.6 | 5.2 | same | 164/78/8 | 142/99/9 |
| lateshover | 71.8% | 68.6% | -3.2 | 5.8 | same | 122/115/13 | 114/115/21 |
| minraiser | 94.6% | 92.6% | -2.0 | 3.1 | same | 223/27/0 | 213/37/0 |
| oddsizer | 87.8% | 86.4% | -1.4 | 4.2 | same | 191/57/2 | 183/66/1 |
| aggressor | 86.8% | 85.6% | -1.2 | 4.4 | same | 189/56/5 | 184/60/6 |
| maniac | 82.4% | 81.2% | -1.2 | 4.9 | same | 167/78/5 | 161/84/5 |
| textbook_tag | 68.0% | 67.6% | -0.4 | 5.9 | same | 107/126/17 | 104/130/16 |
| caller | 96.6% | 96.4% | -0.2 | 2.3 | same | 233/17/0 | 232/18/0 |
| nit | 99.6% | 99.4% | -0.2 | 0.9 | same | 248/2/0 | 247/3/0 |
| allin | 65.2% | 65.2% | 0.0 | 6.0 | same | 105/116/29 | 105/116/29 |
| adaptive | 70.0% | 70.0% | 0.0 | 5.8 | same | 108/134/8 | 112/126/12 |
| nashpush | 88.6% | 88.6% | 0.0 | 4.0 | same | 195/53/2 | 195/53/2 |
| mathematician | 100% | 100% | 0.0 | 0.0 | same | 250/0/0 | 250/0/0 |
| ref_bot_2 | 100% | 100% | 0.0 | 0.0 | same | 250/0/0 | 250/0/0 |
| shark | 100% | 100% | 0.0 | 0.0 | same | 250/0/0 | 250/0/0 |
| potbettor | 76.8% | 77.2% | +0.4 | 5.3 | same | 142/100/8 | 142/102/6 |
| potodds | 88.6% | 89.2% | +0.6 | 4.0 | same | 195/53/2 | 199/48/3 |
| stealer | 67.6% | 68.4% | +0.8 | 5.9 | same | 102/134/14 | 105/132/13 |
| gto_charts | 56.4% | 58.2% | +1.8 | 6.3 | same | 64/154/32 | 69/153/28 |
| bluffer | 80.4% | 82.6% | +2.2 | 4.9 | same | 160/82/8 | 165/83/2 |
| trapper | 91.0% | 93.8% | +2.8 | 3.3 | same | 205/45/0 | 220/29/1 |
| threebettor | 65.0% | 68.6% | +3.6 | 6.0 | same | 93/139/18 | 109/125/16 |
| earlyshover | 64.6% | 70.2% | +5.6 | 5.9 | same | 99/125/26 | 121/109/20 |
| v1_frozen | 55.0% | 61.2% | +6.2 | 6.2 | same | 54/167/29 | 68/170/12 |
| mc_exploiter | 41.4% | 48.8% | +7.4 | 6.3 | UP | 27/153/70 | 44/156/50 |
| smallbet_trap | 83.2% | 94.8% | +11.6 | 3.9 | UP | 168/80/2 | 224/26/0 |
| classifier | 58.4% | 71.8% | +13.4 | 6.0 | UP | 75/142/33 | 125/109/16 |
| jam20 | 47.8% | 62.8% | +15.0 | 6.2 | UP | 53/133/64 | 87/140/23 |
| chartbot | 59.4% | 74.4% | +15.0 | 5.9 | UP | 76/145/29 | 133/106/11 |
| valueshover | 60.8% | 80.4% | +19.6 | 5.6 | UP | 90/124/36 | 159/84/7 |
| donkbettor | 51.0% | 73.8% | +22.8 | 6.0 | UP | 55/145/50 | 129/111/10 |
| overbet_bluffer | 58.0% | 81.8% | +23.8 | 5.6 | UP | 78/134/38 | 163/83/4 |
| slowplayer | 64.2% | 94.0% | +29.8 | 4.8 | UP | 97/127/26 | 220/30/0 |

- Overall on the same 33 opponents: **0.746 -> 0.797 points per pairing**; 74.6% -> 79.7% of matches.
- v3 against v2 head to head (`v2_frozen`): 57.4% (95% CI 53.0-61.7), pairings 59/169/22.
- Reliability: 0 crashes, 0 timeouts, 0 corrected actions over 1,713,390 decisions. Slowest 80 ms.
- 15 to 40 big blind zone: matches that reach it, 72.9% -> 79.4% won; entered behind, 31.6% -> 38.0%.

**Verdict against the rules**
- mc_exploiter, classifier, donkbettor up beyond noise: passed.
- Overall points per pairing up: passed.
- caller -0.2, trapper +2.8, chartbot +15.0, nit -0.2, smallbet_trap +11.6: no drop, passed.
- No matchup dropped beyond noise. Standing rule passed.
- v3 copied into `my_bots/im_just_in_mech_eng`. Validator passed. One real match vs mc_exploiter: 211 of 211 decisions with `data_ok` true, 0 errors, slowest 5 ms. Pushed as `9ec5f23` at 13:35.

**Open problems**
1. mc_exploiter is still below 50% (48.8%). The first try with smaller bets reached 54.0% against it, at the cost of random and lateshover.
2. random -4.6 is inside noise but its luck-adjusted chips also fell, so it is probably a small real drop.
3. In one tuning run under load a decision took 178 ms: the 170 ms stop inside the bot kicked in and no timeout happened, but it shows how close the laptop can get. Half a CPU core in the sandbox is still untested.
4. gto_charts 58.2%, allin 65.2%, threebettor 68.6%, stealer 68.4% unchanged: preflop and short-stack work (Step D).

## 12:34 — Steps A and B done: v2 promoted, field widened to 33, rebaselined

**Step A: robustness check of v2 on four new big-bet bots (250 pairs, same seeds)**

| Opponent | Kind | v1 | v2 | Change | v1 W/D/L | v2 W/D/L |
|---|---|---|---|---|---|---|
| valueshover | honest big bets | 51.8% | 62.2% | +10.4 | 55/149/46 | 90/131/29 |
| slowplayer | honest big bets | 59.8% | 64.2% | +4.4 | 80/139/31 | 97/127/26 |
| overbet_bluffer | big-bet bluffs | 58.0% | 56.2% | -1.8 | 73/144/33 | 68/145/37 |
| earlyshover | big-bet bluffs | 71.8% | 66.2% | -5.6 | 123/113/14 | 107/117/26 |
| Sum of the four | | 0.604 points per pairing | 0.622 | +0.018 | | |

- v2 scored at least as well as v1 over the four, so by Angelo's rule it was copied into
  `my_bots/im_just_in_mech_eng`. Validator passed. One real match vs chartbot: 135 of our 135 decisions had
  `data_ok` true, slowest 11 ms. Committed and pushed as `4fe74a9` at 12:18.
- The pattern is the expected one: v2 gains against honest big bets and gives a little back against big-bet bluffs.

**Step B: field widened (no strategy change)**
- New sparring bots: `classifier`, `mc_exploiter`, `donkbettor`, `textbook_tag`, `jam20` (plus the four from Step A). The field is now 33 opponents.
- Runner now reports hands by effective stack depth and the match win rate in matches that reach 15 to 40 big blinds.
- Pushed as the commit after `4fe74a9` at 12:34.

**New baseline: entry (v2) vs 33 opponents, 250 pairs each (841 s, `results/screen_baseline2.json`)**

| Opponent | Match win rate | 95% CI | Pairings W/D/L | Luck-adjusted chips/100 | Slowest |
|---|---|---|---|---|---|
| mc_exploiter | 41.4% | 37.2-45.8 | 27/153/70 | -3,355 | 40 ms |
| jam20 | 47.8% | 43.5-52.2 | 53/133/64 | -1,140 | 62 ms |
| donkbettor | 51.0% | 46.6-55.4 | 55/145/50 | +232 | 46 ms |
| v1_frozen | 55.0% | 50.6-59.3 | 54/167/29 | +1,446 | 44 ms |
| gto_charts | 56.4% | 52.0-60.7 | 64/154/32 | +2,117 | 45 ms |
| overbet_bluffer | 58.0% | 53.6-62.3 | 78/134/38 | +2,000 | 41 ms |
| classifier | 58.4% | 54.0-62.6 | 75/142/33 | +2,224 | 52 ms |
| chartbot | 59.4% | 55.0-63.6 | 76/145/29 | +1,958 | 59 ms |
| valueshover | 60.8% | 56.5-65.0 | 90/124/36 | +2,324 | 69 ms |
| slowplayer | 64.2% | 59.9-68.3 | 97/127/26 | +2,806 | 64 ms |
| earlyshover | 64.6% | 60.3-68.7 | 99/125/26 | +4,706 | 60 ms |
| threebettor | 65.0% | 60.7-69.0 | 93/139/18 | +11,196 | 40 ms |
| allin | 65.2% | 60.9-69.2 | 105/116/29 | +27,089 | 15 ms |
| stealer | 67.6% | 63.4-71.5 | 102/134/14 | +13,307 | 43 ms |
| textbook_tag | 68.0% | 63.8-71.9 | 107/126/17 | +6,459 | 41 ms |
| adaptive | 70.0% | 65.8-73.9 | 108/134/8 | +16,716 | 68 ms |
| lateshover | 71.8% | 67.7-75.6 | 122/115/13 | +5,828 | 36 ms |
| potbettor | 76.8% | 72.9-80.3 | 142/100/8 | +56,586 | 22 ms |
| bluffer | 80.4% | 76.7-83.6 | 160/82/8 | +21,033 | 50 ms |
| random | 81.2% | 77.5-84.4 | 164/78/8 | +14,239 | 35 ms |
| maniac | 82.4% | 78.8-85.5 | 167/78/5 | +45,452 | 43 ms |
| smallbet_trap | 83.2% | 79.7-86.2 | 168/80/2 | +11,357 | 57 ms |
| aggressor | 86.8% | 83.5-89.5 | 189/56/5 | +47,313 | 32 ms |
| oddsizer | 87.8% | 84.6-90.4 | 191/57/2 | +9,547 | 32 ms |
| nashpush | 88.6% | 85.5-91.1 | 195/53/2 | +7,022 | 13 ms |
| potodds | 88.6% | 85.5-91.1 | 195/53/2 | +23,932 | 39 ms |
| trapper | 91.0% | 88.2-93.2 | 205/45/0 | +9,192 | 63 ms |
| minraiser | 94.6% | 92.3-96.3 | 223/27/0 | +91,331 | 44 ms |
| caller | 96.6% | 94.6-97.9 | 233/17/0 | +53,354 | 40 ms |
| nit | 99.6% | 98.6-99.9 | 248/2/0 | +9,726 | 22 ms |
| mathematician | 100% | 99.2-100 | 250/0/0 | +11,033 | 38 ms |
| ref_bot_2 | 100% | 99.2-100 | 250/0/0 | +11,033 | 36 ms |
| shark | 100% | 99.2-100 | 250/0/0 | +9,786 | 10 ms |

Totals: 12,311/16,500 matches (74.6%); **0.7461 points per pairing**; 1,754,763 decisions, 0 crashes, 0 timeouts,
0 corrected actions, slowest 69 ms. This number is lower than the old 0.813 only because nine harder bots joined the field.

**The 15 to 40 big blind zone (all 16,500 matches)**
- Hands by effective stack (the shorter stack): under 15 bb 15.2%, 15 to 40 bb 21.7%, over 40 bb 63.0%.
- 68.5% of matches reach the zone (11,310 of 16,500). We win 72.9% of those, against 78.3% of the matches that never reach it.
- Entered ahead (we hold more than half the chips at the first zone hand): we win 91.7% of 7,770.
- Entered behind: we win 31.6% of 3,540. Caveat: being behind already means fewer chips, so this is not a pure measure of how we play the zone; the average chip share on entry was not recorded.
- Against the three worst: mc_exploiter 35% of 384 matches reaching the zone (12% when behind), jam20 44% of 408 (16% behind), donkbettor 45% of 388 (19% behind).
- Against bots we split with, entering behind is close to lost: threebettor 17%, stealer 17%, adaptive 17%.

**Reading**
- Two matchups are now below 50%: mc_exploiter (41.4%) and jam20 (47.8%). Both lose luck-adjusted chips too, so it is not luck.
- mc_exploiter is the predicted weakness: it folds to our big bets, bets when we check, and reads our bet size.
- jam20 is not covered by Step C. It shoves at 20 big blinds or less, a depth where we do not yet play all-in-or-fold (our cutoff is 12).

**Open problems**
1. mc_exploiter 41.4%, jam20 47.8%, donkbettor 51.0%.
2. A full-field run at 250 pairs now takes 14 minutes. Tuning uses 100-pair screens; 250 pairs only for a stage's final verdict.
3. Still no run in the Docker sandbox.

## 11:56 — Stage 1 tested: v2 (how we read bets). NOT copied into the entry

**What v2 changes (in `dev/v2/`, entry untouched)**
- Counts per opportunity: every time the opponent could bet or raise after the flop, did they, split into flop bets, turn/river bets, raises over our bets, and big bets (over 1.05 x pot, or a shove over 0.75 x pot).
- Before evidence, a normal bet is read at the minimum defence frequency for its size (a normal mix of value and bluffs). Raises and big bets start narrow.
- Evidence moves the read: bets made almost always become "any hand"; rare bets become narrow. An opponent who raises a lot everywhere (preflop included) starts looser in every bucket.
- Showdown evidence: when their bets keep showing strong hands, the bet is read as "the top X% of hands" with no bluffs; a big bet shown with a weak hand loosens the read of big bets.
- Deep-stack premium: up to 8 points of extra equity to put a deep stack in, fading against a proven maniac.
- Three test rounds were needed. Round 1 lost 6 to 9 points against maniac, aggressor and potbettor (it folded to overbets twice as often as the baseline) and 5.6 against chartbot. The overall-aggression prior, the fading premium and the showdown evidence fixed most of that.

**Result: baseline vs v2, 24 opponents, 250 pairs each, same seeds (549 s)**

| Opponent | Old | New | Change | Noise | Old W/D/L | New W/D/L |
|---|---|---|---|---|---|---|
| bluffer | 86.2% | 82.0% | -4.2 | 4.6 | 182/67/1 | 167/76/7 |
| random | 84.4% | 80.2% | -4.2 | 4.8 | 179/64/7 | 161/79/10 |
| aggressor | 88.4% | 86.0% | -2.4 | 4.2 | 196/50/4 | 186/58/6 |
| lateshover | 73.4% | 71.2% | -2.2 | 5.7 | 126/115/9 | 120/116/14 |
| chartbot | 60.0% | 58.0% | -2.0 | 6.2 | 87/126/37 | 70/150/30 |
| adaptive | 71.6% | 71.2% | -0.4 | 5.7 | 118/122/10 | 115/126/9 |
| caller | 96.6% | 96.4% | -0.2 | 2.3 | 233/17/0 | 232/18/0 |
| allin | 65.2% | 65.2% | 0.0 | 6.0 | 105/116/29 | 105/116/29 |
| maniac | 83.2% | 83.2% | 0.0 | 4.7 | 168/80/2 | 171/74/5 |
| nashpush | 88.6% | 88.6% | 0.0 | 4.0 | 195/53/2 | 195/53/2 |
| nit | 99.4% | 99.4% | 0.0 | 1.0 | 247/3/0 | 247/3/0 |
| mathematician | 100% | 100% | 0.0 | 0.0 | 250/0/0 | 250/0/0 |
| ref_bot_2 | 100% | 100% | 0.0 | 0.0 | 250/0/0 | 250/0/0 |
| shark | 100% | 100% | 0.0 | 0.0 | 250/0/0 | 250/0/0 |
| potodds | 88.2% | 88.4% | +0.2 | 4.1 | 191/59/0 | 195/52/3 |
| minraiser | 94.6% | 95.0% | +0.4 | 2.8 | 223/27/0 | 225/25/0 |
| stealer | 68.6% | 69.2% | +0.6 | 5.9 | 107/129/14 | 111/124/15 |
| threebettor | 64.2% | 65.4% | +1.2 | 6.0 | 93/135/22 | 97/133/20 |
| potbettor | 75.8% | 77.2% | +1.4 | 5.4 | 139/101/10 | 144/98/8 |
| oddsizer | 85.0% | 86.8% | +1.8 | 4.4 | 178/69/3 | 186/62/2 |
| trapper | 87.8% | 90.4% | +2.6 | 3.9 | 190/59/1 | 203/46/1 |
| gto_charts | 53.0% | 56.8% | +3.8 | 6.3 | 50/165/35 | 67/150/33 |
| v1_frozen (head to head) | 51.4% | 56.4% | +5.0 | 6.3 | 31/195/24 | 57/168/25 |
| smallbet_trap | 55.4% | 83.8% | +28.4 | 5.5 | 67/143/40 | 174/71/5 |

- Overall: 0.800 -> 0.813 points per pairing; 80.0% -> 81.3% of matches.
- Reliability: 0 crashes, 0 timeouts, 0 corrected actions over 1,135,101 decisions. Slowest decision 94.8 ms (baseline 55.3 ms).
- "Noise" is two standard errors of the difference between two win rates at 500 matches each.

**Verdict against the rules**
- Overall points per pairing: up, but almost all of it is smallbet_trap. Without that one bot the other 23 opponents net out flat.
- Pass tests "must go up": threebettor +1.2, stealer +0.6, maniac 0.0, gto_charts +3.8. None is beyond noise. NOT passed.
- Pass tests "must not drop": chartbot -2.0 (inside noise), nit 0.0, smallbet_trap +28.4. Passed.
- No matchup dropped beyond noise, but bluffer and random are at the edge (-4.2 each) and their luck-adjusted chips fell too, so those two drops are probably real.
- Standing rule not met, so v2 stays in `dev/v2/` and the entry is unchanged.

**What this says about the diagnosis**
- The idea that folding to flop bets was the main leak against threebettor and stealer was mostly wrong: reading their flop bets as "any hand" moved those matchups by about 1 point.
- The real, large hole was the one the reviewer predicted: big bets from an opponent who only shoves strong hands.

**Open problems**
1. threebettor, stealer, maniac did not improve. The remaining lever against the first two is preflop (Stage 2).
2. v2 is weaker against bluff-heavy bots that bet big early (bluffer, random): it starts out believing big bets.
3. Slowest decision rose to 95 ms on this laptop; still unverified on half a CPU core.
4. dev/v2 and its results are not committed.

## 11:15 — Stage 0 done: wider field, luck-adjusted score, baseline (no strategy change)

**What changed**
- Pending work committed and pushed (`8d77af3`), then Stage 0 itself (`a9743f6`).
- New sparring bots: `smallbet_trap` (bets a third of the pot every street, shoves only with two pair or better), and `aggressor`, `mathematician`, `shark`, `ref_bot_2` copied unmodified from uzlez/fullhouse-engine (MIT; notice in `sparring/FULLHOUSE_NOTICE.txt`). Cloned to a scratch folder outside the repo; none of their code is in our bot. The field is now 24 opponents. `mathematician` and `ref_bot_2` turn out to be the same strategy.
- Runner: when the betting ends with a player all-in before the river, the hand is also credited by equity (exact on flop and turn, 3,000 sampled run-outs preflop) instead of the actual run-out. Reported as luck-adjusted chips per 100 hands. Match win rate stays the deciding number.
- `tools/compare.py`: old vs new table per opponent, sorted by change, with a noise band.
- STATUS.md and CHANGELOG.md times corrected to the real clock; from now on times come from the system clock.

**Baseline: current entry vs 24 opponents, 250 duplicate pairs each (477.5 s, saved as `results/screen_baseline.json`)**

| Opponent | Match win rate | 95% CI | Pairings W/D/L | Luck-adjusted chips/100 | Crashes | Corrected | Slowest |
|---|---|---|---|---|---|---|---|
| v1_frozen (mirror) | 51.4% | 47.0-55.8 | 31/195/24 | +801 | 0 | 0 | 39 ms |
| gto_charts | 53.0% | 48.6-57.3 | 50/165/35 | +1,296 | 0 | 0 | 43 ms |
| smallbet_trap | 55.4% | 51.0-59.7 | 67/143/40 | +2,533 | 0 | 0 | 43 ms |
| chartbot | 60.0% | 55.6-64.2 | 87/126/37 | +2,391 | 0 | 0 | 55 ms |
| threebettor | 64.2% | 59.9-68.3 | 93/135/22 | +8,522 | 0 | 0 | 43 ms |
| allin | 65.2% | 60.9-69.2 | 105/116/29 | +27,089 | 0 | 0 | 7 ms |
| stealer | 68.6% | 64.4-72.5 | 107/129/14 | +10,991 | 0 | 0 | 39 ms |
| adaptive | 71.6% | 67.5-75.4 | 118/122/10 | +17,020 | 0 | 0 | 43 ms |
| lateshover | 73.4% | 69.4-77.1 | 126/115/9 | +5,564 | 0 | 0 | 45 ms |
| potbettor | 75.8% | 71.9-79.3 | 139/101/10 | +44,902 | 0 | 0 | 38 ms |
| maniac | 83.2% | 79.7-86.2 | 168/80/2 | +48,915 | 0 | 0 | 24 ms |
| random | 84.4% | 81.0-87.3 | 179/64/7 | +21,382 | 0 | 0 | 38 ms |
| oddsizer | 85.0% | 81.6-87.9 | 178/69/3 | +9,720 | 0 | 0 | 53 ms |
| bluffer | 86.2% | 82.9-88.9 | 182/67/1 | +27,958 | 0 | 0 | 43 ms |
| trapper | 87.8% | 84.6-90.4 | 190/59/1 | +10,074 | 0 | 0 | 50 ms |
| potodds | 88.2% | 85.1-90.7 | 191/59/0 | +29,794 | 0 | 0 | 42 ms |
| aggressor | 88.4% | 85.3-90.9 | 196/50/4 | +49,769 | 0 | 0 | 43 ms |
| nashpush | 88.6% | 85.5-91.1 | 195/53/2 | +7,022 | 0 | 0 | 7 ms |
| minraiser | 94.6% | 92.3-96.3 | 223/27/0 | +76,456 | 0 | 0 | 54 ms |
| caller | 96.6% | 94.6-97.9 | 233/17/0 | +53,359 | 0 | 0 | 33 ms |
| nit | 99.4% | 98.2-99.8 | 247/3/0 | +9,786 | 0 | 0 | 14 ms |
| mathematician | 100.0% | 99.2-100 | 250/0/0 | +11,033 | 0 | 0 | 37 ms |
| ref_bot_2 | 100.0% | 99.2-100 | 250/0/0 | +11,033 | 0 | 0 | 37 ms |
| shark | 100.0% | 99.2-100 | 250/0/0 | +9,785 | 0 | 0 | 11 ms |

Totals: 9,605/12,000 matches (80.0%); 0.800 points per pairing (0.813 without the mirror); 1,050,066 decisions,
0 crashes, 0 timeouts, 0 corrected actions, slowest 55 ms; 19,935 all-ins credited by equity over 619,409 hands.

**Reading**
- smallbet_trap, the reviewer's test bot, is already our third-worst matchup at 55.4%, before any change.
- Luck-adjusted chips per 100 are not comparable across opponents (short matches against wild bots give huge numbers). Use them only to compare two versions against the same opponent.
- At 250 pairs the noise on one matchup is about plus or minus 4 points, so a change must be bigger than about 6 points on a single opponent to count on its own.

**Open problems**
1. gto_charts 53.0%, smallbet_trap 55.4%, chartbot 60.0% are the three worst.
2. A full-field run at 250 pairs takes 8 minutes; each stage needs one.
3. Still no run in the Docker sandbox.

## 10:55 — Entry renamed, gto_charts, leak report, draws, proposed fixes (nothing implemented)

**What changed**
- Entry folder is now `my_bots/im_just_in_mech_eng` (with `data/`). Validator passed; one real match vs caller: 20 of our 20 decisions had `data_ok` true. Committed and pushed as `915c57f`.
- New sparring bot `sparring/gto_charts`: preflop ranges by stack depth, value bets plus a fixed share of bluffs, no opponent tracking.
- New tool `tools/leaks.py`: sorts every hand of every match into a spot. Output in `results/leaks.txt`.
- No strategy change. gto_charts, leaks.py and the new results are not committed yet.

**gto_charts, 250 pairs:** 53.0% match win rate (95% CI 48.6-57.3), pairings 50/165/35, 0 crashes, 0 corrected, slowest 20 ms.

**Leak report, 250 pairs each (chips per 100 hands / big blinds per 100 hands)**

| Spot | chartbot (60.0%) | threebettor (64.2%) | stealer (68.6%) | gto_charts (53.0%) |
|---|---|---|---|---|
| Our open gets re-raised: how often, we fold | 1.8 per 100, fold 92% | 35.3, fold 38% | 38.6, fold 16% | 6.0, fold 82% |
| ... result | -751 / -5.4 | +4,034 / +72.2 | +6,983 / +122.9 | -1,038 / -8.6 |
| Our big blind faces a raise: how often, we fold | 22.8, fold 42% | 29.9, fold 5% | 49.5, fold 16% | 36.8, fold 20% |
| ... result | -3,728 / -19.5 | +2,007 / +28.3 | +3,984 / +50.0 | -1,025 / -10.1 |
| Postflop bets we face: share we fold to | 48% | 48% | 43% | 58% |
| Hands where we fold to a postflop bet | -8,727 / -56.7 | -23,173 / -292.4 | -24,342 / -296.4 | -8,537 / -73.0 |
| We call a postflop bet and lose | -3,807 / -26.4 | -6,245 / -75.1 | -6,075 / -71.9 | -5,934 / -59.4 |
| We call a postflop bet and win | +5,018 / +41.8 | +16,576 / +208.1 | +15,408 / +190.9 | +5,240 / +55.1 |
| Preflop all-in showdowns: per 100, we win (cards deserved) | 0.91, 40% (43%) | 1.51, 55% (55%) | 1.58, 59% (54%) | 1.54, 46% (47%) |
| ... result | -343 / +0.3 | +91 / +0.8 | +325 / +2.0 | -441 / -1.7 |
| Postflop all-in showdowns: per 100, we win | 1.00, 50% | 4.66, 74% | 4.53, 78% | 1.49, 63% |
| ... result | +273 / +8.4 | +14,686 / +197.6 | +15,990 / +210.6 | +2,919 / +30.9 |
| Overall | +2,168 / +14.2 | +8,747 / +147.1 | +10,901 / +169.9 | +986 / +16.8 |

Reading notes:
- "Overall chips per 100" is not extra evidence. In a freezeout it equals (2 x win rate - 1) x 10,000 / match length, so it only restates the win rate.
- "We fold to a bet" is negative by construction (we lose what we already put in). It is a real leak only where the opponent bets nearly every time (threebettor, stealer) and probably against gto_charts (we fold 58% to bets that are about one third bluffs). Against chartbot, which only bets a pair or better, folding 48% is probably right.
- Folding 92% to chartbot's re-raises is right (it re-raises only premium hands). Folding 82% to gto_charts' re-raises is a leak.
- A cause found in the code: facing a bet from anyone who raised preflop, v1 always gives them the best of at least 2 random hands, however often they bet.

**When matches are decided (2,000 matches, the four bots together)**
- Match length: quartiles 27 / 43 / 77 hands. Biggest hand of the match: quartiles at hand 18 / 31 / 58.
- Blind level of the biggest hand: level 1 in 27.8% of matches, level 2 in 32.6%, level 3 in 15.4%, levels 4+ in 24.2%.
- Biggest hand was a postflop all-in in 60.0% of matches, no all-in 35.1%, preflop all-in 5.0%.
- The last hand was a preflop all-in in 35.0% of matches (chartbot 39.6%, threebettor 22.8%, stealer 25.4%, gto_charts 52.2%).

**Draws**
- Pairings W/D/L over the four: 337/555/108, so 55.5% draws.
- Most of that is arithmetic: with a 60% chance per match, two independent matches split 48% of the time. Draws only shrink when the per-match win rate rises (80% per match gives 32% draws, 90% gives 18%).
- The duplicate format adds a little: in 18.4% of draws the same deal was the biggest hand in both matches (35.2% vs gto_charts), meaning both bots played those cards the same way and the cards decided. Almost never a preflop all-in (0.2%); these are postflop stack-offs.
- To turn draws into wins we must play the same cards better than the opponent: lose less with the losing side of a big deal and win more with the winning side.

**Proposed fixes, ranked (not implemented)**
1. Read a bet by how often that opponent makes it. A bet is treated as the top X% of their hands, X = their observed frequency in that spot, starting from a guess. Biggest expected gain: threebettor, stealer, maniac-type bots.
2. Charge a premium for risking the whole stack that shrinks as blinds rise, sized from the exact all-in solve. Targets allin (ceiling 69.8% vs 65.2%).
3. Preflop: open nearly every small blind and defend re-raises by observed frequency.

**Independent reviewer's objections (fresh subagent, saw only the report, the code and the fixes)**
- Fix 1: a "top X%" range has no bluffs in it, so it does not fix over-folding to gto_charts, our worst matchup. It is blind to bet size: a bot that bets small every street and shoves only with monsters would read as "random hand" and we would call the shove. Small samples: an honest bot that happens to bet its first three flops gets called down light at 200 big blinds. Raises get only 2 to 5 chances per match, so the starting guess decides and 50% is wrong for raises (about 15%). The code needs more work than it sounds: counts are per action not per opportunity, and the simulation only supports whole-number "best of k".
- Fix 2: the right premium equals our edge over that opponent, which we cannot know in 30 hands. The top-3% range is specific to an always-shover; against an equal or better bot the premium should be about zero. It collides with fix 1 (call flop and turn, then fold the river shove with 40% of the stack in). Applied to our own shoves it would remove the all-ins that win us matches.
- Fix 3: without fix 1, defending re-raises wider turns a 2.5 bb loss into 7 to 8 bb (call, then fold the flop). Against tight re-raisers there are 1 to 3 samples per match, so the starting guess decides. Small-blind upside is at most 5 bb/100.
- Its recommendation: build fix 1 in full with a separate all-in/overbet count; shrink fix 2 to preflop only; shrink fix 3 to two constants (open-everything threshold 0.60 to 0.50, re-raise starting guess 12% to 20%).
- Tests it asked for: (1) a new sparring bot that bets a third of the pot every street and shoves only with two pair or better; chartbot and gto_charts must not drop. (2) Fix 2 must gain vs allin without losing vs gto_charts and v1_frozen. (3) vs chartbot and nit, count stacks lost in re-raised pots at levels 1 and 2.

**Open problems**
1. gto_charts at 53.0% is the worst matchup and none of the three fixes clearly targets it.
2. Still no run in the Docker sandbox.

## 10:42 — Sparring field, first screen of v1, all-in sweep

**What changed**
- 15 sparring bots written by `tools/make_sparring.py` into `sparring/`, plus `sparring/v1_frozen` (untouched copy of v1) and the existing `allin` and `bots/caller`. 18 opponents in total. All pass the validator.
- `screen.py`: v1 vs every bot in parallel, then a deeper rerun on the worst matchups. Pair k uses the same seed for every opponent and every version.
- `bot.py`: `"data_ok": DATA_OK` added to the debug output of every decision. No strategy change. The runner exits with an error if it is ever false (tested by hiding the data file: it failed loudly on 286 decisions).
- `tools/allin_sweep.py` (calling-range sweep) and `tools/allin_ceiling.py` (exact best-possible number vs an all-in bot).

**Screen: v1 vs 18 bots, 100 duplicate pairs each (127.6 s for the whole screen)**

| Opponent | Match win rate | 95% CI | Pairings W/D/L | Crashes | Corrected | Slowest |
|---|---|---|---|---|---|---|
| v1_frozen (mirror) | 49.0% | 42.2-55.9 | 15/68/17 | 0 | 0 | 41 ms |
| chartbot | 62.0% | 55.1-68.4 | 39/46/15 | 0 | 0 | 48 ms |
| threebettor | 64.0% | 57.1-70.3 | 38/52/10 | 0 | 0 | 64 ms |
| allin | 66.5% | 59.7-72.7 | 47/39/14 | 0 | 0 | 1 ms |
| stealer | 66.5% | 59.7-72.7 | 38/57/5 | 0 | 0 | 43 ms |
| adaptive | 71.0% | 64.4-76.8 | 46/50/4 | 0 | 0 | 40 ms |
| lateshover | 74.5% | 68.0-80.0 | 53/43/4 | 0 | 0 | 45 ms |
| potbettor | 80.0% | 73.9-85.0 | 62/36/2 | 0 | 0 | 37 ms |
| maniac | 81.0% | 75.0-85.8 | 64/34/2 | 0 | 0 | 44 ms |
| random | 84.0% | 78.3-88.4 | 71/26/3 | 0 | 0 | 36 ms |
| nashpush | 86.5% | 81.1-90.5 | 75/23/2 | 0 | 0 | 1 ms |
| oddsizer | 86.5% | 81.1-90.5 | 73/27/0 | 0 | 0 | 37 ms |
| bluffer | 89.0% | 83.9-92.6 | 78/22/0 | 0 | 0 | 42 ms |
| potodds | 90.5% | 85.6-93.8 | 81/19/0 | 0 | 0 | 37 ms |
| trapper | 90.5% | 85.6-93.8 | 81/19/0 | 0 | 0 | 42 ms |
| minraiser | 95.5% | 91.7-97.6 | 91/9/0 | 0 | 0 | 24 ms |
| caller | 97.5% | 94.3-98.9 | 95/5/0 | 0 | 0 | 39 ms |
| nit | 99.0% | 96.4-99.7 | 98/2/0 | 0 | 0 | 17 ms |

Totals: 2,867/3,600 matches (79.6%), 286,568 decisions, 0 crashes, 0 timeouts, 0 corrected actions, slowest 64 ms.

**Deep: 250 pairs on the 4 worst (mirror excluded), 69.4 s**

| Opponent | Match win rate | 95% CI | Pairings W/D/L | Crashes | Corrected | Slowest |
|---|---|---|---|---|---|---|
| chartbot | 59.6% | 55.2-63.8 | 88/122/40 | 0 | 0 | 50 ms |
| threebettor | 62.6% | 58.3-66.7 | 87/139/24 | 0 | 0 | 54 ms |
| allin | 65.2% | 60.9-69.2 | 105/116/29 | 0 | 0 | 7 ms |
| stealer | 66.6% | 62.4-70.6 | 97/139/14 | 0 | 0 | 80 ms |

**Sweep: fixed calling range vs always-all-in, 1,000 pairs (2,000 matches) each**

| Range played | Weakest hand | Match win rate | 95% CI |
|---|---|---|---|
| top 5% | AJs | 61.8% | 59.6-63.9 |
| top 10% | KJs | 66.3% | 64.2-68.3 |
| top 15% | A5s | 64.5% | 62.4-66.6 |
| top 20% | QJo | 62.3% | 60.1-64.3 |
| top 30% | J9s | 61.1% | 58.9-63.2 |
| top 40% | J7s | 59.0% | 56.8-61.1 |
| top 50% | J5s | 57.0% | 54.9-59.2 |
| v1 as it is | - | 65.2% | 63.1-67.3 |

Exact ceiling (solved backwards from the end of the match, ties counted as half a win): **69.8%**.
It is reached only by a range that changes with the blinds: about top 3% at 25/50 with even stacks,
17% at 150/300, 44% at 400/800, 74% at 1000/2000, and wider when either stack is short.

**Reading**
- v1 at 65.2% equals the best fixed range (66.3%) within noise. The ceiling is 4.6 points higher.
- No bad matchup below 59%, but chartbot, threebettor and stealer are all under 67%.

**Open problems**
1. chartbot 59.6%: cause not diagnosed yet. Matches run long (91 hands), so it is decided in the high-blind phase.
2. threebettor 62.6% and stealer 66.6%: v1 probably gives up too often to preflop raises and re-raises. Not diagnosed yet.
3. allin 65.2%: a blind-level table from the solver could add up to 4.6 points.
4. Many pairings end as draws (one win each), even against bots we beat.
5. Still no run in the Docker sandbox (half a CPU core).
6. Nothing from this step is committed or pushed yet.

## 10:25 — v1 pushed

- v1 built: safety wrapper, preflop tables, opponent counters, postflop equity, equity vs pot odds.
- 250 pairs each, real bot processes: caller 95.8%, always-all-in 65.2%, template 100%.
- 0 crashes, 0 timeouts, 0 corrected actions over 64,182 decisions. Slowest decision 79 ms. Validator passed.
- Pushed to main as commit `ed163ae`.
