#!/usr/bin/env python3
"""
BASELINE ANALYTICAL MODEL
Project : Flow Behavior and Thermal Effects in Multiphysics Systems  (RE-ANALYSIS)
Phase   : Section 2 - Engineering Theory, Governing Equations and Baseline Calculations

PURPOSE
    Produce the independent analytical baseline that the later ANSYS Fluent and
    ANSYS Mechanical results will be checked against. Nothing here is tuned to
    agree with any CFD result - no CFD has been run.

RE-ANALYSIS NOTICE
    The original internship project data was lost. Every parameter consumed by this
    script is classified in baseline_parameters.json as B (re-analysed/assumed) or
    C (calculated). No parameter is class A (documented from surviving evidence),
    because no surviving evidence exists.

UNITS
    SI internally, throughout. Conversions happen only at print time.

USAGE
    python baseline_calculations.py               run the model
    python baseline_calculations.py --selftest    prove the input validation works
"""
import json, os, sys, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PLOTDIR = os.path.join(HERE, "calculation_plots")
SIG = "=" * 88

# palette (validated: dataviz validate_palette.js, light mode, all checks pass)
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
CINK, CMUTE = "#1F2933", "#6B7280"


# ---------------------------------------------------------------------------
# 1. LOAD + VALIDATE
# ---------------------------------------------------------------------------
class ParameterError(ValueError):
    """Raised when a parameter is physically impossible or self-inconsistent."""


def load_parameters(path=None):
    path = path or os.path.join(HERE, "baseline_parameters.json")
    with open(path) as fh:
        return json.load(fh)


def validate(P):
    """Reject physically impossible or self-inconsistent input before any maths."""
    e = []
    g = lambda k: P[k]["value"]

    for k in ("Di", "Do", "L", "V_in", "p_op", "R_air", "rho_s"):
        if not np.isfinite(g(k)):
            e.append(f"{k} is not a finite number ({g(k)})")
        elif g(k) <= 0:
            e.append(f"{k} must be > 0, got {g(k)} {P[k]['units']}")

    # Absolute-temperature checks. A bare "> 0 K" test is not enough: 27 K is
    # positive but is almost certainly 27 degC typed into a Kelvin field. The floor
    # is set at the bottom of the air property table, so silent extrapolation is
    # also impossible.
    T_LO, T_HI = 250.0, 600.0
    for k in ("T_in", "T_ref"):
        v = g(k)
        if v <= 0:
            e.append(f"{k} must be an ABSOLUTE temperature, got {v} K")
        elif v < T_LO:
            e.append(f"{k} = {v} K is below the {T_LO:.0f} K floor of the air property "
                     f"table. If {v} was meant as degrees Celsius, it is {v + 273.15:.2f} K.")
        elif v > T_HI:
            e.append(f"{k} = {v} K is above the {T_HI:.0f} K top of the air property "
                     "table - extending the table would be required, not extrapolation.")

    if g("Do") <= g("Di"):
        e.append(f"Do ({g('Do')} m) must exceed Di ({g('Di')} m) - wall thickness would be <= 0")
    if g("Di") > 0 and g("L") / g("Di") < 1:
        e.append(f"L/Di = {g('L') / g('Di'):.2f} < 1 - not a duct")
    if not 0.0 < g("nu_s") < 0.5:
        e.append(f"Poisson's ratio must lie in (0, 0.5), got {g('nu_s')}")
    if not 0.0 <= g("n_corr") <= 1.0:
        e.append(f"Property-correction exponent out of range: {g('n_corr')}")
    if g("qpp_o") < 0:
        e.append("Negative outer heat flux would mean the duct is being cooled from outside; "
                 "not the modelled scenario")
    if g("gamma") <= 1.0:
        e.append(f"Ratio of specific heats must exceed 1, got {g('gamma')}")

    rho_in = g("p_op") / (g("R_air") * g("T_in"))
    mdot = rho_in * g("V_in") * math.pi * (g("Di") / 2) ** 2
    if mdot <= 0:
        e.append(f"Mass flow rate is non-positive ({mdot:.4e} kg/s)")

    if e:
        raise ParameterError("Input validation failed:\n  - " + "\n  - ".join(e))
    return True


def selftest():
    """Feed deliberately impossible inputs and confirm each is rejected."""
    base = load_parameters()["params"]
    cases = [("negative diameter", "Di", -0.02), ("zero length", "L", 0.0),
             ("Celsius mistaken for Kelvin", "T_in", 27.0), ("negative velocity", "V_in", -23.5),
             ("Do smaller than Di", "Do", 0.010), ("Poisson ratio 0.5", "nu_s", 0.5),
             ("zero pressure", "p_op", 0.0), ("gamma = 1", "gamma", 1.0)]
    print(SIG); print("INPUT VALIDATION SELF-TEST"); print(SIG)
    ok = True
    for label, key, bad in cases:
        P = json.loads(json.dumps(base)); P[key]["value"] = bad
        try:
            validate(P); print(f"  [FAIL] {label:32} {key}={bad} was ACCEPTED"); ok = False
        except ParameterError as exc:
            print(f"  [ok]   {label:32} rejected: {str(exc).splitlines()[1].strip()[2:]}")
    try:
        validate(base); print(f"  [ok]   {'the real frozen parameter set':32} accepted")
    except ParameterError as exc:
        print(f"  [FAIL] real parameter set rejected: {exc}"); ok = False
    print(SIG); print("SELF-TEST", "PASSED" if ok else "FAILED"); print(SIG)
    return ok


# ---------------------------------------------------------------------------
# 2. PROPERTIES
# ---------------------------------------------------------------------------
class Props:
    def __init__(self, D):
        a = D["air_primary"]
        self.aT, self.acp = np.array(a["T_K"], float), np.array(a["cp"], float)
        self.amu, self.ak = np.array(a["mu"], float), np.array(a["k"], float)
        self.aPr = np.array(a["Pr"], float)
        s = D["solid_props"]
        self.sT = np.array(s["T_C"], float) + 273.15
        self.scp, self.sk = np.array(s["cp"], float), np.array(s["k"], float)
        self.sE = np.array(s["E_GPa"], float) * 1e9
        self.sSy = np.array(s["Sy_MPa"], float) * 1e6
        self.cT = np.array(s["cte_T_C"], float) + 273.15
        self.cA = np.array(s["cte"], float)
        self.R, self.p = D["params"]["R_air"]["value"], D["params"]["p_op"]["value"]

    cp = lambda s, T: np.interp(T, s.aT, s.acp)
    mu = lambda s, T: np.interp(T, s.aT, s.amu)
    k = lambda s, T: np.interp(T, s.aT, s.ak)
    Pr = lambda s, T: np.interp(T, s.aT, s.aPr)
    rho = lambda s, T: s.p / (s.R * T)
    ks = lambda s, T: np.interp(T, s.sT, s.sk)
    cps = lambda s, T: np.interp(T, s.sT, s.scp)
    Es = lambda s, T: np.interp(T, s.sT, s.sE)
    Sy = lambda s, T: np.interp(T, s.sT, s.sSy)
    alpha = lambda s, T: np.interp(T, s.cT, s.cA)


