# Section 8A: independent hand buckling estimate for LC2

> **RE-ANALYSIS 2026.** This is a new hand calculation for the re-analysed duct.
>
> - **Inputs:** the frozen geometry, the datasheet tables already used by the solver in 7A/7B, and the reaction forces and nodal temperatures of the solved 7B LC2 model.
> - Nothing here is a recovered internship value, and nothing is a measurement.
> - **Script:** `Buckling/buckling_calculations.py` → `buckling_hand_results.json`. Every number below comes from that run.
> - These are hand estimates, not finite-element results. The FE linear buckling is in `BUCKLING_RESULTS.md`.

## 1. Applied load: what is the "load"?

Three different quantities describe LC2, and only the first is a column load.

| Quantity | Value | Source | Role |
|---|---|---|---|
| **Axial force N** (end reaction) | **548,936.6 N** (compression) | Inlet face +548,936.61 N and outlet face −548,936.61 N, summed over the 612 constrained nodes of each face in `LC2_Restrained/Solver_Output/s7b_react.csv`; they balance to 1.8 × 10⁻⁸ N | **Buckling load basis.** Constant along the duct (7B §4.3) |
| Mean axial stress N/A | **−582.44 MPa** | N / A, with A = 942.48 mm² | Used for stress-based column formulas (Euler/Johnson stress) |
| Local von Mises peak | 605.16 MPa | outer edge of the inlet face (7B) | **Not a column load.** A local combined stress, raised by the entrance-region through-wall gradient; it matters for yield, not for global stability |

**The load is thermal and displacement-controlled.** N is not an applied external force. It comes from the prevented thermal expansion, N ≈ Ē·A·ε̄_th.

- A load factor LF therefore means "LF times the present restrained thermal strain".
- It does **not** mean an external force that keeps pushing after the member deflects.
- This matters for how instability would show itself; see §7.

## 2. Section properties (annulus, D_o 40 mm, D_i 20 mm, L 600 mm)

| Property | Formula | Value |
|---|---|---|
| Area A | π/4 (D_o² − D_i²) | 9.4248 × 10⁻⁴ m² (942.48 mm²) |
| Second moment I | π/64 (D_o⁴ − D_i⁴) | 1.17810 × 10⁻⁷ m⁴ (117,810 mm⁴) |
| Radius of gyration r | √(I/A) = √(D_o² + D_i²)/4 | **11.180 mm** |
| L/r | | **53.67** |
| L/D_o, D_o/t, R_mean/t | | 15, 4.0, 1.5 |

## 3. Elastic modulus: which E?

**The table.** E(T) is interpolated linearly in the same datasheet table the solver uses: 204/199/193/187/180 GPa at 20/100/200/300/400 °C. The mapped field (150.7–289.4 °C) lies inside the table, so no extrapolation is needed.

| Basis | E [GPa] | Why |
|---|---|---|
| Hot end (562.56 K, the lowest E) | 187.64 | a conservative single value |
| Cold end (423.84 K) | 195.96 | an upper single value |
| Volume mean | 189.86 | a representative single value |
| Section bending modulus E_b(z) = ∫E y² dA / I | 195.30 (inlet) → 187.76 (outlet) | computed from the actual nodal temperatures of each of the 261 node planes |
| **Rayleigh mode-weighted E** (primary) | 189.4–190.3, depending on the end condition (table §4) | P_R = ∫E_b(z) I w″² dz / ∫w′² dz with the exact constant-EI mode shape w of each end condition. It weights E where the mode bends most |

**Why the choice hardly matters.** The E spread is only ±2 %, so the modulus choice moves the answer by ±2 % at most.

- The guided and fixed-fixed modes bend most at the ends, one cold and one hot, so their E_eff is close to the mean.
- The pinned mode bends most at mid-span.

## 4. Euler estimates for plausible end conditions

**Which end condition the LC2 model imposes.** U_z = 0 on both *complete* end faces keeps each end plane plane and perpendicular to the axis, so the ends cannot rotate. Radial (in-plane) motion is free, so each end can also translate laterally. The three mid-span hoop nodes only remove the lateral rigid-body motion. They do not stop the section from rotating, and the sway mode has zero lateral deflection at mid-span anyway (verified in the benchmark, `BUCKLING_AUDIT.md` §3).

So the LC2 idealisation is the **guided column (ends fixed against rotation, free to sway), K = 1**. No real end condition is claimed to be exact; the table establishes the range.

**Formulas.**

- Euler: P_E = π² E_eff I / (K L)².
- Shear-corrected (Engesser): P_E / (1 + P_E/(k G A)), with the Cowper shear coefficient k = 0.620 for this hollow section and G = E/2(1+ν).
- Load factor LF = P_cr / N, with N = 548,936.6 N.

| End condition | K (theory) | KL [mm] | **KL/r** | E_eff [GPa] | P_E [kN] | σ_E [MPa] | **LF Euler** | LF Euler + shear | LF Euler, hot-end E |
|---|---|---|---|---|---|---|---|---|---|
| **Guided: rotation fixed, sway free (= LC2 FE supports)** | 1.0 | 600 | **53.67** | 190.25 | 614.5 | 652.0 | **1.119** | **1.104** | 1.104 |
| Pinned–pinned (held laterally, free to rotate) | 1.0 | 600 | 53.67 | 189.38 | 611.6 | 649.0 | 1.114 | 1.099 | 1.104 |
| Fixed–pinned, cold (inlet) end fixed | 0.699 | 419.5 | 37.52 | 189.93 | 1254.8 | 1331.3 | 2.286 | 2.221 | 2.258 |
| Fixed–pinned, hot (outlet) end fixed | 0.699 | 419.5 | 37.52 | 189.62 | 1252.7 | 1329.2 | 2.282 | 2.217 | 2.258 |
| Fixed–fixed, no sway (rigid flanges) | 0.5 | 300 | 26.83 | 189.98 | 2454.4 | 2604.2 | 4.471 | 4.229 | 4.416 |

