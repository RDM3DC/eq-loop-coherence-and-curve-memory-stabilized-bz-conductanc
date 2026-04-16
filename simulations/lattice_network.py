from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean

try:
    from .benchmark_suite import BenchmarkTrace, benchmark_windows, polyline_points, axis_markup
    from .bz_curve_memory import ConductanceLawConfig, alpha_g, mu_g, reinforcement_factor, window_average, wrapped_angle
except ImportError:
    from benchmark_suite import BenchmarkTrace, benchmark_windows, polyline_points, axis_markup
    from bz_curve_memory import ConductanceLawConfig, alpha_g, mu_g, reinforcement_factor, window_average, wrapped_angle


DEFAULT_PLAQUETTES = (
    ((0, 1), (8, 1), (2, -1), (6, -1)),
    ((1, 1), (10, 1), (3, -1), (8, -1)),
    ((2, 1), (9, 1), (4, -1), (7, -1)),
    ((3, 1), (11, 1), (5, -1), (9, -1)),
)


@dataclass(frozen=True)
class LatticeNetworkConfig:
    edge_weights: tuple[float, ...] = (1.05, 1.00, 1.12, 1.08, 0.94, 0.92, 0.88, 0.86, 1.15, 1.10, 0.90, 0.88)
    damage_coupling: tuple[float, ...] = (-0.10, -0.08, 0.82, 0.78, -0.06, -0.04, 0.14, 0.12, 0.88, 0.84, 0.16, 0.14)
    phase_offsets: tuple[float, ...] = (0.10, 0.04, -0.18, -0.12, 0.16, 0.20, -0.08, -0.02, 0.14, 0.10, -0.04, -0.10)
    phase_shear: tuple[float, ...] = (0.04, 0.08, 0.28, 0.22, -0.06, -0.10, 0.18, 0.16, 0.30, 0.26, -0.12, -0.14)
    slip_coupling: tuple[float, ...] = (0.12, 0.10, 0.48, 0.44, 0.08, 0.06, 0.18, 0.16, 0.52, 0.48, 0.20, 0.18)
    plaquettes: tuple[tuple[tuple[int, int], ...], ...] = DEFAULT_PLAQUETTES


@dataclass
class LatticeSimulationResult:
    name: str
    config: ConductanceLawConfig
    times: list[float]
    global_psi: list[float]
    mean_magnitude: list[float]
    mean_memory: list[float]
    max_memory: list[float]
    concentration: list[float]
    stressed_memory: list[float]


def incident_plaquette_map(plaquettes: tuple[tuple[tuple[int, int], ...], ...], edge_count: int) -> list[list[int]]:
    incidents = [[] for _ in range(edge_count)]
    for plaquette_index, plaquette in enumerate(plaquettes):
        for edge_index, _ in plaquette:
            incidents[edge_index].append(plaquette_index)
    return incidents


def default_edge_phase(conductance: complex, fallback_phase: float) -> float:
    if abs(conductance) <= 1e-12:
        return fallback_phase
    return math.atan2(conductance.imag, conductance.real)


def memory_concentration(memories: list[float]) -> float:
    total = sum(memories)
    if total <= 1e-12:
        return 0.0
    return sum((value / total) ** 2 for value in memories)