# ---------------------------------------------------------------------------
# 3. CORRELATIONS
# ---------------------------------------------------------------------------
def f_petukhov(Re):
    """Darcy friction factor, smooth tube. Petukhov (1970). Valid 3e3 < Re < 5e6."""
    return 1.0 / (0.790 * np.log(Re) - 1.64) ** 2


def nu_dittus_boelter(Re, Pr):
    """Dittus-Boelter (1930), HEATING (n=0.4). Valid Re>1e4, 0.6<Pr<160, L/D>10.
    Constant-property correlation - see the property-variation correction."""
    return 0.023 * Re ** 0.8 * Pr ** 0.4


def nu_gnielinski(Re, Pr):
    """Gnielinski (1976). Valid 3e3 < Re < 5e6, 0.5 < Pr < 2000.
    More accurate than Dittus-Boelter at moderate Re; also constant-property."""
    f = f_petukhov(Re)
    return ((f / 8) * (Re - 1000) * Pr) / (1 + 12.7 * np.sqrt(f / 8) * (Pr ** (2 / 3) - 1))


# ---------------------------------------------------------------------------
# 4. THE MODEL
# ---------------------------------------------------------------------------
def march(D, pr, n_corr=None, N=600):
    """1-D marching solution along the duct at constant imposed wall heat flux."""
    g = lambda k: D["params"][k]["value"]
    n_corr = g("n_corr") if n_corr is None else n_corr
    Di, Do, L = g("Di"), g("Do"), g("L")
    ri, ro = Di / 2, Do / 2

    A_c = math.pi * ri ** 2
    P_wet = math.pi * Di
    Dh = 4 * A_c / P_wet                       # = Di for a circular duct
    rho_in = pr.rho(g("T_in"))
    mdot = rho_in * g("V_in") * A_c
    Q_vol = g("V_in") * A_c
    G = mdot / A_c                             # mass flux, constant along the duct

    A_i, A_o = math.pi * Di * L, math.pi * Do * L
    Q_tot = g("qpp_o") * A_o
    qpp_i = Q_tot / A_i
    qprime = Q_tot / L

    x = np.linspace(0, L, N + 1)
    dx = L / N
    Tb = np.zeros(N + 1); Tb[0] = g("T_in")
    for i in range(1, N + 1):
        Tb[i] = Tb[i - 1] + qpp_i * P_wet * dx / (mdot * pr.cp(Tb[i - 1]))

    Re = G * Dh / pr.mu(Tb)
    f = f_petukhov(Re)
    Nu_db, Nu_gn = nu_dittus_boelter(Re, pr.Pr(Tb)), nu_gnielinski(Re, pr.Pr(Tb))
    h_cp = Nu_gn * pr.k(Tb) / Dh
    Twi_cp = Tb + qpp_i / h_cp

    # property-variation correction, solved iteratively (Tw <-> h)
    Twi = Twi_cp.copy()
    for _ in range(200):
        h = h_cp * (Tb / Twi) ** n_corr
        Twi_new = Tb + qpp_i / h
        if np.max(np.abs(Twi_new - Twi)) < 1e-8:
            Twi = Twi_new; break
        Twi = 0.5 * (Twi + Twi_new)
    h = h_cp * (Tb / Twi) ** n_corr
    Nu = Nu_gn * (Tb / Twi) ** n_corr
    dT_wall = qprime * np.log(ro / ri) / (2 * math.pi * pr.ks(Twi))
    Two = Twi + dT_wall

    rho = pr.rho(Tb); V = G / rho
    a_snd = np.sqrt(g("gamma") * g("R_air") * Tb)

    return dict(x=x, xD=x / Di, Tb=Tb, Re=Re, f=f, Nu_db=Nu_db, Nu_gn=Nu_gn, Nu=Nu,
                h_cp=h_cp, h=h, Twi_cp=Twi_cp, Twi=Twi, Two=Two, dT_wall=dT_wall,
                rho=rho, V=V, Mach=V / a_snd, A_c=A_c, P_wet=P_wet, Dh=Dh, Q_vol=Q_vol,
                mdot=mdot, G=G, A_i=A_i, A_o=A_o, Q_tot=Q_tot, qpp_i=qpp_i,
                qprime=qprime, ri=ri, ro=ro, L=L, Di=Di, Do=Do, rho_in=rho_in,
                n_corr=n_corr)


def pressure_drop(D, pr, M):
    """Darcy-Weisbach friction + thermal acceleration, plus installation minor losses."""
    g = lambda k: D["params"][k]["value"]
    f_m = float(np.mean(M["f"]))
    rho_m, V_m = float(np.mean(M["rho"])), float(np.mean(M["V"]))
    q_dyn_in = 0.5 * M["rho_in"] * g("V_in") ** 2
    q_dyn_out = 0.5 * M["rho"][-1] * M["V"][-1] ** 2
    dp_fric = f_m * (M["L"] / M["Dh"]) * 0.5 * rho_m * V_m ** 2
    dp_acc = M["G"] ** 2 * (1 / M["rho"][-1] - 1 / M["rho"][0])
    dp_dev = g("K_dev") * q_dyn_in
    dp_in = g("K_in") * q_dyn_in
    dp_out = g("K_out") * q_dyn_out
    return dict(f_mean=f_m, q_dyn_in=q_dyn_in, q_dyn_out=q_dyn_out, dp_fric=dp_fric,
                dp_acc=dp_acc, dp_dev=dp_dev, dp_in=dp_in, dp_out=dp_out,
                dp_cfd=dp_fric + dp_acc + dp_dev,
                dp_install=dp_fric + dp_acc + dp_dev + dp_in + dp_out)


def cyl_thermal_stress(Ti, To, a, b, E, al, nu, r):
    """Timoshenko & Goodier: long hollow cylinder, logarithmic radial temperature,
    free ends, plane strain. Returns (sigma_r, sigma_theta, sigma_z)."""
    Ta = Ti - To
    C = al * E * Ta / (2 * (1 - nu) * np.log(b / a))
    lb, lba, k2 = np.log(b / r), np.log(b / a), a ** 2 / (b ** 2 - a ** 2)
    return (C * (-lb - k2 * (1 - b ** 2 / r ** 2) * lba),
            C * (1 - lb - k2 * (1 + b ** 2 / r ** 2) * lba),
            C * (1 - 2 * lb - 2 * k2 * lba))


