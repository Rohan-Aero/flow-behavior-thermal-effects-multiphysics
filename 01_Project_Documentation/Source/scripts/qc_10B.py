# -*- coding: utf-8 -*-
"""Section 10B - quality control of the final report (RE-ANALYSIS 2026).
Checks, on the LaTeX sources and the build log (the PDF is produced from exactly these files):
  1. numbers   - every number in the text, tables and appendices is traced to the master dataset
                 (11_Final_Audit/MASTER_PROJECT_DATA.csv, rounding and unit-scale aware) or to a project document
                 (exact token, or a rounding of a value in a result document); what remains is listed for review;
  2. wording   - forbidden / sensitive words with their sentence (validated, safe, best, optimal, adequate, recovered ...);
  3. hygiene   - placeholders (TODO, TBD, ??, XXX), undefined references / citations, overfull boxes;
  4. structure - figure and table numbering sequential, every float referenced in the text, every figure with a
                 provenance line, every table with a source note, every cited key in refs.bib and vice versa;
  5. content   - verbatim re-analysis note, modelling-level labels next to 581.7 / 562.58 / 560.83 / 657.2 / 605.16.
Writes a JSON record. Usage:
  python qc_10B.py <13_Report dir> <build dir> <MASTER_PROJECT_DATA.csv> <out.json> <corpus dir> [<corpus dir> ...]"""
import os, re, sys, csv, json, bisect, hashlib, glob
R, B, MCSV, OUT = sys.argv[1:5]
CORPUS = sys.argv[5:]
res = {"inputs": {"master_csv": MCSV, "master_sha256": hashlib.sha256(open(MCSV, "rb").read()).hexdigest().upper(),
                  "corpus_dirs": CORPUS}}

# ------------------------------------------------------------------ report sources
chap = sorted(glob.glob(os.path.join(R, "Source", "chapters", "*.tex")))
appx = [os.path.join(R, "Appendices", "appendices.tex")]
input_tabs = set()
for f in chap + appx:
    input_tabs.update(re.findall(r"\\input\{\.\./Tables/([^}]+)\}", open(f, encoding="utf-8").read()))
tabs = [os.path.join(R, "Tables", t + ".tex") for t in sorted(input_tabs)]
FILES = chap + appx + tabs
SRC = {f: open(f, encoding="utf-8").read() for f in FILES}


def strip_comments(t):
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", l) for l in t.split("\n"))


# ------------------------------------------------------------------ 1. numbers
def load_master():
    vals, rows = [], {}
    with open(MCSV, encoding="utf-8") as fh:
        lines = [l for l in fh if not l.startswith("#")]
    for r in csv.DictReader(lines):
        rows[r["ID"]] = r
        for col in ("Value", "Documented value"):
            for tok in NUM.findall((r.get(col) or "").replace(",", "") if re.fullmatch(r"[-0-9.,eE+ ]*", r.get(col) or "") else (r.get(col) or "")):
                try:
                    vals.append((abs(float(tok)), r["ID"]))
                except ValueError:
                    pass
    return vals, rows


NUM = re.compile(r"(?<![A-Za-z_\d.])\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
MVALS, MROWS = load_master()
MVALS.sort()
MV = [v for v, _ in MVALS]


def canon(s):
    s = s.lstrip("-+").replace(",", "")
    if "e" in s.lower():
        return "%.6g" % float(s)
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.lstrip("0") or "0"


SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻−", "0123456789--")


def build_corpus():
    exact, rounded, nfiles = {}, [], 0
    for root in CORPUS:
        for dp, dn, fn in os.walk(root):
            if "S10B" in dp or "13_Report" in dp:
                continue
            for f in fn:
                p = os.path.join(dp, f)
                ext = f.lower().rsplit(".", 1)[-1]
                try:
                    sz = os.path.getsize(p)
                except OSError:
                    continue
                if ext in ("md", "json", "txt", "tsv", "py", "out", "log") and sz < 3e6 or ext == "csv" and sz < 3e5:
                    try:
                        t = open(p, encoding="utf-8", errors="ignore").read()
                    except OSError:
                        continue
                    nfiles += 1
                    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)
                    t = re.sub(r"(\d+(?:\.\d+)?)\s*[×x·*]\s*10\s*\^?\{?([-−⁻]?[0-9⁰¹²³⁴⁵⁶⁷⁸⁹]+)\}?",
                               lambda m: " %se%s " % (m.group(1), m.group(2).translate(SUP)), t)
                    rel = os.path.relpath(p, root)
                    for tok in NUM.findall(t):
                        c = canon(tok)
                        if c not in exact:
                            exact[c] = rel
                        # rounding pool: result documents and tables, not iteration histories (random-like numbers)
                        if ext in ("md", "csv", "json") and not re.search(r"monitor|residual|history|nodal|mode\d", rel, re.I):
                            try:
                                rounded.append((float(tok), rel))
                            except ValueError:
                                pass
    rounded.sort()
    return exact, rounded, nfiles


