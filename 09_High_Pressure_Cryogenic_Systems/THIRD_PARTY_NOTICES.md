# Third-party notices

**CONCEPTUAL — NOT APPROVED FOR CONSTRUCTION.** Conceptual and educational study. This file records, for every third-party source used in this folder, what it is, the terms under which it may be reused, and the credit it requires. It is not legal advice. Retrieval and checks: 2026-10-11.

Publicly accessible does not mean freely redistributable. A source is used here only where its reuse terms were read and allow what is done with it. Where they were not clear, the data were **removed** and the results that depend on them are marked **UNAVAILABLE** (`DESIGN_BASIS.md` section 4).

## 1. Software and values computed with it: CoolProp (MIT licence)

| | |
|---|---|
| What | CoolProp 8.0.0, an open-source thermophysical property library. https://github.com/CoolProp/CoolProp |
| Use here | `generate_verified_properties.py` calls it to compute `verified_properties.csv` (nitrogen properties from the published reference equation of state of Span et al. 2000 and the transport correlations of Lemmon and Jacobsen 2004). Three constants are also read from it: the molar mass of nitrogen (VC-02) and the boiling temperature of oxygen at 0.101325 MPa (VC-06), and its version (VC-07). CoolProp itself is **not** copied into this repository; it is installed with `pip install CoolProp==8.0.0` only to regenerate or re-check the table. |
| Licence | MIT. The licence text and copyright line below are reproduced as the licence requires. |
| Scope | The MIT licence covers the CoolProp **software** only. It does **not** cover this repository, and it does **not** cover any material-property data, standard, or other third-party data named in this file. |

```
MIT License

Copyright (c) 2012-2018 Ian H. Bell and other CoolProp developers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

The MIT licence text above was read from the licence file shipped with the CoolProp 8.0.0 distribution that generated the table.

Scientific sources implemented by CoolProp and credited here:

- Span, R., Lemmon, E. W., Jacobsen, R. T, Wagner, W., Yokozeki, A., "A Reference Equation of State for the Thermodynamic Properties of Nitrogen for Temperatures from 63.151 to 1000 K and Pressures to 2200 MPa", J. Phys. Chem. Ref. Data 29, 1361-1433 (2000).
- Lemmon, E. W., Jacobsen, R. T, "Viscosity and Thermal Conductivity Equations for Nitrogen, Oxygen, Argon, and Air", Int. J. Thermophys. 25, 21-69 (2004).
- Bell, I. H., Wronski, J., Quoilin, S., Lemort, V., "Pure and Pseudo-pure Fluid Thermophysical Property Evaluation and the Open-Source Thermophysical Property Library CoolProp", Ind. Eng. Chem. Res. 53, 2498-2508 (2014).

## 2. SI defining constants: BIPM (CC BY 4.0)

| | |
|---|---|
| What | The exact defining constants of the SI (Avogadro constant, Boltzmann constant, Planck constant, speed of light), from BIPM, *The International System of Units (SI)*, 9th edition (2019, updated). https://doi.org/10.59161/AUEZ1291 |
| Use here | `verified_constants.csv` VC-08 to VC-11. The molar gas constant (VC-01) and the Stefan-Boltzmann constant (VC-03) are **derived** from them by the formulas in `validate_design.py` check V-A03. |
| Terms | The BIPM page for the brochure states a Creative Commons Attribution 4.0 International licence (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/). The credit above is the required attribution. Only the numerical values of the defining constants are used; no text or figure of the brochure is copied. No change to the values was made. |

## 3. NASA Earth Fact Sheet (credit NASA)

| | |
|---|---|
| What | The oxygen volume fraction of dry air, 20.95 percent (VC-04), from the NASA Space Science Data Coordinated Archive Earth Fact Sheet. https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html |
| Terms | A single physical-fact figure. NASA's media usage guidelines (https://www.nasa.gov/nasa-brand-center/images-and-media/) state that NASA content is generally not subject to copyright in the United States and ask that NASA be acknowledged as the source. The figure is credited to NASA here; no endorsement by NASA is implied. |

## 4. US federal regulation: 29 CFR 1910.146(b)

| | |
|---|---|
| What | The definition of an oxygen-deficient atmosphere, less than 19.5 percent oxygen by volume (VC-05), in the Code of Federal Regulations, Title 29, section 1910.146(b), US Government Publishing Office edition. https://www.govinfo.gov/content/pkg/CFR-2023-title29-vol5/xml/CFR-2023-title29-vol5-sec1910-146.xml |
| Terms | A work of the US Government, in the public domain. Cited as the source of a threshold only; the regulation is not reproduced, and no compliance with it is claimed. |

## 5. Standards and other documents read

NASA-STD-5005D (with Change 2) and NASA-STD-8719.17D were read in part from their public releases; ASME B31.3 was verified only as a listing and its text was not read; the KSC cryogenic standard could not be opened. **No standard is stored in this repository.** They are cited by number and clause as the source of an idea or a hazard to consider, with no text copied, and no compliance is claimed (`DESIGN_BASIS.md` section 7).

## 6. Rendering tool

The diagrams are Mermaid sources (`.mmd`); the SVG and PNG exports were rendered with `@mermaid-js/mermaid-cli` 11.4.2 (MIT licence). The tool is not included in this repository and its output contains no part of its code.

## 7. Deliberately not included

The following are **not** stored in this repository, because their reuse terms for redistribution were not cleared or because they state that permission is needed:

- **NIST Chemistry WebBook fluid-property tables** (NIST Standard Reference Data 69). NIST states that Standard Reference Data are copyrighted and may not be reproduced, stored or transmitted without permission. The nitrogen table here is computed from the published equation of state with CoolProp and is not a copy of any NIST table. The WebBook was used only to compare individual values at authoring, and `validate_design.py --online` reads a few states live for comparison; the values read are never stored.
- **NIST CODATA recommended values** (SRD 121). The molar gas constant and the Stefan-Boltzmann constant are taken from the SI defining constants (section 2), not from the NIST CODATA pages.
- **NIST cryogenic material-property fits** (thermal conductivity, specific heat, Young's modulus and linear expansion of 304 stainless steel and 6061-T6 aluminium). An earlier draft carried about 60 transcribed coefficients. They were removed. No replacement with verified reuse terms was found, and no value was invented, so the contraction, movement, restraint stress, support conduction and metal cooldown heat are **UNAVAILABLE** (UI-34, UI-35; `thermal_contraction.csv`).

Anyone who adds material data later should record the exact document, its reuse terms and the required credit here before using it.

## 8. This study itself

This folder's own text, code and tables carry the repository's terms (`NOTICE.md` and `README.md` at the repository root): no open-source licence has been selected for the repository. The MIT licence of section 1 does not apply to them.
