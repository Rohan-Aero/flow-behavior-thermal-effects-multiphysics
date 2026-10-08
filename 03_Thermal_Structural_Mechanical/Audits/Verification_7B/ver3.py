import numpy as np
B="<PROJECT_ROOT>/08_Structural_Analysis/"
cases={"LC1":"LC1_Free_Expansion","LC2":"LC2_Restrained","LC2P":"Pressure_Check"}
D={c:np.loadtxt(B+f+"/Solver_Output/s7b_nodal.csv",delimiter=",",skiprows=1) for c,f in cases.items()}
cm=np.load("corner_mask.npy")
cols="node,x,y,z,ur,ut,uz,sr,st,sz,s1,s3,seqv,ee,T".split(","); ci={k:j for j,k in enumerate(cols)}
g=lambda c,k: D[c][:,ci[k]]
x,y,z=g("LC1","x"),g("LC1","y"),g("LC1","z"); r=np.hypot(x,y); TC=g("LC1","T")
# material
Tt=np.array([20,100,200,300,400.]); Et=np.array([204,199,193,187,180])*1e9
Ta=np.array([93.33,204.44,315.56,426.67,537.78]); at=np.array([12.8,13.3,13.9,14.2,14.8])*1e-6
T0=21.11; TR=26.85
ap=(at*(Ta-T0)-12.8e-6*(TR-T0))/(Ta-TR)
eps=lambda T: np.interp(T,Ta,ap)*(T-TR)
Ef=lambda T: np.interp(T,Tt,Et)
Sy=lambda T: np.interp(T,Tt,[1030,1060,1040,1020,1000])
# corner planes and radii
zc=np.unique(np.round(z[cm],7)); print("corner planes",zc.size)
rc=np.unique(np.round(r[cm],7)); print("corner radii (mm)",rc*1e3)
def section(zz):
    m=cm&(np.abs(z-zz)<1e-7)
    rr=np.round(r[m],7); T=TC[m]
    # theta-mean per radius, then annulus trapezoid integration of f(r) r dr
    Tr=np.array([T[rr==q].mean() for q in rc])
    return Tr
A=np.pi*(0.02**2-0.01**2)
def annint(f):  # integral f 2 pi r dr, trapezoid on corner radii
    return np.trapezoid(f*2*np.pi*rc,rc)
num=[];den=[];Ebar=[];epsm=[]
for zz in zc:
    Tr=section(zz); e=eps(Tr); E=Ef(Tr)
    Ebar.append(annint(E)/annint(np.ones_like(rc))); epsm.append(annint(E*e)/annint(E))
Ebar=np.array(Ebar); epsm=np.array(epsm)
dL_int=np.trapezoid(epsm,zc)
# FE face-mean u_z
def facemean(c,zz):
    m=(np.abs(z-zz)<1e-7)&cm
    rr=np.round(r[m],7); u=g(c,"uz")[m]
    ur=np.array([u[rr==q].mean() for q in rc]); return annint(ur)/annint(np.ones_like(rc))
dL_fe=facemean("LC1",0.6)-facemean("LC1",0.0)
print("LC1 dL FE %.5f mm  integral %.5f mm  ratio-1 %.2e ; vs 2.096: %.2f %%"%(dL_fe*1e3,dL_int*1e3,dL_fe/dL_int-1,(dL_fe/2.096e-3-1)*100))
# LC2 analytic N
N=-np.trapezoid(epsm,zc)/np.trapezoid(1/(Ebar*A),zc)
print("LC2 analytic N %.0f N ; N/A %.2f MPa ; FE reaction 548936.61 -> ratio-1 %.2e"%(N,N/A/1e6,548936.6137/(-N)-1))
print("548936.61/A MPa", 548936.6137/A/1e6)
# pressure: max VM diff
vm2=np.where(cm,g("LC2","seqv"),-1); vmp=np.where(cm,g("LC2P","seqv"),-1)
print("max VM diff Pa %.1f  pct %.2e"%(vmp.max()-vm2.max(),(vmp.max()/vm2.max()-1)*100))
dv=(g("LC2P","seqv")-g("LC2","seqv"))[cm]; print("nodewise dVM Pa min %.1f max %.1f"%(dv.min(),dv.max()))
p=443.41; a=0.01; b=0.02; nu=0.294
m=cm&(np.abs(z-0.3)<1e-7)
for k in ("st","sr","sz"):
    d=(g("LC2P",k)-g("LC2",k))
    print(k,"bore %.1f outer %.1f"%(d[m&(np.abs(r-a)<1e-7)].mean(),d[m&(np.abs(r-b)<1e-7)].mean()), "range sz" if k=="sz" else "", (d[m].min(),d[m].max()) if k=="sz" else "")
mb=(np.abs(z-0.3)<1e-7)&(np.abs(r-a)<1e-7)
dur=(g("LC2P","ur")-g("LC2","ur"))[mb].mean(); Tb=TC[mb].mean(); Eb=Ef(Tb)
urL=(1+nu)*p*a/(Eb*(b*b-a*a))*((1-2*nu)*a*a+b*b)
print("Lame st(a) %.1f st(b) %.1f sz %.1f ; dur FE %.4e Lame %.4e (E %.1f GPa at %.2f C)"%(p*(b*b+a*a)/(b*b-a*a),2*p*a*a/(b*b-a*a),nu*(2*p*a*a/(b*b-a*a)),dur,urL,Eb/1e9,Tb))
# utilisation
for c in cases:
    vm=np.where(cm,g(c,"seqv"),-1); j=np.argmax(vm); T=g(c,"T")[j]
    U=vm[j]/1e6/Sy(T); print(c,"U at max VM %.4f margin %.3f Sy %.1f T %.2f K"%(U,1/U-1,Sy(T),T+273.15))
    u=np.where(cm,g(c,"seqv")/1e6/Sy(g(c,"T")),-1); k=np.argmax(u); mm=cm&(z>0.015)&(z<0.585); k2=np.argmax(np.where(mm,u,-1))
    print("   nodewise max U %.4f at z %.1f mm r %.1f ; outside 15-585: %.4f at z %.1f mm, vm %.2f, T %.2f K, Sy %.1f"%(u[k],z[k]*1e3,r[k]*1e3,u[k2],z[k2]*1e3,g(c,"seqv")[k2]/1e6,g(c,"T")[k2]+273.15,Sy(g(c,"T")[k2])))
print("LC2 with scalar 1020:",605.160873/1020)
# LC1 midspan
m=cm&(np.abs(z-0.3)<1e-7)
for rr in (a,b):
    q=m&(np.abs(r-rr)<1e-7)
    print("LC1 mid r=%.0fmm st %.2f sz %.2f vm %.2f T %.2f K"%(rr*1e3,g("LC1","st")[q].mean()/1e6,g("LC1","sz")[q].mean()/1e6,g("LC1","seqv")[q].mean()/1e6,TC[q].mean()+273.15))
    q2=m&(np.abs(r-rr)<1e-7); print("   LC2 mid sz %.2f vm %.2f ur(mm) LC1 %.4f LC2 %.4f"%(g("LC2","sz")[q2].mean()/1e6,g("LC2","seqv")[q2].mean()/1e6,g("LC1","ur")[q2].mean()*1e3,g("LC2","ur")[q2].mean()*1e3))
