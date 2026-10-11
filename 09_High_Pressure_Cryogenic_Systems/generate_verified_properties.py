#!/usr/bin/env python3
"""Generate verified_properties.csv: nitrogen properties from the CoolProp library.

CONCEPTUAL, EDUCATIONAL. Needs the open-source CoolProp library (MIT licence), which implements the
published reference equation of state for nitrogen of Span, Lemmon, Jacobsen, Wagner and Yokozeki,
J. Phys. Chem. Ref. Data 29, 1361-1433 (2000), and the transport correlations of Lemmon and Jacobsen,
Int. J. Thermophys. 25, 21-69 (2004). The generated file was developed with CoolProp 8.0.0.

    pip install CoolProp==8.0.0
    python generate_verified_properties.py            # rewrite verified_properties.csv
    python generate_verified_properties.py --check    # regenerate in memory and compare (relative tolerance 1e-6)

Why CoolProp and not the NIST Chemistry WebBook tables: NIST states that its Standard Reference Data may not be
reproduced without permission, so the WebBook tables are NOT stored in this repository. They were used at authoring
(and by `validate_design.py --online`) only as a comparison for individual values. The output here is computed
from the published equation of state, not copied from any table.

Each dataset_id below is one query. Values are written to 7 significant digits. Nothing is derived or fitted here.
Gauge pressure is absolute pressure minus 0.101325 MPa.
"""
import argparse
import csv
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "verified_properties.csv"
FLUID = "Nitrogen"
P_ATM = 101325.0           # Pa
COLUMNS = ["dataset_id", "row_kind", "T_K", "p_MPa_abs", "rho_kg_m3", "h_kJ_kg", "cp_kJ_kgK", "cv_kJ_kgK",
           "jt_K_per_MPa", "mu_uPa_s", "k_W_mK", "quality", "phase"]

# dataset_id -> (kind, parameters, description)
DATASETS = {
    "N2_GAS_300K_ISOTHERM": ("isotherm", {"T": 300.0, "p0": P_ATM, "n": 31, "dp": 1e6}, "Gaseous N2 at 300 K, 0 to 30 MPa gauge in 1 MPa steps"),
    "N2_GAS_ISOBAR_0MPAG": ("isobar", {"p": P_ATM, "T0": 80.0, "T1": 320.0, "dT": 1.0}, "N2 at 0.101325 MPa abs, 80 to 320 K in 1 K steps"),
    "N2_GAS_ISOBAR_1MPAG": ("isobar", {"p": P_ATM + 1e6, "T0": 200.0, "T1": 320.0, "dT": 2.0}, "Gaseous N2 at 1 MPa gauge, 200 to 320 K in 2 K steps"),
    "N2_GAS_ISOBAR_2MPAG": ("isobar", {"p": P_ATM + 2e6, "T0": 200.0, "T1": 320.0, "dT": 2.0}, "Gaseous N2 at 2 MPa gauge, 200 to 320 K in 2 K steps"),
    "N2_GAS_ISOBAR_5MPAG": ("isobar", {"p": P_ATM + 5e6, "T0": 200.0, "T1": 320.0, "dT": 2.0}, "Gaseous N2 at 5 MPa gauge, 200 to 320 K in 2 K steps"),
    "N2_GAS_ISOBAR_10MPAG": ("isobar", {"p": P_ATM + 10e6, "T0": 200.0, "T1": 320.0, "dT": 2.0}, "Gaseous N2 at 10 MPa gauge, 200 to 320 K in 2 K steps"),
    "N2_SAT_0MPAG": ("sat", {"p": P_ATM}, "Saturated N2 at 0 MPa gauge (70 K liquid, boiling liquid and vapour, 110 K vapour)"),
    "N2_SAT_0P2MPAG": ("sat", {"p": P_ATM + 0.2e6}, "Saturated N2 at 0.2 MPa gauge"),
    "N2_SAT_0P5MPAG": ("sat", {"p": P_ATM + 0.5e6}, "Saturated N2 at 0.5 MPa gauge"),
    "N2_SAT_1MPAG": ("sat", {"p": P_ATM + 1e6}, "Saturated N2 at 1 MPa gauge"),
    "N2_ISOCHORE_806": ("isochore", {"D": 806.0844, "T0": 77.355, "T1": 100.0, "dT": 2.5}, "Closed volume at 806.0844 kg/m3 (saturated liquid at 1 atm), 77.355 to 100 K"),
    "N2_ISOCHORE_760": ("isochore", {"D": 760.0, "T0": 77.355, "T1": 110.0, "dT": 2.5}, "Closed volume at 760 kg/m3, 77.355 to 110 K"),
    "N2_ISOCHORE_700": ("isochore", {"D": 700.0, "T0": 77.355, "T1": 120.0, "dT": 2.5}, "Closed volume at 700 kg/m3, 77.355 to 120 K"),
}


def _cp():
    try:
        import CoolProp.CoolProp as CP
    except ImportError:
        sys.exit("CoolProp is required: pip install CoolProp==8.0.0")
    return CP


