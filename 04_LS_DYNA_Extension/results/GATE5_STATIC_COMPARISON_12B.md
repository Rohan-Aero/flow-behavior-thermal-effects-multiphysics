# Section 12B — Gate 5: linear-elastic static reproduction of LC2 in LS-DYNA

> **Model.** The converted LC2 model (`../inputs/LS_DYNA_IMPORT_AUDIT_12B.md`): perfect geometry, no imperfection, no
> plasticity, no post-buckling. Thermo-elastic MAT_004 with temperature-dependent E and the exact MPAMOD thermal strain;
> LC2 supports; the mapped temperature field ramped over 40 equal steps.
>
> **Run.** `work_12B/G5_static/lc2_static.k`, solver R16.1 student SMP double precision, 4 threads, `memory=20m`.
> Post-processing: `work_12B/post_lc2_12B.py` and `work_12B/sum_spcforc_12B.py`, both read-only on project files.
>
> **Reference.** The Mechanical LC2 solution as recorded in the project:
>
> - `08_Structural_Analysis/LC2_Restrained/Solver_Output/s7b_nodal.csv` (108,252 nodes);
> - max von Mises 605.16 MPa;
> - mean axial stress −582.44 MPa (= −548.94 kN / A_nom);
> - max total deformation 0.1349 mm;
> - critical location at the outer edge of the inlet face.

## 1. Acceptance criteria (frozen before the G5 run)

These were written before the G5 solution existed. They follow from the G2/G3 evidence, and no criterion was loosened
afterwards.

| Quantity | Criterion | Engineering reason |
|---|---|---|
| Axial reaction and mean axial stress | **Raw:** within ±1.5 % of 548.94 kN / −582.44 MPa. **After the documented kinematic correction** (divide by the area factor the G2 benchmark measured, 1.00796): within **±0.5 %** | A resultant depends only on equilibrium, the material law and the supports, all of which are identical. The only known systematic difference is that NSOLVR 12 reports Cauchy stress on the deformed area. In the benchmark this is +0.796 %, against +0.794 % from (1 + (1+ν)αΔT)² |
| Reaction balance | Inlet + outlet Fz = 0 within 10⁻⁶ relative; hoop-node reactions ≈ 0 | Self-equilibrated thermal load |
| Peak von Mises (nodal-averaged, corner nodes) | Within **±3 %** of 605.16 MPa | A local, extrapolated nodal peak at an edge. It is sensitive to the integration rule (14 vs 27 points), extrapolation and averaging, which differ by design (G4). Kinematics do not change Cauchy stress at this strain level (bar C2: −581.40 MPa = closed form) |
| Von Mises / σz field | RMS difference over the corner nodes ≤ **1 %** of 605.16 MPa (≈ 6 MPa) | A field-wide check that the mapped temperatures and material law were applied everywhere, not only at the peak |
| Critical location | Max von Mises at the **outer edge (r = 20 mm) of the inlet face (z = 0)** | Required by the brief; the same physical location as in Mechanical |
| Max total deformation | Within **±1 %** of 0.1349 mm | Displacements are integrals of strain and depend little on the integration rule. Large- vs small-deformation measures differ only by O(ε²) ≈ 10⁻⁵ |
| Radial deformation | u_r range and mid-span outer u_r within ±1 %; nodal u_r RMS difference ≤ 1 % of max \|u_r\| | Same reason as above; radial growth is the main deformation in LC2 |

**Pass rule.**

- **G5 = PASS** if every criterion is met.
- **YELLOW** if a criterion is missed by a margin that a documented difference (G4) explains quantitatively.
- **RED** if any miss is unexplained.

## 2. Run

- **Completion.** Normal termination, 2026-10-02 20:29, after 703 s on 4 threads.
- **Convergence.** Every one of the 40 steps reached equilibrium in 2 BFGS iterations.
- **Messages.** No error. The licence-client notice is the same non-blocking one recorded in G0.
- **Size.** 108,252 nodes and 23,400 elements were accepted under the Student licence.
- **Outputs.** `nodout` (all nodes), `eloutdet` (nodal-averaged global stresses), `spcforc`, `d3plot`.
- **Post-processing records.** `G5_static/post_12B.json` and `spcforc_sum_12B.json`.

