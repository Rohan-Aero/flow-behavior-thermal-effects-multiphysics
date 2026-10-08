import numpy as np, json, re
B="<PROJECT_ROOT>/08_Structural_Analysis/"
cases={"LC1":"LC1_Free_Expansion","LC2":"LC2_Restrained","LC2P":"Pressure_Check"}
D={c:np.loadtxt(B+f+"/Solver_Output/s7b_nodal.csv",delimiter=",",skiprows=1) for c,f in cases.items()}
cm=np.load("corner_mask.npy")
cols="node,x,y,z,ur,ut,uz,sr,st,sz,s1,s3,seqv,ee,T".split(","); ci={k:j for j,k in enumerate(cols)}
g=lambda c,k: D[c][:,ci[k]]
z=g("LC1","z"); r=np.hypot(g("LC1","x"),g("LC1","y"))
for c in ("LC1","LC2"):
    m=cm&(z>=0.05)&(z<=0.55); v=np.where(m,g(c,"seqv"),-1); j=np.argmax(v)
    print(c,"max VM 50-550: %.2f MPa r %.1f z %.1f T %.2f K"%(v[j]/1e6,r[j]*1e3,z[j]*1e3,g(c,"T")[j]+273.15))
S=json.load(open(B+"Audits/mech_solve_7B_summary.json"))
def num(s):
    m=re.match(r"\s*([-+0-9.Ee]+)",str(s)); return float(m.group(1)) if m else None
ours={"Equivalent_Stress_averaged":("seqv",cm,1),"Maximum_Principal_Stress":("s1",cm,1),"Minimum_Principal_Stress":("s3",cm,-1),
      "Total_Deformation":(None,None,1),"Equivalent_Elastic_Strain":("ee",cm,1)}
for c in cases:
    res=S["cases"][c]["results"]
    for k,v in res.items():
        for key,(col,mask,sgn) in ours.items():
            if k.endswith(key) or k==c+"_"+key:
                mx=num(v.get("Maximum")); mn=num(v.get("Minimum"))
                if col is None: o=np.sqrt(g(c,"ur")**2+g(c,"ut")**2+g(c,"uz")**2).max(); mech=mx
                elif sgn==1: o=np.where(mask,g(c,col),-1e30).max(); mech=mx
                else: o=np.where(mask,g(c,col),1e30).min(); mech=mn
                print(c,k,"mech",mech,"snippet",o,"rel %.1e"%(mech/o-1))
