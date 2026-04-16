import cmath
import math
import unittest

from simulations.bz_curve_memory import (
    ConductanceLawConfig,
    loop_coherence_from_holonomy,
    reinforcement_factor,
    simulate_reference_scenario,
    steady_state_conductance,
    summarize_result,
)


class ConductanceLawTests(unittest.TestCase):
    def test_parent_law_is_exact_limit(self) -> None:
        self.assertAlmostEqual(
            reinforcement_factor(psi=0.4, memory_value=0.7, kappa_psi=0.0, xi=0.0),
            1.0,
        )

    def test_reinforcement_moves_in_expected_directions(self) -> None:
        low_coherence = reinforcement_factor(psi=0.1, memory_value=0.2, kappa_psi=0.5, xi=1.0)
        high_coherence = reinforcement_factor(psi=0.8, memory_value=0.2, kappa_psi=0.5, xi=1.0)
        high_memory = reinforcement_factor(psi=0.8, memory_value=0.6, kappa_psi=0.5, xi=1.0)
        self.assertGreater(high_coherence, low_coherence)
        self.assertLess(high_memory, high_coherence)

    def test_loop_coherence_stays_bounded(self) -> None:
        samples = [
            loop_coherence_from_holonomy(-3.2, 1.0),
            loop_coherence_from_holonomy(0.0, 1.0),
            loop_coherence_from_holonomy(2.4, 1.0),
        ]
        for value in samples:
            self.assertGreaterEqual(value, -1.0)
            self.assertLessEqual(value, 1.0)

    def test_closed_form_steady_state_matches_expected_magnitude_and_phase(self) -> None:
        conductance = steady_state_conductance(
            alpha_value=1.2,
            mu_value=0.8,
            current_magnitude=0.9,
            phase=0.25,
            psi=0.5,
            memory_value=0.4,
            kappa_psi=0.6,
            xi=0.8,
        )
        expected_magnitude = 1.2 * ((1.0 + 0.6 * 0.5) / (1.0 + 0.8 * 0.4)) * 0.9 / 0.8
        self.assertAlmostEqual(abs(conductance), expected_magnitude)
        self.assertAlmostEqual(cmath.phase(conductance), 0.25)

    def test_reference_simulation_produces_nonnegative_memory(self) -> None:
        result = simulate_reference_scenario(ConductanceLawConfig(total_time=2.0, dt=0.1))
        self.assertEqual(len(result.times), 21)
        self.assertTrue(all(value >= 0.0 for value in result.mean_memory))
        self.assertGreater(max(result.mean_magnitude), 0.0)
        summary = summarize_result(result)
        self.assertIn("peak_memory", summary)

    def test_reference_model_rejects_kappa_above_unity(self) -> None:
        with self.assertRaises(ValueError):
            ConductanceLawConfig(kappa_psi=1.1)


if __name__ == "__main__":
    unittest.main()
