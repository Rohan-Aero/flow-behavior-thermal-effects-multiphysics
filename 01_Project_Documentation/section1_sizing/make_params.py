from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

F="Arial"
H_FILL=PatternFill("solid",fgColor="1F3864"); H_FONT=Font(F,bold=True,color="FFFFFF",size=10)
CAT_FILL=PatternFill("solid",fgColor="D9E2F3"); CAT_FONT=Font(F,bold=True,size=10,color="1F3864")
IN_FILL=PatternFill("solid",fgColor="FFF2CC"); IN_FONT=Font(F,size=10,color="0000FF")
DER_FONT=Font(F,size=10); BASE=Font(F,size=10)
RED=Font(F,size=10,bold=True,color="C00000")
THIN=Side("thin",color="BFBFBF"); BOX=Border(THIN,THIN,THIN,THIN)
WRAP=Alignment(wrap_text=True,vertical="top"); CTR=Alignment("center","center",wrap_text=True)

wb=Workbook(); 

# ---------------------------------------------------------------- README
ws=wb.active; ws.title="README"
rows=[("PARAMETERS.xlsx  -  Section 1 Parameter Definition",0),
 ("Project: Flow Behavior and Thermal Effects in Multiphysics Systems",1),
 ("Original internship: Eleation, February - May 2025",1),("",0),
 ("RE-ANALYSIS NOTICE",2),
 ("The original internship files were lost. A filesystem sweep on 2026-09-18 confirmed no original artefact survives.",1),
 ("Every parameter in this workbook was newly selected in 2026. NONE of these are the original internship values.",1),
 ("No experimental or measured data appears anywhere in this workbook. Nothing here may be presented as recovered.",1),("",0),
 ("STATUS LEGEND",2),
 ("Re-analysed/Assumed  -  a present-day engineering choice made because the original value is unknowable.",1),
 ("Literature             -  a published material or fluid property, with the source named in column F.",1),
 ("Derived                -  computed from other parameters. See the Derived_Calcs sheet for the live formula.",1),
 ("Verified (this machine)-  measured by actually running the software on this computer on 2026-09-18.",1),("",0),
 ("HOW TO USE",2),
 ("Sheet 'Parameters'       - the full parameter table (Parameter / Value / Units / Source / Reason / Status).",1),
 ("Sheet 'Derived_Calcs'    - LIVE formulas. Edit only the yellow/blue INPUT cells; everything below recomputes.",1),
 ("Sheet 'Verification'     - the numbers the CFD and FEA must reproduce before any result is accepted.",1),("",0),
 ("Blue text on yellow fill = an input you may edit.  Black text = a formula; do not overwrite it.",1)]
for i,(t,k) in enumerate(rows,1):
    c=ws.cell(i,1,t)
    c.font=Font(F,bold=True,size=14,color="1F3864") if k==0 and i==1 else (RED if k==2 else Font(F,size=10))
ws.column_dimensions["A"].width=118

# ---------------------------------------------------------------- PARAMETERS
ws=wb.create_sheet("Parameters")
hdr=["Category","Parameter","Symbol","Value","Units","Source / Basis","Reason for selection","Status"]
for j,h in enumerate(hdr,1):
    c=ws.cell(1,j,h); c.font=H_FONT; c.fill=H_FILL; c.alignment=CTR; c.border=BOX
