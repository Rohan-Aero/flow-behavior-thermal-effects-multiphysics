### T1. Mesh definition and quality

| Mesh | circ × wall × axial | Nodes | Elements (SOLID186) | of 128 k licence | radial size [mm] | circ. size bore / outer [mm] | axial size min / max [mm] | Mechanical aspect ratio max | edge ratio max | Jacobian ratio max | element quality min | inverted (corner Jacobian ≤ 0) | boundary faces found / expected | independent mesh check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| XC extra-coarse | 21 × 3 × 76 (bias 4) | 24,171 | 4,788 | 18.9 % | 3.333 | 2.99 / 5.98 | 3.63 / 14.53 | 4.88 | 4.87 | 1.348 | 0.244 | 0 | 3318 / 3318 | PASS |
| C coarse | 27 × 4 × 98 (bias 4) | 50,652 | 10,584 | 39.6 % | 2.500 | 2.33 / 4.65 | 2.82 / 11.28 | 4.86 | 4.86 | 1.258 | 0.231 | 0 | 5508 / 5508 | PASS |
| B baseline (re-meshed) | 36 × 5 × 130 (bias 4) | 108,252 | 23,400 | 84.6 % | 2.000 | 1.75 / 3.49 | 2.13 / 8.51 | 4.88 | 4.88 | 1.205 | 0.237 | 0 | 9720 / 9720 | PASS |
| B official (7B/8A) | 36 × 5 × 130 (bias 4) | 108,252 | 23,400 | 84.6 % | 2.000 | 1.75 / 3.49 | 2.13 / 8.51 | 4.88 | 4.88 | 1.205 | 0.237 | 0 | 9720 / 9720 | PASS |
| FR fine, through-wall | 36 × 6 × 130 (bias 4) | 127,080 | 28,080 | 99.3 % | 1.667 | 1.75 / 3.49 | 2.13 / 8.51 | 5.11 | 5.11 | 1.171 | 0.199 | 0 | 9792 / 9792 | PASS |
| FA fine, axial | 36 × 5 × 152 (bias 4) | 126,468 | 27,360 | 98.8 % | 2.000 | 1.75 / 3.49 | 1.82 / 7.28 | 4.18 | 4.18 | 1.205 | 0.307 | 0 | 11304 / 11304 | PASS |
| FC fine, circumferential | 42 × 5 × 130 (bias 4) | 126,294 | 27,300 | 98.7 % | 2.000 | 1.50 / 2.99 | 2.13 / 8.51 | 5.69 | 5.69 | 1.203 | 0.207 | 0 | 11340 / 11340 | PASS |
| IL inlet bias 8 | 36 × 5 × 130 (bias 8) | 108,252 | 23,400 | 84.6 % | 2.000 | 1.75 / 3.49 | 1.36 / 10.91 | 6.26 | 6.26 | 1.205 | 0.153 | 0 | 9720 / 9720 | PASS |

### T2. Temperature mapping on each mesh (same source: baseline_medium_final node field)

| Mesh | mapped nodes | unmapped | T min – max [K] | above source max [K] | (A) max error inside / outside source mesh [K] | (A) mean [K] | (B) max vs FV solution [K] | (B) max, z 14–586 mm [K] | nodes in the chord gap (clamped) |
|---|---|---|---|---|---|---|---|---|---|
| XC extra-coarse | 24,171 | 0 | 423.837 – 562.555 | 0.012 | 0.004 / 0.041 | 0.0032 | 2.42 | 0.22 | 4,600 |
| C coarse | 50,652 | 0 | 423.837 – 562.558 | 0.015 | 0.005 / 0.113 | 0.0025 | 2.33 | 0.28 | 7,696 |
| B baseline (re-meshed) | 108,252 | 0 | 423.837 – 562.558 | 0.014 | 0.081 / 0.092 | 0.0022 | 2.57 | 0.25 | 12,544 |
| B official (7B/8A) | 108,252 | 0 | 423.837 – 562.558 | 0.014 | 0.081 / 0.092 | 0.0022 | 2.57 | 0.25 | 12,544 |
| FR fine, through-wall | 127,080 | 0 | 423.837 – 562.558 | 0.014 | 0.081 / 0.092 | 0.0019 | 2.57 | 0.25 | 12,544 |
| FA fine, axial | 126,468 | 0 | 423.837 – 562.558 | 0.014 | 0.080 / 0.133 | 0.0020 | 2.38 | 0.28 | 14,656 |
| FC fine, circumferential | 126,294 | 0 | 423.837 – 562.560 | 0.016 | 0.081 / 0.141 | 0.0024 | 2.58 | 0.25 | 15,680 |
| IL inlet bias 8 | 108,252 | 0 | 423.837 – 562.557 | 0.013 | 0.090 / 0.051 | 0.0020 | 2.52 | 0.27 | 12,544 |

