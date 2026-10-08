// =====================================================================================================
// Section 10C-1 - final technical presentation (RE-ANALYSIS 2026)
// Flow Behavior and Thermal Effects in Multiphysics Systems
// Builds Final/Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx with pptxgenjs.
// Chart data are read from Tables/slide_data.json (generated from 11_Final_Audit/MASTER_PROJECT_DATA.csv by
// scripts/build_slide_data.py); images are the cropped project figures in Figures/ (scripts/prepare_slide_figures.py).
// Speaker notes are in notes.js. Usage: node build_deck.js
// =====================================================================================================
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const NOTES = require("./notes.js");

const ROOT = path.resolve(__dirname, "..");
const FIG = (f) => path.join(ROOT, "Figures", f);
const D = JSON.parse(fs.readFileSync(path.join(ROOT, "Tables", "slide_data.json"), "utf8"));
const OUT = path.join(ROOT, "Final", "Flow_Behavior_Thermal_Effects_Multiphysics_Presentation.pptx");

// ---------------------------------------------------------------- palette and type
const C = {
  navy: "14213D", steel: "2F5D8A", heat: "D9480F", amber: "F59F00", ice: "EEF3F8", line: "C9D3DE",
  text: "243447", muted: "6B7C93", white: "FFFFFF", slate: "5C6B7A", pale: "F7F9FB", sky: "CFE0F1", grey: "9AA5B1",
};
const F = "Calibri";
const W = 13.333, H = 7.5, MX = 0.5;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Rohan Balram Patel";
pres.company = "Eleation internship (Feb-May 2025)";
pres.title = "Flow Behavior and Thermal Effects in Multiphysics Systems";
pres.subject = "CFD, conjugate heat transfer and thermo-structural analysis of a heated cylindrical duct";

