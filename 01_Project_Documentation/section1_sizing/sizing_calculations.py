"""
SECTION 1 SIZING CALCULATIONS
Project : Flow Behavior and Thermal Effects in Multiphysics Systems (RE-ANALYSIS)
Purpose : Derive and justify every design parameter BEFORE any CAD/mesh/CFD work,
          so that CFD results later have an independent baseline to be checked against.

RE-ANALYSIS NOTICE: all parameters here are newly selected in 2026. They are NOT
the original internship values, which were lost. Nothing here is measured data.

Property data source: Incropera & DeWitt, Fundamentals of Heat and Mass Transfer,
Table A.4 (air at 1 atm). Inconel 718: Special Metals alloy datasheet (typical values).
"""
import numpy as np

# ----------------------------------------------------------------------------
# AIR PROPERTIES AT 1 atm  (Incropera Table A.4)
# ----------------------------------------------------------------------------
T_TAB  = np.array([250., 300., 350., 400., 450., 500., 550., 600.])
CP_TAB = np.array([1006., 1007., 1009., 1014., 1021., 1030., 1040., 1051.])
MU_TAB = np.array([1.596, 1.846, 2.082, 2.301, 2.507, 2.701, 2.884, 3.058]) * 1e-5
K_TAB  = np.array([0.02227, 0.02624, 0.03003, 0.03365, 0.03707, 0.04038, 0.04360, 0.04659])
R_AIR  = 287.058
P_OP   = 101325.0
GAMMA  = 1.4

cp = lambda T: np.interp(T, T_TAB, CP_TAB)
mu = lambda T: np.interp(T, T_TAB, MU_TAB)
kf = lambda T: np.interp(T, T_TAB, K_TAB)
rho = lambda T: P_OP / (R_AIR * T)
Pr = lambda T: mu(T) * cp(T) / kf(T)

# ----------------------------------------------------------------------------
# INCONEL 718 (solid wall)  - Special Metals datasheet, typical values
# ----------------------------------------------------------------------------
TS_C   = np.array([21., 93., 205., 315., 425., 540.])          # degC
KS_TAB = np.array([11.4, 12.5, 14.0, 15.5, 17.0, 18.3])        # W/m-K
ES_TAB = np.array([200., 197., 192., 187., 183., 176.]) * 1e9  # Pa
AL_TAB = np.array([13.0, 13.0, 13.5, 14.1, 14.4, 14.8]) * 1e-6 # mean CTE from 21degC, 1/K
NU_S, RHO_S, CP_S = 0.294, 8190.0, 435.0
SY_RT, SY_540 = 1100e6, 1020e6

ks_f = lambda Tk: np.interp(Tk - 273.15, TS_C, KS_TAB)
Es_f = lambda Tk: np.interp(Tk - 273.15, TS_C, ES_TAB)
al_f = lambda Tk: np.interp(Tk - 273.15, TS_C, AL_TAB)
sy_f = lambda Tk: np.interp(Tk - 273.15, [21., 540.], [SY_RT, SY_540])

# ----------------------------------------------------------------------------
# SELECTED GEOMETRY AND OPERATING POINT   [RE-ANALYSED / ASSUMED]
# ----------------------------------------------------------------------------
Di, Do, L = 0.020, 0.040, 0.600
ri, ro = Di / 2, Do / 2
T_in, V_in = 300.0, 23.5
QPP_OUT = 8000.0           # W/m^2 uniform flux on OUTER cylindrical surface
T_REF = 300.0              # stress-free reference temperature

A_c = np.pi * ri**2
A_i = np.pi * Di * L
A_o = np.pi * Do * L
mdot = rho(T_in) * V_in * A_c
Re_in = rho(T_in) * V_in * Di / mu(T_in)
Q_tot = QPP_OUT * A_o
QPP_IN = Q_tot / A_i
qprime = Q_tot / L

print("=" * 78)
print("SECTION 1 SIZING CALCULATIONS  -  RE-ANALYSED PARAMETERS (not originals)")
print("=" * 78)
print("\n--- GEOMETRY ---")
print(f"  Inner diameter  Di   = {Di*1000:.1f} mm")
print(f"  Outer diameter  Do   = {Do*1000:.1f} mm   (Do/Di = {Do/Di:.1f}, wall t = {(ro-ri)*1000:.1f} mm)")
print(f"  Heated length   L    = {L*1000:.1f} mm   (L/Di = {L/Di:.1f})")
print(f"  Flow area       Ac   = {A_c*1e6:.2f} mm^2")

