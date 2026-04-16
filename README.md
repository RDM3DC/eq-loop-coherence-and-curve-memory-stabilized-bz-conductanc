# Loop-Coherence and Curve-Memory Stabilized BZ Conductance Law

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

Lineage-preserving extension of the current BZ-averaged phase-lifted complex conductance update. It inserts a bounded loop-coherence gain through Psi and a chronic-slip curve-memory stabilizer through M_ij, so reinforcement is strongest on edges that are simultaneously active, loop-consistent, and not carrying accumulated topological stress. It recovers the current #1 law exactly when kappa_Psi=0 and xi=0, recovers pure loop-coherence gating when xi=0, and recovers pure curve-memory stabilization when kappa_Psi=0.

## Assumptions

- Psi=(1/N_p) sum_p cos(Theta_p/pi_a) is dimensionless and bounded on the monitored plaquette family.
- M_ij(t) is a nonnegative curve-memory stress integral or discrete exponential moving average built from resolved-phase slip energy.
- xi >= 0 and kappa_Psi >= 0 so the reinforcement prefactor remains nonnegative and reduces smoothly to known limits.
- alpha_G(S) and mu_G(S) retain the units and entropy gating of the current BZ law.

## Repository Structure

```
images/       # Visualizations, plots, diagrams
derivations/  # Step-by-step derivations and proofs
simulations/  # Computational models and code
data/         # Numerical data, experimental results
notes/        # Research notes and references
```

## Links

- [TopEquations Leaderboard](https://rdm3dc.github.io/TopEquations/leaderboard.html)
- [TopEquations Main Repo](https://github.com/RDM3DC/TopEquations)
- [Certificates](https://rdm3dc.github.io/TopEquations/certificates.html)

---
*Part of the [TopEquations](https://github.com/RDM3DC/TopEquations) project.*