// ---------------------------------------------------------------- helpers
// keep a number together with its unit at line breaks (non-breaking space)
const UNITS = "(K|Pa|MPa|kN|mm|W|m/s|W/m²|%|kg/m³|GPa|cells|nodes|iterations)";
const nbspStr = (t) => t.replace(new RegExp("(\\d) " + UNITS + "(?![A-Za-z])", "g"), "$1\u00A0$2").replace(/ \/ /g, "\u00A0/ ");
const nbsp = (t) => typeof t === "string" ? nbspStr(t) : Array.isArray(t) ? t.map((r) => (r && typeof r.text === "string" ? { ...r, text: nbspStr(r.text) } : r)) : t;
let slideNo = 0;
function newSlide(dark = false, foot = "R. B. Patel  ·  Eleation internship project (Feb–May 2025)") {
  const s = pres.addSlide();
  slideNo += 1;
  const _addText = s.addText.bind(s), _addTable = s.addTable.bind(s);
  s.addText = (t, o) => _addText(nbsp(t), o);
  s.addTable = (rows, o) => _addTable(rows.map((r) => r.map((c) => (typeof c === "string" ? nbspStr(c) : c && typeof c.text === "string" ? { ...c, text: nbspStr(c.text) } : c))), o);
  s.background = { color: dark ? C.navy : C.white };
  s.slideNumber = { x: W - 1.0, y: H - 0.42, w: 0.5, h: 0.3, fontFace: F, fontSize: 10, color: dark ? "AFC3D9" : C.muted, align: "right" };
  if (!dark) {
    s.addText(foot, {
      x: MX, y: H - 0.42, w: 8.5, h: 0.3, fontFace: F, fontSize: 9, color: C.muted, margin: 0, isTextBox: true,
    });
  }
  return s;
}
function title(s, t, kicker) {
  s.addText(t, { x: MX, y: 0.3, w: W - 2 * MX, h: 0.62, fontFace: F, fontSize: 30, bold: true, color: C.navy, margin: 0, isTextBox: true, valign: "middle" });
  if (kicker) {
    s.addText(kicker, { x: MX, y: 0.94, w: W - 2 * MX, h: 0.42, fontFace: F, fontSize: 16, color: C.steel, italic: true, margin: 0, isTextBox: true, valign: "middle" });
  }
}
function card(s, x, y, w, h, fill = C.ice, lineColor = null) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: lineColor ? { color: lineColor, width: 0.75 } : { type: "none" } });
}
function stat(s, x, y, w, h, value, unit, label, sub, color = C.heat) {
  card(s, x, y, w, h);
  s.addText([
    { text: value, options: { fontSize: 26, bold: true, color } },
    { text: unit ? "  " + unit : "", options: { fontSize: 15, bold: true, color } },
  ], { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: h * 0.5, fontFace: F, margin: 0, valign: "bottom", isTextBox: true });
  s.addText(label, { x: x + 0.15, y: y + h * 0.55, w: w - 0.3, h: h * 0.24, fontFace: F, fontSize: 13, bold: true, color: C.text, margin: 0, valign: "top", isTextBox: true });
  if (sub) s.addText(sub, { x: x + 0.15, y: y + h * 0.77, w: w - 0.3, h: h * 0.2, fontFace: F, fontSize: 11, color: C.muted, margin: 0, valign: "top", isTextBox: true });
}
function circleNum(s, x, y, d, n, fill = C.navy, fs = 16) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" } });
  s.addText(String(n), { x, y, w: d, h: d, fontFace: F, fontSize: fs, bold: true, color: C.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function arrowRight(s, x, y, w, color = C.grey) {
  s.addShape(pres.shapes.RIGHT_ARROW, { x, y, w, h: 0.28, fill: { color }, line: { type: "none" } });
}
function arrowDown(s, x, y, h, color = C.grey) {
  s.addShape(pres.shapes.DOWN_ARROW, { x, y, w: 0.34, h, fill: { color }, line: { type: "none" } });
}
function caption(s, t, x, y, w, h = 0.3, align = "left") {
  s.addText(t, { x, y, w, h, fontFace: F, fontSize: 11, color: C.muted, italic: true, margin: 0, align, valign: "top", isTextBox: true });
}
function img(s, file, x, y, w, h) {
  s.addImage({ path: FIG(file), x, y, w, h });
}
function imgW(s, file, x, y, w, pxW, pxH) { // keep the aspect ratio of the cropped project figure
  const h = w * pxH / pxW;
  s.addImage({ path: FIG(file), x, y, w, h });
  return h;
}
const v = (k) => D.values[k].value;
const fmt = (x, d) => x.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const axisFont = { valAxisLabelFontFace: F, catAxisLabelFontFace: F, titleFontFace: F, dataLabelFontFace: F, legendFontFace: F };

// ================================================================= SLIDE 1 - TITLE
{
  const s = newSlide(true);
  s.addText("INTERNSHIP PROJECT  ·  FINAL TECHNICAL PRESENTATION", { x: 0.6, y: 0.7, w: 7.4, h: 0.35, fontFace: F, fontSize: 12, bold: true, color: C.amber, charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Flow Behavior and Thermal Effects in Multiphysics Systems", { x: 0.6, y: 1.15, w: 7.2, h: 1.75, fontFace: F, fontSize: 38, bold: true, color: C.white, margin: 0, valign: "top", isTextBox: true });
  s.addText("CFD, Conjugate Heat Transfer and Thermo-Structural Analysis of a Heated Cylindrical Duct", { x: 0.6, y: 2.95, w: 7.0, h: 0.85, fontFace: F, fontSize: 18, color: "CADCFC", margin: 0, valign: "top", isTextBox: true });
  s.addText([
    { text: "Rohan Balram Patel", options: { fontSize: 20, bold: true, color: C.white, breakLine: true } },
    { text: "B.Tech Aerospace Engineering  ·  Dayananda Sagar University, Bengaluru", options: { fontSize: 15, color: "DDE6F0", breakLine: true } },
    { text: "Internship: Eleation  ·  February – May 2025", options: { fontSize: 15, color: "DDE6F0" } },
  ], { x: 0.6, y: 4.2, w: 7.3, h: 1.2, fontFace: F, margin: 0, valign: "top", paraSpaceAfter: 4, isTextBox: true });
  // CAD render in a white card
  card(s, 8.15, 1.25, 4.6, 2.95, C.white);
  const hh = imgW(s, "cad_3d_interface.png", 8.3, 1.75, 4.3, 490, 175);
  s.addText("SpaceClaim CAD: air passage (blue) inside the Inconel 718 duct, Ø20 / Ø40 × 600 mm", { x: 8.35, y: 1.75 + hh + 0.2, w: 4.2, h: 0.55, fontFace: F, fontSize: 11, color: C.muted, margin: 0, align: "center", isTextBox: true });
  // compact re-analysis note
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.85, w: 12.15, h: 0.8, rectRadius: 0.08, fill: { color: "1E2F52" }, line: { color: "3B5078", width: 0.75 } });
  s.addText([
    { text: "Numerical analysis  ", options: { bold: true, color: C.amber } },
    { text: "ANSYS Workbench, ANSYS Fluent and ANSYS Mechanical", options: { color: "DDE6F0" } },
  ], { x: 0.8, y: 5.9, w: 11.8, h: 0.7, fontFace: F, fontSize: 13, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(NOTES[1]);
}

// ================================================================= SLIDE 2 - CONTEXT
{
  const s = newSlide();
  title(s, "Internship and Project Context", "A multiphysics simulation study: one heated duct, three coupled physics, one ANSYS tool chain");
  // left: internship facts
  card(s, MX, 1.6, 6.1, 3.9);
  const rows = [
    ["Organisation", "Eleation"],
    ["Period", "February – May 2025"],
    ["Engineer", "Rohan Balram Patel, B.Tech Aerospace Engineering, Dayananda Sagar University, Bengaluru"],
    ["Domain", "Multiphysics simulation: CFD, conjugate heat transfer, thermo-structural and stability analysis"],
    ["Project", "Flow Behavior and Thermal Effects in Multiphysics Systems"],
  ];
  let y = 1.8;
  rows.forEach(([k, t], i) => {
    const h = i === 2 ? 0.98 : i >= 3 ? 0.8 : 0.5;
    s.addText(k, { x: MX + 0.25, y, w: 1.55, h, fontFace: F, fontSize: 14, bold: true, color: C.steel, margin: 0, valign: "top", isTextBox: true });
    s.addText(t, { x: MX + 1.85, y, w: 4.0, h, fontFace: F, fontSize: 14, color: C.text, margin: 0, valign: "top", isTextBox: true });
    y += h;
  });
  // right: tool chain inside Workbench
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.95, y: 1.6, w: 5.88, h: 3.9, rectRadius: 0.08, fill: { color: C.white }, line: { color: C.line, width: 1, dashType: "dash" } });
  s.addText("ANSYS Workbench project", { x: 7.15, y: 1.72, w: 5.4, h: 0.4, fontFace: F, fontSize: 15, bold: true, color: C.navy, margin: 0, isTextBox: true });
  const tools = [["SpaceClaim", "geometry: fluid + solid bodies, shared interface", C.slate],
                 ["Fluent", "turbulent flow + conjugate heat transfer", C.steel],
                 ["Mechanical", "thermal stress + linear buckling", C.heat]];
  tools.forEach(([n, d, col], i) => {
    const yy = 2.25 + i * 1.02;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.2, y: yy, w: 1.85, h: 0.72, rectRadius: 0.08, fill: { color: col }, line: { type: "none" } });
    s.addText(n, { x: 7.2, y: yy, w: 1.85, h: 0.72, fontFace: F, fontSize: 16, bold: true, color: C.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(d, { x: 9.2, y: yy, w: 3.45, h: 0.72, fontFace: F, fontSize: 14, color: C.text, valign: "middle", margin: 0, isTextBox: true });
    if (i < 2) arrowDown(s, 7.95, yy + 0.74, 0.26);
  });
  s.addText("Temperature field: Fluent → Mechanical (one-way)", { x: 7.2, y: 5.12, w: 5.4, h: 0.3, fontFace: F, fontSize: 12, italic: true, color: C.muted, margin: 0, isTextBox: true });
  // bottom: re-analysis note (verbatim)
  card(s, MX, 5.75, W - 2 * MX, 1.05, "FFF4E6");
  s.addText([
    { text: "Note on the analysis record.  ", options: { bold: true, color: C.heat } },
    { text: "The original internship project files were not retained. The geometry, simulation set-up and numerical results presented here come from a re-analysis of the internship problem, carried out after the internship with ANSYS Workbench, Fluent and Mechanical.", options: { color: C.text } },
  ], { x: MX + 0.25, y: 5.8, w: W - 2 * MX - 0.5, h: 0.95, fontFace: F, fontSize: 14, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(NOTES[2]);
}

// ================================================================= SLIDE 3 - ENGINEERING PROBLEM
{
  const s = newSlide();
  title(s, "The Engineering Problem", "Air cools a heated Inconel duct — and the hot wall, if restrained, is pushed towards buckling");
  // duct schematic (not to scale)
  const x0 = 1.2, x1 = 11.1, yT = 2.3, wall = 0.46, bore = 1.05;
  // restraints
  [x0 - 0.42, x1].forEach((xx) => s.addShape(pres.shapes.RECTANGLE, { x: xx, y: yT - 0.1, w: 0.42, h: 2 * wall + bore + 0.2, fill: { color: "D5DBE3" }, line: { color: C.slate, width: 1 } }));
  s.addShape(pres.shapes.RECTANGLE, { x: x0, y: yT, w: x1 - x0, h: wall, fill: { color: "A9B4C2" }, line: { color: C.slate, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: x0, y: yT + wall + bore, w: x1 - x0, h: wall, fill: { color: "A9B4C2" }, line: { color: C.slate, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: x0, y: yT + wall, w: x1 - x0, h: bore, fill: { color: "DCEBF8" }, line: { color: "7FA8D1", width: 0.75 } });
  for (let k = 0; k < 3; k++) arrowRight(s, x0 + 1.4 + k * 3.0, yT + wall + bore / 2 - 0.14, 1.3, C.steel);
  for (let k = 0; k < 12; k++) {
    const xx = x0 + 0.35 + k * 0.82;
    s.addShape(pres.shapes.DOWN_ARROW, { x: xx, y: yT - 0.42, w: 0.2, h: 0.36, fill: { color: C.heat }, line: { type: "none" } });
    s.addShape(pres.shapes.UP_ARROW, { x: xx, y: yT + 2 * wall + bore + 0.06, w: 0.2, h: 0.36, fill: { color: C.heat }, line: { type: "none" } });
  }
  s.addText("q″ = 8000 W/m² on the outer wall", { x: 3.5, y: 1.47, w: 5.2, h: 0.32, fontFace: F, fontSize: 14, bold: true, color: C.heat, align: "center", margin: 0, isTextBox: true });
  s.addText("Air in: 300 K, 23.5 m/s", { x: x0 + 0.1, y: yT + wall + 0.08, w: 2.6, h: 0.3, fontFace: F, fontSize: 13, bold: true, color: C.navy, margin: 0, isTextBox: true });
  s.addText("Inconel 718 wall, t = 10 mm", { x: x1 - 3.3, y: yT + wall + bore + wall + 0.45, w: 3.2, h: 0.3, fontFace: F, fontSize: 13, color: C.text, align: "right", margin: 0, isTextBox: true });
  s.addText("ends held axially (restrained case)", { x: x0 - 0.45, y: yT + 2 * wall + bore + 0.45, w: 3.6, h: 0.3, fontFace: F, fontSize: 12, italic: true, color: C.muted, margin: 0, isTextBox: true });
  s.addText("schematic, not to scale", { x: x1 + 0.55, y: yT + 0.4, w: 1.2, h: 0.6, fontFace: F, fontSize: 10, italic: true, color: C.muted, margin: 0, isTextBox: true });
  // physics chain
  const chain = ["Internal turbulent flow", "Convective heat transfer", "Conduction through the wall", "Thermal expansion", "Thermal stress", "Axial compression under restraint", "Possible buckling"];
  const cx0 = MX, gap = 0.15, mid = 0.6, cw = (W - 2 * MX - 5 * gap - mid) / 7, cy = 5.2;
  const cxAt = (i) => cx0 + i * (cw + gap) + (i >= 3 ? mid - gap : 0);
  chain.forEach((t, i) => {
    const xx = cxAt(i);
    const col = i < 3 ? C.steel : C.heat;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: xx, y: cy, w: cw, h: 1.15, rectRadius: 0.08, fill: { color: i < 3 ? "E3EDF7" : "FCE9DF" }, line: { type: "none" } });
    circleNum(s, xx + 0.08, cy + 0.08, 0.36, i + 1, col, 13);
    s.addText(t, { x: xx + 0.1, y: cy + 0.46, w: cw - 0.2, h: 0.64, fontFace: F, fontSize: 13, bold: true, color: C.text, margin: 0, valign: "top", isTextBox: true });
  });
  arrowRight(s, cxAt(2) + cw + 0.08, cy + 0.44, mid - 0.16, C.grey);
  s.addText("Fluent — CFD + conjugate heat transfer", { x: cx0, y: cy + 1.22, w: 3 * cw + 2 * gap, h: 0.32, fontFace: F, fontSize: 13, bold: true, color: C.steel, align: "center", margin: 0, isTextBox: true });
  s.addText("Mechanical — static stress + linear buckling", { x: cxAt(3), y: cy + 1.22, w: 4 * cw + 3 * gap, h: 0.32, fontFace: F, fontSize: 13, bold: true, color: C.heat, align: "center", margin: 0, isTextBox: true });
  s.addText("one-way temperature transfer", { x: cxAt(2) + cw - 0.9, y: cy - 0.36, w: mid + 1.8, h: 0.3, fontFace: F, fontSize: 11, italic: true, color: C.muted, align: "center", margin: 0, isTextBox: true });
  s.addNotes(NOTES[3]);
}

// ================================================================= SLIDE 4 - OBJECTIVES
{
  const s = newSlide();
  title(s, "Objectives", "Six questions, in the order the simulation chain answers them");
  const obj = [
    ["Characterise the flow", "Pressure drop, velocity development and wall resolution of turbulent air in the heated duct"],
    ["Determine the thermal response", "Conjugate heat transfer: how hot the Inconel wall gets, and where"],
    ["Verify the CFD against analytical estimates", "Independent correlation-based baseline, built before any mesh; mass and energy conservation"],
    ["Establish mesh sensitivity", "Three CFD meshes with Richardson extrapolation; seven structural meshes"],
    ["Evaluate the thermo-structural response", "Free thermal expansion (LC1) versus axially restrained expansion (LC2)"],
    ["Investigate stability and parameter effects", "Linear buckling, end-support sensitivity, and a velocity / heat-flux / thickness study"],
  ];
  const cw = 5.95, ch = 1.45;
  obj.forEach(([h, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * (cw + 0.4), y = 1.65 + row * (ch + 0.25);
    card(s, x, y, cw, ch);
    circleNum(s, x + 0.25, y + 0.3, 0.62, i + 1, i < 4 ? C.steel : C.heat, 20);
    s.addText(h, { x: x + 1.1, y: y + 0.18, w: cw - 1.3, h: 0.45, fontFace: F, fontSize: 17, bold: true, color: C.navy, margin: 0, valign: "middle", isTextBox: true });
    s.addText(d, { x: x + 1.1, y: y + 0.65, w: cw - 1.3, h: 0.7, fontFace: F, fontSize: 14, color: C.text, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes(NOTES[4]);
}

// ================================================================= SLIDE 5 - GEOMETRY
{
  const s = newSlide();
  title(s, "Geometry and Baseline", "Two bodies — air passage and Inconel 718 wall — sharing one conformal cylindrical interface");
  const hd = imgW(s, "drawing_longitudinal.png", MX, 1.65, 8.1, 2220, 736);
  caption(s, "Section 3 engineering drawing, longitudinal section (dimensions in mm; conventional break)", MX, 1.65 + hd + 0.05, 8.1);
  // domain legend
  const leg = [
    ["DCEBF8", "7FA8D1", "Fluid domain — air (incompressible ideal gas)"],
    ["A9B4C2", "5C6B7A", "Solid domain — Inconel 718 annulus"],
    [C.heat, C.heat, "Heated outer wall — q″ = 8000 W/m²; end faces adiabatic"],
    ["FFFFFF", "2F7FD1", "Fluid–solid interface — Ø20, shared (conformal) topology"],
    [C.steel, C.steel, "Flow direction — inlet z = 0 → outlet z = 600 mm"],
  ];
  leg.forEach(([fill, ln, t], i) => {
    const col = i < 3 ? 0 : 1, row = i < 3 ? i : i - 3;
    const x = MX + col * 4.15, y = 5.05 + row * 0.5;
    s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.07, w: 0.32, h: 0.24, fill: { color: fill }, line: { color: ln, width: 1.5 } });
    s.addText(t, { x: x + 0.45, y, w: 3.6, h: 0.4, fontFace: F, fontSize: 13, color: C.text, margin: 0, valign: "middle", isTextBox: true });
  });
  // right: cross-section + dimensions
  imgW(s, "cad_cross_section.png", 9.25, 1.55, 3.2, 720, 715);
  caption(s, "End face drawn from the exported SpaceClaim geometry", 8.95, 4.78, 3.9, 0.3, "center");
  const dims = [["Inner diameter  Dᵢ", "20 mm"], ["Outer diameter  Dₒ", "40 mm"], ["Wall thickness  t", "10 mm"], ["Length  L", "600 mm"]];
  card(s, 8.95, 5.15, 3.88, 1.72);
  dims.forEach(([k, val], i) => {
    s.addText(k, { x: 9.15, y: 5.25 + i * 0.39, w: 2.2, h: 0.36, fontFace: F, fontSize: 14, color: C.text, margin: 0, valign: "middle", isTextBox: true });
    s.addText(val, { x: 11.3, y: 5.25 + i * 0.39, w: 1.35, h: 0.36, fontFace: F, fontSize: 15, bold: true, color: C.heat, align: "right", margin: 0, valign: "middle", isTextBox: true });
  });
  s.addNotes(NOTES[5]);
}

// ================================================================= SLIDE 6 - CFD METHODOLOGY
{
  const s = newSlide();
  title(s, "CFD Methodology", "A steady conjugate heat transfer model: energy is solved in the air and in the Inconel wall together");
  const steps = [["Geometry", "SpaceClaim: 2 bodies, shared interface"], ["Mesh", "hexahedral O-grid, wall-resolved"], ["Fluent set-up", "materials, BCs, staged solution"],
                 ["CHT solution", "conjugate heat transfer: flow + energy in air and wall"], ["Results + checks", "conservation, analytical, mesh study"]];
  const sw = 2.2, sg = 0.32;
  steps.forEach(([h, d], i) => {
    const x = MX + i * (sw + sg);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.7, w: sw, h: 1.25, rectRadius: 0.08, fill: { color: i === 3 ? C.steel : C.ice }, line: { type: "none" } });
    s.addText(h, { x: x + 0.1, y: 1.76, w: sw - 0.2, h: 0.5, fontFace: F, fontSize: 15, bold: true, color: i === 3 ? C.white : C.navy, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(d, { x: x + 0.1, y: 2.3, w: sw - 0.2, h: 0.6, fontFace: F, fontSize: 12, color: i === 3 ? "E6EEF6" : C.text, align: "center", valign: "top", margin: 0, isTextBox: true });
    if (i < 4) arrowRight(s, x + sw + 0.03, 2.18, 0.26);
  });
  const cols = [
    ["Solver", ["Pressure-based, steady, coupled", "Energy equation on", "Staged: flow → energy → second-order schemes", "Converged at 600, confirmed at 700 iterations"]],
    ["Physics", ["Turbulence: k–ω SST", "Wall-resolved: y⁺ ≤ 0.585, no wall functions", "Air: ideal gas, temperature-dependent properties", "Inconel 718: k(T), cₚ(T)"]],
    ["Boundary conditions", ["Inlet: 23.5 m/s, 300 K", "Outlet: 0 Pa gauge", "Outer wall: q″ = 8000 W/m²; ends adiabatic", "Interface: coupled — temperature solved, not imposed"]],
  ];
  cols.forEach(([h, items], i) => {
    const x = MX + i * 4.18, w = 3.9;
    card(s, x, 3.35, w, 3.3, C.white, C.line);
    s.addText(h, { x: x + 0.25, y: 3.47, w: w - 0.5, h: 0.45, fontFace: F, fontSize: 18, bold: true, color: i === 2 ? C.heat : C.steel, margin: 0, isTextBox: true });
    s.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })),
      { x: x + 0.25, y: 3.98, w: w - 0.45, h: 2.6, fontFace: F, fontSize: 16, color: C.text, margin: 0, valign: "top", paraSpaceAfter: 8, isTextBox: true });
  });
  s.addNotes(NOTES[6]);
}

// ================================================================= SLIDE 7 - MESH AND CONVERGENCE
{
  const s = newSlide();
  title(s, "Mesh and Convergence", "Three systematically refined meshes; the medium mesh carries the results downstream");
  const iw = 8.1, pxw = 1790;
  const ih = imgW(s, "mesh_family.png", MX, 2.05, iw, 1790, 577);
  const cen = [(98 + 595) / 2, (683 + 1181) / 2, (1269 + 1772) / 2].map((p) => MX + p * iw / pxw);
  const lab = [["Coarse", "51,840 cells", C.slate], ["Medium — baseline", "159,840 cells", C.heat], ["Fine — reference", "500,580 cells", C.slate]];
  lab.forEach(([a, b, col], i) => {
    s.addText([{ text: a, options: { bold: true, color: col, breakLine: true } }, { text: b, options: { color: C.text } }],
      { x: cen[i] - 1.3, y: 1.45, w: 2.6, h: 0.58, fontFace: F, fontSize: 14, align: "center", valign: "bottom", margin: 0, isTextBox: true });
  });
  caption(s, "CFD mesh cross-sections (fluid core, graded near-wall layers, solid wall); axes in mm", MX, 2.05 + ih + 0.02, iw);
  card(s, MX, 4.95, iw, 1.9);
  s.addText("Why the medium mesh", { x: MX + 0.25, y: 5.02, w: 4, h: 0.4, fontFace: F, fontSize: 16, bold: true, color: C.navy, margin: 0, isTextBox: true });
  const why = ["Medium → fine: Δp +0.23 %, maximum solid temperature −1.75 K",
               "Medium is 4.4 K above the Richardson-extrapolated 558.13 K: small and conservative",
               "Approximately convergent (apparent order 1.2–1.6); strict mesh independence not claimed",
               "Fine solid would need ≈157 k structural nodes, beyond the 128,000-node licence limit"];
  s.addText(why.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < why.length - 1 } })),
    { x: MX + 0.25, y: 5.42, w: iw - 0.45, h: 1.38, fontFace: F, fontSize: 14, color: C.text, margin: 0, valign: "top", paraSpaceAfter: 2, isTextBox: true });
  // convergence
  const cx = 8.95, cwid = 3.88;
  const chh = imgW(s, "convergence_residuals.png", cx, 1.5, cwid, 705, 702);
  card(s, cx, 1.5 + chh + 0.12, cwid, 6.85 - (1.5 + chh + 0.12));
  s.addText([
    { text: "Baseline run converged", options: { bold: true, color: C.navy, breakLine: true } },
    { text: "iteration 600, confirmed at 700", options: { color: C.text, breakLine: true } },
    { text: "mass imbalance 7.0 × 10⁻¹³ %", options: { color: C.text, breakLine: true } },
    { text: "energy imbalance 3.1 × 10⁻¹¹ %", options: { color: C.text } },
  ], { x: cx + 0.2, y: 1.5 + chh + 0.18, w: cwid - 0.4, h: 6.85 - (1.5 + chh + 0.24), fontFace: F, fontSize: 13, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(NOTES[7]);
}

// ================================================================= SLIDE 8 - BASELINE CFD RESULTS
{
  const s = newSlide();
  title(s, "Baseline CFD Results", "The air film carries most of the thermal resistance: the wall runs far hotter than the air");
  const st = [[fmt(v("dp"), 2), "Pa", "Pressure drop", "inlet – outlet, area-weighted"],
              [fmt(v("Tout"), 2), "K", "Outlet bulk temperature", "mass-weighted"],
              [fmt(v("Q"), 3), "W", "Heat-transfer rate", "through the heated wall"],
              [fmt(v("Tmax"), 2), "K", "Maximum solid temperature", "outer wall, outlet end"]];
  st.forEach((a, i) => stat(s, MX + i * 3.13, 1.55, 2.95, 1.2, a[0], a[1], a[2], a[3], i === 3 ? C.heat : C.steel));
  const P = D.profiles;
  const base = { x: 0, y: 2.95, w: 4.0, h: 3.9, lineSize: 2.25, lineDataSymbol: "none", catAxisMinVal: 0, catAxisMaxVal: 600, catAxisMajorUnit: 100,
                 showCatAxisTitle: true, catAxisTitle: "z [mm]", catAxisTitleFontSize: 12, catAxisLabelFontSize: 12, valAxisLabelFontSize: 12,
                 showTitle: true, titleFontSize: 14, titleColor: C.navy, valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
                 catAxisLabelColor: C.text, valAxisLabelColor: C.text, legendFontSize: 12, ...axisFont };
  s.addChart(pres.charts.SCATTER, [{ name: "z", values: P.z }, { name: "centreline (max)", values: P.w_max }, { name: "section bulk", values: P.w_b }],
    { ...base, x: MX, title: "Axial velocity [m/s]", chartColors: [C.steel, "8FB3D9"], showLegend: true, legendPos: "b", valAxisMinVal: 20, valAxisMaxVal: 36, valAxisMajorUnit: 4 });
  s.addChart(pres.charts.SCATTER, [{ name: "z", values: P.z }, { name: "static pressure", values: P.p_area }],
    { ...base, x: MX + 4.15, title: "Static pressure [Pa gauge]", chartColors: [C.slate], showLegend: false, valAxisMinVal: 0, valAxisMaxVal: 450, valAxisMajorUnit: 100 });
  s.addChart(pres.charts.SCATTER, [{ name: "z", values: P.z }, { name: "outer wall", values: P.Two }, { name: "inner wall", values: P.Twi }, { name: "air (bulk)", values: P.Tb_mass }],
    { ...base, x: MX + 8.3, title: "Temperature [K]", chartColors: [C.heat, C.amber, C.steel], showLegend: true, legendPos: "b", valAxisMinVal: 280, valAxisMaxVal: 600, valAxisMajorUnit: 40 });
  s.addNotes(NOTES[8]);
}

// ================================================================= SLIDE 9 - VERIFICATION
{
  const s = newSlide();
  title(s, "CFD Verification: Analytical vs CFD", "Two independent models of the same duct — the differences are explained, not tuned away");
  const hdr = ["Quantity", "Analytical (Section 2)", "CFD (medium mesh)", "Difference", "Main reason"];
  const H_ = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 14 } });
  const rows = [
    ["Inlet Reynolds number", "29,957", fmt(v("Re_in_cfd"), 0), "< 0.01 %", "same mass flux and inlet state"],
    ["Pressure drop [Pa]", fmt(v("dp_an"), 2), fmt(v("dp"), 2), "−0.77 %", "friction lower (gas heating); flow-development term higher"],
    ["Outlet bulk temperature [K]", fmt(v("Tout_an"), 2), fmt(v("Tout"), 2), "+0.08 K", "faceting of the 48-sided CFD section"],
    ["Heat-transfer rate [W]", fmt(v("Q_an"), 3), fmt(v("Q"), 3), "−0.071 %", "exactly the 48-gon lateral-area ratio"],
    ["Maximum solid temperature [K]", fmt(v("Tmax_an"), 2), fmt(v("Tmax"), 2), "−19.1 K", "higher film coefficient in developing flow (−15.0 K); axial wall conduction (−4.2 K)"],
  ];
  const tb = [hdr.map(H_)].concat(rows.map((r, i) => r.map((c, j) => ({ text: c, options: {
    fontSize: 14, color: j === 3 ? C.heat : C.text, bold: j === 0 || j === 3, fill: { color: i % 2 ? C.white : C.pale },
    align: j >= 1 && j <= 3 ? "center" : "left" } }))));
  s.addTable(tb, { x: MX, y: 1.6, w: W - 2 * MX, colW: [2.95, 2.1, 2.0, 1.3, 3.98], rowH: 0.56, fontFace: F, valign: "middle",
    border: { type: "solid", pt: 0.75, color: C.line }, margin: [0.04, 0.1, 0.04, 0.1] });
  const why = [["Correlations", "Gnielinski / Petukhov with a property-ratio correction"], ["Property variation", "gas heating changes density and viscosity along the duct"],
               ["Developing flow", "thin entrance boundary layer, high local h"], ["Conjugate conduction", "axial heat flow in the wall, absent in 1-D"],
               ["Faceting", "48-sided CFD section vs true circle"]];
  why.forEach(([h, d], i) => {
    const x = MX + i * 2.49, w = 2.33;
    card(s, x, 5.2, w, 1.12);
    s.addText(h, { x: x + 0.12, y: 5.26, w: w - 0.24, h: 0.36, fontFace: F, fontSize: 14, bold: true, color: C.steel, margin: 0, isTextBox: true });
    s.addText(d, { x: x + 0.12, y: 5.62, w: w - 0.24, h: 0.66, fontFace: F, fontSize: 12, color: C.text, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("This is verification against an independent model and conservation checks — not experimental validation: no measurements exist.", { x: MX, y: 6.45, w: W - 2 * MX, h: 0.35, fontFace: F, fontSize: 14, bold: true, color: C.heat, margin: 0, isTextBox: true });
  s.addNotes(NOTES[9]);
}

// ================================================================= SLIDE 10 - THERMAL FIELD TO MECHANICAL
{
  const s = newSlide();
  title(s, "Thermal Field to Mechanical", "One-way coupling: the converged solid temperature field becomes the structural load");
  const bx = MX, bw = 3.85;
  const box = (y, h, head, sub, fill, fc) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y, w: bw, h, rectRadius: 0.08, fill: { color: fill }, line: { type: "none" } });
    s.addText(head, { x: bx + 0.2, y: y + 0.08, w: bw - 0.4, h: 0.38, fontFace: F, fontSize: 16, bold: true, color: fc, margin: 0, isTextBox: true });
    s.addText(sub, { x: bx + 0.2, y: y + 0.45, w: bw - 0.4, h: 0.4, fontFace: F, fontSize: 13, color: fc === C.white ? "E6EEF6" : C.text, margin: 0, valign: "top", isTextBox: true });
  };
  box(1.6, 0.92, "Fluent temperature field", "converged CHT solution, medium mesh", C.steel, C.white);
  arrowDown(s, bx + bw / 2 - 0.17, 2.56, 0.3);
  box(2.9, 0.92, "Temperature mapping", "mesh-based External Data, shape functions", C.ice, C.navy);
  arrowDown(s, bx + bw / 2 - 0.17, 3.86, 0.3);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y: 4.2, w: bw, h: 2.65, rectRadius: 0.08, fill: { color: "FCE9DF" }, line: { type: "none" } });
 s.addText("Mechanical model  ·  T_ref = 300 K", { x: bx + 0.2, y: 4.27, w: bw - 0.4, h: 0.38, fontFace: F, fontSize: 15, bold: true, color: C.heat, margin: 0, isTextBox: true });
  imgW(s, "mech_imported_temperature.png", bx + 0.2, 4.7, bw - 0.4, 1556, 872);
  // right: comparison image + metrics
  const rx = 4.65, rw = W - MX - rx;
  s.addText("Wall temperature, r = 10–20 mm (radial scale exaggerated): Fluent cells (top) vs mapped Mechanical nodes (bottom)", { x: rx, y: 1.55, w: rw, h: 0.32, fontFace: F, fontSize: 12, italic: true, color: C.muted, margin: 0, isTextBox: true });
  const mw = 7.0, mh = imgW(s, "mapping_fluent_vs_mechanical.png", rx + (rw - mw) / 2, 1.9, mw, 1760, 800);
  const my = 1.9 + mh + 0.15;
  const met = [["108,252 / 108,252", "structural nodes mapped"], ["423.84 – 562.56 K", "mapped range (source 423.84 – 562.54 K)"], ["≤ 0.081 K", "interpolation error inside the source mesh"]];
  met.forEach(([a, b], i) => {
    const x = rx + i * (rw / 3), w = rw / 3 - 0.15;
    card(s, x, my, w, 0.98);
    s.addText(a, { x: x + 0.12, y: my + 0.06, w: w - 0.24, h: 0.46, fontFace: F, fontSize: 19, bold: true, color: C.heat, margin: 0, valign: "middle", isTextBox: true });
    s.addText(b, { x: x + 0.12, y: my + 0.52, w: w - 0.24, h: 0.42, fontFace: F, fontSize: 12, color: C.text, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("Not a two-way FSI model: the wall deformation changes the flow area by only 0.70 %, so no feedback to the flow is needed.", { x: rx, y: my + 1.08, w: rw, h: 0.6, fontFace: F, fontSize: 14, bold: true, color: C.navy, margin: 0, valign: "top", isTextBox: true });
  s.addNotes(NOTES[10]);
}

// ================================================================= SLIDE 11 - THERMO-STRUCTURAL RESPONSE
{
  const s = newSlide();
  title(s, "Thermo-Structural Response", "Free expansion produces little stress; preventing the same growth produces large compression");
  const col = (x, head, sub, imA, imB, stats, color) => {
    s.addText(head, { x, y: 1.55, w: 5.95, h: 0.42, fontFace: F, fontSize: 19, bold: true, color, margin: 0, isTextBox: true });
    s.addText(sub, { x, y: 1.95, w: 5.95, h: 0.32, fontFace: F, fontSize: 13, color: C.muted, margin: 0, isTextBox: true });
    const w2 = 2.9;
    const h2 = imgW(s, imA, x, 2.35, w2, 1556, 872);
    imgW(s, imB, x + w2 + 0.15, 2.35, w2, 1556, 872);
    caption(s, "total deformation", x, 2.35 + h2 + 0.02, w2, 0.28, "center");
    caption(s, "von Mises stress", x + w2 + 0.15, 2.35 + h2 + 0.02, w2, 0.28, "center");
    stats.forEach(([a, u, b], i) => {
      const cw = stats.length === 2 ? 2.9 : 1.9, xx = x + i * (cw + 0.12);
      card(s, xx, 4.4, cw, 1.15);
      s.addText([{ text: a, options: { fontSize: 22, bold: true, color } }, { text: " " + u, options: { fontSize: 14, bold: true, color } }],
        { x: xx + 0.12, y: 4.46, w: cw - 0.24, h: 0.55, fontFace: F, margin: 0, valign: "middle", isTextBox: true });
      s.addText(b, { x: xx + 0.12, y: 5.0, w: cw - 0.24, h: 0.5, fontFace: F, fontSize: 12, color: C.text, margin: 0, valign: "top", isTextBox: true });
    });
  };
  col(MX, "LC1 — free thermal expansion", "statically determinate support: the duct grows freely", "mech_LC1_deformation.png", "mech_LC1_vonmises.png",
      [["1.844", "mm", "maximum deformation (outlet end)"], ["24.28", "MPa", "maximum von Mises stress"]], C.steel);
  col(6.88, "LC2 — axially restrained (support S1)", "both end faces held axially: the growth is prevented", "mech_LC2_deformation.png", "mech_LC2_vonmises.png",
      [["0.135", "mm", "maximum deformation"], ["605.16", "MPa", "peak von Mises (inlet-face edge)"], ["548.94", "kN", "end force; mean axial −582.44 MPa"]], C.heat);
  card(s, MX, 5.8, W - 2 * MX, 1.0, "FFF4E6");
  s.addText([
    { text: "Restraint, not the through-wall gradient, dominates the thermal stress: ", options: { bold: true, color: C.navy } },
    { text: "32× the free-expansion stress at mid-span. The LC2 peak is 57.8 % of the local yield strength, so the static state is elastic.", options: { color: C.text } },
  ], { x: MX + 0.25, y: 5.85, w: W - 2 * MX - 0.5, h: 0.9, fontFace: F, fontSize: 15, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(NOTES[11]);
}

// ================================================================= SLIDE 12 - BUCKLING
{
  const s = newSlide();
  title(s, "Buckling of the Restrained Duct", "Linear eigenvalue buckling on the LC2 thermal pre-stress, baseline support S1");
  // flow chips
  const chip = (x, t, fill, fc) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.55, w: 3.3, h: 0.62, rectRadius: 0.08, fill: { color: fill }, line: { type: "none" } });
    s.addText(t, { x, y: 1.55, w: 3.3, h: 0.62, fontFace: F, fontSize: 14, bold: true, color: fc, align: "center", valign: "middle", margin: 0, isTextBox: true });
  };
  chip(MX, "LC2 thermal compression, N = 548.94 kN", C.ice, C.navy);
  arrowRight(s, MX + 3.38, 1.72, 0.4);
  chip(MX + 3.86, "Linear eigenvalue buckling (S1)", C.steel, C.white);
  const ih = imgW(s, "mech_S1_mode1_side.png", MX, 2.35, 7.6, 1524, 872);
  caption(s, "Mode 1, side view: whole-duct sideways sway (eigenvector — amplitude arbitrary)", MX, 2.35 + ih + 0.02, 7.6, 0.3, "center");
  // right column: key numbers
  const rx = 8.45, rw = W - MX - rx;
  card(s, rx, 1.55, rw, 2.35);
  s.addText("λ₁ = 1.108", { x: rx + 0.2, y: 1.65, w: rw - 0.4, h: 0.9, fontFace: F, fontSize: 46, bold: true, color: C.heat, margin: 0, valign: "middle", isTextBox: true });
  s.addText([
    { text: "Critical load  P_cr = λ₁ × N = 608.25 kN", options: { breakLine: true } },
    { text: "First-yield factor 1.730 > λ₁: in the idealised S1 model, elastic bifurcation comes before first yield" },
  ], { x: rx + 0.2, y: 2.55, w: rw - 0.4, h: 1.3, fontFace: F, fontSize: 14, color: C.text, margin: 0, valign: "top", paraSpaceAfter: 5, isTextBox: true });
  card(s, rx, 4.05, rw, 2.8, C.white, C.line);
  s.addText("What λ₁ is — and is not", { x: rx + 0.2, y: 4.12, w: rw - 0.4, h: 0.4, fontFace: F, fontSize: 16, bold: true, color: C.navy, margin: 0, isTextBox: true });
  const pts = ["Guided-column sway: ends translate, end rotation held", "Idealised elastic model: perfectly straight tube, idealised supports",
               "No geometric imperfections, no plasticity, no nonlinear post-buckling", "Not a collapse load and not a factor of safety"];
  s.addText(pts.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < pts.length - 1, bold: k === 3, color: k === 3 ? C.heat : C.text } })),
    { x: rx + 0.2, y: 4.55, w: rw - 0.35, h: 2.25, fontFace: F, fontSize: 14, margin: 0, valign: "top", paraSpaceAfter: 5, isTextBox: true });
  s.addNotes(NOTES[12]);
}

