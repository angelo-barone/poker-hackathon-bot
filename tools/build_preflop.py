"""Offline table builder (not part of the bot; run once on a laptop).

Step 1  sample random heads-up all-in deals and record, for every pair of
        starting-hand classes (169 x 169), how often the first one wins.
Step 2  from that matrix, solve the all-in-or-fold game for short stacks
        (fictitious play, the standard way to find the Nash ranges).

Writes my_bots/v1/data/preflop.json.

  python tools/build_preflop.py --samples 60000000 --workers 8
"""

import argparse
import json
import multiprocessing as mp
import os
import random
import time

import eval7

RANKS = "AKQJT98765432"
SUITS = "shdc"


def class_names():
    names = []
    for i, a in enumerate(RANKS):
        for j, b in enumerate(RANKS):
            if i == j:
                names.append(a + b)
            elif i < j:
                names.append(a + b + "s")
            else:
                names.append(b + a + "o")
    return names


NAMES = class_names()
IDX = {n: k for k, n in enumerate(NAMES)}


def hand_class(c1, c2):
    r1, r2 = c1[0], c2[0]
    if r1 == r2:
        return r1 + r2
    if RANKS.index(r1) > RANKS.index(r2):
        r1, r2 = r2, r1
    return r1 + r2 + ("s" if c1[1] == c2[1] else "o")


def combos(name):
    return 6 if len(name) == 2 else (4 if name[2] == "s" else 12)


def sample_worker(args):
    n, seed = args
    rng = random.Random(seed)
    strs = [r + s for r in RANKS for s in SUITS]
    cards = [eval7.Card(c) for c in strs]
    cls = {}
    for a in range(52):
        for b in range(52):
            if a != b:
                cls[(a, b)] = IDX[hand_class(strs[a], strs[b])]
    win = [0.0] * (169 * 169)
    cnt = [0] * (169 * 169)
    ids = list(range(52))
    ev = eval7.evaluate
    sample = rng.sample
    for _ in range(n):
        s = sample(ids, 9)
        board = [cards[x] for x in s[4:]]
        a = ev([cards[s[0]], cards[s[1]]] + board)
        b = ev([cards[s[2]], cards[s[3]]] + board)
        i = cls[(s[0], s[1])]
        j = cls[(s[2], s[3])]
        k1 = i * 169 + j
        k2 = j * 169 + i
        cnt[k1] += 1
        cnt[k2] += 1
        if a > b:
            win[k1] += 1.0
        elif b > a:
            win[k2] += 1.0
        else:
            win[k1] += 0.5
            win[k2] += 0.5
    return win, cnt


def solve_pushfold(eq, pair_w, stack, ante, iters=3000):
    """Nash ranges for: small blind shoves or folds, big blind calls or folds.
    Units are big blinds. Returns (push_prob[169], call_prob[169])."""
    import numpy as np
    E = np.array(eq)
    W = np.array(pair_w)
    win_pot = 2 * stack + 2 * ante
    risk = stack + ante
    called = W * (E * win_pot - risk)          # shover's result when called, weighted
    stolen = W * (1 + ante)                    # shover's result when the caller folds
    row_w = W.sum(axis=1)
    caller = W * (E.T * win_pot - risk)        # caller's result [shover i, caller j]
    push = np.full(169, 0.5)
    call = np.full(169, 0.5)
    for t in range(1, iters + 1):
        ev_push = (called @ call + stolen @ (1 - call)) / row_w
        br_push = (ev_push > -(0.5 + ante)).astype(float)
        ev_call = (push @ caller) / np.maximum(push @ W, 1e-12)
        br_call = (ev_call > -(1 + ante)).astype(float)
        a = 1.0 / (t + 1)
        push += a * (br_push - push)
        call += a * (br_call - call)
    return push.tolist(), call.tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=40_000_000)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--out", default=os.path.join("my_bots", "v1", "data", "preflop.json"))
    args = ap.parse_args()

    t0 = time.time()
    chunk = 250_000
    tasks = [(chunk, 1000 + k) for k in range(args.samples // chunk)]
    win = [0.0] * (169 * 169)
    cnt = [0] * (169 * 169)
    with mp.Pool(args.workers) as pool:
        for w, c in pool.imap_unordered(sample_worker, tasks):
            for k in range(169 * 169):
                win[k] += w[k]
                cnt[k] += c[k]
        print(f"sampled {args.samples:,} deals in {time.time() - t0:.0f}s, "
              f"smallest cell {min(cnt):,}", flush=True)

        eq = [[(win[i * 169 + j] / cnt[i * 169 + j]) if cnt[i * 169 + j] else 0.5
               for j in range(169)] for i in range(169)]
        total = sum(cnt)
        pair_w = [[cnt[i * 169 + j] / total for j in range(169)] for i in range(169)]

        # equity of each class against a random hand, and the ranking it gives
        vs_random = [sum(pair_w[i][j] * eq[i][j] for j in range(169)) / sum(pair_w[i])
                     for i in range(169)]
        order = sorted(range(169), key=lambda i: -vs_random[i])

        stacks = [x / 2 for x in range(2, 41)]            # 1.0 .. 20.0 big blinds
        jobs = [(s, a) for a in (0.0, 0.1) for s in stacks]
        tables = {"0": {}, "0.1": {}}
        for s, a in jobs:
            p, c = solve_pushfold(eq, pair_w, s, a)
            key = "0" if a == 0 else "0.1"
            tables[key][f"{s:g}"] = {
                "push": "".join("1" if x >= 0.5 else "0" for x in p),
                "call": "".join("1" if x >= 0.5 else "0" for x in c),
            }
        print(f"solved {len(jobs)} push/fold games, total {time.time() - t0:.0f}s", flush=True)

    out = {
        "names": NAMES,
        "combos": [combos(n) for n in NAMES],
        "order": order,                                   # class indices, strongest first
        "vs_random": [round(x, 4) for x in vs_random],
        "eq": [[int(round(eq[i][j] * 10000)) for j in range(169)] for i in range(169)],
        "pushfold": tables,                               # ante("0"/"0.1") -> stack -> bit strings
        "samples": args.samples,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote", args.out, os.path.getsize(args.out) // 1024, "KB")
    for s in ("5", "10", "15"):
        t = tables["0"][s]
        print(f"  {s}bb: push {sum(combos(NAMES[i]) for i in range(169) if t['push'][i] == '1') / 13.26:.1f}%"
              f"  call {sum(combos(NAMES[i]) for i in range(169) if t['call'][i] == '1') / 13.26:.1f}%")


if __name__ == "__main__":
    main()
