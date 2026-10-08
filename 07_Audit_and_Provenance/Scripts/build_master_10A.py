# -*- coding: utf-8 -*-
"""SECTION 10A - builds MASTER_PROJECT_DATA.csv / .md and MASTER_TRACEABILITY.md from the recomputed master data
(Data/master_data_10A.json, written by master_data_10A.py) plus the re-analysed input definitions and the
cross-document number search (Data/crossdoc_10A.json). RE-ANALYSIS 2026.
Usage: python build_master_10A.py <folder with Data/> <out folder>"""
import os, sys, json, csv, re, collections
sys.dont_write_bytecode = True
D, O = sys.argv[1], sys.argv[2]
M = json.load(open(os.path.join(D, "Data", "master_data_10A.json")))
X = json.load(open(os.path.join(D, "Data", "crossdoc_10A.json")))
NOTICE = ("> **RE-ANALYSIS 2026 — Re-analysed / Assumed / Simulated 2026.** The original Eleation internship files (Feb–May 2025) "
          "were lost. Every value below is a 2026 re-analysis: an input chosen in 2026 (class B), a 2026 hand calculation, or a "
          "2026 ANSYS Student 2026 R1 simulation. No value is recovered internship data, and no experimental or measured data exist.")


def fmt(it):
    v, u, p = it["value"], it["units"], it["parameter"].lower()
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return str(v)
    if isinstance(v, int) or any(k in p for k in ("cells", "nodes", "elements")):
        return "%d" % round(v)
    if float(v).is_integer() and u in ("mm", "K") and it["group"] in ("Geometry", "Structural"):
        return "%g" % v
    if u == "%" or (u == "N" and abs(v) < 1):
        return "%.1e" % v
    if u == "K":
        return "%.3f" % v if ("dt" in p or "through-wall" in p) else "%.2f" % v
    if u == "Pa":
        return "%.0f" % v if abs(v) < 100 else "%.2f" % v
    if u == "W":
        return "%.3f" % v
    if u == "MPa":
        return "%.1f" % v if "yield strength" in p else "%.3f" % v
    if u == "mm":
        return "%.4f" % v
    if u == "mm2":
        return "%.3f" % v
    if u in ("m2", "m3"):
        return "%.7g" % v
    if u == "kN":
        return "%.2f" % v
    if u == "N":
        return "%.1f" % v
    if "lambda" in p:
        return "%.5f" % v
    if "reynolds" in p:
        return "%.0f" % v
    if "first-yield" in p:
        return "%.3f" % v
    if "utilisation" in p:
        return "%.4f" % v
    if "y+" in p:
        return "%.3f" % v
    if "nusselt" in p or "nu_fd" in p:
        return "%.2f" % v
    if "friction" in p or "f_fd" in p:
        return "%.5f" % v
    return "%.6g" % v


rows = []
def row(group, param, value, units, level, case, status, source, result, method, documented="", doc_in="", note=""):
    rows.append({"ID": "", "Group": group, "Parameter": param, "Value": value, "Units": units, "Modelling level": level, "Case": case,
                 "Status": status, "Source file": source, "Source result / case": result, "Method": method, "Documented value": documented,
                 "Documented in": doc_in, "Note": note})


