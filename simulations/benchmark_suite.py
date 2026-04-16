from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean, pstdev

try:
    from .bz_curve_memory import (
        ConductanceLawConfig,
        alpha_g,
        mu_g,
        reinforcement_factor,
        window_average,
        wrapped_angle,
    )
except ImportError:
    from bz_curve_memory import (
        ConductanceLawConfig,
        alpha_g,
        mu_g,
        reinforcement_factor,
        window_average,
        wrapped_angle,
    )


EXTERNAL_TRACE_RELATIVE = Path(
    "eq-flat-channel-loop-signature-pi-f-health-observable/data/flat_channel_loop_timeseries.csv"
)


@dataclass(frozen=True)
class BenchmarkTrace:
    source_name: str
    times: list[float]
    psi: list[float]
    holonomy_cosine: list[float]
    signature_drive: list[float]
    current_drive: list[float]
    phase: list[float]
    slip_signal: list[float]
    damage_signal: list[float]
    entropy_signal: list[float]
    pi_a: list[float]
    transfer: list[float]
    boundary_fraction: list[float]
    top_edge_fraction: list[float]
    raw_entropy: list[float]
    damage_time: float
    baseline_raw_entropy: float


@dataclass
class BenchmarkScenarioResult:
    name: str
    config: ConductanceLawConfig
    trace_source: str
    times: list[float]
    psi: list[float]
    current_drive: list[float]
    slip_signal: list[float]
    damage_signal: list[float]
    entropy_signal: list[float]
    memory: list[float]
    gain: list[float]
    magnitude: list[float]
    phase: list[float]


@dataclass(frozen=True)
class SweepEntry:
    kappa_psi: float
    xi: float
    score: float
    recovery_lift: float
    damage_shift: float
    late_std_shift: float


def circular_mean(values: list[float]) -> float:
    sine_sum = fmean(math.sin(value) for value in values)
    cosine_sum = fmean(math.cos(value) for value in values)
    return math.atan2(sine_sum, cosine_sum)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def safe_normalize(values: list[float]) -> list[float]:
    minimum = min(values)
    maximum = max(values)
    if maximum <= minimum:
        return [0.0 for _ in values]
    span = maximum - minimum
    return [(value - minimum) / span for value in values]


def derivative_signal(values: list[float], times: list[float]) -> list[float]:
    output = [0.0]
    for index in range(1, len(values)):
        dt = max(times[index] - times[index - 1], 1e-9)
        output.append((values[index] - values[index - 1]) / dt)
    return output


def exponential_envelope(values: list[float], times: list[float], decay_rate: float) -> list[float]:
    state = 0.0
    output: list[float] = []
    for index, value in enumerate(values):
        if index == 0:
            dt = 0.0
        else:
            dt = max(times[index] - times[index - 1], 1e-9)
        state = max(value, state * math.exp(-decay_rate * dt))
        output.append(state)
    return output


def source_trace_path(repo_root: Path) -> Path:
    return repo_root.parent / EXTERNAL_TRACE_RELATIVE


def read_external_source_rows(path: Path) -> list[dict[str, float]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{key: float(value) for key, value in row.items()} for row in reader]


