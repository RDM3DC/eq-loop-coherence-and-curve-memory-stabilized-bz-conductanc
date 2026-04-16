# Consistency and Stability Notes

## Operating Regime

For the statements below, assume:

- `Psi(t) in [-1, 1]`.
- `M_ij(t) >= 0`.
- `xi >= 0`.
- `0 <= kappa_Psi <= 1`, which is a sufficient condition for `1 + kappa_Psi Psi >= 0` across the full admissible `Psi` range.
- `alpha_G(S) >= 0` and `mu_G(S) >= mu_0 > 0` on the entropy window of interest.

The last two conditions are the same dissipative assumptions already needed by the parent BZ law.

## Proposition 1: Exact Lineage Recovery

The law recovers each intended ancestor exactly.

### Proof

Substitute the required parameter choices directly into

$$
\frac{d\tilde G_{ij}}{dt}=\alpha_G(S)\frac{1+\kappa_{\Psi}\Psi}{1+\xi M_{ij}}|I_{ij}|e^{i\theta_{R,ij}}-\mu_G(S)\tilde G_{ij}.
$$

- `kappa_Psi = 0`, `xi = 0` gives the parent BZ law.
- `xi = 0` gives pure loop-coherence gating.
- `kappa_Psi = 0` gives pure curve-memory attenuation.

No approximation is used. The reduction is algebraically exact.

## Proposition 2: Monotonicity of the Reinforcement Prefactor

Define the dimensionless reinforcement amplitude

$$
R(\Psi,M)=\frac{1+\kappa_{\Psi}\Psi}{1+\xi M}.
$$

Then, in the operating regime above,

$$
\frac{\partial R}{\partial \Psi}=\frac{\kappa_{\Psi}}{1+\xi M}\ge 0,
\qquad
\frac{\partial R}{\partial M}=-\frac{\xi(1+\kappa_{\Psi}\Psi)}{(1+\xi M)^2}\le 0.
$$

### Interpretation

- Higher loop coherence can only increase the source amplitude.
- Larger accumulated memory can only suppress it.

So the new terms do exactly what the narrative claims: they favor loop-consistent edges and damp chronically slipping ones.

## Proposition 3: Uniform Boundedness Under Bounded Forcing

Suppose there is a constant `B > 0` such that

$$
\alpha_G\bigl(S(t)\bigr)|I_{ij}(t)| \le B
$$

for all relevant `t`. Then every solution satisfies

$$
|\tilde G_{ij}(t)|
\le |\tilde G_{ij}(0)|e^{-\mu_0 t}
+\frac{(1+\kappa_{\Psi})B}{\mu_0}\bigl(1-e^{-\mu_0 t}\bigr).
$$

### Proof Sketch

Because `M_ij >= 0`, the denominator obeys `1 + xi M_ij >= 1`. Because `Psi <= 1`, the numerator obeys `1 + kappa_Psi Psi <= 1 + kappa_Psi`. Hence

$$
|F_{ij}(t)|
\le (1+\kappa_{\Psi})B.
$$

Apply the variation-of-constants formula and use `mu_G(S(t)) >= mu_0` inside the exponential kernel. The bound follows from the scalar inequality for a stable linear ODE with bounded forcing.

## Proposition 4: Steady-State Phase Alignment

In any frozen-coefficient window with positive forcing amplitude,

$$
\arg\bigl(\tilde G_{ij}^{\ast}\bigr)=\theta_{R,ij}.
$$

### Proof

The prefactor

$$
\frac{\alpha_G(S)}{\mu_G(S)}\frac{1+\kappa_{\Psi}\Psi}{1+\xi M_{ij}}|I_{ij}|
$$

is real and nonnegative in the operating regime, so it changes only the modulus of the complex exponential `e^{i theta_R,ij}`.

## What Is Actually Proved Here

These notes do not prove that a full adaptive lattice with feedback into `Psi` and `M_ij` is globally asymptotically stable. They prove the more modest and useful facts needed for a standalone equation repo:

- the law is algebraically lineage-consistent,
- the new gate is monotone in the intended directions,
- bounded inputs stay bounded under positive damping,
- and the quasi-static solution has a closed form.

Those are the right proofs to include before moving on to larger network-level experiments.
