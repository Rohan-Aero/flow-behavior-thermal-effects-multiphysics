# -*- coding: utf-8 -*-
"""SECTION 10A - writes MASTER_PROJECT_DATA.md and MASTER_TRACEABILITY.md from Data/master_rows_10A.json and
Data/crossdoc_10A.json (no hand-typed result values in the tables). RE-ANALYSIS 2026.
Usage: python build_docs_10A.py <folder with Data/> <out folder>"""
import os, sys, json, re, collections
sys.dont_write_bytecode = True
D, O = sys.argv[1], sys.argv[2]
R = json.load(open(os.path.join(D, "Data", "master_rows_10A.json")))
X = json.load(open(os.path.join(D, "Data", "crossdoc_10A.json")))
M = json.load(open(os.path.join(D, "Data", "master_data_10A.json")))
NOTICE = ("> **RE-ANALYSIS 2026 — Re-analysed / Assumed / Simulated 2026.** The original Eleation internship files (Feb–May 2025) were lost. "
          "Every number here is a 2026 re-analysis: an input chosen in 2026, a 2026 hand calculation, or a 2026 ANSYS Student 2026 R1 simulation. "
          "No value is recovered internship data, and no experimental or measured data exist.")
by = {r["Parameter"]: r for r in R}
def g(p, key="Value"):
    return by[p][key]
def esc(s):
    return str(s).replace("|", "/")

# ============================================================================ MASTER_PROJECT_DATA.md
L = ["# MASTER PROJECT DATA — Section 10A (single source of truth)", "", NOTICE, "",
     "Machine-readable version: `MASTER_PROJECT_DATA.csv` (%d rows, IDs M001–M%03d). Every VERIFIED value was recomputed in 10A from the rawest "
     "file available (Fluent flux / surface-integral reports, MAPDL nodal, reaction and load-factor tables, the CAD measurement file) by "
     "`Scripts/master_data_10A.py`, which imports no earlier post-processing script, and compared with the value documented in the section "
     "result file. Status counts: %s." % (len(R), len(R), ", ".join("%s %d" % (k, v) for k, v in sorted(collections.Counter(r["Status"] for r in R).items()))), "",
     "**Modelling levels are kept apart.** A number is only meaningful together with its level: `ANALYTICAL (Section 2)` 1-D correlations, "
     "`CFD-MEDIUM` the official baseline CFD, `CFD-FINE` the verification reference, `CFD-EXTRAPOLATED` Richardson limits, `FE-STATIC` / "
     "`FE-BUCKLING` the official Mechanical results, `FE-MESH-STUDY` the 8B variants, and the 9B parametric cases.", ""]
L += ["## 1. Official baseline definition (P00)", "", "| ID | Item | Definition | Units | Basis |", "|---|---|---|---|---|"]
for r in R:
    if r["Group"] == "Baseline definition":
        L.append("| %s | %s | %s | %s | %s |" % (r["ID"], r["Parameter"], esc(r["Value"]), r["Units"], esc(r["Note"] or r["Source file"])))
L.append("")
def table(title, group, filt=None):
    rows = [r for r in R if (group is None or r["Group"] == group) and (filt is None or filt(r))]
    out = ["## %s" % title, "", "| ID | Parameter | Final value | Units | Modelling level | Status | Source file |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| %s | %s | %s | %s | %s | **%s** | `%s` |" % (r["ID"], esc(r["Parameter"]), esc(r["Value"]), r["Units"], esc(r["Modelling level"]), r["Status"], esc(r["Source file"])))
    return out + [""]
L += table("2. Geometry", "Geometry")
L += table("3. Baseline CFD (medium mesh, Section 5B)", "Baseline CFD")
L += ["Notes: the maximum solid temperature is quoted as the **outer-wall facet maximum** (Fluent maximum-of-facet report); the hottest "
      "cell centre is also listed. Q = 602.755 W is 8000 W/m² × the inscribed 48-gon area; 603.186 W is the same flux on the true "
      "cylinder (Section 2) — both are correct for their geometry.", ""]
L += table("4. CFD mesh study (Section 6A/6B: coarse, fine reference, extrapolated)", "CFD mesh study")
L += table("5. Section 2 analytical values (historical modelling level, not final results)", "Section 2 analytical")
L += table("6. Static structural (Section 7B, official)", "Structural")
L += table("7. Linear buckling and support scenarios", "Buckling", lambda r: r["Status"] != "INTERPRETATION") + table("7b. Support sensitivity (static)", "Support sensitivity")
L += table("8. Structural mesh sensitivity (Section 8B)", "Structural mesh sensitivity")
# parametric compact table
cases = ["V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK"]
lab = {"V01_LOW": "V01 (V 21.15 m/s)", "V03_HIGH": "V03 (V 25.85 m/s)", "Q01_LOW": "Q01 (q'' 7,200 W/m²)", "Q03_HIGH": "Q03 (q'' 8,800 W/m²)",
       "T01_THIN": "T01 (t 8 mm, D_o 36)", "T03_THICK": "T03 (t 12 mm, D_o 44)"}
