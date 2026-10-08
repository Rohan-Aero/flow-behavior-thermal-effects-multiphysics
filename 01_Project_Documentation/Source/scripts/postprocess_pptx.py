# -*- coding: utf-8 -*-
"""Section 10C-1 - post-process the generated deck (RE-ANALYSIS 2026).
pptxgenjs applies line style and markers to every series of a chart. The lambda1 = 1 reference series of the
parametric charts (series name 'ref_lambda_1') is restyled here to a thin dashed grey line without markers,
so it reads as a reference line and not as data. No data value is changed.
Usage: python postprocess_pptx.py <deck.pptx>"""
import re, sys, zipfile, shutil, os, tempfile

deck = sys.argv[1]
tmp = tempfile.mktemp(suffix=".pptx")
n = 0
with zipfile.ZipFile(deck) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename.startswith("ppt/charts/chart") and item.filename.endswith(".xml"):
            xml = data.decode("utf-8")

            def fix(m):
                global n
                ser = m.group(0)
                if "ref_lambda_1" not in ser:
                    return ser
                n += 1
                ser = re.sub(r"<a:ln w=\"\d+\"", '<a:ln w="15875"', ser, count=1)                      # 1.25 pt
                ser = re.sub(r"(<c:spPr>.*?<a:ln[^>]*>.*?)<a:prstDash val=\"[a-zA-Z]+\"/>", r'\1<a:prstDash val="dash"/>', ser, count=1, flags=re.S)
                ser = re.sub(r"<c:marker>.*?</c:marker>", '<c:marker><c:symbol val="none"/></c:marker>', ser, count=1, flags=re.S)
                return ser
            xml = re.sub(r"<c:ser>.*?</c:ser>", fix, xml, flags=re.S)
            data = xml.encode("utf-8")
        zout.writestr(item, data)
shutil.move(tmp, deck)
print("reference series restyled:", n)
