# Validation report

Conceptual educational design. This report is written by `validate_design.py`; do not edit it by hand.
It has no timestamps, so a rerun on unchanged inputs reproduces it exactly.

**What is validated.** Arithmetic, internal consistency, traceability of sourced values, consistency between the
diagrams and the schedules, and reproducibility of the calculation script. Independent re-calculations use different
formulations from `calculations.py` (Haaland instead of Colebrook-White for friction, the ISO loss-coefficient form for the
orifice permanent loss, the momentum balance for the expansion, hand arithmetic for the flow basis).

**What is not validated.** No physical test, vendor datasheet or qualified-engineer review was available. The
generic loss coefficients, the filter and flow-element allocations and the routing are assumptions (register:
DESIGN_BASIS.md section 5). A passing check here shows the document set is self-consistent and reproducible, not that the
design is correct for a real facility. A check that failed would have been investigated, not relaxed.


## Summary

| Result | Checks |
|---|---:|
| PASS | 56 |
| FAIL | 0 |
| SKIP | 0 |

## Checks

| ID | Group | Check | Result | Expected | Actual | Note |
|---|---|---|---|---|---|---|
| V-A01 | Inputs | Every input with a master-register ID equals the register value (28 inputs) | PASS | 0 mismatches | 0 mismatches |  |
| V-A02 | Inputs | Every file-sourced input appears in its cited source file (18 inputs) | PASS | 0 missing | 0 missing |  |
| V-A03 | Inputs | Every input has a verifiable source (register ID, or a cited file that exists) | PASS | 0 orphans | 0 |  |
| V-A04 | Inputs | Wall-temperature expectations for TE-111/112/113 reproduce the CFD axial profile | PASS | within 0.06 K | 470.22 / 539.25 / 561.16 K |  |
| V-B01 | Flow | Volumetric flow reproduced independently and matches the quoted 7.38 L/s | PASS | 7.38274 L/s | 7.38274 L/s |  |
| V-B02 | Flow | Mass flow reproduced independently (rho = p/(R T)) | PASS | 8.686472 g/s | 8.686472 g/s |  |
| V-B03 | Flow | Flow continuity: rho_in V_in A = rho_out V_out A, with V_out matching the script | PASS | V_out 28.8995 m/s | 28.8995 / 28.8995 |  |
| V-B04 | Flow | Reynolds number is turbulent and within 0.2 % of the CFD; Mach numbers below 0.1 | PASS | 29958 (CFD), Ma < 0.1 | Re 29958, Ma 0.0677 / 0.0751 |  |
| V-B05 | Flow | All 12 flow cross-checks against the CFD and frozen baseline are within tolerance | PASS | 0 outside tolerance | 0 |  |
| V-B06 | Flow | Heating acceleration term G^2(1/rho_out - 1/rho_in) reproduced and within 1 % of the CFD value | PASS | 149.31 Pa (CFD) | 149.296 Pa |  |
| V-B07 | Flow | The 0.9 and 1.1 flow factors of the duty envelope are the CFD velocity cases (21.15 and 25.85 m/s) | PASS | 0.9 / 1.1 | 0.900000 / 1.100000 |  |
| V-B08 | Interface | Simple free-growth estimate agrees with the Mechanical LC1 free growth (M085) within 1 % | PASS | within 1 % | 0.83 % |  |
| V-B09 | Interface | E A alpha dT estimate of the full-restraint force agrees with the LC2 reaction (M091) within 1 % | PASS | within 1 % | -0.09 % |  |
| V-C01 | Budget | Budget rows sum to the TOTAL row for every candidate and every case (low, nominal, high) | PASS | sums agree to rounding | 0 disagreements |  |
| V-C02 | Budget | low <= nominal <= high for every budget row | PASS | 0 violations | 0 |  |
| V-C03 | Budget | Candidate summary totals equal the budget and its group columns add up to the nominal total | PASS | 0 disagreements | 0 |  |
| V-C04 | Budget | Stream-table closure: test-article static drop = 438.13 Pa, exit static = 0, blower rise = sum of losses | PASS | 438.13 / 0 / 1277.64 | 438.13 / 0.00 / 1277.63 |  |
| V-C05 | Budget | CFD test-article drop appears exactly once, converted to total pressure, bracketed by CFD p0 loss and static drop | PASS | 363.48 Pa in (334.61, 438.13) | 363.48 |  |
| V-C06 | Budget | Friction rows (28) reproduced with the Haaland equation within 4 % in f and 5 % in dp | PASS | 0 outside | 0 |  |
| V-C06b | Budget | Pipe lengths in line_list.csv equal the lengths used by the friction rows (line-loss aggregation) | PASS | all lines agree | 0 disagree |  |
| V-C07 | Budget | Orifice sizing round-trips to the design mass flow; permanent loss matches the ISO loss-coefficient form | PASS | agree to 1e-6 | 0 disagree |  |
| V-C08 | Budget | Expansion loss equals 0.5 rho (V1 - V2)^2 and the static rise across it equals rho V2 (V1 - V2) | PASS | 281.91 Pa loss, 107.39 Pa rise | 281.91 / 107.39 |  |
| V-C09 | Budget | Sensitivity table: multiplier scan is monotonic, x1 gives zero change and x3 adds twice the unsupported share | PASS | x3 adds 957.00 Pa | 956.96 |  |
| V-C10 | Duty | Blower specification follows the affinity laws (Q/0.9, P/0.81) from the upper warm-ambient high-loss point | PASS | 2722 Pa, 9.41 L/s | 2722 Pa, 9.41 L/s |  |
| V-C11 | Duty | The recommended 50 mm bore has the lowest nominal fan pressure of the candidates that pass the screening | PASS | 50 mm | 50 mm (passing: 50, 80) |  |
| V-C12 | Duty | Candidate line velocities and Reynolds numbers reproduced independently | PASS | agree to 1e-6 | 0 disagree |  |
| V-C13 | Budget | Every row relying on generic or vendor-dependent data is flagged with an assumption ID (37.5 % of the 50 mm nominal budget) | PASS | all rows classified | 0 unclassified |  |
| V-D01 | Tags | All equipment, instrument and line tags follow the documented tag syntax | PASS | 0 violations | 0 |  |
| V-D02 | Tags | Tags are unique across the equipment schedule and instrument index; line IDs are unique | PASS | 0 duplicates | 0 |  |
| V-D03 | Tags | Every tag referenced by the line list, schedules and budget exists in a schedule | PASS | 0 unknown | 0 |  |
| V-D04 | Diagrams | PFD and P&ID tags and line IDs match the schedules and line list exactly (both directions) | PASS | no differences | PFD []; P&ID []; lines [] |  |
| V-D05 | Diagrams | PFD stream labels (7) equal the stream table (T, static gauge pressure, mass flow) | PASS | all labels agree | 0 disagree |  |
| V-D06 | Diagrams | The heat input quoted on the PFD equals the CFD heat transfer (M038) | PASS | 602.755 W | present |  |
| V-D07 | Diagrams | Diagrams are labelled conceptual and not approved for construction; the P&ID carries no sizes or ratings | PASS | labelled, 0 sizes | labelled=True, sizes=[] |  |
| V-D08 | Diagrams | Rendered SVG and PNG exports exist, the SVGs are plain text and contain every tag of their .mmd source | PASS | 4 exports valid | 0 problems |  |
| V-D09 | Tags | Numbers quoted in the equipment schedule and instrument index (29) agree with the calculation results | PASS | within 0.5 % | 0 disagree |  |
| V-D10 | Tags | Line-list pressures equal the stream-table station values | PASS | 0 disagreements | 0 |  |
| V-D11 | Assumptions | Every assumption ID used is registered in DESIGN_BASIS.md s.5 and every registered one is used (18 IDs) | PASS | 0 unregistered, 0 unused | unregistered [], unused [] |  |
| V-D12 | Tags | No control or throttling valve exists, nothing valve-like is in the discharge line, and HV-101 is the only valve on the P&ID | PASS | none; HV-101 only | control valves []; discharge []; P&ID valves ['HV-101'] |  |
| V-D13 | Diagrams | Hardwired trips: ZSO-101, PT-101, PDSL-102, TSHH-120 and HS-101 act on ES-101, ES-101 acts on the drive and heater power, and the independent safety inputs go to ES-101 only | PASS | wired as above | missing []; actions []; not ES-101 only []; TE-120 shared False |  |
| V-E01 | Traceability | Requirements (34) have unique IDs, complete fields, valid types and honest status | PASS | 0 problems | 0 |  |
| V-E02 | Traceability | Every register ID, assumption ID and file cited as a requirement source exists | PASS | 0 missing | 0 |  |
| V-E03 | Traceability | Every tag named in 'implemented_in' exists in a schedule | PASS | 0 unknown | 0 |  |
| V-E04 | Traceability | Every check ID cited as verification exists in this script (34 IDs cited) | PASS | 0 unknown | 0 |  |
| V-F01 | Documents | All 22 required deliverables are present | PASS | 0 missing | 0 |  |
| V-F02 | Hygiene | No private paths, secrets, e-mail addresses, vendor names or prices in the new files | PASS | 0 hits | 0 |  |
| V-F03 | Documents | Key calculated values quoted in the documents (19) match the calculation results | PASS | all present | 0 missing |  |
| V-F04 | Documents | README states the chronology (follow-on, not part of the February to May 2025 internship) and that the design is not approved for construction | PASS | present | present |  |
| V-F05 | Documents | Every narrative document says it is conceptual; the heater subsystem section says nothing is inferred from the heat flux | PASS | all | missing in []; heater note True |  |
| V-F06 | Hygiene | Both scripts compile | PASS | compiles | ok |  |
| V-F07 | Hygiene | Only 08_Fluid_Test_Rig_Design/ and README.md differ from origin/main | PASS | 0 other files | 0: [] |  |
| V-G01 | Reproducibility | Clean-directory rerun reproduces the 8 committed outputs byte for byte | PASS | 0 differences | 0:  |  |
| V-G02 | Reproducibility | Two runs give identical output and the run changes no file anywhere in the repository | PASS | identical, repository unchanged | diff []; repository changed=False |  |
| V-G03 | Reproducibility | Invalid dimensions and non-physical inputs are rejected (7 negative tests); valid inputs are accepted | PASS | all rejected | 0 accepted wrongly |  |
| V-G04 | Reproducibility | A missing input raises KeyError instead of being substituted | PASS | KeyError | KeyError |  |
| V-G05 | Reproducibility | calculations.py refuses to write inside the repository outside 08_Fluid_Test_Rig_Design | PASS | refused | exit 1 |  |

