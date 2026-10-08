# Three-Mesh Master Table — Section 6B

**RE-ANALYSIS 2026.** Coarse 51,840 / medium 159,840 / fine 500,580 cells, identical physics.
Full discussion: `../Mesh_Independence_Report.md`. Status: **A** clearly convergent · **B**
approximately convergent · **C** still changing materially · **D** affected by geometry/faceting ·
**E** inconclusive. Raw values with absolute and % differences for every step (including
coarse→fine) are in `three_mesh_raw_table.csv`.

## Master table

Machine-readable, with extrapolated values, GCI and the reason for each status:
`../MESH_INDEPENDENCE_RESULTS.csv`. Temperature percentages are of the rise above 300 K.

| Quantity | Coarse | Medium | Fine | Coarse→Medium | Medium→Fine | Geometry effect | Status |
|---|---|---|---|---|---|---|---|
| Cells | 51,840 | 159,840 | 500,580 | ×3.08 | ×3.13 | N = 32 / 48 / 72 | — |
| ṁ [g/s] | 8.631 | 8.662 | 8.676 | +0.36 % | +0.16 % | 100 % (planar ratio); corrected 8.687 on all | **D** |
| Δp [Pa] | 437.1 | 438.1 | 439.1 | +0.24 % | +0.23 % | est. −1.24 / −0.55 Pa, opposing | **B** |
| Δp, geometry-adjusted (est.) [Pa] | 434.9 | 437.1 | 438.7 | +0.52 % | +0.35 % | removed (estimate) | **B** (ext. 441.8) |
| T_out [K] | 369.12 | 368.93 | 368.85 | −0.18 K (−0.26 %) | −0.08 K (−0.12 %) | 101 % (Q/ṁ); corrected 368.783 / 368.785 / 368.786 | **D** |
| Q [W] | 602.22 | 602.76 | 602.99 | +0.09 % | +0.04 % | 100 % (lateral ratio); corrected 603.19 on all | **D** |
| T_max, solid [K] | 565.4 | 562.6 | 560.8 | −2.8 K (−1.07 %) | −1.7 K (−0.66 %) | bulk shift 7 % / 5 % | **B** (ext. 558.1 ± 3.4) |
| ΔT_wall, mid-span [K] | 7.554 | 7.581 | 7.597 | +0.35 % | +0.21 % | est. ≈ 76 % / 56 % (apothem) | **B** (ext. 7.620 ± 0.03) |
| Nu_fd | 53.4 | 54.2 | 54.7 | +1.48 % | +0.91 % | est. −0.05 % / −0.02 % | **B** (ext. 55.4) |
| f_fd | 0.02134 | 0.02163 | 0.02181 | +1.35 % | +0.85 % | est. −0.05 % / −0.02 % | **B** (ext. 0.0221) |
| Volume-mean solid T [K] | 527.7 | 525.5 | 524.2 | −0.95 % | −0.58 % | bulk shift | B (ext. 522.3) |
| y⁺ mean | 0.238 | 0.241 | 0.243 | +1.2 % | +0.7 % | none (first layer fixed) | B |
| y⁺ max | 0.52 | 0.58 | 0.65 | +12 % | +12 % | sampling position (first slab) | **E** |
| Mass imbalance [%] | 1.2e-13 | 7.0e-13 | 3.9e-12 | — | — | — | A (round-off) |
| Energy imbalance [%] | 2.0e-11 | 3.1e-11 | 6.2e-11 | — | — | — | A (round-off) |