print("\n--- INLET / FLOW ---")
print(f"  Inlet temperature    = {T_in:.1f} K")
print(f"  Inlet velocity       = {V_in:.2f} m/s")
print(f"  Inlet density        = {rho(T_in):.4f} kg/m3")
print(f"  Mass flow rate       = {mdot*1000:.3f} g/s")
print(f"  Reynolds (inlet)     = {Re_in:,.0f}   -> TURBULENT (Re > 4000)")
a_snd = np.sqrt(GAMMA * R_AIR * T_in)
print(f"  Mach (inlet)         = {V_in/a_snd:.4f}  -> incompressible regime (M < 0.3)")

print("\n--- THERMAL LOAD ---")
print(f"  q'' on outer surface = {QPP_OUT:,.0f} W/m2")
print(f"  Outer area           = {A_o*1e4:.1f} cm2")
print(f"  Total heat input Q   = {Q_tot:.1f} W")
print(f"  q'' at inner surface = {QPP_IN:,.0f} W/m2   (= q''_o * Do/Di)")
print(f"  Linear heat rate q'  = {qprime:.1f} W/m")

# ----------------------------------------------------------------------------
# 1-D MARCH ALONG THE DUCT  (constant q'', local properties)
# ----------------------------------------------------------------------------
N = 600
x = np.linspace(0, L, N + 1)
dx = L / N
Tb = np.zeros(N + 1); Tb[0] = T_in
Twi = np.zeros(N + 1); Two = np.zeros(N + 1)
h_l = np.zeros(N + 1); Nu_g = np.zeros(N + 1); Nu_db = np.zeros(N + 1)
Re_l = np.zeros(N + 1); f_l = np.zeros(N + 1)
G = mdot / A_c

def local(Tbulk):
    Re = G * Di / mu(Tbulk)
    P = Pr(Tbulk)
    f = (0.790 * np.log(Re) - 1.64) ** -2
    nu_g = ((f / 8) * (Re - 1000) * P) / (1 + 12.7 * np.sqrt(f / 8) * (P ** (2 / 3) - 1))
    nu_db = 0.023 * Re ** 0.8 * P ** 0.4
    return Re, f, nu_g, nu_db, nu_g * kf(Tbulk) / Di

for i in range(N + 1):
    if i > 0:
        Tb[i] = Tb[i - 1] + QPP_IN * np.pi * Di * dx / (mdot * cp(Tb[i - 1]))
    Re_l[i], f_l[i], Nu_g[i], Nu_db[i], h_l[i] = local(Tb[i])
    Twi[i] = Tb[i] + QPP_IN / h_l[i]
    Two[i] = Twi[i] + qprime * np.log(ro / ri) / (2 * np.pi * ks_f(Twi[i]))

print("\n--- 1-D ENERGY MARCH (Gnielinski h, local properties) ---")
print(f"  Bulk T   : {Tb[0]:.1f} K  ->  {Tb[-1]:.1f} K    (rise {Tb[-1]-Tb[0]:.1f} K)")
print(f"  Re       : {Re_l[0]:,.0f}  ->  {Re_l[-1]:,.0f}   (drops as mu rises; stays turbulent)")
print(f"  Nu Gniel.: {Nu_g[0]:.1f}  ->  {Nu_g[-1]:.1f}")
print(f"  Nu D-B   : {Nu_db[0]:.1f}  ->  {Nu_db[-1]:.1f}   (D-B vs Gnielinski spread {100*abs(Nu_db[-1]-Nu_g[-1])/Nu_g[-1]:.1f}%)")
print(f"  h        : {h_l[0]:.1f}  ->  {h_l[-1]:.1f} W/m2K")
print(f"  Tw inner : {Twi[0]:.1f} K  ->  {Twi[-1]:.1f} K  ({Twi[-1]-273.15:.0f} degC at exit)")
print(f"  Tw outer : {Two[0]:.1f} K  ->  {Two[-1]:.1f} K  ({Two[-1]-273.15:.0f} degC at exit)")
print(f"  Wall-to-bulk dT at exit = {Twi[-1]-Tb[-1]:.1f} K")
print(f"  Through-wall dT at exit = {Two[-1]-Twi[-1]:.1f} K")
V_out = G / rho(Tb[-1])
print(f"  Exit velocity = {V_out:.1f} m/s (accelerates as gas heats); Mach = {V_out/np.sqrt(GAMMA*R_AIR*Tb[-1]):.4f}")