## Preserved observations (not failures)

- **Mass flow against the CFD.** The circular-tube mass flow (8.686 g/s) is 0.28 % above the CFD flux (8.662 g/s). The CFD
  mesh is a 48-sided facetted bore with 0.285 % less flow area, as documented in the CFD results. The design uses the
  circular-tube value, because the rig has a round bore.
- **Outlet Reynolds number.** The Sutherland viscosity gives 25,657 at the outlet against the CFD value of 25,545 (0.44 %),
  because the CFD uses tabulated viscosity. Within the 1 % tolerance of the check.
- **Test-article loss bookkeeping.** The budget converts the CFD static drop (438.13 Pa) to a total-pressure loss with
  1-D velocity pressures (363.48 Pa). The CFD area-weighted total-pressure difference is 334.61 Pa. The budget keeps the
  larger value as nominal and brackets the range in the low and high cases (check V-C05). The repository's own note that
  the CFD total pressure is "not combined with or substituted for the static drop" is respected: the static drop remains
  the source and the CFD total pressure is used only as a cross-check bound.
- **Friction-factor method.** Colebrook-White and Haaland differ by up to 4 % by construction. The check tolerance is set
  to that known spread and is not a statement about the CFD friction factor (fully developed f = 0.02163 in the heated duct).
- **Not checked by this script.** Standards were verified against public catalogue listings by web search while writing
  DESIGN_BASIS.md; the standards themselves are paywalled and were not read. Any use of them needs the purchased text.

## How to run

```
python calculations.py             # regenerates the CSV/JSON outputs
python validate_design.py          # runs every check, rewrites this report, exit code 1 on any failure
python validate_design.py --no-rerun
```