def g7(x):
    return "" if x is None else f"{x:.7g}"


def state(CP, T, p, kind="state", quality="", phase=None):
    """One row from temperature (K) and pressure (Pa) in a single-phase state."""
    pc = CP.PropsSI("pcrit", FLUID)
    if phase is None:
        if p >= pc:
            phase = "supercritical"
        else:
            phase = "liquid" if T < CP.PropsSI("T", "P", p, "Q", 0, FLUID) else "vapor"
    P_ = lambda key: CP.PropsSI(key, "T", T, "P", p, FLUID)
    return {"row_kind": kind, "T_K": g7(T), "p_MPa_abs": g7(p / 1e6), "rho_kg_m3": g7(P_("D")), "h_kJ_kg": g7(P_("Hmass") / 1e3),
            "cp_kJ_kgK": g7(P_("Cpmass") / 1e3), "cv_kJ_kgK": g7(P_("Cvmass") / 1e3),
            "jt_K_per_MPa": g7(CP.PropsSI("d(T)/d(P)|H", "T", T, "P", p, FLUID) * 1e6), "mu_uPa_s": g7(P_("V") * 1e6),
            "k_W_mK": g7(P_("L")), "quality": quality, "phase": phase}


def sat_state(CP, p, q, T):
    P_ = lambda key: CP.PropsSI(key, "P", p, "Q", q, FLUID)
    return {"row_kind": "state", "T_K": g7(T), "p_MPa_abs": g7(p / 1e6), "rho_kg_m3": g7(P_("D")), "h_kJ_kg": g7(P_("Hmass") / 1e3),
            "cp_kJ_kgK": g7(P_("Cpmass") / 1e3), "cv_kJ_kgK": g7(P_("Cvmass") / 1e3),
            "jt_K_per_MPa": g7(CP.PropsSI("d(T)/d(P)|H", "P", p, "Q", q, FLUID) * 1e6), "mu_uPa_s": g7(P_("V") * 1e6),
            "k_W_mK": g7(P_("L")), "quality": "", "phase": "liquid" if q == 0 else "vapor"}


def build():
    CP = _cp()
    rows = []
    for did, (kind, a, _desc) in DATASETS.items():
        if kind == "isotherm":
            for i in range(a["n"]):
                rows.append(dict(state(CP, a["T"], a["p0"] + i * a["dp"]), dataset_id=did))
        elif kind == "isobar":
            n = int(round((a["T1"] - a["T0"]) / a["dT"]))
            for i in range(n + 1):
                rows.append(dict(state(CP, round(a["T0"] + i * a["dT"], 6), a["p"]), dataset_id=did))
        elif kind == "sat":
            p = a["p"]
            Ts = CP.PropsSI("T", "P", p, "Q", 0, FLUID)
            rows.append(dict(state(CP, 70.0, p), dataset_id=did))
            rows.append(dict(sat_state(CP, p, 0, Ts), dataset_id=did))
            rows.append(dict(sat_state(CP, p, 1, Ts), dataset_id=did))
            rows.append(dict(state(CP, 110.0, p), dataset_id=did))
        elif kind == "isochore":
            n = int(round((a["T1"] - a["T0"]) / a["dT"]))
            for i in range(n + 1):
                T = round(a["T0"] + i * a["dT"], 6)
                p = CP.PropsSI("P", "T", T, "D", a["D"], FLUID)
                try:
                    q = CP.PropsSI("Q", "T", T, "D", a["D"], FLUID)
                except ValueError:
                    q = -1.0
                two = 0.0 <= q <= 1.0
                rows.append({"dataset_id": did, "row_kind": "isochore", "T_K": g7(T), "p_MPa_abs": g7(p / 1e6), "rho_kg_m3": g7(a["D"]),
                             "h_kJ_kg": "", "cp_kJ_kgK": "", "cv_kJ_kgK": "", "jt_K_per_MPa": "", "mu_uPa_s": "", "k_W_mK": "",
                             "quality": g7(q) if two else "", "phase": "two_phase" if two else "single_phase"})
    return rows


def to_csv_text(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def compare(text_a, text_b, rel=1e-6):
    """True if two CSV texts have the same rows and numeric values within a relative tolerance."""
    ra, rb = list(csv.DictReader(io.StringIO(text_a))), list(csv.DictReader(io.StringIO(text_b)))
    if len(ra) != len(rb):
        return False
    for x, y in zip(ra, rb):
        for k in COLUMNS:
            if x[k] == y[k]:
                continue
            try:
                a, b = float(x[k]), float(y[k])
            except ValueError:
                return False
            if abs(a - b) > rel * max(abs(a), abs(b), 1e-12):
                return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="regenerate in memory and compare with the committed file")
    args = ap.parse_args()
    text = to_csv_text(build())
    if args.check:
        same = compare(OUT.read_text(encoding="utf-8"), text)
        print("verified_properties.csv matches a fresh generation" if same else "DIFFERENCE between the committed file and a fresh generation")
        return 0 if same else 1
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.name}: {text.count(chr(10)) - 1} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