def simulate_lattice_network(
    trace: BenchmarkTrace,
    law_config: ConductanceLawConfig,
    network_config: LatticeNetworkConfig,
    *,
    name: str,
) -> LatticeSimulationResult:
    edge_count = len(network_config.edge_weights)
    conductances = [0j for _ in range(edge_count)]
    memories = [0.0 for _ in range(edge_count)]
    previous_edge_phases = [trace.phase[0] + offset for offset in network_config.phase_offsets]
    incidents = incident_plaquette_map(network_config.plaquettes, edge_count)

    times = trace.times
    global_psi_series: list[float] = []
    mean_magnitude_series: list[float] = []
    mean_memory_series: list[float] = []
    max_memory_series: list[float] = []
    concentration_series: list[float] = []
    stressed_memory_series: list[float] = []

    for index, time_value in enumerate(times):
        dt = law_config.dt if index == 0 else max(time_value - times[index - 1], 1e-9)
        drive_phases = [
            wrapped_angle(
                trace.phase[index]
                + network_config.phase_offsets[edge_index]
                + network_config.phase_shear[edge_index] * trace.damage_signal[index]
                + network_config.slip_coupling[edge_index] * trace.slip_signal[index]
                + 0.10 * math.sin(0.9 * time_value + 0.35 * edge_index)
            )
            for edge_index in range(edge_count)
        ]
        edge_phases = [
            default_edge_phase(conductance, fallback_phase)
            for conductance, fallback_phase in zip(conductances, drive_phases)
        ]

        plaquette_holonomies: list[float] = []
        plaquette_coherences: list[float] = []
        for plaquette in network_config.plaquettes:
            holonomy = sum(sign * edge_phases[edge_index] for edge_index, sign in plaquette)
            plaquette_holonomies.append(holonomy)
            plaquette_coherences.append(math.cos(holonomy / max(trace.pi_a[index], 1e-9)))
        global_psi = fmean(plaquette_coherences)

        entropy_value = trace.entropy_signal[index]
        alpha_value = alpha_g(entropy_value, law_config)
        mu_value = mu_g(entropy_value, law_config)

        local_psi = [
            fmean(plaquette_coherences[plaquette_index] for plaquette_index in incidents[edge_index])
            if incidents[edge_index]
            else global_psi
            for edge_index in range(edge_count)
        ]

        updated_conductances: list[complex] = []
        for edge_index, conductance in enumerate(conductances):
            current_magnitude = trace.current_drive[index] * network_config.edge_weights[edge_index]
            current_magnitude *= max(0.20, 1.0 - network_config.damage_coupling[edge_index] * trace.damage_signal[index])
            gain = reinforcement_factor(local_psi[edge_index], memories[edge_index], law_config.kappa_psi, law_config.xi)
            drive = complex(math.cos(drive_phases[edge_index]), math.sin(drive_phases[edge_index]))
            drive *= alpha_value * gain * current_magnitude
            updated_conductances.append(conductance + dt * (drive - mu_value * conductance))

        updated_phases = [
            default_edge_phase(conductance, fallback_phase)
            for conductance, fallback_phase in zip(updated_conductances, drive_phases)
        ]
        updated_memories: list[float] = []
        for edge_index, memory_value in enumerate(memories):
            phase_rate = abs(wrapped_angle(updated_phases[edge_index] - previous_edge_phases[edge_index]))
            phase_rate /= max(trace.pi_a[index] * dt, 1e-9)
            disorder = 0.5 * (1.0 - local_psi[edge_index])
            slip_load = phase_rate * phase_rate + 0.65 * disorder + 0.35 * trace.damage_signal[index] * trace.slip_signal[index]
            derivative = 0.65 * law_config.memory_gain * slip_load - 1.10 * law_config.memory_decay * memory_value
            updated_memories.append(max(0.0, memory_value + dt * derivative))

        conductances = updated_conductances
        memories = updated_memories
        previous_edge_phases = updated_phases

        global_psi_series.append(global_psi)
        mean_magnitude_series.append(fmean(abs(value) for value in conductances))
        mean_memory_series.append(fmean(memories))
        max_memory_series.append(max(memories))
        concentration_series.append(memory_concentration(memories))
        stressed_memory_series.append(fmean(memories[edge_index] for edge_index in (2, 3, 8, 9)))

    return LatticeSimulationResult(
        name=name,
        config=law_config,
        times=times,
        global_psi=global_psi_series,
        mean_magnitude=mean_magnitude_series,
        mean_memory=mean_memory_series,
        max_memory=max_memory_series,
        concentration=concentration_series,
        stressed_memory=stressed_memory_series,
    )


def summarize_lattice_result(result: LatticeSimulationResult, trace: BenchmarkTrace) -> dict[str, float]:
    damage_window, recovery_window = benchmark_windows(trace)
    return {
        "min_global_psi": min(result.global_psi),
        "peak_mean_magnitude": max(result.mean_magnitude),
        "final_mean_magnitude": result.mean_magnitude[-1],
        "peak_mean_memory": max(result.mean_memory),
        "peak_memory_concentration": max(result.concentration),
        "damage_window_mean_magnitude": window_average(
            result,
            damage_window[0],
            damage_window[1],
            result.mean_magnitude,
        ),
        "recovery_window_mean_magnitude": window_average(
            result,
            recovery_window[0],
            recovery_window[1],
            result.mean_magnitude,
        ),
    }


