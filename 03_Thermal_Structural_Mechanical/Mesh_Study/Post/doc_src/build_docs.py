# builds the Section 8B markdown documents: replaces {{Tn}} with the generated tables of Post/out/tables_8B.md
import re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
T = open(os.path.join(HERE, "..", "..", "Post", "out", "tables_8B.md")).read()
blocks = {}
for part in T.split("### ")[1:]:
    key = part.split(".")[0].strip()
    body = part.split("\n", 1)[1].strip()
    title = part.split("\n", 1)[0].strip()
    blocks[key] = "**%s**\n\n%s" % (title.split(". ", 1)[1], body)
for f in sys.argv[1:]:
    s = open(os.path.join(HERE, f)).read()
    s = re.sub(r"\{\{(T\d)\}\}", lambda m: blocks[m.group(1)], s)
    out = os.path.join(HERE, "..", f.replace(".src.md", ".md"))
    open(out, "w").write(s)
    print("built", out, len(s))