CEXACT, CROUND, NCF = build_corpus()
CRV = [v for v, _ in CROUND]
res["inputs"]["corpus_files_scanned"] = NCF


def in_interval(arr, pairs, x, d):
    h = 0.5 * 10 ** (-d) * (1 + 1e-9)
    i = bisect.bisect_left(arr, x - h)
    return pairs[i] if i < len(arr) and arr[i] <= x + h else None


SCALES = [(1, ""), (1e3, "x1e3"), (1e-3, "x1e-3"), (1e6, "x1e6"), (1e-6, "x1e-6"), (100, "x100"), (0.01, "x0.01")]


def trace(tok):
    """tok: canonical number string as printed. Returns (class, where)."""
    x = float(tok)
    if "e" in tok:
        m, e = tok.lower().split("e")
        d = (len(m.split(".")[1]) if "." in m else 0) - int(e)
    else:
        d = len(tok.split(".")[1]) if "." in tok else 0
    for s, lab in SCALES:
        # the rounding interval is evaluated in the master unit: scale the half-width with the factor
        h = 0.5 * 10 ** (-d) * s * (1 + 1e-9)
        i = bisect.bisect_left(MV, x * s - h)
        if i < len(MV) and MV[i] <= x * s + h:
            return "master", MVALS[i][1] + ((" " + lab) if lab else "")
    c = canon(tok)
    if c in CEXACT:
        return "document-exact", CEXACT[c]
    h = 0.5 * 10 ** (-d) * (1 + 1e-9)
    i, hits = bisect.bisect_left(CRV, x - h), []
    while i < len(CRV) and CRV[i] <= x + h:
        hits.append(CROUND[i][1]); i += 1
    if hits:                                         # prefer a result document (.md) as the attribution
        return "document-rounded", sorted(hits, key=lambda p: (not p.endswith(".md"), len(p)))[0]
    return "untraced", ""


def numbers_in(text):
    """(token, context) pairs of the numbers a reader sees, excluding cross-reference and identifier numbers."""
    t = strip_comments(text)
    t = re.sub(r"\\begin\{(equation|align)\}.*?\\end\{\1\}", " ", t, flags=re.S)          # correlation constants: cited equations
    for pat in [r"\\(label|ref|eqref|cite|citep|citet|input|includegraphics|texttt|url|href|pageref)(\[[^\]]*\])?\{[^}]*\}",
                r"\\begin\{(tabular|tabularx|subfigure|minipage|multicols)\}(\[[^\]]*\])?(\{[^{}]*(\{[^{}]*\}[^{}]*)*\})+",
                r"\\(vspace|hspace|setlength|addtolength|rule|resizebox|scalebox|multicolumn|multirow|columnbreak|titleformat|arraystretch|renewcommand)\*?(\{[^{}]*\})+",
                r"\[[\d.]+(pt|mm|em|ex)\]", r"[\d.]+\\(linewidth|textwidth|textheight|columnwidth)", r"\{[\d.]+(pt|mm|em|ex|cm)\}",
                r"(Figures?|Tables?|Chapters?|Sections?|Equations?|Appendix|Appendices|Eqs?\.|Eq\.|\\S|§)[~ ]?\(?[\dA-H]+(\.\d+)?[A-C]?\d?\)?((--|–|,| and |~and~| to )[\dA-H]+(\.\d+)?[A-C]?\d?)*",
                r"(?<![A-Za-z])(rows?|M)\s?M?\d{3}(--M?\d{3})?", r"\b[A-Z]{1,3}-?\d{2,3}[A-Z]?\b", r"\b(LC|S|V|Q|T|P|B|F|MI|SOLID|R|XC|C|FR|FA|FC)\d+[A-Z]?\b",
                r"\b(19|20)\d\d\b", r"\\(bibitem|chapter|section|subsection)\b"]:
        t = re.sub(pat, " ", t)
    t = re.sub(r"(\d)\{,\}(\d)", r"\1\2", t)
    t = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", t)
    # scientific notation a\times10^{-n}
    t = re.sub(r"(\d+(?:\.\d+)?)\s*\\times\s*10\^\{?(-?\d+)\}?", lambda m: " %se%s " % (m.group(1), m.group(2)), t)
    t = re.sub(r"(?<![\d.e])10\^\{?(-?\d+)\}?", lambda m: " 1e%s " % m.group(1), t)
    t = re.sub(r"[\^_]\{?[\d./]+\}?", " ", t)                               # exponents / subscripts inside math
    out = []
    for m in re.finditer(r"(?<![A-Za-z_\d.\\])\d+(?:\.\d+)?(?:e-?\d+)?(?![A-Za-z\d])", t):
        tok = m.group(0)
        ctx = re.sub(r"\s+", " ", t[max(0, m.start() - 60):m.end() + 40])
        out.append((tok, ctx))
    return out


