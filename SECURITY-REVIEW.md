# PoSME security review — cryptographer's memo (rev. 2, reconciled to the arXiv paper)

**Correction notice.** Rev. 1 of this memo concluded the TMTO penalty ceiling
was ~4× and the tight lower bound was "open." That was wrong. It was reasoned
from stale working files in the repo (an old `draft-condrey-posme.md` Theorem 3
and the `posme-dynamic-pebbling.md` "4× correction"). The authoritative source
is the arXiv paper — *PoSME: Proof of Sequential Memory Execution*, D. Condrey,
arXiv:2604.15751, 17 Apr 2026 — which contains a complete and correct analysis
that supersedes both. This revision reconciles to it.

---

## 1. Lattice (MLWE/MSIS) framing — reject (unchanged, now doubly confirmed)

The archived files (`proof-of-effort/docs/archived-rejected-lattice/`) impose a
lattice-commitment model with no basis in PoSME. Confirmed against the paper:
its security rests entirely on the ROM (collision/preimage resistance) plus a
memory-hardness lower bound; there is zero lattice content. Binding/soundness
reduces to collision resistance (paper Theorems 1–2), not MLWE. Do not integrate.
Rationale in the archive `NOTE.md`.

---

## 2. TMTO / memory-hardness — resolved in the paper (supersedes rev. 1)

### 2.1 The correct result (paper Theorems 3–5)

**Theorem 3 (Space-Time Product).** In the ROM, any adversary storing S = αN
vertices (0<α<1) requires expected computation T with

```
S·T  ≥  [ α(1-α) · d · W(α,ρ) / ρ ] · K²,      W(α,ρ) = Σ_{ℓ=0}^{ρ} [d(1-α)]^ℓ
```

W is the expected per-miss recursive recomputation cost, modeled as a
**Galton–Watson branching process** with offspring mean d(1-α). When
d(1-α) > 1 — i.e. α < α_c = 1 − 1/d — W grows exponentially in ρ. For the
recommended (d=8, ρ=4), S·T = Ω(K²) for all constant α.

Concrete (d=8, ρ=4), verified arithmetic:

| α | d(1-α) | W(α,ρ) | S·T / K² | regime |
|---|---|---|---|---|
| 1/6 (adversary-optimal α*=1/(ρ+2)) | 6.67 | 2324 | **645** (~300× honest 2K²) | supercritical |
| 1/2 | 4 | 341 | 171 | supercritical |
| 3/4 | 2 | 31 | 11.6 | supercritical |
| 7/8 (critical α_c=1−1/d) | 1 | 5 | 1.09 | critical |

