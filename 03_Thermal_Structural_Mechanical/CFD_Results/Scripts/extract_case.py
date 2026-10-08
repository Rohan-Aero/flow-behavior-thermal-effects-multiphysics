# -*- coding: utf-8 -*-
"""Section 9B-1 - extract every CFD output of one solved case with the P00 (Section 5B) definitions.

RE-ANALYSIS 2026 - reads newly generated Fluent outputs; nothing here is a recovered value.
Used identically for P00 (06_Fluent_CFD) and for every 9B-1 case (10_Parametric_Study/CFD_Cases/<CASE>).

Definitions (10_Parametric_Study/Planning/OUTPUT_DEFINITIONS.md, unchanged from 5B):
  mdot         Fluent conservative mass-flux report, inlet and outlet
  dp           area-weighted static gauge pressure, inlet face minus outlet face (D-031)
  T_out        mass-weighted static temperature on the outlet face
  Q            total heat rate through heated_outer_wall (Fluent flux report); interface heat also reported
  T_max solid  maximum over the solid including its boundary facets = max facet value on heated_outer_wall /
               fluid_solid_interface; the solid cell-centre maximum (monitor T_solid_max) is also reported
  T_max fluid  fluid cell-centre maximum (monitor T_fluid_max); interface facet maximum = near-wall air
  wall T       area-weighted average and facet max/min on heated_outer_wall and fluid_solid_interface
  y+           facet min / area-weighted mean / facet max on fluid_solid_interface
  Re           G D / mu(T_bulk), G = mdot_in / Fluent inlet face area, D = 20 mm nominal, mu from the frozen
               Incropera A.4 table (the table used in Fluent), T_bulk mass-weighted (inlet or outlet)
  mass error   |mdot_in + mdot_out| / mdot_in (flux report)
  energy error |net boundary heat rate| / Q_heated_wall (flux report net over all thermal boundaries)
"""
import os, re, json

AIR_T = [250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0]
AIR_MU = [1.596e-5, 1.846e-5, 2.082e-5, 2.301e-5, 2.507e-5, 2.701e-5, 2.884e-5, 3.058e-5]
D_NOM = 0.020
NUM = re.compile(r"^\s*(\S+)\s+([-+]?[0-9.]+(?:[eE][-+]?\d+)?)\s*$")


def interp(x, xs, ys):
    if x < xs[0] or x > xs[-1]:
        raise ValueError("%.3f K outside the air table %.1f-%.1f K" % (x, xs[0], xs[-1]))
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i])


def mu_air(T):
    return interp(T, AIR_T, AIR_MU)


def report(path):
    """Fluent flux / surface-integral report -> {zone: value} (including 'Net' when present)"""
    out = {}
    with open(path, "r", errors="ignore") as fh:
        for l in fh:
            m = NUM.match(l)
            if m:
                out[m.group(1)] = float(m.group(2))
    return out


def monitors(path):
    hdr, rows = None, []
    with open(path, "r", errors="ignore") as fh:
        for l in fh:
            s = l.strip()
            if s.startswith('("Iteration"'):
                hdr = re.findall(r'"([^"]+)"', s)
                continue
            if hdr and re.match(r"^\d+\s", s):
                try:
                    rows.append([float(x) for x in s.split()])
                except ValueError:
                    pass
    return hdr, rows


