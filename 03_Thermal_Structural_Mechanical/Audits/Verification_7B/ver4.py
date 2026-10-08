import numpy as np
from scipy.integrate import simpson
B="<PROJECT_ROOT>/08_Structural_Analysis/"
a1=np.loadtxt(B+"LC1_Free_Expansion/Solver_Output/s7b_nodal.csv",delimiter=",",skiprows=1)
x,y,z,uz,TC=a1[:,1],a1[:,2],a1[:,3],a1[:,6],a1[:,14]; r=np.hypot(x,y)
Tt=np.array([20,100,200,300,400.]); Et=np.array([204,199,193,187,180])*1e9
Ta=np.array([93.33,204.44,315.56,426.67,537.78]); at=np.array([12.8,13.3,13.9,14.2,14.8])*1e-6
T0=21.11; TR=26.85; ap=(at*(Ta-T0)-12.8e-6*(TR-T0))/(Ta-TR)
eps=lambda T: np.interp(T,Ta,ap)*(T-TR); Ef=lambda T: np.interp(T,Tt,Et)
zr=np.round(z,7); rr=np.round(r,7)
zs=np.unique(zr); rs=np.unique(rr); print("planes",zs.size,"radii",rs*1e3)
A=np.pi*(0.02**2-0.01**2)
key={}
# theta-mean at each (z,r) that exists (corner planes have all 11 radii? midside planes only corner radii)
Ebar=[];epsm=[];zz=[]
for q in zs:
    m=zr==q; R=rr[m]; T=TC[m]
    rad=np.unique(R)
    Tr=np.array([T[R==v].mean() for v in rad])
    if rad.size<3: continue
    f=lambda v: simpson(v*2*np.pi*rad,x=rad) if rad.size%2==1 else np.trapezoid(v*2*np.pi*rad,rad)
    E=Ef(Tr); e=eps(Tr)
    Ebar.append(f(E)/A); epsm.append(f(E*e)/f(E)); zz.append(q)
zz=np.array(zz); Ebar=np.array(Ebar); epsm=np.array(epsm)
print("planes used",zz.size, "radii per plane examples")
dL=simpson(epsm,x=zz); N=-dL/simpson(1/(Ebar*A),x=zz)
def face(q):
    m=zr==q; R=rr[m]; U=uz[m]; rad=np.unique(R); Ur=np.array([U[R==v].mean() for v in rad])
    return simpson(Ur*2*np.pi*rad,x=rad)/simpson(np.ones_like(rad)*2*np.pi*rad,x=rad)
dfe=face(0.6)-face(0.0)
print("dL FE %.6f mm integral %.6f mm ratio-1 %.2e"%(dfe*1e3,dL*1e3,dfe/dL-1))
print("N %.1f N  ratio FE/an-1 %.2e  N/A %.3f MPa"%(N,548936.6137/(-N)-1,N/A/1e6))
# one-alpha volume-mean estimate
print("volume-mean-T estimate (525.52 K):", eps(525.52-273.15)*0.6*1e3,"mm")
