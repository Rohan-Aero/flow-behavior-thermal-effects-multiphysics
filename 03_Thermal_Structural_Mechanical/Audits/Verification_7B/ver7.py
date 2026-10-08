import numpy as np, json
B="<PROJECT_ROOT>/08_Structural_Analysis/"
cases={"LC1":"LC1_Free_Expansion","LC2":"LC2_Restrained","LC2P":"Pressure_Check"}
D={c:np.loadtxt(B+f+"/Solver_Output/s7b_nodal.csv",delimiter=",",skiprows=1) for c,f in cases.items()}
cm=np.load("corner_mask.npy")
cols="node,x,y,z,ur,ut,uz,sr,st,sz,s1,s3,seqv,ee,T".split(","); ci={k:j for j,k in enumerate(cols)}
g=lambda c,k: D[c][:,ci[k]]
x,y,z=g("LC1","x"),g("LC1","y"),g("LC1","z"); r=np.hypot(x,y); TK=g("LC1","T")+273.15; th=np.degrees(np.arctan2(y,x))
def L(j): return "node %d r %.1f z %.2f th %.0f T %.2f"%(g("LC1","node")[j],r[j]*1e3,z[j]*1e3,th[j],TK[j])
j=104045; print("LC2 node 104046 uz %.4f ur %.4f mm"%(g("LC2","uz")[j]*1e3,g("LC2","ur")[j]*1e3))
for c in ("LC1","LC2"):
    s1=np.where(cm,g(c,"s1"),-1e30); s3=np.where(cm,g(c,"s3"),1e30)
    print(c,"s1max",s1.max()/1e6,L(np.argmax(s1)),"| s3min",s3.min()/1e6,L(np.argmin(s3)))
# outlet end LC1 bore vm vs z
for c,rad in (("LC1",0.01),("LC2",0.02)):
    m=cm&(np.abs(r-rad)<1e-7)&(z>0.58)
    zs=np.unique(np.round(z[m],6))
    prof=[(q*1e3,g(c,"seqv")[m&(np.abs(z-q)<1e-6)].mean()/1e6) for q in zs]
    print(c,"r=%g outlet profile"%rad,[("%.1f"%a,"%.2f"%b) for a,b in prof[-10:]])
# theta-avg VM profiles outer/bore LC2 full length
for rad in (0.01,0.02):
    m=cm&(np.abs(r-rad)<1e-7); zs=np.unique(np.round(z[m],6))
    v=np.array([g("LC2","seqv")[m&(np.abs(z-q)<1e-6)].mean() for q in zs])/1e6
    print("LC2 r=%g theta-avg VM range %.1f - %.1f"%(rad,v.min(),v.max()))
# BFBLOCK vs T_used
Lr=open(B+"Mechanical_Setup/Input_Files/LC2_Axially_Restrained_ds.dat").read().splitlines()
k=[i for i,l in enumerate(Lr) if l.lower().startswith("bfblock")][0]+2
bf={}
while not Lr[k].lower().startswith("bf,end"):
    p=Lr[k].split()
    if len(p)==2: bf[int(p[0])]=float(p[1])
    k+=1
nn=g("LC1","node").astype(int)
print("bf count",len(bf)," max|T_used-BF| K", max(abs(g("LC1","T")[i]-bf[nn[i]]) for i in range(len(nn))))
# radial growth bore vs alpha_sec*dT*r
Ta=np.array([93.33,204.44,315.56,426.67,537.78]); at=np.array([12.8,13.3,13.9,14.2,14.8])*1e-6
ap=(at*(Ta-21.11)-12.8e-6*(26.85-21.11))/(Ta-26.85)
print("alpha_sec*dT*r at bore mid (531.69K):", np.interp(258.54,Ta,ap)*(258.54-26.85)*0.01*1e6,"um")
P=json.load(open(B+"Audits/presolve_audit_7B.json"))
for ch in P["checks"]:
    s=json.dumps(ch)
    if any(w in s.lower() for w in ("export","jacobian","quality","aspect","byte","identical")): print(" ",s[:260])
S=json.load(open(B+"Audits/mech_solve_7B_summary.json"))
res=S["cases"]["LC1"]["results"]
for k2,v in res.items():
    if "react" in k2.lower() or "Reaction" in k2: print("LC1",k2,str(v)[:300])
for k2,v in S["cases"]["LC2"]["results"].items():
    if "react" in k2.lower() or "Reaction" in k2: print("LC2",k2,str(v)[:300])
