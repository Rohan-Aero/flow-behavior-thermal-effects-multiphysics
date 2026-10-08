# -*- coding: utf-8 -*-
"""Section 10C-1 - slide data for the final presentation (RE-ANALYSIS 2026).
Every number used by a chart or table in the deck is read here from the audited master dataset
(11_Final_Audit/MASTER_PROJECT_DATA.csv, by row ID) or, for the CFD axial profiles of slide 8, from the project file
06_Fluent_CFD/Profiles/axial_profiles_cfd.csv (SHA-256 checked against the Section 10A manifest).
No value is computed from a new simulation; percentage changes are arithmetic on master values.
Usage: python build_slide_data.py <MASTER_PROJECT_DATA.csv> <axial_profiles_cfd.csv> <Tables dir>"""
import csv, json, os, sys, hashlib

MCSV, PROF, OUT = sys.argv[1:4]
PROF_SHA_MANIFEST = "FB851BA933508EA65687BC914F978DAD516963FF58E681BE3DEC342251E9A7FC"

rows = {}
with open(MCSV, encoding="utf-8") as fh:
    for r in csv.DictReader(l for l in fh if not l.startswith("#")):
        rows[r["ID"]] = r


def V(i):
    return float(rows[i]["Value"])


def pct(a, b):
    return 100.0 * (a / b - 1.0)


vals = {}      # name -> {value, id, units}


def put(name, mid, units=""):
    vals[name] = {"value": V(mid), "id": mid, "units": units, "parameter": rows[mid]["Parameter"],
                  "level": rows[mid]["Modelling level"], "status": rows[mid]["Status"]}


# baseline geometry and operating point
for n, m, u in [("Di", "M023", "mm"), ("Do", "M024", "mm"), ("t", "M025", "mm"), ("L", "M026", "mm"), ("Tin", "M002", "K"),
                ("Vin", "M003", "m/s"), ("Tref", "M014", "K"), ("rho_s", "M008", "kg/m3"),
                # CFD medium baseline
                ("cells_medium", "M033", "-"), ("Re_in_cfd", "M034", "-"), ("dp", "M036", "Pa"), ("Tout", "M037", "K"),
                ("Q", "M038", "W"), ("Tmax", "M039", "K"), ("dTwall_mid", "M041", "K"), ("Nu_fd", "M042", "-"), ("f_fd", "M043", "-"),
                ("yplus_max", "M046", "-"), ("mass_imb", "M047", "%"), ("energy_imb", "M048", "%"),
                # mesh family
                ("cells_fine", "M050", "-"), ("dp_fine", "M051", "Pa"), ("Tmax_fine", "M054", "K"), ("cells_coarse", "M058", "-"),
                ("dp_coarse", "M059", "Pa"), ("Tmax_coarse", "M062", "K"), ("Tmax_extrap", "M066", "K"),
                # analytical (Section 2)
                ("Q_an", "M071", "W"), ("Tout_an", "M072", "K"), ("dp_an", "M073", "Pa"), ("Tmax_an", "M074", "K"),
                ("sig_restrained_an", "M078", "MPa"),
                # structural
                ("nodes_B", "M081", "-"), ("elems_B", "M082", "-"), ("LC1_def", "M084", "mm"), ("LC1_vm", "M086", "MPa"),
                ("LC2_def", "M089", "mm"), ("LC2_vm", "M090", "MPa"), ("LC2_N", "M091", "N"), ("LC2_sigz", "M092", "MPa"),
                ("util", "M095", "-"), ("fy", "M096", "-"),
                # buckling / supports
                ("lam_S1", "M098", "-"), ("Pcr_S1", "M099", "kN"), ("lam_S2", "M101", "-"), ("Pcr_S2", "M102", "kN"),
                ("lam_S3", "M104", "-"), ("Pcr_S3", "M105", "kN"), ("vm_S2", "M108", "MPa"), ("vm_S3", "M109", "MPa")]:
    put(n, m, u)

# analytical inlet Reynolds number is a Section 2 result that is not a master row: taken from the Section 2 result file
vals["Re_in_an"] = {"value": 29956.55473, "id": "02_Engineering_Calculations/baseline_results.csv (Re_in)", "units": "-",
                    "parameter": "Reynolds number, inlet", "level": "ANALYTICAL (Section 2)", "status": "REPORTED (section result file)"}

