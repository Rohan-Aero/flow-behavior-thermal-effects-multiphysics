# -*- coding: utf-8 -*-
"""Section 13 - controlled integration of the additional LS-DYNA nonlinear buckling analysis into the existing report source.
New content: chapters/ch14b_lsdyna.tex (Section 14.7, input after ch14_supports) and Tables/tab_lsdyna.tex.
This script makes the remaining edits: the input line in main.tex, the table index entry and short cross-reference sentences where
the existing text would otherwise contradict the new section. Every edit must match exactly once; no number of the original
analysis is changed. Usage: python section13_edit_report.py <13_Report dir>   (writes section13_report_edits_log.json)"""
import os, sys, json
R = sys.argv[1]
LS = r"Section~\ref{sec:lsdyna}"
EDITS = [
    ("Source/main.tex", "\\input{chapters/ch14_supports}\n", "\\input{chapters/ch14_supports}\n\\input{chapters/ch14b_lsdyna}\n"),
    ("Tables/tables_index.tsv", "tab_support\ttab:support\t", None),   # existence check only; the new row is appended below
    # Abstract: one sentence on the extension; the open-uncertainty sentence is made precise ("measured" imperfections)
    ("Source/chapters/frontmatter.tex",
     "flux and the 8~mm wall.\n\nThe results are not validated against measurement. The real end restraint, geometric imperfections and\n",
     "flux and the 8~mm wall. An additional geometrically nonlinear analysis with ANSYS LS-DYNA, performed as an extension with mode-shaped\n"
     "numerical imperfections of 0.1, 0.6 and 1.2~mm, gives Southwell characteristic-load estimates of 607.7--612.3~kN, close to the linear\n"
     "critical load of 608.25~kN, while lateral deflection and stress grow strongly with the imperfection amplitude.\n\n"
     "The results are not validated against measurement. The real end restraint, measured geometric imperfections and\n"),
    # Ch. 1 scope
    ("Source/chapters/ch01_introduction.tex",
     "These exclusions are revisited as limitations in Chapter~\\ref{ch:unc} and as future work in Chapter~\\ref{ch:future}.\n",
     "These exclusions are revisited as limitations in Chapter~\\ref{ch:unc} and as future work in Chapter~\\ref{ch:future}. An additional\n"
     "geometrically nonlinear, elastic buckling analysis with ANSYS LS-DYNA, performed as an extension of the thermo-structural analysis, is\n"
     "reported separately in " + LS + "; it does not change the scope or the results of the main study.\n"),
    # Ch. 13 limitations
    ("Source/chapters/ch13_buckling.tex",
     "materially nonlinear analysis would be required to determine a collapse load (Chapter~\\ref{ch:future}).",
     "materially nonlinear analysis would be required to determine a collapse load (Chapter~\\ref{ch:future}). An elastic, geometrically\n"
     "nonlinear imperfection-sensitivity extension is reported in " + LS + "; it does not determine a collapse load."),
    # Ch. 16 geometric imperfections
    ("Source/chapters/ch16_uncertainty.tex",
     "laterally below the bifurcation load and its capacity is lower; the size of the reduction is unknown without an imperfection-sensitive\nnonlinear analysis.\n",
     "laterally below the bifurcation load and its capacity is lower; the size of the reduction is unknown without an imperfection-sensitive\n"
     "nonlinear analysis. The additional LS-DYNA analysis (" + LS + ") quantifies the elastic response for three numerical imperfection\n"
     "amplitudes; without measured imperfection data and an inelastic material model, the reduction for a real tube remains unknown.\n"),
    # Ch. 17 buckling behaviour
    ("Source/chapters/ch17_discussion.tex",
     "indicator for a perfect column; imperfections and inelastic behaviour act only to lower the real capacity.\n",
     "indicator for a perfect column; imperfections and inelastic behaviour act only to lower the real capacity. The additional LS-DYNA\n"
     "analysis (" + LS + ") is consistent with this: with mode-shaped imperfections the lateral deflection and stress grow well below\n"
     "$\\lambda_1$, while the Southwell characteristic-load estimates stay within 1\\,\\% of the linear critical load.\n"),
    # Ch. 18 conclusions: new item + precise limitation
    ("Source/chapters/ch18_conclusions.tex",
     "      stability conclusion.\n\\item \\textbf{Limitations.} The real end restraint, geometric imperfections and inelastic material behaviour were not modelled, the CFD model\n"
     "      form was not varied, and no experimental data exist.",
     "      stability conclusion.\n"
     "\\item \\textbf{Additional nonlinear LS-DYNA analysis (extension).} With numerical mode-1 imperfections of 0.1, 0.6 and 1.2~mm, the\n"
     "      Southwell characteristic-load estimates (607.7--612.3~kN) are close to the linear critical load of 608.25~kN: the characteristic\n"
     "      global buckling load is relatively insensitive to the tested amplitudes, while the onset of lateral deformation, the deflection\n"
     "      and the stress at a given load are strongly imperfection-sensitive. The model is elastic and first local yield is reached at\n"
     "      $\\lambda$ = 0.974--1.109, so the later parts of the load paths lie outside its validated range. The result is not a real-world\n"
     "      capacity, a factor of safety or an experimental validation (" + LS + ").\n"
     "\\item \\textbf{Limitations.} The real end restraint and inelastic material behaviour were not modelled, geometric imperfections only as\n"
     "      numerical amplitudes in the additional elastic LS-DYNA analysis, the CFD model form was not varied, and no experimental data exist."),
    # Ch. 19 future work
    ("Source/chapters/ch19_future.tex",
     "The following work would close the open items identified in Chapter~\\ref{ch:unc}. None of it has been performed.\n",
     "The following work would close the open items identified in Chapter~\\ref{ch:unc}. None of it has been performed, except that item 3\n"
     "is addressed in part by the additional elastic LS-DYNA analysis of " + LS + ".\n"),
    ("Source/chapters/ch19_future.tex",
     "      the geometrically nonlinear load--deflection path to the limit point (task T-035).\n",
     "      the geometrically nonlinear load--deflection path to the limit point (task T-035). The additional LS-DYNA analysis covers the\n"
     "      elastic part with numerical amplitudes of 0.1--1.2~mm; tolerance-based amplitudes, an elastic--plastic material model and the\n"
     "      limit point remain open.\n"),
    # Uncertainty register, row 8
    ("Tables/tab_unc.tex",
     "8 & Geometric imperfection & not modelled; reduces real capacity below $\\lambda_1$ by an unknown amount & primary \\\\",
     "8 & Geometric imperfection & not modelled in the Mechanical study (numerical amplitudes only in the additional elastic LS-DYNA analysis, Section~\\ref{sec:lsdyna}); reduces real capacity below $\\lambda_1$ by an unknown amount & primary \\\\"),
]
log = []
for f, old, new in EDITS:
    p = os.path.join(R, f); s = open(p, encoding="utf-8").read()
    n = s.count(old)
    assert n == 1, (f, n, old[:80])
    if new is not None:
        s = s.replace(old, new); open(p, "w", encoding="utf-8", newline="").write(s)
    log.append({"file": f, "old": old, "new": new})
# new table index row (after tab_support)
p = os.path.join(R, "Tables", "tables_index.tsv"); L = open(p, encoding="utf-8").read().split("\n")
i = [k for k, l in enumerate(L) if l.startswith("tab_support\t")][0]
row = "tab_lsdyna\ttab:lsdyna\tAdditional LS-DYNA nonlinear analysis: three-point imperfection sensitivity under S1 / LC2 (elastic, geometrically nonlinear)"
assert not any(l.startswith("tab_lsdyna\t") for l in L)
L.insert(i + 1, row); open(p, "w", encoding="utf-8", newline="").write("\n".join(L))
log.append({"file": "Tables/tables_index.tsv", "old": None, "new": row})
json.dump(log, open(os.path.join(R, "Source", "scripts", "section13_report_edits_log.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("edits applied:", len(log))