# --- official baseline definition (re-analysed inputs, class B)
BP = "02_Engineering_Calculations/baseline_parameters.json"
IN = "INPUT (re-analysed 2026, class B)"
for p, v, u, src, note in (("Fluid", "air, incompressible ideal gas (rho = p_op/(R T)); cp, mu, k piecewise-linear 250-600 K (Incropera A.4)", "-", "06_Fluent_CFD/FLUENT_SETUP_NOTES.md", "D-009, D-021"),
                           ("Inlet temperature T_in", "300", "K", BP, ""), ("Inlet velocity V_in", "23.5", "m/s", BP, "uniform, normal to the inlet"),
                           ("Inlet turbulence intensity", "4.411 (0.16 Re^-1/8, D_h 20 mm)", "%", "06_Fluent_CFD/FLUENT_SETUP_NOTES.md", "[ASSUMED]; ID collision: called A-020 in the CFD documents, A-020 is 'perfect thermal contact' in ASSUMPTIONS.md"),
                           ("Outlet pressure", "0 Pa gauge at operating pressure 101,325 Pa", "Pa", BP, "pressure outlet; atmospheric pressure never applied as a structural load"),
                           ("Outer-wall heat flux q''", "8000 (uniform); end faces adiabatic", "W/m2", BP, "D-015; inner-wall equivalent 16,000 W/m2"),
                           ("Solid material", "Inconel 718 (VDM 4127 / Special Metals datasheets)", "-", "02_Engineering_Calculations/MATERIAL_PROPERTIES.md", "generic datasheet, not lot-specific (A-018)"),
                           ("Solid density", "8190", "kg/m3", "02_Engineering_Calculations/MATERIAL_PROPERTIES.md", "read back from Fluent in 5B (F-023 fixed in 5A)"),
                           ("Solid conductivity / heat capacity (CFD)", "k(T), cp(T) piecewise-linear 293-673 K (VDM 4127)", "-", "06_Fluent_CFD/FLUENT_SETUP_NOTES.md", "D-026"),
                           ("Young's modulus (FE)", "E(T) VDM table, 204 -> 180 GPa over 20-400 C", "GPa", "08_Structural_Analysis/Materials/MATERIAL_MODEL_7A.md", "D-036"),
                           ("Thermal expansion (FE)", "secant alpha(T) from 70 F, 12.8-14.8 e-6 /K, re-referenced to T_ref by MPAMOD", "1/K", "08_Structural_Analysis/Materials/MATERIAL_MODEL_7A.md", "D-036"),
                           ("Poisson's ratio", "0.294 [ASSUMED]", "-", "08_Structural_Analysis/Materials/MATERIAL_MODEL_7A.md", "in neither datasheet (T-014 / F-011 open)"),
                           ("Yield strength (assessment)", "S_y(T) VDM 4127: 1030 / 1060 / 1040 / 1020 / 1000 MPa at 20 / 100 / 200 / 300 / 400 C, linear, no extrapolation", "MPa", "08_Structural_Analysis/STRUCTURAL_RESULTS.md", "typical values, not minimum-guaranteed; the scalar 1020 MPa in Engineering Data is a lower bound and is NOT used for utilisation (F-037, T-031)"),
                           ("Structural reference temperature T_ref", "300", "K", BP, "D-041; dT = T(x,y,z) - 300 K on the full mapped field"),
                           ("Coupling", "one-way: converged CFD solid temperature -> Mechanical (no structural feedback)", "-", "PROJECT_STATE.md (D-013, D-037)", "flow-area change 0.70 % (Section 2)"),
                           ("CFD final reference mesh", "MEDIUM, 159,840 cells (fine mesh 500,580 cells = verification reference only)", "-", "09_Mesh_Independence/Mesh_Independence_Report.md", "D-034"),
                           ("Temperature transfer", "mesh-based External Data, Manual / Bucket Volume / Shape Functions / Nearest Node (7A)", "-", "07_Thermal_Analysis/THERMAL_MAPPING_NOTES.md", "D-038"),
                           ("Structural final mesh", "mesh B: SOLID186 36 x 5 x 130 (bias 4), 108,252 nodes / 23,400 elements", "-", "08_Structural_Analysis/Mesh_Study/STRUCTURAL_MESH_COMPARISON.md", "D-040, D-056"),
                           ("LC1 support (free expansion)", "3 outer-ring nodes on the inlet face (0/120/240 deg), U_theta = U_z = 0 in CS_DUCT_CYL; statically determinate", "-", "08_Structural_Analysis/Boundary_Conditions/BOUNDARY_CONDITIONS_7A.md", "D-042"),
                           ("LC2 support = S1 (baseline)", "U_z = 0 on both complete end faces; 3 mid-span outer nodes U_theta = 0; radial free; ends free to sway, end rotation held (guided column, K = 1)", "-", "08_Structural_Analysis/Boundary_Conditions/BOUNDARY_CONDITIONS_7A.md", "D-043"),
                           ("Support scenario S2", "U_z = U_theta = 0 on every node of both end faces (ends laterally held and rotation held: clamped-clamped, K = 0.5)", "-", "08_Structural_Analysis/Buckling/BUCKLING_RESULTS.md", "8A LC2NS; sensitivity only"),
                           ("Support scenario S3", "inlet face U_z = U_theta = 0 (clamped); outlet deformable remote point on the axis, U = 0, rotations free (pinned); K = 0.699", "-", "10_Parametric_Study/Results/SUPPORT_SENSITIVITY_RESULTS.md", "9B-2; sensitivity only")):
    row("Baseline definition", p, v, u, IN if p not in ("Coupling", "CFD final reference mesh", "Temperature transfer", "Structural final mesh") else "MODEL DECISION (2026)", "P00",
        "INPUT" if "reference mesh" not in p and "Structural final mesh" not in p else "DECISION", src, "P00", "definition", note=note)

