from __future__ import annotations

import csv
import json
from dataclasses import asdict, replace
from pathlib import Path

from bz_curve_memory import ConductanceLawConfig, SimulationResult, simulate_reference_scenario, summarize_result


EQUATION_ID = "eq-loop-coherence-and-curve-memory-stabilized-bz-conductanc"


def write_trace_csv(
    path: Path,
    baseline: SimulationResult,
    full_law: SimulationResult,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "time",
                "loop_coherence",
                "mean_memory",
                "baseline_mean_magnitude",
                "full_law_mean_magnitude",
                "baseline_mean_gain",
                "full_law_mean_gain",
                "slip_energy",
            ]
        )
        for index, time_value in enumerate(full_law.times):
            writer.writerow(
                [
                    f"{time_value:.4f}",
                    f"{full_law.loop_coherence[index]:.6f}",
                    f"{full_law.mean_memory[index]:.6f}",
                    f"{baseline.mean_magnitude[index]:.6f}",
                    f"{full_law.mean_magnitude[index]:.6f}",
                    f"{baseline.mean_gain[index]:.6f}",
                    f"{full_law.mean_gain[index]:.6f}",
                    f"{full_law.slip_energy[index]:.6f}",
                ]
            )


def comparison_summary(baseline: SimulationResult, full_law: SimulationResult) -> dict[str, float]:
    baseline_summary = summarize_result(baseline)
    full_summary = summarize_result(full_law)
    return {
        "damage_window_magnitude_shift": full_summary["damage_window_mean_magnitude"]
        - baseline_summary["damage_window_mean_magnitude"],
        "recovery_window_magnitude_shift": full_summary["recovery_window_mean_magnitude"]
        - baseline_summary["recovery_window_mean_magnitude"],
        "late_time_std_shift": full_summary["late_time_magnitude_std"]
        - baseline_summary["late_time_magnitude_std"],
        "peak_magnitude_shift": full_summary["peak_mean_magnitude"]
        - baseline_summary["peak_mean_magnitude"],
    }


def write_summary_json(path: Path, baseline: SimulationResult, full_law: SimulationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "equation_id": EQUATION_ID,
        "generated_by": "simulations/run_reference_simulation.py",
        "scenarios": {
            "baseline_parent_law": {
                "config": asdict(baseline.config),
                "metrics": summarize_result(baseline),
            },
            "loop_and_memory_stabilized_law": {
                "config": asdict(full_law.config),
                "metrics": summarize_result(full_law),
            },
        },
        "comparison": comparison_summary(baseline, full_law),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def polyline_points(values: list[float], x0: float, y0: float, width: float, height: float) -> str:
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum if maximum > minimum else 1.0
    point_strings: list[str] = []
    for index, value in enumerate(values):
        x_value = x0 + (index / max(1, len(values) - 1)) * width
        y_value = y0 + height - ((value - minimum) / span) * height
        point_strings.append(f"{x_value:.2f},{y_value:.2f}")
    return " ".join(point_strings)


def axis_markup(title: str, x0: float, y0: float, width: float, height: float, damage_x: float) -> str:
    x_axis_y = y0 + height
    return "\n".join(
        [
            f'<text x="{x0:.0f}" y="{y0 - 12:.0f}" font-size="18" font-family="Georgia">{title}</text>',
            f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x0:.0f}" y2="{x_axis_y:.0f}" stroke="#1f2937" stroke-width="1.5"/>',
            f'<line x1="{x0:.0f}" y1="{x_axis_y:.0f}" x2="{x0 + width:.0f}" y2="{x_axis_y:.0f}" stroke="#1f2937" stroke-width="1.5"/>',
            f'<line x1="{damage_x:.2f}" y1="{y0:.0f}" x2="{damage_x:.2f}" y2="{x_axis_y:.0f}" stroke="#b45309" stroke-width="1.2" stroke-dasharray="6 6"/>',
            f'<text x="{damage_x + 8:.2f}" y="{y0 + 16:.0f}" font-size="12" fill="#92400e" font-family="Georgia">damage center</text>',
        ]
    )


def write_svg(path: Path, baseline: SimulationResult, full_law: SimulationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 900
    height = 620
    panel_x = 80
    panel_width = 760
    top_y = 90
    panel_height = 180
    bottom_y = 360
    damage_x = panel_x + (full_law.config.damage_center / full_law.config.total_time) * panel_width

    magnitude_lines = "\n".join(
        [
            f'<polyline fill="none" stroke="#9a3412" stroke-width="2.5" points="{polyline_points(baseline.mean_magnitude, panel_x, top_y, panel_width, panel_height)}"/>',
            f'<polyline fill="none" stroke="#065f46" stroke-width="2.5" points="{polyline_points(full_law.mean_magnitude, panel_x, top_y, panel_width, panel_height)}"/>',
        ]
    )
    coherence_lines = "\n".join(
        [
            f'<polyline fill="none" stroke="#1d4ed8" stroke-width="2.5" points="{polyline_points(full_law.loop_coherence, panel_x, bottom_y, panel_width, panel_height)}"/>',
            f'<polyline fill="none" stroke="#7c3aed" stroke-width="2.5" points="{polyline_points(full_law.mean_memory, panel_x, bottom_y, panel_width, panel_height)}"/>',
        ]
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Loop-coherence and curve-memory stabilized BZ conductance reference simulation</title>
  <desc id="desc">Comparison between the parent BZ law and the loop-coherence plus curve-memory stabilized law on a single-plaquette reference trajectory.</desc>
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="80" y="42" font-size="28" font-family="Georgia" fill="#0f172a">Reference Simulation</text>
  <text x="80" y="66" font-size="14" font-family="Georgia" fill="#334155">Single-plaquette trajectory with a localized slip burst and entropy-gated damping.</text>
  {axis_markup("Mean conductance magnitude", panel_x, top_y, panel_width, panel_height, damage_x)}
  {magnitude_lines}
  <text x="620" y="108" font-size="13" font-family="Georgia" fill="#9a3412">baseline parent law</text>
  <text x="620" y="128" font-size="13" font-family="Georgia" fill="#065f46">loop + memory stabilized law</text>
  {axis_markup("Loop coherence and mean memory", panel_x, bottom_y, panel_width, panel_height, damage_x)}
  {coherence_lines}
  <text x="620" y="378" font-size="13" font-family="Georgia" fill="#1d4ed8">Psi(t)</text>
  <text x="620" y="398" font-size="13" font-family="Georgia" fill="#7c3aed">mean M(t)</text>
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    baseline = simulate_reference_scenario(ConductanceLawConfig(kappa_psi=0.0, xi=0.0))
    full_law = simulate_reference_scenario(ConductanceLawConfig())
    write_trace_csv(root / "data" / "reference_trace.csv", baseline, full_law)
    write_summary_json(root / "data" / "reference_summary.json", baseline, full_law)
    write_svg(root / "images" / "reference_trace.svg", baseline, full_law)


if __name__ == "__main__":
    main()