## 3. Comparison

Mechanical values are those of the solved LC2 (7B) at the same node IDs. "Corner nodes" means the 28,296 nodes at which
Mechanical stores SOLID186 nodal stress (F-041).

| Quantity | Mechanical LC2 | LS-DYNA G5 | Difference | Criterion | Result |
|---|---|---|---|---|---|
| Inlet reaction, raw | 548,936.6 N | 553,247.0 N | +0.785 % | ±1.5 % | **PASS** |
| Inlet reaction, corrected for deformed area (÷ 1.00796, G2 benchmark) | 548,936.6 N | 548,878.5 N | **−0.011 %** | ±0.5 % | **PASS** |
| Mean axial stress −\|F\|/A_nom, raw | −582.44 MPa | −587.01 MPa | +0.785 % | ±1.5 % | **PASS** |
| Mean axial stress, corrected | −582.44 MPa | −582.38 MPa | **−0.011 %** | ±0.5 % | **PASS** |
| Reaction balance (inlet + outlet) | 1.8 × 10⁻⁸ N | ASCII `spcforc`: +6.2 N (553,247.0 vs −553,240.8 N), 1.1 × 10⁻⁵ relative. Binary output of the same solution (G5b): **1.3 × 10⁻⁵ N, 2.4 × 10⁻¹¹ relative** | — | ≤ 10⁻⁶ | **Missed as first measured; met with adequate output precision** (§4, §5) |
| Hoop-node reactions | ≈ 10⁻⁷ N | ≤ 1.1 × 10⁻¹¹ N | — | ≈ 0 | **PASS** |
| **Peak von Mises** (corner nodes) | **605.161 MPa**, node 18865 | **605.160 MPa**, node 18865 | **−1.1 × 10⁻⁴ %** | ±3 % | **PASS** |
| **Critical location** | outer edge of the inlet face: node 18865, r = 20.000 mm, z = 0, 437.99 K | **the same node** 18865, r = 20.000 mm, z = 0, 437.99 K | identical | outer edge of the inlet face | **PASS** |
| Von Mises field (28,296 corner nodes) | — | RMS difference **1.11 MPa** (0.18 % of peak); max \|Δ\| 4.97 MPa at node 18974 (bore, z = 4.3 mm) | — | RMS ≤ 6.05 MPa | **PASS** |
| σ_z field (corner nodes) | — | RMS difference **1.93 MPa**; max \|Δ\| 9.01 MPa at node 18945 (bore, z = 2.1 mm) | — | RMS ≤ 6.05 MPa | **PASS** |
| Same, interior (z = 15–585 mm, 25,272 nodes) | — | von Mises RMS 1.04 / max 3.26 MPa; σ_z RMS 1.84 / max 5.40 MPa, mean −0.14 MPa | — | (information) | — |
| **Max total deformation** | **0.13488 mm**, outer surface, z = 244.1 mm | **0.13556 mm**, outer surface, z = 244.1 mm (different θ on the same ring) | **+0.50 %** | ±1 % | **PASS** |
| Radial deformation u_r, range | 0.026745 – 0.089734 mm | 0.026786 – 0.089915 mm | +0.15 % / +0.20 % | ±1 % | **PASS** |
| u_r at mid-span outer surface (36-node ring mean) | 0.082563 mm | 0.082719 mm | +0.19 % | ±1 % | **PASS** |
| u_r nodal field (108,252 nodes) | — | RMS difference 0.11 µm (0.13 % of max u_r); max 0.18 µm | — | RMS ≤ 1 % of max | **PASS** |
| Axial displacement u_z, minimum (information) | −0.10876 mm | −0.10949 mm | +0.67 % | — | §4 |
| Lateral (non-radial) displacement | 0 (perfect geometry) | ≤ 6.4 × 10⁻⁷ mm | — | — | no spurious sway |

## 4. Explanation of every difference