# --- recomputed items
for it in M["items"]:
    row(it["group"], it["parameter"], fmt(it), it["units"], it["level"], it["case"], it["status"], it["source"], it["case"], it["method"],
        documented=("" if it["documented"] is None else (("%.6g" % it["documented"]) if isinstance(it["documented"], float) else str(it["documented"]))),
        doc_in=it["documented_in"], note=it["note"])

# --- interpretation rows (text, derived from the verified values)
row("Buckling", "Buckling interpretation (all scenarios)", "lambda1 is a LINEAR EIGENVALUE bifurcation indicator of an ideal, perfectly straight tube with idealised supports; no imperfection, no plasticity, no large deflection; it is NOT a collapse load and NOT a factor of safety", "-",
    "INTERPRETATION", "all", "INTERPRETATION", "08_Structural_Analysis/Buckling/BUCKLING_RESULTS.md", "8A section 7", "definition of the method")
row("Buckling", "S1 governing mechanism (idealised model)", "lambda1 1.108 < first-yield factor 1.730: elastic bifurcation of the idealised S1 model comes before first yield (stability-limited); lambda1 this close to 1 means the idealised model is close to instability", "-",
    "INTERPRETATION", "P00 S1", "INTERPRETATION", "master rows S1 lambda1 and first-yield factor", "P00", "comparison of two verified factors")
row("Buckling", "S2 / S3 governing mechanism (idealised model)", "first-yield factor 1.730 < lambda1 (S3 2.232, S2 4.300): first yield (or inelastic buckling, 8A Johnson 1.41 / 1.58) comes before the elastic bifurcation", "-",
    "INTERPRETATION", "P00 S2, S3", "INTERPRETATION", "master rows S2/S3 lambda1 and first-yield factor", "P00", "comparison of two verified factors")
row("Parametric", "Cases with lambda1 < 1 (S1)", "Q03 (0.98834) and T01 (0.94497): LC2 static stress = pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load level. V01 (1.00307) is 0.31 % above 1", "-",
    "INTERPRETATION", "Q03, T01, V01", "INTERPRETATION", "10_Parametric_Study/Results/PARAMETRIC_STRUCTURAL_RESULTS.md", "9B-2", "Part I label")

for k, r in enumerate(rows, 1):
    r["ID"] = "M%03d" % k
cols = list(rows[0].keys())
with open(os.path.join(O, "MASTER_PROJECT_DATA.csv"), "w", newline="", encoding="utf-8") as fh:
    fh.write("# RE-ANALYSIS 2026 - Section 10A MASTER PROJECT DATA (single source of truth). Re-analysed / Assumed / Simulated 2026; "
             "no value is recovered internship data. Status: VERIFIED = recomputed from raw solver/report files in 10A and equal to the documented value; "
             "CROSS-CHECKED = confirmed by an independent second computation; REPORTED = taken from the section result file (reason in Method); "
             "INPUT / DECISION = re-analysed input or model decision; INTERPRETATION = statement derived from verified values.\n")
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
json.dump(rows, open(os.path.join(D, "Data", "master_rows_10A.json"), "w"), indent=1)
print("rows", len(rows), collections.Counter(r["Status"] for r in rows))