### T3. LC1 (free expansion, thermal only)

| Mesh | max total def. [mm] | free growth ΔL [mm] | max von Mises [MPa] | location | unaveraged max [MPa] | mid-span bore σθ [MPa] | mid-span bore VM [MPa] | inlet bore peak θ-mean [MPa] | \|ΣF\| reactions [N] | energy-norm error [%] |
|---|---|---|---|---|---|---|---|---|---|---|
| XC extra-coarse | 1.844368 | 1.840913 | 24.158 | bore, z 7.40 mm, 428.86 K | 24.358 | 17.998 | 17.807 | 24.128 @ 7.40 mm | 1.1e-07 | 1.839 |
| C coarse | 1.844318 | 1.840868 | 24.070 | bore, z 8.71 mm, 430.40 K | 24.272 | 18.213 | 18.078 | 24.042 @ 8.71 mm | 4.1e-07 | 0.970 |
| B baseline (re-meshed) | 1.844307 | 1.840860 | 24.282 | bore, z 6.52 mm, 427.81 K | 24.356 | 18.309 | 18.197 | 24.258 @ 6.52 mm | 3.9e-07 | 0.695 |
| B official (7B/8A) | 1.844307 | 1.840860 | 24.282 | bore, z 6.52 mm, 427.81 K | 24.356 | 18.309 | 18.197 | 24.258 @ 6.52 mm | 3.9e-07 | 0.695 |
| FR fine, through-wall | 1.844317 | 1.840871 | 24.550 | bore, z 6.52 mm, 427.81 K | 24.622 | 18.425 | 18.346 | 24.528 @ 6.52 mm | 5.2e-07 | 0.557 |
| FA fine, axial | 1.844305 | 1.840858 | 24.553 | bore, z 7.49 mm, 428.95 K | 24.792 | 18.310 | 18.196 | 24.531 @ 7.49 mm | 3.5e-07 | 0.720 |
| FC fine, circumferential | 1.844320 | 1.840873 | 24.206 | bore, z 6.52 mm, 427.81 K | 24.252 | 18.285 | 18.161 | 24.194 @ 6.52 mm | 7.6e-07 | 0.610 |
| IL inlet bias 8 | 1.844306 | 1.840859 | 24.511 | bore, z 7.29 mm, 428.71 K | 24.704 | 18.306 | 18.194 | 24.488 @ 7.28 mm | 6.4e-07 | 0.700 |

1-D generalised-plane-strain reference at z = 300 mm (same source field, `ref1d_lc1_8B.py`): bore σθ **18.698 MPa**, bore VM 18.671 MPa, outer σθ -11.550 MPa; ΔT_wall 7.561 K.

### T4. LC2 (axially restrained, thermal only)

