print("PYPROBE-START")
import sys
print("PYPROBE python:", sys.version.replace("\n", " "))
g = sorted([k for k in list(globals().keys()) if not k.startswith("_")])
print("PYPROBE globals:", g)
for name in ("solver", "session", "root", "pyfluent", "flobject"):
    print("PYPROBE has", name, ":", name in globals())
try:
    import ansys.fluent.core as pf
    print("PYPROBE ansys.fluent.core:", pf.__version__)
except Exception as e:
    print("PYPROBE ansys.fluent.core import failed:", type(e).__name__, e)
try:
    print("PYPROBE solver.setup:", solver.setup)
except Exception as e:
    print("PYPROBE solver.setup failed:", type(e).__name__, e)
print("PYPROBE-END")
