# Flow Behavior and Thermal Effects in Multiphysics Systems

This repository holds the files for a multiphysics study of a tube with internal forced convection and wall heating. The study covers computational fluid dynamics (CFD), thermal and structural analysis, a buckling study, and a follow-on nonlinear buckling study in LS-DYNA.

The main work was carried out as an internship project from February to May 2025. The original internship project files were not retained. The analysis was carried out after the internship, from the documented project scope, as stated in the report's declaration. The LS-DYNA study is a follow-on extension carried out after the internship. It was not part of the internship.

Status: Public project repository. The internship work covers February–May 2025, while the documented analysis was carried out afterward from the retained project scope. The LS-DYNA nonlinear buckling study is a follow-on technical extension and was not part of the internship. No open-source licence is granted. Third-party items and attribution information are listed in NOTICE.md

## Geometry and conditions

The tube has an inner diameter of 20 mm, an outer diameter of 40 mm, a length of 600 mm, and a wall thickness of 10 mm. The CFD inlet temperature is 300 K, the inlet velocity is 23.5 m/s, and the wall heat flux is 8000 W/m².

## Stages and tools

| Stage | Tool | Model |
|---|---|---|
| CFD | Fluent 2026 R1 | Medium mesh, 159,840 cells |
| Thermal and structural | ANSYS 2026 R1 (Student) | Mesh B, SOLID186, 108,252 nodes, 23,400 elements |
| Nonlinear buckling (follow-on) | LS-DYNA R16.1 (Student) | ELFORM 23, MAT_004 thermo-elastic (no plasticity), NSOLVR 12 |

## Key results

CFD, medium mesh:

| Quantity | Value |
|---|---|
| Reynolds number at inlet | 29,958 |
| Pressure drop, Δp | 438.13 Pa |
| Outlet fluid temperature | 368.93 K |
| Heat transferred, Q | 602.755 W |
| Maximum solid temperature | 562.58 K |
| Through-wall temperature difference | 7.581 K |

Thermal and structural, buckling:

| Quantity | Value |
|---|---|
| LC2 maximum von Mises stress | 605.161 MPa |
| LC2 maximum deformation | 0.1349 mm |
| LC2 end reaction | 548,936.6 N |
| LC1 maximum deformation | 1.8443 mm |
| LC1 maximum von Mises stress | 24.282 MPa |
| Utilisation at the critical node | 0.5780 |
| First-yield factor | 1.730 |
| Buckling load factor λ₁ (support case S1) | 1.10805 |
| Critical buckling load, P_cr (S1) | 608.25 kN |
| Buckling load factor λ₁ for support cases S2 and S3 | 4.29995 and 2.23224 |
| Critical buckling load for S2 and S3 | 2360.40 kN and 1225.36 kN |

LS-DYNA, 12C nonlinear buckling (follow-on extension):

| Quantity | Value |
|---|---|
| Imperfection amplitudes (cases C1, C3, C5) | 0.1, 0.6, 1.2 mm |
| Southwell characteristic-load estimates | 612.3, 611.1, 607.7 kN |
| Characteristic-load range | 607.7 to 612.3 kN |
| Maximum axial force reached, C1 (0.1 mm) | 601.0 kN at λ = 1.185 |
| Perfect-geometry reference, C0 | not identifiable |

The LS-DYNA model uses MAT_004, a thermo-elastic material with no plasticity. Its characteristic loads should be read with that limit in mind.

## Where to find things

| Item | Location |
|---|---|
| Report (PDF) | [01_Project_Documentation/Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.pdf](01_Project_Documentation/Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.pdf) |
| Report (DOCX) | [01_Project_Documentation/Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.docx](01_Project_Documentation/Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.docx) |
| Presentation | [01_Project_Documentation/Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx](01_Project_Documentation/Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx) |
| Master data register | [05_Data/MASTER_PROJECT_DATA.csv](05_Data/MASTER_PROJECT_DATA.csv) |
| Buckling results | [03_Thermal_Structural_Mechanical/Buckling/BUCKLING_RESULTS.md](03_Thermal_Structural_Mechanical/Buckling/BUCKLING_RESULTS.md) |
| LS-DYNA 12C results | [04_LS_DYNA_Extension/12C_Nonlinear_Buckling/FINAL_12C_RESULTS.md](04_LS_DYNA_Extension/12C_Nonlinear_Buckling/FINAL_12C_RESULTS.md) |
| Folder layout | [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) |
| Content audit | [GITHUB_CONTENT_AUDIT.md](GITHUB_CONTENT_AUDIT.md) |
| Full file list with hashes | [MANIFEST.csv](MANIFEST.csv) |

## What is not included

Solver databases, binary result files, aborted and killed solver runs, licence-probe outputs, CSV exports over 10 MB, and the admin and interview-preparation folders are not in this copy. They remain in the master archive. [GITHUB_CONTENT_AUDIT.md](GITHUB_CONTENT_AUDIT.md) lists the exclusions by reason. To keep the repository under 1 GB, 242 files that were byte-identical to other kept files were also left out. [MANIFEST.csv](MANIFEST.csv) marks each one as removed and names the copy that was kept.

## Reproducing the analysis

Reproducing the analysis needs ANSYS and LS-DYNA with valid licences. Scripts and input files that referred to the original working folder now use placeholders such as `<PROJECT_ROOT>`, `<OUTPUT_ROOT>` and `<SCRATCH_ROOT>`. Set these to local paths before running anything. This README does not claim that the analyses can be re-run from this copy.
