<!-- repo-header:start -->
<h3 align="center">Proof of Sequential Memory Execution (PoSME)</h3>

<p align="center"><strong>Internet-Draft: Proof of Sequential Memory Execution (PoSME) - draft-condrey-cfrg-posme</strong></p>

<p align="center">
  <a href="https://github.com/dcondrey/posme-draft/actions/workflows/publish.yml"><img src="https://img.shields.io/github/actions/workflow/status/dcondrey/posme-draft/publish.yml?style=flat-square&labelColor=20232a&branch=main&label=CI" alt="CI"></a>
  <a href=".bestpractices.json"><img src="https://img.shields.io/badge/best%20practices-evidence%20reviewed-6a4c93?style=flat-square&labelColor=20232a" alt="Best Practices Evidence"></a>
  <a href="https://datatracker.ietf.org/"><img src="https://img.shields.io/badge/standard-IETF%20draft-6a4c93?style=flat-square&labelColor=20232a" alt="IETF"></a>
  <a href="https://github.com/sponsors/dcondrey"><img src="https://img.shields.io/badge/GitHub%20Sponsors-Sponsor-EA4AAA?style=flat-square&labelColor=20232a" alt="GitHub Sponsors"></a>
</p>
<!-- repo-header:end -->

---

This is the working area for the individual Internet-Draft *Proof of Sequential Memory
Execution (PoSME)*.

PoSME is a memory-hard primitive that combines a mutable arena, data-dependent pointer-chase
addressing and per-block causal hash binding in one step function. A prover runs K sequential
steps over an N-block arena; each step reads d blocks at addresses determined by the previous
read, writes one block entangled with its spatial neighbours, and advances a transcript chain.
That buys sequential-time enforcement anchored in physical latency floors, forgery prevention
that reduces to collision resistance of H, and time-memory trade-off resistance scaling as
1/alpha in the adversary's storage fraction. Verification costs O(Q * d^R * log N) hash
evaluations, allocates no arena, and needs no trusted setup.

* [Editor's Copy](https://dcondrey.github.io/posme-draft/#go.draft-condrey-posme.html)
* [Datatracker Page](https://datatracker.ietf.org/doc/draft-condrey-posme)

## Contributing

See the [guidelines for contributions](CONTRIBUTING.md).

Contributions can be made by creating pull requests. The GitHub interface supports creating pull requests using the Edit button.

## Command Line Usage

Formatted text and calculation results can be produced using `make`.

```sh
$ make
```

Command line usage requires that you have the necessary software installed. See [the instructions](https://github.com/martinthomson/i-d-template/blob/main/doc/SETUP.md).
