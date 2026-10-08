"""ENGINEERING_SCHEMATIC.png - Section 1 problem definition diagram (RE-ANALYSIS)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrow, FancyBboxPatch
import numpy as np

C_SOLID,C_SOLID_E="#8C99A6","#33404D"
C_FLUID,C_FLUID_E="#CFE3F2","#2E6DA4"
C_HOT,C_TXT,C_DIM="#C0392B","#1F2933","#5A6672"

fig=plt.figure(figsize=(15.5,9.6),dpi=150,facecolor="white")
gs=fig.add_gridspec(2,2,width_ratios=[2.6,1.0],height_ratios=[1.0,0.95],
                    hspace=0.10,wspace=0.10,left=0.045,right=0.97,top=0.875,bottom=0.05)
fig.text(0.5,0.955,"Heated Thick-Walled Duct - Conjugate Heat Transfer and Thermo-Structural Response",
         ha="center",fontsize=16.5,fontweight="bold",color=C_TXT)
fig.text(0.5,0.921,"Flow Behavior and Thermal Effects in Multiphysics Systems   |   "
         "RE-ANALYSIS (2026) - parameters newly selected, not original internship values",
         ha="center",fontsize=10,color=C_HOT,style="italic")

# ---------------- LONGITUDINAL SECTION (radially exaggerated) ----------------
ax=fig.add_subplot(gs[0,0])
L=600.0; RS=5.0; ri,ro=10*RS,20*RS          # radial exaggeration for legibility
ax.add_patch(Rectangle((0,ri),L,ro-ri,fc=C_SOLID,ec=C_SOLID_E,lw=1.5,zorder=3))
ax.add_patch(Rectangle((0,-ro),L,ro-ri,fc=C_SOLID,ec=C_SOLID_E,lw=1.5,zorder=3))
ax.add_patch(Rectangle((0,-ri),L,2*ri,fc=C_FLUID,ec=C_FLUID_E,lw=1.5,zorder=2))
ax.axhline(0,color=C_DIM,lw=0.9,ls="-.",zorder=4)

for xq in np.linspace(30,L-30,12):
    ax.add_patch(FancyArrow(xq,ro+52,0,-44,width=3.0,head_width=13,head_length=13,
                            fc=C_HOT,ec=C_HOT,zorder=5,length_includes_head=True))
    ax.add_patch(FancyArrow(xq,-ro-52,0,44,width=3.0,head_width=13,head_length=13,
                            fc=C_HOT,ec=C_HOT,zorder=5,length_includes_head=True))
ax.text(L/2,ro+66,'q" = 8 000 W/m$^2$   uniform heat flux on outer surface',ha="center",
        fontsize=11,color=C_HOT,fontweight="bold")

ax.text(L/2,(ri+ro)/2,"SOLID WALL - Inconel 718  (conjugate domain)",ha="center",va="center",
        fontsize=10,color="white",fontweight="bold",zorder=6)
ax.text(L/2,-(ri+ro)/2,"SOLID WALL",ha="center",va="center",fontsize=9.5,color="white",
        fontweight="bold",zorder=6)
ax.text(L/2,ri*0.42,"AIR - turbulent internal flow",ha="center",va="center",fontsize=10.5,
        color=C_FLUID_E,fontweight="bold",zorder=6)

for yv in (-24,0,24):
    ax.add_patch(FancyArrow(-88,yv,58,0,width=2.6,head_width=11,head_length=15,
                            fc=C_FLUID_E,ec=C_FLUID_E,zorder=6,length_includes_head=True))
ax.text(-58,ro+18,"INLET",ha="center",fontsize=10.5,fontweight="bold",color=C_FLUID_E)
ax.text(-58,-ro-14,"velocity-inlet\n$V$ = 23.5 m/s\n$T$ = 300 K\n$Re_D$ = 30 000\n$I$ = 4.4 %",
        ha="center",va="top",fontsize=8.8,color=C_TXT)
ax.add_patch(FancyArrow(L+16,0,54,0,width=2.6,head_width=11,head_length=15,
                        fc=C_FLUID_E,ec=C_FLUID_E,zorder=6,length_includes_head=True))
ax.text(L+56,ro+18,"OUTLET",ha="center",fontsize=10.5,fontweight="bold",color=C_FLUID_E)
ax.text(L+56,-ro-14,"pressure-outlet\n0 Pa gauge\n$T_{out}\\approx$ 369 K\n$V_{out}\\approx$ 28.9 m/s",
        ha="center",va="top",fontsize=8.8,color=C_TXT)

ax.annotate("",xy=(0,-ro-108),xytext=(L,-ro-108),arrowprops=dict(arrowstyle="<->",color=C_DIM,lw=1.3))
ax.text(L/2,-ro-118,"L = 600 mm    (L/D = 30)",ha="center",va="top",fontsize=10,color=C_DIM)
ax.text(-146,-ro-96,"end faces: adiabatic",fontsize=8.6,color=C_DIM,style="italic",ha="left")
ax.text(L,-ro-90,"radially exaggerated 5x",ha="right",fontsize=8.2,color=C_DIM,style="italic")
ax.set_xlim(-150,L+125); ax.set_ylim(-ro-132,ro+88); ax.axis("off")
ax.set_title("Longitudinal section",fontsize=11.5,color=C_TXT,pad=4)

# ---------------- CROSS SECTION ----------------
ax2=fig.add_subplot(gs[0,1]); ri2,ro2=10,20
ax2.add_patch(Circle((0,0),ro2,fc=C_SOLID,ec=C_SOLID_E,lw=1.8,zorder=2))
ax2.add_patch(Circle((0,0),ri2,fc=C_FLUID,ec=C_FLUID_E,lw=1.8,zorder=3))
for th in np.linspace(0,2*np.pi,16,endpoint=False):
    x0,y0=(ro2+12)*np.cos(th),(ro2+12)*np.sin(th)
    ax2.add_patch(FancyArrow(x0,y0,-8.5*np.cos(th),-8.5*np.sin(th),width=0.8,head_width=3.2,
                             head_length=3.2,fc=C_HOT,ec=C_HOT,zorder=4,length_includes_head=True))
ax2.annotate("",xy=(-ri2,0),xytext=(ri2,0),arrowprops=dict(arrowstyle="<->",color=C_FLUID_E,lw=1.4))
ax2.text(0,1.8,"$D_i$ = 20",ha="center",fontsize=9.6,color=C_FLUID_E,fontweight="bold",zorder=6)
ax2.annotate("",xy=(0,-ri2),xytext=(0,-ro2),arrowprops=dict(arrowstyle="<->",color="white",lw=1.4))
ax2.text(1.5,-15.5,"t = 10",fontsize=9.6,color="white",fontweight="bold",zorder=6)
ax2.annotate("",xy=(0,ro2),xytext=(0,-ro2),arrowprops=dict(arrowstyle="<->",color=C_SOLID_E,lw=1.1,ls=":"))
ax2.text(-2.0,10,"$D_o$ = 40",fontsize=9.6,color="white",fontweight="bold",ha="right",zorder=6)
ax2.text(0,-ro2-17,"all dimensions mm\n(true scale)",ha="center",fontsize=8.6,color=C_DIM)
ax2.set_xlim(-38,38); ax2.set_ylim(-42,36); ax2.set_aspect("equal"); ax2.axis("off")
ax2.set_title("Cross-section",fontsize=11.5,color=C_TXT,pad=4)

# ---------------- PHYSICS CHAIN ----------------
ax3=fig.add_subplot(gs[1,:]); ax3.axis("off"); ax3.set_xlim(0,100); ax3.set_ylim(0,34)
ax3.add_patch(FancyBboxPatch((0.8,27.6),46.5,5.6,boxstyle="round,pad=0.3",fc="#EAF0F6",ec=C_FLUID_E,lw=1.0))
ax3.text(24.0,30.4,"Steady-state  |  incompressible ideal gas  |  buoyancy (Gr/Re$^2$=4e-5) and\n"
                   "viscous dissipation (Br=2e-3) both negligible",ha="center",va="center",fontsize=8.8,color=C_TXT)
ax3.add_patch(FancyBboxPatch((52.7,27.6),46.5,5.6,boxstyle="round,pad=0.3",fc="#FBEDEC",ec=C_HOT,lw=1.0))
ax3.text(75.9,30.4,"Target mesh ~170 000 cells  |  Fluent Student capped at 4-way parallel\n"
                   "Verified on this machine 2026-09-18",ha="center",va="center",fontsize=8.8,color=C_TXT)
steps=[("1. FLUID FLOW","Turbulent air\n$Re_D$ = 30 000 -> 25 500\nk-$\\omega$ SST, $y^+\\approx$ 1","#CFE3F2"),
       ("2. CONVECTION","$h\\approx$ 78 - 97 W/m$^2$K\n$Nu\\approx$ 50 - 62\nvs Dittus-Boelter / Gnielinski","#BFE0D2"),
       ("3. CONDUCTION","Conjugate in solid\n$\\Delta T_{wall}\\approx$ 7.2 K\n$T_{metal}\\approx$ 574 K (301 C)","#F2DFA8"),
       ("4. EXPANSION","$\\alpha\\approx$ 13.9e-6 /K\n$T_{ref}$ = 300 K\nbore grows 35 $\\mu$m","#F2C9A0"),
       ("5. STRESS","LC1 free:  16.5 MPa\nLC2 restrained: -668 MPa\nMoS 0.59 vs hot $S_y$","#E8B4AE")]
w,gap=16.4,3.55
for i,(t,b,col) in enumerate(steps):
    x0=0.8+i*(w+gap)
    ax3.add_patch(FancyBboxPatch((x0,7.6),w,16.4,boxstyle="round,pad=0.4",fc=col,ec=C_SOLID_E,lw=1.3))
    ax3.text(x0+w/2,20.7,t,ha="center",fontsize=10.4,fontweight="bold",color=C_TXT)
    ax3.text(x0+w/2,13.8,b,ha="center",va="center",fontsize=8.6,color=C_TXT)
    if i<4:
        ax3.add_patch(FancyArrow(x0+w+0.35,15.8,gap-1.1,0,width=1.0,head_width=2.8,head_length=1.5,
                                 fc=C_SOLID_E,ec=C_SOLID_E,length_includes_head=True))
ax3.annotate("",xy=(0.8,4.9),xytext=(55.6,4.9),arrowprops=dict(arrowstyle="-",color=C_FLUID_E,lw=2.2))
ax3.text(28.2,2.6,"ANSYS Fluent - conjugate heat transfer (fluid <-> solid, TWO-WAY)",
         ha="center",fontsize=9.4,color=C_FLUID_E,fontweight="bold")
ax3.annotate("",xy=(58.6,4.9),xytext=(99.2,4.9),arrowprops=dict(arrowstyle="-",color="#9B3A2F",lw=2.2))
ax3.text(78.9,2.6,"ONE-WAY thermal map  ->  ANSYS Mechanical (static structural)",
         ha="center",fontsize=9.4,color="#9B3A2F",fontweight="bold")

fig.savefig("ENGINEERING_SCHEMATIC.png",dpi=150,facecolor="white",bbox_inches="tight")
print("schematic written")