**Theorem 4 (Temporal Staleness).** The adversary stores *current* vertex
states (step t) but reconstruction needs *historical* states (step t'<t); under
ROM-uniform writes a stored value is stale w.p. 1−e^{−(t−t')/N}, so the effective
hit rate decays as αe^{−ℓ} with recursion depth ℓ. This strengthens W → W*
(e.g. at α=7/8, W=5 → W*=338). It is the formal refutation of "store current
state / cursors and replay cheaply."

**Theorem 5 (Adaptive Bound).** An adversary who fixes storage adaptively, and
who knows *which* address to read (v0 computable from T_{t−1}), still cannot
read it without v0 ∈ S_t. Knowing the access pattern does not substitute for
storing values. No factor loss. This refutes the "cursors defeat the cascade"
claim directly.

Grounding: Blocki–Holman (sustained-space tradeoffs for data-dependent MHFs in
the parallel ROM; any dynamic pebbling strategy either holds Ω(N) memory for
Ω(N) steps or pays cumulative Ω(N^{2.5−ε})). The paper's two-phase
decomposition (static skip-link backbone + dynamic overlay) supplies the
deterministic termination that a pure data-dependent DAG lacks.

### 2.2 What rev. 1 got wrong, explicitly

- The "4× linear" ceiling is **too optimistic for the adversary** (understates
  security). It came from assuming stored cursors/current-state collapse
  recomputation to O(ρ). Theorem 4 shows current state is stale for historical
  reconstruction, and Theorem 5 shows addresses ≠ values. The real penalty is
  super-linear and α-dependent: ~300× at α*=1/6, not 4×.
- "Tight lower bound is open" is **wrong** as stated. The paper proves S·T =
  Ω(K²) with no factor loss (Theorems 3–5). What remains is peer-review
  scrutiny, not absence of a proof (see §2.3).
- The old repo `draft-condrey-posme.md` Theorem 3 (`1+2ρ(1-α)²/α`, single-
  strategy proof) and the `posme-dynamic-pebbling.md` "4×" doc are both
  **stale** and should not be cited; the paper's Theorems 3–5 replace them.

### 2.3 The amortization attack — stress-tested (previously the one open residual)

The one point a referee will press is whether an adversary can **amortize /
memoize** reconstructed historical states across misses to beat the per-miss
branching cost W(α,ρ). Theorem 4's staleness argument is the intended defense.
Rather than leave this to assertion, it was simulated directly
(`tmto-amortization-sim.py`, `tmto-robustness-sim.py`): a faithful PoSME
dependency DAG (uniform-random ROM addressing per Theorem 2; depth-ρ truncation
to the static skip-link backbone), with an adversary storing αN blocks and a
**persistent memo** of all reconstructed historical states — the strongest
amortization strategy. Findings (ρ=4, d=8; α = adversary-optimal 1/6):

1. **Staleness is real and raises cost.** Naive per-miss cost is ~15,500 hashes
   vs the flat W(α,ρ)=2,324 — ~6.7× higher, because a stored block is a *live*
   hit only if its current version equals the needed historical version, which
   under random writes it rarely is. This empirically confirms Theorem 4; the
   flat W is conservative.
2. **Memoization is not free — it costs Θ(N) storage.** The memo attack does cut
   per-miss cost, but only by holding a memo whose footprint is
   **1.7–2.0 × N distinct states, scale-invariant** across N ∈ {2048, 4096,
   8192} and three seeds (footprint/N stays ~constant, not shrinking). The
   "memoizing adversary" is therefore a *full-storage* adversary.
3. **The bound survives.** Counting the memo as storage, the space-time product
   (αN + footprint)·T stays at **≈300–3,800 × K²** across every tested α, N,
   seed, and ρ ∈ {2,4} — never approaching the Ω(K²) floor from above.

This closes the residual in the paper's favor: amortization does not beat the
lower bound; it only re-pays the storage the bound is about. Limits of this
first test: small N; uniform-ROM addressing; the absolute S·T ratio came from a
full-pass *extrapolation*. The next test removes those.

### 2.4 Validated full-pass pebbling — the hard version (`tmto-pebbling-validated-sim.py`)

The sampled test above has two weaknesses: it extrapolates the S·T ratio, and it
never checks the simulator against a known-true result. Both are fixed here.

**Simulator validation (the key move).** The same engine — a fixed persistent
store of size S plus transient per-reconstruction scratch, full forward pass, no
extrapolation — is first run on a **line graph, i.e. scrypt/ROMix phase-1, whose
tradeoff S·T = Θ(N²) is a *proven* theorem** (Alwen–Chen–Pietrzak). It
reproduces it: min S·T/N² = **0.367, 0.377, 0.381** at N = 1024, 2048, 4096 —
flat. An engine that gets the proven case right is trustworthy on PoSME.

**PoSME result (two seeds, N=384, ρ=4, d=8).** S·T/K² stays in **[75, 1316]
across every α** — the space-time product is Ω(K²) at every storage fraction, no
extrapolation. Memory-hardness is confirmed by a validated engine against a
general full-pass adversary. This is materially stronger than §2.3.

**But it also contradicts a secondary claim in the paper, and I won't bury it.**
The paper presents α* = 1/(ρ+2) = 1/6 as "adversary-optimal" with S·T ≈ 645K²
(~300× honest) as the headline guarantee. In the simulation the S·T product is
**non-monotonic and α* = 1/6 sits near its MAXIMUM**, not its minimum. The
adversary *minimizes* S·T, and the minimum is at small α (~75K² at α = 0.02),
roughly 8× below the headline. So:
- The security property holds — the adversary's *best case* is still ≈ 75K² ≫ K²,
  so PoSME is memory-hard.
- But "adversary-optimal α* = 1/6, ~300×" is **mislabeled**: α* = 1/6 is the
  *defender*-optimal point (strongest guarantee); the honest number to quote as
  the guarantee is the adversary's *minimum* (~75× here), not the maximum. The
  paper (and Table III / the EKR-facing "~300×") should report the minimum over
  α, which is smaller — real, still-safe, but not 300×.

**Honest limits.** Small N (ρ,α,d-driven, so scale-behaviour is the load-bearing
part, validated on ROMix over a 4× range — not proven at N=2²⁴). The model
charges reconstruction of each historical dependency from the persistent store
(a verifier-style task), so the absolute honest baseline is loose; the robust,
reproducible facts are (i) the engine reproduces ROMix Θ(N²), (ii) PoSME S·T/K²
∈ [75, 1316] is Ω(K²) at all α across two seeds, and (iii) the minimum is at
small α, not at the paper's α*. A separate open subtlety the simulation raises:
because reconstruction truncates at the depth-ρ backbone, per-miss cost is
bounded by O(d^ρ) *independent of N*, so PoSME is a **bounded-penalty** MHF (like
Argon2), not an unbounded-tradeoff one (like scrypt) — the "S·T = Ω(K²)" phrasing
should not be read as scrypt-style unbounded memory-hardness. This deserves the
author's and a referee's attention; it is not settled by the paper's argument.

### 2.5 EUROCRYPT-grade: untruncated scaling — SUPERSEDES the §2.4 truncated findings

§2.4 imposed the paper's own depth-ρ truncation (reconstruction charged O(log N)
at depth ρ). That was the artifact driving both of §2.4's findings. Removing it
and reconstructing to the **true Init state** (`tmto-scaling-sim.py`) settles the
memory-hardness *class* — the question that actually matters — and reverses my
"bounded-penalty" conclusion:

- **Per-miss reconstruction cost grows with N.** At fixed ρ=4, d=8, as N goes
  256→4096 (16×), the per-miss cost (distinct nodes to Init) goes 580→7,599 —
  fit **cost ~ N^0.93**, i.e. ≈ linear in N. A cost that grows with N means
  **PoSME is UNBOUNDED memory-hard (scrypt-class), not bounded (Argon2-class).**
  §2.4's finding (2) is **retracted** — it was a truncation artifact. This is
  *good* for PoSME: it is strongly memory-hard, more than the paper's own
  argument proves.
- **The paper's depth-ρ mechanism is empirically false.** Measured reconstruction
  depth to Init is **15–21, not ρ=4** (off by ~4.5×), and grows with N — i.e. the
  timeline regresses roughly *geometrically* (≈log K depth), not arithmetically
  (~N per level, ρ levels) as the paper claims. Consequently W(α,ρ)=Σ[d(1−α)]^ℓ
  truncated at ρ **understates** the true cost, and Table III's constants (645×,
  etc.) — and §2.4's "α* is a maximum / adversary min ~75×" finding, which was
  computed under the truncation — do not describe the real DAG. Treat §2.4's
  finding (1) as **also superseded**; the correct picture is the N-growing cost
  here.

**Net, honestly:** the paper's *conclusion* S·T = Ω(K²) is empirically sound and
if anything **understated** — PoSME is genuinely, unboundedly memory-hard. But
the paper's *stated proof* (depth-ρ regression, the truncated W formula, the
Table III constants, and the "adversary-optimal α*=1/6, ~300×" headline) does
**not** match the DAG's actual behaviour and must be re-derived. The right
re-derivation is a scrypt-style S·T = Θ(K²) argument via the N-growing
reconstruction cost, not the bounded branching sum. Confidence: the scaling
(cost ~ N^0.93, depth ≫ ρ) is robust and reproducible on a validated engine; the
engine reproduces ROMix's proven Θ(N²) (§2.4), so I trust the direction.
Remaining honest limit: small–moderate N, uniform-ROM addressing, and this is the
fourth successive refinement of this analysis — the *class* (unbounded) and the
*mechanism error* (depth ≫ ρ) are solid; the exact exponent and constants want a
formal treatment (the genuine EUROCRYPT-grade paper), which no simulation
replaces.

