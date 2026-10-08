# APDL_snippet_test (Section 7B, RE-ANALYSIS 2026)

A syntax test of `Workbench/Scripts/s7b_post_snippet.inp` on a **toy** model.

- **Model.** A hollow cylinder, ri 10 / ro 20 / L 60 mm, SOLID186, with an arbitrary made-up temperature field and LC2-type restraints. It was solved with MAPDL 2026 R1 Student.
- **Purpose.** To prove that every command of the post-processing snippet runs without error before it went into the real solves.
- **Result.** 0 errors.
- **What it found.**
  - FSUM needs element nodal forces, which Mechanical's OUTRES does not store, so FSUM was removed.
  - `*VGET` of stresses returns "undefined" at midside nodes. This later turned out to matter (F-041).

**The toy numbers are not project results and are not reported anywhere.**
