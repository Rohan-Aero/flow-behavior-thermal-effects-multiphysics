# -*- coding: utf-8 -*-
"""SECTION 8B - markdown tables for the mesh-study documents (RE-ANALYSIS 2026).
Every number is read from the JSON written by post_8B.py, mapping_check_8B.py, mesh_geometry_8B.py and ref1d_lc1_8B.py
(no hand transcription). Output: out/tables_8B.md
Usage: python tables_8B.py [out_dir]"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
R = json.load(open(os.path.join(OUT, "post_8B_results.json")))
MAP = json.load(open(os.path.join(OUT, "mapping_check_all.json")))
GEO = json.load(open(os.path.join(OUT, "mesh_geometry.json")))
REF = json.load(open(os.path.join(OUT, "ref1d_lc1_8B.json")))
M = R["meshes"]
ORDER = [t for t in ("XC", "C", "B", "B_official", "FR", "FA", "FC", "IL") if t in M]
NAME = {"XC": "XC extra-coarse", "C": "C coarse", "B": "B baseline (re-meshed)", "B_official": "B official (7B/8A)",
        "FR": "FR fine, through-wall", "FA": "FA fine, axial", "FC": "FC fine, circumferential", "IL": "IL inlet bias 8"}
L = []


def T(head, rows):
    L.append("| " + " | ".join(head) + " |")
    L.append("|" + "|".join("---" for _ in head) + "|")
    for r in rows:
        L.append("| " + " | ".join(str(x) for x in r) + " |")
    L.append("")


def rel(t, v, b):
    return "—" if t == "B" or v is None or b is None else "%+.2e" % ((v - b) / b)


def f(v, fmt):
    return "—" if v is None else fmt % v


# ---- 1. mesh definition and quality
L.append("### T1. Mesh definition and quality\n")
rows = []
for t in ORDER:
    d = M[t]["divisions"]; g = GEO.get(t, {}); mm = (M[t].get("mechanical") or {}).get("mesh_metrics") or {}
    rows.append([NAME[t], "%d × %d × %d (bias %g)" % (d["circumferential"], d["through_wall"], d["axial"], d["axial_bias"]),
                 format(M[t]["LC2"]["nodes"], ","), format(d["circumferential"] * d["through_wall"] * d["axial"], ","),
                 "%.1f %%" % (100 * M[t]["LC2"]["nodes"] / 128000),
                 f(g.get("radial_size_mm"), "%.3f"), "%.2f / %.2f" % (g["circumferential_size_mm"]["bore_r10"], g["circumferential_size_mm"]["outer_r20"]) if g else "—",
                 "%.2f / %.2f" % (g["axial_element_length_mm"]["min"], g["axial_element_length_mm"]["max"]) if g else "—",
                 f(mm.get("AspectRatio", {}).get("max"), "%.2f"), f(g.get("geometric_aspect_ratio_max"), "%.2f"),
                 f(mm.get("JacobianRatio", {}).get("max"), "%.3f"), f(mm.get("ElementQuality", {}).get("min"), "%.3f"),
                 "%d" % g["elements_with_nonpositive_corner_jacobian"] if g else "—",
                 "%d / %d" % (g["boundary_faces"], g["boundary_faces_expected"]) if g else "—",
                 "PASS" if g.get("PASS") else "—"])
T(["Mesh", "circ × wall × axial", "Nodes", "Elements (SOLID186)", "of 128 k licence", "radial size [mm]", "circ. size bore / outer [mm]",
   "axial size min / max [mm]", "Mechanical aspect ratio max", "edge ratio max", "Jacobian ratio max", "element quality min",
   "inverted (corner Jacobian ≤ 0)", "boundary faces found / expected", "independent mesh check"], rows)

# ---- 2. temperature mapping
L.append("### T2. Temperature mapping on each mesh (same source: baseline_medium_final node field)\n")
rows = []
for t in ORDER:
    m = MAP.get(t)
    if not m:
        continue
    rows.append([NAME[t], format(m["mapped"], ","), m["unmapped"], "%.3f – %.3f" % (m["T_min_K"], m["T_max_K"]),
                 "%.3f" % m["extrapolation_above_source_max_K"], "%.3f / %.3f" % (m["A_vs_source_node_field"]["max_inside"], m["A_vs_source_node_field"]["max_outside"]),
                 "%.4f" % m["A_vs_source_node_field"]["mean"], "%.2f" % m["B_vs_FV_solution"]["max"],
                 "%.2f" % m["by_axial_band"]["14-586 mm"]["B_max"], format(m["nodes_outside_source_mesh"], ",")])
T(["Mesh", "mapped nodes", "unmapped", "T min – max [K]", "above source max [K]", "(A) max error inside / outside source mesh [K]",
   "(A) mean [K]", "(B) max vs FV solution [K]", "(B) max, z 14–586 mm [K]", "nodes in the chord gap (clamped)"], rows)

# ---- 3. LC1
L.append("### T3. LC1 (free expansion, thermal only)\n")
rows = []
b1 = M["B"]["LC1"]
for t in ORDER:
    e = M[t]["LC1"]; mech = (M[t].get("mechanical") or {}).get("results", {}).get("LC1", {})
    un = mech.get("LC1_Equivalent_Stress_UNaveraged", {}).get("Maximum")
    rows.append([NAME[t], "%.6f" % (e["max_utot_m"] * 1e3), "%.6f" % (e["dL_face_mean_m"] * 1e3),
                 "%.3f" % (e["max_vm_Pa"] / 1e6), "bore, z %.2f mm, %.2f K" % (e["max_vm_loc"]["z_mm"], e["max_vm_loc"]["T_K"]),
                 f(un and un / 1e6, "%.3f"), "%.3f" % (e["midspan"]["bore_st_Pa"] / 1e6), "%.3f" % (e["midspan"]["bore_vm_Pa"] / 1e6),
                 "%.3f @ %.2f mm" % (e["inlet"]["bore_peak_MPa"], e["inlet"]["bore_peak_z_mm"]),
                 "%.1e" % e["reactions"]["sumF_mag_N"], f(e.get("structural_error", {}).get("energy_norm_error_pct"), "%.3f")])
T(["Mesh", "max total def. [mm]", "free growth ΔL [mm]", "max von Mises [MPa]", "location", "unaveraged max [MPa]",
   "mid-span bore σθ [MPa]", "mid-span bore VM [MPa]", "inlet bore peak θ-mean [MPa]", "\\|ΣF\\| reactions [N]", "energy-norm error [%]"], rows)
L.append("1-D generalised-plane-strain reference at z = 300 mm (same source field, `ref1d_lc1_8B.py`): bore σθ **%.3f MPa**, bore VM %.3f MPa, outer σθ %.3f MPa; ΔT_wall %.3f K.\n"
         % (REF["bore"]["s_t_MPa"], REF["bore"]["vm_MPa"], REF["outer"]["s_t_MPa"], REF["dT_wall_K"]))

# ---- 4. LC2
L.append("### T4. LC2 (axially restrained, thermal only)\n")
rows = []
for t in ORDER:
    e = M[t]["LC2"]; mech = (M[t].get("mechanical") or {}).get("results", {}).get("LC2", {})
    un = mech.get("LC2_Equivalent_Stress_UNaveraged", {}).get("Maximum")
    loc = e["max_vm_loc"]
    rows.append([NAME[t], "%.7f" % (e["max_utot_m"] * 1e3), "%.7f" % (e["min_uz_m"] * 1e3), "%.7f" % (e["max_ur_m"] * 1e3),
                 "%.4f" % (e["max_vm_Pa"] / 1e6), "r %.0f, z %.1f mm, %.2f K" % (loc["r_mm"], loc["z_mm"], loc["T_K"]),
                 f(un and un / 1e6, "%.4f"), "%.4f" % (e["inlet"]["outer_at_face_MPa"]), "%.4f" % (e["mean_axial_stress_Pa"] / 1e6),
                 "%.3f" % (e["max_vm_interior_Pa"] / 1e6), "%.2f" % e["reactions"]["inlet_Fz_N"],
                 f(M[t].get("pressure_effect_max_vm_Pa"), "%+.0f"), f(e.get("structural_error", {}).get("energy_norm_error_pct"), "%.4f")])
T(["Mesh", "max total def. [mm]", "min u_z [mm]", "max u_r [mm]", "max von Mises [MPa]", "location", "unaveraged max [MPa]",
   "outer edge of inlet face, θ-mean [MPa]", "mean axial N/A [MPa]", "max VM 15–585 mm [MPa]", "end reaction [N]",
   "pressure effect on max VM [Pa]", "energy-norm error [%]"], rows)

# ---- 5. buckling
L.append("### T5. LC2 linear buckling\n")
rows = []
for t in ORDER:
    bk = M[t].get("buckling")
    if not bk:
        continue
    m1 = bk["modes"]["1"]
    corr = m1["correlation_with_reference_shapes"]["guided_n1 cos(pi z/L)"]
    ends = m1["lateral_at_ends_and_mid"]
    rows.append([NAME[t], "%.7f" % bk["lambda1"], "%.7f" % bk["lambda2"], "%.1e" % bk["pair_split_rel"], "%.5f" % bk["lambda3"],
                 "%.5f" % bk["lambda5"], "%.3f" % (bk["critical_load_N"] / 1e3), "%.6f" % m1["beam_type_share_of_inplane_motion"],
                 "%.1e" % m1["max_ovalisation_over_max_lateral"], "%.0f" % m1["z_of_max_lateral_mm"],
                 "%.3f / %.1e / %.3f" % (ends[0], ends[1], ends[2]), "%.6f" % abs(corr), "%.1f" % bk["pair_angle_deg"]])
T(["Mesh", "λ₁", "λ₂", "(λ₂−λ₁)/λ₁", "λ₃ (= λ₄)", "λ₅ (= λ₆)", "P_cr = λ₁·N [kN]", "beam-type share of mode 1",
   "ovalisation / lateral", "z of max lateral [mm]", "lateral at inlet / mid / outlet (norm.)", "\\|corr.\\| with cos(πz/L)",
   "mode 1 ⟂ mode 2 [°]"], rows)

# ---- 6. changes
L.append("### T6. Changes relative to the baseline B (relative)\n")
rows = []
for name, v in R["directional_fine"].items():
    vals = v["values"]
    b = vals.get("B")
    rows.append([name] + [rel(t, vals.get(t), b) for t in ("XC", "C", "FR", "FA", "FC", "IL", "B_official")])
T(["Quantity", "XC vs B", "C vs B", "FR vs B", "FA vs B", "FC vs B", "IL vs B", "B official vs B"], rows)

# ---- 7. family assessment
L.append("### T7. Systematic family XC → C → B (r = %.4f): Richardson / GCI (Celik et al. 2008, Fs 1.25)\n" % list(R["family_assessment"].values())[0]["r"])
rows = []
for name, v in R["family_assessment"].items():
    rows.append([name, "%+.2e" % v["change_XC_to_C_rel"], "%+.2e" % v["change_C_to_B_rel"], v["behaviour"],
                 f(v.get("p"), "%.2f"), f(v.get("extrapolated"), "%.7g"), f(v.get("GCI_fine"), "%.2e"),
                 f(v.get("baseline_error_vs_extrapolated_rel"), "%+.2e")])
T(["Quantity", "XC → C", "C → B", "behaviour", "apparent order p", "extrapolated (h → 0)", "GCI_fine (rel.)", "B vs extrapolated"], rows)

open(os.path.join(OUT, "tables_8B.md"), "w").write("\n".join(L))
print("\n".join(L))
