# GitHub Content Audit

Status: final publication audit of the staging copy. **Decision: NOT-PUBLIC-READY.** Nothing has been published. No GitHub repository has been created, git has not been initialised, nothing has been pushed, and no licence has been selected. The master project archive has not been modified. The audit stops here until the owner has reviewed the open points in section 8.

## 0. Final decision

The copy is NOT-PUBLIC-READY. The inventory, manifest, licence exclusion, link and sensitive-information checks pass (section 7). The following items block publication:

1. Eleation's permission to publish its name and the internship description: the owner reports verbal confirmation from Eleation. No written record is held. This is an external decision, not a licensing assumption (section 5).
2. The redistribution terms for Ansys Student and LS-DYNA solver outputs have not been verified against the applicable licence text. The repository makes no claim that these outputs are freely redistributable.
3. Provenance wording was changed in the working files, in the workbook PARAMETERS.xlsx and in a dataset copy. The owner has not yet reviewed that change. Technical uses of "reconstruct" in the Fluent sense are kept on purpose (section 6).
4. The compiled report states no date, but working documents and the presentation text state 2026 in several places. The owner must choose one date policy. The presentation was not modified, because the report and presentation are outside this task (section 6).
5. The QC checklist recorded a page count, a PDF hash and a DOCX hash that did not match the delivered files. They are corrected here, but the QC checks were recorded against an earlier build and must be re-run.

## 1. Scope and method

The master archive was listed in full: path, size and modification time for each of its 5,916 files, with no file contents read to classify them. Each file was then classified as included or excluded by rule. Included files were copied into this repository, and each copy was checked against its source by SHA-256. A sensitive-information scan was run on the copy only. Text copies with local identifiers were sanitised in place, and each sanitised file was checked against its master file by applying the same substitutions and comparing the results.

The repository was then reduced below 1 GB by removing byte-identical duplicate files. Before anything was moved, every candidate was written to a review table with its path, size, purpose and reason for exclusion. Removed files were moved to a quarantine folder beside the repository. None was hard-deleted, and the quarantine folder is outside the repository.

In the final audit the inventory, manifest, binary, licence, link and sensitive checks were run again on the copy as it now stands. The compiled report and presentation were read but not modified. Where a check found an inaccurate statement in the copy, the statement was corrected, and each correction is listed in section 6.

The master was only read: for the listing, for hashing and copying included files, and for the sanitisation and final checks. Nothing was written to it. A content scan of the whole master tree was started earlier but stopped because it was too slow to finish. The scan that replaced it covers only the included set, which is the content that could reach the repository. Detailed per-file records are kept in the review folder beside this repository, outside it.

## 2. Inventory

The counts below are the final recount. Groups A, C and D together account for every file in the master archive, and group B holds files written for this repository.

| Group | Files | Size | Notes |
|---|---|---|---|
| A. Public engineering and data files | 2,919 | 0.83 GB | Copied from the master and hash-verified. This is the publication set. |
| B. Audit, README and notice files | 6 | small text files | README.md, NOTICE.md, GITHUB_CONTENT_AUDIT.md, REPOSITORY_STRUCTURE.md, .gitignore, MANIFEST.csv. Written for this repository, not copied from the master. |
| C. Excluded files (not copied) | 2,755 | about 34.73 GB, plus one small file | 2,754 excluded by rule (sizes from the first audit), and ieee.csl excluded for licence reasons. |
| D. Quarantined duplicate files | 242 | 0.50 GB | Byte-identical copies moved out of the repository to a quarantine folder beside it. They are not in the repository. |
| Master archive (A + C + D) | 5,916 | 36.06 GB | Reconciles exactly: 2,919 + 2,755 + 242 = 5,916. |

Files in the repository: 2,925 (groups A and B, including MANIFEST.csv). The manifest, MANIFEST.csv, has 3,167 rows: 2,924 live rows, one for each file in the repository except MANIFEST.csv itself, and 243 removed rows (242 duplicate files and ieee.csl). Every live row matches a file on disk.

The ieee.csl file is in the quarantine folder, in a subfolder named excluded_from_public. The master copy is unchanged. It was excluded because its upstream licence (CC BY-SA 3.0) and its modified contributor metadata do not allow it to be redistributed here. Its upstream details are recorded in NOTICE.md.