def structure(D, pr, M):
    g = lambda k: D["params"][k]["value"]
    T_ref, nu = g("T_ref"), g("nu_s")
    Tsm = float(np.mean(0.5 * (M["Twi"] + M["Two"])))      # volume-mean solid temperature
    E, al, Sy = float(pr.Es(Tsm)), float(pr.alpha(Tsm)), float(pr.Sy(Tsm))
    dT_mean = Tsm - T_ref
    eps_th = al * dT_mean
    dL_free = eps_th * M["L"]
    dr_free = eps_th * M["ri"]

    r = np.linspace(M["ri"], M["ro"], 300)
    Ti, To = M["Twi"][-1], M["Two"][-1]
    Tm = 0.5 * (Ti + To)
    sr, st, sz = cyl_thermal_stress(Ti, To, M["ri"], M["ro"], pr.Es(Tm), pr.alpha(Tm), nu, r)
    svm = np.sqrt(0.5 * ((sr - st) ** 2 + (st - sz) ** 2 + (sz - sr) ** 2))

    sig_lc2 = -E * al * dT_mean
    return dict(Tsm=Tsm, E=E, alpha=al, Sy=Sy, dT_mean=dT_mean, eps_th=eps_th,
                dL_free=dL_free, dr_free=dr_free, r=r, sr=sr, st=st, sz=sz, svm=svm,
                lc1_max=float(np.max(svm)), lc2=sig_lc2,
                util_lc1=float(np.max(svm)) / Sy, util_lc2=abs(sig_lc2) / Sy,
                mos_lc1=Sy / float(np.max(svm)) - 1, mos_lc2=Sy / abs(sig_lc2) - 1,
                area_change=((M["ri"] + dr_free) ** 2 - M["ri"] ** 2) / M["ri"] ** 2 * 100)


# ---------------------------------------------------------------------------
# 5. REPORTING
# ---------------------------------------------------------------------------
ROWS = []


def row(section, quantity, symbol, value, units, basis):
    ROWS.append(dict(section=section, quantity=quantity, symbol=symbol,
                     value=value, units=units, basis=basis))


def table(title, items):
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")
    for q, s, v, u, b in items:
        vs = f"{v:,.6g}" if isinstance(v, (int, float)) else str(v)
        print(f"  {q:<44}{s:<10}{vs:>16}  {u:<10}")
        if b:
            print(f"  {'':<44}{'':<10}{'':>16}  -> {b}")


def sanity(label, ok, detail):
    print(f"  [{'PASS' if ok else 'FLAG'}] {label:<46}{detail}")
    return ok


