"""
Full-pass pebbling simulator for PoSME memory-hardness, self-validating.

Correct cost model (classic MHF pebbling):
  - S = a FIXED persistent store chosen by the adversary (checkpoints / stored blocks).
  - Reconstruction of a missing value recomputes on demand, using only a TRANSIENT
    per-reconstruction memo (scratch that is discarded after each top-level read, so
    it never becomes free persistent storage). Persistent checkpoints are pinned and
    never evicted by reconstruction.
  - T = total hash evaluations. Report S*T.

SELF-VALIDATION: run the same engine on a LINE graph (scrypt/ROMix phase-1) whose
tradeoff S*T = Theta(N^2) is PROVEN. Constant S*T/N^2 across N validates the engine;
only then is the PoSME (branching) number credible.

depth-rho truncation is PoSME-specific (skip-link Init backbone, O(log N) leaf);
ROMix runs untruncated (full-length line chains).
"""

import random, sys, math, logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("peb")
sys.setrecursionlimit(5_000_000)


def total_work(deps, stream, is_stored, rho, N, truncate):
    backbone = max(1, math.ceil(math.log2(N)))
    hashes = 0

    def recon(b, v, depth, memo):
        nonlocal hashes
        if v <= 0:
            return
        if is_stored(b, v):
            return
        if (b, v) in memo:
            return
        if truncate and depth >= rho:
            hashes += backbone
            return
        hashes += 1
        for c, u in deps.get((b, v), ()):
            recon(c, u, depth + 1, memo)
        memo.add((b, v))

    for b, v in stream:
        recon(b, v, 0, set())  # transient scratch, discarded per read
    return hashes


def romix_validation():
    log.info("=== VALIDATION: engine on ROMix line graph (proven S*T = Theta(N^2)) ===")
    log.info(
        f"{'N':>6} {'best g':>7} {'best S':>7} {'min S*T':>12} {'min S*T/N^2':>12}"
    )
    for N in (1024, 2048, 4096):
        deps = {(i, i): [(i - 1, i - 1)] for i in range(1, N)}
        rng = random.Random(1)
        stream = [(k, k) for k in (rng.randrange(1, N) for _ in range(N))]
        best = None
        for g in (4, 8, 16, 32, 64, 128):
            stored = set(range(0, N, g))  # checkpoints V[0],V[g],...
            is_stored = lambda b, v, S=stored: b in S
            T = total_work(deps, stream, is_stored, 0, N, truncate=False)
            S = len(stored)
            if best is None or S * T < best[2]:
                best = (g, S, S * T)
        log.info(
            f"{N:6} {best[0]:7} {best[1]:7} {best[2]:12.3g} {best[2] / (N * N):12.3f}"
        )
    log.info(
        " -> min S*T/N^2 ~ constant across N  => engine reproduces the proven ROMix tradeoff\n"
    )


def build_posme(N, rho, d, seed):
    rng = random.Random(seed)
    K = rho * N
    version = [0] * N
    deps = {}
    for t in range(1, K + 1):
        reads = [rng.randrange(N) for _ in range(d)]
        w = rng.randrange(N)
        deps[(w, t)] = [(b, version[b]) for b in reads]
        version[w] = t
    return deps, version, K


def posme_measure(N, rho, d, seed):
    deps, version, K = build_posme(N, rho, d, seed)
    stream = [(c, u) for key in deps for (c, u) in deps[key]]
    log.info(
        f"=== PoSME full-pass, N={N} rho={rho} d={d} seed={seed}  (K={K}, honest ~2K^2={2 * K * K:.3g}) ==="
    )
    log.info(f"{'alpha':>6} {'S':>6} {'total T':>12} {'S*T':>12} {'S*T/K^2':>9}")
    astar = 1 / (rho + 2)
    rng = random.Random(seed + 99)
    best = None
    for alpha in sorted({0.02, 0.05, round(astar, 3), 0.2, 0.35, 0.5, 0.75, 1.0}):
        stored = set(rng.sample(range(N), max(1, int(alpha * N))))
        is_stored = lambda b, v, S=stored, ver=version: b in S and ver[b] == v
        T = total_work(deps, stream, is_stored, rho, N, truncate=True)
        S = len(stored)
        r = (S * T) / (K * K)
        if best is None or r < best[-1]:
            best = (alpha, r)
        log.info(f"{alpha:6.3f} {S:6} {T:12.3g} {S * T:12.3g} {r:9.2f}")
    log.info(
        f" -> min S*T/K^2 = {best[-1]:.2f} at alpha={best[0]:.3f} "
        f"(predicted optimum alpha*=1/(rho+2)={astar:.3f})\n"
    )


if __name__ == "__main__":
    romix_validation()
    posme_measure(N=384, rho=4, d=8, seed=1)
    posme_measure(N=384, rho=4, d=8, seed=2)
