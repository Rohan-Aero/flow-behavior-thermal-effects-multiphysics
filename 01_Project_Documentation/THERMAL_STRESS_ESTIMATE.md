# THERMAL EXPANSION AND APPROXIMATE THERMAL STRESS — Section 2

> ### ⚠ THIS IS AN ESTIMATE, NOT A STRUCTURAL RESULT
> Every number below comes from a closed-form hand calculation. **It is not the answer.**
> It exists so that when ANSYS Mechanical produces a number in Section 6, there is
> something independent to compare it against. Where the FEA and this estimate disagree,
> the FEA is more likely right — but the *reason* for the disagreement must be understood
> and explained, not waved away.

**RE-ANALYSIS (2026).** No CFD or FEA has been run.

---

## 1. Thermal expansion

| Quantity | Symbol | Value | Equation |
|---|---|---|---|
| Volume-mean solid temperature | T_s | **554.7 K** (281.6 °C) | mean of (T_wi + T_wo)/2 over the duct |
| Stress-free reference | T_ref | 300 K | assembly / inlet condition |
| Temperature rise | ΔT | **254.7 K** | T_s − T_ref |
| Mean CTE at T_s | α | **13.72 × 10⁻⁶ /K** | Special Metals mean CTE from 21 °C |
| **Thermal strain** | ε_th | **3.494 × 10⁻³ = 3494 µε = 0.349 %** | **α ΔT** |
| Free axial growth | ΔL | **2.096 mm** | ε_th · L |
| Free radial growth of bore | Δr | **34.94 µm** | ε_th · rᵢ |
| Resulting flow-area change | ΔA/A | **0.700 %** | — |

### What thermal strain physically means

ε_th is the strain the material **wants** to take — the shape it would adopt if nothing
stopped it. A free bar heated uniformly by 255 K gets 0.35 % longer and develops
**exactly zero stress**.

**Stress appears only where that strain is prevented.** There are only two ways to prevent
it:

1. **External restraint** — something physically holds the part (→ LC2).
2. **Internal incompatibility** — neighbouring material at a different temperature wants a
   different strain, so the material fights itself (→ LC1).

This project computes both, on one identical temperature field, and compares them. That
comparison is the whole point.

### Note on the mean-CTE datum

Published mean CTE for Inconel 718 is referenced from 21 °C; our stress-free reference is
27 °C. Carrying the 6 K datum offset through rigorously changes total thermal strain by
**0.15 %** — negligible, and neglected with that number stated rather than ignored.

---

## 2. Is σ = E α ΔT applicable? — a question worth answering carefully

The simple constrained-bar formula assumes **uniaxial, complete restraint, uniform
temperature**. Testing it against each load case:

### LC2 — fully restrained: YES, approximately

Axial restraint is total, so the form is correct. The approximation is using a single
**volume-mean** temperature for a field that varies both radially (7.3 K) and axially
(44.8 K). Because the axial variation is the larger, the mean is a reasonable
representative value — but the real part will have higher stress at the hot end and lower
at the cold end. **The FEA will show an axial stress distribution; this estimate gives one
number.**

```
sigma_z = -E alpha ( T_mean - T_ref )
        = -188.1e9 * 13.72e-6 * 254.7
        = -657.2 MPa   (compressive)
```

### LC1 — free expansion: NO, not at all

A freely expanding bar at uniform temperature has **zero** stress, so E α ΔT would give a
meaningless answer. LC1 stress exists *only* because temperature varies through the wall
thickness. The correct tool is the **Timoshenko & Goodier thick-walled-cylinder solution**
for a logarithmic radial temperature field.

```
sigma_r     = C [ -ln(b/r) - k2 (1 - b^2/r^2) ln(b/a) ]
sigma_theta = C [ 1 - ln(b/r) - k2 (1 + b^2/r^2) ln(b/a) ]
sigma_z     = C [ 1 - 2 ln(b/r) - 2 k2 ln(b/a) ]

with  C = alpha E (T_i - T_o) / ( 2 (1 - nu) ln(b/a) ),   k2 = a^2/(b^2 - a^2)
```

---

## 3. Results

### LC1 — gradient-driven (exit station, free ends)