| Mesh | max total def. [mm] | min u_z [mm] | max u_r [mm] | max von Mises [MPa] | location | unaveraged max [MPa] | outer edge of inlet face, θ-mean [MPa] | mean axial N/A [MPa] | max VM 15–585 mm [MPa] | end reaction [N] | pressure effect on max VM [Pa] | energy-norm error [%] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| XC extra-coarse | 0.1348870 | -0.1087485 | 0.0897382 | 604.8670 | r 20, z 0.0 mm, 437.99 K | 604.8676 | 604.8416 | -582.4470 | 591.791 | 548943.37 | +76 | 0.0313 |
| C coarse | 0.1348866 | -0.1087510 | 0.0897350 | 605.0957 | r 20, z 0.0 mm, 437.99 K | 605.0957 | 605.0708 | -582.4399 | 589.665 | 548936.69 | +45 | 0.0165 |
| B baseline (re-meshed) | 0.1348843 | -0.1087563 | 0.0897340 | 605.1609 | r 20, z 0.0 mm, 437.99 K | 605.1853 | 605.1576 | -582.4398 | 591.216 | 548936.61 | +45 | 0.0119 |
| B official (7B/8A) | 0.1348843 | -0.1087563 | 0.0897340 | 605.1609 | r 20, z 0.0 mm, 437.99 K | 605.1853 | 605.1576 | -582.4398 | 591.216 | 548936.61 | +45 | 0.0119 |
| FR fine, through-wall | 0.1348845 | -0.1087561 | 0.0897345 | 605.2204 | r 20, z 0.0 mm, 437.99 K | 605.2426 | 605.2139 | -582.4431 | 591.191 | 548939.73 | +77 | 0.0094 |
| FA fine, axial | 0.1348872 | -0.1087568 | 0.0897340 | 605.1396 | r 20, z 0.0 mm, 437.99 K | 605.1642 | 605.1363 | -582.4392 | 591.506 | 548936.04 | +77 | 0.0124 |
| FC fine, circumferential | 0.1348845 | -0.1087561 | 0.0897346 | 605.1698 | r 20, z 0.0 mm, 437.98 K | 605.1765 | 605.1579 | -582.4441 | 591.224 | 548940.64 | +77 | 0.0104 |
| IL inlet bias 8 | 0.1348848 | -0.1087565 | 0.0897340 | 605.1336 | r 20, z 0.0 mm, 437.99 K | 605.1582 | 605.1302 | -582.4396 | 591.271 | 548936.41 | — | 0.0121 |

### T5. LC2 linear buckling

| Mesh | λ₁ | λ₂ | (λ₂−λ₁)/λ₁ | λ₃ (= λ₄) | λ₅ (= λ₆) | P_cr = λ₁·N [kN] | beam-type share of mode 1 | ovalisation / lateral | z of max lateral [mm] | lateral at inlet / mid / outlet (norm.) | \|corr.\| with cos(πz/L) | mode 1 ⟂ mode 2 [°] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| XC extra-coarse | 1.1079876 | 1.1079876 | 3.8e-08 | 4.29765 | 9.22436 | 608.222 | 0.999999 | 9.8e-10 | 600 | -0.989 / 1.4e-05 / 1.000 | 0.999997 | 90.0 |
| C coarse | 1.1080342 | 1.1080343 | 3.0e-08 | 4.29785 | 9.22473 | 608.241 | 0.999999 | 9.1e-10 | 600 | -0.989 / 1.4e-05 / 1.000 | 0.999997 | 90.0 |
| B baseline (re-meshed) | 1.1080471 | 1.1080475 | 3.4e-07 | 4.29789 | 9.22481 | 608.248 | 0.999999 | 4.3e-11 | 600 | -0.989 / 1.4e-05 / 1.000 | 0.999997 | 90.0 |
| B official (7B/8A) | 1.1080470 | 1.1080471 | 1.3e-07 | 4.29790 | 9.22482 | 608.248 | 0.999999 | 3.0e-11 | 600 | -0.989 / 1.4e-05 / 1.000 | 0.999997 | 90.0 |
| FR fine, through-wall | 1.1080404 | 1.1080405 | 3.2e-08 | 4.29787 | 9.22476 | 608.247 | 0.999999 | 5.8e-11 | 600 | -0.989 / 1.4e-05 / 1.000 | 0.999997 | 90.0 |
| FA fine, axial | 1.1080483 | 1.1080483 | 2.8e-08 | 4.29790 | 9.22483 | 608.248 | 0.999999 | 8.7e-11 | 600 | -0.989 / 1.4e-05 / 1.000 | 0.999997 | 90.0 |
| FC fine, circumferential | 1.1080410 | 1.1080411 | 1.2e-07 | 4.29787 | 9.22477 | 608.249 | 0.999999 | 7.7e-11 | 600 | -0.989 / 1.4e-05 / 1.000 | 0.999997 | 90.0 |

### T6. Changes relative to the baseline B (relative)