Excluded files by reason (first audit; these 2,754 files are group C without ieee.csl):

| Reason | Files | Size |
|---|---|---|
| Aborted or killed solver runs, licence-probe outputs | 312 | 17.06 GB |
| Extension not on the allow-list (for example .rst, .dat, .r001, .h5, .out) | 2,008 | 8.14 GB |
| Solver binaries and scratch (d3plot, d3dump, nodout, eloutdet, disk files) | 218 | 5.36 GB |
| Text or data files over 10 MB | 148 | 4.18 GB |
| Administration folder, held for review | 23 | under 0.01 GB |
| Interview preparation folder | 29 | under 0.01 GB |
| Session outputs at the master root | 13 | under 0.01 GB |
| Root-level working notes, replaced by this repository's README | 3 | under 0.01 GB |

The administration, interview-preparation and session-output folders remain excluded.

Group A by folder in the repository (final counts; sizes from the first audit):

| Group in this repository | Source folders | Files | Size (first audit) |
|---|---|---|---|
| 01_Project_Documentation | 13_Report, 14_Presentation, 01_Requirements, 02_Engineering_Calculations, 03_CAD_Geometry | 265 | 0.04 GB |
| 02_CFD_Fluent | 05_Meshing, 06_Fluent_CFD, 09_Mesh_Independence | 398 | 0.05 GB |
| 03_Thermal_Structural_Mechanical | 07_Thermal_Analysis, 08_Structural_Analysis, 10_Parametric_Study | 1,996 | 0.67 GB |
| 04_LS_DYNA_Extension | 15_LS_DYNA_Extension | 235 | 0.07 GB |
| 05_Data | 11_Final_Audit (one file) | 1 | under 0.01 GB |
| 07_Audit_and_Provenance | 11_Final_Audit (remaining files) | 24 | under 0.01 GB |
| Total | | 2,919 | 0.83 GB |

## 3. Size, duplicates and large files

The included set started at 1.32 GB in the first audit, above the 1 GB target. Removing byte-identical duplicates brought it to 0.83 GB (0.826 GB for the final 2,919 files). That is below 1 GB under either the decimal or the binary definition.

A duplicate is a file whose SHA-256 hash matches another file in the repository. For each of the 402 duplicate groups, one copy was kept, normally the copy in the solver-output, export, mapping or model folder, and the others were moved to quarantine. In total 242 files were moved, 497.7 MB. Each one was checked against its kept copy: the hashes match, and the quarantined copy is the same as the kept copy byte for byte. The breakdown by kind is in REPOSITORY_STRUCTURE.md. The largest group is the Ansys Workbench project-folder mirrors (dp0), 151 files and 359.4 MB. Those mirrors belong to 29 Workbench project files in the master archive. Those project files are excluded, because their extension is not on the allow-list, so the mirrors are copies of solver output with no owning project in the repository. Smaller duplicates, 507 files totalling about 6.6 MB, were kept because they record per-run audit history.

No unique raw exports were removed. The cell-level and nodal CSV exports (404 CSV files, 0.52 GB) remain, because each is the only copy of its content. The earlier option of moving exports to a release archive is therefore not needed to reach the target.

The largest included file is 8.55 MB, a cell-level CFD export at 02_CFD_Fluent/Exports/cells_solid.csv. No included file approaches GitHub's 100 MB hard limit. Git LFS is not needed, and it has not been set up. The one file that would have needed LFS or exclusion, an 85 MB mesh file, is excluded.

## 4. Sensitive-information findings and actions (final scan)

The final scan read every file in the repository: text files as bytes and as UTF-16 where a byte-order mark is present, Office files through their XML parts, and PDFs and images as raw bytes. Counts are files and matches.

