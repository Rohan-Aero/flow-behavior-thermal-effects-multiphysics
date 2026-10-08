# 12C notes: scope change and run handling

## Scope change (2026-10-07, user instruction)

The final 12C study is a **three-point imperfection sensitivity study**:
- C1 = 0.1 mm;
- C3 = 0.6 mm;
- C5 = 1.2 mm.

It is not a full sweep. The completed C5 was kept and not rerun. C1 ran to normal completion and C3 ran after it.

**Not run:** C2 (0.3 mm), C4 (0.9 mm), N1 (0.1 mm with half step) and C0b (perfect geometry with NEGEV = 1, bifurcation
detection). Their decks stay in `runs/` with a `NOT_RUN.txt` file.

**C0 (perfect geometry, 0.0 mm)** had already finished (15:08–16:14) before the scope change. It is used only as the
reference path: F2, and the onset criterion "N 1 % below the perfect path". It is not one of the three sensitivity points.

**C0b** was prepared before the scope change and then withdrawn. It was meant to obtain the bifurcation load of the
perfect geometry, because C0 used the default NEGEV = 2, which R16.1 documents as "ignore negative eigenvalues".

## Run handling

- **Detached launch.** Long runs were launched through WMI so that they survive a dropped remote session (12B lesson).
- **Keep-awake.** The wrapper scripts hold a per-process "system required" request against idle sleep. No power setting
  was changed. A user-initiated restart (3 Oct, 21:34) cannot be prevented this way and ended C5 attempt 2.
- **Memory gate.** A run that starts with too little free memory factorises out of core: about 3–4× slower, with
  identical results. The wrappers wait up to 20 min for ≥ 7 GB free before launching each case.
- **Wrapper replacement.** At 16:48 the original wrapper was stopped without stopping the running C1 solver, and replaced
  by `chain3_C1_C3.ps1`. This wrapper:
  - waited for C1's EXIT line;
  - wrote C1's `done.txt`;
  - ran C3.
