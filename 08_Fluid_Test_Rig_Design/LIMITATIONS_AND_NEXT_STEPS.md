# Limitations and next steps

Conceptual and educational design. It is not construction-ready, not certified for pressure service, and not qualified for rocket-engine or launch-pad operations.

## 1. What this design is and is not

It is a traceable concept: a design basis taken from the existing project, a pressure budget that counts the CFD result once, a blower duty specification, two drawings consistent with their schedules, a preliminary hazard review, and a validation report. It is not a design for a real facility. No vendor data, test data or qualified-engineer review has been used, and no commercial component, rating, price or availability is stated.

## 2. Principal limitations

1. **The inputs are re-analysis values.** Every baseline parameter is class B (`BASELINE_PARAMETERS.md`); the original internship data were not retained and no measured data exist. The CFD is one model; its mesh study shows the static drop moving by 0.2 % (437.09, 438.13, 439.12 Pa), but model-form uncertainty is not quantified.
2. **The test-article loss assumes the CFD boundary conditions.** The CFD has a uniform velocity inlet at 300 K and a pressure outlet. A real adapter gives a different inlet profile and entry-region friction; only the +/-15 % band covers it (AS-10).
3. **About 37 % of the nominal budget rests on generic or vendor-dependent data** (loss coefficients, the filter allocation and the flow-element model). The sensitivity analysis shows the effect, but vendor data may lie outside the ranges used.
4. **Single operating temperature.** The CFD is at 300 K inlet. The blower heats the air by an estimated 2 to 5 K and ambient varies; neither is fed back into the CFD. Humidity is ignored.
5. **Steady state only.** Start-up, heater switch-on, loss-of-flow and cool-down transients are not analysed. The 0.27 K/s heating rate is for the bare tube only.
6. **The heater is not designed.** The 8000 W/m2 and 602.755 W are model values, not a heater rating.
7. **The structural interface is screened, not analysed.** The simple estimates match the existing LC1 and LC2 results, but those results are for the bare tube and do not qualify the new supports, piping, connections or heater.
8. **The standards were not read** and the Crane handbook was not available; titles, editions and scope statements come from public listings, and the loss-coefficient forms from public documentation (`DESIGN_BASIS.md` section 7).
9. **The hazard review is preliminary.** It ranks nothing and is not a HAZOP.
10. **The drawings are conceptual and laid out automatically** by the Mermaid renderer. Membership of the heater boundary is given by the box contents in `PID.mmd`, not by position.
11. **The new folder is not recorded** in `REPOSITORY_STRUCTURE.md`, `GITHUB_CONTENT_AUDIT.md` or `MANIFEST.csv`, which were deliberately left unchanged. The repository's own publication and licensing caveats (`NOTICE.md`) are unchanged and not resolved by this work.
12. **Authorship.** The folder was drafted with AI assistance (Claude Code) at the repository owner's request. The owner should review every number and decision before relying on it.

## 3. Unresolved engineering questions

- What is the blower shut-off pressure, and does it require PSV-101 and a higher design pressure?
- Is the filter allocation (100 Pa clean, 250 Pa loaded) realistic for a filter that protects a 20 mm bore?
- What is the real loss of the line-to-20 mm adapters and instrument spools, and is a diffuser at ADP-102 worth its length (it would remove about 190 Pa, section 6 of `CALCULATION_METHOD.md`)?
- What mixing length does TE-103 need, given an outlet temperature that spans 369 to 553 K?
- What axial travel and stiffness does FC-102 need, and what load does it put on the tube flanges?
- How should thermocouples be mounted under or through the heater?
- What trip setpoints (low differential pressure, over-temperature) are right, given limits that are not set here?
- Does the real inlet adapter change the entry-region friction and heat transfer enough to matter for the comparison with the CFD?
- Is an orifice or a thermal mass flow meter the better primary element once an uncertainty budget is written?

## 4. Items requiring review by a qualified engineer

| Discipline | Items |
| --- | --- |
| Piping | Design pressure and temperature; materials for the hot lines L-106 and L-107; joints; leak-test method and criterion; flexibility analysis; the choice of any code (B31.3 or another) |
| Pressure system | Blower shut-off pressure and the blocked-outlet case; need for, sizing and location of PSV-101; design pressure of every component |
| Electrical | Blower drive, heater supply, wiring and protection ratings, grounding, emergency stop, lock-out |
| Instrumentation and functional safety | Trip architecture and performance level; setpoints and hysteresis; redundancy; the independence of PDSL-102 and TSHH-120 from CS-101; sensor selection and uncertainty budget |
| Mechanical and structural | Supports, guide, loads on the flanges, joint stiffness and travel, modal check, blower mounting |
| Heater subsystem | Everything: construction, power, protection, mounting, insulation, end conduction |
| Facility | Location, ventilation, the position and guarding of the discharge, noise, hot-surface assessment, the jurisdiction and its rules |

## 5. Suggested next steps

1. Obtain vendor data for the blower (curve, shut-off pressure, heating, noise), the filter, the flexible connections and the flow element, and replace the allocations and generic coefficients in `calculations.py`.
2. Write an uncertainty budget for the mass-flow measurement and the energy balance.
3. Run a short CFD or test study of the inlet adapter profile and of the outlet mixing length.
4. Do a flexibility and support analysis with the real layout, including the flange region of the test article and a modal check.
5. Define the heater subsystem and its protection, and then the trip setpoints.
6. Hold a formal hazard study with the facility's engineers and select the applicable codes for the jurisdiction.
7. Write the commissioning procedure: leak test, flow-meter check against the energy balance, and a comparison of the measured differential pressure and wall temperatures with the CFD.

## 6. Reuse

Rerunning `calculations.py` and `validate_design.py` after any change regenerates the outputs and re-checks the document set. A change to an input or assumption changes the numbers quoted in the documents, which `validate_design.py` detects (check V-F03).
