"""Lettore XLSX minimo (solo libreria standard): restituisce le righe del primo foglio come liste di stringhe."""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def col_idx(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_rows(path, sheet="xl/worksheets/sheet1.xml"):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    rows = []
    for r in ET.fromstring(z.read(sheet)).iter("{%s}row" % NS["m"]):
        out = []
        for c in r.findall("m:c", NS):
            i = col_idx(c.get("r"))
            v = c.find("m:v", NS)
            if v is None:
                t = c.find("m:is/m:t", NS)
                val = t.text if t is not None else ""
            else:
                val = shared[int(v.text)] if c.get("t") == "s" else v.text
            while len(out) < i:
                out.append("")
            out.append(val)
        rows.append(out)
    return rows