def write_lattice_trace_csv(path: Path, baseline: LatticeSimulationResult, full_law: LatticeSimulationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "time",
                "baseline_mean_magnitude",
                "full_law_mean_magnitude",
                "baseline_mean_memory",
                "full_law_mean_memory",
                "baseline_global_psi",
                "full_law_global_psi",
                "full_law_concentration",
                "full_law_stressed_memory",
            ]
        )
        for index, time_value in enumerate(full_law.times):
            writer.writerow(
                [
                    f"{time_value:.6f}",
                    f"{baseline.mean_magnitude[index]:.6f}",
                    f"{full_law.mean_magnitude[index]:.6f}",
                    f"{baseline.mean_memory[index]:.6f}",
                    f"{full_law.mean_memory[index]:.6f}",
                    f"{baseline.global_psi[index]:.6f}",
                    f"{full_law.global_psi[index]:.6f}",
                    f"{full_law.concentration[index]:.6f}",
                    f"{full_law.stressed_memory[index]:.6f}",
                ]
            )


def write_lattice_summary(path: Path, trace: BenchmarkTrace, baseline: LatticeSimulationResult, full_law: LatticeSimulationResult) -> None:
    baseline_metrics = summarize_lattice_result(baseline, trace)
    full_metrics = summarize_lattice_result(full_law, trace)
    payload = {
        "trace_source": trace.source_name,
        "baseline_parent_law": {
            "config": asdict(baseline.config),
            "metrics": baseline_metrics,
        },
        "loop_and_memory_stabilized": {
            "config": asdict(full_law.config),
            "metrics": full_metrics,
        },
        "comparison": {
            "damage_window_shift": full_metrics["damage_window_mean_magnitude"]
            - baseline_metrics["damage_window_mean_magnitude"],
            "recovery_window_shift": full_metrics["recovery_window_mean_magnitude"]
            - baseline_metrics["recovery_window_mean_magnitude"],
            "peak_memory_concentration_shift": full_metrics["peak_memory_concentration"]
            - baseline_metrics["peak_memory_concentration"],
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_lattice_svg(path: Path, trace: BenchmarkTrace, baseline: LatticeSimulationResult, full_law: LatticeSimulationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 940
    height = 900
    panel_x = 80
    panel_width = 780
    panel_height = 180
    top_y = 90
    middle_y = 350
    bottom_y = 610
    damage_x = panel_x + (trace.damage_time / trace.times[-1]) * panel_width

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Multi-plaquette lattice benchmark response</title>
  <desc id="desc">Stylized four-plaquette lattice comparison between the parent and stabilized laws under the vendored benchmark trace.</desc>
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="80" y="42" font-size="28" font-family="Georgia" fill="#0f172a">Multi-Plaquette Lattice Response</text>
  <text x="80" y="66" font-size="14" font-family="Georgia" fill="#334155">Four coupled plaquettes with corridor damage, local curve memory, and loop-coherence feedback.</text>
  {axis_markup("Mean conductance magnitude", panel_x, top_y, panel_width, panel_height, damage_x)}
  <polyline fill="none" stroke="#9a3412" stroke-width="2.4" points="{polyline_points(baseline.mean_magnitude, panel_x, top_y, panel_width, panel_height)}"/>
  <polyline fill="none" stroke="#065f46" stroke-width="2.4" points="{polyline_points(full_law.mean_magnitude, panel_x, top_y, panel_width, panel_height)}"/>
  <text x="650" y="108" font-size="13" font-family="Georgia" fill="#9a3412">baseline parent law</text>
  <text x="650" y="126" font-size="13" font-family="Georgia" fill="#065f46">loop + memory stabilized law</text>
  {axis_markup("Global Psi and stressed-edge memory", panel_x, middle_y, panel_width, panel_height, damage_x)}
  <polyline fill="none" stroke="#1d4ed8" stroke-width="2.4" points="{polyline_points(full_law.global_psi, panel_x, middle_y, panel_width, panel_height)}"/>
  <polyline fill="none" stroke="#7c3aed" stroke-width="2.4" points="{polyline_points(full_law.stressed_memory, panel_x, middle_y, panel_width, panel_height)}"/>
  <text x="650" y="368" font-size="13" font-family="Georgia" fill="#1d4ed8">global psi</text>
  <text x="650" y="386" font-size="13" font-family="Georgia" fill="#7c3aed">stressed-edge mean memory</text>
  {axis_markup("Memory concentration", panel_x, bottom_y, panel_width, panel_height, damage_x)}
  <polyline fill="none" stroke="#b45309" stroke-width="2.4" points="{polyline_points(full_law.concentration, panel_x, bottom_y, panel_width, panel_height)}"/>
  <text x="650" y="628" font-size="13" font-family="Georgia" fill="#b45309">Herfindahl memory concentration</text>
</svg>
'''
    path.write_text(svg, encoding="utf-8")
