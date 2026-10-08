# -*- coding: utf-8 -*-
"""Section 13 - controlled integration of the additional LS-DYNA analysis into the EXISTING deck.
The existing 18 slides are kept byte-identical except slide 17 (three limitation / future-work strings) and its speaker note
(one added sentence). Three new slides (built by build_deck.js as slides 14-16, keys 13a-13c in notes.js) are copied from a
full rebuild into the existing package as slide19-21.xml and inserted in the slide order after slide 13 (Support Sensitivity).
Usage: python section13_edit_deck.py <existing.pptx> <full rebuild.pptx> <out.pptx>   (writes section13_deck_edits_log.json)"""
import sys, re, json, zipfile, os
OLD, NEW, OUT = sys.argv[1:4]
zo, zn = zipfile.ZipFile(OLD), zipfile.ZipFile(NEW)
files = {n: zo.read(n) for n in zo.namelist()}
infos = {i.filename: i for i in zo.infolist()}
log = {"inserted_slides": [], "text_edits": []}
# ---------------------------------------------------------------- 1. copy the three new slides
MAP = {14: 19, 15: 20, 16: 21}                      # slide number in the rebuild -> part number in the existing package
for src, dst in MAP.items():
    sx = zn.read(f"ppt/slides/slide{src}.xml").decode("utf-8")
    rel = zn.read(f"ppt/slides/_rels/slide{src}.xml.rels").decode("utf-8")
    for m in re.findall(r'Target="\.\./media/(image-%d-(\d+)\.png)"' % src, rel):
        old_name, k = m
        new_name = f"image-{dst}-{k}.png"
        assert f"ppt/media/{new_name}" not in files
        files[f"ppt/media/{new_name}"] = zn.read(f"ppt/media/{old_name}")
        rel = rel.replace(f"../media/{old_name}", f"../media/{new_name}")
    rel = rel.replace(f"../notesSlides/notesSlide{src}.xml", f"../notesSlides/notesSlide{dst}.xml")
    nx = zn.read(f"ppt/notesSlides/notesSlide{src}.xml")
    nrel = zn.read(f"ppt/notesSlides/_rels/notesSlide{src}.xml.rels").decode("utf-8").replace(f"../slides/slide{src}.xml", f"../slides/slide{dst}.xml")
    for p in (f"ppt/slides/slide{dst}.xml", f"ppt/notesSlides/notesSlide{dst}.xml"):
        assert p not in files
    files[f"ppt/slides/slide{dst}.xml"] = sx.encode("utf-8")
    files[f"ppt/slides/_rels/slide{dst}.xml.rels"] = rel.encode("utf-8")
    files[f"ppt/notesSlides/notesSlide{dst}.xml"] = nx
    files[f"ppt/notesSlides/_rels/notesSlide{dst}.xml.rels"] = nrel.encode("utf-8")
    log["inserted_slides"].append({"rebuild_slide": src, "part": f"slide{dst}.xml", "title": re.findall(r"<a:t>([^<]*)</a:t>", sx)[1]})
# content types
ct = files["[Content_Types].xml"].decode("utf-8")
add = "".join(f'<Override PartName="/ppt/slides/slide{d}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
              f'<Override PartName="/ppt/notesSlides/notesSlide{d}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>' for d in MAP.values())
assert 'Extension="png"' in ct
files["[Content_Types].xml"] = ct.replace("</Types>", add + "</Types>").encode("utf-8")
# presentation rels + slide order (after slide 13 = sldId 268)
pr = files["ppt/_rels/presentation.xml.rels"].decode("utf-8")
ids = [int(x) for x in re.findall(r'Id="rId(\d+)"', pr)]
newr = {d: f"rId{max(ids) + i + 1}" for i, d in enumerate(MAP.values())}
pr = pr.replace("</Relationships>", "".join(
    f'<Relationship Id="{newr[d]}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{d}.xml"/>'
    for d in MAP.values()) + "</Relationships>")
files["ppt/_rels/presentation.xml.rels"] = pr.encode("utf-8")
p = files["ppt/presentation.xml"].decode("utf-8")
sids = [int(x) for x in re.findall(r'<p:sldId id="(\d+)"', p)]
anchor = re.search(r'<p:sldId id="268" r:id="rId14"/>', p)
assert anchor, "slide 13 anchor not found"
ins = "".join(f'<p:sldId id="{max(sids) + i + 1}" r:id="{newr[d]}"/>' for i, d in enumerate(MAP.values()))
p = p[:anchor.end()] + ins + p[anchor.end():]
files["ppt/presentation.xml"] = p.encode("utf-8")
files["docProps/app.xml"] = zn.read("docProps/app.xml")            # slide count 21 (generic metadata)
# ---------------------------------------------------------------- 2. slide 17 wording (run level) + note
def rep(part, old, new):
    s = files[part].decode("utf-8"); n = s.count(old)
    assert n == 1, (part, old, n)
    files[part] = s.replace(old, new).encode("utf-8")
    log["text_edits"].append({"part": part, "old": old, "new": new})
rep("ppt/slides/slide17.xml", "<a:t>No geometric imperfections</a:t>", "<a:t>No measured geometric imperfections</a:t>")
rep("ppt/slides/slide17.xml", "<a:t>No nonlinear (post-)buckling analysis</a:t>", "<a:t>Nonlinear buckling: elastic LS-DYNA extension only</a:t>")
rep("ppt/slides/slide17.xml", "<a:t>imperfection-seeded load–deflection path to the limit point</a:t>", "<a:t>elastic–plastic, with tolerance-based imperfections</a:t>")
rep("ppt/notesSlides/notesSlide17.xml", "no imperfections, no plasticity, no post-buckling path.",
    "no imperfections, no plasticity, no post-buckling path. The additional LS-DYNA extension covers only the elastic, geometrically nonlinear part, with numerical imperfections.")
# ---------------------------------------------------------------- 3. cached slide-number field values of the moved slides
# slides 14-18 move to positions 17-21; the slidenum field is recomputed by PowerPoint, but its cached text is updated as well
for k in range(14, 19):
    part = f"ppt/slides/slide{k}.xml"; s = files[part].decode("utf-8")
    pat = re.compile(r'(<a:fld [^>]*type="slidenum"[^>]*>(?:(?!</a:fld>).)*?<a:t>)%d(</a:t>)' % k, re.S)
    s2, n = pat.subn(lambda m: m.group(1) + str(k + 3) + m.group(2), s)
    assert n == 1, (part, n)
    files[part] = s2.encode("utf-8")
    log["text_edits"].append({"part": part, "old": "slidenum field cached text %d" % k, "new": str(k + 3)})
# ---------------------------------------------------------------- write (existing entries keep their order and compression)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for n in zo.namelist():
        z.writestr(infos[n], files[n])
    for n in files:
        if n not in infos:
            z.writestr(n, files[n])
json.dump(log, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "section13_deck_edits_log.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("inserted", [s["title"] for s in log["inserted_slides"]], "| text edits", len(log["text_edits"]))
