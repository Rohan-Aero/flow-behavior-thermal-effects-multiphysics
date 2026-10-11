# Validation report

**CONCEPTUAL — NOT APPROVED FOR CONSTRUCTION.** Result of `validate_design.py` on this folder. Generated: do not edit by hand. The report has no timestamps; re-running reproduces it.

Mode: offline checks plus online re-check of the verified data (`--online`). 52 checks: 52 pass, 0 fail, 0 skipped. Mutation tests: 22 of 22 detected.

These checks validate the arithmetic, the data traceability and the internal consistency of the study. They do **not** validate pressure-vessel or piping integrity, relief-device sizing or code compliance, which this study does not attempt.

## A. Source and verified data

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-A01 | EXISTING parameters equal the master register and the baseline sheet | PASS | each EXISTING value is in its source | 5 conditions, all hold | M002, M003, M005, M023 and the air gas constant of BASELINE_PARAMETERS.md |
| V-A02 | Illustrative mass flow equals the existing rig design flow (independent recomputation and 08 flow_basis.csv) | PASS | equal within 2e-6 (the 08 file holds 6 digits) | 2 conditions, all hold | IL-01 is reused only for its magnitude |
| V-A03 | Verified constants: SI defining constants are exact; derived constants and copies agree; every source is listed in THIRD_PARTY_NOTICES.md | PASS | exact SI relations hold; every row has a URL and date; every source URL is in THIRD_PARTY_NOTICES.md | 34 conditions, all hold | BIPM SI defining constants (CC BY 4.0), CoolProp 8.0.0 (MIT), NASA, 29 CFR 1910.146(b) |
| V-A04 | Verified nitrogen tables are internally consistent | PASS | tolerances: 0.15 percent for the ideal-gas density (Z = 0.9998), 5 percent for Clapeyron (central difference over a 19 K interval carries a curvature error of a few percent) | 13 conditions, all hold | equation-of-state tables |
| V-A05 | Provenance guard: no uncleared third-party data in the folder; licence notices intact; unavailable results hold no numbers | PASS | verified constants come only from the BIPM, CoolProp, NASA and the CFR; no NIST SRD source, material-fit coefficient or material name remains; the five material-dependent results carry no number | 89 conditions, all hold | NIST WebBook, CODATA and cryogenic-material data are not stored (THIRD_PARTY_NOTICES.md section 7) |
| V-A06 | Online: transcribed constants are on their live pages, library values agree, and spot states agree with the NIST WebBook (read for comparison only) | PASS | the NASA and CFR values are on their pages; spot states agree with the NIST WebBook within 5e-6 relative (observed agreement at authoring: about 1e-6) | 72 conditions, all hold | NASA, govinfo.gov; NIST WebBook read for comparison only and never stored; table regenerated with CoolProp and compared |

## B. Units and formulas

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-B01 | Units: allowed unit strings, and unit conversions in the CSV outputs agree with independent recomputation | PASS | conversion factors agree to 2e-5 (CSV values carry 6 significant digits) | 244 conditions, all hold | kPa, MPa, g/s, L/h, kJ, kg per MJ, min |
| V-B02 | Pipe pressure loss: isothermal compressible formula against independent Colebrook (bisection) and Haaland | PASS | 0.1 percent for a 0.05 m segment (pressure drop about 0.007 percent of the pressure, so the compressible and Darcy-Weisbach formulas must coincide); 2 percent for 6 m (compressibility changes the result by about half the relative pressure drop, here under 1 percent) | 6 conditions, all hold |  |
| V-B03 | Choked and subsonic flux formulas | PASS | equal to 1e-12 (same equations, written independently) | 13 conditions, all hold |  |
| V-B04 | Radiation and gas-conduction formulas against limiting cases (support conduction is not modelled) | PASS | limiting cases to 1e-6 to 1e-12 (closed-form identities) | 7 conditions, all hold |  |
| V-B05 | Cooldown: liquid per megajoule from the verified enthalpies; the metal heat is unavailable | PASS | to 1e-5 | 5 conditions, all hold |  |
| V-B06 | Unavailable results: contraction, support conduction and metal cooldown heat are never calculated or defaulted | PASS | each unavailable result has no number, a registered unresolved input and its equation; totals are radiation plus gas conduction | 21 conditions, all hold |  |
| V-B07 | Joule-Thomson drop consistent with the integral of the tabulated coefficient | PASS | ratio between 0.98 and 1.15: the 300 K coefficient integral neglects that mu_JT rises as the gas cools, so the true drop is slightly larger; a ratio below 1 or far above would indicate an error | 1 conditions, all hold |  |
| V-B08 | Trapped-liquid pressure rise and time to threshold | PASS | slopes between 1.0 and 2.5 MPa/K (the isochore is nearly linear at about 1.7 MPa/K) | 9 conditions, all hold |  |
| V-B09 | Oxygen-deficiency formula | PASS | to 1e-5 | 25 conditions, all hold |  |

