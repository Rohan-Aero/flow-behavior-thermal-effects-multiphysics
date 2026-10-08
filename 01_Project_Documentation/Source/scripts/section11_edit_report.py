# -*- coding: utf-8 -*-
"""Section 11 - targeted date/framing edits of the existing report source (no technical content changed)."""
import sys, os
R = sys.argv[1]          # 13_Report directory
E = {}
def rep(f, a, b, count=1):
    E.setdefault(f, []).append((a, b, count))

# ------------------------------------------------------------------ preamble (PDF metadata, running header, provenance macros)
f = "Source/preamble.tex"
rep(f, "pdfsubject={Re-analysed CFD, conjugate heat transfer and thermo-structural analysis of a heated cylindrical duct},",
       "pdfsubject={CFD, conjugate heat transfer and thermo-structural analysis of a heated cylindrical duct},")
rep(f, "thermal stress, linear buckling, re-analysis 2026}}", "thermal stress, linear buckling, Eleation internship}}")
rep(f, r"\fancyhead[R]{\sffamily\footnotesize\color{recon} Re-analysis 2026}", r"\fancyhead[R]{\sffamily\footnotesize Eleation internship, February--May 2025}")
rep(f, r"\newcommand{\provmech}{ANSYS Mechanical 2026 R1 image export", r"\newcommand{\provmech}{ANSYS Mechanical image export")
rep(f, r"exported from the converged ANSYS Fluent 2026 R1 solution; not a GUI screenshot.}", r"exported from the converged ANSYS Fluent solution; not a GUI screenshot.}")
rep(f, r"\newcommand{\provcad}{Rendered from the geometry exported by ANSYS SpaceClaim 2026 R1; not a GUI screenshot.}",
       r"\newcommand{\provcad}{Rendered from the geometry exported by ANSYS SpaceClaim; not a GUI screenshot.}")

# ------------------------------------------------------------------ front matter
f = "Source/chapters/frontmatter.tex"
rep(f, r"{\sffamily\Large Re-analysed CFD, Conjugate Heat Transfer and Thermo-Structural Analysis of a Heated Cylindrical Duct\par}",
       r"{\sffamily\Large CFD, Conjugate Heat Transfer and Thermo-Structural Analysis of a Heated Cylindrical Duct\par}")
rep(f, r"{\footnotesize\itshape Physics chain of the re-analysed model (Section 3 drawing;", r"{\footnotesize\itshape Physics chain of the model (Section 3 drawing;")
rep(f, r"{\normalsize Internship organisation: Eleation \quad\textbullet\quad Internship period: February--May 2025\par}",
       "{\\normalsize Eleation\\par}\n{\\normalsize Internship: February--May 2025\\par}")
rep(f, r"{\sffamily\small\color{recon} Technical re-analysis prepared in 2026 with ANSYS Student 2026 R1\par}",
       r"{\sffamily\small Numerical analysis using ANSYS Workbench, ANSYS Fluent and ANSYS Mechanical\par}")
rep(f, "\\vfill\n{\\small September 2026\\par}\n\\end{titlepage}", "\\vfill\n\\end{titlepage}")
rep(f, "Tools of the original internship & ANSYS Workbench, ANSYS Fluent, ANSYS Mechanical \\\\\n"
       "Tools of this re-analysis & ANSYS Student 2026 R1: Workbench, SpaceClaim, Fluent, Mechanical / MAPDL; Python 3.10 (bundled with ANSYS) for calculations and post-processing \\\\\n"
       "Re-analysis period & September 2026 \\\\\n"
       "Report status & Final engineering report of the re-analysed project (Section 10B)",
       "Tools & ANSYS Workbench (SpaceClaim), ANSYS Fluent, ANSYS Mechanical / MAPDL; Python 3.10 (bundled with ANSYS) for calculations and post-processing \\\\\n"
       "Report status & Final internship engineering report")
rep(f, "Re-analysed CFD, Conjugate Heat Transfer and Thermo-Structural Analysis of a Heated Cylindrical Duct\n\n\\section*{What is historical and what is re-analysed}\n"
       "Only the items in the first five rows of the table above (engineer, programme, organisation, period and the original tool set) are\n"
       "documented facts of the 2025 internship. The problem definition, geometry, materials, loads, meshes, solver settings and every\n"
       "numerical result in this report are 2026 re-analysiss. Chapter~\\ref{ch:intro} and Appendix~\\ref{app:trace} describe the labelling used.\n",
       "CFD, Conjugate Heat Transfer and Thermo-Structural Analysis of a Heated Cylindrical Duct\n")
