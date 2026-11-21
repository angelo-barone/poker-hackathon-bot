#!/usr/bin/env python3
"""Duplicate-match runner: the tournament's qualification format, on a laptop.

Each PAIR is two freezeout matches on the same seed (the same cards), with the
seats swapped. Win both = pairing win, one each = draw. It uses the organisers'
own table and engine code (pokercore), untouched.

  python arena.py my_bots/v1 bots/caller --pairs 200
  python arena.py my_bots/v1 sparring/allin --pairs 200 --workers 6
  python arena.py my_bots/v1 bots/caller --pairs 20 --real     # real sandboxed bot processes

Default mode calls each bot's decide() directly in this process (fast). --real
starts the bots exactly as play.py does (slower, but the tournament's own path).

For the FIRST bot it reports: match win rate, pairing record, crashes,
timeouts, corrected actions (anything the engine had to change) and the
slowest decision.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import multiprocessing as mp
import os
import random
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# The local (non-Docker) bot process gets a stripped environment; on Windows
# Python cannot start without these, so let them through. Does not touch pokercore.
os.environ.setdefault("BOT_ENV_ALLOW", "SYSTEMROOT,SystemRoot,WINDIR,windir,TEMP,TMP,"
                      "USERPROFILE,COMSPEC,PATHEXT,NUMBER_OF_PROCESSORS")

from pokercore import structures                      # noqa: E402
from pokercore.seats import BotSeat, Seat             # noqa: E402
from pokercore.seeds import derive_seed               # noqa: E402
from pokercore.table import MatchConfig, play_match   # noqa: E402

VALID = ("fold", "check", "call", "raise", "all_in")


def _bot_file(path):
    p = Path(path)
    return p if p.suffix == ".py" else p / "bot.py"


def _bot_name(path):
    p = Path(path).resolve()
    return p.parent.name if p.name == "bot.py" else p.name


class LocalSeat(Seat):
    """A bot called directly in this process. Mirrors pokercore/sandbox/runner.py:
    a fresh module per match, the same per-decision seeding, a fold on any
    exception, bad return value or overrun of the time limit."""

    kind = "bot"

    def __init__(self, name, path, seed, time_limit_ms=2000):
        super().__init__(name, time_limit_ms)
        self.path, self.seed = str(_bot_file(path)), seed
        self.module = None
        self.errors = []
        self.decisions = 0
        self.think_total = 0.0
        self.think_max = 0.0
        self.timeouts = 0

    def _seed(self, *parts):
        digest = hashlib.sha256(":".join(str(p) for p in (self.seed,) + parts).encode()).digest()
        random.seed(int.from_bytes(digest[:8], "big"))

    def start(self):
        self._seed("load")
        data_dir = os.path.join(os.path.dirname(os.path.abspath(self.path)), "data")
        os.environ["BOT_DATA_DIR"] = data_dir
        spec = importlib.util.spec_from_file_location("bot_" + self.name + "_" + str(self.seed), self.path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def warmup(self):
        self._seed("warmup")
        try:
            self.module.decide({"type": "warmup"})
        except Exception:
            pass
        return {"ok": True}

    def request_action(self, state):
        msg = dict(state)
        msg["time_limit_ms"] = self.time_limit_ms
        self._seed(msg.get("hand_num"), len(msg.get("action_log") or []))
        t0 = time.perf_counter()
        try:
            raw = self.module.decide(msg)
        except Exception:
            self.errors.append("exception")
            return self._done({"action": "fold", "error": "exception",
                               "error_detail": traceback.format_exc()[-2000:]}, t0)
        ms = (time.perf_counter() - t0) * 1000
        if ms > self.time_limit_ms:
            self.errors.append("timeout")
            self.timeouts += 1
            return self._done({"action": "fold", "error": "timeout"}, t0)
        if not isinstance(raw, dict) or "action" not in raw:
            self.errors.append("invalid_return")
            return self._done({"action": "fold", "error": "invalid_return"}, t0)
        reply = {"action": str(raw["action"])}
        if raw.get("amount") is not None:
            try:
                reply["amount"] = int(raw["amount"])
            except (TypeError, ValueError):
                reply["amount"] = 0
        if "debug" in raw:
            reply["debug"] = raw["debug"]
        return self._done(reply, t0)

    def _done(self, reply, t0):
        ms = (time.perf_counter() - t0) * 1000
        reply["think_ms"] = round(ms, 3)
        self.decisions += 1
        self.think_total += ms
        self.think_max = max(self.think_max, ms)
        return reply

    def summary(self):
        n = self.decisions
        return {"decisions": n, "avg_think_ms": round(self.think_total / n, 3) if n else 0.0,
                "max_think_ms": round(self.think_max, 3), "timeouts": self.timeouts,
                "errors": len(self.errors), "restarts": 0, "disabled": False,
                "errors_list": self.errors[:50]}


class Audit:
    """The match log: counts what the engine had to correct for each bot."""

    def __init__(self, out=None):
        self.out = open(out, "w") if out else None
        self.n = 0
        self.per_bot = {}
        self.examples = []

    def _bot(self, name):
        return self.per_bot.setdefault(name, {"decisions": 0, "errors": 0, "corrected": 0,
                                              "free_folds": 0, "max_ms": 0.0, "sum_ms": 0.0})

    def emit(self, event_type, **data):
        event = {"i": self.n, "type": event_type, **data}
        self.n += 1
        if self.out:
            self.out.write(json.dumps(event, default=str) + "\n")
        if event_type == "decision":
            b = self._bot(data["bot"])
            b["decisions"] += 1
            ms = data.get("think_ms") or 0.0
            b["max_ms"] = max(b["max_ms"], ms)
            b["sum_ms"] += ms
            reply, applied, state = data["reply"], data["applied"], data["state"]
            asked = str(reply.get("action") or "").lower().strip()
            problem = None
            if data.get("error"):
                b["errors"] += 1
                problem = "error:" + str(data["error"])
            elif asked not in VALID:
                problem = "unknown action %r" % asked
            elif asked != applied["action"]:
                problem = "%s played as %s" % (asked, applied["action"])
            elif asked == "raise" and int(reply.get("amount") or 0) != applied["amount"]:
                problem = "raise %s played as %s" % (reply.get("amount"), applied["amount"])
            if problem and not data.get("error"):
                b["corrected"] += 1
            if problem and len(self.examples) < 5:
                self.examples.append({"bot": data["bot"], "hand": data["hand"], "problem": problem,
                                      "street": data["street"], "owed": state.get("amount_owed"),
                                      "detail": data.get("error_detail")})
            if applied["action"] == "fold" and state.get("can_check"):
                b["free_folds"] += 1
        return event

    def close(self):
        if self.out:
            self.out.close()


def play_one(bot_a, bot_b, seed, first, real, log_path=None):
    """One freezeout match. `first` (0/1) says which bot takes seat 0."""
    paths = [bot_a, bot_b]
    names = ["A:" + _bot_name(bot_a), "B:" + _bot_name(bot_b)]
    order = [0, 1] if first == 0 else [1, 0]
    seats = []
    for k in order:
        bot_seed = derive_seed(seed, "bot", names[k])
        if real:
            spec = type("Spec", (), {"name": names[k], "path": paths[k], "hash": None, "source": "local"})()
            seats.append(BotSeat(spec, seed=bot_seed, use_docker=False))
        else:
            seats.append(LocalSeat(names[k], paths[k], bot_seed))
    config = MatchConfig(mode="freezeout", hands=2000, starting_stack=10_000,
                         structure=structures.parse("standard", 10_000), seed=seed)
    audit = Audit(log_path)
    try:
        result = play_match(seats, config, "arena", audit)
    finally:
        audit.close()
    winner = None
    for r in result["results"]:
        if r["place"] == 1 and r["final_stack"] > 0:
            winner = r["bot"]
    a = audit.per_bot.get(names[0], {})
    summ = {r["bot"]: r for r in result["results"]}
    a_res = summ.get(names[0], {})
    return {
        "a_won": winner == names[0], "hands": result["hands"], "stopped": result["stopped"],
        "decisions": a.get("decisions", 0), "errors": a.get("errors", 0),
        "corrected": a.get("corrected", 0), "free_folds": a.get("free_folds", 0),
        "max_ms": a.get("max_ms", 0.0), "sum_ms": a.get("sum_ms", 0.0),
        "timeouts": a_res.get("timeouts") or 0, "restarts": a_res.get("restarts") or 0,
        "examples": [e for e in audit.examples if e["bot"] == names[0]],
    }


def play_pair(args):
    bot_a, bot_b, seed, real = args
    try:
        return seed, [play_one(bot_a, bot_b, seed, 0, real), play_one(bot_a, bot_b, seed, 1, real)]
    except Exception:
        return seed, {"crash": traceback.format_exc()[-1500:]}


def wilson(wins, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = wins / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return centre - half, centre + half


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bot_a")
    ap.add_argument("bot_b")
    ap.add_argument("--pairs", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1, help="base seed; pair k uses a seed derived from it")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--real", action="store_true", help="sandboxed bot processes, as play.py runs them")
    ap.add_argument("--json", metavar="FILE", help="also write the summary as JSON")
    args = ap.parse_args()

    seeds = [derive_seed(args.seed, "pair", k) % (2 ** 31) for k in range(args.pairs)]
    jobs = [(args.bot_a, args.bot_b, s, args.real) for s in seeds]
    t0 = time.time()
    matches, pair_w, pair_d, pair_l, runner_crashes = [], 0, 0, 0, []
    with mp.Pool(args.workers) as pool:
        for seed, res in pool.imap_unordered(play_pair, jobs):
            if isinstance(res, dict):
                runner_crashes.append((seed, res["crash"]))
                continue
            matches += res
            won = sum(1 for m in res if m["a_won"])
            pair_w += won == 2
            pair_d += won == 1
            pair_l += won == 0

    n = len(matches)
    wins = sum(1 for m in matches if m["a_won"])
    lo, hi = wilson(wins, n)
    pairs = pair_w + pair_d + pair_l
    decisions = sum(m["decisions"] for m in matches)
    summary = {
        "bot": args.bot_a, "opponent": args.bot_b, "mode": "real" if args.real else "in-process",
        "pairs": pairs, "matches": n, "match_wins": wins,
        "match_win_rate": round(wins / n, 4) if n else None,
        "ci95": [round(lo, 4), round(hi, 4)],
        "pairings": {"win": pair_w, "draw": pair_d, "loss": pair_l},
        "points_per_pairing": round((pair_w + 0.5 * pair_d) / pairs, 4) if pairs else None,
        "decisions": decisions,
        "crashes": sum(m["errors"] for m in matches),
        "timeouts": sum(m["timeouts"] for m in matches),
        "restarts": sum(m["restarts"] for m in matches),
        "corrected_actions": sum(m["corrected"] for m in matches),
        "free_folds": sum(m["free_folds"] for m in matches),
        "slowest_ms": round(max((m["max_ms"] for m in matches), default=0.0), 1),
        "avg_ms": round(sum(m["sum_ms"] for m in matches) / decisions, 2) if decisions else 0.0,
        "avg_hands": round(sum(m["hands"] for m in matches) / n, 1) if n else 0,
        "hand_limit_matches": sum(1 for m in matches if m["stopped"] != "one_player_left"),
        "runner_crashes": len(runner_crashes),
        "seconds": round(time.time() - t0, 1),
    }
    print(f"\n{_bot_name(args.bot_a)} vs {_bot_name(args.bot_b)}  "
          f"({summary['mode']}, {pairs} duplicate pairs, {n} matches, {summary['seconds']}s)")
    print(f"  match win rate      {wins}/{n} = {100 * wins / max(n, 1):.1f}%   "
          f"(95% CI {100 * lo:.1f}-{100 * hi:.1f}%)")
    print(f"  pairings W/D/L      {pair_w}/{pair_d}/{pair_l}   "
          f"points per pairing {summary['points_per_pairing']}")
    print(f"  crashes             {summary['crashes']}   timeouts {summary['timeouts']}   "
          f"restarts {summary['restarts']}")
    print(f"  corrected actions   {summary['corrected_actions']}   (folds when a check was free: "
          f"{summary['free_folds']})")
    print(f"  slowest decision    {summary['slowest_ms']} ms   (average {summary['avg_ms']} ms over "
          f"{decisions:,} decisions)")
    print(f"  average match       {summary['avg_hands']} hands")
    examples = [e for m in matches for e in m["examples"]][:5]
    for e in examples:
        print("  example problem:", e)
    for seed, tb in runner_crashes[:2]:
        print(f"  RUNNER CRASH on seed {seed}:\n{tb}")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(summary, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