// ================================================================= SLIDE 13 - SUPPORT SENSITIVITY
{
  const s = newSlide();
  title(s, "Support Sensitivity", "Same duct, same thermal load, same static stress — only the end restraint changes");
  const sc = [["S1 — baseline", "guided: ends sway, rotation held", "K = 1", fmt(v("lam_S1"), 3), fmt(v("Pcr_S1"), 2), "mech_S1_mode1_iso.png", "bifurcation before first yield (1.108 < 1.730)"],
              ["S3", "clamped – pinned", "K = 0.699", fmt(v("lam_S3"), 3), fmt(v("Pcr_S3"), 2), "mech_S3_mode1_iso.png", "first yield before bifurcation (1.730 < 2.232)"],
              ["S2", "clamped – clamped", "K = 0.5", fmt(v("lam_S2"), 3), fmt(v("Pcr_S2"), 2), "mech_S2_mode1_iso.png", "first yield before bifurcation (1.730 < 4.300)"]];
  s.addText("increasing end restraint  →", { x: MX, y: 1.5, w: W - 2 * MX, h: 0.3, fontFace: F, fontSize: 13, italic: true, color: C.muted, align: "right", margin: 0, isTextBox: true });
  const cw = 3.95, gap = 0.225;
  sc.forEach(([h, d, k, lam, pcr, im, mech], i) => {
    const x = MX + i * (cw + gap);
    card(s, x, 1.85, cw, 4.2, C.white, C.line);
    s.addText(h, { x: x + 0.2, y: 1.93, w: cw - 0.4, h: 0.4, fontFace: F, fontSize: 18, bold: true, color: i === 0 ? C.heat : C.navy, margin: 0, isTextBox: true });
    s.addText(d + "  ·  " + k, { x: x + 0.2, y: 2.32, w: cw - 0.4, h: 0.3, fontFace: F, fontSize: 13, color: C.muted, margin: 0, isTextBox: true });
    imgW(s, im, x + 0.1, 2.65, cw - 0.2, 1556, 872);
    s.addText([{ text: "λ₁ = " + lam, options: { fontSize: 30, bold: true, color: i === 0 ? C.heat : C.steel } }],
      { x: x + 0.2, y: 4.72, w: cw - 0.4, h: 0.55, fontFace: F, margin: 0, valign: "middle", isTextBox: true });
    s.addText("P_cr = " + pcr + " kN  ·  " + mech, { x: x + 0.2, y: 5.28, w: cw - 0.4, h: 0.7, fontFace: F, fontSize: 12, color: C.text, margin: 0, valign: "top", isTextBox: true });
  });
  card(s, MX, 6.2, W - 2 * MX, 0.65, "FFF4E6");
  s.addText([
    { text: "λ₁ changes by a factor of 3.9 at an identical 605.16 MPa static peak. ", options: { bold: true, color: C.navy } },
    { text: "The real support stiffness is not defined, so the scenarios are not ranked.", options: { color: C.text } },
  ], { x: MX + 0.25, y: 6.22, w: W - 2 * MX - 0.5, h: 0.6, fontFace: F, fontSize: 14, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(NOTES[13]);
}

// ================================================================= SLIDES 13a-13c - ADDITIONAL LS-DYNA ANALYSIS (Section 13)
// Additional nonlinear buckling analysis using ANSYS LS-DYNA (follow-on extension). Values from
// 15_LS_DYNA_Extension/12C_Nonlinear_Buckling (FINAL_12C_RESULTS.md, IMPERFECTION_SENSITIVITY.csv); figures are the 12C plots
// with the title strip cropped (Figures/LSD_*_nt.png).
const LSD_FOOT = "R. B. Patel  ·  Additional LS-DYNA analysis (follow-on extension of the project)";
function lsdImg(s, file, x, y, w, pxW, pxH, alt) {
  const h = w * pxH / pxW;
  s.addImage({ path: FIG(file), x, y, w, h, altText: alt });
  return h;
}
{
  const s = newSlide(false, LSD_FOOT);
  title(s, "LS-DYNA Nonlinear Buckling Extension", "Additional geometrically nonlinear analysis of the S1 / LC2 duct — a follow-on extension of the Mechanical study");
  card(s, MX, 1.55, 5.75, 4.45, C.white, C.line);
  s.addText("What was added", { x: MX + 0.25, y: 1.63, w: 5.3, h: 0.42, fontFace: F, fontSize: 18, bold: true, color: C.navy, margin: 0, isTextBox: true });
  const pts = ["Same LC2 model: mapped Fluent temperature field, S1 supports, 108,252-node mesh",
               "LS-DYNA verified first: peak von Mises 605.160 vs 605.161 MPa; linear λ₁ = 1.1095 (+0.13 %)",
               "Geometrically nonlinear (large deflection); elastic, temperature-dependent material",
               "Temperature rise scaled by λ up to 1.3, with fine steps from λ = 1.0 to 1.2",
               "Imperfection = buckling mode 1 shape: 0.1 / 0.6 / 1.2 mm (numerical sensitivity values) + perfect reference"];
  s.addText(pts.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < pts.length - 1 } })),
    { x: MX + 0.25, y: 2.15, w: 5.35, h: 3.8, fontFace: F, fontSize: 15.5, color: C.text, margin: 0, valign: "top", paraSpaceAfter: 10, isTextBox: true });
  const rx = 6.5, rw = W - MX - rx;
  const ih = lsdImg(s, "LSD_deformed_shape_C5_nt.png", rx, 1.6, rw, 1650, 610,
    "LS-DYNA case C5 (1.2 mm): lateral deflection along the duct and deformed outline at load parameter 1.30, global guided sway");
  caption(s, "Case C5 (1.2 mm), λ = 1.15–1.30: global guided sway — ends move in opposite directions, mid-span lateral ≈ 0, no local or shell mode", rx, 1.6 + ih + 0.05, rw, 0.55, "center");
  card(s, rx, 4.75, rw, 1.25);
  s.addText([
    { text: "Three numerical cases  ", options: { bold: true, color: C.navy } },
    { text: "C1 = 0.1 mm · C3 = 0.6 mm · C5 = 1.2 mm, plus the perfect-geometry reference C0. All four runs terminated normally.", options: { color: C.text } },
  ], { x: rx + 0.2, y: 4.8, w: rw - 0.4, h: 1.15, fontFace: F, fontSize: 14, margin: 0, valign: "middle", isTextBox: true });
  card(s, MX, 6.2, W - 2 * MX, 0.65, "FFF4E6");
  s.addText([
    { text: "An additional analysis, not part of the original internship work programme. ", options: { bold: true, color: C.navy } },
    { text: "The Mechanical result λ₁ = 1.108 remains the reference.", options: { color: C.text } },
  ], { x: MX + 0.25, y: 6.22, w: W - 2 * MX - 0.5, h: 0.6, fontFace: F, fontSize: 14, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(NOTES["13a"]);
}
{
  const s = newSlide(false, LSD_FOOT);
  title(s, "Imperfection Sensitivity", "Imperfection size controls when the duct starts to bend — and how much it bends and stresses at a given load");
  const ih = lsdImg(s, "LSD_load_lateral_nt.png", MX, 1.55, 7.75, 1650, 610,
    "LS-DYNA load-lateral displacement curves for 0.1, 0.6 and 1.2 mm imperfections and the perfect reference, and normalised curves");
  caption(s, "Axial compression N against total relative end sway (left) and normalised by P_cr and the initial sway (right)", MX, 1.55 + ih + 0.04, 7.75, 0.3, "center");
  const rx = 8.5, rw = W - MX - rx;
  card(s, rx, 1.55, rw, 3.2, C.white, C.line);
  s.addText("At a glance", { x: rx + 0.2, y: 1.62, w: rw - 0.4, h: 0.4, fontFace: F, fontSize: 16, bold: true, color: C.navy, margin: 0, isTextBox: true });
  const hdr = { bold: true, color: C.white, fill: { color: C.steel }, fontSize: 11.5, align: "center", valign: "middle" };
  const cel = { fontSize: 12, color: C.text, align: "center", valign: "middle" };
  const rows = [
    [{ text: "Case", options: hdr }, { text: "1 % drop λ", options: hdr }, { text: "N at λ = 1", options: hdr }, { text: "VM at λ = 1", options: hdr }, { text: "Yield λ", options: hdr }],
    ["C1  0.1 mm", "1.070", "552.2 kN", "690 MPa", "1.109"],
    ["C3  0.6 mm", "0.825", "531.2 kN", "966 MPa", "1.031"],
    ["C5  1.2 mm", "0.375", "503.5 kN", "1104 MPa", "0.974"],
  ].map((r, i) => i === 0 ? r : r.map((t, j) => ({ text: t, options: { ...cel, bold: j === 0, fill: { color: i % 2 ? C.pale : C.white } } })));
  s.addTable(rows, { x: rx + 0.15, y: 2.1, w: rw - 0.3, colW: [0.98, 0.8, 0.86, 0.86, 0.6], rowH: 0.42, fontFace: F, margin: 0.03, border: { type: "solid", pt: 0.5, color: C.line } });
  caption(s, "1 % drop: N falls 1 % below the perfect path. Yield λ: peak von Mises reaches the local yield estimate.", rx + 0.2, 3.95, rw - 0.4, 0.7);
  card(s, MX, 4.95, W - 2 * MX, 1.9);
  const tk = ["Larger imperfection → earlier departure from the perfect path: λ = 1.070 → 0.825 → 0.375",
              "At the operating field (λ = 1): lower axial force (552.2 → 503.5 kN) and higher peak stress (690 → 1104 MPa)",
              "Normalised curves collapse onto one: a single global mode, amplified by the imperfection"];
  s.addText(tk.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < tk.length - 1 } })),
    { x: MX + 0.25, y: 5.05, w: W - 2 * MX - 0.5, h: 1.7, fontFace: F, fontSize: 15, color: C.text, margin: 0, valign: "middle", paraSpaceAfter: 6, isTextBox: true });
  s.addNotes(NOTES["13b"]);
}
{
  const s = newSlide(false, LSD_FOOT);
  title(s, "Mechanical vs LS-DYNA Buckling", "Characteristic load 607.7–612.3 kN against the Mechanical P_cr = 608.25 kN (λ₁ = 1.108)");
  const ih = lsdImg(s, "LSD_mechanical_vs_nonlinear_nt.png", MX, 1.55, 7.3, 1275, 581,
    "Bar chart: Mechanical and LS-DYNA linear critical loads, LS-DYNA maximum attained axial force and Southwell estimates for the three imperfection cases");
  caption(s, "Bars: linear critical loads and maximum attained N (λ ≤ 1.3); markers: Southwell estimates. 8A = Mechanical, 12B G6 = LS-DYNA linear check", MX, 1.55 + ih + 0.04, 7.3, 0.5, "center");
  const rx = 8.05, rw = W - MX - rx;
  stat(s, rx, 1.55, rw, 1.3, "607.7–612.3", "kN", "Southwell characteristic load", "three imperfection cases: −0.1 % to +0.7 % of P_cr");
  stat(s, rx, 2.98, rw, 1.3, "608.25", "kN", "Mechanical P_cr", "λ₁ = 1.108 — linear, perfect elastic tube", C.steel);
  stat(s, rx, 4.41, rw, 1.3, "601.0", "kN", "Maximum load, 0.1 mm case", "at λ = 1.185; C3 and C5 still rising at λ = 1.3", C.navy);
  card(s, MX, 5.95, W - 2 * MX, 0.9, "FFF4E6");
  s.addText([
    { text: "Elastic model only: ", options: { bold: true, color: C.navy } },
    { text: "first local yield at λ = 0.974–1.109, so the later curves lie outside the elastic range. The perfect-geometry run gives no bifurcation load. Not a factor of safety, not experimental validation.", options: { color: C.text } },
  ], { x: MX + 0.25, y: 5.98, w: W - 2 * MX - 0.5, h: 0.84, fontFace: F, fontSize: 14, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(NOTES["13c"]);
}

// ================================================================= SLIDE 14 - PARAMETRIC STUDY DESIGN
{
  const s = newSlide();
  title(s, "Parametric Study", "One factor at a time around the baseline P00 — every case is a complete simulation chain");
  // star diagram
  const cx = 3.35, cy = 4.15;
  const arms = [["Inlet velocity", "21.15 m/s", "25.85 m/s", C.steel, -150, -30], ["Wall heat flux", "7200 W/m²", "8800 W/m²", C.heat, 150, 30], ["Wall thickness", "8 mm", "12 mm", C.slate, 90, 270]];
  const node = (x, y, t, col) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x - 0.72, y: y - 0.27, w: 1.44, h: 0.54, rectRadius: 0.08, fill: { color: col }, line: { type: "none" } });
    s.addText(t, { x: x - 0.72, y: y - 0.27, w: 1.44, h: 0.54, fontFace: F, fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
  };
  const R = 1.95;
  const pos = (ang) => [cx + R * Math.cos(ang * Math.PI / 180), cy + 0.78 * R * Math.sin(ang * Math.PI / 180)];
  arms.forEach(([nm, lo, hi, col, a1, a2]) => {
    [a1, a2].forEach((a) => {
      const [x, y] = pos(a);
      s.addShape(pres.shapes.LINE, { x: Math.min(cx, x), y: Math.min(cy, y), w: Math.abs(x - cx), h: Math.abs(y - cy), line: { color: col, width: 2.5 }, flipH: (x < cx) !== (y < cy) });
    });
  });
  arms.forEach(([nm, lo, hi, col, a1, a2]) => {
    const [x1, y1] = pos(a1), [x2, y2] = pos(a2);
    node(x1, y1, lo, col); node(x2, y2, hi, col);
  });
  s.addShape(pres.shapes.OVAL, { x: cx - 1.0, y: cy - 0.6, w: 2.0, h: 1.2, fill: { color: C.navy }, line: { type: "none" } });
  s.addText([{ text: "P00 baseline", options: { bold: true, fontSize: 16, breakLine: true } }, { text: "23.5 m/s", options: { fontSize: 11, breakLine: true } }, { text: "8000 W/m² · 10 mm", options: { fontSize: 11 } }],
    { x: cx - 1.0, y: cy - 0.6, w: 2.0, h: 1.2, fontFace: F, color: C.white, align: "center", valign: "middle", margin: 0.05, isTextBox: true });
  s.addText([{ text: "velocity", options: { color: C.steel, bold: true } }, { text: "  ·  ", options: { color: C.muted } }, { text: "heat flux", options: { color: C.heat, bold: true } }, { text: "  ·  ", options: { color: C.muted } }, { text: "thickness", options: { color: C.slate, bold: true } }],
    { x: cx - 2.6, y: 6.45, w: 5.2, h: 0.3, fontFace: F, fontSize: 13, align: "center", margin: 0, isTextBox: true });
  // right: variable table
  const rx = 6.55, rw = W - MX - rx;
  const tb = [
    [{ text: "Variable", options: { bold: true, color: C.white, fill: { color: C.navy } } }, { text: "Cases", options: { bold: true, color: C.white, fill: { color: C.navy } } }, { text: "Held constant", options: { bold: true, color: C.white, fill: { color: C.navy } } }],
    [{ text: "Inlet velocity", options: { bold: true, color: C.steel } }, "21.15 / 23.5 / 25.85 m/s (∓10 %)", "heat flux, geometry"],
    [{ text: "Wall heat flux", options: { bold: true, color: C.heat } }, "7200 / 8000 / 8800 W/m² (∓10 %)", "velocity, geometry"],
    [{ text: "Wall thickness", options: { bold: true, color: C.slate } }, "8 / 10 / 12 mm (Dₒ 36 / 40 / 44 mm)", "bore, velocity, total heat input Q"],
  ];
  s.addTable(tb, { x: rx, y: 1.6, w: rw, colW: [1.5, 3.05, 1.73], rowH: 0.55, fontFace: F, fontSize: 13, color: C.text, valign: "middle",
    border: { type: "solid", pt: 0.75, color: C.line }, fill: { color: C.white }, margin: [0.04, 0.08, 0.04, 0.08] });
  card(s, rx, 4.05, rw, 2.8);
  s.addText("Every case, not an estimate", { x: rx + 0.2, y: 4.12, w: rw - 0.4, h: 0.4, fontFace: F, fontSize: 16, bold: true, color: C.navy, margin: 0, isTextBox: true });
  const pts = ["Own converged Fluent CFD solution", "Own temperature mapping to Mechanical", "LC1 + LC2 statics and linear buckling, support S1",
               "Thickness: flux rescaled so total heat input stays constant", "Control case C00 repeated P00 and reproduced it"];
  s.addText(pts.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < pts.length - 1 } })),
    { x: rx + 0.2, y: 4.58, w: rw - 0.35, h: 2.2, fontFace: F, fontSize: 15, color: C.text, margin: 0, valign: "top", paraSpaceAfter: 7, isTextBox: true });
  s.addNotes(NOTES[14]);
}