RA="Re-analysed/Assumed"; LI="Literature"; DV="Derived"; VF="Verified (this machine)"
P=[
("GEOMETRY","Inner (bore) diameter","Di",20,"mm","Re-analysed selection","Sets the flow scale. Gives Re=30,000 at a low-subsonic air velocity and is large enough to resolve a y+~1 boundary layer without an excessive cell count.",RA),
("GEOMETRY","Outer diameter","Do",40,"mm","Re-analysed selection","Chosen so Do/Di is exactly 2, making ln(Do/Di)=ln2 and keeping the thick-walled-cylinder closed-form thermal stress solution a clean validation target.",RA),
("GEOMETRY","Wall thickness","t",10,"mm","Derived: (Do-Di)/2","Thick enough to produce a measurable through-wall temperature gradient and a genuine 3-D conduction path, rather than a thin-shell approximation.",DV),
("GEOMETRY","Heated length","L",600,"mm","Re-analysed selection","L/D=30. The turbulent hydrodynamic entry length is ~18 D, so ~12 diameters of fully developed flow remain for correlation comparison.",RA),
("GEOMETRY","Length-to-diameter ratio","L/Di",30,"-","Derived","Long enough for fully developed flow; short enough to keep the mesh near 170k cells.",DV),
("FLUID","Working fluid","air","-","-","Re-analysed selection","Aerospace-relevant coolant (bleed / ram air). Well-documented properties. Deliberately a poor coolant, so metal temperature rather than air temperature drives material selection - a realistic engineering situation.",RA),
("FLUID","Density model","rho","incompressible ideal gas","-","Fluent material model","Density falls ~29% from 300 K to 403 K, but pressure varies only 0.5%. The pressure-independent ideal gas law is therefore the correct low-Mach model; full compressibility is unnecessary.",RA),
("FLUID","Inlet velocity","V_in",23.5,"m/s","Re-analysed selection, set to hit Re=30,000","Places the flow solidly in the turbulent regime where Dittus-Boelter and Gnielinski are both valid (Re>10^4), while keeping Mach at 0.07.",RA),
("FLUID","Inlet temperature","T_in",300,"K","Re-analysed selection","Standard ambient. Also used as the stress-free reference temperature, so thermal strain is measured from the as-assembled state.",RA),
("FLUID","Operating pressure","p_op",101325,"Pa","Standard sea-level atmosphere","Sea-level static condition.",RA),
("FLUID","Specific heat (constant)","cp",1009,"J/kg.K","Incropera Table A.4, air at 1 atm","Varies under 1.5% over 300-403 K, so a constant value is justified and simplifies the energy balance check.",LI),
("FLUID","Dynamic viscosity at 300 K","mu",1.846e-5,"Pa.s","Incropera Table A.4","Varies ~25% over the temperature range, so it is applied as temperature-dependent in Fluent.",LI),
("FLUID","Thermal conductivity at 350 K","k_air",0.03003,"W/m.K","Incropera Table A.4","Temperature-dependent in Fluent; the tabulated 350 K value anchors the hand calculation.",LI),
("FLUID","Prandtl number at 300 K","Pr",0.707,"-","Incropera Table A.4","Near-constant for air; within the validity range of both Nusselt correlations.",LI),
("SOLID","Material","Inconel 718","-","-","Special Metals alloy datasheet","Aerospace nickel superalloy. Its service temperature comfortably covers the computed 655 K metal temperature, and its high yield strength keeps BOTH structural load cases elastic, so a linear analysis stays valid throughout.",RA),
("SOLID","Density","rho_s",8190,"kg/m3","Special Metals datasheet","Standard published value.",LI),
("SOLID","Thermal conductivity at ~575 K","k_s",15.3,"W/m.K","Datasheet, interpolated to metal temperature","Deliberately low conductivity, which produces a measurable through-wall gradient rather than an isothermal wall.",LI),
("SOLID","Specific heat","cp_s",435,"J/kg.K","Special Metals datasheet","Not used in a steady-state solution; listed for completeness and for any future transient extension.",LI),
("SOLID","Young's modulus at ~555 K","E",188.5e9,"Pa","Datasheet, interpolated","Evaluated at operating temperature rather than room temperature, since stiffness falls ~8% over this range.",LI),
("SOLID","Poisson's ratio","nu",0.294,"-","Special Metals datasheet","Standard published value.",LI),
("SOLID","Mean CTE from 294 K","alpha",13.9e-6,"1/K","Datasheet, interpolated","Mean (not instantaneous) CTE is the correct quantity for a total thermal strain measured from the reference temperature.",LI),
("SOLID","Yield strength at ~555 K","Sy",1060e6,"Pa","Datasheet, interpolated","Hot yield, not room-temperature yield, is the correct basis for a margin of safety at operating temperature.",LI),
("BOUNDARY","Inlet condition","-","velocity-inlet, 23.5 m/s, 300 K","-","Re-analysed selection","A velocity inlet fixes the mass flow exactly (inlet density is fixed by T_in and p_op), which makes the global energy balance an exact validation check.",RA),
("BOUNDARY","Inlet turbulence","I",4.4,"%","I = 0.16*Re^(-1/8)","Standard empirical estimate for fully developed pipe flow; length scale set to the hydraulic diameter, 20 mm.",DV),
("BOUNDARY","Outlet condition","-","pressure-outlet, 0 Pa gauge","-","Re-analysed selection","Static pressure outlet is the standard, well-posed choice for subsonic internal flow discharging to ambient.",RA),
("BOUNDARY","Outer cylindrical surface","q''_o",8000,"W/m2","Re-analysed selection","Uniform heat flux gives a linear bulk temperature rise and a constant wall-to-bulk difference in the developed region - both exactly checkable against theory. Magnitude RE-SELECTED after the correlation-validity check: 12 kW/m2 pushed the restrained case past hot yield, and that verdict flipped with the correction exponent. 8 kW/m2 keeps BOTH load cases elastic under either treatment, so the conclusion is robust.",RA),
("BOUNDARY","End annular faces","-","adiabatic","-","Re-analysed selection","Isolates one-dimensional radial conduction and removes an arbitrary end-loss assumption that could not be justified.",RA),
("BOUNDARY","Fluid-solid interface","-","coupled (conjugate)","-","Fluent CHT","Wall temperature is solved, not prescribed. This is the core of the project: the solid and fluid thermal fields are computed simultaneously.",RA),
("BOUNDARY","Reference temperature","T_ref",300,"K","Matches inlet / assembly temperature","Defines the stress-free state, so computed thermal strain is physically meaningful.",RA),
("BOUNDARY","Structural load case 1","LC1","free axial growth","-","Re-analysed selection","Statically determinate restraint: isolates stress caused purely by temperature GRADIENTS.",RA),
("BOUNDARY","Structural load case 2","LC2","both ends axially fixed","-","Re-analysed selection","Fully restrained growth: isolates stress caused purely by RESTRAINT. Comparing LC1 and LC2 identifies the true design driver.",RA),
("NUMERICAL","Analysis type","-","steady-state","-","Re-analysed selection","Boundary conditions are time-invariant and the equilibrium thermal-stress state is what is sought. Start-up transients are a separate study.",RA),
("NUMERICAL","Turbulence model","-","k-omega SST","-","Re-analysed selection","Integrates to the wall without wall functions. Conjugate heat transfer is highly sensitive to near-wall resolution, because wall heat flux sets the solid temperature and hence the stress.",RA),
("NUMERICAL","Near-wall treatment","y+","<= 1","-","Re-analysed selection","Wall-resolved. Wall functions would introduce modelling error directly into the quantity of interest.",RA),
("NUMERICAL","First cell height","y1",12.1,"um","Derived from Petukhov friction factor","Sized to give y+ ~ 1 at inlet conditions, the most demanding station.",DV),
("NUMERICAL","Inflation layers","-",18,"-","Re-analysed selection","With growth ratio 1.2 gives a 1.55 mm prism stack, about 16% of the pipe radius.",RA),
("NUMERICAL","Coupling direction","-","one-way (CFD -> FEA)","-","Justified by deformation check","Free thermal growth of the bore is 29 um, changing flow area by 0.6% - far below turbulence-model uncertainty on Nu (5-15%). Two-way coupling would cost 5-10x the runtime for no meaningful change.",DV),
("NUMERICAL","Target mesh size","-",170000,"cells","Derived from mesh sizing calculation","Fits comfortably on 15.7 GB RAM and 4 cores; refined during the Section 4 mesh independence study.",DV),
("SOFTWARE","ANSYS release","-","2026 R1 (v261)","-","Verified on this machine 2026-09-18","Installed build. NOTE: the 2025 original would have used 2024 R2 / 2025 R1 - a version difference that must be disclosed.",VF),
("SOFTWARE","Fluent parallel limit","-",4,"cores","Fluent transcript: 'Your license enables 4-way parallel execution'","A hard Student-licence constraint measured directly, not assumed. Caps achievable mesh size and turnaround.",VF),
("SOFTWARE","Mechanical solver check","-","PASSED","-","MAPDL batch run 2026-09-18","Minimal thermal-stress case returned sigma = -240.000 MPa against an analytical -240 MPa. Solver licence confirmed.",VF),
("SOFTWARE","Fluent solver check","-","PASSED","-","Fluent batch run 2026-09-18","50-cell case read, initialised and ran 25 iterations with converging residuals. Solver licence confirmed.",VF),
]
r=2; last=None
for cat,name,sym,val,unit,src,why,st in P:
    if cat!=last:
        ws.cell(r,1,cat).font=CAT_FONT
        for j in range(1,9): ws.cell(r,j).fill=CAT_FILL; ws.cell(r,j).border=BOX
        r+=1; last=cat
    for j,v in enumerate([ "",name,sym,val,unit,src,why,st],1):
        c=ws.cell(r,j,v); c.font=RED if st==RA and j==8 else BASE
        c.alignment=WRAP; c.border=BOX
    r+=1