## C. Mass flow and pressure budget

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-C01 | Mass-flow continuity in the budget rows (v rho A equals the illustrative flow) | PASS | equal to 3e-5 (6-digit CSV values) | 18 conditions, all hold |  |
| V-C02 | Pressure chain arithmetic: pressure after each row equals pressure before minus loss; regulators land on their set pressures | PASS | each row to within 2e-4 MPa (the CSV prints 6 significant digits of a 20 MPa value) | 43 conditions, all hold |  |
| V-C03 | Zone totals equal the sum of the included rows, and all-zone equals the sum of the zones | PASS | to 2e-5 | 14 conditions, all hold |  |
| V-C04 | Low, nominal and high cases are ordered for every included passive row | PASS | low <= nominal <= high | 16 conditions, all hold | controlled rows are excluded: their drop falls as upstream losses rise |
| V-C05 | Unresolved rows carry no value and are excluded from totals; included rows have a value | PASS | all conditions hold | 22 conditions, all hold |  |
| V-C06 | Sensitivity table reproduces the reference budget and moves in the expected direction | PASS | all conditions hold | 35 conditions, all hold |  |
| V-C07 | Regulator envelope: choked flag, flux and required area are consistent | PASS | all conditions hold | 85 conditions, all hold |  |

## D. Parameter bounds and output sanity

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-D01 | Every numeric parameter lies within its stated bounds; bounds are ordered; sweeps parse | PASS | each value within [bound_min, bound_max]; emissivities and accommodation in (0, 1] | 239 conditions, all hold | bounds are physical limits, not tuned to the results |
| V-D02 | Output sanity: totals equal their parts, scenario order, shares, signs | PASS | all conditions hold | 56 conditions, all hold |  |

## E. Tags, diagrams and schedules

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-E01 | Tags are unique, well formed and in the right area; schedules do not overlap | PASS | all conditions hold | 149 conditions, all hold |  |
| V-E02 | Diagram tags equal the schedule flags in both directions, by system and drawing | PASS | diagram tags == flagged tags of the system | 8 conditions, all hold |  |
| V-E03 | Diagram line IDs equal the line-list flags in both directions | PASS | all conditions hold | 4 conditions, all hold |  |
| V-E04 | Every diagram has the banner in its title and body, and current SVG and PNG renders exist | PASS | all conditions hold | 163 conditions, all hold | SVG and PNG were rendered with @mermaid-js/mermaid-cli 11.4.2 |
| V-E05 | Numbers in the diagrams equal the calculated values | PASS | each marked value equals the formatted calculated value and appears in the drawing text | 16 conditions, all hold |  |
| V-E06 | Line lists agree with the calculations and the budget | PASS | all conditions hold | 16 conditions, all hold |  |
| V-E07 | Schedules, instruments and line lists reference each other correctly | PASS | all conditions hold | 259 conditions, all hold |  |
| V-E08 | Every tag, line and station in the documents exists | PASS | all conditions hold | 31 conditions, all hold |  |
| V-E09 | Boundary-condition and station tags exist | PASS | all conditions hold | 22 conditions, all hold |  |
| V-E10 | No size, rating or model is given in the schedules | PASS | all conditions hold | 317 conditions, all hold |  |