def extract(case_dir, monitor_file):
    A = os.path.join(case_dir, "Audit")
    fm = report(os.path.join(A, "fluent_flux_mass.txt"))
    fh = report(os.path.join(A, "fluent_flux_heat.txt"))
    ar = report(os.path.join(A, "fluent_si_areas.txt"))
    pa = report(os.path.join(A, "fluent_si_p_area.txt"))
    tm = report(os.path.join(A, "fluent_si_T_mass.txt"))
    twmax = report(os.path.join(A, "fluent_si_Twall_max.txt"))
    twmin = report(os.path.join(A, "fluent_si_Twall_min.txt"))
    twa = report(os.path.join(A, "fluent_si_Twall_area.txt"))
    ypx = report(os.path.join(A, "fluent_si_yplus_max.txt"))
    ypn = report(os.path.join(A, "fluent_si_yplus_min.txt"))
    ypa = report(os.path.join(A, "fluent_si_yplus_area.txt"))
    qpa = report(os.path.join(A, "fluent_si_qpp_area.txt"))
    hdr, rows = monitors(os.path.join(case_dir, monitor_file))
    c = {n: i for i, n in enumerate(hdr)}
    last = rows[-1]
    mon = {n: last[c[n]] for n in hdr[1:]}

    mdot_in, mdot_out = fm["fluid_inlet"], fm["fluid_outlet"]
    q_wall = fh["heated_outer_wall"]
    G = mdot_in / ar["fluid_inlet"]
    T_in_b, T_out_b = tm["fluid_inlet"], tm["fluid_outlet"]
    r = dict(
        iterations=int(last[0]),
        mdot_in_kg_s=mdot_in, mdot_out_kg_s=mdot_out,
        mass_error=abs(mdot_in + mdot_out) / mdot_in,
        mass_error_monitor=abs(mon["mdot_in"] + mon["mdot_out"]) / mon["mdot_in"],
        energy_error_monitor=abs(mon["q_net_all"]) / mon["q_heated_wall"],
        dp_Pa=pa["fluid_inlet"] - pa["fluid_outlet"], p_out_area_Pa=pa["fluid_outlet"],
        T_in_bulk_K=T_in_b, T_out_K=T_out_b, dT_bulk_K=T_out_b - T_in_b,
        Q_heated_wall_W=q_wall, Q_interface_W=fh["fluid_solid_interface"],
        Q_fluid_inlet_W=fh["fluid_inlet"], Q_fluid_outlet_W=fh["fluid_outlet"],
        Q_solid_ends_W=fh["solid_inlet_end"] + fh["solid_outlet_end"],
        energy_net_W=fh["Net"], energy_error=abs(fh["Net"]) / q_wall,
        fluid_enthalpy_balance_error=abs(fh["fluid_outlet"] + fh["fluid_inlet"] + fh["fluid_solid_interface"]) / q_wall,
        A_inlet_m2=ar["fluid_inlet"], A_heated_m2=ar["heated_outer_wall"], A_interface_m2=ar["fluid_solid_interface"],
        qpp_heated_area_avg_W_m2=qpa["heated_outer_wall"], qpp_interface_area_avg_W_m2=qpa["fluid_solid_interface"],
        T_solid_max_K=max(twmax["heated_outer_wall"], twmax["fluid_solid_interface"]),
        T_outer_max_K=twmax["heated_outer_wall"], T_outer_min_K=twmin["heated_outer_wall"],
        T_outer_avg_K=twa["heated_outer_wall"],
        T_interface_max_K=twmax["fluid_solid_interface"], T_interface_min_K=twmin["fluid_solid_interface"],
        T_interface_avg_K=twa["fluid_solid_interface"],
        T_solid_cell_max_K=mon["T_solid_max"], T_solid_cell_min_K=mon["T_solid_min"],
        T_solid_mean_K=mon["T_solid_mean"],
        T_fluid_max_K=mon["T_fluid_max"], T_fluid_min_K=mon["T_fluid_min"],
        yplus_min=ypn["fluid_solid_interface"], yplus_mean=ypa["fluid_solid_interface"],
        yplus_max=ypx["fluid_solid_interface"],
        G_kg_m2s=G, Re_in=G * D_NOM / mu_air(T_in_b), Re_out=G * D_NOM / mu_air(T_out_b),
        F_wall_z_N=mon["F_wall_z"], v_out_max_m_s=mon["v_out_max"],
        monitor_last_row={n: mon[n] for n in mon},
    )
    # every monitored temperature over EVERY iteration (property-table check from raw data)
    ext = {}
    for n in ["T_fluid_max", "T_fluid_min", "T_wall_max", "T_out_bulk", "T_in_bulk", "T_solid_max", "T_solid_min",
              "T_outer_max", "T_outer_avg", "T_inner_avg"]:
        v = [row[c[n]] for row in rows]
        i_max = max(range(len(v)), key=lambda i: v[i])
        ext[n] = {"min": min(v), "max": max(v), "iteration_of_max": int(rows[i_max][0]), "final": v[-1]}
    r["temperature_history_extremes"] = ext
    return r


if __name__ == "__main__":
    import sys
    print(json.dumps(extract(sys.argv[1], sys.argv[2]), indent=2))