for col,w in zip("ABCDEFGH",[13,27,10,17,10,34,62,21]): ws.column_dimensions[col].width=w
ws.freeze_panes="B2"

# ---------------------------------------------------------------- DERIVED
ws=wb.create_sheet("Derived_Calcs")
ws.cell(1,1,"LIVE CALCULATION SHEET - edit ONLY the yellow INPUT cells; every value below is a formula").font=Font(F,bold=True,size=12,color="1F3864")
ws.cell(2,1,"This sheet is a SINGLE-POINT estimate using inlet (300 K) air properties. sizing_calculations.py marches along the duct with LOCAL properties and is the authoritative source for the Verification targets. Rows marked 'est.' differ from the marched values for that reason - the comparison block at the bottom shows both.").font=Font(F,size=9,italic=True)
for j,h in enumerate(["Quantity","Symbol","Value","Units","Formula / basis"],1):
    c=ws.cell(4,j,h); c.font=H_FONT; c.fill=H_FILL; c.alignment=CTR; c.border=BOX
INP=[("Inner diameter","Di",0.020,"m"),("Outer diameter","Do",0.040,"m"),("Heated length","L",0.600,"m"),
("Inlet velocity","V",23.5,"m/s"),("Inlet temperature","T_in",300.0,"K"),("Operating pressure","p_op",101325.0,"Pa"),
("Outer heat flux","q''_o",8000.0,"W/m2"),("Gas constant, air","R",287.058,"J/kg.K"),("Ratio of specific heats","gamma",1.4,"-"),
("Air specific heat","cp",1009.0,"J/kg.K"),("Air viscosity at 300 K","mu",1.846e-5,"Pa.s"),
("Air conductivity at 300 K","k_air",0.02624,"W/m.K"),("Air Prandtl number at 300 K","Pr",0.707,"-"),
("Solid conductivity at 575 K","k_s",15.3,"W/m.K"),("Solid Young's modulus at 555 K","E",188.5e9,"Pa"),
("Solid mean CTE","alpha",13.9e-6,"1/K"),("Solid Poisson ratio","nu",0.294,"-"),
("Solid yield at 555 K","Sy",1060e6,"Pa"),("Stress-free reference temp","T_ref",300.0,"K"),
("Volume-mean solid temp (corrected march)","T_s_mean",554.6,"K")]
ws.cell(5,1,"INPUTS").font=CAT_FONT; ws.cell(5,1).fill=CAT_FILL
r=6
for n,s,v,u in INP:
    ws.cell(r,1,n).font=BASE; ws.cell(r,2,s).font=BASE
    c=ws.cell(r,3,v); c.font=IN_FONT; c.fill=IN_FILL; c.number_format="General"
    ws.cell(r,4,u).font=BASE; ws.cell(r,5,"INPUT - edit me").font=Font(F,size=9,italic=True,color="808080")
    for j in range(1,6): ws.cell(r,j).border=BOX
    r+=1
