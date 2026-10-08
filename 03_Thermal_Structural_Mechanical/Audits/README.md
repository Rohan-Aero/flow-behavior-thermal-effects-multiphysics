# Audits (Section 7B, RE-ANALYSIS 2026)

| File / folder | Content |
|---|---|
| `presolve_audit_7B.json` | the 61 pre-solve gate checks (all PASS in run 2), run inside Mechanical before any solve |
| `Presolve_Inputs/` | LC1, LC2 and LC2P solver inputs written **before** any 7B change. Compared section by section with the 7A inputs (LC1, LC2) and with LC2 (LC2P) |
| `mech_solve_7B_log.txt`, `mech_solve_7B_summary.json` | Mechanical solve log; result-object maxima and minima, probes, messages, states, image list |
| `wb_solve_7B_log.txt`, `wb_solve_7B_driver.txt` | Workbench journal log (cell states after the solve: all Up to Date) |
| `pre7B_*`, `post7B_*` | SHA-256 records. The 7A project is content-identical before and after 7B; the 7B project files are recorded after the solve |
| `Gate_Run1_FAIL/` | run 1: the gate stopped the solve because the EBLOCK check also compared the SURF154 pressure elements. Nothing was solved. Log, JSON, inputs and the run-1 script are kept |
| `APDL_snippet_test/` | syntax test of the post snippet on a **toy** cylinder (not a project result) |
| `mech_zoom_images_7B_log*.txt`, `wb_zoom_images_7B_*` | read-only image runs (no save). Run 1: wrong camera attribute. Run 2: stale script copy. Run 3: images written |