| Finding | Final scan result | Action in this repository |
|---|---|---|
| Local user-profile path (Windows profile prefix) | 0 | None needed. |
| Local account name | 0 | None needed. |
| Workstation host name (case-sensitive search) | 0 | None needed. The case-insensitive matches in the first pass were the author's first name, not the host name. |
| Desktop project path, and sandbox or container path prefixes | 0 | None needed. |
| Profile-folder environment variable | 1 file (02_CFD_Fluent/MESH_NOTES.md) | Kept. It is a variable name in a Fluent path note, not a path to a person's files. |
| UNC-like patterns | 34 files, 35 matches | False positives: escape sequences in LaTeX, Scheme and Fluent transcripts, and binary image data. Not changed. |
| E-mail addresses | 2 matches, both in binary PNG data | False positives. No third-party addresses remain. The citation style file's four addresses were removed before that file was excluded. |
| Keys, tokens, private keys, key formats (ghp_, AKIA, sk-, and similar) | 0 | None needed. |
| Credential keywords | 3 files, 6 matches: the word "Password" in two Workbench probe logs (Fluent launcher setting names such as CachePassword), and the word "password" in this audit | No secret values. Kept. |
| Private, local and cloud-share URLs | 0 | None needed. |
| Licence-server variable name (ANSYSLMD_LICENSE_FILE) | 5 files, 5 matches | Variable name only. No server address appears in any file. |
| Author's name and degree details | 16 files, 179 matches | Kept as authorship attribution, as instructed (section 5). |
| Company name (Eleation) | 36 files, 157 matches, including the report, the presentation and their Office XML | Kept, as instructed. Owner reports verbal permission from Eleation; no written record (section 5). |
| Vendor banners and copyright lines (ANSYS Student, Synopsys, LSTC, LS-DYNA) | 180 files, 778 matches | Generated solver output, kept unchanged. See section 5. |
| "reconstruct" (technical Fluent sense) | 46 files, 52 matches, excluding this audit document, which quotes the terms | Kept. See section 6. |
| References to master folder names, such as 06_Fluent_CFD/ | 503 files, 19,971 matches (pattern: a two-digit folder prefix followed by a name and a slash) | Intentional. See section 9. |

Corrections to earlier statements. The first audit recorded one third-party email address in the citation style file. The file in fact contains four addresses, in its author and contributor blocks, and all four have been removed before the file was excluded. The first verification also reported that no local user-profile path or account name remained in any file, including Office files. That was wrong for two text logs stored as UTF-16, which the byte-level check did not decode: 02_CFD_Fluent/Logs/postprocess_log.txt and 03_Thermal_Structural_Mechanical/Results/Data/post_9B2_stdout.txt. The final scan found them. They have now been sanitised (two and one replacements), and each was checked against its master file by applying the same substitutions. The sanitisation log records every changed file with its hash before and after.

Further corrections made in the final audit are listed in section 6.

## 5. Licence and proprietary-material concerns

No licence has been selected, and none should be selected until the following have been reviewed. The contents mix three kinds of material with different rights. Engineering scripts, reports and data prepared for this work belong to the owner. Outputs from Ansys (Mechanical and Fluent) and LS-DYNA were produced under student licences, and those licence terms may restrict publication or redistribution of outputs. Material connected with the internship host organisation, including its name and the internship documents that refer to it, may be subject to that organisation's confidentiality or publication terms.

Ansys and LS-DYNA outputs. The solver logs and exports contain vendor banners, which are kept as generated (NOTICE.md, section 3). The published Ansys student terms describe free student downloads as for educational use only, meaning self-learning, student instruction, student projects and student demonstrations. Whether those terms permit publishing solver outputs has not been confirmed. The repository therefore makes no claim that Ansys or LS-DYNA outputs are freely redistributable.

Eleation. The internship was carried out with Eleation from February to May 2025. Publication of the company name and the internship description needs Eleation's permission. That permission has not been confirmed. It is an external decision and is not treated as a licensing assumption.

Citation style file. The IEEE citation style file ieee.csl is excluded from the repository (NOTICE.md, section 2). Its upstream licence is Creative Commons Attribution-ShareAlike 3.0, and its upstream README asks that author and contributor listings be kept as they are when styles are redistributed. The copy first prepared for this repository had contributor e-mail addresses removed, so it is not redistributed here.

Material-property data. Material values are cited to a VDM Metals Alloy 718 data sheet (No. 4127), Special Metals and MatWeb. No datasheet text, MatWeb page or database export is reproduced. MatWeb's terms restrict redistribution of its database. The owner should confirm that the cited values may be published with their citations.

## 6. Provenance, wording and records (final audit)

