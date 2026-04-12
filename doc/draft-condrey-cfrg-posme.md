---
v: 3
docname: draft-condrey-cfrg-posme-latest
title: "Proof of Sequential Memory Execution (PoSME)"
abbrev: PoSME
category: info
ipr: trust200902
submissiontype: IRTF
area: Security
workgroup: Crypto Forum Research Group
keyword:
  - memory-hard
  - sequential execution
  - causal hash
  - latency-bound
  - ASIC resistance

stand_alone: yes
pi:
  toc: yes
  tocdepth: "4"
  sortrefs: yes
  symrefs: yes

author:
  - fullname: David Condrey
    initials: D.
    surname: Condrey
    organization: WritersLogic Inc
    abbrev: WritersLogic
    city: San Diego
    region: California
    country: United States
    email: david@writerslogic.com

normative:
  RFC8610:
  RFC8949:
  RFC9106:

informative:
  RFC6962:
---

--- abstract

This document defines Proof of Sequential Memory Execution (PoSME),
a cryptographic primitive combining mutable arena state, data-
dependent pointer-chase addressing, per-block causal hash binding,
and execution entropy entanglement in a single step function. A
Prover executes K sequential steps over a mutable N-block arena.
Each step reads d blocks at addresses determined by the previous
read's result (pointer chasing), writes one block with symbiotic
binding (new data depends on old causal hash; new causal hash
depends on cursor), and advances a transcript chain. At regular
intervals, CPU jitter entropy is folded into the transcript,
binding the proof to physical execution on a general-purpose
system. The construction provides four properties: (1)
unconditional sequential time enforcement (Omega(K) computation
regardless of storage), (2) forgery prevention via causal hashes
(reduces to collision resistance of H), (3) TMTO resistance
scaling linearly with write density rho = K/N (34x penalty at
rho=16 for a zero-storage adversary), and (4) execution-
environment ASIC resistance (the adversary must execute on a
general-purpose CPU with an operating system to produce valid
entropy, limiting the advantage to commodity hardware variation).
A compact parameter profile achieves these properties with
approximately 32 MiB peak RAM. Verification requires O(Q * d^R *
log N) hash evaluations with no arena allocation. No trusted setup
is required.

--- middle

# Introduction {#introduction}

Existing primitives for proving sequential computation have
complementary weaknesses. Verifiable Delay Functions (VDFs)
{{Boneh2018}} {{Wesolowski2019}} prove sequential time but offer no memory-hardness.
Proofs of Sequential Work (PoSW) {{CohenPietrzak2018}} prove
traversal of a depth-robust graph but operate over static memory.
Memory-hard functions (MHFs) such as Argon2id {{RFC9106}} resist
ASIC acceleration but are single-evaluation primitives with no
chain proof system. Composing these (e.g., chaining Argon2id with
Merkle sampling) produces a construction where sequentiality and
memory-hardness are independent properties; neither reinforces the
other.

PoSME takes a different approach. A persistent mutable arena IS
the computation state. Each step reads via data-dependent pointer
chasing (sequential because each address depends on the previous
read's result) and modifies the arena in-place. A per-block
causal hash chain binds each block's value to the cursor of the
step that wrote it, preventing forgery (the adversary cannot
produce a valid causal hash without knowing the writer's cursor,
which depends on d other blocks' causal hashes, recursively).
The data and causal hash are symbiotically bound: new data
depends on the old causal hash, and the new causal hash depends
on the cursor.

The primary contribution is latency-bound ASIC resistance. Each
pointer-chase iteration is bottlenecked by random DRAM access
(~45ns on DDR5 {{JESD79-5}}), with hash computation (~3ns via
BLAKE3) as a minor component. The ASIC advantage is bounded by
the memory latency ratio (approximately 2x for DDR5 vs HBM3),
tighter than the 8-16x bandwidth bounds of Argon2id
{{Biryukov2016}}. Memory latency improves more slowly than
bandwidth across technology generations (constrained by signal
propagation and DRAM cell sensing time), making this bound more
durable than bandwidth-based resistance.

## Related Work {#related-work}

### Proofs of Sequential Work

PoSW {{CohenPietrzak2018}} proves traversal of a depth-robust
graph via Fiat-Shamir-sampled Merkle proofs. PoSME differs: the
graph is a mutable arena (not a static DAG), the access pattern
is data-dependent (not fixed), and each node carries a causal hash
binding its value to its full write history.

### Memory-Hard Functions

Argon2id {{RFC9106}} resists TMTO via bandwidth-hardness
{{Boneh2016}}, with a single-pass TMTO penalty of approximately 2x. PoSME uses Argon2id
only for arena initialization. The ongoing computation uses
pointer-chasing with in-place writes, creating latency-hardness
(2x ASIC bound vs Argon2id's 8-16x). PoSME's TMTO penalty is
approximately 2+2\*rho for zero-storage adversaries, where
rho = K/N is the write density (10x at rho=4 vs Argon2id's 2x).

### Proofs of Space-Time

Proofs of Space-Time (PoST) {{Chia2024}} {{Spacemesh2023}} enforce both
sequential time and persistent storage by requiring a Prover to
repeatedly prove possession of stored data over a sequence of
time intervals. PoST operates over a static graph: the stored
data does not change between proofs, and the graph structure is
fixed before execution. PoSME differs in that the arena is
mutable (each step modifies it), the access pattern is data-
dependent (addresses are determined by arena contents, not
pre-computed), and each block carries a causal hash binding its
current value to its write history. These differences make PoSME
a different construction with different TMTO characteristics,
not a strict improvement over PoST.

# Conventions and Definitions {#conventions}

{::boilerplate bcp14-tagged}

H:
: BLAKE3 in XOF mode, producing 32-byte output.

XOF(input, index):
: BLAKE3 XOF evaluated at (input \|\| I2OSP(index, 4)),
  producing 4 bytes.

I2OSP(x, len):
: Integer-to-Octet-String Primitive per {{!RFC8017}}.

MerkleRoot(A):
: Merkle tree root over arena blocks using domain-separated
  hashing per {{RFC6962}}.

MerkleUpdate(root, index, new\_value):
: Incremental Merkle root update at the given index.

Prover:
: The entity executing the PoSME computation and generating proofs.

Verifier:
: The entity checking PoSME proofs.

Arena:
: A mutable array of N blocks, each containing a 32-byte data
  field and a 32-byte causal hash.

Causal hash:
: A per-block running hash chain binding each block's value to
  the cursor of the step that wrote it.
