"""Icone delle macro-aree italiane (Nord, Centro, Sud e Isole) per la scheda prodotto.

Ogni icona ha il contorno di tutta l'Italia (Natural Earth 1:50m, già in data/raw/naturalearth/) e l'area
interessata piena. Le aree sono ritagliate con una maschera SVG: i confini tra le macro-aree sono spezzate
che approssimano i confini delle regioni elencate in metadata.italy_macro_areas_legend.*.regions (raggruppamento scelto dall'utente, con l'Abruzzo nel Centro) (Nord: fino a Liguria ed Emilia-Romagna; Centro: Toscana,
Umbria, Marche, Lazio e Abruzzo; Sud e Isole: da Molise e Campania in giù, Sicilia e Sardegna). A 20 px di icona la
precisione regionale non si vede; per un confine esatto servirebbero i poligoni delle regioni.

Uscita: app/assets/icons/italy/{nord,centro,sud_isole}.svg (colore = currentColor, ricolorate dall'app).
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/raw/naturalearth/ne_50m_admin_0_countries.geojson"
OUT = ROOT / "app/assets/icons/italy"

LON0, LAT_TOP = 6.4, 47.2
KX = math.cos(math.radians(42))
SIZE, PAD = 24.0, 1.0

# Confini delle macro-aree (lon, lat). Poligoni anche concavi: servono solo come maschera.
NORD = [(5, 47.5), (19, 47.5), (19, 43.95), (12.8, 43.95), (12.3, 43.75), (11.0, 44.2), (10.02, 44.05),
        (10.02, 43.6), (5, 43.6)]
# Centro con l'Abruzzo (scelta dell'utente, 2026-11-12): il confine con il Sud segue Lazio-Campania e
# Abruzzo-Molise (foce del Trigno).
CENTRO = [(9.5, 43.6), (10.02, 43.6), (10.02, 44.05), (11.0, 44.2), (12.3, 43.75), (12.8, 43.95), (15.2, 43.95),
          (15.2, 42.1), (14.78, 42.07), (14.45, 41.85), (14.1, 41.72), (13.95, 41.6), (13.8, 41.3), (13.8, 41.0),
          (10.5, 41.0), (10.5, 41.4), (9.5, 41.4)]
SUD = [(19, 43.95), (15.2, 43.95), (15.2, 42.1), (14.78, 42.07), (14.45, 41.85), (14.1, 41.72), (13.95, 41.6),
       (13.8, 41.3), (13.8, 41.0), (10.5, 41.0), (10.5, 41.4), (9.5, 41.4), (5, 41.4), (5, 35), (19, 35)]
AREAS = {"nord": NORD, "centro": CENTRO, "sud_isole": SUD}


def italy_rings():
    gj = json.load(open(SRC, encoding="utf-8"))
    for f in gj["features"]:
        if f["properties"].get("ADM0_A3") == "ITA":
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            return [p[0] for p in polys]  # solo il bordo esterno
    raise SystemExit("Italia non trovata")


def simplify(pts, tol):
    """Douglas-Peucker (anello chiuso: si tiene sempre il primo punto)."""
    if len(pts) < 4:
        return pts

    def dist(p, a, b):
        (x, y), (x1, y1), (x2, y2) = p, a, b
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            return math.hypot(x - x1, y - y1)
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))

    def rec(a, b):
        i, dmax = None, tol
        for k in range(a + 1, b):
            d = dist(pts[k], pts[a], pts[b])
            if d > dmax:
                i, dmax = k, d
        return [pts[a]] if i is None else rec(a, i) + rec(i, b)

    far = max(range(len(pts)), key=lambda k: math.hypot(pts[k][0] - pts[0][0], pts[k][1] - pts[0][1]))
    return rec(0, far) + rec(far, len(pts) - 1) + [pts[-1]]


def area(r):
    return abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))) / 2


def build():
    rings = [r for r in italy_rings() if area(r) > 0.02]  # via gli isolotti
    xs = [(lon - LON0) * KX for r in rings for lon, _ in r]
    ys = [LAT_TOP - lat for r in rings for _, lat in r]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    s = (SIZE - 2 * PAD) / max(w, h)
    ox = (SIZE - w * s) / 2 - min(xs) * s
    oy = (SIZE - h * s) / 2 - min(ys) * s

    def P(lon, lat):
        return ((lon - LON0) * KX * s + ox, (LAT_TOP - lat) * s + oy)

    def path(points, close=True):
        out = "M" + " ".join(f"{x:.2f} {y:.2f}" for x, y in points)
        return out + ("Z" if close else "")

    land = "".join(path(simplify([P(*p) for p in r], 0.08)) for r in rings)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, poly in AREAS.items():
        mask_poly = path([P(*p) for p in poly])
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">'
               f'<mask id="it-{name}"><path d="{mask_poly}" fill="#fff"/></mask>'
               f'<path d="{land}" mask="url(#it-{name})"/>'
               f'<path d="{land}" fill="none" stroke="currentColor" stroke-width="0.9" stroke-linejoin="round"/>'
               '</svg>')
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(name, f"{len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    build()