// ================================================================= SLIDE 15 - PARAMETRIC RESULTS
{
  const s = newSlide();
  title(s, "Parametric Results", "Velocity acts through cooling, heat flux through temperature, thickness through the cross-section");
  const Cc = D.charts;
  const rowsDef = [
    ["Inlet velocity", "21.15 · 23.5 · 25.85 m/s", C.steel, { min: 20, max: 27, unit: 1 },
      [["V_dp", "Pressure drop [Pa]", 360, 520, 40, 1], ["V_tout", "Outlet bulk temperature [K]", 358, 382, 6, 1], ["V_lam", "λ₁ (S1)", 0.9, 1.3, 0.1, 3]]],
    ["Wall heat flux", "7200 · 8000 · 8800 W/m²", C.heat, { min: 7000, max: 9000, unit: 500 },
      [["Q_tmax", "Maximum solid temperature [K]", 520, 610, 30, 1], ["Q_vm", "LC2 max von Mises [MPa]", 510, 710, 50, 1], ["Q_lam", "λ₁ (S1)", 0.9, 1.35, 0.15, 3]]],
    ["Wall thickness", "8 · 10 · 12 mm  (Q constant)", C.slate, { min: 7, max: 13, unit: 1 },
      [["T_def", "LC1 max deformation [mm]", 1.83, 1.86, 0.01, 3], ["T_pcr", "Critical load P_cr [kN]", 300, 1000, 200, 0], ["T_lam", "λ₁ (S1)", 0.9, 1.35, 0.15, 3]]],
  ];
  const lw = 1.55, x0 = MX + lw + 0.1, cw = (W - MX - x0 - 0.2) / 3, ch = 1.78, y0 = 1.5;
  rowsDef.forEach(([rn, rv, col, xa, charts], r) => {
    const y = y0 + r * (ch + 0.05);
    card(s, MX, y + 0.1, lw, ch - 0.2);
    s.addText([{ text: rn, options: { bold: true, fontSize: 15, color: col, breakLine: true } }, { text: rv, options: { fontSize: 11, color: C.text } }],
      { x: MX + 0.1, y: y + 0.15, w: lw - 0.2, h: ch - 0.3, fontFace: F, margin: 0, valign: "middle", isTextBox: true });
    charts.forEach(([key, ttl, ymin, ymax, yu, dec], c) => {
      const d = Cc[key];
      const series = [{ name: "x", values: d.x }, { name: ttl, values: d.y, labels: [d.y.map((vv) => fmt(vv, dec))] }];
      const isLam = key.endsWith("lam");
      if (isLam) series.push({ name: "ref_lambda_1", values: [1, 1, 1], labels: [key === "Q_lam" ? ["λ₁ = 1", "", ""] : ["", "", "λ₁ = 1"]] });
      s.addChart(pres.charts.SCATTER, series, {
        x: x0 + c * (cw + 0.1), y, w: cw, h: ch, chartColors: isLam ? [col, "9AA5B1"] : [col], lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 8,
        showLabel: true, dataLabelFormatScatter: "custom", dataLabelPosition: "t", dataLabelFontSize: 12, dataLabelColor: C.text, dataLabelFontBold: true,
        valAxisMinVal: ymin, valAxisMaxVal: ymax, valAxisMajorUnit: yu, catAxisMinVal: xa.min, catAxisMaxVal: xa.max, catAxisMajorUnit: xa.unit,
        valAxisLabelFontSize: 10, catAxisLabelFontSize: 10, valAxisLabelColor: C.muted, catAxisLabelColor: C.muted,
        // axis number format left at General: pptxgenjs writes the scatter X axis with the Y-axis format code
        showTitle: true, title: ttl, titleFontSize: 12, titleColor: C.navy, showLegend: false,
        valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" }, ...axisFont,
      });
    });
  });
  s.addNotes(NOTES[15]);
}