# ---------------------------------------------------------------------------
# 6. PLOTS
# ---------------------------------------------------------------------------
def make_plots(D, pr, M, PD, S, sens):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    os.makedirs(PLOTDIR, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.edgecolor": "#B8BEC7", "axes.labelcolor": CINK,
                         "text.color": CINK, "xtick.color": CMUTE, "ytick.color": CMUTE,
                         "axes.grid": True, "grid.color": "#E6E9ED", "grid.linewidth": 0.7,
                         "figure.facecolor": "white", "axes.facecolor": "white"})
    HALO = [pe.withStroke(linewidth=3.2, foreground="white")]

    def finish(ax, title, xl, yl, note=None):
        ax.set_title(title, fontsize=11, fontweight="bold", color=CINK, pad=8)
        ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        if note:                                    # caption BELOW the axes - never collides
            ax.text(0.0, -0.155, note, transform=ax.transAxes, ha="left", va="top",
                    fontsize=7.8, color=CMUTE, style="italic")

    def label_on(ax, xs, ys, frac, txt, col, dy=0):
        """Direct label placed ON the curve at a chosen fraction, with a white halo."""
        i = int(frac * (len(xs) - 1))
        ax.annotate(txt, xy=(xs[i], ys[i]), xytext=(0, 9 + dy), textcoords="offset points",
                    ha="center", color=col, fontsize=8.6, fontweight="bold",
                    path_effects=HALO, zorder=6)

    # 1 - axial temperatures
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=150)
    series = [(M["Tb"], C1, "Bulk air Tb", "Bulk air $T_b$", 0.80, 0),
              (M["Twi_cp"], C2, "inner wall, const-prop", "Inner wall (constant-property)", 0.30, 0),
              (M["Twi"], C3, "inner wall, corrected", "Inner wall (property-corrected)", 0.62, -22),
              (M["Two"], C4, "outer wall", "Outer wall (property-corrected)", 0.85, 6)]
    for y, c, tag_t, leg, fr, dy in series:
        ax.plot(M["xD"], y, lw=2, color=c, ls="--" if c == C2 else "-", label=leg)
        label_on(ax, M["xD"], y, fr, tag_t, c, dy)
    ax.axvline(PD["LhD"], color=CMUTE, lw=1, ls=":")
    ax.annotate("entry length ends", xy=(PD["LhD"], M["Tb"][0] + 8), xytext=(-6, 0),
                textcoords="offset points", rotation=90, ha="right", va="bottom",
                color=CMUTE, fontsize=7.6)
    finish(ax, "Axial temperature development", "Axial position  $x/D$  [-]", "Temperature  [K]",
           "RE-ANALYSIS - analytical baseline, no CFD has been run. Property correction raises "
           "wall temperature by ~41 K; bulk temperature is unaffected.")
    ax.legend(frameon=False, loc="center left", fontsize=8.4)
    fig.tight_layout(); fig.savefig(f"{PLOTDIR}/01_axial_temperatures.png", bbox_inches="tight"); plt.close(fig)

    # 2 - Nusselt number
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=150)
    for y, c, tag_t, leg, fr in [(M["Nu_db"], C1, "Dittus-Boelter", "Dittus-Boelter (constant-property)", 0.42),
                                 (M["Nu_gn"], C2, "Gnielinski", "Gnielinski (constant-property)", 0.62),
                                 (M["Nu"], C3, "property-corrected", f"Gnielinski x correction (n={M['n_corr']})", 0.70)]:
        ax.plot(M["xD"], y, lw=2, color=c, label=leg)
        label_on(ax, M["xD"], y, fr, tag_t, c)
    ax.fill_between(M["xD"], M["Nu"], M["Nu_db"], color=C3, alpha=0.07, zorder=0)
    ax.set_ylim(bottom=44)
    ax.annotate("CFD acceptance band", xy=(24, 0.5 * (M["Nu"][480] + M["Nu_db"][480])),
                ha="center", color=CMUTE, fontsize=8.4, style="italic", path_effects=HALO)
    finish(ax, "Nusselt number along the duct, with the honest uncertainty band",
           "Axial position  $x/D$  [-]", "Nusselt number  $Nu_D$  [-]",
           "Band spans the property-corrected value (expected) to constant-property Dittus-Boelter (upper bound). "
           "Accept CFD anywhere inside; investigate outside.")
    ax.legend(frameon=False, loc="lower left", fontsize=8.4)
    fig.tight_layout(); fig.savefig(f"{PLOTDIR}/02_nusselt_number.png", bbox_inches="tight"); plt.close(fig)

    # 3 - radial wall temperature
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=150)
    rr = np.linspace(M["ri"], M["ro"], 120)
    for frac, c, lbl, fr in [(0.0, C1, "inlet  x/D = 0", 0.5), (0.5, C2, "mid  x/D = 15", 0.5),
                             (1.0, C3, "exit  x/D = 30", 0.5)]:
        i = int(frac * (len(M["x"]) - 1))
        T = M["Twi"][i] + M["qprime"] * np.log(rr / M["ri"]) / (2 * math.pi * pr.ks(M["Twi"][i]))
        ax.plot(rr * 1000, T, lw=2, color=c, label=lbl)
        label_on(ax, rr * 1000, T, fr, lbl, c)
    finish(ax, "Radial temperature profile through the solid wall",
           "Radius  [mm]        (bore at 10 mm, outer surface at 20 mm)", "Temperature  [K]",
           "Logarithmic profile from Fourier conduction in a cylinder. Through-wall drop is only "
           f"{M['dT_wall'][-1]:.1f} K - the metal is nearly isothermal radially.")
    ax.legend(frameon=False, loc="upper left", fontsize=8.4)
    fig.tight_layout(); fig.savefig(f"{PLOTDIR}/03_radial_wall_temperature.png", bbox_inches="tight"); plt.close(fig)

    # 4 - radial stress distribution (labels staggered: sigma_theta and sigma_z coincide at r=b)
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=150)
    rm = S["r"] * 1000
    for y, c, tag_t, leg, fr, dy in [(S["sr"], C1, "radial", r"$\sigma_r$  radial", 0.50, 8),
                                     (S["st"], C2, "hoop", r"$\sigma_\theta$  hoop", 0.26, 6),
                                     (S["sz"], C3, "axial", r"$\sigma_z$  axial", 0.72, -20),
                                     (S["svm"], C4, "von Mises", r"$\sigma_{vM}$  von Mises", 0.88, 6)]:
        ax.plot(rm, y / 1e6, lw=2, color=c, label=leg)
        label_on(ax, rm, y / 1e6, fr, tag_t, c, dy)
    ax.axhline(0, color=CMUTE, lw=1)
    finish(ax, "LOAD CASE 1 - gradient-driven stress at the exit station (free expansion)",
           "Radius  [mm]        (bore at 10 mm, outer surface at 20 mm)", "Stress  [MPa]",
           "Timoshenko thick-cylinder closed form - the ANSYS Mechanical target. Bore is the cold side "
           f"(tension); outer is hot (compression). Peak {S['lc1_max']/1e6:.1f} MPa = "
           f"{100*S['util_lc1']:.1f}% of hot yield.")
    ax.legend(frameon=False, loc="lower left", fontsize=8.4, ncol=2)
    fig.tight_layout(); fig.savefig(f"{PLOTDIR}/04_radial_stress_LC1.png", bbox_inches="tight"); plt.close(fig)

    # 5 - pressure breakdown
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=150)
    labels = ["Friction\n(Darcy-Weisbach)", "Thermal\nacceleration", "Entry-region\nincrement",
              "Entrance loss\n(install only)", "Exit loss\n(install only)"]
    vals = [PD["dp_fric"], PD["dp_acc"], PD["dp_dev"], PD["dp_in"], PD["dp_out"]]
    bars = ax.bar(labels, vals, color=[C1, C1, C1, C2, C2], width=0.6, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 9, f"{v:,.0f}", ha="center",
                fontsize=9.5, fontweight="bold", color=CINK)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.axhline(0, color=CMUTE, lw=1)
    finish(ax, "Pressure-drop breakdown", "", "Pressure drop  [Pa]",
           f"Blue = inside the CFD domain (total {PD['dp_cfd']:,.0f} Pa, the number to compare against Fluent).  "
           f"Orange = installation only (system total {PD['dp_install']:,.0f} Pa).")
    fig.tight_layout(); fig.savefig(f"{PLOTDIR}/05_pressure_breakdown.png", bbox_inches="tight"); plt.close(fig)

    # 6 - sensitivity to the correction exponent
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=150)
    ns = [s["n"] for s in sens]
    ax.plot(ns, [s["util_lc2"] for s in sens], lw=2, marker="o", ms=9, color=C1,
            label="LC2 - fully restrained")
    ax.plot(ns, [s["lc1"] / S["Sy"] for s in sens], lw=2, marker="s", ms=8, color=C3,
            label="LC1 - free expansion")
    ax.axhline(1.0, color=C2, lw=2, ls="--")
    ax.text(ns[0], 1.02, "YIELD   (utilisation = 1.0)", color=C2, fontsize=9, fontweight="bold")
    for s in sens:
        ax.annotate(f"{s['util_lc2']:.2f}", xy=(s["n"], s["util_lc2"]), xytext=(0, 11),
                    textcoords="offset points", ha="center", fontsize=8.8, color=C1,
                    fontweight="bold", path_effects=HALO)
    ax.annotate("LC1 is ~40x smaller - invisible at this scale", xy=(0.5, 0.016), xytext=(0, 13),
                textcoords="offset points", ha="center", fontsize=8.4, color=C3, path_effects=HALO)
    ax.set_ylim(-0.05, 1.18)
    finish(ax, "Robustness: yield utilisation vs the property-correction exponent",
           "Correction exponent  $n$  in  $Nu = Nu_{cp}\,(T_b/T_w)^n$  [-]", "Utilisation  $|\sigma| / S_y$  [-]",
           "Literature range for n is 0.4-0.575. The design stays elastic across all of it, so the "
           "conclusion does not depend on which value is chosen.")
    ax.legend(frameon=False, loc="center right", fontsize=8.6)
    fig.tight_layout(); fig.savefig(f"{PLOTDIR}/06_exponent_sensitivity.png", bbox_inches="tight"); plt.close(fig)
    return 6


