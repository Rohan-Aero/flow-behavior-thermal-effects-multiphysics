# Section 12B — Gate 0 (installation) and Gate 1 (Student size limit): evidence

> **Method.** Executable banners, licence messages and solver output from runs on device `HOST`, 2026-10-02. Capabilities
> were not inferred from Workbench add-ins.
>
> **Where the runs live.** Test decks and solver outputs are in `work_12B/G0_install/` and `work_12B/G1_sizelimit/`. The
> runner is `work_12B/run_lsdyna.cmd`.
>
> **Scope.** Every model in this file is a synthetic test (one cube, one bar, unit blocks). None is project geometry or a
> project result.

## Gate 0 — installed LS-DYNA

| # | Question | Evidence | Answer |
|---|---|---|---|
| 1 | Exact version | Solver banner: `Version : smp d R16`, `Revision: R16.1-180-gd50332dbe5`, build date 07/09/2025, `AnLicVer: 2026 R1 (20251230+dl-79-g6933d52)`. Product registered as **"LS-DYNA Suite R16.1 Student"**, DisplayVersion 25.2.1, publisher Ansys, installed 20261002 | **LS-DYNA R16.1 (R16.1-180-gd50332dbe5), Student suite** |
| 2 | Executable path(s) | `C:\Program Files\LS-DYNA Suite R16.1 Student\lsdyna\ls-dyna_smp_d_R16.1_180-gd50332dbe5_winx64_ifort190_sse2_studentversion.exe` (272,936,448 B; SHA-256 `75230A8B…1DAB`). Also present: `ls-dyna_smp_d_R14.1.1s_1-gef50e1efb1_winx64_ifort190.exe` (279,986,176 B; `8B4600A2…1247`). The installer's registry entry (`HKCU\Software\ANSYS, Inc.\LS-DYNA Suite R16.1 Student\lsdyna_path`) points to the **R16.1 student executable** | R16.1 student executable used for all 12B runs |
| 3 | SMP / MPP | Only `ls-dyna_smp_*` files; banner "Shared Memory Parallel" | **SMP only**; no MPP executable |
| 4 | Single / double precision | File names contain `_d_`; banner `Precision : Double precision (I8R8)` | **Double precision only**; no single-precision executable |
| 5 | Executable for implicit | The double-precision SMP R16.1 student executable | same as #2 |
| 6 | Launch from command line | `exe i=<deck> ncpu=<n> memory=<m>` runs to `N o r m a l  t e r m i n a t i o n`. It needs `LSTC_LICENSE=ansys`, the value the installer wrote at machine level. Without it in the process environment: *"Local license: Error Environment variable LSTC_FILE not set! … Error 70022"* | **Yes** (with `LSTC_LICENSE=ansys`) |
| 7 | LS-PrePost | `lspp\lsprepost4.12.exe`, file version 4.12.0.1. Batch launch (`-nographics c=…`) printed *"LS-PrePost(R) 2025 R1 (v4.12.6) - 14May2025"* and read the G0 `d3plot` (*"Total number of states = 2"*). The interactive GUI was not opened | **Installed and launches** (batch mode verified) |
| 8 | Student licence recognised | Every run prints *"Student license active; 331 days remaning."* and *"Executing with ANSYS license"* (option *"check ansys licenses only"*) | **Yes** |
| 9 | Authorised under the Student installation | Executable name `…_studentversion.exe`; registered by the Student installer; Student licence active; Student element limit enforced (Gate 1) | **Yes.** The R14.1.1s executable also runs on the Student licence (330 days), but it is not the registered solver and is not used |
| 10 | Implicit available | One-element implicit linear static test: `BEGIN implicit statics`, normal termination. Result equals the hand solution exactly: top u_z = −5.000 × 10⁻⁴ m, lateral 1.500 × 10⁻⁴ m. Nonlinear implicit (NSOLVR 12) and `*CONTROL_IMPLICIT_BUCKLE` (*"BEGIN buckling analysis … solving buckling eigenproblem"*, `eigout` written) also ran (Gates 2 and 6) | **Yes** |
| 11 | Double precision available and licensed | Banner I8R8; runs under the Student licence | **Yes** |
| 12 | Explicit-only restriction | None reported. Implicit static, nonlinear and buckling runs completed | **No restriction found** |

**Licence warning (non-blocking).** Each run first prints:

> *"[license/error] … Your version of the Ansys license client software is out of date … The version of the license
> client <port>@HOST [Ansys Release 2025 R2] must be greater or equal to the client LSDYNA version [Ansys Release 2026 R1]."*

The solver then continues on the Student licence. No run was stopped by it.

**Memory setting (affects run time, not results).**

- With `memory=500m` the benchmark factorisation ran out of core and took 2,423 s.
- With `memory=20m` the same factorisation finished in about 20 s.
- The solver's own advice is *"Memory Management for Implicit has changed after R10 … use memory= 3M"*.
- All gate runs use `memory=20m`.
- On the full mesh, a static run without buckling factorises **in core**: G5 took about 17 s per step and 703 s for
  40 steps.
- Adding `*CONTROL_IMPLICIT_BUCKLE` makes the solver choose an **out-of-core** solution for every step (*"an
  OUT-OF-CORE solution will be performed"*). That takes about 2–4.5 min per step, because the 15.7 GB machine leaves
  about 2–5 GB free. G6 with 10 steps took 45 min.
- A static run started before the previous solver had released its memory also went out of core: G5b attempt 2 took
  about 80 s per step. Started on free memory, G5b took about 40 s per step with 3 iterations.
- Results are unaffected; run time is not.

**Launch note.** A solver started as a child of the remote shell is ended when that session drops. G6 run 1 was
ended this way at step 3 (exit code 0x40010004, kept in `work_12B/G6_buckle/run1_killed_at_step3_session_disconnect/`).
Long runs are therefore launched detached through WMI (`Win32_Process.Create`).

## Gate 1 — enforced Student model-size limit

**Test models.** Synthetic free blocks with controlled counts, explicit, terminated after 2 cycles
(`work_12B/G1_sizelimit/make_probes.py`, `run_probes.cmd`):

| Probe | Nodes | Elements | Nodes + elements | Solver result |
|---|---|---|---|---|
| P1 (hex) | 127,500 | 120,050 | 247,550 | normal termination |
| P2 (hex) | 128,502 | 120,640 | 249,142 | normal termination |
| P3 (hex) | **131,502** | 123,000 | 254,502 | normal termination |
| P4 (tetra) | 29,640 | **128,520** | 158,160 | **`*** Error 70043 … Number of elements( 128520) exceeds limit 128000`**, error termination |
| P5 (tetra) | 29,808 | **131,495** | 161,303 | **`Number of elements( 131495) exceeds limit 128000`**, error termination |

**What this establishes.**

- The installed Student solver checks the **element count, limit 128,000**.
- A node count of 131,502 was accepted, so no node limit applies at or below that value.
- The combined count (up to 254,502) is **not** checked.

**The real model.**

- The converted LC2 model has 108,252 nodes and **23,400 elements** (combined 131,652).
- It was accepted and solved without any limit message (G2 benchmarks, G5, G5b and G6 on the full mesh).
- **No reduced model is needed.**

**Gate 0: PASS. Gate 1: PASS.**