| Quantity | XC vs B | C vs B | FR vs B | FA vs B | FC vs B | IL vs B | B official vs B |
|---|---|---|---|---|---|---|---|
| LC1 max von Mises [Pa] | -5.12e-03 | -8.75e-03 | +1.10e-02 | +1.11e-02 | -3.15e-03 | +9.40e-03 | +0.00e+00 |
| LC1 max total deformation [m] | +3.28e-05 | +6.02e-06 | +5.15e-06 | -1.21e-06 | +6.99e-06 | -8.06e-07 | +0.00e+00 |
| LC1 free growth dL [m] | +2.89e-05 | +4.60e-06 | +6.07e-06 | -1.12e-06 | +6.90e-06 | -3.96e-07 | +0.00e+00 |
| LC1 mid-span bore hoop stress [Pa] | -1.70e-02 | -5.26e-03 | +6.37e-03 | +5.27e-05 | -1.32e-03 | -1.50e-04 | +0.00e+00 |
| LC1 mid-span bore von Mises [Pa] | -2.14e-02 | -6.51e-03 | +8.20e-03 | -3.80e-05 | -1.98e-03 | -1.72e-04 | +0.00e+00 |
| LC1 inlet bore peak (theta-mean) [MPa] | -5.35e-03 | -8.93e-03 | +1.11e-02 | +1.13e-02 | -2.66e-03 | +9.49e-03 | +0.00e+00 |
| LC2 max von Mises [Pa] | -4.86e-04 | -1.08e-04 | +9.84e-05 | -3.51e-05 | +1.47e-05 | -4.51e-05 | +0.00e+00 |
| LC2 mean axial stress [Pa] | +1.23e-05 | +1.32e-07 | +5.68e-06 | -1.05e-06 | +7.33e-06 | -3.70e-07 | -0.00e+00 |
| LC2 max total deformation [m] | +1.99e-05 | +1.69e-05 | +1.34e-06 | +2.14e-05 | +1.83e-06 | +3.94e-06 | +0.00e+00 |
| LC2 min axial displacement [m] | -7.16e-05 | -4.81e-05 | -1.12e-06 | +4.92e-06 | -1.21e-06 | +2.57e-06 | -0.00e+00 |
| LC2 max radial displacement [m] | +4.73e-05 | +1.12e-05 | +5.54e-06 | -5.08e-07 | +6.49e-06 | -2.90e-08 | +0.00e+00 |
| LC2 end reaction [N] | +1.23e-05 | +1.32e-07 | +5.68e-06 | -1.05e-06 | +7.33e-06 | -3.70e-07 | +0.00e+00 |
| LC2 max von Mises 15-585 mm [Pa] | +9.73e-04 | -2.62e-03 | -4.28e-05 | +4.90e-04 | +1.38e-05 | +9.18e-05 | +0.00e+00 |
| LC2 outer edge at inlet face (theta-mean) [MPa] | -5.22e-04 | -1.43e-04 | +9.30e-05 | -3.52e-05 | +4.82e-07 | -4.53e-05 | +0.00e+00 |
| lambda_1 | -5.37e-05 | -1.16e-05 | -6.02e-06 | +1.08e-06 | -5.52e-06 | — | -1.11e-07 |
| critical buckling load [N] | -4.14e-05 | -1.15e-05 | -3.44e-07 | +3.04e-08 | +1.81e-06 | — | -1.11e-07 |
| lambda_3 | -5.53e-05 | -1.02e-05 | -4.78e-06 | +1.03e-06 | -5.28e-06 | — | +8.61e-07 |
| lambda_5 | -4.88e-05 | -8.87e-06 | -4.71e-06 | +2.25e-06 | -3.55e-06 | — | +8.23e-07 |
| LC1 energy-norm error [%] | +1.64e+00 | +3.95e-01 | -1.98e-01 | +3.57e-02 | -1.23e-01 | +7.34e-03 | +0.00e+00 |
| LC2 energy-norm error [%] | +1.63e+00 | +3.88e-01 | -2.06e-01 | +4.39e-02 | -1.23e-01 | +1.98e-02 | +0.00e+00 |
| LC1 max von Mises unaveraged [Pa] | +9.02e-05 | -3.45e-03 | +1.09e-02 | +1.79e-02 | -4.29e-03 | +1.43e-02 | +0.00e+00 |
| LC2 max von Mises unaveraged [Pa] | -5.25e-04 | -1.48e-04 | +9.47e-05 | -3.50e-05 | -1.46e-05 | -4.48e-05 | +0.00e+00 |