num_rows, counts = [], {}
for f in FILES:
    for tok, ctx in numbers_in(SRC[f]):
        c = canon(tok) if "e" not in tok else tok
        sig = len(re.sub(r"[^\d]", "", tok.split("e")[0]).lstrip("0"))
        cls, where = trace(c if "e" not in tok else tok)
        if cls == "untraced" and sig <= 1:
            cls = "single-digit"                     # counts, enumerations, 'two', ordinal-like - not a result value
        counts[cls] = counts.get(cls, 0) + 1
        num_rows.append({"file": os.path.relpath(f, R), "number": tok, "sig_digits": sig, "class": cls, "traced_to": where, "context": ctx})
info = {}
for r in num_rows:
    if r["sig_digits"] >= 3:
        info[r["class"]] = info.get(r["class"], 0) + 1
res["numbers"] = {"total": len(num_rows), "by_class": counts, "by_class_3plus_significant_digits": info,
                  "untraced": [r for r in num_rows if r["class"] == "untraced"],
                  "document_rounded": [r for r in num_rows if r["class"] == "document-rounded"],
                  "all": num_rows}

# ------------------------------------------------------------------ 2. wording
WORDS = {"validat": r"\bvalidat\w*", "safe": r"\bsafe\w*|\bsafety\b", "best": r"\bbest\b", "worst": r"\bworst\b",
         "optimal": r"\boptim\w*", "failure-proof": r"failure[- ]proof", "revolutionary": r"revolutionar", "cutting-edge": r"cutting[- ]edge",
         "highly accurate": r"highly accurate", "guarantee": r"\bguarant\w*", "adequa": r"\badequa\w*", "recovered": r"\brecover\w*",
         "factor of safety": r"factor of safety|safety factor", "proven": r"\bprove[dn]?\b", "experimentally": r"experimental\w*"}
NEG = re.compile(r"\b(not|no|never|nor|without|cannot|unavailable|rather than|instead|would|only route|none|neither)\b|n't", re.I)
fulltext = {f: strip_comments(SRC[f]) for f in FILES}
fulltext[os.path.join(R, "Source", "main.tex")] = strip_comments(open(os.path.join(R, "Source", "main.tex"), encoding="utf-8").read())
wording = []
for f, t in fulltext.items():
    flat = re.sub(r"\s+", " ", t)
    for key, pat in WORDS.items():
        for m in re.finditer(pat, flat, re.I):
            a = max(flat.rfind(". ", 0, m.start()), flat.rfind("\\item", 0, m.start()), flat.rfind("\\par", 0, m.start()), 0)
            b = flat.find(". ", m.end()); b = len(flat) if b < 0 else b
            sent = flat[a:b + 1].strip(". ")
            wording.append({"file": os.path.relpath(f, R), "word": key, "negated_or_conditional": bool(NEG.search(sent)), "sentence": sent[:400]})
res["wording"] = {"occurrences": len(wording), "not_negated": [w for w in wording if not w["negated_or_conditional"]], "all": wording}

# ------------------------------------------------------------------ 3. hygiene
PH = re.compile(r"TODO|TBD|FIXME|XXX|\?\?|\[citation|lorem ipsum|PLACEHOLDER|INSERT", re.I)
res["placeholders"] = [{"file": os.path.relpath(f, R), "line": i + 1, "text": l.strip()[:160]}
                       for f, t in fulltext.items() for i, l in enumerate(t.split("\n")) if PH.search(l)]
log = open(os.path.join(B, "main.log"), encoding="utf-8", errors="ignore").read()
res["log"] = {"undefined_references": len(re.findall(r"Reference `[^']+' on page", log)),
              "undefined_citations": len(re.findall(r"Citation `[^']+' on page", log)),
              "multiply_defined": len(re.findall(r"multiply defined", log)),
              "overfull_boxes": len(re.findall(r"Overfull \\hbox", log)),
              "latex_warnings": len(re.findall(r"LaTeX Warning", log)),
              "missing_figures": len(re.findall(r"File `[^']+' not found", log)),
              "pages": int(re.search(r"Output written on .*?\((\d+) pages", log, re.S).group(1))}

