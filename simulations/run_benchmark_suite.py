from __future__ import annotations

import json
from pathlib import Path

try:
    from .benchmark_suite import (
        ensure_vendored_benchmark_trace,
        run_parameter_sweep,
        run_scenario_suite,
        scenario_summary_payload,
        write_scenario_svg,
        write_sweep_csv,
        write_sweep_heatmap,
        write_sweep_summary,
    )
    from .bz_curve_memory import ConductanceLawConfig
    from .lattice_network import (
        LatticeNetworkConfig,
        simulate_lattice_network,
        write_lattice_summary,
        write_lattice_svg,
        write_lattice_trace_csv,
    )
except ImportError:
    from benchmark_suite import (
        ensure_vendored_benchmark_trace,
        run_parameter_sweep,
        run_scenario_suite,
        scenario_summary_payload,
        write_scenario_svg,
        write_sweep_csv,
        write_sweep_heatmap,
        write_sweep_summary,
    )
    from bz_curve_memory import ConductanceLawConfig
    from lattice_network import (
        LatticeNetworkConfig,
        simulate_lattice_network,
        write_lattice_summary,
        write_lattice_svg,
        write_lattice_trace_csv,
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    trace = ensure_vendored_benchmark_trace(repo_root)

    scenarios = run_scenario_suite(trace)
    (repo_root / "data" / "benchmark_scenarios.json").write_text(
        json.dumps(scenario_summary_payload(trace, scenarios), indent=2),
        encoding="utf-8",
    )
    write_scenario_svg(repo_root / "images" / "benchmark_scenarios.svg", trace, scenarios)

    sweep_entries = run_parameter_sweep(trace)
    write_sweep_csv(repo_root / "data" / "benchmark_sweep.csv", sweep_entries)
    write_sweep_summary(repo_root / "data" / "benchmark_sweep_summary.json", sweep_entries)
    write_sweep_heatmap(repo_root / "images" / "benchmark_sweep_heatmap.svg", sweep_entries)

    network = LatticeNetworkConfig()
    baseline = simulate_lattice_network(
        trace,
        ConductanceLawConfig(kappa_psi=0.0, xi=0.0),
        network,
        name="baseline_parent_law",
    )
    full_law = simulate_lattice_network(
        trace,
        ConductanceLawConfig(kappa_psi=0.35, xi=2.5),
        network,
        name="loop_and_memory_stabilized",
    )
    write_lattice_trace_csv(repo_root / "data" / "lattice_network_trace.csv", baseline, full_law)
    write_lattice_summary(repo_root / "data" / "lattice_network_summary.json", trace, baseline, full_law)
    write_lattice_svg(repo_root / "images" / "lattice_network.svg", trace, baseline, full_law)


if __name__ == "__main__":
    main()
