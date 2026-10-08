# -*- coding: utf-8 -*-
"""Section 9B-1 - writes CFD_Results/SCREENING_COMPARISON.md: solved CFD against the 9A anchored screening.

RE-ANALYSIS 2026. The numbers come from screening_comparison.json (written by post_9B1.py from the raw case
outputs and Analytical_Screening/screening_results.json). Nothing is fitted or adjusted: the screening values are
the ones frozen in 9A, and the CFD values are the solved results. The attribution text below was written after the
results were inspected. Each attribution names ONE category from the 9B-1 brief (nonlinear properties, Re, geometry,
developing flow, heat transfer, mesh, numerics) and the physical reason.
"""
import os, sys, json

ROOT = sys.argv[1] if len(sys.argv) > 1 else r"<PROJECT_ROOT>"
RES = os.path.join(ROOT, "10_Parametric_Study", "CFD_Results")
CASES = ["V01_LOW", "V03_HIGH", "Q01_LOW", "Q03_HIGH", "T01_THIN", "T03_THICK"]
# anchor values frozen in 9A (screening_results.json -> anchor_P00, rounded as stored there)
ANCH = {"Re inlet": 29956.55473478329, "Δp [Pa]": 438.13, "T_out [K]": 368.93, "T max interface [K]": 555.27,
        "T max fluid [K]": 553.41, "T max solid, cell [K]": 562.13, "T solid mean [K]": 525.48, "T solid min [K]": 423.97,
        "Q [W]": 602.76, "y+ max": 0.58484}
P00 = {"Re inlet": 29958.1745, "Δp [Pa]": 438.12633, "T_out [K]": 368.93236, "T max interface [K]": 555.26709,
       "T max fluid [K]": 553.4130789, "T max solid, cell [K]": 562.1271022, "T solid mean [K]": 525.4829346,
       "T solid min [K]": 423.9664736, "Q [W]": 602.75524, "y+ max": 0.58483571}