D=dict(Di="C6",Do="C7",L="C8",V="C9",Tin="C10",pop="C11",qo="C12",R="C13",g="C14",cp="C15",
       mu="C16",ka="C17",Pr="C18",ks="C19",E="C20",al="C21",nu="C22",Sy="C23",Tref="C24",Tsm="C25")
r+=1
ws.cell(r,1,"DERIVED (formulas)").font=CAT_FONT; ws.cell(r,1).fill=CAT_FILL; r+=1
DER=[("Flow area","A_c",f"=PI()*({D['Di']}/2)^2","m2","pi*ri^2"),
("Inlet density","rho",f"={D['pop']}/({D['R']}*{D['Tin']})","kg/m3","ideal gas p/(RT)"),
("Mass flow rate","mdot",f"=C{r}*{D['V']}*C{r-1}" if False else None,"kg/s","rho*V*Ac")]
rows_def=[("Flow area","A_c",f"=PI()*({D['Di']}/2)^2","m2","pi*ri^2"),
("Inlet density","rho_in",f"={D['pop']}/({D['R']}*{D['Tin']})","kg/m3","ideal gas, p/(R*T)"),
("Mass flow rate","mdot","=RHO*VV*AC","kg/s","rho*V*A_c"),
("Reynolds number (inlet)","Re","=RHO*VV*DI/MU","-","rho*V*D/mu   -> turbulent if >4000"),
("Mach number (inlet)","M","=VV/SQRT(GG*RR*TIN)","-","V/sqrt(gamma*R*T)  -> incompressible if <0.3"),
("Outer surface area","A_o","=PI()*DO_*LL","m2","pi*Do*L"),
("Inner surface area","A_i","=PI()*DI*LL","m2","pi*Di*L"),
("Total heat input","Q","=QO*AO","W","q''_o * A_o"),
("Inner-surface heat flux","q''_i","=QQ/AI","W/m2","Q/A_i  (= q''_o * Do/Di)"),
("Linear heat rate","q'","=QQ/LL","W/m","Q/L"),
("Bulk temperature rise","dT_b","=QQ/(MD*CP)","K","Q/(mdot*cp)  - energy balance"),
("Outlet bulk temperature","T_out","=TIN+DTB","K","T_in + dT_b"),
("Darcy friction factor","f","=1/(0.790*LN(RE)-1.64)^2","-","Petukhov correlation"),
("Nusselt - Dittus-Boelter","Nu_DB","=0.023*RE^0.8*PR^0.4","-","0.023*Re^0.8*Pr^0.4 (heating)"),
("Nusselt - Gnielinski","Nu_G","=((FF/8)*(RE-1000)*PR)/(1+12.7*SQRT(FF/8)*(PR^(2/3)-1))","-","Gnielinski, more accurate at moderate Re"),
("Convective coefficient (inlet-property est.)","h","=NUG*KA/DI","W/m2.K","Nu*k/D  (Gnielinski)"),
("Wall-to-bulk dT (inlet-property est.)","dT_conv","=QI/HH","K","q''_i / h"),
("Through-wall temp difference","dT_wall","=QP*LN((DO_/2)/(DI/2))/(2*PI()*KS)","K","cylindrical conduction q'*ln(ro/ri)/(2*pi*k)"),
("Inner wall temp at exit (upper-bound est.)","T_wi","=TOUT+DTC","K","T_out + dT_conv"),
("Outer wall temp at exit (upper-bound est.)","T_wo","=TWI+DTW","K","T_wi + dT_wall"),
("Wall shear stress","tau_w","=FF/8*RHO*VV^2","Pa","(f/8)*rho*V^2"),
("Friction velocity","u_tau","=SQRT(TAU/RHO)","m/s","sqrt(tau_w/rho)"),
("First cell height for y+=1","y1","=(MU/RHO)/UT","m","nu/u_tau"),
("Hydrodynamic entry length","L_h","=1.359*DI*RE^0.25","m","turbulent entry correlation"),
("LC1 gradient stress (scale estimate)","sig_1","=AL*EE*DTW/(2*(1-NU))","Pa","alpha*E*dT_wall/(2(1-nu)) - thick cylinder scale"),
("LC2 restrained axial stress","sig_2","=-EE*AL*(TSM-TREF)","Pa","-E*alpha*(T_mean - T_ref), fully restrained"),
("LC2 utilisation of yield","ratio","=ABS(SIG2)/SY","-","|sigma|/Sy   - must stay below 1.0"),
("LC2 margin of safety","MoS","=SY/ABS(SIG2)-1","-","Sy/|sigma| - 1"),
("Free radial growth of bore","dr","=AL*(TSM-TREF)*(DI/2)","m","alpha*dT*ri"),
("Flow area change","dA","=((DI/2+DR)^2-(DI/2)^2)/(DI/2)^2*100","%","justifies ONE-WAY coupling if small")]
first=r; addr={}
for i,(n,s,f_,u,b) in enumerate(rows_def): addr[s]=f"C{first+i}"
rep={"DI":D['Di'],"DO_":D['Do'],"LL":D['L'],"VV":D['V'],"TIN":D['Tin'],"PO":D['pop'],"QO":D['qo'],
"RR":D['R'],"GG":D['g'],"CP":D['cp'],"MU":D['mu'],"KA":D['ka'],"PR":D['Pr'],"KS":D['ks'],
"EE":D['E'],"AL":D['al'],"NU":D['nu'],"SY":D['Sy'],"TREF":D['Tref'],"TSM":D['Tsm'],
"AC":addr["A_c"],"RHO":addr["rho_in"],"MD":addr["mdot"],"RE":addr["Re"],"AO":addr["A_o"],
"AI":addr["A_i"],"QQ":addr["Q"],"QI":addr["q''_i"],"QP":addr["q'"],"DTB":addr["dT_b"],
"TOUT":addr["T_out"],"FF":addr["f"],"NUG":addr["Nu_G"],"HH":addr["h"],"DTC":addr["dT_conv"],
"DTW":addr["dT_wall"],"TWI":addr["T_wi"],"TAU":addr["tau_w"],"UT":addr["u_tau"],
"SIG2":addr["sig_2"],"DR":addr["dr"]}
import re
for i,(n,s,f_,u,b) in enumerate(rows_def):
    for k in sorted(rep,key=len,reverse=True): f_=re.sub(r'\b'+k+r'\b',rep[k],f_)
    ws.cell(r,1,n).font=BASE; ws.cell(r,2,s).font=BASE
    c=ws.cell(r,3,f_); c.font=DER_FONT; c.number_format="0.000000E+00" if "y1" in s else "0.0000"
    ws.cell(r,4,u).font=BASE; ws.cell(r,5,b).font=Font(F,size=9,color="404040")
    for j in range(1,6): ws.cell(r,j).border=BOX; ws.cell(r,j).alignment=WRAP
    r+=1

