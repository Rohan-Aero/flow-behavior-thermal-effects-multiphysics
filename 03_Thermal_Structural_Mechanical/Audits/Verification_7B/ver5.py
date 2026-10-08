import numpy as np
from scipy.integrate import simpson
exec(open("ver4.py").read().split("key={}")[0])
cm=np.load("corner_mask.npy")
zc=np.unique(zr[cm])
out={}
for mode in ("simpson_r11","trap_r11"):
    Eb=[];em=[]
    for q in zc:
        m=zr==q; R=rr[m]; T=TC[m]; rad=np.unique(R); Tr=np.array([T[R==v].mean() for v in rad])
        f=(lambda v: simpson(v*2*np.pi*rad,x=rad)) if mode=="simpson_r11" else (lambda v: np.trapezoid(v*2*np.pi*rad,rad))
        E=Ef(Tr); e=eps(Tr); Eb.append(f(E)/f(np.ones_like(rad))); em.append(f(E*e)/f(E))
    Eb=np.array(Eb); em=np.array(em)
    for zm in ("trap","simpson"):
        I=(np.trapezoid if zm=="trap" else (lambda v,x: simpson(v,x=x)))
        dL=I(em,zc); N=-dL/I(1/(Eb*A),zc)
        print(mode,zm,"dL %.6f mm  FE/int-1 %.2e   N %.1f  FE/an-1 %.2e"%(dL*1e3,1.840860e-3/dL-1,N,548936.6137/(-N)-1))
