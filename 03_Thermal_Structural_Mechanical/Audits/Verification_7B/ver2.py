import numpy as np, json
B="<PROJECT_ROOT>/08_Structural_Analysis/"
cases={"LC1":"LC1_Free_Expansion","LC2":"LC2_Restrained","LC2P":"Pressure_Check"}
rot={"LC1":{18870,18882,18894},"LC2":{25862,25874,25886},"LC2P":{25862,25874,25886}}
for c,f in cases.items():
    a=np.atleast_2d(np.loadtxt(B+f+"/Solver_Output/s7b_react.csv",delimiter=",",skiprows=1))
    n=a[:,0].astype(int); x,y,z=a[:,1],a[:,2],a[:,3]; fx,fy,fz=a[:,4].copy(),a[:,5].copy(),a[:,6].copy()
    for q in range(len(n)):
        if n[q] in rot[c]:
            th=np.arctan2(y[q],x[q]); fr,ft=fx[q],fy[q]
            fx[q]=fr*np.cos(th)-ft*np.sin(th); fy[q]=fr*np.sin(th)+ft*np.cos(th)
    F=np.array([fx.sum(),fy.sum(),fz.sum()]); M=np.array([(y*fz-z*fy).sum(),(z*fx-x*fz).sum(),(x*fy-y*fx).sum()])
    print(c,"nodes",len(n),"max|nodal|",np.abs(np.c_[fx,fy,fz]).max(),"SumF",F,"|F|",np.linalg.norm(F),"M",M,"|M|",np.linalg.norm(M))
    if c!="LC1":
        mi=z<1e-9; mo=z>0.6-1e-9; mh=np.isin(n,list(rot[c]))
        print("   inlet",mi.sum(),fz[mi].sum()," outlet",mo.sum(),fz[mo].sum()," hoop nodes |F|",np.abs(np.c_[fx,fy,fz][mh]).max())
    print("   totals file:",open(B+f+"/Solver_Output/s7b_totals.txt").read().replace("\n"," | "))
    t=open(B+f+"/Solver_Output/s7b_prrsol.txt").read()
    print("   PRRSOL total line:",[l for l in t.splitlines() if "VALUE" in l])
S=json.load(open(B+"Audits/mech_solve_7B_summary.json"))
print(S.keys())
for c in S.get("cases",{}):
    cc=S["cases"][c]
    print(c, {k:cc[k] for k in cc if k in ("solution_state","status","solve_state","object_state","solver_type","solve_time_s")})
    for k in cc:
        if "react" in k.lower() or "probe" in k.lower(): print("  ",k,str(cc[k])[:600])