- **Reaction and mean axial stress, +0.785 % raw.**
  - NSOLVR 12 is a large-deformation formulation. The reaction is the Cauchy stress integrated over the **deformed**
    end-face area. That area has grown by about (1 + (1+ν)ε)², with the mean mechanical strain |ε| ≈ 3.07 × 10⁻³
    (582 MPa / ≈ 190 GPa).
  - The G2 benchmark on the same mesh measured this factor as 1.00796 at the same strain level (analytic 1.00794).
  - Removing it leaves **−0.011 %**. This is not a tuning step: the factor was measured on a separate model before G5
    and frozen in §1.
- **Reaction balance: 1.1 × 10⁻⁵ as first measured (criterion 10⁻⁶).**
  - **First explanation (wrong).** I first attributed it to LS-DYNA's default convergence tolerances: DCTOL 1.0 × 10⁻³
    and ECTOL 1.0 × 10⁻², with the residual-force tolerance RCTOL off by default (9.99 × 10¹⁰). Diagnostic G5b (§5)
    **disproved** this.
  - **What G5b showed.**
    - With residual-norm ratios reduced to 6 × 10⁻¹¹, the ASCII reactions are identical to G5 in every printed digit,
      including the 6.2 N imbalance.
    - The binary output of the same solution balances to 1.3 × 10⁻⁵ N.
  - **Actual cause.** The 6.2 N is rounding in the ASCII `spcforc` file, which prints each nodal force to 5
    significant digits. The worst-case bound over 2 × 612 nodes at t = 1 is 45 N.
  - **Status.** The criterion is unchanged and is met by the solution. The first measurement method was not precise
    enough for a 10⁻⁶ check.
- **Axial displacement, +0.67 %, and total deformation, +0.50 %.**
  - With both end faces held, u_z(z) is the small difference between the local thermal strain and the mechanical
    strain.
  - In the large-deformation solution the axial force is constant, but the Cauchy stress varies along z with the local
    area: σ_C(z) = N / A_def(z).
  - This changes the local mechanical strain by about 2(1+ν)|ε| ≈ 0.8 % of the strain differences that build u_z. The
    observed +0.67 % is that order and sign.
  - Total deformation combines u_r (+0.2 %) and u_z (+0.67 %) as (u_r² δ_r + u_z² δ_z) / |u|². At the maximum node this
    gives 0.49 %, against 0.50 % observed.
  - **Correction to the §1 rationale.** §1 expected O(ε²) differences in displacement. That holds for u_r, but not for
    u_z: u_z is a small difference of strains, so the kinematic effect on it is O(ε) relative. The ±1 % criterion itself
    is unchanged and is met.
- **σ_z field, RMS 1.9 MPa (interior 1.8 MPa).** The same cause. In the interior, σ_C(z) − N/A₀ ≈ −σ · 2(1+ν) Δε_th(z).
  The axial mean-strain variation Δε_th ≈ ±1 × 10⁻³ gives ±1.5 MPa. The interior mean difference is only −0.14 MPa.
- **Local field maxima, 4.97 MPa von Mises / 9.0 MPa σ_z.**
  - Both are at the **bore within 5 mm of the inlet face**, in the entrance-region zone of the steepest temperature
    gradient (F-035 / F-040).
  - That is where the integration rule matters most: 14 points vs 27, and a different extrapolation to the nodes.
  - Both are below the F-040 temperature-transfer bound of ±9.8 MPa that already applies there.
- **Peak von Mises.** The peak node, its temperature and its value agree to 1 × 10⁻⁶. The governing outer-edge state is
  smooth, nearly uniaxial and dominated by temperature, so the formulation differences cancel there.

## 5. Diagnostic G5b: convergence tolerance and reaction output

**Purpose.** Find out whether the 6.2 N imbalance comes from the solver's convergence, or from the precision of the
reaction output. G5b is a diagnostic, not a gate result. Deck: `work_12B/G5b_tol_diag/lc2_static_tol.k`. It is the G5
deck with only these changes:

- DCTOL = ECTOL = RCTOL = 1 × 10⁻⁶ and ABSTOL = 10⁻²⁰;
- NLPRINT 2, which prints every convergence norm;
- reaction forces also written to the binary `binout` (single precision, about 7 digits) next to the ASCII `spcforc`
  (5 significant digits).

