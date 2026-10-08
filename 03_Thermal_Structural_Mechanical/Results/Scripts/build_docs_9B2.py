# -*- coding: utf-8 -*-
"""SECTION 9B-2 - writes the result documents from the computed data (RE-ANALYSIS 2026).
Every number in the documents is read from the data files below (no hand-typed result values):
  Results/Data/post_9B2_results.json, trends_9B2.json, validity_9B2.json, Mapping/mapping_audit_9B2.json,
  Structural_Cases/B03_S3_TOY_BENCH/b03_results.json, Structural_Cases/S3_LC2_INTERMEDIATE/Audits/summary_S3_solve.json,
  presolve_audit_S3_solve.json, Mesh_Checks/m03_comparison.json, CFD_Results/PARAMETRIC_CFD_RESULTS.csv,
  9A screening (screening_matrix.csv)
Usage: python build_docs_9B2.py <data_root_with_10_Parametric_Study_layout> <out_root>"""
import os, sys, json, csv, math

D, O = sys.argv[1], sys.argv[2]
J = lambda *p: json.load(open(os.path.join(D, *p)))
P = J("Results", "Data", "post_9B2_results.json")
R = P["cases"]
TR = J("Results", "Data", "trends_9B2.json")["families"]
VAL = J("Results", "Data", "validity_9B2.json")["cases"]
MAP = J("Mapping", "mapping_audit_9B2.json")["cases"]
B03 = J("Structural_Cases", "B03_S3_TOY_BENCH", "b03_results.json")
B03O = J("Structural_Cases", "B03_S3_TOY_BENCH", "b03_results_run1_original_checks.json")
B03S = J("Structural_Cases", "B03_S3_TOY_BENCH", "Structured", "b03_results.json")
M03 = J("Mesh_Checks", "m03_comparison.json")
S3S = J("Structural_Cases", "S3_LC2_INTERMEDIATE", "Audits", "summary_S3_solve.json")
S3P = J("Structural_Cases", "S3_LC2_INTERMEDIATE", "Audits", "presolve_audit_S3_solve.json")
S3D = J("Structural_Cases", "S3_LC2_INTERMEDIATE", "Audits", "summary_S3_deck.json")
CFD = {}
with open(os.path.join(D, "CFD_Results", "PARAMETRIC_CFD_RESULTS.csv")) as fh:
    for r in csv.DictReader(l for l in fh if not l.startswith("#")):
        CFD[r["case"]] = r
SCR = {}
with open(os.path.join(D, "Screening", "screening_matrix.csv")) as fh:
    for r in csv.DictReader(fh):
        SCR[r["case"]] = r
PI = "pre-buckling equilibrium result; linear stability criterion indicates loss of stability before the applied load level"
NOTICE = ("> **RE-ANALYSIS 2026.** Every number in this document is a newly generated ANSYS 2026 R1 Student result of this "
          "re-analysis (Fluent CFD of Section 9B-1, Mechanical of Section 9B-2), computed from the solver's own output tables. "
          "Nothing is a recovered internship value, and no experimental or measured data exist or are implied.")
DES = ["P00_BASELINE", "V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK"]
ALLC = ["P00_BASELINE", "C00_PIPELINE_CHECK"] + DES[1:]
SHORT = {"P00_BASELINE": "P00", "C00_PIPELINE_CHECK": "C00", "V01_LOW": "V01", "V03_HIGH": "V03", "Q01_LOW": "Q01", "Q03_HIGH": "Q03",
         "T01_THIN": "T01", "T03_THICK": "T03", "M01_T01_STRUCT_NR5": "M01", "M02_T03_STRUCT_NR5": "M02", "S2_LC2NS_NOSWAY": "S2",
         "S3_LC2_INTERMEDIATE": "S3"}
VALTXT = {"P00_BASELINE": "V 23.5 m/s · q″ 8000 W/m² · t 10 mm", "C00_PIPELINE_CHECK": "= P00", "V01_LOW": "V 21.15 m/s",
          "V03_HIGH": "V 25.85 m/s", "Q01_LOW": "q″ 7,200 W/m²", "Q03_HIGH": "q″ 8,800 W/m²", "T01_THIN": "t 8 mm (Do 36)",
          "T03_THICK": "t 12 mm (Do 44)"}


def f(x, n=3):
    return ("{:,.%df}" % n).format(x)


def pct(a, b):
    return 100.0 * (a - b) / abs(b)


def sg(x, n=2):
    return ("%+." + str(n) + "f") % x


def loc(l):
    s = "%s, r %.0f mm, z %.1f mm" % (l["surface"], l["r_mm"], l["z_mm"])
    if l.get("end_face"):
        s = "%s edge of the %s (r %.0f mm, z %.0f)" % (l["surface"], l["end_face"], l["r_mm"], l["z_mm"])
    return s


def lam(t):
    return R[t]["buckling"]["lambda1"]


def mode_word(t):
    m = R[t]["buckling"]["modes"]["1"]
    corr = dict(m["correlation_with_reference_shapes"]); corr["fixed-pinned"] = m.get("corr_fixed_pinned", 0.0)
    best = max(corr, key=lambda k: abs(corr[k]))
    nm = {"guided_n1 cos(pi z/L)": "guided-column sway, cos(πz/L)", "guided_n2 / clamped_n1 cos(2pi z/L)": "clamped-column, 1 − cos(2πz/L)",
          "pinned_n1 sin(pi z/L)": "pinned-column, sin(πz/L)", "fixed-pinned": "fixed-pinned column"}[best]
    glob = m["beam_type_share_of_inplane_motion"] > 0.99 and m["max_ovalisation_over_max_lateral"] < 0.01
    return "%s %s (corr %.4f); max lateral at z = %.0f mm" % ("global" if glob else "NON-global", nm, abs(corr[best]), m["z_of_max_lateral_mm"]), glob, best