**Imperfect fixity (information only).** Design practice uses larger K for real, imperfect clamps: 1.2 guided, 1.0 pinned, 0.8 fixed–pinned, 0.65 fixed–fixed (AISC 360 Commentary, Table C-A-7.1). With these, the Euler load factors become 0.78 / 1.11 / 1.75 / 2.65. These are shown to illustrate the sensitivity to end fixity; they are not claimed to be the real K.

## 5. Is Euler theory appropriate here?

**Not fully.** It is a first estimate and an upper bound on the elastic value, for three reasons.

1. **Intermediate slenderness.**
   - The transition slenderness is C_c = √(2π² E / S_y) = 60.2 (hot-end E 187.64 GPa, S_y 1022.1 MPa).
   - Every case lies below it: KL/r = 26.8–53.7. These are intermediate (inelastic-range) columns, not long elastic ones.
   - Even the most slender cases have σ_E ≈ 650 MPa. That is above the conventional proportional limit S_y/2 ≈ 511 MPa, although below S_y.
2. **The real inelastic answer needs the material's tangent modulus.** That requires a stress–strain curve for age-hardened Inconel 718 at 150–290 °C, which is **not part of the project's material data**.
   - The **Johnson parabola** σ_cr = S_y − (S_y²/4π²E)(KL/r)² is therefore given as a *conventional* inelastic estimate. It is not a material-specific result.
3. **Short, thick member.**
   - L/D = 15 and the wall is thick (R/t = 1.5), so shear deformation matters.
   - The Engesser correction lowers P_cr by 1.4 % (K = 1) to 5.4 % (K = 0.5).
   - The FE benchmark (`BUCKLING_AUDIT.md` §3) lands between the plain and the shear-corrected Euler values.
   - The thick wall does *not* invalidate beam theory for the global mode: the section does not distort. The benchmark modes are 99.999 % rigid-section motion.

| End condition | Johnson σ_cr [MPa] (hot-end S_y, E) | **LF Johnson** | Johnson with volume-mean S_y, E |
|---|---|---|---|
| Guided (LC2 supports) / pinned–pinned | 615.9 | **1.058** | 1.068 |
| Fixed–pinned | 823.5 | 1.414 | 1.426 |
| Fixed–fixed | 920.6 | 1.581 | 1.593 |
| Squash load S_y·A, the first-yield ceiling of any column mode | 1022.1 | 1.755 | — |

**Reference: first yield in 7B.** LC2 reaches first yield at a load factor of about 1/0.578 = **1.73** at the inlet edge (1/0.575 = 1.74 in the hot interior). This assumes the whole stress state scales together.

For the guided and pinned conditions, every column estimate (1.06–1.12) is **well below** this first-yield factor. **For those end conditions, instability, not yield, governs.**

## 6. Local / shell buckling

A shell-buckling treatment is **not warranted**, and no shell-buckling load is claimed.

| Check | Value | Conclusion |
|---|---|---|
| Wall slenderness | R_mean/t = 1.5; D_o/t = 4 | a thick-walled tube, not a shell |
| Classical thin-shell axial buckling σ_cl = E t / (R √(3(1−ν²))) | 75,600 MPa | **Formula outside its validity** (thin-shell theory needs R/t ≳ 10). Shown only to show the order of magnitude: 74 × S_y |
| Compactness, AISC round HSS in compression: D/t < 0.11 E/F_y | 4.0 < 20.2 | compact: local buckling does not govern; the wall yields first |
| Ovalisation (Brazier) | — | a bending instability of thin tubes (D/t ≫ 20); not relevant at D/t = 4 |
| Circumferential instability | — | needs external pressure or hoop compression. The only pressure is +443 Pa internal, which is stabilising, and the hoop stresses are small |
| End effects | — | the hand theory cannot resolve them. The FE eigen-analysis would reveal any local end mode among its lowest modes |

## 7. Interpretation of the hand estimates

**LC2 supports as modelled (guided, sway free).** These are the governing case.

- Elastic Euler: LF ≈ 1.10–1.12.
- Johnson inelastic estimate: LF ≈ 1.06.
- All three are barely above 1.

**What that means in temperature.** The restrained force is proportional to the integrated thermal strain, so an LF of about 1.10 corresponds to about 10 % more restrained thermal strain. That is roughly a 23 K higher mean temperature rise than the present 225.5 K (about 13 K on the Johnson estimate). This is approximate, because E(T) and α(T) are not constant.

**Compared with the Section 2 temperature basis.** Section 2 assumed a 254.7 K mean rise, 1.129 times the CFD value. On that basis these load factors would already fall **below 1**: 1.104/1.129 = 0.98 (Euler + shear) and 0.94 (Johnson).

**Ends held laterally.**

- **Pinned–pinned:** no better than the guided case, because the same K = 1 applies.
- **Clamped, no sway (fixed–fixed):** the elastic LF rises to about 4.2–4.5. The member then becomes a stocky column whose capacity is set by inelastic behaviour: Johnson 1.58, close to the squash limit of 1.755.

**How a thermal restraint buckles.** Because the load is displacement-controlled, instability would appear as lateral bowing that relieves part of the axial force. It would not be a sudden collapse under a sustained external load. The bowing adds bending stress on top of the 582 MPa compression, so it would bring yield forward.

**Why a factor this close to 1 is not "safe".** Imperfections, residual stress, end-condition uncertainty, material scatter and thermal-field uncertainty all push the real capacity *below* an ideal linear eigenvalue. See `BUCKLING_RESULTS.md` §7.
