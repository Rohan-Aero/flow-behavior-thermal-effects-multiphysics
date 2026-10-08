# -*- coding: utf-8 -*-
"""SECTION 7B - builds the result tables (CSV + Markdown fragments) from out/post_7B_results.json and hand_checks_7B.json.
RE-ANALYSIS 2026. No number is typed in by hand here."""
import json, csv, os
OUT = os.environ.get("S7B_OUT", "<OUTPUT_ROOT>/S7B/Post/out")
R = json.load(open(os.path.join(OUT, "post_7B_results.json")))
H = json.load(open(os.path.join(OUT, "hand_checks_7B.json")))
X, U = R["extremes"], R["utilisation"]


def loc(a, surf):
    return "r %.0f mm, z %.2f mm, theta %.0f deg (%s; node %d)" % (a["r_mm"], a["z_mm"], a["theta_deg"], surf, a["node"])


rows = []
for case, lab in (("LC1", "LC1 free expansion (thermal only)"), ("LC2", "LC2 axially restrained (thermal only)")):
    u = U[case]["at_max_vm"]
    rows.append([lab, "max von Mises stress", "%.2f MPa" % (u["vm_Pa"] / 1e6), loc(u["loc"], u["surface"]),
                 "%.2f K (%.1f C)" % (u["loc"]["T_K"], u["loc"]["T_C"]),
                 "S_y(T) = %.1f MPa (VDM 4127, linear); utilisation %.4f; margin %.3f" % (u["Sy_T_Pa"] / 1e6, u["utilisation"], u["margin_Sy_over_vm_minus_1"])])
    t = X[case]["total_deformation_m"]
    rows.append([lab, "max total deformation", "%.4f mm" % (t["max"] * 1e3), loc(t["max_at"], t["max_surface"]),
                 "%.2f K (%.1f C)" % (t["max_at"]["T_K"], t["max_at"]["T_C"]), "n/a (deformation)"])
u = U["LC2P"]["at_max_vm"]
rows.append(["LC2P restrained, thermal + 443.41 Pa", "max von Mises stress", "%.6f MPa" % (u["vm_Pa"] / 1e6), loc(u["loc"], u["surface"]),
             "%.2f K (%.1f C)" % (u["loc"]["T_K"], u["loc"]["T_C"]),
             "S_y(T) = %.1f MPa; utilisation %.4f; margin %.3f" % (u["Sy_T_Pa"] / 1e6, u["utilisation"], u["margin_Sy_over_vm_minus_1"])])
for case in ("LC1", "LC2"):
    u = U[case]["max_utilisation_interior_15-585mm"]
    rows.append([case + " (supplementary: outside the 15 mm end zones)", "max utilisation", "%.2f MPa" % (u["vm_Pa"] / 1e6), loc(u["loc"], u["surface"]),
                 "%.2f K (%.1f C)" % (u["loc"]["T_K"], u["loc"]["T_C"]),
                 "S_y(T) = %.1f MPa; utilisation %.4f; margin %.3f" % (u["Sy_T_Pa"] / 1e6, u["utilisation"], u["margin"])])
hdr = ["Case", "Quantity", "Value", "Location", "Temperature", "Yield basis"]
with open(os.path.join(OUT, "critical_locations_7B.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(hdr)
    w.writerows(rows)
md = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)] + ["| " + " | ".join(r) + " |" for r in rows]
open(os.path.join(OUT, "critical_locations_7B.md"), "w").write("\n".join(md) + "\n")

# summary table
S = []
def add(q, lc1, lc2, lc2p, note=""):
    S.append([q, lc1, lc2, lc2p, note])
f6 = lambda v: "%.6g" % v
add("max total deformation [mm]", "%.4f" % (X["LC1"]["total_deformation_m"]["max"] * 1e3), "%.4f" % (X["LC2"]["total_deformation_m"]["max"] * 1e3), "%.4f" % (X["LC2P"]["total_deformation_m"]["max"] * 1e3))
add("axial deformation u_z max / min [mm]", "%.4f / %.2e" % (X["LC1"]["axial_deformation_uz_m"]["max"] * 1e3, X["LC1"]["axial_deformation_uz_m"]["min"] * 1e3),
    "%.1f / %.4f" % (X["LC2"]["axial_deformation_uz_m"]["max"] * 1e3, X["LC2"]["axial_deformation_uz_m"]["min"] * 1e3),
    "%.1f / %.4f" % (X["LC2P"]["axial_deformation_uz_m"]["max"] * 1e3, X["LC2P"]["axial_deformation_uz_m"]["min"] * 1e3))