The compiled report uses the terms Selected, Assumed, Calculated and Simulated for its values. Its declaration states that the original internship files were not retained and that the analysis was carried out after the internship. Earlier working files in the master archive labelled some values as reconstructed. In the public copy those labels were changed to re-analysed (and RECONSTRUCTION to RE-ANALYSIS), so that the copy does not describe the internship work as a reconstruction. The changes were made in three places.

Text files. Three wording passes changed 773 text files (761, 11 and 1 files). Each changed file was checked for its encoding, line count, JSON syntax and Python syntax against its master copy, and each change is recorded in the sanitisation log. Some JSON field names that contained the old wording were renamed to re_analysis names.

PARAMETERS.xlsx. The text passes skipped Office files, so five labels in the workbook's shared strings ("RECONSTRUCTION NOTICE", "Reconstructed/Assumed" and "Reconstructed selection") remained. In the final audit they were changed to the same re-analysis wording (five replacements in one XML part). The zip and the XML were checked after the change. As a result the workbook is no longer byte-identical to the master: the copy has SHA-256 021A8EA9..., and the master has F9859D45.... This is the only binary file changed by the final audit.

Dataset copy. The copy of MASTER_PROJECT_DATA.csv in 05_Data differs from the master in 22 cells: the header, and cells that read "reconstructed 2026, class B". Each difference was checked by applying the same label rules to the master cell and comparing the result with the copy. Every difference is explained by the label rules, and no numeric value differs.

Technical uses are kept. "Reconstruct" is also a Fluent term for node and gradient reconstruction and for the reconstruction of cell-centre mass flow. Those uses are kept. The final scan finds 52 occurrences in 46 files, all of this kind. They include three in the report DOCX (binary, unchanged), and three lowercase "reconstructed" in CFD audit notes that describe a mass flow reconstructed from cell centres. None of them describes the internship work as a reconstruction.

Date statements. The master archive's report edits removed "September 2026" from the cover and the declaration and substituted no other date. The compiled PDF therefore states no date. The copy still contains 2026 date statements in working documents and presentation text, for example ASSUMPTIONS.md ("every assumption below was made in 2026"), CAD_NOTES.md ("created from scratch in 2026"), BASELINE_PARAMETERS.md ("during the 2026 re-analysis") and the presentation's slide text ("regenerated in 2026"). These are not corrected here. The choice of date policy belongs to the owner (section 8, item 4), and the presentation may not be changed in this task.

Corrections made to the copy in the final audit:

- README.md and NOTICE.md said the analysis was carried out "again in 2026 ... as stated in the report's declaration". The declaration says it was carried out after the internship and gives no year. Both files now say "after the internship".
- REPORT_QC_CHECKLIST.md header: the phrase "re-analysis documented September 2026" was removed, and "RE-ANALYSIS 2026 ... 2026 re-analysed work" was aligned with the compiled report.
- REPORT_QC_CHECKLIST.md, section 1: the PDF row gave 50 pages and SHA-256 A62CC938...; the delivered PDF has 55 page breaks and SHA-256 57CF71DC.... The DOCX row gave 931F10EB...; the delivered DOCX is C38A55AB.... The master-dataset row gave the master hash without saying that the copy differs; both hashes are now stated. The QC result line now says it was recorded against an earlier build.
- The earlier statement that the QC checklist showed no personal names was withdrawn in the first pass. The compiled front matter does name the author, degree, university and organisation, as the instructions required. This was checked against the PDF text, not against the QC record.

## 7. Verification (final audit)

The checks below were run on the final state of the copy.

