from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from statistics import fmean, pstdev


@dataclass(frozen=True)
class ConductanceLawConfig:
    dt: float = 0.05
    total_time: float = 20.0
    pi_a: float = 1.0
    alpha_0: float = 1.15
    mu_0: float = 0.72
    entropy_target: float = 0.42
    entropy_sensitivity: float = 0.65
    damping_sensitivity: float = 0.80
    kappa_psi: float = 0.35
    xi: float = 2.50
    memory_gain: float = 1.75
    memory_decay: float = 1.35
    damage_center: float = 8.0
    damage_width: float = 1.30
    slip_phase_amplitude: float = 1.80
    edge_orientations: tuple[int, ...] = (1, 1, -1, -1)
    base_currents: tuple[float, ...] = (1.00, 1.08, 0.96, 1.04)
    base_phases: tuple[float, ...] = (0.08, 0.18, -0.05, 0.02)

    def __post_init__(self) -> None:
        edge_count = len(self.base_currents)
        if edge_count == 0:
            raise ValueError("base_currents must not be empty")
        if len(self.base_phases) != edge_count or len(self.edge_orientations) != edge_count:
            raise ValueError("currents, phases, and orientations must have the same length")
        if self.dt <= 0.0 or self.total_time <= 0.0:
            raise ValueError("dt and total_time must be positive")
        if self.pi_a <= 0.0:
            raise ValueError("pi_a must be positive")
        if self.mu_0 <= 0.0 or self.memory_decay <= 0.0:
            raise ValueError("mu_0 and memory_decay must be positive")
        if self.kappa_psi < 0.0 or self.xi < 0.0:
            raise ValueError("kappa_psi and xi must be nonnegative")
        if self.kappa_psi > 1.0:
            raise ValueError(
                "kappa_psi must be <= 1.0 in the reference model so 1 + kappa_psi * Psi stays nonnegative for Psi in [-1, 1]"
            )


@dataclass
class SimulationResult:
    config: ConductanceLawConfig
    times: list[float]
    loop_coherence: list[float]
    holonomy: list[float]
    entropy: list[float]
    mean_memory: list[float]
    mean_gain: list[float]
    mean_magnitude: list[float]
    max_magnitude: list[float]
    slip_energy: list[float]


def gaussian_pulse(time_value: float, center: float, width: float) -> float:
    normalized_distance = (time_value - center) / max(width, 1e-9)
    return math.exp(-(normalized_distance * normalized_distance))


def wrapped_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def loop_coherence_from_holonomy(holonomy: float, pi_a: float) -> float:
    if pi_a <= 0.0:
        raise ValueError("pi_a must be positive")
    return math.cos(holonomy / pi_a)


def reinforcement_factor(psi: float, memory_value: float, kappa_psi: float, xi: float) -> float:
    if memory_value < 0.0:
        raise ValueError("memory_value must be nonnegative")
    if kappa_psi < 0.0 or xi < 0.0:
        raise ValueError("kappa_psi and xi must be nonnegative")
    denominator = 1.0 + xi * memory_value
    if denominator <= 0.0:
        raise ValueError("reinforcement denominator must stay positive")
    return (1.0 + kappa_psi * psi) / denominator


def alpha_g(entropy: float, config: ConductanceLawConfig) -> float:
    entropy_excess = max(0.0, entropy - config.entropy_target)
    return config.alpha_0 / (1.0 + config.entropy_sensitivity * entropy_excess)


def mu_g(entropy: float, config: ConductanceLawConfig) -> float:
    entropy_offset = abs(entropy - config.entropy_target)
    return config.mu_0 * (1.0 + config.damping_sensitivity * entropy_offset)


def steady_state_conductance(
    *,
    alpha_value: float,
    mu_value: float,
    current_magnitude: float,
    phase: float,
    psi: float,
    memory_value: float,
    kappa_psi: float,
    xi: float,
) -> complex:
    if mu_value <= 0.0:
        raise ValueError("mu_value must be positive")
    drive_magnitude = alpha_value * reinforcement_factor(psi, memory_value, kappa_psi, xi) * current_magnitude
    return cmath.rect(drive_magnitude / mu_value, phase)


def entropy_profile(time_value: float, config: ConductanceLawConfig) -> float:
    damage = gaussian_pulse(time_value, config.damage_center, config.damage_width)
    oscillation = 0.045 * math.sin(0.42 * time_value)
    return config.entropy_target + oscillation + 0.14 * damage


def current_profile(time_value: float, config: ConductanceLawConfig) -> list[float]:
    damage = gaussian_pulse(time_value, config.damage_center, config.damage_width)
    magnitudes: list[float] = []
    for index, base_current in enumerate(config.base_currents):
        ripple = 1.0 + 0.05 * math.sin(0.55 * time_value + 0.7 * index)
        damage_drop = 1.0 - 0.33 * damage + 0.04 * damage * index
        magnitudes.append(max(0.08, base_current * ripple * damage_drop))
    return magnitudes


def phase_profile(time_value: float, config: ConductanceLawConfig) -> list[float]:
    damage = gaussian_pulse(time_value, config.damage_center, config.damage_width)
    phases: list[float] = []
    for index, base_phase in enumerate(config.base_phases):
        drift = 0.12 * math.sin(0.47 * time_value + 0.55 * index)
        if index == 1:
            slip_burst = config.slip_phase_amplitude * damage
        elif index == 2:
            slip_burst = 0.55 * config.slip_phase_amplitude * damage
        else:
            slip_burst = -0.10 * config.slip_phase_amplitude * damage if index == 3 else 0.0
        phases.append(base_phase + drift + slip_burst)
    return phases