// ================================================================= SLIDE 16 - KEY FINDINGS
{
  const s = newSlide();
  title(s, "Key Engineering Findings", "Within the idealised model — each statement traces to the final engineering audit");
  const fd = [
    ["Restraint dominates the thermal stress", "LC2: 548.94 kN end force, −582.44 MPa mean axial stress, 605.16 MPa peak — vs 24.28 MPa for free expansion"],
    ["The idealised S1 model is stability-limited", "λ₁ = 1.108 is below the first-yield factor 1.730: bifurcation comes first, close to instability"],
    ["End restraint controls the buckling response", "λ₁ = 1.108 (S1) · 2.232 (S3) · 4.300 (S2) at an identical static stress"],
    ["Heat flux drives temperature and stress", "±10 % q″: T_max −28.1 / +28.6 K, LC2 stress −11.0 / +11.2 %, λ₁ 1.255 / 0.988"],
    ["Thickness acts on stiffness, not temperature", "8 / 12 mm at constant Q: P_cr −36.6 / +49.3 %, T_max −0.61 / +0.50 K, λ₁ 0.945 / 1.287"],
    ["Discretisation is not the dominant uncertainty", "CFD mesh 4.4 K on T_max, structural mesh ≤ 4.9 × 10⁻⁴, pressure load negligible — the support definition dominates"],
  ];
  const cw = 5.95, ch = 1.5;
  fd.forEach(([h, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * (cw + 0.4), y = 1.55 + row * (ch + 0.22);
    card(s, x, y, cw, ch);
    circleNum(s, x + 0.22, y + 0.25, 0.55, i + 1, C.heat, 18);
    s.addText(h, { x: x + 0.95, y: y + 0.12, w: cw - 1.15, h: 0.48, fontFace: F, fontSize: 18, bold: true, color: C.navy, margin: 0, valign: "middle", isTextBox: true });
    s.addText(d, { x: x + 0.95, y: y + 0.62, w: cw - 1.15, h: 0.82, fontFace: F, fontSize: 15, color: C.text, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes(NOTES[16]);
}

// ================================================================= SLIDE 17 - LIMITATIONS AND FUTURE WORK
{
  const s = newSlide();
  title(s, "Limitations and Future Work", "The limits define what the results can support — and what to do next");
  const lim = ["Original internship files not retained; analysis redone", "No experimental validation — verified, not validated", "Idealised end supports (S1 / S2 / S3)",
               "No measured geometric imperfections", "Nonlinear buckling: elastic LS-DYNA extension only", "No temperature-dependent inelastic stress–strain model",
               "Poisson's ratio assumed (0.294)", "One-factor-at-a-time parametric study: no interactions", "CFD model form not varied (model-form uncertainty)"];
  const fut = [["Experimental validation", "wall thermocouples and pressure taps on a heated-duct rig"], ["Realistic support characterisation", "lateral and rotational stiffness of the real mounting"],
               ["Imperfect, nonlinear buckling", "elastic–plastic, with tolerance-based imperfections"], ["Temperature-dependent inelastic behaviour", "elastic–plastic analysis with specification-minimum data"],
               ["Turbulence and radiation modelling", "alternative turbulence models; internal radiation, where justified"]];
  card(s, MX, 1.55, 6.0, 5.3, C.white, C.line);
  s.addText("Limitations", { x: MX + 0.25, y: 1.63, w: 5.5, h: 0.45, fontFace: F, fontSize: 19, bold: true, color: C.heat, margin: 0, isTextBox: true });
  s.addText(lim.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < lim.length - 1 } })),
    { x: MX + 0.25, y: 2.15, w: 5.6, h: 4.6, fontFace: F, fontSize: 16, color: C.text, margin: 0, valign: "top", paraSpaceAfter: 9, isTextBox: true });
  const rx = 6.85, rw = W - MX - rx;
  s.addText("Future work", { x: rx, y: 1.63, w: rw, h: 0.45, fontFace: F, fontSize: 19, bold: true, color: C.steel, margin: 0, isTextBox: true });
  fut.forEach(([h, d], i) => {
    const y = 2.15 + i * 0.94;
    card(s, rx, y, rw, 0.82);
    circleNum(s, rx + 0.15, y + 0.18, 0.46, i + 1, C.steel, 15);
    s.addText(h, { x: rx + 0.78, y: y + 0.06, w: rw - 0.95, h: 0.36, fontFace: F, fontSize: 15, bold: true, color: C.navy, margin: 0, valign: "middle", isTextBox: true });
    s.addText(d, { x: rx + 0.78, y: y + 0.42, w: rw - 0.95, h: 0.34, fontFace: F, fontSize: 12.5, color: C.text, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes(NOTES[17]);
}

// ================================================================= SLIDE 18 - CONCLUSION
{
  const s = newSlide(true);
  s.addText("Conclusion", { x: 0.6, y: 0.55, w: 7.6, h: 0.7, fontFace: F, fontSize: 34, bold: true, color: C.white, margin: 0, isTextBox: true });
  const cl = [
    ["A complete, checked chain from flow to stability", "converged, verified conjugate heat transfer; maximum solid temperature 562.58 K on the medium mesh"],
    ["Restraint turns thermal growth into compression", "605.16 MPa local peak, 57.8 % of the local yield strength"],
    ["The idealised S1 duct is stability-limited", "λ₁ = 1.108 — and the end restraint controls that conclusion (1.108 to 4.300)"],
  ];
  cl.forEach(([h, d], i) => {
    const y = 1.5 + i * 1.3;
    circleNum(s, 0.6, y + 0.08, 0.5, i + 1, C.heat, 17);
    s.addText(h, { x: 1.3, y, w: 6.9, h: 0.45, fontFace: F, fontSize: 19, bold: true, color: C.white, margin: 0, valign: "middle", isTextBox: true });
    s.addText(d, { x: 1.3, y: y + 0.47, w: 6.9, h: 0.65, fontFace: F, fontSize: 15, color: "CADCFC", margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("Within an idealised numerical model that has not been validated against measurement. The results characterise the mechanism and its sensitivities; they do not show that a real component is structurally adequate.",
    { x: 0.6, y: 5.55, w: 7.6, h: 1.0, fontFace: F, fontSize: 13, italic: true, color: "AFC3D9", margin: 0, valign: "top", isTextBox: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.75, y: 1.5, w: 4.0, h: 4.6, rectRadius: 0.1, fill: { color: "1E2F52" }, line: { color: "3B5078", width: 0.75 } });
  s.addText([{ text: "Thank You", options: { fontSize: 36, bold: true, color: C.white, breakLine: true } }, { text: "Questions?", options: { fontSize: 28, color: C.amber } }],
    { x: 8.75, y: 2.2, w: 4.0, h: 2.0, fontFace: F, align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText("Rohan Balram Patel\nB.Tech Aerospace Engineering\nDayananda Sagar University, Bengaluru", { x: 8.95, y: 4.45, w: 3.6, h: 1.2, fontFace: F, fontSize: 13, color: "CADCFC", align: "center", valign: "top", margin: 0, isTextBox: true });
  s.addNotes(NOTES[18]);
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("written", f, "slides", slideNo));
