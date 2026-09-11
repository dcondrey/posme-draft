# A cumulative-memory-complexity lower bound for PoSME — proof draft

**Status.** This is a rigorous *draft* reduction, not a certified theorem. Every
load-bearing step is made explicit, and the two steps that carry real risk
(Lemma 1's embedding faithfulness, Lemma 2's non-amortization in the parallel
ROM) are flagged as such in §6. It is intended as a starting point a
cryptographer can check and complete, and it should not be cited as settled. The
author of this memo has revised the PoSME memory-hardness analysis four times in
one sitting; that is itself a reason to treat a first-pass proof with suspicion
until refereed.

It does **not** establish a correction to the paper's Ω(K²): see §2 — a metric
mismatch (cc_mem vs S·T) and a log N factor mean the informal "factor-ρ
over-claim" does not hold at the recommended ρ = 4. The exact bound and whether
the paper over- or under-claims are **unresolved**. What is robust is empirical
(§ SECURITY-REVIEW.md 2.5): reconstruction cost grows ~N^0.93 and depth is
~15–21 not ρ, so the memory-hardness is genuine and unbounded in N — but the
constant/exponent is not pinned down here.

---

## 1. Model and definitions

We work in the **parallel random oracle model (pROM)** of Alwen–Serbinenko
(STOC 2015): an algorithm proceeds in rounds; in each round it may make an
unbounded batch of random-oracle queries to H (w-bit outputs) in parallel, and
carries a state between rounds. The **cumulative memory complexity** of an
execution is `cc_mem = Σ_i |state_i|` (sum over rounds of the state size in
bits); `cc_mem(f) = min` over algorithms computing f of the expected cumulative
memory. cc_mem is the amortization-resistant cost measure: it lower-bounds
space·time and is robust to computing many instances in parallel (Alwen–Blocki
2016).

**The result we reduce to (ACP17).** Alwen, Chen, Pietrzak, Reyzin, Tessaro
(EUROCRYPT 2017) prove that scrypt's core, ROMix on n iterations with w-bit
labels, has `cc_mem = Ω(w·n²)` in the pROM, and this is maximal for a function
making n sequential queries. The hardness comes from ROMix phase 2: n reads at
**data-dependent, H-determined addresses** into an array of n high-entropy
labels, where the j-th address is a function of the (j−1)-th read value, so an
algorithm cannot know a read target until the previous read completes.

**PoSME as a function.** Fix parameters (N, K, d), ρ = K/N ≥ 1 integer, w-bit
hash. PoSME computes a transcript T_K by K sequential steps over an N-cell arena.
Step t (i) derives d addresses a_{t,1..d} from the cursor c_t = H(c_{t−1}‖…) via
H (Theorem 2: the a_{t,j} are, in the ROM, pairwise independent and within N/2⁶⁴
of uniform on [0,N)); (ii) reads those cells; (iii) writes one cell w_t with a
value and causal hash depending on the d reads; (iv) folds the arena root into
T_t = H(T_{t−1}‖t‖c_t‖root_t). The output T_K binds all K roots.

**Claim.** `cc_mem(PoSME) = Θ(w·ρ·N²) = Θ(K²/ρ)` in the pROM.

---

## 2. Upper bound: cc_mem = O(w·ρ·N²)

The honest algorithm keeps the N-cell arena (w bits each, so wN state) resident
and advances one step per round for K rounds, updating the Merkle root
incrementally in O(log N) work. Its state never exceeds wN + O(w log N) bits, for
K rounds, so `cc_mem ≤ (wN + O(w log N))·K = O(wNK) = O(w·ρ·N²)`. ∎

**Caution — this does NOT cleanly refute the paper's S·T = Ω(K²), and I will not
claim it does.** Two factors I initially glossed and then caught: (i) *metric* —
the bound above is on cc_mem, but the paper's claim is on S·T, and cc_mem ≤ S·T,
so a cc_mem upper bound does not bound S·T from above; (ii) *log factor* — the
honest algorithm's S·T is O(wN · K log N) = O(wρN² log N) once Merkle-update time
is counted, so honest S·T *exceeds* Ω(K²) whenever ρ < log N — which includes the
recommended ρ = 4 (log N ≈ 24). So at the recommended parameters there is **no
contradiction** with Ω(K²); the "factor-ρ over-claim" only appears asymptotically
(ρ ≫ log N) and under the cc_mem metric, not S·T. Whether the paper over- or
under-claims at real parameters is **unresolved here**. This is the fifth
subtle w / log N / cc_mem-vs-S·T / ρ factor to flip a conclusion in this analysis;
treat every constant below accordingly.

---

## 3. Epoch decomposition

Partition the K steps into ρ **epochs** E_1,…,E_ρ of N consecutive steps each.
Within an epoch, N steps perform N data-dependent reads into the (mutating)
N-cell arena. We treat one epoch as an instance of a *mutable* ROMix over an
N-cell array.

**Lemma 1 (per-epoch hardness).** In the pROM, computing the arena state and
transcript across a single epoch E_i, given the arena state at the epoch's start,
has cc_mem = Ω(w·N²).