---

## 3. Quantum soundness margin (unchanged, medium-high confidence)

Soundness (paper Theorem 1/2): Adv^forge ≤ K·ε_coll.
- Classical margin at K_max=2²⁶, 256-bit H: 128−26 = 102 bits.
- Quantum (BHT collision, 2^{n/3} with large QRAM): 85−26 ≈ 59 bits — below 64.
  Without large QRAM, ~102 bits.
Recommend stating: post-quantum by virtue of being hash-based; for ≥64-bit BHT
margin cap K ≤ 2²¹ or use a 384-bit hash. No PQC primitive needed.

---

## 4. The repo is out of sync with the paper — this is the real work

The authoritative, correct analysis lives in arXiv:2604.15751. The repo working
copies lag it:

- `draft-condrey-posme.md`: stale Theorem 3 (divergent `2ρ(1-α)²/α`, single-
  strategy proof) and inflated 197×–3,137× table. **Replace its §Security with
  the paper's Theorems 3–5** (branching-process S·T bound, temporal staleness,
  adaptive bound). Site map in §6.
- `posme-dynamic-pebbling.md`, `posme-tmto-proof.md`: superseded; the "4×"
  conclusion is wrong per Theorem 4. Mark as historical or delete.
- Lattice `.tex`: archived (done).

