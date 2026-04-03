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
