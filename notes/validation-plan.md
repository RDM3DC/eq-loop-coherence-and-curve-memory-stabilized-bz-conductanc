# Validation Plan

## Objective

Turn the equation into a falsifiable research object rather than a descriptive formula. The minimum bar is to show that the loop-coherence gain and curve-memory stabilizer produce distinct, measurable behavior relative to the parent BZ law.

## Core Predictions

1. In high-coherence windows with low accumulated memory, the stabilized law should produce a larger effective source amplitude than the parent law.
2. During repeated slip bursts, the `1 / (1 + xi M_ij)` factor should reduce conductance overshoot on the stressed edges.
3. After the slip burst ends and `M_ij` decays, the stabilized law should recover toward the same resolved-phase direction as the parent law.
4. Setting `kappa_Psi = 0` and `xi = 0` in the simulation code should reproduce the parent-law traces exactly.
5. For frozen inputs, the simulated late-time conductance should converge to the closed-form steady state in [derivations/analytic-solution.md](../derivations/analytic-solution.md).

## Numerical Program

### Phase 1: Single-Plaquette Reference Case

- Use the reference script in [simulations/run_reference_simulation.py](../simulations/run_reference_simulation.py).
- Drive one plaquette through a localized slip burst.
- Record `Psi(t)`, mean memory, and mean conductance magnitude for both the parent and stabilized laws.

This phase is already implemented and is intended to catch algebraic mistakes early.

### Phase 2: Parameter Sweeps

- Sweep `kappa_Psi` over `[0, 1]`.
- Sweep `xi` over a practical damping range.
- For each pair, measure damage-window mean magnitude, recovery-window mean magnitude, and late-time variance.

The goal is to map where the law is amplifying useful coherent transport versus over-damping recovery.

This phase is now implemented in [simulations/run_benchmark_suite.py](../simulations/run_benchmark_suite.py) and the current committed outputs are [data/benchmark_sweep.csv](../data/benchmark_sweep.csv), [data/benchmark_sweep_summary.json](../data/benchmark_sweep_summary.json), and [images/benchmark_sweep_heatmap.svg](../images/benchmark_sweep_heatmap.svg).

### Phase 3: Multi-Plaquette Lattice

- Promote `Psi` from a single plaquette observable to an average over a monitored plaquette family.
- Let `M_ij` evolve edge-by-edge from local slip energy.
- Reuse the same metrics used in the single-plaquette case, but add spatial concentration metrics to detect whether stress localizes on damaged cuts.

This phase is now implemented as a stylized four-plaquette network in [simulations/lattice_network.py](../simulations/lattice_network.py) with committed outputs in [data/lattice_network_summary.json](../data/lattice_network_summary.json), [data/lattice_network_trace.csv](../data/lattice_network_trace.csv), and [images/lattice_network.svg](../images/lattice_network.svg).

## Minimal Falsifiers

The equation should be considered weakened if any of the following happen consistently.

1. The stabilized law cannot outperform the parent law on any coherence-sensitive recovery metric.
2. Memory accumulation never suppresses conductance during slip-heavy windows.
3. The law changes the preferred steady-state phase instead of only rescaling the amplitude.
4. The numerics fail to recover the parent law in the `kappa_Psi = xi = 0` limit.

## Repository Outputs

- [data/reference_trace.csv](../data/reference_trace.csv) stores the committed reference trajectory.
- [data/reference_summary.json](../data/reference_summary.json) stores scenario-level metrics.
- [images/reference_trace.svg](../images/reference_trace.svg) visualizes the reference run.
- [data/benchmark_forcing.csv](../data/benchmark_forcing.csv) stores the vendored benchmark forcing trace used by the new suite.
- [data/benchmark_scenarios.json](../data/benchmark_scenarios.json) stores scenario-level results under the imported benchmark.
- [data/benchmark_sweep_summary.json](../data/benchmark_sweep_summary.json) stores the top-scoring benchmark sweep configurations.
- [images/benchmark_scenarios.svg](../images/benchmark_scenarios.svg) visualizes the imported benchmark scenarios.
- [images/benchmark_sweep_heatmap.svg](../images/benchmark_sweep_heatmap.svg) visualizes the parameter sweep.
- [images/lattice_network.svg](../images/lattice_network.svg) visualizes the multi-plaquette lattice response.

## Near-Term Extensions

1. Add a sweep script that emits a small grid of JSON summaries for `(kappa_Psi, xi)` pairs.
2. Add an explicit memory-only comparison case with `kappa_Psi = 0`, `xi > 0`.
3. Link the reference simulation to an existing QWZ recovery or topolectrical benchmark so the forcing signals are no longer synthetic.