# energy balance closure check
Q_check = mdot * np.mean(cp(Tb)) * (Tb[-1] - Tb[0])
print(f"  ENERGY BALANCE CHECK: Q_applied={Q_tot:.1f} W vs mdot*cp*dT={Q_check:.1f} W "
      f"-> closure error {100*abs(Q_check-Q_tot)/Q_tot:.2f}%")

# ----------------------------------------------------------------------------
# ENTRY LENGTHS, PRESSURE DROP, MESH SIZING
# ----------------------------------------------------------------------------
Lh = 1.359 * Di * Re_in ** 0.25
print("\n--- DEVELOPMENT LENGTHS ---")
print(f"  Turbulent hydrodynamic entry  L_h = 1.359*D*Re^0.25 = {Lh*1000:.0f} mm  (x/D = {Lh/Di:.1f})")
print(f"  Engineering rule of thumb     L_h ~ 10*D          = {10*Di*1000:.0f} mm  (x/D = 10)")
print(f"  -> evaluate fully-developed Nu and f for x/D > {Lh/Di:.0f}, i.e. x > {Lh*1000:.0f} mm")

rho_m, V_m = np.mean(rho(Tb)), np.mean(G / rho(Tb))
dp_fric = np.mean(f_l) * (L / Di) * 0.5 * rho_m * V_m ** 2
dp_acc = G ** 2 * (1 / rho(Tb[-1]) - 1 / rho(Tb[0]))
print("\n--- PRESSURE DROP (Darcy-Weisbach + thermal acceleration) ---")
print(f"  Mean Darcy f  = {np.mean(f_l):.5f}")
print(f"  Friction dp   = {dp_fric:.1f} Pa")
print(f"  Acceleration  = {dp_acc:.1f} Pa")
print(f"  Total dp      = {dp_fric+dp_acc:.1f} Pa  ({100*(dp_fric+dp_acc)/P_OP:.3f}% of operating pressure)")
print("  -> pressure variation << 1%, so INCOMPRESSIBLE IDEAL GAS density is appropriate")

tau_w = np.mean(f_l) / 8 * rho(T_in) * V_in ** 2
u_tau = np.sqrt(tau_w / rho(T_in))
y1 = mu(T_in) / rho(T_in) / u_tau
print("\n--- NEAR-WALL MESH SIZING (target y+ = 1 for wall-resolved SST) ---")
print(f"  Wall shear tau_w = {tau_w:.4f} Pa ; u_tau = {u_tau:.4f} m/s")
print(f"  First-cell HEIGHT for y+=1 : {y1*1e6:.1f} um  (first cell CENTROID at 2x this if measured to centre)")
gr, nlay = 1.2, 18
print(f"  With growth {gr} and {nlay} layers -> BL thickness {y1*(gr**nlay-1)/(gr-1)*1000:.2f} mm "
      f"({100*y1*(gr**nlay-1)/(gr-1)/ri:.0f}% of pipe radius)")

Ncirc, Nax, Nrad_solid, Ncore = 48, 90, 10, 520
cells = ((Ncirc * nlay + Ncore) + (Ncirc * Nrad_solid)) * Nax
print("\n--- MESH SIZE ESTIMATE ---")
print(f"  Circumferential {Ncirc}, axial {Nax}, BL layers {nlay}, core ~{Ncore}, solid radial {Nrad_solid}")
print(f"  Estimated total cells = {cells:,}  (fluid {(Ncirc*nlay+Ncore)*Nax:,} + solid {Ncirc*Nrad_solid*Nax:,})")
print(f"  Solid nodes (for Mechanical) ~ {int(Ncirc*(Nrad_solid+1)*(Nax+1)):,} -> within typical Student 128k node limit")