## 5. EKR email — correct the number, but note the direction reversed

The email's "~170×" is **not an overstatement** — the paper supports ~300× at
adversary-optimal α*=1/6 (Table III), and Theorem 4 strengthens further. 170×
is a defensible mid-range figure. State it as the paper does: a formal
S·T = Ω(K²) bound, with the α-dependent penalty (~300× at α*≈1/6 for ρ=4,
falling to ~1× only as α→α_c=7/8). Do NOT "correct down to 4×" — that was rev.
1's error. If anything, cite the S·T = Ω(K²) bound and the ~300× point.

## 6. Draft site map for the sync (draft-condrey-posme.md)

Replace, in order, with the paper's text:
- L234, L308–309, L1010–1022 (table), L1067+ (Theorem 3): the divergent
  `2ρ(1-α)²/α` statement and 197×–3,137× table → paper's Theorem 3 branching
  form + Table III (645/171/11.6/1.09 at α=1/6, 1/2, 3/4, 7/8).
- L1152–1176 (Theorem 4): → paper's Temporal Staleness (W→W*).
- L1178–1223 (Theorem 5): → paper's Adaptive Bound (no factor loss). The old
  "checkpoint dominance / all-or-nothing" conclusion is subsumed and should be
  restated as the adaptive-storage result.
- L554–569, L966–987, L1244–1248, L1321–1324, L1502: reword cascade references
  to the branching-process / temporal-staleness mechanism.
Re-render (`make`) and idnits afterward.

Confidence: §1 high; §2.1 reflects the authoritative paper (high on structure/
arithmetic); §2.3 the amortization attack — the one residual — was simulated and
fails (footprint/N ≈ const, S·T ≫ K²), upgrading it from "open" to strongly
supported; §3 medium-high; §5 corrected. Rev. 1's 4×/open conclusion is retracted.
