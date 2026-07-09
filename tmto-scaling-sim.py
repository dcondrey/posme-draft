"""
EUROCRYPT-grade question: is PoSME memory-hardness BOUNDED (Argon2-class,
per-miss recomputation ~d^rho independent of N) or UNBOUNDED (scrypt-class,
growing with N)?  This is decided by how deep reconstruction must go before
reaching the Init state, and how per-miss cost scales with N at FIXED rho.

Method (no depth truncation, reconstruct to the TRUE Init v=0):
  - build the PoSME dependency DAG (uniform ROM addressing, faithful per the
    paper's Theorem 2), fixed rho, vary N.
  - for random current-value misses at zero persistent storage (alpha=0, the
    worst case), reconstruct fully to Init with a per-reconstruction memo
    (cost = distinct nodes = the true recomputation work, no double counting).
  - measure: mean/max recursion DEPTH to Init, and per-miss COST vs N.
  - fit: does cost saturate (bounded) or grow as a power of N (unbounded)?

Decisive: depth ~ rho and cost saturating as N grows => BOUNDED (Argon2-class).
          depth ~ log K or cost growing with N          => UNBOUNDED (scrypt-class).
"""

import random, sys, math, logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("sc")
sys.setrecursionlimit(20_000_000)
NODE_BUDGET = 3_000_000


def build(N, rho, d, seed):
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


def recon_full(deps, b, v):
    # reconstruct (b,v) fully to Init; return (distinct_nodes, max_depth, exploded)
    memo = set()
    max_depth = [0]
    exploded = [False]
    stack = [(b, v, 0)]
    while stack:
        if len(memo) > NODE_BUDGET:
            exploded[0] = True
            break
        node = stack.pop()
        bb, vv, dep = node
        if vv <= 0 or (bb, vv) in memo:
            continue
        memo.add((bb, vv))
        if dep > max_depth[0]:
            max_depth[0] = dep
        for c, u in deps.get((bb, vv), ()):
            if (c, u) not in memo:
                stack.append((c, u, dep + 1))
    return len(memo), max_depth[0], exploded[0]


def run(rho=4, d=8, seed=1, n_samples=150):
    log.info(
        f"=== reconstruction scaling at FIXED rho={rho}, d={d} (alpha=0 worst case) ==="
    )
    log.info(
        f"{'N':>6} {'K':>7} {'depth_mean':>10} {'depth_max':>9} {'cost_mean':>10} "
        f"{'cost/d^rho':>10} {'exploded%':>9}"
    )
    prev = None
    dpow = d**rho
    for N in (256, 512, 1024, 2048, 4096):
        deps, version, K = build(N, rho, d, seed)
        rng = random.Random(seed + 5)
        samp = [b for b in rng.sample(range(N), min(n_samples, N)) if version[b] > 0][
            :n_samples
        ]
        depths, costs, expl = [], [], 0
        for b in samp:
            c, dep, ex = recon_full(deps, b, version[b])
            costs.append(c)
            depths.append(dep)
            expl += ex
        dm = sum(depths) / len(depths)
        cm = sum(costs) / len(costs)
        log.info(
            f"{N:6} {K:7} {dm:10.2f} {max(depths):9} {cm:10.1f} {cm / dpow:10.3f} "
            f"{100 * expl / len(samp):8.1f}%"
        )
    log.info(
        f"\n d^rho = {dpow}. If cost_mean saturates (cost/d^rho ~ const) and depth ~ rho={rho}"
    )
    log.info(" as N grows 16x -> BOUNDED memory-hardness (Argon2-class).")
    log.info(" If cost_mean grows with N -> UNBOUNDED (scrypt-class).")


def run_vary_rho(N=1024, d=8, seed=1, n_samples=120):
    log.info(
        f"\n=== depth vs rho at FIXED N={N} (does depth track rho, per the paper's claim?) ==="
    )
    log.info(
        f"{'rho':>4} {'K':>7} {'depth_mean':>10} {'depth_max':>9} {'cost_mean':>10}"
    )
    for rho in (2, 4, 8):
        deps, version, K = build(N, rho, d, seed)
        rng = random.Random(seed + 5)
        samp = [b for b in rng.sample(range(N), min(n_samples, N)) if version[b] > 0][
            :n_samples
        ]
        depths, costs = [], []
        for b in samp:
            c, dep, ex = recon_full(deps, b, version[b])
            costs.append(c)
            depths.append(dep)
        log.info(
            f"{rho:4} {K:7} {sum(depths) / len(depths):10.2f} {max(depths):9} {sum(costs) / len(costs):10.1f}"
        )
    log.info(" paper predicts depth ~ rho (arithmetic ~N regression per level).")


if __name__ == "__main__":
    run()
    run_vary_rho()