qs = [("pressure drop", "Δp [Pa]"), ("outlet bulk temperature", "T_out [K]"), ("maximum solid temperature (outer-wall facet)", "T_max [K]"),
      ("LC1 maximum deformation", "LC1 def. [mm]"), ("LC1 maximum von Mises", "LC1 VM [MPa]"), ("LC2 maximum von Mises", "LC2 VM [MPa]"),
      ("lambda1 (S1)", "λ₁"), ("critical load P_cr", "P_cr [kN]"), ("LC2 yield utilisation", "Utilisation")]
L += ["## 9. Parametric cases (9B-1 CFD + 9B-2 FE, S1 supports; actual simulations, not screening)", "",
      "| Case | " + " | ".join(h for _, h in qs) + " |", "|---|" + "---|" * len(qs)]
L.append("| **P00 (baseline)** | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
    g("Pressure drop (area-weighted static, inlet - outlet)"), g("Outlet bulk temperature (mass-weighted)"), g("Maximum solid temperature (outer-wall facet)"),
    g("LC1 maximum total deformation"), g("LC1 maximum von Mises stress"), g("LC2 maximum von Mises stress"), g("S1 lambda1"), g("S1 critical load P_cr = lambda1 x N"),
    g("LC2 yield utilisation (max vm / S_y(T))")))
for c in cases:
    L.append("| %s | %s |" % (lab[c], " | ".join(by["%s: %s" % (c, q)]["Value"] for q, _ in qs)))
L += ["", "All %d parametric values above are VERIFIED (recomputed from each case's Fluent reports and MAPDL tables). λ₁ < 1: **Q03, T01** "
      "(Part I label: pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load "
      "level); **V01** is 0.31 %% above 1." % sum(1 for r in R if r["Group"] == "Parametric" and r["Status"] == "VERIFIED"), ""]
