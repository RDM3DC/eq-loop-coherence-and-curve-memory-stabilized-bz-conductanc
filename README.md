# Loop-Coherence and Curve-Memory Stabilized BZ Conductance Law

<!-- HERO_ANIMATION:BEGIN -->
![Loop-coherence + curve-memory stabilised BZ conductance](images/loop_memory_conductance_3d.gif)

_Hero animation: **Loop-coherence + curve-memory stabilised BZ conductance**. [Download high-resolution MP4](images/loop_memory_conductance_3d.mp4)._
<!-- HERO_ANIMATION:END -->

**ID:** `eq-loop-coherence-and-curve-memory-stabilized-bz-conductanc`  
**Tier:** derived  
**Score:** 100  
**Units:** OK  
**Theory:** PASS-WITH-ASSUMPTIONS  

## Equation

$$
\frac{d\tilde G_{ij}}{dt}=\alpha_G(S)\frac{1+\kappa_\Psi\Psi}{1+\xi M_{ij}}|I_{ij}|e^{i\theta_{R,ij}}-\mu_G(S)\tilde G_{ij}
$$

## Description

Lineage-preserving extension of the BZ-averaged phase-lifted complex conductance update. The new factor couples a loop-coherence gain `Psi` to a chronic-slip curve-memory attenuator `M_ij`, so edges are reinforced most strongly when they are active, holonomy-consistent, and not already carrying accumulated topological stress.

The law recovers the parent BZ equation exactly when `kappa_Psi = 0` and `xi = 0`, reduces to pure loop-coherence gating when `xi = 0`, and reduces to pure curve-memory stabilization when `kappa_Psi = 0`.

## What This Repository Now Contains

- Closed-form solutions for the time-dependent and frozen-coefficient cases.
- Consistency proofs for the parent-law limits and the monotonic role of `Psi` and `M_ij`.
- A pure-Python reference simulator with committed CSV, JSON, and SVG outputs.
- A benchmark-driven scenario suite built from a vendored flat-channel loop-signature trace.
- A parameter sweep over `(kappa_Psi, xi)` with committed CSV, JSON, and heatmap artifacts.
- A stylized multi-plaquette lattice model for testing edge-local memory against shared loop coherence.
- A small unittest suite covering the core algebra and the reference model.

## Assumptions

- `Psi = (1 / N_p) sum_p cos(Theta_p / pi_a)` is dimensionless and bounded in `[-1, 1]` on the monitored plaquette family.
- `M_ij(t)` is a nonnegative curve-memory stress integral or exponential moving average built from resolved-phase slip energy.
- `xi >= 0` and the operating regime satisfies `1 + kappa_Psi Psi >= 0`; a sufficient global condition is `0 <= kappa_Psi <= 1`.
- `alpha_G(S) >= 0` and `mu_G(S) > 0` retain the units and entropy gating of the parent BZ law.

## Quick Start

Run the committed reference simulation:

```bash
python simulations/run_reference_simulation.py
```

Run the benchmark import, scenario suite, sweep, and lattice artifacts:

```bash
python simulations/run_benchmark_suite.py
```

Run the tests:

```bash
python -m unittest discover -s tests
```

## Key Documents

- [derivations/analytic-solution.md](derivations/analytic-solution.md) - integrating-factor solution, frozen-coefficient solution, and exact limit recoveries.
- [derivations/consistency-and-stability.md](derivations/consistency-and-stability.md) - proof notes for monotonicity, boundedness, and phase alignment.
- [notes/validation-plan.md](notes/validation-plan.md) - falsifiable predictions and the staged validation program.
- [simulations/run_reference_simulation.py](simulations/run_reference_simulation.py) - reproducible CLI that generates the committed artifacts.
- [simulations/run_benchmark_suite.py](simulations/run_benchmark_suite.py) - vendors the benchmark forcing trace when available and regenerates the benchmark, sweep, and lattice artifacts.
- [data/reference_summary.json](data/reference_summary.json) - scenario-level metrics for the reference run.
- [data/benchmark_forcing.csv](data/benchmark_forcing.csv) - vendored forcing bundle derived from the flat-channel loop-signature benchmark trace.
- [data/benchmark_scenarios.json](data/benchmark_scenarios.json) - baseline, loop-only, memory-only, and full-law benchmark comparisons.
- [data/benchmark_sweep_summary.json](data/benchmark_sweep_summary.json) - top-scoring `(kappa_Psi, xi)` combinations under the imported benchmark.
- [data/lattice_network_summary.json](data/lattice_network_summary.json) - multi-plaquette lattice comparison between the parent and stabilized laws.
- [images/reference_trace.svg](images/reference_trace.svg) - visualization of the baseline vs stabilized trajectories.
- [images/benchmark_sweep_heatmap.svg](images/benchmark_sweep_heatmap.svg) - heatmap of benchmark sweep scores.
- [images/lattice_network.svg](images/lattice_network.svg) - multi-plaquette lattice response plot.

## Current Readout

The imported benchmark and the synthetic reference do not prefer the same operating point. The synthetic single-plaquette reference still rewards stronger curve-memory stabilization, while the imported flat-channel trace currently favors high loop gain and weaker memory damping. The multi-plaquette lattice model lands in between: under the same imported benchmark trace, the combined loop-plus-memory law improves both the damage-window and recovery-window mean magnitude relative to the parent law.

## Repository Structure

```text
images/       visualizations and plots
derivations/  derivations and proof notes
simulations/  reference model and artifact generator
data/         committed outputs from the reference run
notes/        validation notes and research framing
tests/        regression tests for the law and simulator
```

## Links

- [TopEquations Leaderboard](https://rdm3dc.github.io/TopEquations/leaderboard.html)
- [TopEquations Main Repo](https://github.com/RDM3DC/TopEquations)
- [Certificates](https://rdm3dc.github.io/TopEquations/certificates.html)

---
*Part of the [TopEquations](https://github.com/RDM3DC/TopEquations) project.*
