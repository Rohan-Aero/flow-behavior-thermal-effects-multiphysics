import numpy as np, os
R=r"<PROJECT_ROOT>"
f=os.path.join(R,"10_Parametric_Study","Structural_Cases","S2_REEXTRACT","s2x_nodal.csv")
ds=os.path.join(R,"08_Structural_Analysis","Buckling","Mechanical","LC2NS_NoSway_Static","Solver_Output","ds.dat")
A=np.loadtxt(f,delimiter=",",skiprows=1)
rot=set(int(l.split(",")[1]) for l in open(ds,errors="ignore") if l.lower().startswith("nmod,"))
m=np.isin(A[:,0].astype(int),list(rot))
print("nmod nodes in table", m.sum())
print("max |u_t| at NMOD (U_theta-constrained) nodes [m]:", np.abs(A[m,5]).max())
print("u_r at NMOD nodes min/max [m]:", A[m,4].min(), A[m,4].max())
for zz in (0.0,0.6):
    k=m & (np.abs(A[:,3]-zz)<1e-9) & (np.abs(np.hypot(A[:,1],A[:,2])-0.02)<1e-9)
    print("z",zz,"outer ring n",k.sum(),"u_r min/max",A[k,4].min(),A[k,4].max(),"u_t maxabs",np.abs(A[k,5]).max())
# neighbours just inside the end faces (unrotated): outer ring at first interior z-level
zl=np.unique(A[:,3]); z1=zl[zl>1e-9][0]
k=(np.abs(A[:,3]-z1)<1e-12)&(np.abs(np.hypot(A[:,1],A[:,2])-0.02)<1e-9)
print("first interior level z",z1,"n",k.sum(),"u_r min/max",A[k,4].min(),A[k,4].max(),"u_t maxabs",np.abs(A[k,5]).max())