rep(f, "% ---------------------------------------------------------------- 4. declaration / re-analysis note\n\\chapter*{Declaration and Re-analysis Note}\n\\addcontentsline{toc}{chapter}{Declaration and Re-analysis Note}\n",
       "% ---------------------------------------------------------------- 4. declaration / note on the analysis record\n\\chapter*{Declaration}\n\\addcontentsline{toc}{chapter}{Declaration}\n")
rep(f, "\\recbox{\\textbf{Re-analysis note.} The original internship project files were unavailable at the time of re-analysis. Accordingly,\n"
       "the geometry, operating parameters, simulation setup and numerical results presented in this report are re-analysed engineering work\n"
       "based on the surviving project documentation and newly generated ANSYS simulations. They should not be interpreted as recovered copies of\n"
       "the original internship analysis.}",
       "\\recbox{\\textbf{Note on the analysis record.} The original internship project files were not retained. The geometry, operating\n"
       "parameters, simulation set-up and numerical results presented in this report therefore come from a complete re-analysis of the\n"
       "internship problem, carried out after the internship with ANSYS Workbench, Fluent and Mechanical and based on the documented project\n"
       "scope. They are not copies of the original internship analysis.}")
rep(f, "The project record states the governing position as follows. The original internship project files were lost; a filesystem sweep on\n"
       "18 September 2026 found no original ANSYS artefact. The present work is a technical re-analysis made in 2026, covering the geometry,\n"
       "boundary conditions, material selections, analytical calculations, CFD simulations, structural simulations and results. Only surviving\n"
       "documented internship information is described as historical fact. Everything else is labelled with one of the following terms:",
       "Only documented internship information (engineer, programme, organisation, period and tool set) is described as historical fact.\n"
       "Every other value in this report is labelled with one of the following terms:")
rep(f, "\\item \\textbf{Re-analysed} -- an input value chosen in 2026 with a stated rationale", "\\item \\textbf{Selected} -- an input value chosen for this study with a stated rationale")
rep(f, "\\item \\textbf{Assumed} -- an engineering idealisation made in 2026 (for example", "\\item \\textbf{Assumed} -- an engineering idealisation (for example")
rep(f, "\\item \\textbf{Calculated 2026} -- a hand or script calculation from re-analysed inputs (the Section 2 analytical baseline);",
       "\\item \\textbf{Calculated} -- a hand or script calculation from the selected inputs (the Section 2 analytical baseline);")
rep(f, "\\item \\textbf{Simulated 2026} -- the output of an ANSYS Student 2026 R1 solution of this project.",
       "\\item \\textbf{Simulated} -- the output of an ANSYS solution of this project.")
rep(f, "\\textbf{Declaration.} This report presents the re-analysed analysis as documented in the project record (the file",
       "\\textbf{Declaration.} This report presents the analysis as documented in the project record (the file")
rep(f, "(\\texttt{MASTER\\_PROJECT\\_DATA.csv}). Every numerical result quoted is a\n2026 calculation or simulation of the re-analysed problem and is traceable to a project file.",
       "(\\texttt{MASTER\\_PROJECT\\_DATA.csv}). Every numerical result quoted is a\ncalculation or simulation of the analysed problem and is traceable to a project file.")
rep(f, "Rohan Balram Patel \\hfill September 2026", "Rohan Balram Patel")
rep(f, "% ---------------------------------------------------------------- 5. acknowledgement\n\\chapter*{Acknowledgement}",
       "% ---------------------------------------------------------------- 5. acknowledgement\n\\clearpage   % keeps the original page break (Acknowledgement and Abstract on page ii)\n\\chapter*{Acknowledgement}")
rep(f, "during which the original project on flow behaviour and\nthermal effects in multiphysics systems was carried out,",
       "during which the project on flow behaviour and\nthermal effects in multiphysics systems was carried out,")
rep(f, "The re-analysis documented here relied on the ANSYS Student 2026 R1 software\nand on the published data and correlations listed in the references.",
       "The analysis documented here relied on ANSYS Workbench, Fluent and Mechanical\nand on the published data and correlations listed in the references.")
rep(f, "This report presents a technical re-analysis of the Eleation internship project \\emph{Flow Behavior and Thermal Effects in Multiphysics\n"
       "Systems} (February--May 2025). The original project files were unavailable; the geometry, operating parameters, simulation set-up and all\n"
       "numerical results are 2026 re-analysiss produced with ANSYS Student 2026 R1. The system is an air-cooled, externally heated Inconel 718\n"
       "duct (20/40~mm inner/outer diameter, 600~mm long).",
       "This report presents the Eleation internship project \\emph{Flow Behavior and Thermal Effects in Multiphysics Systems}\n"
       "(February--May 2025): a numerical analysis using ANSYS Workbench, ANSYS Fluent and ANSYS Mechanical. The system is an air-cooled,\n"
       "externally heated Inconel 718 duct (20/40~mm inner/outer diameter, 600~mm long).")