def build_trace_from_source_rows(rows: list[dict[str, float]], source_name: str) -> BenchmarkTrace:
    times = [row["t"] for row in rows]
    top_signature = [row["top_strip_signature"] for row in rows]
    boundary_signature = [row["boundary_signature"] for row in rows]
    center_signature = [row["center_signature"] for row in rows]
    pi_a = [row["pi_a"] for row in rows]
    transfer = [row["transfer"] for row in rows]
    boundary_fraction = [row["boundary_fraction"] for row in rows]
    top_edge_fraction = [row["top_edge_fraction"] for row in rows]
    raw_entropy = [row["entropy"] for row in rows]

    signature_drive_raw = [
        0.60 * top_value + 0.30 * boundary_value + 0.10 * center_value
        for top_value, boundary_value, center_value in zip(
            top_signature,
            boundary_signature,
            center_signature,
        )
    ]
    signature_drop_rate = [max(0.0, -value) for value in derivative_signal(signature_drive_raw, times)]
    damage_impulse = safe_normalize(signature_drop_rate)
    damage_signal = exponential_envelope(damage_impulse, times, decay_rate=1.35)
    damage_index = max(range(len(damage_signal)), key=damage_signal.__getitem__)
    damage_time = times[damage_index]
    pre_damage_signature = [value for time_value, value in zip(times, signature_drive_raw) if time_value <= damage_time]
    pre_damage_entropy = [value for time_value, value in zip(times, raw_entropy) if time_value <= damage_time]
    signature_reference = max(pre_damage_signature) if pre_damage_signature else max(signature_drive_raw)
    baseline_raw_entropy = fmean(pre_damage_entropy) if pre_damage_entropy else raw_entropy[0]
    transport_norm = safe_normalize(transfer)
    top_edge_norm = safe_normalize(top_edge_fraction)

    holonomy_cosine: list[float] = []
    signature_drive: list[float] = []
    current_drive: list[float] = []
    phase: list[float] = []
    entropy_signal: list[float] = []
    for row, raw_signature, transport_value, top_edge_value, damage_value in zip(
        rows,
        signature_drive_raw,
        transport_norm,
        top_edge_norm,
        damage_signal,
    ):
        top_cosine = math.cos(row["top_strip_holonomy"] / max(row["pi_a"], 1e-9))
        boundary_cosine = math.cos(row["boundary_holonomy"] / max(row["pi_a"], 1e-9))
        center_cosine = math.cos(row["center_holonomy"] / max(row["pi_a"], 1e-9))
        mean_cosine = (top_cosine + boundary_cosine + center_cosine) / 3.0
        normalized_signature = clamp(raw_signature / max(signature_reference, 1e-9), 0.0, 1.05)

        holonomy_cosine.append(mean_cosine)
        signature_drive.append(normalized_signature)
        current_drive.append(clamp(0.25 + 0.55 * transport_value + 0.20 * top_edge_value - 0.18 * damage_value, 0.20, 1.10))
        phase.append(
            wrapped_angle(
                (
                    row["top_strip_holonomy"]
                    + row["boundary_holonomy"]
                    + row["center_holonomy"]
                )
                / 12.0
            )
        )
        entropy_signal.append(0.42 + 0.16 * damage_value + 0.04 * (1.0 - mean_cosine))

    holonomy_rate = []
    for index, row in enumerate(rows):
        if index == 0:
            holonomy_rate.append(0.0)
            continue
        dt = max(times[index] - times[index - 1], 1e-9)
        rate_value = (
            abs(wrapped_angle(row["top_strip_holonomy"] - rows[index - 1]["top_strip_holonomy"]))
            + abs(wrapped_angle(row["boundary_holonomy"] - rows[index - 1]["boundary_holonomy"]))
            + abs(wrapped_angle(row["center_holonomy"] - rows[index - 1]["center_holonomy"]))
        ) / (3.0 * dt)
        holonomy_rate.append(rate_value)
    rate_norm = safe_normalize(holonomy_rate)
    slip_signal = [
        clamp(0.45 * holonomy_component + 0.70 * damage_component, 0.0, 1.5)
        for holonomy_component, damage_component in zip(rate_norm, damage_signal)
    ]

    psi = [
        clamp(0.35 * cosine + 0.65 * (1.0 - 2.0 * damage_value), -1.0, 1.0)
        for cosine, damage_value in zip(holonomy_cosine, damage_signal)
    ]

    return BenchmarkTrace(
        source_name=source_name,
        times=times,
        psi=psi,
        holonomy_cosine=holonomy_cosine,
        signature_drive=signature_drive,
        current_drive=current_drive,
        phase=phase,
        slip_signal=slip_signal,
        damage_signal=damage_signal,
        entropy_signal=entropy_signal,
        pi_a=pi_a,
        transfer=transfer,
        boundary_fraction=boundary_fraction,
        top_edge_fraction=top_edge_fraction,
        raw_entropy=raw_entropy,
        damage_time=damage_time,
        baseline_raw_entropy=baseline_raw_entropy,
    )


def trace_csv_fieldnames() -> list[str]:
    return [
        "time",
        "psi",
        "holonomy_cosine",
        "signature_drive",
        "current_drive",
        "phase",
        "slip_signal",
        "damage_signal",
        "entropy_signal",
        "pi_a",
        "transfer",
        "boundary_fraction",
        "top_edge_fraction",
        "raw_entropy",
    ]