add("radial deformation u_r max [mm]", "%.4f" % (X["LC1"]["radial_deformation_ur_m"]["max"] * 1e3), "%.4f" % (X["LC2"]["radial_deformation_ur_m"]["max"] * 1e3), "%.4f" % (X["LC2P"]["radial_deformation_ur_m"]["max"] * 1e3))
add("max von Mises [MPa]", "%.3f" % (X["LC1"]["von_mises_Pa"]["max"] / 1e6), "%.6f" % (X["LC2"]["von_mises_Pa"]["max"] / 1e6), "%.6f" % (X["LC2P"]["von_mises_Pa"]["max"] / 1e6))
add("max principal s1 [MPa]", "%.3f" % (X["LC1"]["max_principal_Pa"]["max"] / 1e6), "%.3f" % (X["LC2"]["max_principal_Pa"]["max"] / 1e6), "%.3f" % (X["LC2P"]["max_principal_Pa"]["max"] / 1e6))
add("min principal s3 [MPa]", "%.3f" % (X["LC1"]["min_principal_Pa"]["min"] / 1e6), "%.3f" % (X["LC2"]["min_principal_Pa"]["min"] / 1e6), "%.3f" % (X["LC2P"]["min_principal_Pa"]["min"] / 1e6))
add("max equivalent elastic strain [-]", "%.4e" % X["LC1"]["equiv_elastic_strain"]["max"], "%.5e" % X["LC2"]["equiv_elastic_strain"]["max"], "%.5e" % X["LC2P"]["equiv_elastic_strain"]["max"])
for c in ("LC1", "LC2", "LC2P"):
    pass
RE = R["reactions"]
add("magnitude of the reaction force sum [N]", "%.2e" % (sum(v * v for v in RE["LC1"]["sum_F_N"]) ** 0.5), "%.2e" % (sum(v * v for v in RE["LC2"]["sum_F_N"]) ** 0.5), "%.2e" % (sum(v * v for v in RE["LC2P"]["sum_F_N"]) ** 0.5))
add("magnitude of the reaction moment sum about (0,0,0) [N m]", "%.2e" % (sum(v * v for v in RE["LC1"]["sum_M_about_origin_Nm"]) ** 0.5), "%.2e" % (sum(v * v for v in RE["LC2"]["sum_M_about_origin_Nm"]) ** 0.5), "%.2e" % (sum(v * v for v in RE["LC2P"]["sum_M_about_origin_Nm"]) ** 0.5))
add("inlet / outlet end-face axial reaction [N]", "- (3-node support: max nodal %.1e N)" % RE["LC1"]["max_abs_nodal_reaction_N"],
    "%+.1f / %+.1f" % (RE["LC2"]["groups"]["inlet_end_face_z0"]["Fz"], RE["LC2"]["groups"]["outlet_end_face_zL"]["Fz"]),
    "%+.1f / %+.1f" % (RE["LC2P"]["groups"]["inlet_end_face_z0"]["Fz"], RE["LC2P"]["groups"]["outlet_end_face_zL"]["Fz"]))
add("utilisation at max von Mises (S_y(T))", "%.4f" % U["LC1"]["at_max_vm"]["utilisation"], "%.4f" % U["LC2"]["at_max_vm"]["utilisation"], "%.4f" % U["LC2P"]["at_max_vm"]["utilisation"])
hdr2 = ["Quantity", "LC1 (thermal only)", "LC2 (thermal only)", "LC2P (thermal + pressure)", ""]
with open(os.path.join(OUT, "results_summary_7B.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(hdr2[:4])
    w.writerows([r[:4] for r in S])
md = ["| " + " | ".join(hdr2[:4]) + " |", "|---|---|---|---|"] + ["| " + " | ".join(r[:4]) + " |" for r in S]
open(os.path.join(OUT, "results_summary_7B.md"), "w").write("\n".join(md) + "\n")
print(open(os.path.join(OUT, "critical_locations_7B.md")).read())
print(open(os.path.join(OUT, "results_summary_7B.md")).read())
