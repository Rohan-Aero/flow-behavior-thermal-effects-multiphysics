# -*- coding: utf-8 -*-
"""Section 10B - converts the LaTeX master of the report into an editable DOCX (RE-ANALYSIS 2026).
The LaTeX source is the master; this conversion is secondary and loses some layout (sub-figure grids, coloured box,
two-column contents). Steps:
  1. flatten main.tex (inline every \\input);
  2. replace \\ref / \\eqref by the numbers LaTeX assigned (read from main.aux), prefix every caption with its number;
  3. simplify commands pandoc does not translate (coloured box, manual lists of figures/tables, trimming options);
  4. run pandoc with citeproc (IEEE CSL, numeric like the PDF) and a Word table of contents.
Usage: python make_docx.py <Source dir> <build dir with main.aux> <References dir> <Figures dir> <out.docx>"""
import os, re, sys, subprocess
SRC, BUILD, REF, FIG, OUT = sys.argv[1:6]


def flatten(path):
    txt = open(path, encoding="utf-8").read()

    def rep(m):                                   # LaTeX resolves \input relative to the Source directory
        name = m.group(1)
        return flatten(os.path.normpath(os.path.join(SRC, name if name.endswith(".tex") else name + ".tex")))
    return re.sub(r"\\input\{([^}]+)\}", rep, txt)


main = open(os.path.join(SRC, "main.tex"), encoding="utf-8").read()
body = main[main.find("\\begin{document}"):]
open(os.path.join(BUILD, "_body.tex"), "w", encoding="utf-8").write(body)
PRE = r"""\documentclass{report}
\newcommand{\diameter}{Ø}
\newcommand{\lamone}{\ensuremath{\lambda_1}}
\newcommand{\src}[1]{\par\emph{#1}\par}
\newcommand{\provmech}{ANSYS Mechanical image export (Graphics.ExportImage) of the solved result object, unedited.}
\newcommand{\provcfd}{Plotted with matplotlib from data exported from the converged ANSYS Fluent solution; not a GUI screenshot.}
\newcommand{\provmesh}{matplotlib render of the actual mesh arrays read by Fluent; not an ANSYS GUI screenshot.}
\newcommand{\provcad}{Rendered from the geometry exported by ANSYS SpaceClaim; not a GUI screenshot.}
\newcommand{\provdata}{Plotted with matplotlib from the solver output tables of this project.}
"""
tex = PRE + flatten(os.path.join(BUILD, "_body.tex"))
aux = open(os.path.join(BUILD, "main.aux"), encoding="utf-8", errors="ignore").read()
labels = dict(re.findall(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux))

# numbered captions: find each float, its label and caption
def number_caption(env, word):
    global tex
    out, pos = [], 0
    for m in re.finditer(r"\\begin\{%s\}.*?\\end\{%s\}" % (env, env), tex, re.S):
        block = m.group(0)
        lab = re.findall(r"\\label\{([^}]+)\}", block)
        lab = [l for l in lab if l.startswith(("fig:", "tab:"))]
        num = labels.get(lab[-1]) if lab else None
        if num:
            # the float-level caption is the last \caption in the block (sub-captions come first)
            idx = block.rfind("\\caption")
            j = idx + len("\\caption")
            if block[j] == "[":
                d, k = 0, j
                while True:
                    if block[k] == "[": d += 1
                    elif block[k] == "]":
                        d -= 1
                        if d == 0: break
                    k += 1
                block = block[:j] + block[k + 1:]
            block = block[:j] + block[j:].replace("{", "{%s %s: " % (word, num), 1)
        out.append(tex[pos:m.start()]); out.append(block); pos = m.end()
    out.append(tex[pos:]); tex = "".join(out)


# display equations: align blocks -> one equation per row (Word has no alignment points); the LaTeX number is
# written after each equation because pandoc does not number display math
def eq_row(row):
    labs = re.findall(r"\\label\{([^}]+)\}", row)
    row = re.sub(r"\\label\{[^}]+\}", "", row).replace("&", "").strip().rstrip("\\").strip()
    num = labels.get(labs[0]) if labs else None
    return "\\begin{equation*}\n%s%s\n\\end{equation*}" % (row, "\\qquad (%s)" % num if num else "")