# ---- analytical vs CFD table (slide 9)
av = [
    ("Inlet Reynolds number", "-", vals["Re_in_an"]["value"], V("M034"), "{:,.0f}", "same mass flux and inlet properties"),
    ("Pressure drop", "Pa", V("M073"), V("M036"), "{:.2f}", "friction lower (gas heating), flow-development term higher"),
    ("Outlet bulk temperature", "K", V("M072"), V("M037"), "{:.2f}", "48-facet CFD section (faceting)"),
    ("Heat-transfer rate", "W", V("M071"), V("M038"), "{:.3f}", "exactly the 48-gon lateral-area ratio"),
    ("Maximum solid temperature", "K", V("M074"), V("M039"), "{:.2f}", "higher CFD film coefficient in developing flow; axial conduction"),
]
with open(os.path.join(OUT, "slide09_analytical_vs_cfd.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["quantity", "units", "analytical_section2", "cfd_medium", "difference", "reason", "source"])
    for q, u, a, c, f, why in av:
        d = "%+.2f K" % (c - a) if u == "K" else "%+.3f %%" % pct(c, a) if q.startswith("Heat") else "%+.2f %%" % pct(c, a)
        w.writerow([q, u, f.format(a), f.format(c), d, why, "M071-M074, M034-M039; Re_an from baseline_results.csv"])

# ---- support scenarios (slide 13), listed with increasing end restraint (not a ranking)
sup = [("S1", "guided (ends sway, rotation held)", 1.0, V("M098"), V("M099"), V("M090")),
       ("S3", "clamped - pinned", 0.699, V("M104"), V("M105"), V("M109")),
       ("S2", "clamped - clamped", 0.5, V("M101"), V("M102"), V("M108"))]
with open(os.path.join(OUT, "slide13_support_scenarios.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["scenario", "end condition", "K", "lambda1", "P_cr_kN", "LC2_static_max_vm_MPa", "source"])
    for s in sup:
        w.writerow(list(s) + ["M090, M098-M109"])

# ---- parametric results (slides 14-15)
P = {"P00": dict(dp=V("M036"), tout=V("M037"), tmax=V("M039"), lc1def=V("M084"), lc2vm=V("M090"), lam=V("M098"), pcr=V("M099"))}
base = {"V01": 125, "V03": 134, "Q01": 143, "Q03": 152, "T01": 161, "T03": 170}
for c, b in base.items():
    m = lambda k: "M%03d" % (b + k)
    P[c] = dict(dp=V(m(0)), tout=V(m(1)), tmax=V(m(2)), lc1def=V(m(3)), lc2vm=V(m(5)), lam=V(m(7)), pcr=V(m(8)))
x = {"V": [21.15, 23.5, 25.85], "Q": [7200, 8000, 8800], "T": [8, 10, 12]}
series = {"V": ["V01", "P00", "V03"], "Q": ["Q01", "P00", "Q03"], "T": ["T01", "P00", "T03"]}
with open(os.path.join(OUT, "slide15_parametric_results.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["case", "variable_value", "dp_Pa", "Tout_K", "Tmax_K", "LC1_maxdef_mm", "LC2_maxvm_MPa", "lambda1_S1", "Pcr_kN"])
    for k in "VQT":
        for xv, c in zip(x[k], series[k]):
            p = P[c]
            w.writerow([c, xv, p["dp"], p["tout"], p["tmax"], p["lc1def"], p["lc2vm"], p["lam"], p["pcr"]])

charts = {}
for key, var, resp in [("V_dp", "V", "dp"), ("V_tout", "V", "tout"), ("V_lam", "V", "lam"),
                       ("Q_tmax", "Q", "tmax"), ("Q_vm", "Q", "lc2vm"), ("Q_lam", "Q", "lam"),
                       ("T_def", "T", "lc1def"), ("T_pcr", "T", "pcr"), ("T_lam", "T", "lam")]:
    charts[key] = {"x": x[var], "y": [P[c][resp] for c in series[var]], "cases": series[var]}

# ---- CFD axial profiles (slide 8)
sha = hashlib.sha256(open(PROF, "rb").read()).hexdigest().upper()
assert sha == PROF_SHA_MANIFEST, "axial_profiles_cfd.csv does not match the 10A manifest"
with open(PROF, encoding="utf-8") as fh:
    pr = list(csv.DictReader(l for l in fh if not l.startswith('"#') and not l.startswith("#")))
prof = {k: [round(float(r[k]) * (1000 if k == "z" else 1), 4) for r in pr] for k in ("z", "w_b", "w_max", "p_area", "Tb_mass", "Twi", "Two")}
with open(os.path.join(OUT, "slide08_cfd_axial_profiles_medium.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["z_mm", "w_bulk_m_s", "w_centreline_max_m_s", "p_static_area_avg_Pa", "T_bulk_K", "T_wall_inner_K", "T_wall_outer_K"])
    for i in range(len(pr)):
        w.writerow([prof[k][i] for k in ("z", "w_b", "w_max", "p_area", "Tb_mass", "Twi", "Two")])

data = {"values": vals, "parametric": P, "charts": charts, "profiles": prof,
        "sources": {"master_csv_sha256": hashlib.sha256(open(MCSV, "rb").read()).hexdigest().upper(), "axial_profiles_sha256": sha}}
json.dump(data, open(os.path.join(OUT, "slide_data.json"), "w", encoding="utf-8"), indent=1)

# percentage changes quoted in the deck (arithmetic on master values)
chg = {c: {k: round(pct(P[c][k], P["P00"][k]), 2) for k in P[c]} for c in base}
json.dump(chg, open(os.path.join(OUT, "parametric_changes_pct.json"), "w"), indent=1)
print("slide data written:", len(vals), "values;", len(charts), "charts;", len(pr), "profile stations")
print(json.dumps(chg, indent=0)[:900])
