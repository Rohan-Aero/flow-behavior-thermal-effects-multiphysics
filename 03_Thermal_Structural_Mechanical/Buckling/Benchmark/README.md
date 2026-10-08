# Benchmark (Section 8A), toy model: not project results

This folder checks the thermal-prestress eigen-buckling method on a tube with the duct geometry (ri 10 mm, ro 20 mm, L 600 mm). It uses **constant** E = 190 GPa, ν = 0.294, α = 13.6 × 10⁻⁶ /K and a **uniform** ΔT = 225 K, so that the exact answer is known.

| Case | End condition | FE λ₁ | Euler | Euler + shear |
|---|---|---|---|---|
| `sway/` | LC2-type: U_z = 0 on both end faces + 3 mid-span hoop nodes (guided, K = 1) | 1.1176 | 1.1199 | 1.1040 |
| `nosway/` | U_z = 0 and U_θ = 0 on both end faces (clamped, K = 0.5) | 4.3422 | 4.4796 | 4.237 |

- **Inputs:** `bench_main.inp` (with `bench_sway.inp` / `bench_nosway.inp`), run by `run_bench.ps1` (MAPDL 2026 R1 Student).
- **Outputs:** `*/s8a_load_factors.csv`, `*/s8a_mode*.csv`, `*/bench_*.out`.
- **What it shows:** the method scales the restrained thermal force as intended, the LC2 supports act as a guided column, and the FE lies between the plain and the shear-corrected Euler values.