tex = re.sub(r"\\begin\{align\}(.*?)\\end\{align\}",
             lambda m: "\n".join(eq_row(r) for r in re.split(r"\\\\\s*\n", m.group(1).strip()) if r.strip()), tex, flags=re.S)
tex = re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}", lambda m: eq_row(m.group(1)), tex, flags=re.S)

number_caption("figure", "Figure")
number_caption("table", "Table")
tex = re.sub(r"\\eqref\{([^}]+)\}", lambda m: "(%s)" % labels.get(m.group(1), "?"), tex)
tex = re.sub(r"\\ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "?"), tex)

# simplifications for pandoc
# text symbols pandoc drops silently; @{} inside \multicolumn makes pandoc drop the whole table
for a, b in (("textdegree", "°"), ("textmu", "µ"), ("textbullet", "•")):
    tex = re.sub(r"\\%s(?![a-zA-Z])(\{\})?[ ]?" % a, b if a != "textbullet" else b + " ", tex)   # the space ends the macro
tex = re.sub(r"\\multicolumn\{(\d+)\}\{@\{\}([lrc])\}", r"\\multicolumn{\1}{\2}", tex)
# math with an empty base (m$^2$, GCI$_{fine}$) becomes an empty OMML placeholder box in Word -> text super/subscripts;
# y^+ without braces makes Word attach the following relation to the exponent -> braced
tex = re.sub(r"\$\^\{?([0-9a-z]+)\}?\$", r"\\textsuperscript{\1}", tex)
tex = re.sub(r"\$_\{([a-z]+)\}\$", r"\\textsubscript{\1}", tex)
tex = tex.replace("^+", "^{\\text{+}}")
# inline math that starts with a relation ($< 10^{-4}$, $\le$) has no left operand; write the relation as text
REL = {"<": "<", ">": ">", "\\le": "≤", "\\leq": "≤", "\\ge": "≥", "\\geq": "≥", "\\approx": "≈", "\\sim": "∼"}
seg = re.split(r"(?<!\\)\$", tex)
assert len(seg) % 2 == 1, "unbalanced inline math"
for i in range(1, len(seg), 2):
    m = re.match(r"\s*(<|>|\\leq|\\le|\\geq|\\ge|\\approx|\\sim)(?![a-zA-Z])\s*(.*)$", seg[i], re.S)
    if m:
        rest = m.group(2).strip()
        seg[i] = "\x00" + REL[m.group(1)] + (" \x01" + rest + "\x01" if rest else "")
tex = ""
for i, s in enumerate(seg):
    if i % 2 and s.startswith("\x00"):
        tex += s[1:].replace("\x01", "$")
    elif i % 2:
        tex += "$" + s + "$"
    else:
        tex += s
tex = re.sub(r"\\text\{([^{}]*)\}", lambda m: "\\text{" + m.group(1).replace("\\,", " ") + "}", tex)
tex = tex.replace("\\recbox{", "\\begin{quote}\\textbf{}").replace("\\makeatletter", "").replace("\\makeatother", "")
tex = re.sub(r"\\begin\{quote\}\\textbf\{\}(.*?)\}\n", lambda m: "\\begin{quote}" + m.group(1) + "\\end{quote}\n", tex, flags=re.S)
tex = re.sub(r"\{\\small[^\n]*\\@starttoc\{toc\}[^\n]*\n", "", tex)
tex = re.sub(r"\{[^\n]*\\@starttoc\{(lof|lot)\}[^\n]*\n", "", tex)
tex = re.sub(r"\\includegraphics\[[^\]]*\]", "\\\\includegraphics[width=0.9\\\\linewidth]", tex)
tex = tex.replace("\\begin{titlepage}", "").replace("\\end{titlepage}", "")
tex = tex.replace("\\cleardoublepage", "").replace("\\clearpage", "")
tex = re.sub(r"\\chapter\*\{Contents\}\n\\addcontentsline\{toc\}\{chapter\}\{Contents\}\n", "", tex)
tex = re.sub(r"\\phantomsection\n\\addcontentsline\{toc\}\{chapter\}\{List of (Figures|Tables)\}\n\{\\sffamily\\bfseries\\LARGE List of (Figures|Tables)\\par\}\\vspace\{2pt\}\\hrule\\vspace\{8pt\}\n", "", tex)
tex = tex.replace("{\\sffamily\\bfseries\\LARGE List of Abbreviations and Symbols\\par}\\vspace{2pt}\\hrule\\vspace{6pt}",
                  "\\chapter*{List of Abbreviations and Symbols}")
tex = tex.replace("\\bibliographystyle{unsrtnat}\n\\bibliography{refs}", "\\section*{References}\n")
# figures -> non-floating blocks: each (sub)image on its own line, sub-caption below it, numbered caption as a paragraph
def defloat(m):
    blk = m.group(0)
    cap_i = blk.rfind("\\caption")
    parts = []
    for sm in re.finditer(r"\\begin\{subfigure\}.*?\\includegraphics\[[^\]]*\]\{([^}]+)\}.*?\\caption\{(.*?)\}\\end\{subfigure\}", blk, re.S):
        parts.append("\\includegraphics[width=0.72\\linewidth]{%s}\n\n\\emph{(%s) %s}\n" % (sm.group(1), "abcdefgh"[len(parts)], sm.group(2)))
    if not parts:
        for im in re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", blk):
            parts.append("\\includegraphics[width=0.9\\linewidth]{%s}\n" % im)
    # caption text with balanced braces
    j = blk.find("{", cap_i); d = 0; k = j
    while True:
        if blk[k] == "{": d += 1
        elif blk[k] == "}":
            d -= 1
            if d == 0: break
        k += 1
    cap = blk[j + 1:k]
    srcm = re.search(r"\\src\{(.*)\}\s*\\end\{figure\}", blk, re.S)
    src = "\n\\emph{%s}\n" % srcm.group(1) if srcm else ""
    w, _, rest = cap.partition(": ")
    return "\n".join(parts) + "\n\\textbf{%s:} %s\n%s\n" % (w, rest, src)
tex = re.sub(r"\\begin\{figure\}\[[^\]]*\].*?\\end\{figure\}", defloat, tex, flags=re.S)

# table column specs -> simple l/r columns so that Word auto-fits them
def simple_spec(spec):
    spec = re.sub(r">\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", "", spec)
    spec = re.sub(r"@\{[^}]*\}", "", spec)
    spec = re.sub(r"p\{[^}]*\}", "l", spec).replace("X", "l")
    return "".join(ch for ch in spec if ch in "lrc")
tex = re.sub(r"\\begin\{tabularx\}\{[^}]*\}\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}", lambda m: "\\begin{tabular}{%s}" % simple_spec(m.group(1)), tex)
tex = tex.replace("\\end{tabularx}", "\\end{tabular}")
tex = re.sub(r"\\begin\{tabular\}\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}", lambda m: "\\begin{tabular}{%s}" % simple_spec(m.group(1)), tex)

# explicit heading numbers (pandoc cannot number appendices with letters)
out, ch, sec, app = [], 0, 0, False
for line in tex.split("\n"):
    if line.startswith("\\appendix"):
        app, ch = True, 0; continue
    m = re.match(r"\\chapter\{(.*)\}(.*)$", line)
    if m:
        ch += 1; sec = 0
        num = ("Appendix " + "ABCDEFGH"[ch - 1]) if app else str(ch)
        line = "\\chapter*{%s  %s}%s" % (num, m.group(1), m.group(2))
    m = re.match(r"\\section\{(.*)\}(.*)$", line)
    if m:
        sec += 1
        line = "\\section*{%s.%d  %s}%s" % ("ABCDEFGH"[ch - 1] if app else ch, sec, m.group(1), m.group(2))
    out.append(line)
tex = "\n".join(out)
flat = os.path.join(BUILD, "report_flat_for_docx.tex")
open(flat, "w", encoding="utf-8").write(tex)
cmd = ["pandoc", flat, "-f", "latex", "-t", "docx", "-o", OUT, "--toc", "--toc-depth=2", "--citeproc",
       "--bibliography", os.path.join(REF, "refs.bib"), "--csl", os.path.join(REF, "ieee.csl"),
       "--resource-path", FIG + os.pathsep + SRC, "--metadata", "reference-section-title=References"]
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.returncode, r.stderr[-3000:])
