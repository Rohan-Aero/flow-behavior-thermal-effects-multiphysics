# ENGINEERING REQUIREMENTS — Section 1

**Project:** Flow Behavior and Thermal Effects in Multiphysics Systems (RE-ANALYSIS, 2026)
**Date:** 2026-09-18

> All requirements below are **re-analysed** engineering targets defined in 2026.
> They are not requirements carried over from the lost 2025 original.

Requirement status: `OPEN` = not yet addressed · `MET` = satisfied and evidenced.

---

## FR — Functional Requirements (what the model must represent)

| ID | Requirement | Verification method | Status |
|----|-------------|--------------------|--------|
| FR-01 | The model shall represent steady, turbulent, internal forced convection of air in a circular duct at Re ≥ 10⁴. | Report inlet and outlet Re from the converged solution. | OPEN |
| FR-02 | The model shall solve conjugate heat transfer, with the fluid–solid interface temperature computed rather than prescribed. | Confirm coupled wall BC; show continuous temperature across the interface. | OPEN |
| FR-03 | The model shall resolve the temperature distribution through the full solid wall thickness. | Extract radial temperature profile at ≥ 3 axial stations. | OPEN |
| FR-04 | The model shall compute thermal expansion and the resulting stress from the CFD temperature field. | Imported body temperature in Mechanical; displacement and stress fields. | OPEN |
| FR-05 | The model shall evaluate two structural restraint cases sharing one identical temperature field. | LC1 and LC2 results compared side by side. | OPEN |
| FR-06 | The analysis shall remain within the linear-elastic regime, or explicitly declare where it does not. | Compare peak stress to hot yield strength. | OPEN |

## PR — Performance / Physics Requirements (what the answer must be)

| ID | Requirement | Target | Acceptance | Status |
|----|-------------|--------|-----------|--------|
| PR-01 | Global energy balance shall close. | Q = 603.2 W | within **0.5 %** | OPEN |
| PR-02 | Outlet bulk temperature shall match the 1-D energy march. | 368.9 K | within **3 %** | OPEN |
| PR-03 | Fully developed Nusselt number shall fall within the correlation band. | 49.6 property-corrected; 61.9–66.8 constant-property | accept **44–67**, expect near 50 | OPEN |
| PR-04 | Darcy friction factor shall match Petukhov. | 0.0241 | within **10 %** | OPEN |
| PR-05 | Total pressure drop shall match the analytical estimate. | 412 Pa (263 friction + 149 acceleration) | within **15 %** | OPEN |
| PR-06 | Peak inner-wall temperature shall match the 1-D march. | 574.3 K corrected (533.5 K uncorrected) | within **5 %** of corrected | OPEN |
| PR-07 | Through-wall temperature drop shall match cylindrical conduction theory. | 7.2 K | within **10 %** | OPEN |
| PR-08 | LC1 peak von Mises stress shall match the thick-cylinder closed form. | 16.5 MPa | within **15 %** | OPEN |
| PR-09 | LC2 axial stress shall match −E·α·ΔT. | −668 MPa | within **10 %** | OPEN |
| PR-10 | Margin of safety against hot yield shall be reported for both load cases. | LC2 MoS ≈ 0.59 (utilisation 0.63) | must be **> 0** | OPEN |
| PR-11 | The LC2/LC1 stress ratio shall be quantified — the central finding. | ≈ 40× | order of magnitude | OPEN |

## NR — Numerical Quality Requirements (what makes the answer trustworthy)

| ID | Requirement | Acceptance | Status |
|----|-------------|-----------|--------|
| NR-01 | Wall y⁺ on the conjugate interface shall support wall-resolved treatment. | y⁺ ≤ 1 target; ≤ 5 acceptable, reported either way | OPEN |
| NR-02 | Mesh independence shall be demonstrated across three refinement levels. | < **3 %** change in Nu and peak solid temperature | OPEN |
| NR-03 | Scaled residuals shall converge. | energy < 1 × 10⁻⁶; continuity, momentum, turbulence < 1 × 10⁻⁴ | OPEN |
| NR-04 | Convergence shall be confirmed by a physical monitor, not residuals alone. | outlet bulk temperature plateaus to < 0.1 K drift | OPEN |
| NR-05 | Mesh quality shall meet solver guidance. | orthogonal quality > 0.1; max skewness < 0.95 | OPEN |
| NR-06 | Second-order discretisation shall be used for the final solution. | second-order upwind on momentum, energy and turbulence | OPEN |
| NR-07 | The thermal mapping from CFD to FEA shall conserve the temperature field. | mapped min/max within 1 K of source; mapping summary recorded | OPEN |

## CR — Computational Constraints (the machine this must actually run on)

| ID | Constraint | Value | Source | Status |
|----|-----------|-------|--------|--------|
| CR-01 | Fluent parallel execution is capped by the Student licence. | **4 cores** | Measured: Fluent transcript, 2026-09-18 | **MET (verified)** |
| CR-02 | Available system memory. | 15.7 GB | Measured on device | **MET (verified)** |
| CR-03 | Target mesh size. | ~170 000 cells (fluid ≈ 125 k + solid ≈ 43 k) | Derived from mesh sizing | OPEN |
| CR-04 | Solid mesh must stay within the Mechanical node limit. | ≈ 48 000 nodes, under the typical 128 k Student limit | Derived; limit itself **unverified** | OPEN |
| CR-05 | Two-way FSI coupling shall not be used unless justified. | One-way; justified by 0.71 % flow-area change | Derived | **MET** |
| CR-06 | No additional software or plugins shall be installed. | PyAnsys absent → native journal files used | User directive | **MET** |

## DR — Documentation & Integrity Requirements (non-negotiable)

| ID | Requirement | Status |
|----|-------------|--------|
| DR-01 | Every deliverable shall carry the re-analysis notice. | **MET** |
| DR-02 | No output shall ever be described as recovered, restored, measured, or original. | **MET** |
| DR-03 | Every parameter shall carry a source/basis and a `[RE-ANALYSED]`/`[ASSUMED]`/`[LITERATURE]` tag. | **MET** (PARAMETERS.xlsx) |
| DR-04 | Hand calculations shall precede simulation, so CFD has an independent baseline. | **MET** (sizing_calculations.py) |
| DR-05 | PROJECT_STATE.md shall be updated at the end of every phase. | **MET** |
| DR-06 | Physically questionable assumptions shall be flagged, not hidden. | **MET** (ASSUMPTIONS.md) |
| DR-07 | Software versions and licence limits shall be recorded from measurement, not assumption. | **MET** (verified 2026-09-18) |
| DR-08 | Where a validity check fails, the design shall be changed and the reasoning recorded — not the check ignored. | **MET** (heat flux re-selected, ASSUMPTIONS A-006) |

---

## Traceability: requirement → research question

| RQ | Addressed by |
|----|-------------|
| RQ1 — correlation agreement | PR-03, PR-04, PR-05 |
| RQ2 — wall temperature distribution | FR-02, FR-03, PR-06, PR-07 |
| RQ3 — gradient vs restraint | FR-05, PR-08, PR-09 |
| RQ4 — structural acceptability | FR-06, PR-10 |
| RQ5 — coupling sufficiency | CR-05 |
| RQ3 — gradient vs restraint (ratio) | PR-11 |