# ----------------------------------------------------------------------------
# DIMENSIONLESS CHECKS THAT JUSTIFY MODELLING SIMPLIFICATIONS
# ----------------------------------------------------------------------------
Tf = 0.5 * (Twi[-1] + Tb[-1])
beta = 1 / Tf
nu_f = mu(Tf) / rho(Tf)
Gr = 9.81 * beta * (Twi[-1] - Tb[-1]) * Di ** 3 / nu_f ** 2
Ri = Gr / Re_l[-1] ** 2
Ec = V_in ** 2 / (cp(T_in) * (Twi[-1] - Tb[-1]))
Br = Ec * Pr(Tf)
print("\n--- JUSTIFICATION OF MODELLING SIMPLIFICATIONS ---")
print(f"  Grashof Gr           = {Gr:,.0f}")
print(f"  Richardson Gr/Re^2   = {Ri:.2e}  << 0.1  -> BUOYANCY NEGLIGIBLE (pure forced convection)")
print(f"  Eckert  Ec           = {Ec:.2e}")
print(f"  Brinkman Br = Ec*Pr  = {Br:.2e}  << 1   -> VISCOUS DISSIPATION NEGLIGIBLE")
print(f"  Peclet  Pe = Re*Pr   = {Re_l[-1]*Pr(Tb[-1]):,.0f}  -> advection dominated")

# ----------------------------------------------------------------------------
# THERMAL STRESS  -  closed form, thick-walled cylinder, logarithmic profile
# Timoshenko & Goodier, Theory of Elasticity, free-ended long cylinder
# ----------------------------------------------------------------------------
def cyl_thermal_stress(Ti, To, a, b, E, al, nu, r):
    Ta = Ti - To
    C = al * E * Ta / (2 * (1 - nu) * np.log(b / a))
    lb = np.log(b / r); lba = np.log(b / a); k2 = a**2 / (b**2 - a**2)
    sr = C * (-lb - k2 * (1 - b**2 / r**2) * lba)
    st = C * (1 - lb - k2 * (1 + b**2 / r**2) * lba)
    sz = C * (1 - 2 * lb - 2 * k2 * lba)
    return sr, st, sz

Ti_ex, To_ex = Twi[-1], Two[-1]
Tm = 0.5 * (Ti_ex + To_ex)
E_op, al_op, sy_op = Es_f(Tm), al_f(Tm), sy_f(Tm)
r_ev = np.linspace(ri, ro, 200)
sr, st, sz = cyl_thermal_stress(Ti_ex, To_ex, ri, ro, E_op, al_op, NU_S, r_ev)
svm = np.sqrt(0.5 * ((sr - st) ** 2 + (st - sz) ** 2 + (sz - sr) ** 2))

print("\n" + "=" * 78)
print("THERMAL STRESS - ANALYTICAL BASELINE (to be compared with FEA later)")
print("=" * 78)
print(f"  Evaluated at exit station: Ti={Ti_ex:.1f} K, To={To_ex:.1f} K, dT_wall={To_ex-Ti_ex:.1f} K")
print(f"  Properties at Tm={Tm:.0f} K: E={E_op/1e9:.0f} GPa, alpha={al_op*1e6:.1f} e-6/K, "
      f"nu={NU_S}, Sy={sy_op/1e6:.0f} MPa")
print("\n  LOAD CASE 1 - free axial growth, gradient-driven stress only:")
print(f"    sigma_r   : {sr.min()/1e6:+.2f} to {sr.max()/1e6:+.2f} MPa")
print(f"    sigma_hoop: {st.min()/1e6:+.2f} to {st.max()/1e6:+.2f} MPa  "
      f"(inner {st[0]/1e6:+.2f}, outer {st[-1]/1e6:+.2f})")
print(f"    sigma_z   : {sz.min()/1e6:+.2f} to {sz.max()/1e6:+.2f} MPa")
print(f"    von Mises max = {svm.max()/1e6:.2f} MPa  -> MoS = {sy_op/svm.max()-1:.1f} (very large)")

