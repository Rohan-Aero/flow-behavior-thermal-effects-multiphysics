import numpy as np, os
R=r"<PROJECT_ROOT>"
v1=os.path.join(R,"10_Parametric_Study","Structural_Cases","S2_REEXTRACT","s1x_nodal.csv")
v0=os.path.join(R,"08_Structural_Analysis","Buckling","Mechanical","LC2_prestress_resolve","Solver_Output","s7b_nodal.csv")
A1=np.loadtxt(v1,delimiter=",",skiprows=1); A0=np.loadtxt(v0,delimiter=",",skiprows=1)
np.set_printoptions(precision=6, suppress=False, linewidth=200)
for c,name in ((4,"ur"),(5,"ut")):
    d=np.abs(A1[:,c]-A0[:,c]); idx=np.argsort(d)[::-1][:6]
    print(name,"top diffs")
    for i in idx: print(int(A0[i,0]), A0[i,1:4], "s1x", A1[i,4:7], "8A", A0[i,4:7], "d", d[i])
    print(name, "n nodes diff>1e-9:", int((d>1e-9).sum()))
for n in (25862,25874,25886):
    i=np.where(A0[:,0]==n)[0][0]; print(n, A0[i,1:4], "s1x", A1[i,4:7], "8A", A0[i,4:7])