# ------------------------------------------------------------------ chapters
f = "Source/chapters/ch01_introduction.tex"
rep(f, "May 2025 with ANSYS Workbench, Fluent and Mechanical. Its files were later lost. This report documents a complete technical re-analysis\n"
       "of the project made in 2026: a representative multiphysics problem was defined, solved and audited again from first principles, with every\n"
       "input labelled as re-analysed or assumed and every result traceable to a 2026 calculation or simulation. The re-analysis note at the\n"
       "front of the report states this status formally; it applies to every number in the following chapters.",
       "May 2025 with ANSYS Workbench, Fluent and Mechanical. Its original files were not retained, so the analysis reported here was carried\n"
       "out again after the internship: a representative multiphysics problem was defined, solved and audited from first principles, with every\n"
       "input labelled as selected or assumed and every result traceable to a calculation or simulation in the project record. The note on the\n"
       "analysis record at the front of the report states this formally; it applies to every number in the following chapters.")
rep(f, "The re-analysis has two purposes. The first is technical:", "The study has two purposes. The first is technical:")
rep(f, "The second is documentary: to replace the lost internship record with a reproducible one whose status is stated explicitly, so that no\n"
       "re-analysed value can be mistaken for a recovered original.",
       "The second is documentary: to provide a reproducible and auditable record of the internship problem, in which the status of every\n"
       "value is stated explicitly.")
f = "Source/chapters/ch02_system.tex"
rep(f, "All dimensions and loads are re-analysed class-B inputs (Chapter~\\ref{ch:params}).", "All dimensions and loads are selected class-B inputs (Chapter~\\ref{ch:params}).")
rep(f, "\\caption[Engineering drawing of the re-analysed heated duct]{Engineering drawing of the re-analysed heated duct:",
       "\\caption[Engineering drawing of the heated duct]{Engineering drawing of the heated duct:")
rep(f, "\\src{Source: \\texttt{03\\_CAD\\_Geometry/Drawings/ENGINEERING\\_DRAWING.png}; drawing produced in 2026 for the re-analysis, not an original internship drawing.}",
       "\\src{Source: \\texttt{03\\_CAD\\_Geometry/Drawings/ENGINEERING\\_DRAWING.png} (project drawing of the analysed duct).}")
rep(f, "\\src{Source: \\texttt{03\\_CAD\\_Geometry/Drawings/PHYSICS\\_SCHEMATIC.png} (Section 3, 2026).}",
       "\\src{Source: \\texttt{03\\_CAD\\_Geometry/Drawings/PHYSICS\\_SCHEMATIC.png} (Section 3).}")
f = "Source/chapters/ch03_theory.tex"
rep(f, "theory; what is re-analysed is the choice of relations and the parameters fed into them.", "theory; what is specific to this study is the choice of relations and the parameters fed into them.")
f = "Source/chapters/ch04_parameters.tex"
rep(f, "The geometry of Table~\\ref{tab:geometry} was chosen in 2026 (decision D-008):", "The geometry of Table~\\ref{tab:geometry} was chosen by decision D-008:")
f = "Source/chapters/ch05_cad.tex"
rep(f, "The geometry was built in ANSYS SpaceClaim 2026 R1 entirely by an IronPython script", "The geometry was built in ANSYS SpaceClaim entirely by an IronPython script")
rep(f, "\\caption[Re-analysed CAD model]{Re-analysed CAD model:", "\\caption[CAD model]{CAD model:")
f = "Source/chapters/ch08_cfd_results.tex"
rep(f, "They are simulated 2026 results of the re-analysed problem.", "They are simulation results of the baseline problem.")
f = "Source/chapters/ch14_supports.tex"
rep(f, "The real flange of the duct is not defined in the re-analysed project,", "The real flange of the duct is not defined in this project,")
f = "Source/chapters/ch16_uncertainty.tex"
rep(f, "\\section{Reconstruction Limitation}\n"
       "The original internship files are unavailable. No result can be compared with the 2025 analysis, the original geometry and parameters are\n"
       "unknown, and nothing in this report is a recovered value. The re-analysed problem is representative, not a reproduction.",
       "\\section{Data-Availability Limitation}\n"
       "The original internship files were not retained, so no result can be compared with the analysis made during the internship, and nothing\n"
       "in this report is a recovered value. The analysed problem is representative of the internship problem, not a reproduction of it.")
