import numpy as np
from scipy.integrate import simpson
exec(open("ver4.py").read().split("key={}")[0])
d=lambda f,T,h=1e-3:(f(T+h)-f(T-h))/(2*h)
Tm=525.52-273.15
s=d(eps,Tm); print("deps/dT at vol-mean %.4e ; L*: %.3f um/K ; range %.1f / %.1f um best %.1f"%(s,0.6*s*1e6,-3.6*0.6*s*1e6,1.0*0.6*s*1e6,-3.1*0.6*s*1e6))
Ebar=189.3e9
# LC2 uniform shift: section-mean E around the field; use A-weighted mean E over volume
print("LC2 -Ebar*deps/dT (Ebar from N/A / eps?)")
Evol=np.average(Ef(TC)); print(" E vol-mean %.2f GPa -> %.3f MPa/K ; range %.1f/%.1f best %.1f"%(Evol/1e9,Evol*s/1e6,-3.6*Evol*s/1e6,1.0*Evol*s/1e6,-3.1*Evol*s/1e6))
Tc=437.99-273.15; Ec=Ef(Tc); at=d(eps,Tc); print("peak: E %.2f GPa alpha_tan %.3e -> %.3f MPa/K ; -5.1: %.1f +1.6: %.1f"%(Ec/1e9,at,Ec*at/1e6,-5.1*Ec*at/1e6,1.6*Ec*at/1e6))
Sy=lambda T: np.interp(T,[20,100,200,300,400.],[1030,1060,1040,1020,1000])
# utilisation under uniform shift: stress changes by E*alpha_sec-change ~ -Evol*s*dT ; Sy changes at the peak location
for dT in (-3.6,1.0,-3.1):
    sig=605.16+ Evol*s/1e6*dT; print(" dT %+.1f: U %.4f"%(dT, sig/Sy(Tc+dT)))
# Timoshenko at mid-span with the FE radial profile (generalized plane strain, free ends)
m=(zr==0.3); R=rr[m]; T=TC[m]; rad=np.unique(R); Tr=np.array([T[R==v].mean() for v in rad])
e=eps(Tr); a,b=0.01,0.02; nu=0.294
Em=Ef(Tr.mean()); c=Em/(1-nu)
I=lambda rr_: simpson((e*rad)[rad<=rr_+1e-12],x=rad[rad<=rr_+1e-12]) if rr_>a+1e-12 else 0.0
Ib=simpson(e*rad,x=rad)
def st(r_,er): return c/r_**2*((r_**2+a**2)/(b**2-a**2)*Ib+I(r_)-er*r_**2)
def sz(er): return c*(2*Ib/(b**2-a**2)-er)
print("Timoshenko bore st %.2f sz %.2f ; outer st %.2f sz %.2f (E %.1f GPa)"%(st(a,e[0])/1e6,sz(e[0])/1e6,st(b,e[-1])/1e6,sz(e[-1])/1e6,Em/1e9))