T_solid_mean = np.mean(0.5 * (Twi + Two))
sz_restr = -Es_f(T_solid_mean) * al_f(T_solid_mean) * (T_solid_mean - T_REF)
print("\n  LOAD CASE 2 - fully axially restrained (both ends built in):")
print(f"    Volume-mean solid temperature ~ {T_solid_mean:.1f} K "
      f"(dT above {T_REF:.0f} K reference = {T_solid_mean-T_REF:.1f} K)")
print(f"    sigma_z ~ -E*alpha*dT = {sz_restr/1e6:.0f} MPa (compressive)")
print(f"    |sigma_z| / Sy = {abs(sz_restr)/sy_f(T_solid_mean):.2f}  "
      f"-> MoS = {sy_f(T_solid_mean)/abs(sz_restr)-1:.2f}")
print(f"    RATIO LC2/LC1 = {abs(sz_restr)/svm.max():.0f}x")
print("\n  ENGINEERING CONCLUSION (to be tested by FEA):")
print("    Restraint, not the through-wall gradient, is the dominant thermal-stress driver.")

dr = al_op * (T_solid_mean - T_REF) * ri
print("\n--- ONE-WAY vs TWO-WAY COUPLING CHECK ---")
print(f"  Free radial growth of bore = {dr*1e6:.1f} um = {100*dr/ri:.3f}% of radius")
print(f"  Flow-area change           = {100*((ri+dr)**2-ri**2)/ri**2:.3f}%")
print("  -> geometry change is far below mesh/turbulence-model uncertainty (~5-15% on Nu)")
print("  -> ONE-WAY coupling (CFD temperatures -> FEA) is justified; two-way not required")
print("  NOTE: fluid<->solid CONJUGATE heat transfer is still fully two-way inside Fluent.")
print("=" * 78)

np.savetxt("axial_profiles.csv",
           np.column_stack([x, x / Di, Tb, Twi, Two, h_l, Nu_g, Nu_db, Re_l]),
           delimiter=",", header="x_m,x_over_D,Tb_K,Twall_inner_K,Twall_outer_K,h_W_m2K,Nu_gnielinski,Nu_dittus_boelter,Re",
           comments="")
np.savetxt("radial_stress_exit.csv", np.column_stack([r_ev, sr, st, sz, svm]), delimiter=",",
           header="r_m,sigma_r_Pa,sigma_hoop_Pa,sigma_z_Pa,sigma_vm_Pa", comments="")
print("\nWrote axial_profiles.csv and radial_stress_exit.csv")

# ============================================================================
# PROPERTY-VARIATION CORRECTION  (added after reviewing correlation validity)
# ----------------------------------------------------------------------------
# FLAG: Dittus-Boelter and Gnielinski are CONSTANT-PROPERTY correlations. Their
# usual stated validity for gases is |Tw - Tb| of order 60 K. Here the computed
# wall-to-bulk difference reaches ~240 K, FAR outside that range, because air is
# a poor coolant. Ignoring this would overstate h and understate metal temperature.
#
# Correction (Kays & Crawford, turbulent gas flow, heating):
#     Nu = Nu_const-prop * (Tb/Tw)^n ,  n ~ 0.5   (n in the literature: 0.4 - 0.575)
# Solved iteratively at each station because Tw depends on h which depends on Tw.
# ============================================================================
print("\n" + "=" * 78)
print("PROPERTY-VARIATION CORRECTION - correlation validity check")
print("=" * 78)
n_exp = 0.5
Twi_c = np.zeros(N + 1); h_c = np.zeros(N + 1); Two_c = np.zeros(N + 1); Nu_c = np.zeros(N + 1)
for i in range(N + 1):
    Tw = Twi[i]
    for _ in range(80):
        corr = (Tb[i] / Tw) ** n_exp
        h_i = h_l[i] * corr
        Tw_new = Tb[i] + QPP_IN / h_i
        if abs(Tw_new - Tw) < 1e-6: Tw = Tw_new; break
        Tw = 0.5 * (Tw + Tw_new)
    corr = (Tb[i] / Tw) ** n_exp
    h_c[i] = h_l[i] * corr; Nu_c[i] = Nu_g[i] * corr; Twi_c[i] = Tw
    Two_c[i] = Tw + qprime * np.log(ro / ri) / (2 * np.pi * ks_f(Tw))