f = "Source/chapters/ch17_discussion.tex"
rep(f, "The engineering implication, within the\nre-analysed idealised model, is that", "The engineering implication, within the\nidealised model, is that")
f = "Source/chapters/ch18_conclusions.tex"
rep(f, "The following conclusions apply within the re-analysed, idealised numerical model; they are 2026 simulation results that have not been\nvalidated against measurement.",
       "The following conclusions apply within the idealised numerical model; they are simulation results that have not been\nvalidated against measurement.")

# ------------------------------------------------------------------ appendices
f = "Appendices/appendices.tex"
rep(f, "Table~\\ref{tab:appA} lists the complete re-analysed input set of the official baseline P00;", "Table~\\ref{tab:appA} lists the complete input set of the official baseline P00;")
rep(f, "All inputs are class B\n(re-analysed with a stated rationale); the project contains no class-A (documented original) parameter.",
       "All inputs are class B\n(selected with a stated rationale); no input is class A (taken from an original internship document).")
rep(f, "matplotlib plots of the 2026 analytical model.}", "matplotlib plots of the analytical model.}")
rep(f, "\\chapter{Traceability and Re-analysis Note}\\label{app:trace}\n"
       "\\textbf{Status of the work.} The re-analysis note at the front applies to every value: the results are 2026 re-analysiss, not recovered\n"
       "copies of the original internship analysis; only the engineer, programme, organisation, period and tool set are documented internship facts.",
       "\\chapter{Traceability}\\label{app:trace}\n"
       "\\textbf{Status of the work.} The note on the analysis record at the front of the report applies to every value; only the engineer,\n"
       "programme, organisation, period and tool set are documented internship facts.")
rep(f, "All figures are hash-verified 2026 project files (\\texttt{Figures/figure\\_sources.json});", "All figures are hash-verified project files (\\texttt{Figures/figure\\_sources.json});")

# ------------------------------------------------------------------ generated tables (and their generator, kept in sync)
for f in ("Tables/tab_geometry.tex", "Source/scripts/gen_tables.py"):
    rep(f, "Duct geometry of the re-analysed baseline (re-analysed class-B inputs, verified in the CAD model)",
           "Duct geometry of the baseline (selected class-B inputs, verified in the CAD model)")
for f in ("Tables/tab_operating.tex", "Source/scripts/gen_tables.py"):
    rep(f, "Baseline operating condition P00 (re-analysed inputs)", "Baseline operating condition P00 (selected inputs)")
for f in ("Tables/tab_appA.tex", "Source/scripts/gen_tables.py"):
    rep(f, "Complete re-analysed input set of the baseline P00", "Complete input set of the baseline P00")
    rep(f, "All inputs are re-analysed (class B); none is a recovered original value.", "All inputs are selected (class B) with a stated rationale.")
f = "Tables/tab_operating.tex"
rep(f, "& re-analysed \\\\", "& selected \\\\", count=6)
rep(f, "& simulated 2026 \\\\", "& simulated \\\\")
f = "Source/scripts/gen_tables.py"
rep(f, '"re-analysed"]', '"selected"]', count=6)
rep(f, '"simulated 2026"]', '"simulated"]')

# ------------------------------------------------------------------ references (citation kept factual; framing note neutral)
f = "References/refs.bib"
rep(f, "note         = {Software used for all CFD solutions of this re-analysis}", "note         = {Software used for all CFD solutions of this study}")

# ------------------------------------------------------------------ DOCX converter: same provenance macros as the PDF
f = "Source/scripts/make_docx.py"
rep(f, r"\newcommand{\provmech}{ANSYS Mechanical 2026 R1 image export", r"\newcommand{\provmech}{ANSYS Mechanical image export")
rep(f, r"exported from the converged ANSYS Fluent 2026 R1 solution; not a GUI screenshot.}", r"exported from the converged ANSYS Fluent solution; not a GUI screenshot.}")
rep(f, r"\newcommand{\provcad}{Rendered from the geometry exported by ANSYS SpaceClaim 2026 R1; not a GUI screenshot.}",
       r"\newcommand{\provcad}{Rendered from the geometry exported by ANSYS SpaceClaim; not a GUI screenshot.}")

log, new = [], {}
for f, reps in E.items():                       # pass 1: validate every replacement before writing anything
    p = os.path.join(R, f)
    s = open(p, encoding="utf-8").read()
    for a, b, n in reps:
        c = s.count(a)
        if c != n:
            raise SystemExit("COUNT %d != %d in %s: %r" % (c, n, f, a[:90]))
        s = s.replace(a, b)
        log.append((f, a.replace("\n", " ")[:110], b.replace("\n", " ")[:110], n))
    new[p] = s
for p, s in new.items():                        # pass 2: write
    open(p, "w", encoding="utf-8").write(s)
import json
json.dump(log, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_edits_log.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("edits applied:", len(log), "files:", len(E))