### T7. Systematic family XC → C → B (r = 1.3027): Richardson / GCI (Celik et al. 2008, Fs 1.25)

| Quantity | XC → C | C → B | behaviour | apparent order p | extrapolated (h → 0) | GCI_fine (rel.) | B vs extrapolated |
|---|---|---|---|---|---|---|---|
| LC1 max von Mises [Pa] | -3.66e-03 | +8.75e-03 | divergent / not in asymptotic range | — | — | — | — |
| LC1 max total deformation [m] | -2.68e-05 | -6.02e-06 | monotonic convergence | 5.64 | 0.001844304 | 2.18e-06 | +1.75e-06 |
| LC1 free growth dL [m] | -2.43e-05 | -4.60e-06 | monotonic convergence | 6.30 | 0.001840858 | 1.34e-06 | +1.07e-06 |
| LC1 mid-span bore hoop stress [Pa] | +1.18e-02 | +5.26e-03 | monotonic convergence | 3.04 | 1.838676e+07 | 5.32e-03 | -4.24e-03 |
| LC1 mid-span bore von Mises [Pa] | +1.50e-02 | +6.51e-03 | monotonic convergence | 3.13 | 1.828878e+07 | 6.32e-03 | -5.03e-03 |
| LC1 inlet bore peak (theta-mean) [MPa] | -3.61e-03 | +8.93e-03 | divergent / not in asymptotic range | — | — | — | — |
| LC2 max von Mises [Pa] | +3.78e-04 | +1.08e-04 | monotonic convergence | 4.75 | 6.051869e+08 | 5.37e-05 | -4.29e-05 |
| LC2 mean axial stress [Pa] | -1.22e-05 | -1.32e-07 | monotonic convergence | 17.12 | -5.824398e+08 | 1.80e-09 | +1.44e-09 |
| LC2 max total deformation [m] | -2.99e-06 | -1.69e-05 | divergent / not in asymptotic range | — | — | — | — |
| LC2 min axial displacement [m] | +2.35e-05 | +4.81e-05 | divergent / not in asymptotic range | — | — | — | — |
| LC2 max radial displacement [m] | -3.61e-05 | -1.12e-05 | monotonic convergence | 4.44 | 8.973356e-05 | 6.25e-06 | +5.00e-06 |
| LC2 end reaction [N] | -1.22e-05 | -1.32e-07 | monotonic convergence | 17.12 | 548936.6 | 1.80e-09 | +1.44e-09 |
| LC2 max von Mises 15-585 mm [Pa] | -3.61e-03 | +2.62e-03 | oscillatory convergence | — | — | — | — |
| LC2 outer edge at inlet face (theta-mean) [MPa] | +3.79e-04 | +1.43e-04 | monotonic convergence | 3.67 | 605.2105 | 1.09e-04 | -8.74e-05 |
| lambda_1 | +4.21e-05 | +1.16e-05 | monotonic convergence | 4.86 | 1.108052 | 5.55e-06 | -4.44e-06 |
| critical buckling load [N] | +2.99e-05 | +1.15e-05 | monotonic convergence | 3.62 | 608252 | 8.97e-06 | -7.18e-06 |
| lambda_3 | +4.51e-05 | +1.02e-05 | monotonic convergence | 5.62 | 4.297905 | 3.72e-06 | -2.97e-06 |
| lambda_5 | +3.99e-05 | +8.87e-06 | monotonic convergence | 5.69 | 9.224831 | 3.17e-06 | -2.53e-06 |
| LC1 energy-norm error [%] | -8.96e-01 | -3.95e-01 | monotonic convergence | 4.36 | 0.5684874 | 2.28e-01 | +2.23e-01 |
| LC2 energy-norm error [%] | -8.97e-01 | -3.88e-01 | monotonic convergence | 4.41 | 0.009802456 | 2.20e-01 | +2.13e-01 |
| LC1 max von Mises unaveraged [Pa] | -3.55e-03 | +3.45e-03 | oscillatory convergence | — | — | — | — |
| LC2 max von Mises unaveraged [Pa] | +3.77e-04 | +1.48e-04 | monotonic convergence | 3.53 | 6.052433e+08 | 1.20e-04 | -9.57e-05 |