print(f"  Correction exponent n = {n_exp} applied as Nu = Nu_cp * (Tb/Tw)^n")
print(f"  Exit correction factor      = {(Tb[-1]/Twi_c[-1])**n_exp:.4f}  ({100*((Tb[-1]/Twi_c[-1])**n_exp-1):.1f}% on h)")
print(f"  Nu at exit  : uncorrected {Nu_g[-1]:.1f}  ->  corrected {Nu_c[-1]:.1f}")
print(f"  h  at exit  : uncorrected {h_l[-1]:.1f}  ->  corrected {h_c[-1]:.1f} W/m2K")
print(f"  Tw_i at exit: uncorrected {Twi[-1]:.1f} K ->  corrected {Twi_c[-1]:.1f} K  "
      f"(+{Twi_c[-1]-Twi[-1]:.1f} K, {Twi_c[-1]-273.15:.0f} degC)")
print(f"  Tw_o at exit: uncorrected {Two[-1]:.1f} K ->  corrected {Two_c[-1]:.1f} K")
print(f"  Through-wall dT at exit    : {Two_c[-1]-Twi_c[-1]:.2f} K")
print(f"  Bulk temperature is UNCHANGED at {Tb[-1]:.1f} K - it is fixed by the energy balance,")
print("    not by h. Only the WALL temperature moves. This is an important distinction.")

Tsm_c = np.mean(0.5 * (Twi_c + Two_c))
E_c, al_c, sy_c = Es_f(Tsm_c), al_f(Tsm_c), sy_f(Tsm_c)
sz_c = -E_c * al_c * (Tsm_c - T_REF)
Ti_c, To_c = Twi_c[-1], Two_c[-1]
Tm_c = 0.5 * (Ti_c + To_c)
sr_c, st_c, sz_g = cyl_thermal_stress(Ti_c, To_c, ri, ro, Es_f(Tm_c), al_f(Tm_c), NU_S, r_ev)
svm_c = np.sqrt(0.5 * ((sr_c - st_c) ** 2 + (st_c - sz_g) ** 2 + (sz_g - sr_c) ** 2))
print("\n  KNOCK-ON EFFECT ON STRUCTURE:")
print(f"    Volume-mean solid T : {T_solid_mean:.1f} K -> {Tsm_c:.1f} K")
print(f"    LC1 peak von Mises  : {svm.max()/1e6:.1f} MPa -> {svm_c.max()/1e6:.1f} MPa")
print(f"    LC2 axial stress    : {sz_restr/1e6:.0f} MPa -> {sz_c/1e6:.0f} MPa")
print(f"    LC2 utilisation     : {abs(sz_restr)/sy_f(T_solid_mean):.2f} -> {abs(sz_c)/sy_c:.2f} of hot yield")
print(f"    LC2 margin of safety: {sy_f(T_solid_mean)/abs(sz_restr)-1:.2f} -> {sy_c/abs(sz_c)-1:.2f}")
print(f"    Peak metal {Twi_c[-1]-273.15:.0f} degC vs Inconel 718 service limit ~650 degC -> "
      f"{'ACCEPTABLE' if Twi_c[-1]-273.15 < 650 else 'EXCEEDED'}")

print("\n  HOW THIS IS USED:")
print("    Fluent solves with TEMPERATURE-DEPENDENT air properties and a wall-resolved")
print("    boundary layer, so it captures this effect natively. The CFD result is therefore")
print("    expected to sit NEAR THE CORRECTED VALUE, not the constant-property one.")
print("    VERIFICATION BAND for fully developed Nu at exit:")
print(f"      corrected (expected)     {Nu_c[-1]:.1f}")
print(f"      constant-property upper  {Nu_db[-1]:.1f}  (Dittus-Boelter, no correction)")
print(f"    -> accept CFD anywhere in {Nu_c[-1]:.0f} - {Nu_db[-1]:.0f}; investigate outside it.")
print("=" * 78)
np.savetxt("axial_profiles_corrected.csv",
           np.column_stack([x, x/Di, Tb, Twi, Twi_c, Two_c, h_l, h_c, Nu_g, Nu_c]), delimiter=",",
           header="x_m,x_over_D,Tb_K,Twi_uncorr_K,Twi_corr_K,Two_corr_K,h_uncorr,h_corr,Nu_uncorr,Nu_corr",
           comments="")