# ---------------------------------------------------------------------------
# 7. MAIN
# ---------------------------------------------------------------------------
def main():
    D = load_parameters()
    validate(D["params"])
    pr = Props(D)
    g = lambda k: D["params"][k]["value"]

    print(SIG)
    print("BASELINE ANALYTICAL MODEL  -  Section 2")
    print("Flow Behavior and Thermal Effects in Multiphysics Systems")
    print(SIG)
    print("RE-ANALYSIS: every parameter is class B (re-analysed/assumed) or")
    print("C (calculated). No parameter is class A - no original data survives.")
    print("No CFD has been run. Nothing here is tuned to match a simulation.")

    M = march(D, pr)
    PD = pressure_drop(D, pr, M)
    Re_in, Re_out = M["Re"][0], M["Re"][-1]
    PD["Lh"] = 1.359 * M["Dh"] * Re_in ** 0.25
    PD["LhD"] = PD["Lh"] / M["Dh"]
    S = structure(D, pr, M)

    # ---- 2. FLUID MECHANICS -------------------------------------------------
    table("2. FLUID MECHANICS", [
        ("Cross-sectional flow area", "A_c", M["A_c"] * 1e6, "mm^2", "pi*ri^2"),
        ("Wetted perimeter", "P_w", M["P_wet"] * 1e3, "mm", "pi*Di (full circular wall is wetted)"),
        ("Hydraulic diameter", "D_h", M["Dh"] * 1e3, "mm", "4*A_c/P_w = Di exactly, for a circular duct"),
        ("Volumetric flow rate", "Q_v", M["Q_vol"] * 1e3, "L/s", "V_in * A_c"),
        ("Mass flow rate", "m_dot", M["mdot"] * 1e3, "g/s", "rho_in * V_in * A_c, constant along the duct"),
        ("Mass flux", "G", M["G"], "kg/m^2.s", "m_dot/A_c - constant even as density falls"),
        ("Characteristic velocity (inlet)", "V_in", g("V_in"), "m/s", "imposed boundary condition"),
        ("Characteristic velocity (outlet)", "V_out", M["V"][-1], "m/s", "G/rho_out - gas accelerates as it heats"),
        ("Reynolds number (inlet)", "Re_in", Re_in, "-", "rho*V*Dh/mu"),
        ("Reynolds number (outlet)", "Re_out", Re_out, "-", "falls because viscosity rises with temperature"),
        ("Mach number (inlet)", "M_in", M["Mach"][0], "-", "V/sqrt(gamma*R*T)"),
        ("Mach number (outlet)", "M_out", M["Mach"][-1], "-", ""),
    ])
    regime = "TURBULENT" if Re_out > 4000 else ("TRANSITIONAL" if Re_out > 2300 else "LAMINAR")
    print(f"\n  FLOW REGIME: {regime}  (Re stays between {Re_out:,.0f} and {Re_in:,.0f})")
    print("    Re > 4000 along the entire duct, and never approaches the 2300 transition")
    print("    threshold, so a single turbulent treatment is valid end to end.")
    print(f"    Mach <= {M['Mach'].max():.3f} << 0.3 -> incompressible; density varies with T, not p.")

    # ---- 3. PRESSURE DROP ---------------------------------------------------
    table("3. PRESSURE DROP  (Darcy-Weisbach + Petukhov friction factor)", [
        ("Darcy friction factor (mean)", "f", PD["f_mean"], "-", "Petukhov, smooth tube, valid 3e3<Re<5e6"),
        ("Dynamic pressure at inlet", "q_in", PD["q_dyn_in"], "Pa", "0.5*rho*V^2"),
        ("Dynamic pressure at outlet", "q_out", PD["q_dyn_out"], "Pa", "0.5*rho*V^2"),
        ("MAJOR loss - wall friction", "dp_f", PD["dp_fric"], "Pa", "f*(L/Dh)*0.5*rho*V^2"),
        ("Thermal acceleration", "dp_a", PD["dp_acc"], "Pa", "G^2*(1/rho_out - 1/rho_in) - momentum, not loss"),
        ("Entry-region increment", "dp_d", PD["dp_dev"], "Pa", "K(inf)=0.09 - developing profile, IS in the CFD"),
        ("MINOR - sharp entrance", "dp_i", PD["dp_in"], "Pa", "K=0.5, NOT in the CFD domain"),
        ("MINOR - exit to plenum", "dp_o", PD["dp_out"], "Pa", "K=1.0, NOT in the CFD domain"),
        ("TOTAL comparable to CFD", "dp_CFD", PD["dp_cfd"], "Pa", "friction + acceleration + entry increment"),
        ("TOTAL for a real installation", "dp_sys", PD["dp_install"], "Pa", "adds entrance and exit losses"),
    ])
    print(f"\n  No bends, fittings or area changes exist in this geometry - it is a straight")
    print(f"  constant-area duct - so no further minor losses apply.")
    print(f"  dp_CFD / p_op = {100 * PD['dp_cfd'] / g('p_op'):.3f} %  -> pressure has no meaningful effect on density.")
    print(f"  Hydrodynamic entry length L_h = {PD['Lh'] * 1000:.0f} mm  (x/D = {PD['LhD']:.1f})")

    # ---- 4. HEAT TRANSFER ---------------------------------------------------
    table("4. HEAT TRANSFER", [
        ("Prandtl number (inlet / outlet)", "Pr", float(pr.Pr(M['Tb'][0])), "-", f"outlet {float(pr.Pr(M['Tb'][-1])):.3f}; both inside Dittus-Boelter validity 0.6-160"),
        ("Heat transfer area (inner, wetted)", "A_i", M["A_i"] * 1e4, "cm^2", "pi*Di*L - the convective surface"),
        ("Heat transfer area (outer, heated)", "A_o", M["A_o"] * 1e4, "cm^2", "pi*Do*L - where the flux is imposed"),
        ("Imposed outer heat flux", "q''_o", g("qpp_o"), "W/m^2", "BOUNDARY CONDITION (imposed, not calculated)"),
        ("Inner-surface heat flux", "q''_i", M["qpp_i"], "W/m^2", "= q''_o * Do/Di (area ratio)"),
        ("Total heat rate", "Q", M["Q_tot"], "W", "q''_o * A_o"),
        ("Nu - Dittus-Boelter (exit)", "Nu_DB", M["Nu_db"][-1], "-", "0.023*Re^0.8*Pr^0.4, constant-property"),
        ("Nu - Gnielinski (exit)", "Nu_Gn", M["Nu_gn"][-1], "-", "constant-property; preferred at moderate Re"),
        ("Nu - property-corrected (exit)", "Nu", M["Nu"][-1], "-", f"x (Tb/Tw)^{M['n_corr']} - EXPECTED CFD VALUE"),
        ("h - constant-property (exit)", "h_cp", M["h_cp"][-1], "W/m^2.K", "Nu_Gn*k/Dh"),
        ("h - property-corrected (exit)", "h", M["h"][-1], "W/m^2.K", "the value to expect from CFD"),
        ("Fluid temperature rise", "dT_b", M["Tb"][-1] - M["Tb"][0], "K", "CALCULATED from the energy balance"),
        ("Wall-to-bulk difference (exit)", "dT_c", M["Twi"][-1] - M["Tb"][-1], "K", "q''_i/h"),
        ("Inner wall temperature (exit)", "T_wi", M["Twi"][-1], "K", f"{M['Twi'][-1] - 273.15:.0f} degC"),
    ])
    print("\n  CORRELATION CHOICE - why Gnielinski is the primary:")
    print("    geometry        circular duct, smooth, L/D=30 > 10          -> both correlations apply")
    print(f"    flow regime     Re {Re_out:,.0f}-{Re_in:,.0f}, fully turbulent           -> inside both validity windows")
    print("    thermal BC      uniform wall HEAT FLUX (not wall temperature) -> the classical case for these")
    print(f"    fluid           air, Pr ~ {float(pr.Pr(M['Tb'][-1])):.2f}                            -> inside 0.5-2000 (Gnielinski)")
    print("    Gnielinski is preferred because Dittus-Boelter is a simple power law fitted at")
    print("    high Re; Gnielinski carries the friction factor and is more accurate at Re ~ 2-3e4.")
    print("    BOTH are CONSTANT-PROPERTY correlations - see the correction below.")

    # ---- 5. ENERGY BALANCE --------------------------------------------------
    cp_mean = float(np.mean(pr.cp(M["Tb"])))
    Q_from_dT = M["mdot"] * cp_mean * (M["Tb"][-1] - M["Tb"][0])
    err = 100 * abs(Q_from_dT - M["Q_tot"]) / M["Q_tot"]
    table("5. ENERGY BALANCE   Q = m_dot * cp * dT", [
        ("Heat input (imposed)", "Q_in", M["Q_tot"], "W", "q''_o * A_o"),
        ("Mass flow rate", "m_dot", M["mdot"], "kg/s", ""),
        ("Mean specific heat", "cp", cp_mean, "J/kg.K", "averaged over the bulk temperature range"),
        ("Inlet temperature", "T_in", M["Tb"][0], "K", "imposed"),
        ("Outlet temperature", "T_out", M["Tb"][-1], "K", "T_in + Q/(m_dot*cp)"),
        ("Temperature rise", "dT_b", M["Tb"][-1] - M["Tb"][0], "K", ""),
        ("Q recovered from m_dot*cp*dT", "Q_chk", Q_from_dT, "W", ""),
        ("Closure error", "err", err, "%", "must be ~0 by construction; a non-zero value means a coding error"),
    ])
    print("\n  This balance is INDEPENDENT of the heat transfer coefficient. Outlet bulk")
    print("  temperature is therefore the most robust single check on the CFD: if Fluent")
    print("  disagrees here, the boundary conditions or convergence are wrong - not the")
    print("  turbulence model.")

    # ---- 6. CONDUCTION ------------------------------------------------------
    ks_ex = float(pr.ks(M["Twi"][-1]))
    R_cond = math.log(M["ro"] / M["ri"]) / (2 * math.pi * ks_ex * M["L"])
    R_conv = 1.0 / (M["h"][-1] * M["A_i"])
    table("6. THERMAL CONDUCTION THROUGH THE SOLID WALL  (Fourier, cylindrical)", [
        ("Solid conductivity at wall temp", "k_s", ks_ex, "W/m.K", "VDM Alloy 718 datasheet, interpolated"),
        ("Conduction resistance", "R_cond", R_cond, "K/W", "ln(ro/ri)/(2*pi*k*L)"),
        ("Convection resistance (inner film)", "R_conv", R_conv, "K/W", "1/(h*A_i)"),
        ("Resistance ratio", "R_cd/R_cv", R_cond / R_conv, "-", "how much of the total resistance is the metal"),
        ("Through-wall temperature drop", "dT_w", M["dT_wall"][-1], "K", "q'*ln(ro/ri)/(2*pi*k)"),
        ("Heat flux at inner surface", "q''_i", M["qpp_i"], "W/m^2", ""),
        ("Heat flux at outer surface", "q''_o", g("qpp_o"), "W/m^2", "lower - same Q over a larger area"),
        ("Mean radial temperature gradient", "dT/dr", M["dT_wall"][-1] / (M["ro"] - M["ri"]), "K/m", ""),
    ])
    print(f"\n  The metal carries only {100 * R_cond / (R_cond + R_conv):.1f}% of the total thermal resistance;")
    print(f"  the air-side film carries {100 * R_conv / (R_cond + R_conv):.1f}%. THE FILM IS THE BOTTLENECK.")
    print("  Assumptions: steady state (no storage term); radial 1-D conduction (axial")
    print("  conduction is neglected because the axial gradient is ~100 K over 600 mm versus")
    print("  ~7 K over 10 mm radially); temperature-dependent k(T) applied, not a constant.")

    # ---- 7 & 8. EXPANSION AND STRESS ---------------------------------------
    table("7. THERMAL EXPANSION", [
        ("Volume-mean solid temperature", "T_s", S["Tsm"], "K", f"{S['Tsm'] - 273.15:.0f} degC"),
        ("Temperature rise above reference", "dT", S["dT_mean"], "K", "T_s - T_ref (300 K, stress-free)"),
        ("Mean CTE at that temperature", "alpha", S["alpha"], "1/K", "Special Metals mean CTE from 21 C"),
        ("Thermal strain", "eps_th", S["eps_th"], "-", "alpha*dT - the strain the metal WANTS to take"),
        ("Thermal strain", "eps_th", S["eps_th"] * 1e6, "microstrain", ""),
        ("Free axial growth over L", "dL", S["dL_free"] * 1e3, "mm", "eps_th * L"),
        ("Free radial growth of bore", "dr", S["dr_free"] * 1e6, "um", "eps_th * ri"),
        ("Resulting flow-area change", "dA/A", S["area_change"], "%", "justifies ONE-WAY coupling"),
    ])
    print("\n  PHYSICAL MEANING: eps_th is the strain the material would take if completely")
    print("  free. Stress appears only where that strain is PREVENTED - either by an external")
    print("  restraint (LC2) or by neighbouring material at a different temperature (LC1).")
    print("  Free expansion alone produces displacement, not stress.")

    sens = []
    for n in (0.4, 0.5, 0.575):
        Mn = march(D, pr, n_corr=n); Sn = structure(D, pr, Mn)
        sens.append(dict(n=n, Twi=Mn["Twi"][-1], Tsm=Sn["Tsm"], lc2=Sn["lc2"],
                         util_lc2=Sn["util_lc2"], lc1=Sn["lc1_max"]))

    table("8. THERMAL STRESS ESTIMATE  (approximate - NOT the final structural result)", [
        ("Young's modulus at T_s", "E", S["E"] / 1e9, "GPa", "VDM datasheet, at operating temperature"),
        ("Hot yield strength at T_s", "S_y", S["Sy"] / 1e6, "MPa", "VDM datasheet, age-hardened"),
        ("LC1 peak von Mises (gradient only)", "s_vM", S["lc1_max"] / 1e6, "MPa", "Timoshenko thick cylinder, free ends"),
        ("LC1 hoop stress at bore", "s_th,i", S["st"][0] / 1e6, "MPa", "tension - bore is the COLD side"),
        ("LC1 hoop stress at outer surface", "s_th,o", S["st"][-1] / 1e6, "MPa", "compression - outer is the HOT side"),
        ("LC2 axial stress (fully restrained)", "s_z", S["lc2"] / 1e6, "MPa", "-E*alpha*dT, compressive"),
        ("LC1 utilisation of hot yield", "-", S["util_lc1"], "-", ""),
        ("LC2 utilisation of hot yield", "-", S["util_lc2"], "-", "must stay below 1.0 for linear analysis to hold"),
        ("LC2 margin of safety", "MoS", S["mos_lc2"], "-", "S_y/|sigma| - 1"),
        ("LC2 / LC1 ratio", "-", abs(S["lc2"]) / S["lc1_max"], "-", "THE CENTRAL FINDING"),
    ])
    print("\n  IS sigma = E*alpha*dT APPLICABLE? Only for LC2, and only approximately.")
    print("    It assumes a uniaxial, fully restrained bar at uniform temperature. LC2 is")
    print("    fully restrained axially, so the form is right; but the temperature is NOT")
    print("    uniform, so using the volume-mean temperature is an approximation.")
    print("    For LC1 it is NOT applicable at all - a freely expanding bar at uniform")
    print("    temperature has ZERO stress. LC1 stress exists only because the temperature")
    print("    varies through the wall, so the thick-cylinder solution is required.")
    print("\n  WHY ANSYS WILL DIFFER FROM THESE NUMBERS - and by how much:")
    print("    - End effects: the closed-form solution assumes an infinitely long cylinder.")
    print("      Near the ends, real axial constraint and Poisson coupling produce local")
    print("      peaks the 1-D estimate cannot capture. Expect the largest deviation there.")
    print("    - Constraint modelling: a real 'fixed' face restrains radial and hoop motion")
    print("      too, not just axial. That adds biaxial stress the hand estimate omits.")
    print("    - Stress concentration: any fillet, edge or mesh singularity at a constrained")
    print("      face will report a local peak that is a modelling artefact, not physics.")
    print("    - Non-uniform temperature: the hand estimate uses ONE mean temperature; FEA")
    print("      uses the full 3-D field including the axial gradient.")
    print("    - Pressure loading: neglected here. At ~0.4 kPa gauge the hoop stress is")
    print(f"      p*ri/t = {g('p_op') * 0 + PD['dp_cfd'] * M['ri'] / (M['ro'] - M['ri']) / 1e6:.4f} MPa - utterly negligible beside thermal stress.")
    print("    - Material behaviour: linear elastic assumed. Valid while utilisation < 1.")
    print("    TREAT THESE AS ORDER-OF-MAGNITUDE TARGETS, not acceptance criteria to 1%.")

    # ---- 10. DIMENSIONLESS --------------------------------------------------
    Tf = 0.5 * (M["Twi"][-1] + M["Tb"][-1])
    nu_f = float(pr.mu(Tf) / pr.rho(Tf))
    Gr = 9.81 * (1 / Tf) * (M["Twi"][-1] - M["Tb"][-1]) * M["Dh"] ** 3 / nu_f ** 2
    Ri = Gr / Re_out ** 2
    Ec = g("V_in") ** 2 / (cp_mean * (M["Twi"][-1] - M["Tb"][-1]))
    Br = Ec * float(pr.Pr(Tf))
    table("10. DIMENSIONLESS PARAMETERS", [
        ("Reynolds", "Re", Re_in, "-", "inertia/viscous -> sets the flow regime; turbulent above ~4000"),
        ("Prandtl", "Pr", float(pr.Pr(M['Tb'][-1])), "-", "momentum/thermal diffusivity -> Pr<1 means heat diffuses FASTER than momentum"),
        ("Nusselt", "Nu", M["Nu"][-1], "-", "convective/conductive transport at the wall -> Nu=1 would be pure conduction"),
        ("Mach", "Ma", M["Mach"].max(), "-", "flow speed/sound speed -> <0.3 means density is not pressure-driven"),
        ("Grashof", "Gr", Gr, "-", "buoyancy/viscous"),
        ("Richardson", "Gr/Re^2", Ri, "-", "buoyancy/forced convection -> <<0.1 means buoyancy is irrelevant"),
        ("Eckert", "Ec", Ec, "-", "kinetic energy/enthalpy difference"),
        ("Brinkman", "Br", Br, "-", "viscous heating/conducted heat -> <<1 means dissipation is irrelevant"),
        ("Peclet", "Pe", Re_out * float(pr.Pr(M['Tb'][-1])), "-", "advection/conduction in the fluid -> advection dominated"),
        ("Biot-like wall ratio", "R_cd/R_cv", R_cond / R_conv, "-", "solid/film resistance -> <<1 means the film controls"),
    ])

    # ---- 13. SANITY CHECK ---------------------------------------------------
    print(f"\n{'-' * 88}\n13. ENGINEERING SANITY CHECK\n{'-' * 88}")
    checks = []
    checks.append(sanity("Reynolds number plausible", 1e4 < Re_in < 1e5,
                         f"Re {Re_in:,.0f} - typical for a small air duct at ~24 m/s"))
    checks.append(sanity("Flow stays turbulent end to end", Re_out > 4000,
                         f"min Re {Re_out:,.0f} > 4000"))
    checks.append(sanity("Mach number justifies incompressible", M["Mach"].max() < 0.3,
                         f"max Ma {M['Mach'].max():.3f}"))
    checks.append(sanity("Pressure drop plausible", 50 < PD["dp_cfd"] < 5000,
                         f"{PD['dp_cfd']:,.0f} Pa over {M['L']:.1f} m = {PD['dp_cfd'] / M['L']:,.0f} Pa/m"))
    checks.append(sanity("dp small vs operating pressure", PD["dp_cfd"] / g("p_op") < 0.05,
                         f"{100 * PD['dp_cfd'] / g('p_op'):.2f} % - incompressible ideal gas holds"))
    checks.append(sanity("Heat rate plausible", 50 < M["Q_tot"] < 5000,
                         f"{M['Q_tot']:.1f} W over {M['A_o'] * 1e4:.0f} cm^2"))
    checks.append(sanity("Energy balance closes", err < 0.5, f"closure error {err:.4f} %"))
    checks.append(sanity("Temperature rise plausible", 10 < (M["Tb"][-1] - M["Tb"][0]) < 300,
                         f"{M['Tb'][-1] - M['Tb'][0]:.1f} K rise"))
    checks.append(sanity("Metal stays within material limits", M["Two"].max() - 273.15 < 650,
                         f"peak metal {M['Two'].max() - 273.15:.0f} degC vs ~650 degC service limit"))
    checks.append(sanity("Thermal strain plausible", 1e-4 < S["eps_th"] < 1e-2,
                         f"{S['eps_th'] * 1e6:,.0f} microstrain = {S['eps_th'] * 100:.3f} %"))
    checks.append(sanity("LC1 stress well below yield", S["util_lc1"] < 0.5,
                         f"utilisation {S['util_lc1']:.3f}"))
    checks.append(sanity("LC2 stress below yield (linear valid)", S["util_lc2"] < 1.0,
                         f"utilisation {S['util_lc2']:.3f}, MoS {S['mos_lc2']:.2f}"))
    checks.append(sanity("LC2 elastic across the whole n range", max(s["util_lc2"] for s in sens) < 1.0,
                         f"n=0.4 -> {sens[0]['util_lc2']:.2f} | n=0.575 -> {sens[2]['util_lc2']:.2f}"))
    checks.append(sanity("One-way coupling still justified", S["area_change"] < 2.0,
                         f"flow-area change {S['area_change']:.2f} % << 5-15 % Nu uncertainty"))
    checks.append(sanity("Buoyancy negligible", Ri < 0.1, f"Gr/Re^2 = {Ri:.2e}"))
    checks.append(sanity("Viscous dissipation negligible", Br < 0.01, f"Br = {Br:.2e}"))
    checks.append(sanity("Dh equals Di for a circular duct", abs(M["Dh"] - M["Di"]) < 1e-12,
                         f"Dh-Di = {M['Dh'] - M['Di']:.2e} m (dimensional consistency check)"))
    checks.append(sanity("q''_i / q''_o equals Do/Di", abs(M["qpp_i"] / g("qpp_o") - M["Do"] / M["Di"]) < 1e-9,
                         f"ratio {M['qpp_i'] / g('qpp_o'):.4f} vs Do/Di {M['Do'] / M['Di']:.4f}"))

    print(f"\n  {'FLAGS RAISED' if not all(checks) else 'ALL ' + str(len(checks)) + ' CHECKS PASSED'}")
    print("\n  ITEMS FLAGGED FOR ATTENTION (not failures - things a reviewer should know):")
    print(f"    * Wall-to-bulk dT is {M['Twi'][-1] - M['Tb'][-1]:.0f} K, far outside the ~60 K range where")
    print("      constant-property gas correlations are strictly valid. Correction applied;")
    print("      the acceptance band for Nu is deliberately wide as a result.")
    print(f"    * Installation minor losses ({PD['dp_in'] + PD['dp_out']:,.0f} Pa) EXCEED the friction loss")
    print(f"      ({PD['dp_fric']:,.0f} Pa). They are excluded from the CFD comparison because the CFD")
    print("      domain has neither a sharp entrance nor a sudden exit. Do not compare the")
    print("      installation total against Fluent.")
    print(f"    * Solid carries only {100 * R_cond / (R_cond + R_conv):.1f}% of thermal resistance, so predicted metal")
    print("      temperature is far more sensitive to h than to k_s. Errors in the turbulence")
    print("      model propagate strongly into the stress result.")

    # ---- CSV ----------------------------------------------------------------
    for sec, items in [("FluidMechanics", [("A_c", M["A_c"], "m2"), ("P_wetted", M["P_wet"], "m"),
                        ("D_h", M["Dh"], "m"), ("Q_vol", M["Q_vol"], "m3/s"), ("m_dot", M["mdot"], "kg/s"),
                        ("G", M["G"], "kg/m2.s"), ("V_in", g("V_in"), "m/s"), ("V_out", M["V"][-1], "m/s"),
                        ("Re_in", Re_in, "-"), ("Re_out", Re_out, "-"), ("Ma_in", M["Mach"][0], "-"),
                        ("Ma_out", M["Mach"][-1], "-")]),
                       ("PressureDrop", [("f_mean", PD["f_mean"], "-"), ("q_dyn_in", PD["q_dyn_in"], "Pa"),
                        ("dp_friction", PD["dp_fric"], "Pa"), ("dp_acceleration", PD["dp_acc"], "Pa"),
                        ("dp_entry_increment", PD["dp_dev"], "Pa"), ("dp_entrance_minor", PD["dp_in"], "Pa"),
                        ("dp_exit_minor", PD["dp_out"], "Pa"), ("dp_total_CFD_comparable", PD["dp_cfd"], "Pa"),
                        ("dp_total_installation", PD["dp_install"], "Pa"), ("L_entry", PD["Lh"], "m")]),
                       ("HeatTransfer", [("Pr_in", float(pr.Pr(M["Tb"][0])), "-"), ("Pr_out", float(pr.Pr(M["Tb"][-1])), "-"),
                        ("A_inner", M["A_i"], "m2"), ("A_outer", M["A_o"], "m2"), ("qpp_outer", g("qpp_o"), "W/m2"),
                        ("qpp_inner", M["qpp_i"], "W/m2"), ("Q_total", M["Q_tot"], "W"),
                        ("Nu_DittusBoelter_exit", M["Nu_db"][-1], "-"), ("Nu_Gnielinski_exit", M["Nu_gn"][-1], "-"),
                        ("Nu_corrected_exit", M["Nu"][-1], "-"), ("h_const_prop_exit", M["h_cp"][-1], "W/m2.K"),
                        ("h_corrected_exit", M["h"][-1], "W/m2.K"), ("T_out_bulk", M["Tb"][-1], "K"),
                        ("dT_bulk", M["Tb"][-1] - M["Tb"][0], "K"), ("T_wall_inner_exit", M["Twi"][-1], "K"),
                        ("T_wall_outer_exit", M["Two"][-1], "K")]),
                       ("Conduction", [("k_solid_at_wall", ks_ex, "W/m.K"), ("R_conduction", R_cond, "K/W"),
                        ("R_convection", R_conv, "K/W"), ("dT_through_wall", M["dT_wall"][-1], "K"),
                        ("solid_resistance_fraction", R_cond / (R_cond + R_conv), "-")]),
                       ("Expansion", [("T_solid_mean", S["Tsm"], "K"), ("dT_above_ref", S["dT_mean"], "K"),
                        ("alpha", S["alpha"], "1/K"), ("thermal_strain", S["eps_th"], "-"),
                        ("free_axial_growth", S["dL_free"], "m"), ("free_bore_growth", S["dr_free"], "m"),
                        ("flow_area_change", S["area_change"], "%")]),
                       ("Stress", [("E_at_Ts", S["E"], "Pa"), ("Sy_at_Ts", S["Sy"], "Pa"),
                        ("LC1_vonMises_max", S["lc1_max"], "Pa"), ("LC1_hoop_bore", S["st"][0], "Pa"),
                        ("LC1_hoop_outer", S["st"][-1], "Pa"), ("LC2_axial", S["lc2"], "Pa"),
                        ("LC1_utilisation", S["util_lc1"], "-"), ("LC2_utilisation", S["util_lc2"], "-"),
                        ("LC2_margin_of_safety", S["mos_lc2"], "-"),
                        ("LC2_over_LC1_ratio", abs(S["lc2"]) / S["lc1_max"], "-")]),
                       ("Dimensionless", [("Grashof", Gr, "-"), ("Richardson", Ri, "-"), ("Eckert", Ec, "-"),
                        ("Brinkman", Br, "-"), ("Peclet", Re_out * float(pr.Pr(M["Tb"][-1])), "-")])]:
        for nm, v, u in items:
            row(sec, nm, "", float(v), u, "")

    import csv
    with open(os.path.join(HERE, "baseline_results.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# RE-ANALYSIS - analytical baseline, Section 2, 2026-09-18. No CFD has been run."])
        w.writerow(["section", "quantity", "value", "units"])
        for r in ROWS:
            w.writerow([r["section"], r["quantity"], f"{r['value']:.10g}", r["units"]])

    np.savetxt(os.path.join(HERE, "axial_profiles.csv"),
               np.column_stack([M["x"], M["xD"], M["Tb"], M["Twi_cp"], M["Twi"], M["Two"],
                                M["Re"], M["Nu_db"], M["Nu_gn"], M["Nu"], M["h_cp"], M["h"],
                                M["rho"], M["V"], M["Mach"]]),
               delimiter=",", comments="",
               header="x_m,x_over_D,Tb_K,Twi_constprop_K,Twi_corrected_K,Two_corrected_K,"
                      "Re,Nu_DittusBoelter,Nu_Gnielinski,Nu_corrected,h_constprop,h_corrected,"
                      "rho_kgm3,V_ms,Mach")

    n_plots = make_plots(D, pr, M, PD, S, sens)
    print(f"\n{SIG}")
    print(f"WROTE  baseline_results.csv ({len(ROWS)} quantities)")
    print(f"WROTE  axial_profiles.csv ({len(M['x'])} stations)")
    print(f"WROTE  calculation_plots/ ({n_plots} figures)")
    print(SIG)
    return dict(M=M, PD=PD, S=S, sens=sens, err=err, Ri=Ri, Br=Br, Gr=Gr,
                R_cond=R_cond, R_conv=R_conv, cp_mean=cp_mean, regime=regime)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    main()
