# F-029 Isothermal Diagnostic — Section 6B

**Folder:** `06_Fluent_CFD/Diagnostics/F029_Isothermal/`
**Date:** 2026-09-24 · ANSYS Fluent 2026 R1 (v261), `3ddp -g -py -t4`, batch
**RE-ANALYSIS 2026 — a newly generated diagnostic run, not a recovered original. No measured data exists or is used.**
**Label: DIAGNOSTIC (not part of the mesh study, not a design case)**

## 1. Why this run exists

F-029: the fully developed Darcy friction factor from the heated CFD (medium mesh, 0.02163) is
10.4 % below the Section 2 value (0.02413). The Section 6B brief asks whether this is mesh,
turbulence model, polygon geometry, entrance effects or correlation limits, and says not to blame
the mesh automatically. The three-mesh study measures the mesh part. It cannot separate the
turbulence model from the effect of heating, because every heated run has both. This run removes
the heating: **same case, same medium mesh, energy equation switched off**. Whatever friction
deficit remains in isothermal flow belongs to the turbulence model, the mesh and flow development,
not to the variable-property heating effect.

## 2. What was run

| Item | Value |
|---|---|
| Case | `../../Case/baseline_medium_final.cas.h5`, **settings only** (data not read) |
| Mesh | medium, 159,840 cells (unchanged) |
| **Only change** | energy equation **not solved** at any iteration; the whole domain stays at 300 K |
| Air | incompressible ideal gas at 300 K → ρ = 1.176655 kg/m³; μ(300 K) = 1.846 × 10⁻⁵ Pa·s (same table) |
| Inlet / outlet / turbulence / numerics | 23.5 m/s, I = 4.411 %, 0 Pa; k-ω SST `correlation`; Coupled, pseudo-time; first order 150 iterations, then second order |
| Pre-solve audit | 9 items read back (model, wall treatment, inlet velocity, temperature and intensity, outlet pressure, equations solved, p-v coupling, startup scheme): **9 / 9** (`Audit/iso_setup_audit.json`) |
| Convergence | residuals < 1e-4; over a 200-iteration second-order window, Δp and wall-force drift < 0.1 %, ṁ_out drift < 0.01 %, mass imbalance < 0.01 %; then 100 confirmation iterations |
| Result | 350: refused (Δp drift 0.25 %, wall force 0.63 %) · **450: converged** · **550: confirmed**. Final residuals: continuity 6.6 × 10⁻¹², momentum ≤ 2.7 × 10⁻¹⁷, k 2.5 × 10⁻¹⁶, ω 1.6 × 10⁻¹⁶ |
| Wall clock | 16 min 52 s (01:00:17 → 01:17:09) |
| Post-processing | `Journals/iso_post.py`: slab-averaged axial wall shear → f = 8τ_wρ/G², window mean over x/D 18–29 by linear interpolation (the definition used in the three-mesh study) |

Fluent printed "connection reset" and "an error or interrupt occurred while reading the journal"
**after** the journal's final `exit()`; every step before it, including all writes and exports,
logged OK (`Logs/iso_log.txt`, `ISO-DONE` in `Logs/iso_stdout.txt`). It is the shutdown of the
Python journal, not a failure of the run.

## 3. Results (`iso_results.json`, `iso_f_profile.csv`, `Figures/iso_friction_factor.png`)

| Quantity | Isothermal (medium) | Heated baseline (medium) |
|---|---|---|
| Mass flow | 8.66216 g/s | 8.66216 g/s |
| Re (D = 20 mm) | 29 958 everywhere | 29 958 → 25 545; 26 346 averaged over the window |
| Static Δp, inlet − outlet | 258.08 Pa | 438.13 Pa (includes 149 Pa of acceleration) |
| Axial wall force | 0.07305 N | 0.07608 N |
| y⁺ mean / max | 0.462 / 0.850 | 0.241 / 0.585 |
| **f, window x/D 18–29** | **0.023039** | **0.021626** |
| Local f at x/D 18 → 29 | 0.022736 → 0.023402 (**+2.9 %**) | 0.021243 → 0.022055 (+3.8 %; Re falls and T_w/T_b changes along the window) |
| Petukhov at the run's Re | 0.023647 (Re 29 958) → CFD **−2.57 %** | 0.024403 (Re 26 346) → CFD −11.38 % |
| Blasius at Re 29 958 | 0.024019 → CFD −4.08 % | — |
| T_w/T_b over the window | 1 | 1.548 |

(Heated local f at x/D 18 and 29 are from the medium slab profile.)

## 4. What it shows

**(a) In isothermal flow, SST on the medium mesh is 2.6 % below Petukhov**, not 10 %.
That 2.6 % is within the combined size of the two effects measured separately:
- the mesh: the heated three-mesh study puts the medium f 2.2 % below its Richardson limit (the limit is 2.3 % above it); applying
  the same factor, the isothermal f would be 0.4 % below Petukhov;
- flow development: at constant Re the isothermal f still rises 2.9 % across x/D 18–29 and is still
  rising at the outlet. The window mean is 1.6 % below its own x/D 29 value. The window is not
  fully developed.

There is therefore **no evidence of a material SST friction deficit in isothermal pipe flow** at
this Reynolds number, within about ±2 %.

**(b) Heating is the largest part of F-029.** At the same mesh and definitions, the heated f is
0.9387 × the isothermal f. A constant-property correlation predicts × 1.0320 for the lower window
Re alone. The heating effect in the CFD is therefore **0.9096 (−9.0 %)**, at T_w/T_b = 1.548. The
Petukhov correction for gas heating used in Section 5B, (T_w/T_b)^−0.1, gives 0.9573 (−4.3 %). The
CFD's response corresponds to an exponent of **m ≈ −0.22** instead of −0.1. The Section 2 value
(0.02413) is a constant-property Petukhov value with no heating correction, so it cannot contain
this effect.

**(c) Decomposition of the medium-mesh gap** (`09_Mesh_Independence/Comparison_Tables/f029_decomposition.csv`, multiplicative, exact):

| Factor | Value | % |
|---|---|---|
| Reynolds-number basis: Petukhov at the heated window Re / Section 2 value | 1.0112 | +1.1 |
| Isothermal SST on the medium mesh / Petukhov (includes mesh and development) | 0.9743 | −2.6 |
| Heating effect in the CFD, beyond the constant-property Re change | 0.9096 | −9.0 |
| **Product = medium f / Section 2 f** | **0.8961** | **−10.4** |

In logarithmic shares of the gap: heating about 86 %, the isothermal factor about 24 %, and the Re
basis −10 % (it works the other way).

## 5. Limits of this diagnostic

- Only the medium mesh was run isothermal. Transferring the heated study's mesh factor (+2.3 %) to
  the isothermal flow is an assumption, although both flows share the mesh and the near-wall
  resolution (isothermal y⁺ ≤ 0.85).
- "Heating effect" here is everything that differs between the two runs: property variation near
  the wall, flow acceleration, and a heated flow that develops differently. It is a CFD result, not
  a measurement. Whether real air under this heating loses 9 % or 4 % of its friction cannot be
  settled without data. That residual (≈ 5 points) is recorded as a model/correlation uncertainty.
- The inlet is a uniform velocity with I = 4.411 % (A-020), so development in the window depends on
  that assumed inlet state.