ATTR = {
    "Re inlet": ("numerics", "The change is identical (0, −10, +10 %). The absolute values differ by +0.005 % in every case. That "
                 "offset is Fluent's ideal-gas constant (287.0425 vs 287.058 J/kg K) in the density, already identified in 5B; "
                 "G = ρV does not depend on the 48-facet area"),
    "Δp [Pa]": {
        "V": ("developing flow", "CFD Δp is slightly less sensitive to V than the 1-D model (−13.3 / +14.1 % vs −14.0 / +14.8 %). "
              "The 1-D model applies a fully developed Petukhov friction factor over the whole length. In the CFD about 10 % of "
              "Δp is the entrance-region momentum-profile development (46 Pa in P00), whose Re dependence is weaker than that "
              "of fully developed friction"),
        "Q": ("nonlinear properties", "±0.09 %. The acceleration and friction terms depend on the bulk and wall air "
              "density and viscosity. The 1-D model evaluates them at mean temperatures, while the CFD uses the local "
              "piecewise-linear properties"),
        "T": ("numerics", "≤ 0.004 %. The fluid mesh and inlet state are identical, so a thickness change has no mechanism "
              "to alter Δp. The residue is the tiny wall-viscosity change from the redistributed wall temperature"),
    },
    "T_out [K]": ("numerics", "≤ 0.015 K in every case. It is the energy balance ṁ·c̄p·ΔT = Q, identical in both models. The residue is "
                  "the rounding of the stored P00 anchor (±0.005 K) and the c_p(T) integration"),
    "T max interface [K]": {
        "V": ("heat transfer", "≤ 0.11 K. The exit h from the CFD against the Gnielinski scaling with the property ratio; "
              "both see the same bulk temperature"),
        "Q": ("heat transfer", "≤ 0.16 K, as for V"),
        "T": ("geometry", "±0.49 K where the screening predicted 0. The 1-D model has radial conduction only. The CFD "
              "solid conducts heat axially along a cross-section that is 25 % smaller (T01) or 28 % larger (T03) than P00's. "
              "A thin wall redistributes less heat from the hot outlet end towards the cooler inlet end, so the interface peak at the outlet rises; a "
              "thick wall does the opposite"),
    },
    "T max fluid [K]": {
        "V": ("heat transfer", "≤ 0.36 K. Follows the interface temperature; the fluid-cell maximum is 1.7–1.9 K below the interface "
              "facet maximum in every case"),
        "Q": ("heat transfer", "≤ 0.08 K, as for V"),
        "T": ("geometry", "±0.49 K; follows the interface maximum (axial conduction)"),
    },
    "T max solid, cell [K]": {
        "V": ("heat transfer", "≤ 0.11 K; the through-wall ΔT is unchanged and the interface agrees"),
        "Q": ("heat transfer", "≤ 0.15 K"),
        "T": ("geometry", "The CFD change (−0.57 / +0.54 K) is about half the screening change (−1.03 / +0.93 K). The "
              "through-wall conduction term q″·r_o·ln(r_o/r_i)/k changes as predicted, but axial conduction moves the "
              "interface peak the opposite way (row above) and cancels about half of it"),
    },
    "T solid mean [K]": {
        "V": ("developing flow", "The CFD change is 5 % smaller (+21.5 / −17.7 K vs +22.6 / −18.6 K). The 1-D model uses a fully "
              "developed h over the whole length and overpredicts the absolute solid temperature rise by 13 % in P00 "
              "(1-D mean 554.7 K vs CFD 525.5 K). The anchored change inherits that factor. The higher entrance-region h "
              "in the CFD keeps the upstream half cooler"),
        "Q": ("developing flow", "The CFD change is 5–6 % smaller (−24.4 / +24.8 K vs −25.8 / +26.5 K), for the same reason as V. "
              "The CFD response is still about 1.1 × the ±10 % heat-flux step. This is the nonlinearity from k_air(T), μ_air(T) and k_Inconel(T)"),
        "T": ("geometry", "The CFD change (−0.94 / +0.90 K) is twice the screening change (−0.50 / +0.46 K). The volume-weighted mean "
              "over a thicker annulus puts more material near the heated outer surface, and axial conduction warms the "
              "inlet end. Neither effect is in the 1-D radial model"),
    },
    "T solid min [K]": {
        "V": ("heat transfer", "−0.37 / +0.24 K. The minimum is at the adiabatic inlet end face. The 1-D model has no axial "
              "conduction into that end, and the anchoring scales it linearly"),
        "Q": ("heat transfer", "+0.94 / −1.13 K, as for V"),
        "T": ("geometry", "−5.6 / +4.7 K, the largest difference. The adiabatic inlet end is fed by axial conduction from "
              "downstream through the solid cross-section, which shrinks or grows with t. The 1-D model predicts only "
              "∓0.3 K"),
    },
    "Q [W]": ("numerics", "≤ 0.001 %: the anchor is stored as 602.76 W. The heat input is imposed, and T01/T03 hold it at P00's value"),
    "y+ max": {
        "V": ("nonlinear properties", "The Re effect (±9 %) is captured. The extra −1.5 / +1.5 % comes from the inlet wall "
              "temperature. The y⁺ maximum sits in the first axial slab, where the wall is already at 414–436 K. The wall-adjacent air viscosity "
              "follows that wall temperature, which rises at low V and falls at high V. The screening scaled with 300 K inlet properties"),
        "Q": ("nonlinear properties", "+3.4 / −3.2 % where the screening predicted 0: same mechanism, since the inlet wall "
              "temperature scales with q″ (411 K at Q01, 437 K at Q03)"),
        "T": ("nonlinear properties", "+1.5 / −1.2 %. Axial conduction changes the inlet-end wall temperature (418 K at T01, "
              "429 K at T03), and through it the near-wall viscosity at the y⁺ peak. The root cause is geometric; the "
              "mechanism on y⁺ is the temperature dependence of μ"),
    },
}
ORDER = ["Re inlet", "Δp [Pa]", "T_out [K]", "T max interface [K]", "T max fluid [K]", "T max solid, cell [K]",
         "T solid mean [K]", "T solid min [K]", "Q [W]", "y+ max"]
REL = {"Re inlet", "Δp [Pa]", "Q [W]", "y+ max"}


def attr(q, case):
    a = ATTR[q]
    return a if isinstance(a, tuple) else a[case[0]]


