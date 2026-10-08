# Repository Structure

This copy groups the master archive under six top-level folders. Each group keeps the contents of the master folders mapped to it, with the master folder name dropped, so that files sit where their group says. Where two master folders held files with the same name, the second copy carries a suffix (listed below). Admin, interview-preparation, session-output and root working files are not included.

## Top-level layout

```
Flow_Behavior_Thermal_Effects_Multiphysics_GitHub/
├── README.md
├── GITHUB_CONTENT_AUDIT.md
├── REPOSITORY_STRUCTURE.md
├── MANIFEST.csv
├── .gitignore
├── 01_Project_Documentation/
├── 02_CFD_Fluent/
├── 03_Thermal_Structural_Mechanical/
├── 04_LS_DYNA_Extension/
├── 05_Data/
└── 07_Audit_and_Provenance/
```

There is no 06 folder. The planned analysis-and-scripts folder was not created, because the scripts depend on the study folders they sit in, and moving them would break their relative references. The numbering therefore skips 06. The master archive itself has no 04 or 12 folder either.

MANIFEST.csv lists every file in this repository with its size, SHA-256 hash, group and source location in the master archive. It also lists the 242 duplicate files that were removed from this copy, marked as removed, with the path of the identical copy that was kept.

## Mapping from master folders

| Master folder | Location in this copy | Notes |
|---|---|---|
| 13_Report | 01_Project_Documentation/ | Report PDF and DOCX in Final_Report/, LaTeX source in Source/ |
| 14_Presentation | 01_Project_Documentation/ | Presentation PPTX in Final/ |
| 01_Requirements | 01_Project_Documentation/ | |
| 02_Engineering_Calculations | 01_Project_Documentation/ | Includes baseline_parameters.json and section1_sizing/ |
| 03_CAD_Geometry | 01_Project_Documentation/ | |
| 05_Meshing | 02_CFD_Fluent/ | |
| 06_Fluent_CFD | 02_CFD_Fluent/ | |
| 09_Mesh_Independence | 02_CFD_Fluent/ | |
| 07_Thermal_Analysis | 03_Thermal_Structural_Mechanical/ | |
| 08_Structural_Analysis | 03_Thermal_Structural_Mechanical/ | Includes Buckling/ and Results/ |
| 10_Parametric_Study | 03_Thermal_Structural_Mechanical/ | |
| 15_LS_DYNA_Extension | 04_LS_DYNA_Extension/ | Main results in 12C_Nonlinear_Buckling/ |
| 11_Final_Audit | 07_Audit_and_Provenance/ | Except MASTER_PROJECT_DATA.csv, which is in 05_Data/ |
| 00_admin | Not included | Held for review |
| 15_Interview_Preparation | Not included | Personal |
| Claude outputs | Not included | Session outputs |
| Master root notes and README | Not included | Replaced by this repository's README |

## Suffixed copies

Five destination names were claimed by two master files each. Where the two files were identical, one copy was kept. Where they differed, the second source is kept under a suffixed name:

| Copy path | Master source |
|---|---|
| 03_Thermal_Structural_Mechanical/Figures/README.md | 08_Structural_Analysis/Figures/README.md |
| 03_Thermal_Structural_Mechanical/Figures/README_from_10_Parametric_Study.md | 10_Parametric_Study/Figures/README.md |
| 03_Thermal_Structural_Mechanical/Results/README.md | 08_Structural_Analysis/Results/README.md |
| 03_Thermal_Structural_Mechanical/Results/README_from_10_Parametric_Study.md | 10_Parametric_Study/Results/README.md |
| 01_Project_Documentation/Figures/LSD_deformed_shape_C5_nt.png | 13_Report/Figures/LSD_deformed_shape_C5_nt.png |
| 01_Project_Documentation/Figures/LSD_deformed_shape_C5_nt_from_14_Presentation.png | 14_Presentation/Figures/LSD_deformed_shape_C5_nt.png |
| 01_Project_Documentation/Figures/LSD_load_lateral_nt.png | 13_Report/Figures/LSD_load_lateral_nt.png |
| 01_Project_Documentation/Figures/LSD_load_lateral_nt_from_14_Presentation.png | 14_Presentation/Figures/LSD_load_lateral_nt.png |
| 01_Project_Documentation/Figures/LSD_mechanical_vs_nonlinear_nt.png | 13_Report/Figures/LSD_mechanical_vs_nonlinear_nt.png |
| 01_Project_Documentation/Figures/LSD_mechanical_vs_nonlinear_nt_from_14_Presentation.png | 14_Presentation/Figures/LSD_mechanical_vs_nonlinear_nt.png |