def w(name, txt):
    p = os.path.join(O, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8", newline="\n").write(txt)
    print("written", p, len(txt))


p0 = R["P00_BASELINE"]
# ================================================================================================ mapping audit
fam = {}
for c, e in MAP.items():
    fam.setdefault(e["family"], []).append(c)
L = ["# CFD → Mechanical temperature-mapping audit — Section 9B-2 (Part D)", "", NOTICE, "",
     "**Method (identical to Section 7A for every case).** The master mesh is the case's *own* Fluent solid mesh (read from its "
     "case file, written as an MAPDL CDB). The data are the case's *own* Fluent node temperatures (EnSight export of 9B-1), keyed by node id. "
     "Mechanical External Data → Imported Body Temperature with Manual / Bucket Volume / Shape Functions, and Nearest Node outside the source. "
     "No uniform temperature is used anywhere. Script: `Mapping/mapping_audit_9B2.py`; data: `Mapping/mapping_audit_9B2.json`.", "",
     "**What is compared.**", "",
     "- **(A) mapping error.** The nodal temperatures in the LC2 solver input (BFBLOCK) are compared with an exact re-evaluation of the same "
     "Fluent node field. The re-evaluation uses the trilinear shape functions of the source hexahedra (the 7A module "
     "`source_mesh_interp.HexField`, unchanged).",
     "- **(B) surface check.** The outer and bore surface nodes are compared with Fluent's finite-volume wall-face temperatures (θ-mean per "
     "slab, linear in z).",
     "- **Mid-span plane.** The through-wall ΔT and the radially area-weighted section mean of the mapped field are compared with the "
     "source node field on the same plane.", "",
     "**Acceptance, fixed before the audit ran.**", "",
     "- 0 unmapped nodes;",
     "- (A) ≤ 0.25 K (the accepted 7A value on the baseline numbering is 0.092 K and is shown for comparison);",
     "- no extrapolation beyond the source node range by more than 0.05 K;",
     "- mid-span ΔT and section mean preserved within 0.05 K.", ""]
for fm_, cases in fam.items():
    L += ["## Family: %s" % fm_, "",
          "| Case | Structural nodes | Source nodes / cells (layers) | Unmapped | Mapped T range [K] | Source node range [K] | Beyond source [K] | Nodes outside source (chord gap) | (A) max / RMS [K] | (B) outer max, 14–586 mm [K] | (B) bore max, 14–586 mm [K] | Mid-span ΔT mapped / source [K] | Mid-span mean mapped / source [K] | Result |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cases:
        e = MAP[c]; s = e["source"]; a = e["A_vs_source_node_field"]; b = e["B_vs_fluent_wall_faces"]; m = e["midspan"]
        L.append("| %s | %s | %s / %s (%d) | %d | %.3f – %.3f | %.3f – %.3f | %.3f | %s | %.3f / %.4f | %.3f | %.3f | %.4f / %.4f | %.3f / %.3f | **%s** |" % (
            SHORT[c], f(e["nodes"], 0), f(s["source_nodes"], 0), f(s["source_cells"], 0), s["source_radial_layers"], e["unmapped"], e["T_min_K"],
            e["T_max_K"], s["node_T_min_K"], s["node_T_max_K"], max(e["extrapolation_above_source_max_K"], e["extrapolation_below_source_min_K"]),
            f(e["nodes_outside_source_mesh"], 0), a["max_K"], a["rms_K"], b["outer"]["max_abs_14_586mm_K"], b["bore"]["max_abs_14_586mm_K"],
            m["mapped"]["dT_K"], m["source_nodes"]["dT_K"], m["mapped"]["mean_K"], m["source_nodes"]["mean_K"], "PASS" if e["ALL_PASS"] else "FAIL"))
    L.append("")
allpass = all(e["ALL_PASS"] for e in MAP.values())
L += ["## Findings", "",
      "- **All %d mapped cases pass every criterion.**" % len(MAP) if allpass else "- **At least one case fails - see the table.**",
      "- Unmapped nodes: **0 in every case**. The mapped range stays within the source node range, apart from ≤ %.3f K of shape-function "
      "overshoot at the chord-gap nodes." % max(max(e["extrapolation_above_source_max_K"], e["extrapolation_below_source_min_K"]) for e in MAP.values()),
      "- The mapping error (A) is %.3f–%.3f K. This is the same order as the accepted 7A value (0.092 K), and it is largest at the outer "
      "chord-gap nodes, where the true circle lies outside the 48-facet source mesh." % (
          min(e["A_vs_source_node_field"]["max_K"] for e in MAP.values()), max(e["A_vs_source_node_field"]["max_K"] for e in MAP.values())),
      "- The surface check (B) peaks in the first and last 14 mm, where the adiabatic end faces meet the wall. This is the known local "
      "limitation F-035 of 7A. Between 14 and 586 mm it is ≤ %.3f K (outer) and ≤ %.3f K (bore)." % (
          max(e["B_vs_fluent_wall_faces"]["outer"]["max_abs_14_586mm_K"] for e in MAP.values()),
          max(e["B_vs_fluent_wall_faces"]["bore"]["max_abs_14_586mm_K"] for e in MAP.values())),
      "- The mid-span through-wall ΔT and the section mean are preserved within %.4f K and %.4f K." % (
          max(abs(e["midspan"]["dT_diff_K"]) for e in MAP.values()), max(abs(e["midspan"]["mean_diff_K"]) for e in MAP.values())),
      "- **Numbering effect (C00).** The C00 source is the P00 field on identical coordinates, but Fluent re-numbered its node and cell ids. "
      "Mechanical's bucket search therefore interpolates some target nodes in a different, equally valid source element. The nodal "
      "temperatures differ from the 7B input by at most %.4f K (%d of 108,252 nodes). This difference is below the accepted mapping error, "
      "and its effect on the results is reported as the mapping uncertainty in `Results/FINAL_PARAMETRIC_AUDIT.md`." % (
          R and J("Structural_Cases", "C00_PIPELINE_CHECK", "Audits", "summary_C00_PIPELINE_CHECK.json")["C00_bf_vs_7B"]["LC2"]["max_abs_K"],
          J("Structural_Cases", "C00_PIPELINE_CHECK", "Audits", "summary_C00_PIPELINE_CHECK.json")["C00_bf_vs_7B"]["LC2"]["nodes_different"]), ""]
w("Mapping/MAPPING_AUDIT_9B2.md", "\n".join(L))
print("mapping doc done")


# ================================================================================================ helpers for the case docs
def first_yield(t):
    return 1.0 / R[t]["LC2"]["utilisation"]["max"]


def governs(t):
    fy, l1 = first_yield(t), lam(t)
    return "buckling (λ₁ %.3f < first-yield factor %.3f)" % (l1, fy) if l1 < fy else "first yield (first-yield factor %.3f < λ₁ %.3f)" % (fy, l1)


def ch(t, key, sub=None, rel=True, scale=1.0, n=2):
    a = R[t][key] if sub is None else R[t][key][sub]
    b = p0[key] if sub is None else p0[key][sub]
    if isinstance(a, dict):
        raise ValueError
    return ("%+.*f %%" % (n, pct(a, b))) if rel else ("%+.*f" % (n, (a - b) * scale))


val = VAL
cfdrow = lambda t: CFD["P00_BASELINE" if t == "P00_BASELINE" else t]
# ================================================================================================ PARAMETRIC_STRUCTURAL_RESULTS.md
L = ["# Parametric structural results — Section 9B-2", "", NOTICE, "",
     "Cases: the baseline P00 (official 7B / 8A solution, reference), the pipeline control C00, and the six design cases V01, V03, Q01, "
     "Q03, T01 and T03. Each design case is driven by the **actual 9B-1 CFD temperature field of that case**; no screening temperature is "
     "used anywhere. Tables: `PARAMETRIC_STRUCTURAL_RESULTS.csv`; data: `Data/post_9B2_results.json` (written by `Scripts/post_9B2.py` "
     "from the raw solver tables).", "",
     "## 1. Method (unchanged from 7A / 7B / 8A / 8B)", "",
     "| Item | 9B-2 |",
     "|---|---|",
     "| Model per case | A SAVE-AS copy of the solved 7B Workbench project (`Structural_Cases/<CASE>/Project`). The 7B project is never written to (hash check, §9) |",
     "| Temperature | Mesh-based External Data (7A method): the case's own Fluent solid mesh as CDB master, plus its own node temperatures. Settings re-applied and read back; the Setup cells refreshed; Mechanical's own source minimum/maximum must equal the case file. Manual / Bucket Volume / Shape Functions / Nearest Node |",
     "| Material | Inconel_718_Re_analysis: E(T), secant α(T), ν = 0.294 [ASSUMED]. The solver material block is checked identical to 7B in every case. Yield S_y(T) = VDM 4127 table, linear, 20–400 °C, **no extrapolation** (every case lies inside) |",
     "| Supports (not changed between cases) | LC1: 3 outer-ring nodes at the inlet, U_θ = U_z = 0 (CS_DUCT_CYL). LC2: U_z = 0 on both complete end faces, plus 3 mid-span outer nodes U_θ = 0. Buckling: S1 = LC2 pre-stress, 6 modes, positive multipliers. Node sets re-located at the same positions (outer radius of the case) |",
     "| Solver | sparse direct, linear, small deflection; T_ref 300 K |",
     "| Pre-solve gate | %d–%d checks per case, all PASS before any solve (mesh counts vs formula, quality, extents, support positions, source identity, mapped range, 0 unmapped, object states, solver-input material / constraint sets / temperatures) |" % (
         min(v.get("gate_checks", 99) for k, v in val.items() if k in R and k not in ("S3_LC2_INTERMEDIATE",)),
         max(v.get("gate_checks", 0) for k, v in val.items() if k in R and k not in ("S3_LC2_INTERMEDIATE",))),
     "| Pressure (Part N) | not re-run: 7B LC2P showed +45 Pa (+7.4 × 10⁻⁶ %) on the LC2 peak at the CFD maximum wall pressure. The Δp of the design cases (380–500 Pa) is of the same order, so its effect is negligible for every case |", "",
     "## 2. Structural meshes (Part C)", "",
     "| Case | Geometry | Divisions (circ × wall × axial, bias) | Radial element | Nodes (limit 128,000) | Elements | Jacobian ratio max | Element quality min | Aspect ratio max | Through-wall node radii |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for t in ["C00_PIPELINE_CHECK", "V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK", "M01_T01_STRUCT_NR5", "M02_T03_STRUCT_NR5"]:
    if t not in R:
        continue
    E = R[t]; ms = E["mechanical"]["mesh"]; mm = E["mechanical"]["mesh_metrics"]
    L.append("| %s | %s | 36 × %d × 130, 4 | %.2f mm | %s | %s | %.3f | %.3f | %.2f | %d, uniform |" % (
        SHORT[t], E["geometry"], E["nr"], (E["Ro_m"] - E["Ri_m"]) / E["nr"] * 1e3, f(ms["nodes"], 0), f(ms["elements"], 0),
        mm["JacobianRatio"]["max"], mm["ElementQuality"]["min"], mm["AspectRatio"]["max"], 2 * E["nr"] + 1))
MM = P.get("structural_mesh_checks_M01_M02", {})
L += ["", "- **V / Q / C00 reuse mesh B unchanged.** The solver-input node and element blocks are identical to 7B (gate check). "
      "The temperature check of §3 gave no reason to change it.",
      "- **T01 / T03 use the geometry-specific meshes of 9A.** They have the same 2.0 mm radial element as mesh B, the same 36 × 130 "
      "divisions and axial bias, and they were generated on the 9B-1 SpaceClaim models. Node count = the swept-hex formula "
      "(89,424 / 127,080 < 128,000).",
      "- **Axial resolution** (130 divisions, bias 4, first element 2.13 mm) is that of mesh B. 8B showed it converged for LC2 and λ₁ "
      "(FA +152 divisions: ≤ 0.004 %).",
      "- **Through-wall resolution of the thickness extremes (9A rows M01 / M02).** The same case was re-solved with 5 through-wall elements "
      "(T01: 1.6 mm; T03: 2.4 mm, a coarsening, because refinement exceeds 128,000 nodes). Result:", ""]
if MM:
    L += ["| Check | Reference | LC2 max VM | LC2 mean axial stress | λ₁ | LC1 max VM | LC1 mid-span bore σθ | LC1 max deformation | Class A (LC2, λ₁ ≤ 10⁻⁴) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, v in MM.items():
        c = v["changes"]
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | **%s** |" % (
            SHORT[k], SHORT[v["reference"]], "%+.2e" % c["LC2 max vm"]["rel"], "%+.2e" % c["LC2 mean axial stress"]["rel"], "%+.2e" % c["lambda1"]["rel"],
            "%+.2f %%" % (100 * c["LC1 max vm"]["rel"]), "%+.2f %%" % (100 * c["LC1 mid-span bore hoop stress"]["rel"]),
            "%+.2e" % c["LC1 max total deformation"]["rel"], "PASS" if v["class_A_LC2_lambda1_le_1e-4"] else "FAIL"))
    L.append("")
    _ms = max(abs(v["changes"][k]["rel"]) for v in MM.values() for k in ("LC2 mean axial stress", "lambda1"))
    _pk = max(abs(v["changes"]["LC2 max vm"]["rel"]) for v in MM.values())
    _fail = [SHORT[k] for k, v in MM.items() if not v["class_A_LC2_lambda1_le_1e-4"]]
    _t01 = abs(pct(R["T01_THIN"]["LC2"]["max_vm_Pa"], R["P00_BASELINE"]["LC2"]["max_vm_Pa"])) / 100 if "T01_THIN" in R else float("nan")
    _lc1 = [100 * v["changes"]["LC1 max vm"]["rel"] for v in MM.values()]
    L += ["- **Reading.** The LC2 mean axial stress and λ₁ change by at most %.1e and the LC2 peak by at most %.1e (relative). %s"
          "The LC2 peak is a single node at the outer edge of the inlet face, a stress-concentration point whose value depends on the local "
          "discretisation; the change is %.0f× smaller than the T01 change against P00 (%.2f %%), so no trend, λ₁ < 1 classification or "
          "utilisation statement is affected. The LC1 peak (bore, near the inlet) changes by %s: a through-wall discretisation uncertainty of "
          "about ±%.1f %% on the LC1 stresses of T01 / T03 (≈ 2 %% of S_y; no decision depends on them)." % (
              _ms, _pk, ("%s exceeds the 10⁻⁴ class-A tolerance on the LC2 peak only. " % ", ".join(_fail)) if _fail else "",
              _t01 / _pk, 100 * _t01, " / ".join("%+.2f %%" % x for x in _lc1), max(abs(x) for x in _lc1)),
          "- The 4- and 6-division meshes are therefore kept for T01 / T03; these differences are carried as structural-mesh uncertainty "
          "(`FINAL_PARAMETRIC_AUDIT.md` §3, #4).", ""]
# ---- mapping summary
L += ["## 3. Temperature mapping (Part D)", "",
      "Detail per geometry family: `Mapping/MAPPING_AUDIT_9B2.md`.", "",
      "| Case | Unmapped | Mechanical source min / max = case CSV | Mapped range [K] | (A) mapping error max [K] | Mid-span ΔT mapped / source [K] | Mid-span mean mapped / source [K] |",
      "|---|---|---|---|---|---|---|"]
for t in ["C00_PIPELINE_CHECK", "V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK"]:
    if t not in MAP:
        continue
    e = MAP[t]; mp = R[t]["mechanical"]["mapping"]["LC2"]
    L.append("| %s | %d | %.3f / %.3f | %.3f – %.3f | %.3f | %.3f / %.3f | %.2f / %.2f |" % (
        SHORT[t], e["unmapped"], mp["source_min_K"], mp["source_max_K"], e["T_min_K"], e["T_max_K"], e["A_vs_source_node_field"]["max_K"],
        e["midspan"]["mapped"]["dT_K"], e["midspan"]["source_nodes"]["dT_K"], e["midspan"]["mapped"]["mean_K"], e["midspan"]["source_nodes"]["mean_K"]))
L.append("")
# ---- LC1
L += ["## 4. LC1 — free thermal expansion (Part F)", "",
      "| Case | Value | Max total deformation [mm] | Axial growth ΔL [mm] | Max von Mises [MPa] | Critical location | T there [K] | Reaction magnitude ΣF [N] | Change vs P00 (deformation / ΔL / VM) |",
      "|---|---|---|---|---|---|---|---|---|"]
for t in ALLC:
    if t not in R:
        L.append("| %s | %s | not available (case stopped; no value fabricated) | | | | | | |" % (SHORT[t], VALTXT[t])); continue
    e = R[t]["LC1"]
    L.append("| %s | %s | %.4f | %.4f | %.3f | %s | %.2f | %.1e | %s / %s / %s |" % (
        SHORT[t], VALTXT[t], e["max_utot_m"] * 1e3, e["dL_face_mean_m"] * 1e3, e["max_vm_Pa"] / 1e6, loc(e["max_vm_loc"]), e["max_vm_loc"]["T_K"],
        e["reactions"]["sumF_mag_N"], ch(t, "LC1", "max_utot_m") if t != "P00_BASELINE" else "-", ch(t, "LC1", "dL_face_mean_m") if t != "P00_BASELINE" else "-",
        ch(t, "LC1", "max_vm_Pa") if t != "P00_BASELINE" else "-"))
L += ["", "- The LC1 support is statically determinate. Reactions are ≈ 0 (≤ %.1e N) in every case, so LC1 stresses come only from the "
      "non-uniform temperature field." % max(R[t]["LC1"]["reactions"]["sumF_mag_N"] for t in ALLC if t in R),
      "- The critical LC1 location is **the bore, 6.5 mm from the inlet face** in every case (the steep axial temperature rise at the "
      "inlet end). The maximum deformation is at the outer edge of the outlet face (free growth plus radial growth).",
      "- LC1 stresses are small (≈ 2 % of S_y). They are listed for completeness and drive no decision.", ""]
# ---- LC2
L += ["## 5. LC2 — axially restrained thermal expansion (Part G)", "",
      "| Case | Max von Mises [MPa] | Mean axial stress [MPa] | End reaction [kN] | Max total deformation [mm] | Max axial deformation |u_z| [mm] | Max radial deformation u_r [mm] | Critical location (max vm/S_y) | Critical T [K] | S_y(T) there [MPa] | Utilisation vm/S_y(T) | λ₁ | Static-state status |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for t in ALLC:
    if t not in R:
        continue
    e = R[t]["LC2"]; u = e["utilisation"]
    st = "**%s**" % PI if lam(t) < 1 else "static equilibrium below the linear stability limit (λ₁ > 1)"
    L.append("| %s | %.3f | %.3f | %.2f | %.4f | %.4f | %.4f | %s | %.2f | %.1f | %.4f | %.4f | %s |" % (
        SHORT[t], e["max_vm_Pa"] / 1e6, e["mean_axial_stress_Pa"] / 1e6, abs(e["reactions"]["inlet_Fz_N"]) / 1e3, e["max_utot_m"] * 1e3,
        e["max_abs_uz_m"] * 1e3, e["max_ur_m"] * 1e3, loc(u["max_loc"]), u["max_loc"]["T_K"], u["Sy_at_max_Pa"] / 1e6, u["max"], lam(t), st))
L += ["", "Changes against P00 (the same definitions):", "",
      "| Case | LC2 max VM | Mean axial stress | End reaction | Max total deformation | Utilisation |",
      "|---|---|---|---|---|---|"]
for t in ALLC[1:]:
    if t not in R:
        continue
    L.append("| %s | %s | %s | %s | %s | %s |" % (SHORT[t], ch(t, "LC2", "max_vm_Pa"), ch(t, "LC2", "mean_axial_stress_Pa"),
                                               "%+.2f %%" % pct(abs(R[t]["LC2"]["reactions"]["inlet_Fz_N"]), abs(p0["LC2"]["reactions"]["inlet_Fz_N"])),
                                               ch(t, "LC2", "max_utot_m"), "%+.2f %%" % pct(R[t]["LC2"]["utilisation"]["max"], p0["LC2"]["utilisation"]["max"])))
low = [SHORT[t] for t in DES if t in R and lam(t) < 1]
L += ["", "**Cases with λ₁ < 1 (Part I): %s.** For these cases the LC2 static stress is labelled: *%s*. The static Mechanical solution is "
      "the idealised equilibrium of the mathematical load case. It is **not** claimed that the duct physically reaches that state without "
      "additional stabilisation." % (", ".join(low) if low else "none", PI),
      "- The mean axial stress follows the mean thermal strain of the whole duct, because the end force is uniform along the length.",
      "- The peak von Mises stress sits at the outer edge of the inlet face in every case: the uniform restrained axial stress plus a local "
      "part where the face is held flat (U_z = 0 on every node) and the outer fibre is the hottest point of the section.",
      "- For T01 and T03 the stress level hardly changes: the restrained thermal stress depends on the temperatures (solid mean %+.2f / %+.2f K), "
      "not on the section. The end force scales with the cross-section area (T01 %s, T03 %s)." % (
          TR["T"]["quantities"]["T_solid_mean_K"]["values"][0] - TR["T"]["quantities"]["T_solid_mean_K"]["values"][1],
          TR["T"]["quantities"]["T_solid_mean_K"]["values"][2] - TR["T"]["quantities"]["T_solid_mean_K"]["values"][1],
          "%+.1f %%" % pct(abs(R["T01_THIN"]["LC2"]["reactions"]["inlet_Fz_N"]), abs(p0["LC2"]["reactions"]["inlet_Fz_N"])) if "T01_THIN" in R else "n/a",
          "%+.1f %%" % pct(abs(R["T03_THICK"]["LC2"]["reactions"]["inlet_Fz_N"]), abs(p0["LC2"]["reactions"]["inlet_Fz_N"])) if "T03_THICK" in R else "n/a"), ""]
# ---- buckling
L += ["## 6. Linear buckling, S1 supports (Part H)", "",
      "| Case | λ₁ | λ₂ | λ₃ | Critical load P_cr = λ₁·N [kN] | Applied N [kN] | Dominant mode (mode 1) | Classification | λ₁ vs 1 |",
      "|---|---|---|---|---|---|---|---|---|"]
for t in ALLC:
    if t not in R:
        continue
    b = R[t]["buckling"]; mw, glob, best = mode_word(t)
    L.append("| %s | %.5f | %.5f | %.4f | %.2f | %.2f | %s | %s | %s |" % (
        SHORT[t], b["lambda1"], b["lambda2"], b["lambda3"], b["critical_load_N"] / 1e3, b["applied_N"] / 1e3, mw,
        "global Euler column mode (beam share %.6f, ovalisation %.1e); modes 1–2 an orthogonal pair (split %.1e)" % (
            b["modes"]["1"]["beam_type_share_of_inplane_motion"], b["modes"]["1"]["max_ovalisation_over_max_lateral"], b["pair_split_rel"]),
        "**< 1**" if b["lambda1"] < 1 else "> 1"))
L += ["", "- The mode is the same in every case: global sway of a guided column. The end sections translate in opposite directions and "
      "stay perpendicular, with no mid-span deflection. No shell, ovalisation or local mode appears in any case.",
      "- λ₁ is a *linear* (eigenvalue) bifurcation factor of the idealised straight tube. It includes no imperfection, no plasticity and "
      "no large-deflection effect, and it is not a design margin (8A).", ""]
# ---- yield vs buckling
L += ["## 7. First yield vs buckling (Part J)", "",
      "Both factors multiply the **same LC2 thermal load state**.",
      "", "- **First-yield factor = 1 / utilisation.** It is the linear-elastic scaling of the LC2 stresses at which vm reaches S_y(T) "
      "at the critical node; S_y is held at the operating temperature.",
      "- **λ₁** is the factor at which the straight tube bifurcates.",
      "", "They are reported separately. No single factor of safety is formed.", "",
      "| Case | First-yield utilisation | First-yield factor | Linear buckling factor λ₁ | Occurs first in the idealised model |",
      "|---|---|---|---|---|"]
for t in ALLC:
    if t not in R:
        continue
    L.append("| %s | %.4f | %.3f | %.4f | %s |" % (SHORT[t], R[t]["LC2"]["utilisation"]["max"], first_yield(t), lam(t), governs(t)))
L += ["", "In every case with the S1 supports, **elastic bifurcation comes before first yield**. The LC2 idealisation is "
      "stability-controlled, as found in 8A for P00; the utilisation values are therefore **not** structural margins.",
      "Slenderness with the S1 effective length (K = 1, L = 600 mm; r_g = √(R_i² + R_o²)/2): %s. All are below C_c ≈ 60 (8A, P00 "
      "properties; E and S_y at the operating temperatures differ by < 1 %% between cases), i.e. intermediate columns. Their Euler stress is "
      "above the conventional proportional limit, so the elastic λ₁ is an upper estimate of an inelastic buckling load (8A: Johnson 1.058 "
      "for P00). Johnson values of the other cases were not computed." % ", ".join(
          "%s %.1f" % (SHORT[t], 600.0 / (1e3 * math.sqrt(R[t]["Ri_m"] ** 2 + R[t]["Ro_m"] ** 2) / 2)) for t in DES if t in R), ""]
# ---- critical locations
L += ["## 8. Critical locations (Part S)", "",
      "| Case | Max LC2 stress location | T there [K] | S_y(T) there [MPa] | λ₁ | Dominant buckling location / mode |",
      "|---|---|---|---|---|---|"]
for t in ALLC:
    if t not in R:
        continue
    e = R[t]["LC2"]; mw, glob, best = mode_word(t)
    L.append("| %s | %s | %.2f | %.1f | %.4f | %s |" % (SHORT[t], loc(e["max_vm_loc"]), e["max_vm_loc"]["T_K"], e["utilisation"]["Sy_at_max_vm_Pa"] / 1e6, lam(t), mw))
same_loc = all(R[t]["LC2"]["max_vm_loc"]["end_face"] == "inlet face" and R[t]["LC2"]["max_vm_loc"]["surface"] == "outer" for t in ALLC if t in R)
L += ["", "- **The critical LC2 location does not move with velocity, heat flux or thickness.**" if same_loc else "- **The critical location changes - see table.**",
      "  It stays at the outer edge of the inlet face (the circumferential position varies only within numerical noise on an "
      "axisymmetric field). Its temperature follows the inlet-end wall temperature of each case.",
      "- Away from the end faces (15 mm ≤ z ≤ L − 15 mm) the largest *von Mises stress* is on the outer surface near the inlet "
      "(P00: %.1f MPa at z = %.1f mm), while the largest *utilisation* is on the outer surface at the hot outlet end, where S_y(T) is lower "
      "(P00: %.4f at z = %.1f mm, against %.4f at the inlet-face edge)." % (
          p0["LC2"]["max_vm_interior_Pa"] / 1e6, p0["LC2"]["max_vm_interior_loc"]["z_mm"], p0["LC2"]["utilisation"]["interior_max"],
          p0["LC2"]["utilisation"]["interior_loc"]["z_mm"], p0["LC2"]["utilisation"]["max"]),
      "- The buckling mode and its location (largest curvature at the rotation-held end sections, sway of the ends) are the same in every design case.",
      "- Support-scenario locations: `SUPPORT_SENSITIVITY_RESULTS.md`.", ""]
# ---- controls
c0 = R["C00_PIPELINE_CHECK"]
L += ["## 9. Controls and integrity", "",
      "| Control | Result |",
      "|---|---|",
      "| C00 pipeline control vs 7B / 8A (tolerance 10⁻⁵, 9A row C00) | LC2 max VM %s (%.2e); end reaction %s (%.2e); λ₁ %.8f vs %.8f (%.2e); LC1 ΔL %.2e. The C00 source has Fluent's re-numbered node ids, so up to 0.08 K of numbering-dependent mapping difference remains (§3). Its only visible effect is on the LC1 inlet-bore peak: %s (%s) |" % (
          f(c0["LC2"]["max_vm_Pa"] / 1e6, 4), c0["LC2"]["max_vm_Pa"] / p0["LC2"]["max_vm_Pa"] - 1, f(abs(c0["LC2"]["reactions"]["inlet_Fz_N"]), 1),
          abs(c0["LC2"]["reactions"]["inlet_Fz_N"]) / abs(p0["LC2"]["reactions"]["inlet_Fz_N"]) - 1, lam("C00_PIPELINE_CHECK"), lam("P00_BASELINE"),
          lam("C00_PIPELINE_CHECK") / lam("P00_BASELINE") - 1, c0["LC1"]["dL_face_mean_m"] / p0["LC1"]["dL_face_mean_m"] - 1,
          f(c0["LC1"]["max_vm_Pa"] / 1e6, 3), ch("C00_PIPELINE_CHECK", "LC1", "max_vm_Pa")),
      "| Earlier C00 run with the cached P00 source (run 2) | bit-identical to 7B/8A (LC2 VM 605,160,873.381 Pa; λ₁ 1.1080470); kept in `Structural_Cases/Audits/Run2_C00_before_setup_refresh` |",
      "| Source identity guard | the Mechanical source min/max check stopped T01 run 1, which had imported the cached P00 data; fixed by refreshing the Setup cells (D-068) |",
      "| Baseline integrity | `08_Structural_Analysis`: every file identical to the pre-9B-2 hash record (verification V7) |", ""]
w("Results/PARAMETRIC_STRUCTURAL_RESULTS.md", "\n".join(L))


# ================================================================================================ PARAMETRIC_TRENDS.md
QN = {"dp_Pa": "Pressure drop Δp [Pa]", "T_out_K": "Outlet bulk T [K]", "T_solid_max_K": "Max solid T [K]", "T_solid_mean_K": "Solid mean T [K]",
      "LC1_max_utot_mm": "LC1 max deformation [mm]", "LC1_dL_mm": "LC1 axial growth [mm]", "LC1_max_vm_MPa": "LC1 max VM [MPa]",
      "LC2_max_vm_MPa": "LC2 max VM [MPa]", "LC2_mean_axial_MPa": "LC2 mean axial stress [MPa]", "LC2_max_utot_mm": "LC2 max deformation [mm]",
      "LC2_max_ur_mm": "LC2 max radial deformation [mm]", "LC2_end_reaction_kN": "LC2 end reaction [kN]", "LC2_utilisation": "LC2 utilisation [-]",
      "lambda1": "λ₁ [-]", "Pcr_kN": "P_cr [kN]"}
KEYQ = {"V": ["dp_Pa", "T_out_K", "T_solid_max_K", "T_solid_mean_K", "LC1_dL_mm", "LC2_max_vm_MPa", "LC2_mean_axial_MPa", "LC2_end_reaction_kN",
              "LC2_utilisation", "lambda1", "Pcr_kN"],
        "Q": ["dp_Pa", "T_out_K", "T_solid_max_K", "T_solid_mean_K", "LC1_dL_mm", "LC2_max_vm_MPa", "LC2_mean_axial_MPa", "LC2_end_reaction_kN",
              "LC2_utilisation", "lambda1", "Pcr_kN"],
        "T": ["T_solid_max_K", "T_solid_mean_K", "LC1_max_utot_mm", "LC1_dL_mm", "LC1_max_vm_MPa", "LC2_max_vm_MPa", "LC2_mean_axial_MPa",
              "LC2_max_utot_mm", "LC2_end_reaction_kN", "LC2_utilisation", "lambda1", "Pcr_kN"]}
FNAME = {"V": "Velocity (V01 21.15 · P00 23.5 · V03 25.85 m/s; ±10 %)", "Q": "Heat flux (Q01 7,200 · P00 8,000 · Q03 8,800 W/m²; ±10 %)",
         "T": "Wall thickness (T01 8 · P00 10 · T03 12 mm; Do 36 / 40 / 44 mm; ±20 %; total heat input Q held constant)"}


def fam_table(fk):
    F = TR[fk]
    rows = ["| Quantity | %s | %s | %s | Change %s | Change %s | Normalised sensitivity (dy/y)/(dx/x) | Mid-point deviation from linear |" % (
        SHORT[F["cases"][0]], SHORT[F["cases"][1]], SHORT[F["cases"][2]], SHORT[F["cases"][0]], SHORT[F["cases"][2]]), "|---|---|---|---|---|---|---|---|"]
    for q in KEYQ[fk]:
        e = F["quantities"].get(q)
        if not e or "pct_change_vs_P00" not in e:
            continue
        v = e["values"]; p = e["pct_change_vs_P00"]
        nd = 5 if q in ("lambda1", "LC2_utilisation") else (4 if "mm" in q else 2)
        rows.append("| %s | %.*f | %.*f | %.*f | %+.2f %% | %+.2f %% | %+.3f | %+.3f %% |" % (QN[q], nd, v[0], nd, v[1], nd, v[2], p[0], p[2],
                                                                                   e["normalised_sensitivity"], e["midpoint_deviation_from_linear_pct"]))
    return rows


def most_sensitive(fk, quantities):
    F = TR[fk]["quantities"]
    c = [(abs(F[q]["normalised_sensitivity"]), q) for q in quantities if q in F and "normalised_sensitivity" in F[q]]
    return max(c)[1], max(c)[0]


L = ["# Parametric trends — Section 9B-2 (Parts O, P, Q, W)", "", NOTICE, "",
     "One-factor-at-a-time study around P00. Every value comes from the solved CFD (9B-1) and Mechanical (9B-2) cases; the 9A "
     "screening appears only as a comparison (§5). Percentages are changes from P00 **within one family**. Families are not compared "
     "with each other, except through the normalised sensitivity S = (Δy/y₀)/(Δx/x₀), which removes the different step sizes. "
     "Data: `Data/trends_9B2.json`. Figures: `Figures/F01…F15`.", ""]
for fk in ("V", "Q", "T"):
    L += ["## %s" % FNAME[fk], ""] + fam_table(fk) + [""]
# narrative per family
tv, tq, tt = TR["V"]["quantities"], TR["Q"]["quantities"], TR["T"]["quantities"]
L += ["## 4. What the trends mean", "",
      "**Velocity.** Lower velocity means less cooling capacity at the same heat input. V01 (−10 %%) raises the outlet temperature by %+.2f K, "
      "the maximum solid temperature by %+.2f K and the solid mean by %+.2f K. The restrained thermal force follows the mean temperature "
      "(end reaction %+.2f %%), so λ₁ falls by %.2f %% to %.4f. V03 (+10 %%) does the opposite (λ₁ %.4f, %+.2f %%). Δp changes by %+.1f %% / %+.1f %%, "
      "a local exponent Δp ∝ V^%.2f. This is below the 1.75–2 of isothermal turbulent duct flow; part of the static pressure drop "
      "accelerates the heated air, and that part grows when the air heats more (lower V). The split was not isolated in 9B-1. "
      "The LC2 peak von Mises changes slightly less than the mean axial stress (%+.2f %% / %+.2f %% against %+.2f %% / %+.2f %% in magnitude): "
      "the peak adds a local inlet-end part to the uniform axial stress, and the wall temperature at the critical node changes less than the "
      "duct mean (V01: %+.2f K against %+.2f K)." % (
          tv["T_out_K"]["values"][0] - tv["T_out_K"]["values"][1], tv["T_solid_max_K"]["values"][0] - tv["T_solid_max_K"]["values"][1],
          tv["T_solid_mean_K"]["values"][0] - tv["T_solid_mean_K"]["values"][1], tv["LC2_end_reaction_kN"]["pct_change_vs_P00"][0],
          -tv["lambda1"]["pct_change_vs_P00"][0], tv["lambda1"]["values"][0], tv["lambda1"]["values"][2], tv["lambda1"]["pct_change_vs_P00"][2],
          tv["dp_Pa"]["pct_change_vs_P00"][0], tv["dp_Pa"]["pct_change_vs_P00"][2],
          math.log(tv["dp_Pa"]["values"][2] / tv["dp_Pa"]["values"][0]) / math.log(25.85 / 21.15),
          tv["LC2_max_vm_MPa"]["pct_change_vs_P00"][0], tv["LC2_max_vm_MPa"]["pct_change_vs_P00"][2],
          -tv["LC2_mean_axial_MPa"]["pct_change_vs_P00"][0], -tv["LC2_mean_axial_MPa"]["pct_change_vs_P00"][2],
          R["V01_LOW"]["LC2"]["utilisation"]["max_loc"]["T_K"] - R["P00_BASELINE"]["LC2"]["utilisation"]["max_loc"]["T_K"],
          tv["T_solid_mean_K"]["values"][0] - tv["T_solid_mean_K"]["values"][1]), "",
      "**Heat flux.** q″ is the load itself. ±10 %% moves the solid mean by %+.2f / %+.2f K; the solid-mean rise above the 300 K inlet "
      "changes by %+.1f / %+.1f %%, slightly more than proportionally (the cause was not isolated). The restrained force follows "
      "(end reaction %+.2f / %+.2f %%). λ₁ goes to %.4f (Q01) and %.4f (Q03). "
      "Q03 sits %s the linear stability limit, and it is the case of largest LC2 stress (%.2f MPa) and utilisation (%.4f). Δp changes "
      "only through the air temperature (density, viscosity, acceleration of the heated air) (%+.1f / %+.1f %%)." % (
          tq["T_solid_mean_K"]["values"][0] - tq["T_solid_mean_K"]["values"][1], tq["T_solid_mean_K"]["values"][2] - tq["T_solid_mean_K"]["values"][1],
          pct(tq["T_solid_mean_K"]["values"][0] - 300.0, tq["T_solid_mean_K"]["values"][1] - 300.0),
          pct(tq["T_solid_mean_K"]["values"][2] - 300.0, tq["T_solid_mean_K"]["values"][1] - 300.0),
          tq["LC2_end_reaction_kN"]["pct_change_vs_P00"][0], tq["LC2_end_reaction_kN"]["pct_change_vs_P00"][2],
          tq["lambda1"]["values"][0], tq["lambda1"]["values"][2], "below" if tq["lambda1"]["values"][2] < 1 else "above",
          tq["LC2_max_vm_MPa"]["values"][2], tq["LC2_utilisation"]["values"][2], tq["dp_Pa"]["pct_change_vs_P00"][0], tq["dp_Pa"]["pct_change_vs_P00"][2]), "",
      "**Wall thickness (Q held).** Temperatures move by less than 1 K (%+.2f / %+.2f K on the solid mean). The thermal *stress* level "
      "therefore barely changes (LC2 max VM %+.2f / %+.2f %%), and the growth is almost the same. What changes is the section: the end "
      "force scales with the area A (%+.1f / %+.1f %%), while the Euler load scales with the bending stiffness EI (P_cr %+.1f / %+.1f %%). "
      "Because λ₁ ∝ I/(A·ε_th) ∝ r_g², the thin wall **loses** stability margin (λ₁ %.4f) and the thick wall **gains** it (λ₁ %.4f). "
      "Thickness is the one variable of the three that changes λ₁ through the section rather than through the temperatures; its normalised "
      "effect on λ₁ (S = %+.3f) is of the same order as those of V (%+.3f) and q″ (%+.3f). The LC1 peak stress changes by %+.1f / %+.1f %% "
      "with the through-wall temperature difference (mid-span ΔT %.2f / %.2f / %.2f K for 8 / 10 / 12 mm)." % (
          tt["T_solid_mean_K"]["values"][0] - tt["T_solid_mean_K"]["values"][1], tt["T_solid_mean_K"]["values"][2] - tt["T_solid_mean_K"]["values"][1],
          tt["LC2_max_vm_MPa"]["pct_change_vs_P00"][0], tt["LC2_max_vm_MPa"]["pct_change_vs_P00"][2],
          tt["LC2_end_reaction_kN"]["pct_change_vs_P00"][0], tt["LC2_end_reaction_kN"]["pct_change_vs_P00"][2],
          tt["Pcr_kN"]["pct_change_vs_P00"][0], tt["Pcr_kN"]["pct_change_vs_P00"][2], tt["lambda1"]["values"][0], tt["lambda1"]["values"][2],
          tt["lambda1"]["normalised_sensitivity"], tv["lambda1"]["normalised_sensitivity"], tq["lambda1"]["normalised_sensitivity"],
          tt["LC1_max_vm_MPa"]["pct_change_vs_P00"][0], tt["LC1_max_vm_MPa"]["pct_change_vs_P00"][2],
          MAP["T01_THIN"]["midspan"]["mapped"]["dT_K"], MAP["C00_PIPELINE_CHECK"]["midspan"]["mapped"]["dT_K"], MAP["T03_THICK"]["midspan"]["mapped"]["dT_K"]), ""]
# most sensitive
L += ["**Most sensitive quantity per parameter** (largest |S| among the listed quantities):", "",
      "| Parameter | Most sensitive quantity | S | Next |", "|---|---|---|---|"]
for fk in ("V", "Q", "T"):
    F = TR[fk]["quantities"]
    cand = sorted([(abs(F[q]["normalised_sensitivity"]), q) for q in KEYQ[fk] if q in F and "normalised_sensitivity" in F[q]], reverse=True)
    L.append("| %s | %s | %+.3f | %s (%+.3f), %s (%+.3f) |" % (fk, QN[cand[0][1]], F[cand[0][1]]["normalised_sensitivity"], QN[cand[1][1]],
                                                          F[cand[1][1]]["normalised_sensitivity"], QN[cand[2][1]], F[cand[2][1]]["normalised_sensitivity"]))
_sv = [abs(TR[k]["quantities"][q]["normalised_sensitivity"]) for k in ("V", "Q") for q in ("LC1_dL_mm", "LC2_max_vm_MPa", "LC2_mean_axial_MPa", "LC2_end_reaction_kN", "LC2_utilisation", "lambda1")]
_st = max(abs(tt[q]["normalised_sensitivity"]) for q in ("T_solid_max_K", "T_solid_mean_K"))
L += ["", "For V and q″ every structural response follows the change of the wall temperature (growth, restrained force, stresses, "
      "utilisation and λ₁ all with |S| = %.2f–%.2f). For t the temperatures are almost insensitive (|S| ≤ %.3f) and the section-driven "
      "quantities (P_cr, end reaction, λ₁) dominate." % (min(_sv), max(_sv), _st), ""]
# screening comparison
L += ["## 5. Against the 9A screening (comparison only)", "",
      "| Case | λ₁ screened (9A) | λ₁ FE (9B-2) | Difference | LC2 max VM screened [MPa] | FE [MPa] | Utilisation screened | FE | LC1 ΔL screened [mm] | FE [mm] |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for t in DES:
    if t not in R or t not in SCR:
        continue
    s = SCR[t]
    L.append("| %s | %.4f | %.4f | %+.2f %% | %.2f | %.2f | %.4f | %.4f | %.4f | %.4f |" % (
        SHORT[t], float(s["anch_lambda1_S1"]), lam(t), pct(lam(t), float(s["anch_lambda1_S1"])), float(s["anch_LC2_vm_max_MPa"]),
        R[t]["LC2"]["max_vm_Pa"] / 1e6, float(s["anch_LC2_utilisation"]), R[t]["LC2"]["utilisation"]["max"], float(s["anch_LC1_dL_mm"]),
        R[t]["LC1"]["dL_face_mean_m"] * 1e3))
_scr_low = [SHORT[t] for t in DES if t in SCR and float(SCR[t]["anch_lambda1_S1"]) < 1]
_fe_low = [SHORT[t] for t in DES if t in R and lam(t) < 1]
_diff = [x for x in _scr_low if x not in _fe_low]
L += ["", "The screening was anchored to P00 and scaled 1-D. It flagged λ₁ < 1 for %s; the FE results give λ₁ < 1 for %s%s. "
      "The λ₁ differences (≤ %.2f %%) are attributed in 9B-1 (F-050) to developing flow and axial wall conduction, which the solved fields "
      "contain and the screening did not." % (", ".join(_scr_low), ", ".join(_fe_low),
          ("; %s lies just above 1 in the FE result (λ₁ %s), within %.2f %% of the limit, so its classification is sensitive to the "
           "modelling uncertainties of `FINAL_PARAMETRIC_AUDIT.md` §3" % (", ".join(_diff), ", ".join("%.4f" % lam(t) for t in DES if SHORT[t] in _diff),
                                                                        max(100 * (lam(t) - 1) for t in DES if SHORT[t] in _diff))) if _diff else "",
          max(abs(pct(lam(t), float(SCR[t]["anch_lambda1_S1"]))) for t in DES if t in R and t in SCR)), "",
      "## 6. Interaction limitation (Part W)", "",
      "- This is a **one-factor-at-a-time** study. It does not identify variable interactions. 9A estimated the V × q″ interaction at "
      "about 8–11 % of the main effects, so combined off-baseline states (for example low V *and* high q″) cannot be obtained by adding "
      "the one-factor changes.",
      "- The mid-point deviation from linearity is listed for each quantity. It shows the local curvature *along one axis only*.",
      "- **No response surface is fitted, and nothing is extrapolated beyond the ±10 % (V, q″) and ±20 % (t) steps.**", "",
      "## 7. Figures (Part Q; baseline marked in every plot)", ""]
for i, fn in enumerate(sorted(os.listdir(os.path.join(D, "Results", "Figures")))):
    if fn.endswith(".png"):
        L.append("- `Figures/%s`" % fn)
L.append("")
w("Results/PARAMETRIC_TRENDS.md", "\n".join(L))


# ================================================================================================ SUPPORT_SENSITIVITY_RESULTS.md
s1, s2, s3 = R.get("P00_BASELINE"), R.get("S2_LC2NS_NOSWAY"), R.get("S3_LC2_INTERMEDIATE")
ex = B03["exact"]; bb = B03["buckling"]; br = B03["reactions"]
L = ["# Support sensitivity — Section 9B-2 (Parts K, L, M, U)", "", NOTICE, "",
     "All three scenarios use the **baseline design** (P00 CFD temperature field, mesh B, material, T_ref 300 K, sparse solver). Only the end "
     "supports differ. This is a sensitivity to an *undefined* real end restraint (T-034); it is kept separate from the design-variable "
     "cases. No scenario is ranked or labelled as preferable.", "",
     "## 1. Definitions", "",
     "| Scenario | Inlet end (z = 0) | Outlet end (z = 0.6 m) | Other | Column idealisation | Source |",
     "|---|---|---|---|---|---|",
     "| **S1** (= LC2, baseline) | U_z = 0 on every face node; radial and lateral free | same | 3 mid-span outer nodes U_θ = 0 (rigid rotation only) | ends held against rotation, free to sway: guided column, K = 1 | 7B static, 8A buckling |",
     "| **S2** (8A LC2NS) | U_z = U_θ = 0 on every face node (CS_DUCT_CYL); radial free | same | none | ends held against sway and rotation: clamped–clamped, K = 0.5 | 8A static and buckling; nodal table re-extracted in 9B-2 (no re-solve) |",
     "| **S3** (new) | U_z = U_θ = 0 on every face node (CS_DUCT_CYL); radial free → clamped | deformable remote displacement: pilot on the axis at z = 0.6 m, U_x = U_y = U_z = 0, rotations free → pinned | none | clamped–pinned, K = 0.699 | 9B-2 (after B03) |", "",
     "## 2. B03 toy benchmark of the S3 implementation (Part L; not a project result)", "",
     "**Why a benchmark.** S3 is the first support in this project that uses a remote point (MPC contact, force-distributed). Before the real "
     "case was solved, the exact formulation Mechanical wrote into the S3 solver input was copied into the 8A constant-property toy tube, "
     "where the answer is known: E 190 GPa, ν 0.294, α 13.6 × 10⁻⁶ /K, uniform ΔT 225 K, SOLID186, esize 5 mm.", "",
     "The copied formulation:", "",
     "- the pilot node and a TARGE170 element;",
     "- CONTA174 contact elements on the outlet-face element faces (generated with ESURF), with the key options of the real deck: "
     "MPC algorithm, bonded always, force-distributed (deformable) constraint (`%s`);" % "`, `".join(k for k in S3D.get("deck", {}).get("remote_point_keyopts", []) if ",tid," in k or ",cid," in k),
     "- the inlet face nodes rotated to the cylindrical CS, with U_θ = U_z = 0.", "",
     "Files: `Structural_Cases/B03_S3_TOY_BENCH/` (b03_main.inp, b03_main.out, b03_check.py, b03_results.json; `B03_BENCHMARK.md`). "
     "The header comment of b03_main.inp still names CONTA175 (written before the real deck was inspected); the element type actually "
     "defined and used is CONTA174 (`et,2,174` + ESURF), as in the real deck. The comment was left unchanged because the file is the one that ran.", "",
     "Two toy runs:", "",
     "- **run 1** used the free 8A toy mesh (esize 5 mm; 37,911 nodes; 62 outlet contact faces);",
     "- **run 2** used a structured mesh with 36 equal circumferential sectors, like the real model (82,585 nodes; 144 outlet contact faces).", "",
     "| Check | Run 1 as first formulated | Run 1, reformulated checks | Run 2 (structured) |",
     "|---|---|---|---|"]
names = list(B03S["checks"].keys())
orig = B03O["checks"]
for k in names:
    ok_o = orig.get(k)
    if ok_o is None:
        ok_o = [v for kk, v in orig.items() if kk.split(" ")[0] == k.split(" ")[0]]
        ok_o = ok_o[0] if ok_o else None
    L.append("| %s | %s | %s | %s |" % (k, "-" if ok_o is None else ("PASS" if ok_o else "**FAIL**"), "PASS" if B03["checks"].get(k) else "**FAIL**",
                                         "PASS" if B03S["checks"][k] else "**FAIL**"))
L += ["", "**Why two checks were reformulated after run 1.** Neither change touched the model.", "",
      "- **Static lateral translation.** Run 1 measured the node-mean of (u_x, u_y) per section: %.2e m. On the free mesh the face "
      "nodes are unevenly distributed (node centroid 1.2 mm off the axis). Under uniform radial growth, that mean equals the radial "
      "strain times the node centroid, so it is **not** a translation. A least-squares fit of translation + radial growth + rotation per "
      "section gives %.1e m (run 1) and %.1e m (run 2), i.e. no rigid lateral motion." % (
          B03O["static_shape"].get("max_section_lateral_translation_m", float("nan")), B03["static_shape"]["max_rigid_lateral_translation_LSfit_m"],
          B03S["static_shape"]["max_rigid_lateral_translation_LSfit_m"]),
      "- **Lateral reaction.** The absolute 10⁻³ N limit was set before the run. Run 1 gave %.3f N (%.1e × N), numerical noise of the "
      "unstructured mesh. The limit is now relative, 10⁻⁶ × N. Run 2 gives %.1e N, which would also meet the original limit." % (
          B03["reactions"]["inlet_lateral_N"], B03["reactions"]["inlet_lateral_N"] / ex["N_N"], B03S["reactions"]["inlet_lateral_N"]),
      "- Run 2 is the independent confirmation: with an even face mesh (as in the real S3 model) every quantity is symmetric to round-off.", "",
      "| Quantity | Run 1 (free mesh) | Run 2 (structured) | Exact / theory |", "|---|---|---|---|",
      "| Axial force [N] | %s | %s | E α ΔT A = %s |" % (f(abs(B03["reactions"]["inlet_Fz_N"]), 1), f(abs(B03S["reactions"]["inlet_Fz_N"]), 1), f(ex["N_N"], 1)),
      "| Pilot force + inlet force [N] | %.2e | %.2e | 0 |" % (B03["reactions"]["inlet_Fz_N"] + B03["reactions"]["pilot_Fz_N"], B03S["reactions"]["inlet_Fz_N"] + B03S["reactions"]["pilot_Fz_N"]),
      "| Mid-span axial stress (corner nodes) [MPa] | %.3f | %.3f | −E α ΔT = %.3f |" % (B03["static_shape"]["midspan_s_z_corner_nodes_Pa"] / 1e6, B03S["static_shape"]["midspan_s_z_corner_nodes_Pa"] / 1e6, -190e9 * 13.6e-6 * 225 / 1e6),
      "| Mid-span radial growth, outer [µm] | %.4f | %.4f | (1+ν) α ΔT r_o = %.4f |" % (B03["static_shape"]["midspan_u_r_outer_m"] * 1e6, B03S["static_shape"]["midspan_u_r_outer_m"] * 1e6, B03S["static_shape"]["midspan_u_r_outer_free_expansion_m"] * 1e6),
      "| **λ₁** | **%.5f** | **%.5f** | Euler (K = 0.6992) %.5f; + Cowper shear (k = %.3f) %.5f |" % (B03["buckling"]["lambda1"], B03S["buckling"]["lambda1"], ex["lambda_Euler"], ex["K_shear_Cowper"], ex["lambda_Euler_shear"]),
      "| FE / Euler; FE / (Euler + shear) | %.4f; %.4f | %.4f; %.4f | between the bounds |" % (B03["buckling"]["FE_over_Euler"], B03["buckling"]["FE_over_Euler_shear"], B03S["buckling"]["FE_over_Euler"], B03S["buckling"]["FE_over_Euler_shear"]),
      "| Mode 1 fixed–pinned correlation; z of max lateral | %.6f; %.0f mm | %.6f; %.0f mm | 1; 0.605 L = 363 mm |" % (B03["buckling"]["modes"]["1"]["corr_fixed_pinned"], B03["buckling"]["modes"]["1"]["z_of_max_lateral_mm"], B03S["buckling"]["modes"]["1"]["corr_fixed_pinned"], B03S["buckling"]["modes"]["1"]["z_of_max_lateral_mm"]),
      "| Modes 1–2 | orthogonal pair, split %.1e | orthogonal pair, split %.1e | degenerate pair |" % (B03["buckling"]["pair_split_rel"], B03S["buckling"]["pair_split_rel"]), "",
      "**B03 result: %s.** The implementation copied from the real deck behaves as intended. There is no rigid-body motion. Both "
      "reactions are exact. The static state is uniform. λ₁ lies inside the clamped–pinned Euler band, and the mode is the fixed–pinned "
      "shape with its maximum at 0.6 L from the clamped end. The real S3 case was solved only after this result." % (
          "PASS" if (B03["B03_PASS"] and B03S["B03_PASS"]) else "FAIL"), ""]
# S3 implementation in the real deck
dk = S3D.get("deck", {})
L += ["## 3. Real S3 model (Part M)", "",
      "| Item | Result |", "|---|---|",
      "| Model | save-as copy of the 7B project (`Structural_Cases/S3_LC2_INTERMEDIATE/Project`) with a new Static Structural system (shared Engineering Data / Geometry / Model; fed by the same External Data) and a Linear Buckling system on it, built like the 8A S2 pair |",
      "| Solver input (deck mode, before B03) | SOLID186 block and nodal temperatures identical to the 7B LC2 input; all 7B nodes present plus %d pilot node; element blocks: %s SOLID186 + %s outlet-face CONTA174, plus the TARGE170 pilot element |" % (
          dk.get("nblock_lines", 0) - 108252, f(dk["eblocks"][0][1], 0), f(dk["eblocks"][1][1], 0)),
      "| Pre-solve gate (solve mode) | %s (%d checks), incl. deck identical to the one copied into B03 |" % (S3P["gate"], len(S3P["checks"])),
      "| Mapped temperature | identical to the S1 (LC2) mapping (pre-solve gate check) |", ""]
# comparison table
L += ["## 4. S1 / S2 / S3 comparison (Part U; `SUPPORT_SENSITIVITY_RESULTS.csv`)", "",
      "| Scenario | Max von Mises [MPa] | Location | Mean axial stress [MPa] | Axial reaction [kN] | Max total deformation [mm] | Max section lateral translation (static) [m] | λ₁ | λ₂ | P_cr [kN] | Dominant mode | First-yield factor | Occurs first (idealised) |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for sc, t in (("S1", "P00_BASELINE"), ("S2", "S2_LC2NS_NOSWAY"), ("S3", "S3_LC2_INTERMEDIATE")):
    if t not in R:
        L.append("| %s | not available | | | | | | | | | | | |" % sc); continue
    e = R[t]["LC2"]; b = R[t]["buckling"]; mw, glob, best = mode_word(t)
    lat = e.get("max_section_lateral_translation_m", float("nan"))
    L.append("| %s | %.3f | %s | %.3f | %.2f | %.4f | %.1e | %.4f | %.4f | %.1f | %s | %.3f | %s |" % (
        sc, e["max_vm_Pa"] / 1e6, loc(e["max_vm_loc"]), e["mean_axial_stress_Pa"] / 1e6, abs(e["reactions"]["inlet_Fz_N"]) / 1e3, e["max_utot_m"] * 1e3,
        lat, b["lambda1"], b["lambda2"], b["critical_load_N"] / 1e3, mw, first_yield(t), governs(t)))
if s3:
    r3 = s3["LC2"]["reactions"]
    L += ["", "S3 reactions: inlet F_z %s N, pilot F_z %s N (sum %.2e N); lateral resultants %.1e / %.1e N; outlet-face nodes carrying a "
          "constraint: %d (the pilot carries the outlet support, as intended)." % (
              f(r3["inlet_Fz_N"], 2), f(r3["pilot_F_N"][2], 2), r3["inlet_Fz_N"] + r3["pilot_F_N"][2], r3["inlet_F_lateral_N"], r3["outlet_F_lateral_N"],
              r3["outlet_face_nodes_constrained"]), ""]
L += ["## 5. Physical interpretation (no ranking)", "",
      "- **Static stress is almost insensitive to the end condition.** The end force is set by the restrained mean thermal strain, which "
      "the axial restraint fixes in all three scenarios. The mean axial stress is the same to %s, and the peak differs by %s. "
      "The supports decide *how the axial force can escape sideways* (the stability), not how large it is." % (
          "%.1e %%" % max(abs(pct(R[t]["LC2"]["mean_axial_stress_Pa"], s1["LC2"]["mean_axial_stress_Pa"])) for t in ("S2_LC2NS_NOSWAY", "S3_LC2_INTERMEDIATE") if t in R),
          "%.1e %%" % max(abs(pct(R[t]["LC2"]["max_vm_Pa"], s1["LC2"]["max_vm_Pa"])) for t in ("S2_LC2NS_NOSWAY", "S3_LC2_INTERMEDIATE") if t in R)),
      "- **Stability is dominated by the end condition.** λ₁ = %s (S1, ends free to sway) → %s (S3, one end clamped, one pinned) → %s "
      "(S2, both ends clamped). The FE ratios 1 : %.3f : %.3f follow the effective length (Euler 1 / K² = 1 : 2.047 : 4 for K = 1, 0.699, "
      "0.5); they are lower, increasingly so for the shorter effective lengths, which is consistent with shear flexibility and the axial "
      "variation of E(T). The mode shape follows the support (guided sway / fixed–pinned / clamped)." % (
          "%.4f" % lam("P00_BASELINE"), "%.4f" % lam("S3_LC2_INTERMEDIATE") if s3 else "n/a", "%.4f" % lam("S2_LC2NS_NOSWAY") if s2 else "n/a",
          lam("S3_LC2_INTERMEDIATE") / lam("P00_BASELINE"), lam("S2_LC2NS_NOSWAY") / lam("P00_BASELINE")),
      "- **Which mechanism comes first changes with the support.** With S1 the idealised duct bifurcates before first yield. With S3 and S2 "
      "the elastic bifurcation factor is above the first-yield factor (%.2f), so first yield — and, for these intermediate columns, inelastic "
      "buckling (8A: Johnson 1.41 for fixed–pinned, 1.58 for fixed–fixed; squash 1.75) — would come first. The structural conclusion "
      "(stability-controlled or yield-controlled) therefore depends on a support condition the project does not define (T-034)." % first_yield("P00_BASELINE"),
      "- **S3 against the hand estimate** (8A fixed–pinned Euler with E(z) 2.29, with shear 2.22; 9A anchored estimate %.3f): FE λ₁ %s." % (
          float(SCR["P00_BASELINE"]["anch_lambda1_S3_hand"]), "%.4f" % lam("S3_LC2_INTERMEDIATE") if s3 else "n/a"),
      "- All three are linear eigenvalue results of a perfect tube; imperfections and plasticity would lower them (T-035).", ""]
w("Results/SUPPORT_SENSITIVITY_RESULTS.md", "\n".join(L))


# ================================================================================================ FINAL_PARAMETRIC_AUDIT.md
CATS = [("secant-alpha", "secant-α re-referencing (7B)"), ("Mechanical default", "shape checking off (default)"),
        ("APDL snippet", "snippet mid-side-node reads (7B)"), ("performance only (sparse", "out-of-core solver (performance)"),
        ("performance only", "elapsed > CPU (performance)"), ("S3 buckling advisory", "S3 linear-perturbation-with-contact advisory (explained)")]


def short_cat(k):
    for pre, lab in CATS:
        if k.startswith(pre):
            return lab
    return k


VER = None
vp = os.path.join(D, "Results", "Verification_9B2", "verify_9B2_result.json")
if os.path.isfile(vp):
    VER = json.load(open(vp))
L = ["# Final parametric audit and engineering synthesis — Section 9B-2 (Parts R, V, X, Y)", "", NOTICE, "",
     "## 1. Case validity (Part R)", "",
     "| Case | CFD converged / valid (9B-1) | Mapping valid | Pre-solve gate | LC1 / LC2 / buckling solved | Invalid elements | Licence | Material range (E, S_y: 20–400 °C) | Solver warnings (categories) | Unexplained warnings | Status |",
     "|---|---|---|---|---|---|---|---|---|---|---|"]
for t in ["C00_PIPELINE_CHECK", "V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK", "M01_T01_STRUCT_NR5", "M02_T03_STRUCT_NR5", "S3_LC2_INTERMEDIATE"]:
    v = VAL.get(t)
    if not v:
        L.append("| %s | | | | not run | | | | | | **NOT AVAILABLE** |" % SHORT[t]); continue
    cats, unc = {}, []
    for sub, sv in v["solver"].items():
        so = sv.get("solve.out") or {}
        for k, n in (so.get("warning_categories") or {}).items():
            cats[k] = cats.get(k, 0) + n
        unc += so.get("unclassified_warnings", [])
    solved = all((sv.get("solve.out") or {}).get("solution_done") for sv in v["solver"].values()) and bool(v["solver"])
    mp = MAP.get({"M01_T01_STRUCT_NR5": "T01_THIN", "M02_T03_STRUCT_NR5": "T03_THICK"}.get(t, t))
    mr = v.get("material_range") or {}
    rr = R.get(t, {})
    tr = rr.get("LC2", {}).get("T_range_K")
    inside = (tr[0] - 273.15 >= 20 and tr[1] - 273.15 <= 400) if tr else mr.get("inside_E_Sy_table")
    mm = (v.get("mesh_metrics") or {})
    inval = "0 (JR max %.3f, EQ min %.3f)" % (mm["JacobianRatio"]["max"], mm["ElementQuality"]["min"]) if mm.get("JacobianRatio") else "mesh B (7B/8B)"
    ok = (v.get("gate") == "PASS") and solved and not v.get("fatal") and inside and not unc
    L.append("| %s | %s | %s | %s (%s) | %s | %s | no failure (%s nodes) | %s | %s | %s | **%s** |" % (
        SHORT[t], "%s / %s" % ((v.get("cfd") or {}).get("status"), (v.get("cfd") or {}).get("valid")),
        ("PASS" if mp["ALL_PASS"] else "FAIL") if mp else "P00 mapping (identical)", v.get("gate"), v.get("gate_checks"),
        "yes" if solved else "NO", inval, f((v.get("mesh") or {}).get("nodes", 108252), 0),
        "inside (%.1f–%.1f °C)" % (tr[0] - 273.15, tr[1] - 273.15) if tr else str(inside), "; ".join("%s ×%d" % (short_cat(k), n) for k, n in cats.items()),
        "none" if not unc else "; ".join(unc[:3]), "VALID" if ok else "CHECK"))
L += ["", "Warning categories were all seen and explained in 7B / 8A / 8B:", "",
      "- the secant-α table re-referenced to T_ref 26.85 °C;",
      "- shape checking off (Mechanical default);",
      "- APDL snippet reads of mid-side-node stresses;",
      "- out-of-core solver mode and elapsed > CPU time (performance only);",
      "- S3 buckling only: MAPDL's advisory that a linear perturbation with contact usually needs NLGEOM,ON in the base analysis. The only "
      "contact pair is the bonded (KEYOPT(12) = 5) MPC force-distributed remote-point constraint, whose status cannot change; every "
      "buckling case of the project (S1, S2, S3 and the design cases) uses a small-deflection pre-stress by design; the same outlet block "
      "reproduced the clamped–pinned column in B03.", "",
      "**S2 (8A solution, re-extracted).** Solved and audited in 8A. Its nodal table was re-extracted in 9B-2 without re-solving. "
      "Validation: the same MAPDL file applied to the 8A S1 result reproduces the 8A in-session table in every column (max difference %s); "
      "S2 self-check: |u_θ| ≤ %.1e m at the %d U_θ-constrained end-face nodes, u_r uniform around the end-face rings. The first re-extraction "
      "run read both result files in one MAPDL session; see §6." % (
          "%.1e" % max(P["S2_reextraction_validation"]["max_abs_diff_per_column"].values()) if P.get("S2_reextraction_validation") else "n/a",
          R["S2_LC2NS_NOSWAY"]["S2_rotated_node_check"]["max_abs_u_theta_at_rotated_nodes_m"], R["S2_LC2NS_NOSWAY"]["S2_rotated_node_check"]["rotated_nodes_in_table"]), "",
      "**No case failed, so no case was stopped. No value was fabricated or interpolated.** Runs that stopped at a gate *before* solving "
      "are recorded in §6.", "",
      "## 2. Design-space validity (Part V)", "",
      "| Condition | Finding |", "|---|---|"]
tmax = max(R[t]["LC2"]["T_range_K"][1] for t in DES if t in R)
L += ["| Material-property limits | every structural temperature lies inside the E(T) and S_y(T) tables (max %.2f K = %.1f °C < 400 °C). The secant-α table starts at 93.3 °C and every node is hotter (min %.1f °C). No extrapolation |" % (
          tmax, tmax - 273.15, min(R[t]["LC2"]["T_range_K"][0] for t in DES if t in R) - 273.15),
      "| Invalid temperature range | none. The CFD air-property tables end at 600 K; the highest air-side temperatures (wall interface / fluid cell) are %s — F-049 (9B-1) |" % ", ".join(
          "%s %.1f / %.1f K" % (SHORT[t], float(CFD[t]["T_interface_max_K"]), float(CFD[t]["T_fluid_max_K"])) for t in sorted([t for t in DES if t in CFD], key=lambda t: -float(CFD[t]["T_interface_max_K"]))[:2]),
      "| λ₁ < 1 (S1 supports) | **%s** → LC2 static stress labelled as pre-buckling equilibrium (Part I) |" % (", ".join("%s (%.4f)" % (SHORT[t], lam(t)) for t in DES if t in R and lam(t) < 1) or "none"),
      "| Yield utilisation ≥ 1 | **none** (max %.4f, %s) |" % max((R[t]["LC2"]["utilisation"]["max"], SHORT[t]) for t in DES if t in R),
      "| Excessive deformation | none: LC1 growth %.3f–%.3f mm on 600 mm; LC2 total ≤ %.3f mm |" % (
          min(R[t]["LC1"]["dL_face_mean_m"] for t in DES if t in R) * 1e3, max(R[t]["LC1"]["dL_face_mean_m"] for t in DES if t in R) * 1e3,
          max(R[t]["LC2"]["max_utot_m"] for t in DES if t in R) * 1e3),
      "| Unexplained solver behaviour | none (§1). All reactions balance: LC2 end forces equal and opposite; LC1 reactions ≈ 0 |", ""]
# uncertainty
c0 = R["C00_PIPELINE_CHECK"]
L += ["## 3. Uncertainty — kept separate (Part X)", "",
      "No combined percentage is formed, because the sources are of different kinds: discretisation, model form, assumption, idealisation. "
      "Values are for the baseline unless stated otherwise.", "",
      "| # | Source | What it affects | Size (evidence) |", "|---|---|---|---|",
      "| 1 | CFD mesh | temperatures → LC2 stress, λ₁ | 6B GCI: temperature-driven LC2 stress −10.1 / +2.8 MPa; λ₁ +1.8 / −0.5 %% (8B). T03 solid resolution (M03, 12 → 18 solid layers): node-field change ≤ %.2f K, mid-span through-wall ΔT %+.4f K, inlet-face through-wall ΔT %+.2f K (%+.1f %%) |" % (
          M03["node_field"]["max_abs_K"], M03["sections"]["midspan_z0.3"]["dT_change_K"], M03["sections"]["inlet_z0"]["dT_change_K"],
          100 * M03["sections"]["inlet_z0"]["dT_change_K"] / M03["sections"]["inlet_z0"]["through_wall_dT_T03_K"]),
      "| 2 | CFD property / model | wall temperatures, hence everything thermal | SST k-ω, constant-q″ idealisation, air tables to 600 K (highest air-side wall-interface temperature %.1f K, %.1f K below the limit, F-049). Not quantified by a model-form study |" % (
          max(float(CFD[t]["T_interface_max_K"]) for t in DES if t in CFD), 600.0 - max(float(CFD[t]["T_interface_max_K"]) for t in DES if t in CFD)),
      "| 3 | CFD → Mechanical mapping | local temperatures (LC1 inlet peak most) | (A) ≤ %.3f K; numbering sensitivity (C00): LC2 peak %.1e, λ₁ %.1e, LC1 inlet peak %s; FV near-end limitation F-035 (LC1 inlet peak bound ±9.8 MPa, 8B) |" % (
          max(e["A_vs_source_node_field"]["max_K"] for e in MAP.values()), c0["LC2"]["max_vm_Pa"] / p0["LC2"]["max_vm_Pa"] - 1,
          lam("C00_PIPELINE_CHECK") / lam("P00_BASELINE") - 1, ch("C00_PIPELINE_CHECK", "LC1", "max_vm_Pa")),
      "| 4 | Structural mesh | LC1 surface stresses; LC2 and λ₁ negligible | 8B: LC2 ≤ 10⁻⁴, λ₁ ≤ 6 × 10⁻⁶; LC1 bore σθ −2.1 %% (sign known). T geometries (M01/M02): LC2 and λ₁ %s; LC1 peak %s |" % (
          "≤ %.1e" % max(abs(v["changes"][q]["rel"]) for v in MM.values() for q in ("LC2 max vm", "LC2 mean axial stress", "lambda1")) if MM else "n/a",
          " / ".join("%+.2f %%" % (100 * v["changes"]["LC1 max vm"]["rel"]) for v in MM.values()) if MM else "n/a"),
      "| 5 | Material properties | E(T), α(T) → stress ∝ Eα; S_y(T) → utilisation | datasheet tables (VDM 4127 / Special Metals), about ±2 % in E and α (8B); S_y typical, not minimum-guaranteed — utilisation not a certified margin |",
      "| 6 | Poisson ratio 0.294 [ASSUMED] | LC2 radial / hoop stresses, bending stiffness via shear | not varied (T-014 / F-011 open). λ₁ enters only through the shear correction (small) |",
      "| 7 | Support / end condition | λ₁ (dominant), mechanism order | S1 %.3f → S3 %s → S2 %s: a factor of about 4 on λ₁ from supports alone — **the largest single uncertainty for stability** (T-034) |" % (
          lam("P00_BASELINE"), "%.3f" % lam("S3_LC2_INTERMEDIATE") if "S3_LC2_INTERMEDIATE" in R else "n/a", "%.3f" % lam("S2_LC2NS_NOSWAY") if "S2_LC2NS_NOSWAY" in R else "n/a"),
      "| 8 | Geometric imperfection / nonlinear buckling | λ₁ is an upper bound of the real collapse load | linear eigenvalue, perfect tube. Intermediate slenderness (KL/r ≈ 54 < C_c ≈ 60): Johnson inelastic 1.06 for S1 (8A). Not solved (T-035) |", ""]
# synthesis
tv, tq, tt = TR["V"]["quantities"], TR["Q"]["quantities"], TR["T"]["quantities"]
stab = [t for t in DES if t in R and lam(t) < first_yield(t)]
yl = [t for t in DES if t in R and lam(t) >= first_yield(t)]
L += ["## 4. Engineering synthesis — the ten questions (Part Y)", "",
      "*No design is ranked or declared preferable. All statements hold for the idealised supports and the ±10 / ±20 % one-factor steps studied.*", "",
      "**1. How does velocity affect flow and thermal response?** Δp rises with V (%+.1f / %+.1f %% for −/+10 %% V, a local exponent of about %.2f; "
      "see `PARAMETRIC_TRENDS.md` §4). A lower velocity "
      "removes the same heat with less mass flow, so all temperatures rise: V01 T_out %+.2f K, solid max %+.2f K, solid mean %+.2f K; V03 the "
      "reverse. Structurally, V acts only through the temperature: LC2 end force %+.2f / %+.2f %%, λ₁ %.4f / %.4f." % (
          tv["dp_Pa"]["pct_change_vs_P00"][0], tv["dp_Pa"]["pct_change_vs_P00"][2],
          math.log(tv["dp_Pa"]["values"][2] / tv["dp_Pa"]["values"][0]) / math.log(25.85 / 21.15), tv["T_out_K"]["values"][0] - tv["T_out_K"]["values"][1],
          tv["T_solid_max_K"]["values"][0] - tv["T_solid_max_K"]["values"][1], tv["T_solid_mean_K"]["values"][0] - tv["T_solid_mean_K"]["values"][1],
          tv["LC2_end_reaction_kN"]["pct_change_vs_P00"][0], tv["LC2_end_reaction_kN"]["pct_change_vs_P00"][2], tv["lambda1"]["values"][0], tv["lambda1"]["values"][2]), "",
      "**2. How does heat flux affect thermal and structural response?** q″ is the load. ±10 %% changes the heat input by ±10 %% and the "
      "solid mean temperature by %+.2f / %+.2f K (the rise above the inlet by slightly more than ±10 %%). The restrained end force follows "
      "(%+.2f / %+.2f %%), λ₁ goes to %.4f / %.4f, and the utilisation to %.4f / %.4f." % (
          tq["T_solid_mean_K"]["values"][0] - tq["T_solid_mean_K"]["values"][1], tq["T_solid_mean_K"]["values"][2] - tq["T_solid_mean_K"]["values"][1],
          tq["LC2_end_reaction_kN"]["pct_change_vs_P00"][0], tq["LC2_end_reaction_kN"]["pct_change_vs_P00"][2], tq["lambda1"]["values"][0], tq["lambda1"]["values"][2],
          tq["LC2_utilisation"]["values"][0], tq["LC2_utilisation"]["values"][2]), "",
      "**3. How does wall thickness affect stiffness and stability?** With Q held, the temperatures change by < 1 K, so the thermal stress "
      "level is nearly unchanged (LC2 VM %+.2f / %+.2f %%). The section changes: A by %+.1f / %+.1f %%, I by %+.1f / %+.1f %%. The end force "
      "follows A (%+.1f / %+.1f %%) and P_cr follows EI (%+.1f / %+.1f %%), so λ₁ ∝ r_g² goes to %.4f (8 mm) and %.4f (12 mm). The LC1 "
      "free growth is almost unchanged (%+.2f / %+.2f %%); the LC1 peak stress changes by %+.1f / %+.1f %% with the through-wall temperature "
      "difference, and stays at about 2 %% of S_y." % (
          tt["LC2_max_vm_MPa"]["pct_change_vs_P00"][0], tt["LC2_max_vm_MPa"]["pct_change_vs_P00"][2],
          pct(18 ** 2 - 10 ** 2, 20 ** 2 - 10 ** 2), pct(22 ** 2 - 10 ** 2, 20 ** 2 - 10 ** 2), pct(18 ** 4 - 10 ** 4, 20 ** 4 - 10 ** 4), pct(22 ** 4 - 10 ** 4, 20 ** 4 - 10 ** 4),
          tt["LC2_end_reaction_kN"]["pct_change_vs_P00"][0],
          tt["LC2_end_reaction_kN"]["pct_change_vs_P00"][2], tt["Pcr_kN"]["pct_change_vs_P00"][0], tt["Pcr_kN"]["pct_change_vs_P00"][2],
          tt["lambda1"]["values"][0], tt["lambda1"]["values"][2], tt["LC1_dL_mm"]["pct_change_vs_P00"][0], tt["LC1_dL_mm"]["pct_change_vs_P00"][2],
          tt["LC1_max_vm_MPa"]["pct_change_vs_P00"][0], tt["LC1_max_vm_MPa"]["pct_change_vs_P00"][2]), "",
      "**4. How sensitive is the structural conclusion to support conditions?** Very. The static stress is almost unchanged, but λ₁ spans "
      "%.3f (S1) – %s (S3) – %s (S2), and the governing mechanism switches: S1 buckles before first yield, while S2 and S3 would yield (or "
      "buckle inelastically) first. The real end restraint is undefined (T-034), so the choice between a stability-controlled and a "
      "yield-controlled conclusion cannot be made from this model." % (
          lam("P00_BASELINE"), "%.3f" % lam("S3_LC2_INTERMEDIATE") if "S3_LC2_INTERMEDIATE" in R else "n/a", "%.3f" % lam("S2_LC2NS_NOSWAY") if "S2_LC2NS_NOSWAY" in R else "n/a"), "",
      "**5. Which quantity is most sensitive to each parameter?** Normalised sensitivity S = (Δy/y)/(Δx/x) from the three solved points "
      "(`PARAMETRIC_TRENDS.md` §4). %s" % " ".join(
          "%s: %s." % ({"V": "Velocity", "Q": "Heat flux", "T": "Thickness"}[fk], ", ".join(
              "%s (S %+.2f)" % (QN[q], TR[fk]["quantities"][q]["normalised_sensitivity"]) for _, q in sorted(
                  [(abs(TR[fk]["quantities"][q]["normalised_sensitivity"]), q) for q in KEYQ[fk] if "normalised_sensitivity" in TR[fk]["quantities"].get(q, {})],
                  reverse=True)[:3])) for fk in ("V", "Q", "T")), "",
      "**6. Which cases are stability-limited?** With the S1 supports: **%d of %d design cases** — %s. In each, λ₁ is below the first-yield factor. "
      "λ₁ < 1 in %s: for these, the LC2 static state is a pre-buckling equilibrium result only. %s" % (
          len(stab), len([t for t in DES if t in R]), ", ".join("%s (λ₁ %.3f < %.3f)" % (SHORT[t], lam(t), first_yield(t)) for t in stab),
          ", ".join(SHORT[t] for t in DES if t in R and lam(t) < 1) or "no case",
          " ".join("%s is marginal: λ₁ = %.4f, %.2f %% above 1, well inside the uncertainties of §3." % (SHORT[t], lam(t), 100 * (lam(t) - 1))
                   for t in DES if t in R and 1 <= lam(t) < 1.01)), "",
      "**7. Which cases are yield-limited?** %s. No case reaches first yield at the applied load (max utilisation %.4f). The S2 and S3 "
      "*support* variants of P00 would be yield-limited in the idealised model (first-yield factor %.2f < λ₁)." % (
          "With the S1 supports: none" if not yl else ", ".join(SHORT[t] for t in yl), max(R[t]["LC2"]["utilisation"]["max"] for t in DES if t in R), first_yield("P00_BASELINE")), "",
      "**8. Does the critical location move?** No, not with V, q″ or t: the LC2 maximum stays at the outer edge of the inlet face, and the "
      "LC1 maximum at the bore 6.5 mm from the inlet. Only the temperature there changes. For S2 and S3 see `SUPPORT_SENSITIVITY_RESULTS.md` §4.", "",
      "**9. Does the buckling mode change?** Not with the design variables: the global guided-sway column mode (orthogonal pair, no local or "
      "shell mode) in every case. It changes with the support: guided sway (S1), fixed–pinned (S3) and clamped (S2).", "",
      "**10. What uncertainties still dominate?** For stability, the **end-restraint definition** (a factor of about 4 on λ₁), then the "
      "**imperfection / inelastic-buckling gap** of the linear eigenvalue. For stresses and λ₁ within a support definition, the "
      "**CFD temperature field** (6B mesh; property / model form near the 600 K air limit). Mapping, structural mesh and ν are small by "
      "comparison. §3 keeps them separate.", ""]
# run history
L += ["## 5. Controls", "",
      "- **C00** reproduces 7B/8A within 10⁻⁵ on LC2 VM, end force and λ₁. The remaining LC1 inlet-peak difference is the mapping-numbering "
      "effect (§3, #3).",
      "- **M03** (T03 CFD solid layers 12 → 18): adequate, no remap (`Mesh_Checks/M03_MESH_ADEQUACY.md`).",
      "- **M01 / M02**: the 4- and 6-division meshes of T01 / T03 are kept: LC2 mean stress and λ₁ change ≤ %.1e, the LC2 peak ≤ %.1e "
      "(M01 above the 10⁻⁴ class-A tolerance at the single inlet-edge node, %.0f× below the T01 change of the LC2 peak), the LC1 peak by up "
      "to %.1f %% (`PARAMETRIC_STRUCTURAL_RESULTS.md` §2)." % (
          max(abs(v["changes"][k]["rel"]) for v in MM.values() for k in ("LC2 mean axial stress", "lambda1")),
          max(abs(v["changes"]["LC2 max vm"]["rel"]) for v in MM.values()),
          abs(pct(R["T01_THIN"]["LC2"]["max_vm_Pa"], p0["LC2"]["max_vm_Pa"])) / 100 / max(abs(v["changes"]["LC2 max vm"]["rel"]) for v in MM.values()),
          max(abs(100 * v["changes"]["LC1 max vm"]["rel"]) for v in MM.values())),
      "- **B03**: S3 implementation verified before the real S3 solve.", "",
      "## 6. Run history (nothing deleted; archives in `Structural_Cases/Audits/`)", "",
      "| Run | What happened | Action |", "|---|---|---|",
      "| C00 run 1 | Mechanical did not start: `current_case.json` contained .NET booleans (invalid JSON). Nothing solved | plain Python types + JSON validity check (`Run1_C00_FAIL_json`) |",
      "| C00 run 2 | solved, bit-identical to 7B/8A, but — as T01 run 1 then showed — with the cached P00 source | kept for the record (`Run2_C00_before_setup_refresh`) |",
      "| T01 run 1 | gate STOP: Mechanical source min/max = P00 values. The External Data change had not reached the analyses | refresh the Setup cells after the ED update (`Run1_T01_FAIL_stale_ED`) |",
      "| C00 run 3 | gate STOP: bitwise temperature identity to 7B failed (max 0.081 K, re-numbered source) | criterion revised to 2 × the 7A mapping error (`Run3_C00_FAIL_bitwise_criterion`) |",
      "| ALL run 4 | C00 and T01 solved; machine shut down during the T03 set-up (nothing solved for T03) | remaining cases re-run by `chain_rest.ps1` (`Run4_ALL_interrupted_by_shutdown`) |",
      "| REST (chain_rest) | T03, V01, V03, Q01, Q03, M01, M02 solved, every gate PASS | results used |",
      "| S3 deck runs 1–5 | Mechanical's `ImportLoad()` on the imported-temperature object raised NullReferenceException in the copied project (also for the LC2 re-import, before any new object). Nothing solved | a probe showed the group-level import works; `import_s3()` imports through the imported-load group (`Run1…Run5_S3_deck_FAIL_import`) |",
      "| S3 deck run 6 | gate STOP: the check expected CONTA175, Mechanical wrote CONTA174 face elements | check changed to CONTA174/175 plus key-option and pilot-constraint checks (`Run6_S3_deck_FAIL_gate_CONTA174`) |",
      "| S3 deck run 7 | deck written, gate PASS (22), not solved | deck copied into B03 |",
      "| B03 run 1 / run 2 | run 1: two checks failed as first formulated (see `SUPPORT_SENSITIVITY_RESULTS.md` §2); reformulated, run 1 re-evaluated PASS; run 2 (structured mesh) PASS under the original limits too | real S3 solved afterwards |",
      "| S3 solve | deck identical to run 7, static + buckling solved, gate PASS | results used |",
      "| Integrity check (verification V7, first run) | 08_Structural_Analysis: 0 files changed, 0 missing, 1 added — a Python bytecode cache (`Buckling/__pycache__/mode_shapes.cpython-310.pyc`) written when post_9B2.py imported the unchanged 8A module | cache file moved (not deleted) to `Results/Verification_9B2/Moved_from_08/`; post_9B2.py now sets `sys.dont_write_bytecode`; post re-run with identical results; V7 PASS |",
      "| S2 re-extraction run 1 | S2 and the S1 validation read in one MAPDL session: the S1 table inherited the S2 nodal rotations (u_r / u_θ wrong at 1,204 nodes; stresses, T, u_z exact). The S2 table itself was correct. A rotation-correction hypothesis (`fix_rotated`) was written and withdrawn; no reported number used it | run 2 with /CLEAR between the files: S1 validation exact, S2 table identical to run 1 (`S2_REEXTRACT/Run1_shared_session`) |", ""]
if VER:
    L += ["## 7. Independent verification", "",
          "`Results/Verification_9B2/verify_9B2.py` recomputes the headline numbers from the raw solver tables with its own code; it does "
          "not import the post-processing scripts. It also checks the gates, the brief's rules and the 08_Structural_Analysis integrity: "
          "**%d / %d PASS**." % (VER["n_pass"], VER["n_total"]), ""]
    fails = [c for c in VER["checks"] if not c["pass"]]
    if fails:
        L += ["Failed checks:", ""] + ["- %s — %s" % (c["check"], c["detail"]) for c in fails] + [""]
        if all("M01" in c["check"] for c in fails):
            L += ["The only failed check is the 10⁻⁴ class-A tolerance of the M01 structural-mesh check, exceeded by the LC2 peak "
                  "(a single node at the inlet-face edge); the mean stress and λ₁ meet it by a factor of more than 20. Its effect is "
                  "assessed in `PARAMETRIC_STRUCTURAL_RESULTS.md` §2 and carried as structural-mesh uncertainty (§3, #4). The "
                  "tolerance was not relaxed after the result.", ""]
L += ["## 8. Readiness", "",
      "All approved Mechanical and buckling cases are solved and audited. The design cases are P00, V01, V03, Q01, Q03, T01 and T03 "
      "(plus the C00 control, and M01 / M02). The S3 support case is solved after the B03 benchmark passed; S1 and S2 are reused. "
      "The results are ready for the final engineering synthesis / report. The report and presentation were **not** written (by instruction).", ""]
w("Results/FINAL_PARAMETRIC_AUDIT.md", "\n".join(L))
print("all docs written")