| Attempt | Outcome | Kept in |
|---|---|---|
| 1: DCTOL = ECTOL = 10⁻⁶ only | **Stopped at step 7.** Still converged in 2 iterations (\|du\|/\|u\| ≈ 1.1 × 10⁻⁴ accepted), so the change had no effect. The criterion that accepted it is not printed at the default print level, and the cause was not established. Attempt 2 sets RCTOL and ABSTOL explicitly and prints every norm | `work_12B/G5b_run1_DCTOL_ECTOL_only_ABORTED/` |
| 2: full settings | **Stopped at step 3** to run G6 first. It had started out of core while memory from the stopped G6 run was not yet free (≈ 80 s per step). Steps 1–2 converged in 3 iterations; the residual-norm ratio fell to 2 × 10⁻¹³ | `work_12B/G5b_tol_diag/run2_stopped_step3_to_run_G6_first/` |
| 3: full settings | see below | `work_12B/G5b_tol_diag/` |

**Attempt 3: completed.**

- **Run.** Normal termination at 2026-10-03 01:30, 1,575 s elapsed; no out-of-core message.
- **Convergence.** All 40 steps converged in **3** iterations (G5: 2). The final residual-norm ratio was
  5.6 × 10⁻¹¹ (tolerance 10⁻⁶). At iteration 2, where the default criteria stopped in G5, attempt 2 printed about
  3 × 10⁻⁹.

| Quantity at t = 1 | G5 (default tolerances) | G5b (tight tolerances) | Difference |
|---|---|---|---|
| ASCII `spcforc`, inlet / outlet | 553,247.0 / −553,240.8 N | 553,247.0 / −553,240.8 N | **identical** (imbalance +6.2 N in both) |
| Binary `binout`, inlet / outlet | not written | **553,246.352 / −553,246.352 N** | imbalance **1.3 × 10⁻⁵ N** (2.4 × 10⁻¹¹ relative) |
| Sum of all SPC z-forces (`binout` z-resultant) | — | 1.3 × 10⁻⁵ N | — |
| Von Mises field (108,252 nodes) | — | — | RMS 5 × 10⁻⁴ MPa, max 0.010 MPa (= the print resolution) |
| σ_z field | — | — | RMS 5 × 10⁻⁴ MPa, max 0.010 MPa; mean ratio 1.0000000006 |
| Peak von Mises | 605.160 MPa, node 18865 | 605.160 MPa, node 18865 | 0 |

**Conclusions.**

1. Tightening convergence changes no compared quantity beyond the print resolution. The default tolerances used in
   G5, G6 and the benchmarks are adequate for this linear-elastic, thermally loaded state.
2. The equilibrium of the solution is exact to 2.4 × 10⁻¹¹. The ASCII imbalance comes from 5-digit printing. At the
   other output times it is −0.92, −0.88, −4.88 and +6.20 N, each inside the worst-case print bound for that time
   (6.1, 25.6, 40.1 and 45.0 N).
3. The precise inlet reaction is 553,246.35 N, 0.69 N below the ASCII sum. After the deformed-area factor this is
   548,877.8 N, **−0.011 %** from Mechanical, unchanged from §3.
4. For later work, reactions should be read from `binout` (recommendation for 12C).

Records:

- `G5b_tol_diag/spcforc_sum_12B.json`;
- `compare_vs_G5_static.json`;
- `binout`;
- the binout sums (session workspace script output, reproduced in this table);
- `work_12B/spcforc_precision_12B.py` (print-precision bound).

## 6. Gate 5 outcome

**PASS.**

- Every comparison required by the brief meets its frozen criterion: maximum deformation, radial deformation, mean
  axial stress, peak von Mises, reaction forces and critical location.
- The one internal check that missed as first measured (reaction balance) is met when the reactions are read at
  adequate precision (G5b). The criterion was not changed.
- Two systematic differences remain, both documented:
  - large-deformation kinematics: reaction +0.79 % raw, u_z +0.67 %;
  - the integration rule, visible only in local fields near the inlet face.