r+=1
ws.cell(r,1,"SINGLE-POINT ESTIMATE  vs  MARCHED SOLUTION (sizing_calculations.py)").font=CAT_FONT
ws.cell(r,1).fill=CAT_FILL; r+=1
for j,h in enumerate(["Quantity","This sheet (inlet props)","Marched (local props)","Units","Why they differ"],1):
    c=ws.cell(r,j,h); c.font=Font(F,bold=True,size=9); c.fill=PatternFill("solid",fgColor="EDEDED"); c.border=BOX
r+=1
CMP=[("Nusselt (Gnielinski)","70.5 at inlet","70.7 inlet -> 61.9 exit (const-prop)","-","Re falls 29,957 -> 25,548 as viscosity rises with temperature."),
("Nusselt, property-corrected","n/a","49.6 at exit","-","Nu*(Tb/Tw)^0.5 correction for the large wall-to-bulk dT. See ASSUMPTIONS.md A-006."),
("Convective coefficient h","92.5","92.7 inlet -> 97.2 exit; 77.9 corrected","W/m2.K","k_air rises with temperature faster than Nu falls; correction then reduces h ~20%."),
("Wall-to-bulk dT","173","164.6 const-prop; 205.4 corrected","K","Single-point uses inlet h with exit bulk T. The corrected value is the one to expect from CFD."),
("Inner wall temp at exit","542","533.5 const-prop; 574.3 corrected","K","Use the CORRECTED value as the verification target."),
("LC1 peak stress","13.6 (scale formula)","17.0 const-prop; 16.5 corrected (exact thick cylinder)","MPa","alpha*E*dT/(2(1-nu)) is a magnitude estimate; the Timoshenko solution is exact and ~22% higher."),
("LC2 axial stress","-667","-539 const-prop; -668 corrected","MPa","Driven by volume-mean solid temperature, which the correction raises by ~48 K.")]
for row in CMP:
    for j,v in enumerate(row,1):
        c=ws.cell(r,j,v); c.font=Font(F,size=9); c.alignment=WRAP; c.border=BOX
    r+=1

