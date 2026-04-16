# Analytic Solution and Limit Cases

## Compact Form

Write the law as

$$
\frac{d\tilde G_{ij}}{dt}=F_{ij}(t)-\mu_G\bigl(S(t)\bigr)\tilde G_{ij}(t),
$$

with

$$
F_{ij}(t)=\alpha_G\bigl(S(t)\bigr)\frac{1+\kappa_{\Psi}\Psi(t)}{1+\xi M_{ij}(t)}\,|I_{ij}(t)|\,e^{i\theta_{R,ij}(t)}.
$$

This isolates the new ingredients cleanly:

- `Psi(t)` is a loop-level coherence gain.
- `M_ij(t)` is an edge-level chronic-slip memory.
- `alpha_G(S)` and `mu_G(S)` retain the entropy-gated parent dynamics.

## General Time-Dependent Solution

Using the integrating factor

$$
\mathcal I(t)=\exp\!\left(\int_0^t \mu_G\bigl(S(u)\bigr)\,du\right),
$$

the exact mild solution is

$$
\tilde G_{ij}(t)=e^{-\int_0^t \mu_G(S(u))\,du}\,\tilde G_{ij}(0)
+\int_0^t e^{-\int_{\tau}^t \mu_G(S(u))\,du}\,F_{ij}(\tau)\,d\tau.
$$

Two consequences are immediate.

1. Past forcing is exponentially forgotten at a rate controlled by `mu_G(S)`.
2. The new loop and memory terms only modify the source term `F_ij`; they do not alter the linear damping structure.

## Frozen-Coefficient Solution

If `S`, `Psi`, `M_ij`, `|I_ij|`, and `theta_R,ij` are approximately constant over a short window, then `F_ij` and `mu_G` are constant and the solution reduces to

$$
\tilde G_{ij}(t)=\tilde G_{ij}^{\ast}+\bigl(\tilde G_{ij}(0)-\tilde G_{ij}^{\ast}\bigr)e^{-\mu_G t},
$$

where the local steady state is

$$
\tilde G_{ij}^{\ast}=\frac{\alpha_G(S)}{\mu_G(S)}\frac{1+\kappa_{\Psi}\Psi}{1+\xi M_{ij}}|I_{ij}|e^{i\theta_{R,ij}}.
$$

This is the main closed-form "solution" for the law: in any quasi-static regime, the complex conductance aligns with the resolved phase and its magnitude is rescaled by the loop-coherence and curve-memory factor.

## Magnitude and Phase Separation

From the frozen steady state,

$$
|\tilde G_{ij}^{\ast}|=\frac{\alpha_G(S)}{\mu_G(S)}\frac{1+\kappa_{\Psi}\Psi}{1+\xi M_{ij}}|I_{ij}|,
\qquad
\arg\bigl(\tilde G_{ij}^{\ast}\bigr)=\theta_{R,ij}.
$$

So the new law changes the equilibrium magnitude, but it does not rotate the preferred phase away from the resolved-phase reference. The `M_ij` term is purely stabilizing in amplitude space.

## Exact Limit Recoveries

The law preserves the intended lineage exactly.

### Parent BZ Law

Setting `kappa_Psi = 0` and `xi = 0` gives

$$
\frac{d\tilde G_{ij}}{dt}=\alpha_G(S)|I_{ij}|e^{i\theta_{R,ij}}-\mu_G(S)\tilde G_{ij},
$$

which is the BZ-averaged phase-lifted parent law.

### Pure Loop-Coherence Gating

Setting `xi = 0` gives

$$
\frac{d\tilde G_{ij}}{dt}=\alpha_G(S)\bigl(1+\kappa_{\Psi}\Psi\bigr)|I_{ij}|e^{i\theta_{R,ij}}-\mu_G(S)\tilde G_{ij}.
$$

The only modification is the loop-consistency gain.

### Pure Curve-Memory Stabilization

Setting `kappa_Psi = 0` gives

$$
\frac{d\tilde G_{ij}}{dt}=\alpha_G(S)\frac{|I_{ij}|e^{i\theta_{R,ij}}}{1+\xi M_{ij}}-\mu_G(S)\tilde G_{ij}.
$$

The loop term vanishes and only chronic-slip attenuation remains.

## Interpretation

The law is best viewed as a linear stable filter with a structured source term:

- `Psi` rewards loop-consistent forcing.
- `M_ij` penalizes edges that have accumulated unresolved slip stress.
- `mu_G(S)` still guarantees exponential forgetting whenever entropy gating stays strictly dissipative.

That separation is what makes the equation analytically manageable and numerically easy to test.
