# Independent re-computation (written fresh, does not import post_7B.py)
import numpy as np, json, re
B="<PROJECT_ROOT>/08_Structural_Analysis/"
dat=B+"Mechanical_Setup/Input_Files/LC2_Axially_Restrained_ds.dat"
L=open(dat).read().splitlines()
i=[k for k,l in enumerate(L) if l.lower().startswith("eblock")][0]+2
E=[]
while L[i].strip()!="-1":
    E.append([int(x) for x in L[i].split()]); i+=1
E=np.array(E); print("elements",E.shape)
corner=np.unique(E[:,1:9]); mid=np.unique(E[:,9:21])
print("corner",corner.size,"mid",mid.size,"overlap",np.intersect1d(corner,mid).size)
cases={"LC1":"LC1_Free_Expansion","LC2":"LC2_Restrained","LC2P":"Pressure_Check"}
D={}
for c,f in cases.items():
    a=np.loadtxt(B+f+"/Solver_Output/s7b_nodal.csv",delimiter=",",skiprows=1)
    D[c]=a
    print(c,a.shape, "nodes 1..",int(a[:,0].max()))
cols="node,x,y,z,ur,ut,uz,sr,st,sz,s1,s3,seqv,ee,T".split(",")
ci={k:j for j,k in enumerate(cols)}
def g(c,k): return D[c][:,ci[k]]
isc=np.zeros(int(D["LC1"][:,0].max())+1,bool); isc[corner]=True
cm=isc[D["LC1"][:,0].astype(int)]
# midside stresses zero?
print("midside seqv nonzero count LC2:", np.count_nonzero(g("LC2","seqv")[~cm]))
res={}
for c in cases:
    x,y,z=g(c,"x"),g(c,"y"),g(c,"z"); r=np.hypot(x,y); th=np.degrees(np.arctan2(y,x)); TK=g(c,"T")+273.15
    def loc(j): return dict(node=int(g(c,"node")[j]),r_mm=round(r[j]*1e3,3),z_mm=round(z[j]*1e3,3),th=round(th[j],1),T_K=round(TK[j],2))
    vm=np.where(cm,g(c,"seqv"),-1); j=np.argmax(vm)
    ut=np.sqrt(g(c,"ur")**2+g(c,"ut")**2+g(c,"uz")**2); k=np.argmax(ut)
    out=dict(vm_max_MPa=vm[j]/1e6,vm_loc=loc(j),utot_max_mm=ut[k]*1e3,utot_loc=loc(k),
             uz_max_mm=g(c,"uz").max()*1e3, uz_min_mm=g(c,"uz").min()*1e3, uz_min_loc=loc(np.argmin(g(c,"uz"))),
             ur_max_mm=g(c,"ur").max()*1e3, ur_max_loc=loc(np.argmax(g(c,"ur"))),
             s1_max_MPa=np.where(cm,g(c,"s1"),-1e30).max()/1e6, s3_min_MPa=np.where(cm,g(c,"s3"),1e30).min()/1e6,
             ee_max=np.where(cm,g(c,"ee"),-1).max(), ee_loc=loc(np.argmax(np.where(cm,g(c,"ee"),-1))),
             T_range_K=(TK.min(),TK.max()))
    # outside end zones
    m=cm&(z>0.015)&(z<0.585); jj=np.argmax(np.where(m,g(c,"seqv"),-1)); out["vm_max_15_585"]=(g(c,"seqv")[jj]/1e6,loc(jj))
    res[c]=out
for c in res:
    print("\n==",c)
    for k,v in res[c].items(): print(" ",k,v)
# temperature vs 7A export
t7=np.loadtxt("<PROJECT_ROOT>/07_Thermal_Analysis/Mapping/Mechanical_Export/LC1_imported_body_temperature.txt",skiprows=1,encoding="latin-1",usecols=(0,1))
t7d=dict(zip(t7[:,0].astype(int),t7[:,1]))
Tn=g("LC1","T"); nn=g("LC1","node").astype(int)
diff=np.array([abs(Tn[q]-t7d[nn[q]]) for q in range(len(nn))])
print("\nmax|T_used-7A export| K",diff.max(), " LC2/LC2P T identical to LC1:", np.abs(g("LC2","T")-Tn).max(), np.abs(g("LC2P","T")-Tn).max())
np.save("corner_mask.npy",cm)