| Check | Result |
|---|---|
| Master archive unchanged: 5,916 files and 36.06 GB, none added or missing; sizes match the listing taken at the start of the audit; master ieee.csl SHA-256 begins B4C7619F and matches the record | Pass |
| Report PDF, report DOCX and presentation PPTX identical to master by SHA-256 (hashes begin 57CF71DC, C38A55AB and C9ED0C49) | Pass |
| PARAMETERS.xlsx differs from master by design (section 6): master F9859D45, copy 021A8EA9 | Expected difference, documented |
| Engineering files: 2,919 files in group A, each on disk and matching its MANIFEST.csv hash; 0 mismatches. No file on disk is missing from the manifest | Pass |
| Removed rows: 243 (242 duplicates and ieee.csl). All 242 quarantined duplicate files match removed-row hashes; 175 unique hashes. QUARANTINE_README.txt is excluded from the count | Pass |
| Stray files and cache files in the repository | Pass: none |
| Ignore rules: 56 rules in .gitignore checked against the included files | Pass: none conflict |
| README relative links: 14 targets | Pass: none broken |
| README numbers: 41 numeric tokens, each appearing in at least seven source files | Pass, as a presence check only. This is the weakest check in this table; it does not compare each README value with its source value |
| Dataset copy against master: 22 cells differ, all explained by the label rules | Pass, documented change |
| Sensitive-information scan (section 4) | Pass. Remaining matches are the author's name, the company name, vendor banners, solver terms, and false positives listed in section 4 |
| Compiled PDF front matter: author, degree, university and organisation are present, as the instructions required | Pass |
| QC checklist: hashes and page count | Corrected in this audit. The QC checks themselves must be re-run on the delivered files |

## 8. Decisions and open points for the owner

These points must be resolved before the copy can become PUBLIC-READY. Items 1 to 5 are blockers. Items 6 to 12 are decisions that can be made at the same time.

1. Eleation's permission to publish its name and the internship description. This is external. Obtain it, or remove the company name and the internship description from the public copy.
2. Solver outputs. Check the applicable Ansys Student terms and the LS-DYNA licence terms. Then decide whether outputs are published, or whether they are excluded.
3. Provenance wording. Review the re-analysis wording in the text files, in PARAMETERS.xlsx and in the 05_Data dataset copy (section 6). Reverting the wording would reintroduce "reconstructed" into the public copy, which conflicts with the stated requirement.
4. Date policy. Choose one: either no date, matching the compiled report, or 2026, applied everywhere. The 2026 statements are in ASSUMPTIONS.md, CAD_NOTES.md, BASELINE_PARAMETERS.md, REPORT_QC_CHECKLIST.md (section 6, "2026 project files"), the figure scripts, and the presentation text. Changing the presentation requires a separate task, because it is not to be modified here.
5. QC re-run. Re-run the QC checks against the delivered PDF, DOCX and PPTX. Until then, the QC PASS result applies to an earlier build only.
6. Author's name and degree details. These are kept as attribution, as instructed. Confirm that they may be public.
7. Citation style file. Either keep ieee.csl excluded and cite the upstream source by link, or include a version that keeps the upstream contributor metadata unchanged.
8. Cited material-property data. Confirm that the VDM Alloy 718 data sheet, Special Metals and MatWeb values may be published with their citations. MatWeb restricts redistribution of its database.
9. Excluded folders. The administration, interview-preparation and session-output folders stay excluded.
10. Workbench project files. The 29 .wbpj files are excluded. Decide whether a later release should include them.
11. Master-folder references. 503 included files refer to master folder names, such as 06_Fluent_CFD/. Decide whether to keep these references, with REPOSITORY_STRUCTURE.md as the mapping.
12. Quarantine folder. It holds the 242 removed duplicate files and the ieee.csl copy, outside the repository. It can be reviewed and removed by the owner. Nothing has been permanently deleted.

## 9. Known limitations

The sensitive scan read Office files through their XML parts, and text files in UTF-8 and UTF-16. PDF files and images were searched as raw bytes. Text inside compressed PDF streams is not reliably searchable, so the report PDF was checked for the identifiers above only as raw bytes, not exhaustively.

The e-mail, UNC-like and phone-number-like patterns are broad. They produce false positives in binary data and in numeric LS-DYNA and export data, as listed in section 4.

The README number check is a presence check (section 7). It does not compare each README value with its source value.

The upstream details of ieee.csl (title, version and updated date) were taken from a summarised web fetch. They were not compared byte for byte with the upstream file, which was not downloaded again for this audit.

Modification times of master files were not compared. Names, sizes and hashes were.

Some scripts refer to master folder names and to the removed duplicate paths. Each removed path has the same content at the kept path listed in MANIFEST.csv, so references can be changed to the kept path. The master-folder count in section 4 uses a folder-name pattern. It is an indicator, not an exact count of path references.

The size figures for excluded files come from the first audit and are carried forward.