Three Fluent cleanup scripts had a host name in their filenames. They are renamed to replace that name with HOST (for example cleanup-fluent-HOST-25340.bat), and the name inside them is replaced the same way.

## Removed duplicate copies

242 files were removed from this repository because each was byte-identical (same SHA-256 hash) to another file that is kept. Each removed file's identical copy is named in MANIFEST.csv. No content was lost. Where a script or note refers to a removed path, the file at the kept path has the same content.

| Kind of duplicate | Files | Size |
|---|---|---|
| Ansys Workbench project-folder mirror (dp0) of a solver output file | 151 | 359.4 MB |
| Audit copy of a mapped or solver output file | 32 | 49.0 MB |
| Audit or mapping copy from a superseded or failed run | 22 | 31.3 MB |
| Other duplicate copies (CFD cell exports, meshes, LS-DYNA node decks, EnSight geometry) | 30 | 53.5 MB |
| Workbench project-folder copy of a solver output file | 2 | 2.8 MB |
| Mesh-study solver output copy | 5 | 1.7 MB |
| Total | 242 | 497.7 MB |

The Workbench project files (.wbpj) that owned the dp0 folders are not in this repository, because their extension is not on the allow-list. The dp0 copies were therefore not usable on their own. Smaller duplicate copies, under 100 KB in total about 6.6 MB across 507 files, were kept because they record per-run audit history.

## Key locations

| Content | Path |
|---|---|
| Report, PDF | 01_Project_Documentation/Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.pdf |
| Report, DOCX | 01_Project_Documentation/Final_Report/Flow_Behavior_Thermal_Effects_Multiphysics_Internship_Report.docx |
| Report edit audit (LS-DYNA section) | 01_Project_Documentation/Final_Report/EDIT_AUDIT_LSDYNA.md |
| Presentation | 01_Project_Documentation/Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx |
| Presentation edit audit (LS-DYNA section) | 01_Project_Documentation/Final/EDIT_AUDIT_LSDYNA.md |
| Master data register | 05_Data/MASTER_PROJECT_DATA.csv |
| Buckling results | 03_Thermal_Structural_Mechanical/Buckling/BUCKLING_RESULTS.md |
| LS-DYNA 12C results | 04_LS_DYNA_Extension/12C_Nonlinear_Buckling/FINAL_12C_RESULTS.md |
| LS-DYNA 12C data | 04_LS_DYNA_Extension/12C_Nonlinear_Buckling/IMPERFECTION_SENSITIVITY.csv and MECHANICAL_vs_LSDYNA.csv |
| LS-DYNA 12C plots | 04_LS_DYNA_Extension/12C_Nonlinear_Buckling/ |
| Master audit records | 07_Audit_and_Provenance/ |
| Full file list with hashes | MANIFEST.csv |

## Paths inside documents

Many files in this copy refer to master folder names such as `06_Fluent_CFD/...` or `08_Structural_Analysis/...`. Those references describe the master archive, and they do not resolve inside this copy. Use the mapping above to find the file that a reference points to. Scripts that rebuild the report or presentation also refer to the master layout and will need path edits before they can run from this copy.
