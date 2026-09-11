"""
PoSME memory-hardness stress test (depth-rho truncated, faithful to paper's W).

Reconstruction terminates when a branch (a) reaches the Init state (version 0),
(b) hits a LIVE stored block (stored AND current version == needed historical
version), or (c) reaches recursion depth rho -> the static skip-link backbone,
charged O(log N). This matches Theorem 3's W(alpha,rho)=sum_{l=0}^rho [d(1-a)]^l.

Key subtlety it exposes: a stored block helps ONLY if its CURRENT value equals
the needed HISTORICAL version. Under random writes it is usually stale, so the
effective hit rate is below alpha (Theorem 4). We measure:
  naive/miss  : per-miss branching cost (no cross-miss reuse)
  memo/miss   : amortized cost with a persistent memo across all misses (the attack)
  footprint   : distinct historical states the memo had to hold, as a multiple of N
  S*T check   : (alpha*N + footprint) * T_total  vs  K^2   (does the bound survive?)
"""

import random, sys, math, logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("posme")
sys.setrecursionlimit(1_000_000)


def build_history(N, K, d, seed):
    rng = random.Random(seed)
    version = [0] * N
    deps = {}
    for t in range(1, K + 1):
        reads = [rng.randrange(N) for _ in range(d)]
        w = rng.randrange(N)
        deps[(w, t)] = [(b, version[b]) for b in reads]
        version[w] = t
    return version, deps


def make_recon(deps, stored, cur_version, rho, backbone):
    def recon(b, v, depth, memo):
        if v == 0:
            return 1
        if memo is not None and (b, v) in memo:
            return 0
        if depth >= rho:
            return backbone  # static skip-link backbone terminates the branch
        cost = 1
        for c, u in deps.get((b, v), ()):
            if stored[c] and cur_version[c] == u:  # LIVE stored hit (not stale)
                continue
            cost += recon(c, u, depth + 1, memo)
        if memo is not None:
            memo.add((b, v))
        return cost

    return recon


def theoretical_W(alpha, rho, d):
    return sum((d * (1 - alpha)) ** l for l in range(rho + 1))


def run(N=4096, rho=4, d=8, seed=1, n_samples=500):
    K = rho * N
    backbone = max(1, math.ceil(math.log2(N)))
    version, deps = build_history(N, K, d, seed)
    rng = random.Random(seed + 99)
    log.info(
        f"N={N} K={K} rho={rho} d={d}  honest S*T ~ 2K^2 = {2 * K * K:.3g}, backbone={backbone}"
    )
    log.info(
        f"{'alpha':>6} {'W_flat':>9} {'naive/miss':>11} {'memo/miss':>10} "
        f"{'reuse':>7} {'footprint':>10} {'(S+memo)*T / K^2':>18}"
    )
    for alpha in (1 / 6, 1 / 4, 1 / 2, 3 / 4, 7 / 8):
        n_store = int(alpha * N)
        stored_ids = set(rng.sample(range(N), n_store))
        stored = [i in stored_ids for i in range(N)]
        recon = make_recon(deps, stored, version, rho, backbone)
        misses = [
            b for b in rng.sample(range(N), min(n_samples * 2, N)) if not stored[b]
        ][:n_samples]
        naive = [recon(b, version[b], 0, None) for b in misses]
        naive_avg = sum(naive) / len(naive)
        memo = set()
        memo_total = sum(recon(b, version[b], 0, memo) for b in misses)
        memo_avg = memo_total / len(misses)
        Wt = theoretical_W(alpha, rho, d)
        reuse = naive_avg / memo_avg if memo_avg else float("inf")
        foot = len(memo) / N
        # Bound survival: total hashes to answer these misses under the memo attack is
        # memo_total; the adversary's real storage is alpha*N + memo footprint. Scale the
        # per-miss cost to a full forward pass (K*d*(1-alpha) misses) to compare with K^2.
        full_misses = K * d * (1 - alpha)
        T_full = full_misses * memo_avg
        S_real = alpha * N + len(memo)
        st_ratio = (S_real * T_full) / (K * K)
        log.info(
            f"{alpha:6.3f} {Wt:9.1f} {naive_avg:11.1f} {memo_avg:10.1f} "
            f"{reuse:6.2f}x {foot:9.2f}N {st_ratio:17.2f}"
        )


if __name__ == "__main__":
    log.info("=== PoSME TMTO stress test: can memoization beat W(alpha,rho)? ===\n")
    run()
    log.info("\nReads:")
    log.info(
        " naive/miss vs W_flat: naive >= W_flat confirms staleness raises cost (Thm 4)"
    )
    log.info(
        " reuse large + footprint ~O(N): memo attack works ONLY by returning to full storage (defense B)"
    )
    log.info(" (S+memo)*T / K^2 >= ~1: space-time lower bound survives the memo attack")