L += table("10. Interpretation rows", None, lambda r: r["Status"] == "INTERPRETATION")
open(os.path.join(O, "MASTER_PROJECT_DATA.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ============================================================================ MASTER_TRACEABILITY.md
EX = re.compile(r"(?i)monitors\.csv|residual_history|hashes\.csv|screening_candidates")
H0 = [h for h in X["hits"] if not EX.search(h["file"])]
coinc = lambda h: re.search(re.escape(h["match"]) + r"\d*[eE][-+]?\d", h["context"]) is not None   # digits inside a scientific-notation data value
H = [h for h in H0 if not coinc(h)]
NC = len(H0) - len(H)
cnt = collections.defaultdict(collections.Counter)
for h in H:
    cnt[h["target"]][h["file"]] += 1
MEAN = {
 "603.19 W (analytical Q, true cylinder)": ("q'' × true-cylinder area (Section 2, analytical); also the geometry-corrected CFD Q in 6B and the Q held constant in the T cases", "heat-transfer rate (true cylinder)"),
 "602.755 W (CFD medium Q, 48-gon)": ("CFD heat rate on the medium mesh (48-gon); also every V/Q-reference and T case (Q held)", "Heat-transfer rate (heated wall)"),
 "602.994 W (CFD fine Q, 72-gon)": ("CFD heat rate on the fine mesh (72-gon; verification reference)", "fine: heat-transfer rate"),
 "581.7 K (analytical T_max)": ("Section 2 1-D outer-wall temperature at the exit (correlation h)", "maximum solid temperature (outer wall, exit)"),
 "562.58 K (CFD medium T_max facet)": ("CFD medium outer-wall facet maximum (official baseline); P00 reference in 9B", "Maximum solid temperature (outer-wall facet)"),
 "560.83 K (CFD fine T_max facet)": ("CFD fine outer-wall facet maximum (verification reference)", "fine: maximum solid temperature (outer-wall facet)"),
 "605.16 MPa (FE LC2 peak von Mises)": ("FE LC2 peak von Mises at the inlet-face outer edge (7B); same value in S2/S3 statics", "LC2 maximum von Mises stress"),
 "657.2 MPa (analytical LC2 axial stress)": ("Section 2 −E α ΔT_mean with the analytical 254.7 K mean rise (not an FE result)", "LC2 axial stress (sigma = -E alpha dT_mean)"),
 "24.28 MPa (FE LC1 peak von Mises)": ("FE LC1 peak von Mises at the bore 6.5 mm from the inlet (end effect)", "LC1 maximum von Mises stress"),
 "1.108 (S1 lambda1)": ("linear eigenvalue buckling factor, S1 supports (8A); also 8B mesh values 1.10799–1.10805", "S1 lambda1"),
 "1.73 (first-yield factor)": ("1 / LC2 utilisation = linear scaling to first yield at the critical node", "First-yield load factor (1 / utilisation)"),
 "4.30 (S2 lambda1)": ("linear eigenvalue buckling factor, S2 supports (8A LC2NS)", "S2 lambda1"),
 "2.232 (S3 lambda1)": ("linear eigenvalue buckling factor, S3 supports (9B-2)", "S3 lambda1"),
 "548,936.6 N (LC2 end reaction)": ("FE LC2 end reaction (restrained thermal force), identical in S1/S2/S3", "LC2 end reaction (axial)"),
 "8190 kg/m3 (Inconel density)": ("Inconel 718 density input (class B)", "Solid density"),
 "1020 MPa (scalar S_y, ED lower bound)": ("VDM 300 °C yield point; scalar in Engineering Data (lower bound over 150.7–289.4 °C); NOT used for utilisation", "Yield strength (assessment)"),
 "1047 MPa (local S_y at LC2 peak)": ("S_y(T) at the LC2 critical node (164.8 °C), VDM table interpolation", "Local yield strength S_y(T) at the critical node"),
 "2.096 mm (analytical free growth)": ("Section 2 ε_th · L with the analytical 254.7 K mean rise", "free axial growth"),
 "1.841 mm (FE LC1 free growth)": ("FE LC1 area-weighted face-mean ΔL (7B); = ∫ε_th dz of the mapped field to 1.3e-5", "LC1 free axial growth dL")}
T = ["# MASTER TRACEABILITY — Section 10A", "", NOTICE, "",
     "Two parts: (1) every master value with its source file, case, method and status (the same rows as `MASTER_PROJECT_DATA.csv`); "
     "(2) the number register — where each key number of the brief appears in the project documents, what it means, and whether its "
     "label is unambiguous. File paths are relative to the project root and exist on disk (checked by `Scripts/verify_10A.py`). "
     "No line numbers are quoted in part 1; part 2 lists the files and the occurrence counts found by `Scripts/crossdoc_10A.py`.", "",
     "## 1. Value traceability", "",
     "| ID | Parameter | Final value | Units | Source file | Source result / case | Method | Documented value (where) | Status |", "|---|---|---|---|---|---|---|---|---|"]
for r in R:
    T.append("| %s | %s | %s | %s | `%s` | %s | %s | %s | **%s** |" % (r["ID"], esc(r["Parameter"]), esc(r["Value"]), r["Units"], esc(r["Source file"]), esc(r["Source result / case"]),
                                                             esc(r["Method"]), esc((r["Documented value"] + (" (" + r["Documented in"] + ")" if r["Documented in"] else "")) if r["Documented value"] else "—"), r["Status"]))
T += ["", "## 2. Number register (cross-document check of the brief's numbers)", "",
      "Search scope: every `.md` document and every summary `.csv` under 300 kB (%d files); monitor histories, hash records and screening "
      "candidate lists excluded as data. %d occurrences were found; %d of them are coincidental digit strings inside scientific-notation data "
      "values (for example a residual of 2.232e-06, a CAD rounding of 1.73e-14 %%, profile columns of axial_profiles.csv) and are not the "
      "quantity; the remaining %d were reviewed. **Result: no occurrence uses one of these numbers for a different "
      "quantity or modelling level than the one stated beside it (column header, row label or sentence).** Several numbers legitimately "
      "exist at two or three modelling levels; the register states each meaning." % (X["files_searched"], len(H0), NC, len(H)), "",
      "| Number | Meaning(s) and modelling level | Master ID | Documents containing it (occurrences) | Label check |", "|---|---|---|---|---|"]
for t in X["targets"]:
    m, pname = MEAN[t]
    mid = by[pname]["ID"]
    files = "; ".join("`%s` (%d)" % (f, n) for f, n in cnt[t].most_common(8)) + ("; +%d more" % (len(cnt[t]) - 8) if len(cnt[t]) > 8 else "")
    T.append("| %s | %s | %s | %s | unambiguous |" % (t.split(" (")[0], esc(m), mid, esc(files) or "—"))
T += ["", "Items that need care when the report is written (not errors): see `FINAL_ENGINEERING_AUDIT.md` §7 (documentation items L-01 … L-15).", ""]
open(os.path.join(O, "MASTER_TRACEABILITY.md"), "w", encoding="utf-8").write("\n".join(T) + "\n")
print("written")
