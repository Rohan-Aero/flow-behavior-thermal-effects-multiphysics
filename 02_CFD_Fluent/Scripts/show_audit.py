import json, os
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "Mesh_Quality", "python_quality_audit.json")
d = json.load(open(p))
for lv in ("coarse", "medium", "fine"):
    s = d["levels"][lv]
    print("=== %s ===" % lv)
    for k in ("NC", "NR", "NRS", "NZ", "nodes", "cells", "fluid_cells", "solid_cells",
              "faces", "negative_cells", "vol_ratio", "oq_min", "oq_mean",
              "oq_frac_below_0p2", "skew_max", "skew_mean", "skew_frac_above_0p5",
              "skew_frac_above_0p8", "cells_above_skew_0p8", "ar_max", "ar_mean",
              "growth_fluid", "growth_solid", "infl_18_thickness_m",
              "infl_layers_within_1p56mm", "axial_cell_m"):
        print("   %-26s %s" % (k, s.get(k)))
    for k in ("oq_worst", "skew_worst", "ar_worst"):
        w = s.get(k, {})
        print("   %-26s value=%.5g  zone=%s  r=%.3f mm  z=%.2f mm  theta=%.1f deg"
              % (k, w.get("value", float('nan')), w.get("zone"), w.get("r_mm", float('nan')),
                 w.get("z_mm", float('nan')), w.get("theta_deg", float('nan'))))
    print("   interface", json.dumps(s["interface"]))