def write_benchmark_trace_csv(path: Path, trace: BenchmarkTrace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=trace_csv_fieldnames())
        writer.writeheader()
        for index, time_value in enumerate(trace.times):
            writer.writerow(
                {
                    "time": f"{time_value:.6f}",
                    "psi": f"{trace.psi[index]:.6f}",
                    "holonomy_cosine": f"{trace.holonomy_cosine[index]:.6f}",
                    "signature_drive": f"{trace.signature_drive[index]:.6f}",
                    "current_drive": f"{trace.current_drive[index]:.6f}",
                    "phase": f"{trace.phase[index]:.6f}",
                    "slip_signal": f"{trace.slip_signal[index]:.6f}",
                    "damage_signal": f"{trace.damage_signal[index]:.6f}",
                    "entropy_signal": f"{trace.entropy_signal[index]:.6f}",
                    "pi_a": f"{trace.pi_a[index]:.6f}",
                    "transfer": f"{trace.transfer[index]:.6f}",
                    "boundary_fraction": f"{trace.boundary_fraction[index]:.6f}",
                    "top_edge_fraction": f"{trace.top_edge_fraction[index]:.6f}",
                    "raw_entropy": f"{trace.raw_entropy[index]:.6f}",
                }
            )


def write_benchmark_metadata(path: Path, trace: BenchmarkTrace, provenance: str) -> None:
    payload = {
        "source_name": trace.source_name,
        "provenance": provenance,
        "damage_time": trace.damage_time,
        "baseline_raw_entropy": trace.baseline_raw_entropy,
        "sample_count": len(trace.times),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_local_benchmark_trace(path: Path) -> BenchmarkTrace:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    data = {field: [float(row[field]) for row in rows] for field in trace_csv_fieldnames()}
    damage_signal = data["damage_signal"]
    damage_index = max(range(len(damage_signal)), key=damage_signal.__getitem__)
    raw_entropy = data["raw_entropy"]
    times = data["time"]
    baseline_entropy = fmean(
        value for time_value, value in zip(times, raw_entropy) if time_value < times[damage_index]
    )
    return BenchmarkTrace(
        source_name=path.name,
        times=times,
        psi=data["psi"],
        holonomy_cosine=data["holonomy_cosine"],
        signature_drive=data["signature_drive"],
        current_drive=data["current_drive"],
        phase=data["phase"],
        slip_signal=data["slip_signal"],
        damage_signal=data["damage_signal"],
        entropy_signal=data["entropy_signal"],
        pi_a=data["pi_a"],
        transfer=data["transfer"],
        boundary_fraction=data["boundary_fraction"],
        top_edge_fraction=data["top_edge_fraction"],
        raw_entropy=raw_entropy,
        damage_time=times[damage_index],
        baseline_raw_entropy=baseline_entropy,
    )


def ensure_vendored_benchmark_trace(repo_root: Path) -> BenchmarkTrace:
    local_csv = repo_root / "data" / "benchmark_forcing.csv"
    metadata_path = repo_root / "data" / "benchmark_forcing_metadata.json"
    external_source = source_trace_path(repo_root)
    if external_source.exists():
        rows = read_external_source_rows(external_source)
        trace = build_trace_from_source_rows(rows, external_source.name)
        write_benchmark_trace_csv(local_csv, trace)
        write_benchmark_metadata(metadata_path, trace, str(external_source.relative_to(repo_root.parent)))
        return trace
    if local_csv.exists():
        return load_local_benchmark_trace(local_csv)
    raise FileNotFoundError(
        f"No external source trace at {external_source} and no local benchmark trace at {local_csv}"
    )


def simulate_benchmark_trace(
    trace: BenchmarkTrace,
    config: ConductanceLawConfig,
    *,
    scenario_name: str,
) -> BenchmarkScenarioResult:
    conductance = 0j
    memory_value = 0.0
    times = trace.times
    magnitudes: list[float] = []
    memories: list[float] = []
    gains: list[float] = []
    phases: list[float] = []

    for index, time_value in enumerate(times):
        if index == 0:
            dt = config.dt
        else:
            dt = max(time_value - times[index - 1], 1e-9)
        entropy_value = trace.entropy_signal[index]
        alpha_value = alpha_g(entropy_value, config)
        mu_value = mu_g(entropy_value, config)
        gain = reinforcement_factor(trace.psi[index], memory_value, config.kappa_psi, config.xi)
        drive = complex(math.cos(trace.phase[index]), math.sin(trace.phase[index]))
        drive *= alpha_value * gain * trace.current_drive[index]
        conductance = conductance + dt * (drive - mu_value * conductance)
        memory_derivative = config.memory_gain * trace.slip_signal[index] - config.memory_decay * memory_value
        memory_value = max(0.0, memory_value + dt * memory_derivative)

        magnitudes.append(abs(conductance))
        memories.append(memory_value)
        gains.append(gain)
        phases.append(math.atan2(conductance.imag, conductance.real) if abs(conductance) > 1e-12 else trace.phase[index])

    return BenchmarkScenarioResult(
        name=scenario_name,
        config=config,
        trace_source=trace.source_name,
        times=times,
        psi=trace.psi,
        current_drive=trace.current_drive,
        slip_signal=trace.slip_signal,
        damage_signal=trace.damage_signal,
        entropy_signal=trace.entropy_signal,
        memory=memories,
        gain=gains,
        magnitude=magnitudes,
        phase=phases,
    )


def benchmark_windows(trace: BenchmarkTrace) -> tuple[tuple[float, float], tuple[float, float]]:
    remaining = max(trace.times[-1] - trace.damage_time, 1e-9)
    damage_window = (
        max(trace.times[0], trace.damage_time - 0.05 * remaining),
        min(trace.times[-1], trace.damage_time + 0.10 * remaining),
    )
    recovery_window = (
        min(trace.times[-1], trace.damage_time + 0.35 * remaining),
        min(trace.times[-1], trace.damage_time + 0.65 * remaining),
    )
    return damage_window, recovery_window


def summarize_benchmark_result(result: BenchmarkScenarioResult, trace: BenchmarkTrace) -> dict[str, float]:
    damage_window, recovery_window = benchmark_windows(trace)
    late_values = result.magnitude[max(1, len(result.magnitude) * 3 // 4) :]
    return {
        "min_psi": min(result.psi),
        "peak_memory": max(result.memory),
        "peak_magnitude": max(result.magnitude),
        "final_magnitude": result.magnitude[-1],
        "mean_gain": fmean(result.gain),
        "damage_window_mean_magnitude": window_average(
            result,
            damage_window[0],
            damage_window[1],
            result.magnitude,
        ),
        "recovery_window_mean_magnitude": window_average(
            result,
            recovery_window[0],
            recovery_window[1],
            result.magnitude,
        ),
        "late_time_magnitude_std": pstdev(late_values),
    }


def scenario_configurations() -> dict[str, ConductanceLawConfig]:
    return {
        "baseline_parent_law": ConductanceLawConfig(kappa_psi=0.0, xi=0.0),
        "loop_only": ConductanceLawConfig(kappa_psi=0.35, xi=0.0),
        "memory_only": ConductanceLawConfig(kappa_psi=0.0, xi=2.5),
        "loop_and_memory_stabilized": ConductanceLawConfig(kappa_psi=0.35, xi=2.5),
    }


def run_scenario_suite(trace: BenchmarkTrace) -> dict[str, BenchmarkScenarioResult]:
    return {
        name: simulate_benchmark_trace(trace, config, scenario_name=name)
        for name, config in scenario_configurations().items()
    }


def scenario_summary_payload(trace: BenchmarkTrace, results: dict[str, BenchmarkScenarioResult]) -> dict[str, object]:
    baseline_metrics = summarize_benchmark_result(results["baseline_parent_law"], trace)
    payload: dict[str, object] = {
        "trace": {
            "source_name": trace.source_name,
            "damage_time": trace.damage_time,
            "baseline_raw_entropy": trace.baseline_raw_entropy,
        },
        "scenarios": {},
        "comparisons_vs_baseline": {},
    }
    for name, result in results.items():
        metrics = summarize_benchmark_result(result, trace)
        payload["scenarios"][name] = {
            "config": asdict(result.config),
            "metrics": metrics,
        }
        if name != "baseline_parent_law":
            payload["comparisons_vs_baseline"][name] = {
                "damage_window_shift": metrics["damage_window_mean_magnitude"]
                - baseline_metrics["damage_window_mean_magnitude"],
                "recovery_window_shift": metrics["recovery_window_mean_magnitude"]
                - baseline_metrics["recovery_window_mean_magnitude"],
                "late_std_shift": metrics["late_time_magnitude_std"]
                - baseline_metrics["late_time_magnitude_std"],
                "peak_magnitude_shift": metrics["peak_magnitude"]
                - baseline_metrics["peak_magnitude"],
            }
    return payload


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


def write_scenario_svg(path: Path, trace: BenchmarkTrace, results: dict[str, BenchmarkScenarioResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 940
    height = 680
    panel_x = 80
    panel_width = 780
    top_y = 90
    mid_y = 340
    panel_height = 170
    damage_x = panel_x + (trace.damage_time / trace.times[-1]) * panel_width

    palette = {
        "baseline_parent_law": "#9a3412",
        "loop_only": "#1d4ed8",
        "memory_only": "#7c3aed",
        "loop_and_memory_stabilized": "#065f46",
    }

    magnitude_lines = "\n".join(
        [
            f'<polyline fill="none" stroke="{palette[name]}" stroke-width="2.4" points="{polyline_points(result.magnitude, panel_x, top_y, panel_width, panel_height)}"/>'
            for name, result in results.items()
        ]
    )
    drive_lines = "\n".join(
        [
            f'<polyline fill="none" stroke="#1d4ed8" stroke-width="2.2" points="{polyline_points(trace.psi, panel_x, mid_y, panel_width, panel_height)}"/>',
            f'<polyline fill="none" stroke="#b91c1c" stroke-width="2.0" points="{polyline_points(trace.damage_signal, panel_x, mid_y, panel_width, panel_height)}"/>',
            f'<polyline fill="none" stroke="#7c3aed" stroke-width="2.0" points="{polyline_points(trace.current_drive, panel_x, mid_y, panel_width, panel_height)}"/>',
        ]
    )

    legend_lines = []
    legend_y = 112
    for name, color in palette.items():
        legend_lines.append(
            f'<text x="650" y="{legend_y}" font-size="13" font-family="Georgia" fill="{color}">{name}</text>'
        )
        legend_y += 18

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Benchmark-driven loop-coherence and curve-memory scenario comparison</title>
  <desc id="desc">Four scenario comparison driven by the flat-channel loop-signature benchmark trace.</desc>
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="80" y="42" font-size="28" font-family="Georgia" fill="#0f172a">Benchmark-Driven Scenario Suite</text>
  <text x="80" y="66" font-size="14" font-family="Georgia" fill="#334155">Parent, loop-only, memory-only, and full stabilized laws under a vendored flat-channel forcing trace.</text>
  {axis_markup("Conductance magnitude", panel_x, top_y, panel_width, panel_height, damage_x)}
  {magnitude_lines}
  {' '.join(legend_lines)}
  {axis_markup("Psi, damage signal, and current drive", panel_x, mid_y, panel_width, panel_height, damage_x)}
  {drive_lines}
  <text x="650" y="362" font-size="13" font-family="Georgia" fill="#1d4ed8">psi</text>
  <text x="650" y="380" font-size="13" font-family="Georgia" fill="#b91c1c">damage signal</text>
  <text x="650" y="398" font-size="13" font-family="Georgia" fill="#7c3aed">current drive</text>
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def run_parameter_sweep(trace: BenchmarkTrace) -> list[SweepEntry]:
    baseline = simulate_benchmark_trace(trace, ConductanceLawConfig(kappa_psi=0.0, xi=0.0), scenario_name="baseline")
    baseline_metrics = summarize_benchmark_result(baseline, trace)
    kappa_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    xi_values = [0.0, 0.6, 1.2, 1.8, 2.4, 3.0]
    entries: list[SweepEntry] = []
    for kappa_value in kappa_values:
        for xi_value in xi_values:
            result = simulate_benchmark_trace(
                trace,
                ConductanceLawConfig(kappa_psi=kappa_value, xi=xi_value),
                scenario_name=f"kappa_{kappa_value:.1f}_xi_{xi_value:.1f}",
            )
            metrics = summarize_benchmark_result(result, trace)
            recovery_lift = (
                metrics["recovery_window_mean_magnitude"]
                - baseline_metrics["recovery_window_mean_magnitude"]
            )
            damage_shift = (
                metrics["damage_window_mean_magnitude"]
                - baseline_metrics["damage_window_mean_magnitude"]
            )
            late_std_shift = (
                metrics["late_time_magnitude_std"]
                - baseline_metrics["late_time_magnitude_std"]
            )
            score = recovery_lift - 0.40 * max(0.0, damage_shift) - 0.25 * late_std_shift
            entries.append(
                SweepEntry(
                    kappa_psi=kappa_value,
                    xi=xi_value,
                    score=score,
                    recovery_lift=recovery_lift,
                    damage_shift=damage_shift,
                    late_std_shift=late_std_shift,
                )
            )
    return entries


def write_sweep_csv(path: Path, entries: list[SweepEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["kappa_psi", "xi", "score", "recovery_lift", "damage_shift", "late_std_shift"],
        )
        writer.writeheader()
        for entry in entries:
            writer.writerow(asdict(entry))


def write_sweep_summary(path: Path, entries: list[SweepEntry]) -> None:
    ordered = sorted(entries, key=lambda entry: entry.score, reverse=True)
    payload = {
        "best": asdict(ordered[0]),
        "top_five": [asdict(entry) for entry in ordered[:5]],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def heatmap_color(value: float, minimum: float, maximum: float) -> str:
    if maximum <= minimum:
        normalized = 0.5
    else:
        normalized = (value - minimum) / (maximum - minimum)
    red = int(140 + 80 * (1.0 - normalized))
    green = int(80 + 130 * normalized)
    blue = int(60 + 100 * (1.0 - abs(normalized - 0.5) * 2.0))
    return f"#{red:02x}{green:02x}{blue:02x}"


def write_sweep_heatmap(path: Path, entries: list[SweepEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kappa_values = sorted({entry.kappa_psi for entry in entries})
    xi_values = sorted({entry.xi for entry in entries})
    cell_width = 100
    cell_height = 62
    origin_x = 140
    origin_y = 110
    values = [entry.score for entry in entries]
    minimum = min(values)
    maximum = max(values)
    by_key = {(entry.kappa_psi, entry.xi): entry for entry in entries}

    cell_markup: list[str] = []
    for row_index, xi_value in enumerate(xi_values):
        for column_index, kappa_value in enumerate(kappa_values):
            entry = by_key[(kappa_value, xi_value)]
            x_value = origin_x + column_index * cell_width
            y_value = origin_y + row_index * cell_height
            fill = heatmap_color(entry.score, minimum, maximum)
            cell_markup.append(
                "\n".join(
                    [
                        f'<rect x="{x_value}" y="{y_value}" width="{cell_width - 6}" height="{cell_height - 6}" rx="10" fill="{fill}"/>',
                        f'<text x="{x_value + 12}" y="{y_value + 24}" font-size="13" font-family="Georgia" fill="#f8fafc">score {entry.score:.3f}</text>',
                        f'<text x="{x_value + 12}" y="{y_value + 42}" font-size="11" font-family="Georgia" fill="#e5e7eb">rec {entry.recovery_lift:.3f} / dmg {entry.damage_shift:.3f}</text>',
                    ]
                )
            )

    header_markup = []
    for index, kappa_value in enumerate(kappa_values):
        header_markup.append(
            f'<text x="{origin_x + index * cell_width + 24}" y="88" font-size="14" font-family="Georgia" fill="#0f172a">k={kappa_value:.1f}</text>'
        )
    row_markup = []
    for index, xi_value in enumerate(xi_values):
        row_markup.append(
            f'<text x="74" y="{origin_y + index * cell_height + 30}" font-size="14" font-family="Georgia" fill="#0f172a">xi={xi_value:.1f}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="560" viewBox="0 0 820 560" role="img" aria-labelledby="title desc">
  <title id="title">Benchmark parameter sweep heatmap</title>
  <desc id="desc">Score heatmap over kappa_Psi and xi for the benchmark-driven simulation.</desc>
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="70" y="44" font-size="28" font-family="Georgia" fill="#0f172a">Benchmark Sweep</text>
  <text x="70" y="68" font-size="14" font-family="Georgia" fill="#334155">Score = recovery lift - 0.40 * positive damage overshoot - 0.25 * late-time variance shift.</text>
  {' '.join(header_markup)}
  {' '.join(row_markup)}
  {' '.join(cell_markup)}
</svg>
'''
    path.write_text(svg, encoding="utf-8")
