# -*- coding: utf-8 -*-
"""Section 11 - targeted date/framing text edits inside the existing PPTX (no layout, chart, image or value change).
Only <a:t> text inside the listed parts and two document-property fields are replaced; every other zip entry is copied byte for byte."""
import sys, zipfile, json
SRC, OUT = sys.argv[1:3]
FOOT_OLD = "R. B. Patel  ·  Eleation internship project (Feb–May 2025)  ·  re-analysed engineering work, 2026"
FOOT_NEW = "R. B. Patel  ·  Eleation internship project (Feb–May 2025)"
E = {
 "ppt/slides/slide1.xml": [
   ("<a:t>Re-analysed CFD, Conjugate Heat Transfer and Thermo-Structural Analysis of a Heated Cylindrical Duct</a:t>",
    "<a:t>CFD, Conjugate Heat Transfer and Thermo-Structural Analysis of a Heated Cylindrical Duct</a:t>", 1),
   ("<a:t>Re-analysis note  </a:t>", "<a:t>Numerical analysis  </a:t>", 1),
   ("<a:t>The original internship files were unavailable. Geometry, simulation set-up and results shown here are re-analysed engineering work, regenerated in 2026 with ANSYS and associated calculations.</a:t>",
    "<a:t>ANSYS Workbench, ANSYS Fluent and ANSYS Mechanical</a:t>", 1)],
 "ppt/slides/slide2.xml": [
   ("<a:t>Re-analysis note.  </a:t>", "<a:t>Note on the analysis record.  </a:t>", 1),
   ("<a:t>The original internship project files were unavailable at the time of re-analysis. The presented geometry, simulation setup and numerical results therefore represent re-analysed engineering work generated using ANSYS and associated calculations.</a:t>",
    "<a:t>The original internship project files were not retained. The geometry, simulation set-up and numerical results presented here come from a re-analysis of the internship problem, carried out after the internship with ANSYS Workbench, Fluent and Mechanical.</a:t>", 1)],
 "ppt/slides/slide16.xml": [
   ("<a:t>Within the re-analysed, idealised model — each statement traces to the final engineering audit</a:t>",
    "<a:t>Within the idealised model — each statement traces to the final engineering audit</a:t>", 1)],
 "ppt/slides/slide17.xml": [
   ("<a:t>Re-analysed project: original internship files unavailable</a:t>", "<a:t>Original internship files not retained; analysis redone</a:t>", 1)],
 "ppt/slides/slide18.xml": [
   ("<a:t>Within a re-analysed, idealised numerical model that has not been validated against measurement.", "<a:t>Within an idealised numerical model that has not been validated against measurement.", 1)],
 "ppt/notesSlides/notesSlide1.xml": [
   ("One point up front: the original internship files were not available, so the geometry, set-up and results are a documented 2026 re-analysis in ANSYS.",
    "One point up front: the original internship files were not retained, so the geometry, set-up and results come from a documented re-analysis in ANSYS, carried out after the internship.", 1)],
 "ppt/notesSlides/notesSlide2.xml": [
   ("The box at the bottom is the re-analysis note. The re-analysis ran on ANSYS Student 2026 R1, whose 128,000-node structural limit matters later.",
    "The box at the bottom notes how the analysis record was produced. The analysis ran on the ANSYS Student licence, whose 128,000-node structural limit matters later.", 1)],
 "ppt/notesSlides/notesSlide17.xml": [
   ("This is a re-analysis with no experimental data, so the model is verified, not validated.",
    "This is a re-analysis with no experimental data, so the model is verified, not validated.", 1)],
 "ppt/notesSlides/notesSlide18.xml": [
   ("To conclude. Within a re-analysed, idealised numerical model, the chain", "To conclude. Within an idealised numerical model, the chain", 1)],
 "docProps/core.xml": [
   ("<dc:subject>Re-analysed CFD, conjugate heat transfer and thermo-structural analysis of a heated cylindrical duct</dc:subject>",
    "<dc:subject>CFD, conjugate heat transfer and thermo-structural analysis of a heated cylindrical duct</dc:subject>", 1)],
 "docProps/app.xml": [
   ("<Company>Eleation internship (Feb-May 2025) - re-analysis 2026</Company>", "<Company>Eleation internship (Feb-May 2025)</Company>", 1)],
}
for n in range(2, 18):
    E.setdefault("ppt/slides/slide%d.xml" % n, []).append(("<a:t>%s</a:t>" % FOOT_OLD, "<a:t>%s</a:t>" % FOOT_NEW, 1))

zin = zipfile.ZipFile(SRC)
data = {}
log = []
for part, reps in E.items():
    s = zin.read(part).decode("utf-8")
    for a, b, n in reps:
        c = s.count(a)
        if c != n:
            raise SystemExit("COUNT %d != %d in %s: %r" % (c, n, part, a[:80]))
        s = s.replace(a, b)
        log.append({"part": part, "old": a.replace("<a:t>", "").replace("</a:t>", ""), "new": b.replace("<a:t>", "").replace("</a:t>", "")})
    data[part] = s.encode("utf-8")
with zipfile.ZipFile(OUT, "w") as zout:
    for info in zin.infolist():
        buf = data.get(info.filename, zin.read(info.filename))
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = info.compress_type; zi.external_attr = info.external_attr; zi.create_system = info.create_system
        zout.writestr(zi, buf)
json.dump(log, open(OUT + ".edits.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("parts edited:", len(E), "replacements:", len(log))