## F. Requirement traceability

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-F01 | Traceability matrix is well formed: unique IDs, real tags and files, registered verification IDs | PASS | all conditions hold | 345 conditions, all hold |  |
| V-F02 | Hazards and requirements cross-reference in both directions | PASS | all conditions hold | 183 conditions, all hold |  |
| V-F03 | Unresolved inputs: register, missing-inputs file and design basis agree; every UI reference exists | PASS | all conditions hold | 31 conditions, all hold |  |
| V-F04 | Status rules: MET IN CONCEPT has verification; OPEN names unresolved inputs or decisions | PASS | all conditions hold | 62 conditions, all hold |  |

## G. Assumptions

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-G01 | Every AS and IL ID used is registered in DESIGN_BASIS.md section 5, and every registered ID is used | PASS | all conditions hold | 100 conditions, all hold |  |
| V-G02 | Class labelling: each register row has a class, a source and the right kind of source | PASS | all conditions hold | 432 conditions, all hold |  |

## H. Missing inputs and scope guards

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-H01 | Unresolved inputs have no value, are registered once, and have a missing-inputs entry | PASS | all conditions hold | 32 conditions, all hold |  |
| V-H02 | Calculations refuse unresolved inputs and invalid registrations | PASS | MissingInputError, ValueError and KeyError are raised | 5 conditions, all hold |  |
| V-H03 | Outputs for unresolved quantities are blank or flagged, never numbers | PASS | all conditions hold | 13 conditions, all hold |  |
| V-H04 | Scope and claim guards: out-of-scope fluids only as exclusions; no compliance, certification or approval claims | PASS | all conditions hold | 8 conditions, all hold |  |

## I. Deterministic regeneration

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-I01 | Regeneration in clean directories is byte-identical to the committed outputs and to itself | PASS | 13 files identical (SHA256 digest); two runs with different PYTHONHASHSEED | 28 conditions, all hold |  |
| V-I02 | verified_properties.csv covers every dataset of generate_verified_properties.py and nothing else | PASS | all conditions hold | 576 conditions, all hold |  |

## J. Hygiene and claims

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-J01 | No private paths, secrets or e-mail addresses in any file of the folder | PASS | all conditions hold | 492 conditions, all hold | validate_design.py holds the patterns and is skipped |
| V-J02 | Every document carries the status banner near its top | PASS | all conditions hold | 9 conditions, all hold |  |
| V-J03 | Only expected file types; no standard, PDF or archive is stored | PASS | all conditions hold | 47 conditions, all hold |  |

## K. Repository integrity

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-K01 | Existing repository files are unchanged (only the root README link and the NOTICE.md section may change) | PASS | only README.md and NOTICE.md modified; new files only under 09_High_Pressure_Cryogenic_Systems/ (compared with origin/main) | 48 conditions, all hold | 08_Fluid_Test_Rig_Design, the CFD, Mechanical, LS-DYNA, SQL, report and presentation files are unchanged |
| V-K02 | The root README and NOTICE.md changes are additions only | PASS | all conditions hold | 5 conditions, all hold |  |

## L. Numbers quoted in documents

| ID | Check | Result | Expected | Actual | Note |
| --- | --- | --- | --- | --- | --- |
| V-L01 | Numbers quoted in the documents equal the calculated values | PASS | each marked number equals the formatted headline value | 117 conditions, all hold |  |

## Mutation tests: do the checks fail when a source value or an important output is corrupted?

Each test copies this folder and the three repository files it reads to a temporary directory, corrupts one thing on purpose, runs every check, and requires the listed checks to FAIL. Nothing in the real folder is touched.