def holonomy_from_phases(phases: list[float], orientations: tuple[int, ...]) -> float:
    return sum(orientation * phase for orientation, phase in zip(orientations, phases))


def slip_energy_from_phase_step(
    current_phases: list[float],
    previous_phases: list[float],
    current_holonomy: float,
    previous_holonomy: float,
    pi_a: float,
    dt: float,
) -> list[float]:
    holonomy_rate = abs(wrapped_angle(current_holonomy - previous_holonomy)) / (pi_a * max(dt, 1e-9))
    edge_energies: list[float] = []
    for current_phase, previous_phase in zip(current_phases, previous_phases):
        local_rate = abs(wrapped_angle(current_phase - previous_phase)) / (pi_a * max(dt, 1e-9))
        edge_energies.append(local_rate * local_rate + 0.35 * holonomy_rate * holonomy_rate)
    return edge_energies


def simulate_reference_scenario(config: ConductanceLawConfig) -> SimulationResult:
    step_count = int(round(config.total_time / config.dt))
    conductances = [0j for _ in config.base_currents]
    memories = [0.0 for _ in config.base_currents]
    previous_phases = phase_profile(0.0, config)
    previous_holonomy = holonomy_from_phases(previous_phases, config.edge_orientations)

    times: list[float] = []
    loop_coherence: list[float] = []
    holonomy: list[float] = []
    entropy: list[float] = []
    mean_memory: list[float] = []
    mean_gain: list[float] = []
    mean_magnitude: list[float] = []
    max_magnitude: list[float] = []
    slip_energy: list[float] = []

    for step_index in range(step_count + 1):
        time_value = step_index * config.dt
        current_phases = phase_profile(time_value, config)
        current_holonomy = holonomy_from_phases(current_phases, config.edge_orientations)
        psi = loop_coherence_from_holonomy(current_holonomy, config.pi_a)
        current_entropy = entropy_profile(time_value, config)
        currents = current_profile(time_value, config)
        alpha_value = alpha_g(current_entropy, config)
        mu_value = mu_g(current_entropy, config)

        gains: list[float] = []
        updated_conductances: list[complex] = []
        for current_magnitude, current_phase, conductance, memory_value in zip(
            currents, current_phases, conductances, memories
        ):
            gain = reinforcement_factor(psi, memory_value, config.kappa_psi, config.xi)
            drive = cmath.rect(alpha_value * gain * current_magnitude, current_phase)
            updated_conductances.append(conductance + config.dt * (drive - mu_value * conductance))
            gains.append(gain)

        edge_slip = slip_energy_from_phase_step(
            current_phases,
            previous_phases,
            current_holonomy,
            previous_holonomy,
            config.pi_a,
            config.dt,
        )
        updated_memories: list[float] = []
        for memory_value, slip_value in zip(memories, edge_slip):
            derivative = config.memory_gain * slip_value - config.memory_decay * memory_value
            updated_memories.append(max(0.0, memory_value + config.dt * derivative))

        conductances = updated_conductances
        memories = updated_memories
        previous_phases = current_phases
        previous_holonomy = current_holonomy

        times.append(time_value)
        holonomy.append(current_holonomy)
        loop_coherence.append(psi)
        entropy.append(current_entropy)
        mean_memory.append(fmean(memories))
        mean_gain.append(fmean(gains))
        mean_magnitude.append(fmean(abs(value) for value in conductances))
        max_magnitude.append(max(abs(value) for value in conductances))
        slip_energy.append(fmean(edge_slip))

    return SimulationResult(
        config=config,
        times=times,
        loop_coherence=loop_coherence,
        holonomy=holonomy,
        entropy=entropy,
        mean_memory=mean_memory,
        mean_gain=mean_gain,
        mean_magnitude=mean_magnitude,
        max_magnitude=max_magnitude,
        slip_energy=slip_energy,
    )


def window_average(result: SimulationResult, start_time: float, end_time: float, values: list[float]) -> float:
    selected = [value for time_value, value in zip(result.times, values) if start_time <= time_value <= end_time]
    return fmean(selected) if selected else values[-1]


def summarize_result(result: SimulationResult) -> dict[str, float]:
    center = result.config.damage_center
    width = result.config.damage_width
    late_values = result.mean_magnitude[max(1, len(result.mean_magnitude) * 3 // 4) :]
    return {
        "min_loop_coherence": min(result.loop_coherence),
        "mean_loop_coherence": fmean(result.loop_coherence),
        "peak_mean_magnitude": max(result.mean_magnitude),
        "final_mean_magnitude": result.mean_magnitude[-1],
        "peak_memory": max(result.mean_memory),
        "mean_gain": fmean(result.mean_gain),
        "damage_window_mean_magnitude": window_average(
            result,
            center - width,
            center + width,
            result.mean_magnitude,
        ),
        "recovery_window_mean_magnitude": window_average(
            result,
            center + 3.0 * width,
            center + 5.0 * width,
            result.mean_magnitude,
        ),
        "late_time_magnitude_std": pstdev(late_values),
    }