def main():
    sc = json.load(open(os.path.join(RES, "screening_comparison.json")))
    L = ["# Section 9B-1: solved CFD against the 9A anchored screening", "",
         "> **RE-ANALYSIS 2026.**", ">",
         "> - Screening: `Analytical_Screening/screening_results.json`, frozen in 9A. It is the Section 2 1-D model anchored to the solved P00.",
         "> - CFD: the solved 9B-1 cases.",
         "> - Nothing was adjusted to make them agree.",
         "> - Generated by `Scripts/screening_comparison_md.py` from `screening_comparison.json`.", "",
         "## 1. How the comparison is made", "",
         "Both models are compared as **changes from their own P00 value**:",
         "",
         "- screening: case minus the 9A anchor;",
         "- CFD: case minus the solved P00.",
         "",
         "This removes the anchoring offset. Temperatures are compared in K; Δp, Re, Q and y⁺ in %.",
         "",
         "Every difference is attributed to one category from the brief: **nonlinear properties, Re, geometry, developing "
         "flow, heat transfer, mesh, numerics**.",
         "",
         "**Mesh is not a cause in any row.**",
         "",
         "- The fluid mesh is bitwise identical in every case.",
         "- The V and Q cases reuse the P00 mesh.",
         "- The T meshes differ only in the solid, and follow the P00 layer rule.",
         "- The solid-layer adequacy check at t = 12 mm (M03) was not in the approved 9B-1 list and is still pending.", "",
         "## 2. Summary", "",
         "| Quantity | Largest CFD − screening difference in the change from P00 | Category |", "|---|---|---|"]
    summ = {}
    for q in ORDER:
        worst = None
        for c in CASES:
            rows = {r[0]: r for r in sc[c]["rows"]}
            s, v = rows[q][1], rows[q][2]
            ds = (s - ANCH[q]) / ANCH[q] * 100 if q in REL else s - ANCH[q]
            dc = (v - P00[q]) / P00[q] * 100 if q in REL else v - P00[q]
            diff = dc - ds
            if worst is None or abs(diff) > abs(worst[1]):
                worst = (c, diff)
        summ[q] = worst
        cats = sorted({attr(q, c)[0] for c in CASES})
        L.append("| %s | %+.3f %s (%s) | %s |" % (q, worst[1], "%" if q in REL else "K", worst[0], " / ".join(cats)))
    L += ["", "**Reading.**", "",
          "- For the operating variables (V, q″), the anchored 1-D screening predicted every maximum temperature, T_out, "
          "Δp and Re within 0.4 K or 0.8 %.",
          "- Its known blind spots show up where they should:",
          "  - the thermal entrance region, which affects the solid mean temperature by 0.9–1.7 K;",
          "  - the wall-temperature dependence of near-wall viscosity, which affects y⁺ by ±3.4 %.",
          "- For wall thickness, the 1-D radial model misses **axial conduction in the solid**. That effect is the same size as "
          "the through-wall effect it does capture. Consequences:",
          "  - the net change of the solid maximum is about half of what was screened;",
          "  - the interface peak changes by +0.5 / −0.5 K where the screening predicted 0;\n  - the inlet-end minimum changes by −5.9 / +5.0 K where the screening predicted ∓0.3 K.",
          "- None of these differences changes a validity margin: the closest is Q03 near-wall air at 583.4 K against 583.4 K screened.",
          "", "## 3. Case by case (change from P00: screening vs CFD)", ""]
    for c in CASES:
        rows = {r[0]: r for r in sc[c]["rows"]}
        L += ["### %s" % c, "", "| Quantity | Screening (absolute) | CFD (absolute) | Screening change | CFD change | CFD − screening | Category | Reason |",
              "|---|---|---|---|---|---|---|---|"]
        for q in ORDER:
            s, v = rows[q][1], rows[q][2]
            if q in REL:
                ds, dc = (s - ANCH[q]) / ANCH[q] * 100, (v - P00[q]) / P00[q] * 100
                u = "%"
            else:
                ds, dc = s - ANCH[q], v - P00[q]
                u = "K"
            cat, why = attr(q, c)
            fs = ("%.1f" % s) if q == "Re inlet" else ("%.4f" % s if q == "y+ max" else "%.3f" % s)
            fv = ("%.1f" % v) if q == "Re inlet" else ("%.4f" % v if q == "y+ max" else "%.3f" % v)
            L.append("| %s | %s | %s | %+.3f %s | %+.3f %s | %+.3f %s | %s | %s |" % (q, fs, fv, ds, u, dc, u, dc - ds, u, cat, why))
        L.append("")
    L += ["## 4. Consequence for later sections", "",
          "- **The screening is adequate for trends and validity margins of the operating variables.** For those, the CFD "
          "confirms it within the stated accuracy.",
          "- **For thickness, the screening understates the axial redistribution of temperature.** The structural "
          "screening for T01/T03 (9A) used the 1-D temperature changes; 9B-2 must use the solved CFD fields (EnSight "
          "exports in each case folder), never the screened ones.",
          "- **The y⁺ policy margin is unaffected.** The largest measured y⁺ is 0.645 (V03), against the 1.0 limit and the 0.8 reuse threshold.", ""]
    open(os.path.join(RES, "SCREENING_COMPARISON.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("SCREENING_COMPARISON.md written;", ascii({q: (w[0], round(w[1], 3)) for q, w in summ.items()}))


if __name__ == "__main__":
    main()