for col,w in zip("ABCDE",[34,22,24,11,56]): ws.column_dimensions[col].width=w

# ---------------------------------------------------------------- VERIFICATION
ws=wb.create_sheet("Verification")
ws.cell(1,1,"VERIFICATION TARGETS - the CFD and FEA must reproduce these before any result is accepted").font=Font(F,bold=True,size=12,color="1F3864")
ws.cell(2,1,"Values from sizing_calculations.py (1-D march, local air properties). Hand calculation FIRST, simulation SECOND.").font=Font(F,size=9,italic=True)
for j,h in enumerate(["Check","Analytical target","Units","Acceptance criterion","Why it matters"],1):
    c=ws.cell(4,j,h); c.font=H_FONT; c.fill=H_FILL; c.alignment=CTR; c.border=BOX
V=[("Global energy balance","603.2","W","within 0.5%","If Q_in does not equal mdot*cp*dT_b, the solution is not converged or the BCs are wrong. This is the single hardest pass/fail test."),
("Outlet bulk temperature","368.9","K","within 3%","Fixed by the energy balance and INDEPENDENT of the heat transfer coefficient, so it is the most robust scalar check."),
("Fully developed Nu (x/D>18)","49.6 corrected  |  61.9-66.8 constant-property","-","accept 44-67; expect near 50","Validates turbulence model and near-wall mesh. The wide band is honest: constant-property correlations are outside their validity range here (see ASSUMPTIONS A-006)."),
("Darcy friction factor","0.0241","-","within 10%","Independent check on momentum and near-wall resolution, separate from heat transfer."),
("Total pressure drop","412 (263 friction + 149 acceleration)","Pa","within 15%","Confirms the thermal-acceleration term is captured, not just friction."),
("Peak inner wall temperature","574.3 corrected (533.5 uncorrected)","K","within 5% of corrected","Drives material selection and the entire stress field. Expect CFD near the corrected value."),
("Through-wall temperature drop","7.2","K","within 10%","Validates the conjugate conduction path through the solid."),
("y+ on the fluid-solid wall","<= 1 target, < 5 acceptable","-","checked post-solve","If y+ is too large the wall heat flux is modelled rather than resolved, and the solid temperature is unreliable."),
("LC1 peak von Mises","16.5","MPa","within 15% of thick-cylinder closed form","Validates the thermal-stress mapping and the FEA itself."),
("LC2 axial stress","-668","MPa","within 10% of -E*alpha*dT","Validates restraint modelling and confirms the result stays elastic."),
("LC2 utilisation of hot yield","0.63","-","must stay below 1.0","If it reaches 1.0 the linear-elastic result is invalid and plasticity is required."),
("LC2 margin of safety","0.59","-","must be > 0","Robust to the correction exponent: 0.98 uncorrected, 0.59 corrected. Both positive."),
("LC2 / LC1 stress ratio","~40x","-","order of magnitude","The central finding: restraint dominates the through-wall gradient."),
("Mesh independence","<3% change in Nu and peak T","-","across 3 mesh levels","Without this, no result is defensible regardless of how well it matches a correlation.")]
r=5
for row in V:
    for j,v in enumerate(row,1):
        c=ws.cell(r,j,v); c.font=BASE; c.alignment=WRAP; c.border=BOX
    r+=1
for col,w in zip("ABCDE",[32,40,9,34,70]): ws.column_dimensions[col].width=w
ws.freeze_panes="A5"

wb.save("<SCRATCH_ROOT>/calc/PARAMETERS.xlsx")
print("workbook written")