| Location | σ_r | σ_θ (hoop) | σ_z (axial) | σ_vM |
|---|---|---|---|---|
| Bore (r = 10 mm) | 0.00 | **+16.31** | +16.31 | **16.31 MPa** |
| Mid-wall (r = 15 mm) | +2.08 | −1.32 | +0.76 | 2.97 MPa |
| Outer (r = 20 mm) | 0.00 | **−10.34** | −10.34 | 10.34 MPa |

**Sign check — the physics must make sense:** the bore is the **cold** side, so it wants to
be shorter than its surroundings, is stretched by them, and goes into **tension**. The
outer surface is the **hot** side, wants to be longer, is held back, and goes into
**compression**. Radial stress is zero at both free surfaces, as it must be. Peak von
Mises **16.3 MPa = 1.6 % of hot yield.**

### LC2 — restraint-driven

| Quantity | Value |
|---|---|
| Axial stress | **−657.2 MPa** (compressive) |
| Hot yield strength at T_s | 1023.7 MPa |
| **Utilisation** | **0.642** |
| **Margin of safety** | **0.56** |

### The comparison

| | LC1 free | LC2 restrained | **Ratio** |
|---|---|---|---|
| Peak stress | 16.3 MPa | 657.2 MPa | **40.3×** |
| Utilisation of hot yield | 0.016 | 0.642 | |
| Margin of safety | 61 | 0.56 | |

> **Restraint dominates the through-wall gradient by a factor of 40.**
> If the FEA confirms this, the design driver is the mounting arrangement, not the thermal
> load. A duct like this must be allowed to grow — an expansion joint or a sliding support
> is worth more than any change of alloy.

### Robustness

Across the full literature range of the correlation-correction exponent:

| n | LC2 stress | Utilisation | Elastic? |
|---|---|---|---|
| 0.400 | −624.6 MPa | 0.609 | ✅ |
| 0.500 | −657.2 MPa | 0.642 | ✅ |
| 0.575 | −685.7 MPa | 0.671 | ✅ |

The conclusion holds throughout. Linear-elastic analysis stays valid in every case.

---

## 4. 🔴 Why ANSYS will differ — and where to expect it

Listing this **before** running the FEA is what separates verification from
rationalisation. Discrepancies at these locations are expected physics; discrepancies
elsewhere are errors.

| # | Cause | Expected effect | Where |
|---|---|---|---|
| 1 | **End effects.** The closed form assumes an infinitely long cylinder. Real ends have axial constraint and Poisson coupling the 1-D solution cannot represent. | Local peaks, possibly **several times** the mid-span value | within ~1–2 wall thicknesses of each end face |
| 2 | **Constraint modelling.** A real "fixed" face restrains radial and hoop motion too, not only axial. | Adds biaxial stress the estimate omits; raises local von Mises | at the restrained faces |
| 3 | **Stress concentration.** Any edge, fillet or mesh singularity at a constrained face reports a peak. | Can be **unbounded** with mesh refinement — a modelling artefact, not physics | sharp corners |
| 4 | **Non-uniform temperature field.** The estimate uses one mean temperature; FEA uses the full 3-D field including the 44.8 K axial variation. | LC2 stress higher at the hot end, lower at the cold end | along the duct |
| 5 | **Pressure loading.** Neglected here. Hoop stress p·rᵢ/t at the gauge pressure is **0.0004 MPa**. | Utterly negligible — 6 orders below thermal stress | everywhere |
| 6 | **Material behaviour.** Linear elastic assumed, valid while utilisation < 1 (max 0.64). | None, unless a local concentration drives a point past yield | at concentrations |

### How to use this estimate correctly

- ✅ Compare **away from the end faces**, in the mid-span region where the closed-form
  assumptions actually hold.
- ✅ Treat agreement within **±15 %** at mid-span as validation of the thermal mapping and
  the FEA setup.
- ❌ Do **not** compare against a peak value at a constrained corner — that is a
  singularity, and refining the mesh will only make it larger.
- ❌ Do **not** treat these as acceptance criteria to 1 %. They are order-of-magnitude
  targets.
- ⚠ If the FEA reports LC2 far from −E α ΔT at mid-span, suspect the **temperature import**
  before suspecting the stress solver.