| # | Corruption | Must fail | Failed | Detected |
| --- | --- | --- | --- | --- |
| 1 | Change the CFD inlet temperature M002 in the master register copy (300 K to 310 K) | V-A01 | V-A01 | YES |
| 2 | Raise the tabulated N2 density at 300 K and 1 atm by 5 percent | V-A04 | V-A04, V-C01, V-I01, V-L01 | YES |
| 3 | Set the molar gas constant to 8.4 | V-A03 | V-A03, V-A04, V-B04, V-I01, V-L01 | YES |
| 4 | Re-insert an uncleared NIST cryogenic-material fit coefficient into verified_constants.csv | V-A05, V-A03 | V-A03, V-A05 | YES |
| 5 | Multiply one nominal budget loss (B19 delivery pipe friction) by 1.5 in pressure_budget.csv | V-C03, V-I01 | V-C02, V-C03, V-I01 | YES |
| 6 | Put a contraction number into the unavailable thermal-contraction register | V-A05, V-I01 | V-A05, V-I01 | YES |
| 7 | Silently default a support-conduction value in the heat-leak table | V-A05, V-I01 | V-A05, V-I01 | YES |
| 8 | Alter the CoolProp copyright line in THIRD_PARTY_NOTICES.md | V-A05 | V-A05 | YES |
| 9 | Double the S1 nominal heat-leak total | V-D02, V-I01 | V-B01, V-B06, V-D02, V-I01 | YES |
| 10 | Change the K of a bend in calculations.py without regenerating the outputs | V-I01 | V-I01, V-L01 | YES |
| 11 | Delete the FLT-301 row from the equipment schedule | V-E02 | V-E02, V-E07, V-E08 | YES |
| 12 | Remove the banner from the cryogenic P&ID source | V-E04 | V-E04 | YES |
| 13 | Change a calculated temperature shown on the GN2 PFD label (271.7 K to 281.7 K) | V-E05 | V-E05 | YES |
| 14 | Put a value into the unresolved input UI-01 | V-H01 | V-G02, V-H01, V-I01 | YES |
| 15 | Remove an unresolved input from the missing-inputs register | V-H01, V-F03 | V-F03, V-H01, V-I01 | YES |
| 16 | Point a requirement at a verification check that does not exist | V-F01 | V-F01 | YES |
| 17 | Use an unregistered assumption ID in a CSV | V-G01 | V-G01, V-I01 | YES |
| 18 | Push an emissivity outside (0, 1] | V-D01 | V-D01, V-I01 | YES |
| 19 | Edit a number quoted in a document | V-L01 | V-L01 | YES |
| 20 | Put a private path in a document | V-J01 | V-J01 | YES |
| 21 | Add a size and rating to an equipment schedule row | V-E10 | V-E10 | YES |
| 22 | Add a compliance claim to a document | V-H04 | V-H04 | YES |

## Tests not performed, and why

- **Solver runs.** Fluent, Mechanical, LS-DYNA and the SQL import were not run, by design. No CFD or finite-element result is reused: the existing models cover air below 1 atm and Inconel 718 at 293 to 673 K only.
- **Independent verification of the nitrogen table.** The data are checked for internal consistency (ideal-gas limit, Clapeyron relation, isotherm against isobars, monotonic isochores) and, with `--online`, against the live NIST WebBook (read for comparison only, never stored) and a fresh CoolProp run. They were not checked against a second independent equation of state or against measurements.
- **Material-property values.** None are held (UI-34, UI-35), so none can be tested. The five dependent results are UNAVAILABLE and are tested only for the absence of numbers and defaults (V-A05, V-B06).
- **Validation against experiment or a real system.** None exists. The numbers are screening values for placeholder assumptions.
- **Relief-device sizing, vessel and piping integrity, stress margins, two-phase and transient behaviour, plume dispersion.** Not calculated (`CALCULATION_METHOD.md` section 7); there is nothing to test.
- **Standards compliance.** Not claimed, so not tested. The standards were read in part or only as listings (`DESIGN_BASIS.md` section 7).
- **Python 3.9 to 3.12.** The code was written for Python 3.9 or later and run with Python 3.13 only; no other interpreter was available.
- **Mermaid rendering from a clean machine.** The SVG and PNG files were rendered once with mermaid-cli 11.4.2; validation checks that they exist, carry the banner and show the current tags and numbers, but does not re-render them.

