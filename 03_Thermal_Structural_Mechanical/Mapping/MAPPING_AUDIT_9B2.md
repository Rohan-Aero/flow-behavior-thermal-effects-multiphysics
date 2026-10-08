# CFD → Mechanical temperature-mapping audit — Section 9B-2 (Part D)

> **RE-ANALYSIS 2026.** Every number in this document is a newly generated ANSYS 2026 R1 Student result of this re-analysis (Fluent CFD of Section 9B-1, Mechanical of Section 9B-2), computed from the solver's own output tables. Nothing is a recovered internship value, and no experimental or measured data exist or are implied.

**Method (identical to Section 7A for every case).** The master mesh is the case's *own* Fluent solid mesh (read from its case file, written as an MAPDL CDB). The data are the case's *own* Fluent node temperatures (EnSight export of 9B-1), keyed by node id. Mechanical External Data → Imported Body Temperature with Manual / Bucket Volume / Shape Functions, and Nearest Node outside the source. No uniform temperature is used anywhere. Script: `Mapping/mapping_audit_9B2.py`; data: `Mapping/mapping_audit_9B2.json`.

**What is compared.**

- **(A) mapping error.** The nodal temperatures in the LC2 solver input (BFBLOCK) are compared with an exact re-evaluation of the same Fluent node field. The re-evaluation uses the trilinear shape functions of the source hexahedra (the 7A module `source_mesh_interp.HexField`, unchanged).
- **(B) surface check.** The outer and bore surface nodes are compared with Fluent's finite-volume wall-face temperatures (θ-mean per slab, linear in z).
- **Mid-span plane.** The through-wall ΔT and the radially area-weighted section mean of the mapped field are compared with the source node field on the same plane.

**Acceptance, fixed before the audit ran.**

- 0 unmapped nodes;
- (A) ≤ 0.25 K (the accepted 7A value on the baseline numbering is 0.092 K and is shown for comparison);
- no extrapolation beyond the source node range by more than 0.05 K;
- mid-span ΔT and section mean preserved within 0.05 K.

## Family: baseline geometry (mesh B)

| Case | Structural nodes | Source nodes / cells (layers) | Unmapped | Mapped T range [K] | Source node range [K] | Beyond source [K] | Nodes outside source (chord gap) | (A) max / RMS [K] | (B) outer max, 14–586 mm [K] | (B) bore max, 14–586 mm [K] | Mid-span ΔT mapped / source [K] | Mid-span mean mapped / source [K] | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C00 | 108,252 | 48,048 / 43,200 (10) | 0 | 423.837 – 562.566 | 423.837 – 562.544 | 0.022 | 12,544 | 0.096 / 0.0066 | 0.061 | 0.221 | 7.5796 / 7.5805 | 536.363 / 536.358 | **PASS** |
| V01 | 108,252 | 48,048 / 43,200 (10) | 0 | 435.916 – 587.455 | 435.916 – 587.433 | 0.022 | 12,544 | 0.103 / 0.0065 | 0.063 | 0.233 | 7.3780 / 7.3789 | 559.140 / 559.135 | **PASS** |
| V03 | 108,252 | 48,048 / 43,200 (10) | 0 | 413.884 – 542.088 | 413.884 – 542.066 | 0.023 | 12,544 | 0.090 / 0.0066 | 0.058 | 0.210 | 7.7540 / 7.7550 | 517.596 / 517.591 | **PASS** |
| Q01 | 108,252 | 48,048 / 43,200 (10) | 0 | 410.597 – 534.435 | 410.597 – 534.415 | 0.021 | 12,544 | 0.086 / 0.0060 | 0.055 | 0.198 | 7.0344 / 7.0353 | 510.615 / 510.610 | **PASS** |
| Q03 | 108,252 | 48,048 / 43,200 (10) | 0 | 437.279 – 591.115 | 437.279 – 591.092 | 0.024 | 12,544 | 0.106 / 0.0070 | 0.068 | 0.244 | 8.0885 / 8.0895 | 562.567 / 562.561 | **PASS** |

## Family: T01 thin wall (36 x 4 x 130)

| Case | Structural nodes | Source nodes / cells (layers) | Unmapped | Mapped T range [K] | Source node range [K] | Beyond source [K] | Nodes outside source (chord gap) | (A) max / RMS [K] | (B) outer max, 14–586 mm [K] | (B) bore max, 14–586 mm [K] | Mid-span ΔT mapped / source [K] | Mid-span mean mapped / source [K] | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T01 | 89,424 | 43,680 / 38,880 (9) | 0 | 417.966 – 561.941 | 417.966 – 561.927 | 0.014 | 11,496 | 0.154 / 0.0075 | 0.099 | 0.222 | 6.4356 / 6.4366 | 535.837 / 535.830 | **PASS** |

## Family: T03 thick wall (36 x 6 x 130)

| Case | Structural nodes | Source nodes / cells (layers) | Unmapped | Mapped T range [K] | Source node range [K] | Beyond source [K] | Nodes outside source (chord gap) | (A) max / RMS [K] | (B) outer max, 14–586 mm [K] | (B) bore max, 14–586 mm [K] | Mid-span ΔT mapped / source [K] | Mid-span mean mapped / source [K] | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T03 | 127,080 | 56,784 / 51,840 (12) | 0 | 428.783 – 563.058 | 428.783 – 563.044 | 0.014 | 10,980 | 0.105 / 0.0063 | 0.062 | 0.234 | 8.6070 / 8.6080 | 536.837 / 536.830 | **PASS** |

## Findings

- **All 7 mapped cases pass every criterion.**
- Unmapped nodes: **0 in every case**. The mapped range stays within the source node range, apart from ≤ 0.024 K of shape-function overshoot at the chord-gap nodes.
- The mapping error (A) is 0.086–0.154 K. This is the same order as the accepted 7A value (0.092 K), and it is largest at the outer chord-gap nodes, where the true circle lies outside the 48-facet source mesh.
- The surface check (B) peaks in the first and last 14 mm, where the adiabatic end faces meet the wall. This is the known local limitation F-035 of 7A. Between 14 and 586 mm it is ≤ 0.099 K (outer) and ≤ 0.244 K (bore).
- The mid-span through-wall ΔT and the section mean are preserved within 0.0011 K and 0.0079 K.
- **Numbering effect (C00).** The C00 source is the P00 field on identical coordinates, but Fluent re-numbered its node and cell ids. Mechanical's bucket search therefore interpolates some target nodes in a different, equally valid source element. The nodal temperatures differ from the 7B input by at most 0.0814 K (4639 of 108,252 nodes). This difference is below the accepted mapping error, and its effect on the results is reported as the mapping uncertainty in `Results/FINAL_PARAMETRIC_AUDIT.md`.