*Proof idea.* An epoch performs N reads whose addresses are H-outputs of the
evolving cursor (Theorem 2), hence data-dependent and, until the previous read
resolves, unknown to the algorithm. This is exactly the access structure ACP17
prove maximally hard for ROMix on n = N iterations over N w-bit labels: the label
array has ≥ N·w bits of entropy (each cell is an H-output), reads are
data-dependent, and the round-i target is unpredictable before round i−1
completes. The ACP17 lower bound applies to any pROM algorithm and yields
cc_mem ≥ Ω(w·N²) for the epoch. (Faithfulness of this embedding — that PoSME's
mutable arena and causal-hash writes do not give the algorithm a shortcut absent
from static ROMix — is the load-bearing assumption; see §6(a).) ∎

---

## 4. Non-amortization across epochs

**Lemma 2 (sequential, non-amortizable epochs).** The ρ epochs cannot be
overlapped or shared: cc_mem(PoSME) ≥ Σ_{i=1}^{ρ} cc_mem(E_i) − o(w·ρ·N²).

*Proof idea.* Two mechanisms prevent amortization. (i) **Sequentiality:** cursor
c_t = H(c_{t−1}‖·) is a hash chain, so epoch E_{i+1}'s first address depends on
E_i's last cursor, which depends on E_i's reads; no round of E_{i+1} can be
scheduled before the corresponding round of E_i, so the epochs occupy disjoint
round-intervals and their cumulative-memory contributions add. (ii)
**State-freshness:** E_{i+1} reads the arena as mutated by E_i; by Theorem 2 the
addresses are fresh H-outputs independent of E_i's, so the memory an optimal
algorithm holds for E_{i+1} is not reusable work from E_i (the labels it needs
are new). Hence the per-epoch Ω(wN²) contributions do not collapse under a shared
strategy, and `cc_mem ≥ ρ·Ω(wN²) = Ω(w·ρ·N²)`. (The pROM amortization argument —
that a *parallel* adversary cannot pay once and reuse across epochs — is the
delicate step ACP17 needed heavy machinery for; see §6(b).) ∎

---

## 5. Main theorem

**Conjectured Theorem (NOT proven here).** In the parallel random oracle model,
`cc_mem(PoSME(N,K,d)) = Θ(w·ρ·N²) = Θ(K²/ρ)`, where ρ = K/N.

*Status of the argument.* Upper bound (§2): rigorous for cc_mem. Lower bound:
Lemma 1 (per-epoch, Ω(wN²)) and Lemma 2 (sum over ρ epochs) are **asserted by
reduction/analogy to ACP17, not derived** — §6(a),(b). So the lower bound is a
conjecture with a plausible route, not a theorem.

**On the space–time form.** cc_mem ≤ S·T, so a cc_mem *lower* bound would give an
S·T lower bound — but the lower bound is unproven, and (§2) the honest S·T carries
a log N factor that makes any "factor-ρ below Ω(K²)" statement fail at the
recommended ρ = 4. **Do not read this as a proven correction to the paper.** The
one robust, metric-independent fact is empirical: reconstruction cost grows with
N (~N^0.93, `tmto-scaling-sim.py`), so the memory-hardness is genuine and
unbounded in N — the *class* is settled even though the *constant/exponent* is
not.

---

## 6. Where this needs a referee (do not skip)

This draft is only as strong as two steps, both of which are exactly the parts
that make data-dependent MHF lower bounds hard (and that ACP17's 40 pages exist
to handle):

**(a) Lemma 1 embedding faithfulness.** I assert PoSME's mutable arena +
causal-hash writes instantiate ROMix hardness. A referee must verify no shortcut:
e.g. that writes do not let an algorithm reconstruct labels more cheaply than the
static-array ROMix bound assumes, and that the causal hashes (which *add*
dependencies) can only increase, not decrease, cc_mem. This is plausible but not
proven here; a clean reduction would exhibit an explicit ROMix-instance simulator
inside PoSME.

**(b) Lemma 2 parallel-ROM amortization.** The claim that ρ epochs' costs *add*
under an optimal *parallel* adversary is the hard part. Sequentiality (cursor
chain) gives disjoint round-intervals, but a parallel adversary could in
principle pre-invest memory usable across epochs. ACP17-style single-instance→
amortized lifting is what rules this out for scrypt; I have asserted the analogue,
not derived it. This is the most likely place for the bound to be wrong or to lose
a log factor (cf. the earlier Ω(w n²/log²n) restricted-adversary bound before the
full ACP17 result).

**(c) Addressing idealization.** Theorem 2's "addresses are uniform+independent"
is used throughout; the real pointer-chase is only statistically close, and
ACP17's structure-specific arguments may need re-checking against the exact
distribution.

**Honest bottom line.** I can produce this reduction and I believe its *shape*
(reduce per-epoch to ACP17, sum ρ non-amortizable epochs, land at Θ(K²/ρ)) is
right and is the correct fix for the paper's over-claimed Ω(K²). I cannot certify
(a) and (b); those are genuine research steps, and my repeated revisions this
session are evidence that first-pass confidence here is not warranted. Treat this
as the scaffold for the real proof, to be checked and completed by a cryptographer
(and this is the natural place for EKR / a CFRG reviewer to engage).
