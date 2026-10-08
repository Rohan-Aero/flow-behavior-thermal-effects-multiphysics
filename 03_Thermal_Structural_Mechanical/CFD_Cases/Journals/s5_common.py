# -*- coding: utf-8 -*-
"""Shared helpers for the Section 5B Fluent journals (run inside Fluent's Python console).

Every setter verifies by reading the value back out of Fluent. Section 5A showed that the
settings API can (a) raise while succeeding and (b) succeed while silently falling back
to a different value; neither the exception nor its absence can be trusted on its own.
"""
import os, re, json, traceback

LOG = []
FAIL = []


def log(msg):
    LOG.append(str(msg))
    print("S5B " + str(msg))


def step(label, fn, critical=True):
    try:
        r = fn()
        log("OK    %-54s %s" % (label, "" if r is None else repr(r)[:110]))
        return r
    except Exception as e:
        FAIL.append(("CRITICAL " if critical else "minor ") + "%s: %s: %s" % (label, type(e).__name__, e))
        log("%-5s %-54s %s: %s" % ("FAIL" if critical else "warn", label, type(e).__name__, str(e)[:140]))
        return None


def _close(a, b, rtol=1e-6):
    try:
        return abs(float(a) - float(b)) <= 1e-9 + rtol * abs(float(b))
    except Exception:
        return a == b


def readv(parent, name):
    node = getattr(parent, name)
    for fn in (lambda: node.value(), lambda: node()):
        try:
            v = fn()
            if isinstance(v, dict) and "value" in v:
                return v["value"]
            if isinstance(v, (int, float, str, bool)):
                return v
        except Exception:
            continue
    return None


def setv(parent, name, val):
    node = getattr(parent, name)
    errs = []
    for how, fn in (("value", lambda: setattr(node, "value", val)),
                    ("direct", lambda: setattr(parent, name, val)),
                    ("set_state", lambda: node.set_state(val))):
        try:
            fn()
            got = readv(parent, name)
            if got is None or _close(got, val):
                return "%s <- %s (%s, read back %s)" % (name, val, how, got)
            errs.append("%s gave %r" % (how, got))
        except Exception as e:
            errs.append("%s: %s" % (how, type(e).__name__))
    raise RuntimeError("; ".join(errs))


def set_scheme(ds, key, val):
    """Set one discretisation scheme and prove it by read-back."""
    try:
        ds[key] = val
    except Exception:
        pass
    got = ds[key]()
    if got != val:
        raise RuntimeError("scheme %s is %r, wanted %r" % (key, got, val))
    return got


def read_report_file(path):
    """Parse a Fluent report (.out) file -> (header list, list of float rows)."""
    hdr, rows = None, []
    if not os.path.isfile(path):
        return hdr, rows
    with open(path, "r", errors="ignore") as fh:
        for l in fh:
            s = l.strip()
            if s.startswith('("Iteration"') or s.startswith('("Time Step"'):
                hdr = re.findall(r'"([^"]+)"', s)
                continue
            if hdr and re.match(r"^\d+\s", s):
                try:
                    rows.append([float(x) for x in s.split()])
                except ValueError:
                    pass
    return hdr, rows


def write_json(path, obj):
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2, default=str)


def flush_log(path):
    with open(path, "w") as fh:
        fh.write("\n".join(LOG))
