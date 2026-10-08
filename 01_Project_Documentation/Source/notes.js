// Speaker notes for the Section 10C-1 presentation (RE-ANALYSIS 2026).
// Each note: what the audience sees, the engineering point, the number that matters, and the transition.
module.exports = {
1: `[~40 s] Good morning. This is my internship project at Eleation, February to May 2025: flow behaviour and thermal effects in a multiphysics system.

The picture is the system itself — an Inconel 718 duct, 600 mm long, cooled by air inside and heated outside. Simple geometry, but it couples turbulent flow, conjugate heat transfer and thermo-structural response, up to buckling.

One point up front: the original internship files were not retained, so the geometry, set-up and results come from a documented re-analysis in ANSYS, carried out after the internship. Every number traces to an audited dataset, and I will be explicit about what the model can and cannot claim.

Transition: first, the context and the tools.`,

2: `[~35 s] The internship was at Eleation from February to May 2025, during my B.Tech in Aerospace Engineering at Dayananda Sagar University; the domain is multiphysics simulation.

On the right, the ANSYS Workbench chain: SpaceClaim for the geometry, Fluent for flow and heat transfer, Mechanical for thermal stress and linear buckling. The only data passed between the solvers is the temperature field.

The box at the bottom notes how the analysis record was produced. The analysis ran on the ANSYS Student licence, whose 128,000-node structural limit matters later.

Transition: so what exactly is the engineering problem?`,

3: `[~55 s] Read the schematic from left to right. Air enters at 300 K and 23.5 m/s. The outer surface receives a uniform 8000 W/m². That heat conducts through the 10 mm Inconel wall, is convected into the air, and the air carries it out of the duct.

The engineering point is the chain along the bottom. A hot wall wants to grow. If the duct is free, it simply gets longer. If both ends are held axially, that growth is prevented and turns into axial compression — and a long, compressed tube can buckle sideways.

So the questions are linked: how hot does the wall get, how much stress does the restraint create, and how close is the restrained duct to instability. Steps one to three run in Fluent, four to seven in Mechanical, linked by a one-way temperature transfer.

Transition: that gives the six objectives.`,

4: `[~35 s] Six objectives, in the order the workflow answers them.

One and two are the physics: the flow and the thermal field in the wall.

Three and four are about trusting those results: an independent analytical model built before any mesh existed, and mesh studies on both the CFD side and the structural side.

Five and six are the structural questions: how much stress free versus restrained expansion produces, and how the stability depends on the supports and on velocity, heat flux and wall thickness.

I will close the loop on each of these in the findings slide.

Transition: the geometry.`,

5: `[~40 s] The drawing is the longitudinal section: a straight duct, 20 mm bore, 40 mm outside diameter — so a 10 mm wall — and 600 mm long.

It is modelled as two bodies that share one cylindrical interface: the fluid domain, air, in blue, and the solid domain, Inconel 718, in grey. Because the interface topology is shared, the mesh is conformal, and heat passes directly from solid cells to fluid cells with no interpolation.

Heat enters only through the outer cylindrical wall, the red arrows; the end faces are adiabatic. Flow runs from z equals 0 to 600 mm. The end face on the right is drawn from the exported SpaceClaim geometry.

Transition: how the CFD was set up on this geometry.`,

6: `[~50 s] Top row: the workflow, ending in a conjugate heat transfer solution — the energy equation is solved in the air and in the Inconel wall together.

The solver is pressure-based, steady and coupled, with energy on. Turbulence is k-omega SST on a wall-resolved mesh: the first cell sits inside the viscous sublayer, y-plus at most 0.585, so no wall functions are used.

The key modelling choice is on the right: the interface temperature is not imposed — it is part of the solution. The boundary conditions are the baseline: 23.5 m/s and 300 K at the inlet, zero gauge pressure at the outlet, 8000 W/m² on the outer wall, adiabatic ends. The run was staged — flow, then energy, then second-order schemes.

Transition: which mesh, and how do I know it converged?`,

7: `[~55 s] Three meshes built from the same scripted topology: coarse 51,840 cells, medium 159,840, fine 500,580.

The number that matters: from medium to fine, the pressure drop changes by 0.23 % and the maximum solid temperature by 1.75 K. Richardson extrapolation puts the medium mesh 4.4 K above the extrapolated 558.13 K, so its error is small and on the hotter, conservative side. The observed order is 1.2 to 1.6, so I call this approximately convergent — I do not claim strict mesh independence.

The medium mesh became the baseline for a second, practical reason: the fine solid would need about 157 thousand structural nodes, above the 128,000-node limit.

On the right, the residual history: converged at 600, confirmed at 700, with mass and energy imbalances at round-off level.

Transition: what the converged solution shows.`,

8: `[~55 s] Four numbers summarise the baseline, all on the medium mesh: pressure drop 438.13 Pa, outlet bulk temperature 368.93 K, 602.755 W into the air, and a maximum solid temperature of 562.58 K on the outer wall at the outlet end.

The charts explain them. Left: the air accelerates along the duct — the area is constant, but the air heats and its density falls. Middle: the static pressure falls steeply at the inlet, where the boundary layer is thin, then almost linearly. Right: the air heats linearly, as a uniform flux requires, while the wall runs far above it.

Look at the gap between the inner and outer wall curves: at mid-span it is only 7.58 K. The metal conducts well; the air film carries most of the thermal resistance.

Transition: can these numbers be trusted?`,

9: `[~60 s] Before any mesh existed I built an independent analytical model from standard correlations, so this table compares two independent models of the same duct.

Reynolds number matches because it is fixed by the mass flux. The heat input differs by 0.071 %, which is exactly the area ratio of the 48-sided CFD cross-section: a geometric effect, not a modelling error. The pressure drop agrees within 0.77 %, but for partly compensating reasons: friction is lower in the CFD because the heated gas changes its properties, while the flow-development term is higher.

The largest difference is the maximum solid temperature: 19.1 K lower in the CFD — 15.0 K from the higher heat-transfer coefficient in the developing flow and 4.2 K from axial conduction in the wall, which a one-dimensional model cannot see.

Neither model was adjusted to match the other — and this is verification, not experimental validation: there are no measurements.

Transition: moving the temperature field into the structure.`,

10: `[~50 s] The structural model imports its temperature from Fluent. Left column: Fluent field, mapping with mesh-based external data and shape functions, then the Mechanical model, with zero thermal strain at 300 K.

The coupling is one-way: temperature goes from CFD to the structure and nothing comes back. That is justified because the wall deformation changes the flow area by only 0.70 % — this is not a two-way FSI model.

The quality numbers: all 108,252 structural nodes received a temperature, the mapped range matches the source range, and against an exact shape-function evaluation the error is at most 0.081 K inside the source mesh. The picture compares Fluent cell values with mapped Mechanical node values in the wall — they are practically identical.

Transition: what that temperature field does to the structure.`,

11: `[~55 s] Two load cases, same temperature field, different supports.

Left, LC1: the duct is held just enough to stop rigid-body motion, so it expands freely — about 1.844 mm — and the only stress comes from the temperature gradients: a peak of 24.28 MPa.

Right, LC2: both end faces are held axially — support S1. The same growth is now prevented. That creates an end force of 548.94 kN, a mean axial stress of minus 582.44 MPa, and a local peak von Mises stress of 605.16 MPa at the outer edge of the inlet face.

The engineering message is in the box: in a hot, thick-walled duct, the restraint — not the gradient — creates the stress; at mid-span the restrained stress is 32 times the free one. The peak is 57.8 % of the local yield strength, so the static state is elastic.

Transition: that much compression raises the stability question.`,

12: `[~65 s] A tube carrying 548.94 kN of compression must be checked for buckling, so I ran a linear eigenvalue buckling analysis on the LC2 pre-stress.

For support S1 the first eigenvalue is 1.108: the idealised model bifurcates at 1.108 times the thermal load — a critical load of 608.25 kN. The picture is mode 1 from the side: a whole-duct sideways sway, the ends moving in opposite directions while their rotation is held — a guided column. The colours are a normalised eigenvector, so the amplitude has no physical meaning.

Compare with the first-yield factor of 1.730: in this idealised model elastic bifurcation comes before first yield, so the S1 model is stability-limited and close to instability.

Just as important is what 1.108 is not. It belongs to a perfectly straight, elastic tube with idealised supports. Real tubes have imperfections and plasticity, which lower the capacity. So it is not a collapse load and not a factor of safety.

Transition: how strongly this depends on the supports.`,

13: `[~50 s] Same duct, same thermal load, three idealised end conditions, arranged by increasing end restraint.

S1, the baseline, lets the ends sway: λ1 = 1.108. S3 clamps one end and pins the other: 2.232. S2 clamps both ends: 4.300.

The static peak stress is identical in all three — 605.16 MPa. Only the stability changes, by a factor of 3.9. The governing mechanism changes too: under S1 bifurcation comes first; under S3 and S2 first yield comes first.

I deliberately do not rank these. The real support of the duct is not defined, and this slide shows that its lateral and rotational stiffness controls the stability conclusion more than anything else in the model.

Transition: the operating and design parameters.`,

"13a": `[~55 s] The linear eigenvalue result belongs to a perfectly straight, elastic tube. To see how a duct with a small initial out-of-straightness behaves as the thermal load rises, I added a geometrically nonlinear buckling analysis in ANSYS LS-DYNA. It is a follow-on extension of the project, not part of the original internship work, and the Mechanical result remains the reference.

First I verified the LS-DYNA model against Mechanical: same mesh, same mapped Fluent temperatures, same S1 supports. The static peak is 605.160 against 605.161 MPa, and the linear buckling factor 1.1095, 0.13 % from Mechanical.

Then I seeded the first buckling mode with three numerical amplitudes — 0.1, 0.6 and 1.2 mm. These are sensitivity values, not manufacturing tolerances. A perfect-geometry run serves as reference, and the temperature rise was raised to 1.3 times the operating field. The picture shows the 1.2 mm case: the whole duct sways sideways, ends in opposite directions, with no local mode.

Transition: what the imperfection size changes.`,

"13b": `[~55 s] The three cases represent small, medium and large numerical imperfections of the same mode shape.

The imperfection size decides when the duct starts to bend. The response leaves the perfect path — axial force 1 % below the perfect case — at λ 1.070 for 0.1 mm, 0.825 for 0.6 mm and already 0.375 for 1.2 mm. At the operating field, λ = 1, the axial force falls from 552.2 to 503.5 kN and the peak stress rises from 690 to 1104 MPa as the amplitude grows.

On the right of the chart the curves are normalised by the critical load and the initial sway, and they collapse onto one curve: a single global mode, amplified by the imperfection.

Transition: how this compares with the Mechanical buckling result.`,

"13c": `[~60 s] Here is the comparison with Mechanical. Southwell plots of the three load paths give a characteristic load of 607.7 to 612.3 kN, against the Mechanical critical load of 608.25 kN at λ1 = 1.108. So the characteristic global buckling load is relatively insensitive to the tested amplitudes, while the deformation and stress response is strongly imperfection-sensitive. The 0.1 mm case reaches a maximum of 601.0 kN at λ 1.185; the other two are still rising at λ 1.3.

This is not a factor of safety, and it is not experimental validation: it is a second numerical model of the same idealised problem.

The material model is elastic, because the project has no defensible temperature-dependent plastic stress-strain curve for Inconel 718. The peak stress reaches the local yield estimate at λ 1.109, 1.031 and 0.974 — the 1.2 mm case slightly before λ = 1 — so the later parts of the curves lie outside the elastic range and are not a collapse prediction. The perfect-geometry run does not identify a bifurcation load, so the Mechanical eigenvalue remains the reference.

Transition: back to the main study — the parametric study.`,

14: `[~45 s] The parametric study moves one factor at a time around the baseline P00: inlet velocity plus and minus 10 %, outer-wall heat flux plus and minus 10 %, and wall thickness 8 and 12 mm.

For thickness the total heat input is held constant, so the flux is rescaled; otherwise a thicker wall would simply receive more heat and hide the cross-section effect.

The important point is on the right: every case is a full chain — its own converged CFD, its own temperature mapping, LC1 and LC2 statics and a buckling analysis, all with support S1. No screening estimate or interpolation enters the results, and a control case repeated the baseline and reproduced it.

One-factor-at-a-time cannot show interactions; I come back to that in the limitations.

Transition: the results.`,

15: `[~60 s] Nine charts, three per variable; the middle point is always the baseline.

Top row, velocity: it acts mainly on the cooling and the pressure drop. Minus 10 % velocity lowers the pressure drop by 13.3 % and the air leaves hotter; λ1 follows the wall temperature and falls to 1.003.

Middle row, heat flux: this is the thermal load itself. The maximum solid temperature moves by about 28 K each way, the LC2 stress by minus 11.0 and plus 11.2 %, and at plus 10 % flux λ1 drops below 1, to 0.988.

Bottom row, thickness at constant total heat: the temperatures barely move and the deformation changes by about half a percent, but the critical load changes by minus 36.6 and plus 49.3 %, and the 8 mm wall has λ1 = 0.945.

For the two cases below 1, the static stresses are pre-buckling equilibrium results.

Transition: what all of this adds up to.`,

16: `[~50 s] Six findings, each traced to the final engineering audit.

One: restraint dominates the thermal stress. Two: the idealised baseline is stability-limited — λ1 of 1.108 sits below the first-yield factor. Three: the end support controls that conclusion — 1.108 to 4.300 at the same stress. Four: heat flux drives temperature and stress directly. Five: thickness acts on stiffness and buckling capacity, not on temperature.

Six links back to the verification objectives: the numerical uncertainty is small compared with the modelling uncertainty. Mesh effects are 4.4 K on the CFD side and below 5 × 10⁻⁴ on the structural side, and the fluid pressure load is negligible — while the support definition changes λ1 by a factor of 3.9.

Transition: the limits of these statements.`,

17: `[~45 s] The limitations are part of the result.

This is a re-analysis with no experimental data, so the model is verified, not validated. The supports are idealised, and the buckling analysis is linear: no imperfections, no plasticity, no post-buckling path. The additional LS-DYNA extension covers only the elastic, geometrically nonlinear part, with numerical imperfections. The material model has temperature-dependent stiffness and expansion but no inelastic stress-strain data, and Poisson's ratio is an assumption. The parametric study is one-factor-at-a-time, and the CFD model form — for example the turbulence model — was not varied.

The future work follows directly from that list: measure the wall temperatures and pressure drop on a rig, characterise the real support stiffness, run an imperfection-sensitive nonlinear buckling analysis with inelastic data, and examine turbulence and radiation modelling where it is justified.

Transition: to conclude.`,

18: `[~35 s] To conclude. Within an idealised numerical model, the chain from flow to stability is complete and checked at every step.

The CFD is converged and verified, with a maximum solid temperature of 562.58 K. Restraint turns thermal growth into a 605.16 MPa local peak stress. The idealised S1 duct is stability-limited at λ1 = 1.108, and the end restraint controls that conclusion.

What the work does not show is that a real component is structurally adequate — that would need the real supports, imperfections, inelastic behaviour and measurements.

Thank you. I am happy to take questions.`,
};
