# -*- coding: utf-8 -*-
"""Section 9B-1 - C00 vs P00: compare the complete monitor history (29 reports x every iteration).
RE-ANALYSIS 2026. Writes CFD_Cases/C00_PIPELINE_CHECK/C00_monitor_history_comparison.json."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_case import monitors
R = sys.argv[1] if len(sys.argv) > 1 else r"<PROJECT_ROOT>"
h1, a = monitors(os.path.join(R, "06_Fluent_CFD", "Monitors", "baseline_monitors.out"))
h2, b = monitors(os.path.join(R, "10_Parametric_Study", "CFD_Cases", "C00_PIPELINE_CHECK", "Monitors",
                              "C00_PIPELINE_CHECK_monitors.out"))
res = {"header_identical": h1 == h2, "rows_P00": len(a), "rows_C00": len(b),
       "rows_bitwise_identical": sum(1 for ra, rb in zip(a, b) if ra == rb),
       "max_abs_difference_any_monitor_any_iteration": max(abs(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))}
print(json.dumps(res))
json.dump(res, open(os.path.join(R, "10_Parametric_Study", "CFD_Cases", "C00_PIPELINE_CHECK",
                                 "C00_monitor_history_comparison.json"), "w"), indent=2)