# ------------------------------------------------------------------ 4. structure
def entries(ext):
    return re.findall(r"\\contentsline \{(?:figure|table)\}\{\\numberline \{([^}]+)\}", open(os.path.join(B, "main." + ext), encoding="utf-8").read())


def sequential(nums):
    bad, last = [], {}
    for n in nums:
        c, k = n.rsplit(".", 1)
        if int(k) != last.get(c, 0) + 1:
            bad.append(n)
        last[c] = int(k)
    return bad


figs, tbls = entries("lof"), entries("lot")
alltext = "\n".join(fulltext.values())
floats = {"figure": [], "table": []}
for f in FILES:
    for env in ("figure", "table"):
        for m in re.finditer(r"\\begin\{%s\}.*?\\end\{%s\}" % (env, env), fulltext[f], re.S):
            lab = [l for l in re.findall(r"\\label\{([^}]+)\}", m.group(0)) if l.startswith(("fig:", "tab:"))][-1]
            others = alltext.replace(m.group(0), "")
            floats[env].append({"label": lab, "file": os.path.relpath(f, R),
                                "referenced": bool(re.search(r"\\ref\{%s\}" % re.escape(lab), others)),
                                "provenance_or_source_note": ("\\src{" in m.group(0)) if env == "figure" else ("Source" in m.group(0))})
bib = open(os.path.join(R, "References", "refs.bib"), encoding="utf-8").read()
bibkeys = set(re.findall(r"@\w+\{([^,]+),", bib))
cited = set(k.strip() for g in re.findall(r"\\cite[pt]?\{([^}]+)\}", alltext) for k in g.split(","))
res["structure"] = {"figures": len(figs), "tables": len(tbls), "figure_numbering_gaps": sequential(figs), "table_numbering_gaps": sequential(tbls),
                    "floats_not_referenced": [x["label"] for e in floats.values() for x in e if not x["referenced"]],
                    "figures_without_provenance": [x["label"] for x in floats["figure"] if not x["provenance_or_source_note"]],
                    "tables_without_source_note": [x["label"] for x in floats["table"] if not x["provenance_or_source_note"]],
                    "cited_not_in_bib": sorted(cited - bibkeys), "bib_not_cited": sorted(bibkeys - cited), "bib_entries": len(bibkeys)}

# ------------------------------------------------------------------ 5. content
NOTE = ("The original internship project files were unavailable at the time of re-analysis. Accordingly, the geometry, operating parameters, "
        "simulation setup and numerical results presented in this report are re-analysed engineering work based on the surviving project "
        "documentation and newly generated ANSYS simulations. They should not be interpreted as recovered copies of the original internship analysis.")
fm = re.sub(r"\s+", " ", fulltext[os.path.join(R, "Source", "chapters", "frontmatter.tex")])
LEVEL = {"581.7": r"analytic|one-dimensional|Section 2|1-D", "562.58": r"medium|baseline|CFD|Fluent|P00", "560.83": r"fine",
         "657.2": r"analytic|restrained|hand|closed-form|-E", "605.16": r"FE|peak|von Mises|LC2|VM"}
lev = []
for f, t in fulltext.items():
    flat = re.sub(r"\s+", " ", t)
    for v, pat in LEVEL.items():
        for m in re.finditer(re.escape(v), flat):
            # in a table the caption and column headers carry the level; in running text the surrounding sentence(s)
            win = flat if "/Tables/" in f else flat[max(0, m.start() - 250):m.end() + 120]
            lev.append({"file": os.path.relpath(f, R), "value": v, "level_label_nearby": bool(re.search(pat, win, re.I))})
res["content"] = {"re_analysis_note_verbatim": NOTE in fm,
                  "modelling_level_occurrences": len(lev), "modelling_level_unlabelled": [x for x in lev if not x["level_label_nearby"]]}

json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps({"numbers": res["numbers"]["by_class"], "numbers_3sig": info, "untraced": len(res["numbers"]["untraced"]),
                  "wording_not_negated": len(res["wording"]["not_negated"]), "placeholders": len(res["placeholders"]),
                  "log": res["log"], "structure": {k: v for k, v in res["structure"].items()},
                  "note": res["content"]["re_analysis_note_verbatim"], "level_unlabelled": len(res["content"]["modelling_level_unlabelled"])}, indent=1))
