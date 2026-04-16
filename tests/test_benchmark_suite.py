from pathlib import Path
import unittest

from simulations.benchmark_suite import (
    load_local_benchmark_trace,
    run_parameter_sweep,
    run_scenario_suite,
    summarize_benchmark_result,
)
from simulations.lattice_network import (
    LatticeNetworkConfig,
    simulate_lattice_network,
    summarize_lattice_result,
)
from simulations.bz_curve_memory import ConductanceLawConfig


REPO_ROOT = Path(__file__).resolve().parents[1]


class BenchmarkSuiteTests(unittest.TestCase):
    def load_trace(self):
        return load_local_benchmark_trace(REPO_ROOT / "data" / "benchmark_forcing.csv")

    def test_vendored_trace_has_expected_damage_time(self) -> None:
        trace = self.load_trace()
        self.assertAlmostEqual(trace.damage_time, 2.0)
        self.assertGreater(len(trace.times), 50)
        self.assertTrue(all(-1.0 <= value <= 1.0 for value in trace.psi))

    def test_benchmark_scenarios_show_recovery_tradeoffs(self) -> None:
        trace = self.load_trace()
        results = run_scenario_suite(trace)
        baseline = summarize_benchmark_result(results["baseline_parent_law"], trace)
        loop_only = summarize_benchmark_result(results["loop_only"], trace)
        memory_only = summarize_benchmark_result(results["memory_only"], trace)

        self.assertGreater(
            baseline["recovery_window_mean_magnitude"],
            baseline["damage_window_mean_magnitude"],
        )
        self.assertGreater(
            loop_only["recovery_window_mean_magnitude"],
            baseline["recovery_window_mean_magnitude"],
        )
        self.assertLess(
            memory_only["damage_window_mean_magnitude"],
            baseline["damage_window_mean_magnitude"],
        )

    def test_parameter_sweep_returns_full_grid_with_positive_best_score(self) -> None:
        trace = self.load_trace()
        entries = run_parameter_sweep(trace)
        self.assertEqual(len(entries), 36)
        self.assertGreater(max(entry.score for entry in entries), 0.0)

    def test_lattice_suite_shows_positive_recovery_shift(self) -> None:
        trace = self.load_trace()
        network = LatticeNetworkConfig()
        baseline = simulate_lattice_network(
            trace,
            ConductanceLawConfig(kappa_psi=0.0, xi=0.0),
            network,
            name="baseline",
        )
        full_law = simulate_lattice_network(
            trace,
            ConductanceLawConfig(kappa_psi=0.35, xi=2.5),
            network,
            name="full_law",
        )
        baseline_metrics = summarize_lattice_result(baseline, trace)
        full_metrics = summarize_lattice_result(full_law, trace)
        self.assertGreater(
            full_metrics["recovery_window_mean_magnitude"],
            baseline_metrics["recovery_window_mean_magnitude"],
        )
