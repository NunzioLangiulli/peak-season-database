"""Mappa dell'Europa colorata per zona climatica EUFIC (SVG per l'app).

Dati:
- confini: Natural Earth "Admin 0 - Countries" 1:50m (pubblico dominio),
  data/raw/naturalearth/ne_50m_admin_0_countries.geojson
- zone, Paesi (ISO 3166-1 alpha-2) e colori: database,
  metadata.eufic_climatic_zones_legend (countries_primary_iso,
  countries_partial_iso, color_hex)
- regioni: EEA "Biogeographical regions, Europe 2016" (EEA, Copenaghen, 2016; CC BY 4.0),
  scaricate semplificate dal servizio ArcGIS EEA in EPSG:3035:
  data/raw/eea_biogeo/biogeo_regions_3035_simplified.geojson
Output:
- app/assets/maps/europe_zones_light.svg e europe_zones_dark.svg: zone continue come
  sulla mappa EUFIC (regioni EEA colorate con i colori del database, confini degli Stati sopra)
- app/assets/icons/season/europe.svg (sagoma reale dell'Europa per l'icona "Zona Climatica")
Proiezione: azimutale equivalente di Lambert centrata su 10°E 52°N (come ETRS89-LAEA).
Uso: python scripts/build_europe_map.py
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NE = ROOT / "data" / "raw" / "naturalearth" / "ne_50m_admin_0_countries.geojson"
DB = ROOT / "data" / "database.json"
EEA = ROOT / "data" / "raw" / "eea_biogeo" / "biogeo_regions_3035_simplified.geojson"
OUT_MAP = ROOT / "app" / "assets" / "maps"

# Regione EEA -> zona dell'app: letta dal database
# (eufic_climatic_zones_legend.<zona>.eea_regions, approssimazioni in eea_regions_approx).
ARCTIC = "#5B6670"  # come su EUFIC: Artica in grigio (non è una zona dell'app)
FE, FN, R = 4321000.0, 3210000.0, 6371007.0  # EPSG:3035 → coordinate sulla sfera unitaria
OUT_ICON = ROOT / "app" / "assets" / "icons" / "season" / "europe.svg"

LON0, LAT0 = math.radians(10), math.radians(52)
VIEW = (-25, 34, 40, 72)          # lon min, lat min, lon max, lat max della mappa
ICON_VIEW = (-11, 35, 32, 71.5)    # area più stretta per l'icona (niente Islanda/Russia)
W = 1000                           # larghezza SVG della mappa


def laea(lon, lat):
    lam, phi = math.radians(lon), math.radians(lat)
    k = math.sqrt(2 / (1 + math.sin(LAT0) * math.sin(phi) + math.cos(LAT0) * math.cos(phi) * math.cos(lam - LON0)))
    x = k * math.cos(phi) * math.sin(lam - LON0)
    y = k * (math.cos(LAT0) * math.sin(phi) - math.sin(LAT0) * math.cos(phi) * math.cos(lam - LON0))
    return x, y


def dp(points, tol):
    """Douglas-Peucker: semplifica una linea mantenendo la forma."""
    if len(points) < 3:
        return points
    (x1, y1), (x2, y2) = points[0], points[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy)
    dmax, idx = 0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if norm < 1e-9:  # anello chiuso: distanza dal punto di partenza
            d = math.hypot(px - x1, py - y1)
        else:
            d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / norm
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return dp(points[: idx + 1], tol)[:-1] + dp(points[idx:], tol)
    return [points[0], points[-1]]


def polygons(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def frame(view):
    lon_min, lat_min, lon_max, lat_max = view
    pts = [laea(lon, lat) for lon in range(lon_min, lon_max + 1) for lat in (lat_min, lat_max)]
    pts += [laea(lon, lat) for lat in range(int(lat_min), int(lat_max) + 1) for lon in (lon_min, lon_max)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    # riquadro interno (si taglia sui lati), per non vedere i bordi curvi
    return min(xs) * 0.82, max(xs) * 0.9, min(ys) + 0.02, max(ys) * 0.97


def path_for(geom, view, width, tol):
    x0, x1, y0, y1 = frame(view)
    scale = width / (x1 - x0)
    lon_min, lat_min, lon_max, lat_max = view
    parts = []
    for poly in polygons(geom):
        ring = poly[0]
        if not any(lon_min - 5 <= lon <= lon_max + 5 and lat_min - 5 <= lat <= lat_max + 5 for lon, lat in ring):
            continue
        for r in poly:
            pts = [((laea(lon, lat)[0] - x0) * scale, (y1 - laea(lon, lat)[1]) * scale) for lon, lat in r]
            pts = dp(pts, tol)
            if len(pts) < 3:
                continue
            area = abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2
            if area < tol * tol * 4:
                continue
            parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(parts), (x1 - x0) * scale, (y1 - y0) * scale


def main():
    ne = json.loads(NE.read_text(encoding="utf-8"))
    legend = json.loads(DB.read_text(encoding="utf-8"))["metadata"]["eufic_climatic_zones_legend"]
    zones = {z: v for z, v in legend.items()
             if isinstance(v, dict) and "color_hex" in v and not z.startswith("_") and z != "arctic"}
    primary, partial = {}, {}
    for z, v in zones.items():
        for iso in v.get("countries_primary_iso", []):
            primary[iso] = z
        for iso in v.get("countries_partial_iso", []):
            partial.setdefault(iso, []).append(z)

    eea = json.loads(EEA.read_text(encoding="utf-8"))
    eea_to_zone = {r: z for z, v in zones.items() for r in v.get("eea_regions", [])}
    arctic = legend.get("_eea_regions", {}).get("arctic", {}).get("color_hex", ARCTIC)
    x0, x1, y0, y1 = frame(VIEW)
    scale = W / (x1 - x0)
    height = (y1 - y0) * scale

    def path_3035(geom, tol=0.6):
        parts = []
        for poly in polygons(geom):
            for ring in poly:
                pts = [(((X - FE) / R - x0) * scale, (y1 - (Y - FN) / R) * scale) for X, Y in ring]
                pts = dp(pts, tol)
                if len(pts) >= 3:
                    parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
        return "".join(parts)

    OUT_MAP.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        dark = theme == "dark"
        sea = "#1B1D1F" if dark else "#DCE5EA"
        land = "#3A3D40" if dark else "#ECEEEA"
        border = "#141516" if dark else "#FFFFFF"
        shapes = [f'<rect width="{W}" height="{height:.0f}" fill="{sea}"/>']
        # 1) tutte le terre in grigio
        for f in ne["features"]:
            d, _, _ = path_for(f["geometry"], VIEW, W, 0.6)
            if d:
                shapes.append(f'<path d="{d}" fill="{land}"/>')
        # 2) regioni biogeografiche colorate
        for f in eea["features"]:
            code = f["properties"]["code"]
            if code == "Outside":
                continue
            z = eea_to_zone.get(code)
            color = zones[z]["color_hex"] if z in zones else arctic
            d = path_3035(f["geometry"])
            if d:
                shapes.append(f'<path d="{d}" fill="{color}" stroke="{color}" stroke-width="0.4"/>')
        # 3) confini degli Stati sopra, sottili
        for f in ne["features"]:
            d, _, _ = path_for(f["geometry"], VIEW, W, 0.6)
            if d:
                shapes.append(f'<path d="{d}" fill="none" stroke="{border}" stroke-width="0.7" stroke-linejoin="round" stroke-opacity="0.85"/>')
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height:.0f}">{"".join(shapes)}</svg>'
        (OUT_MAP / f"europe_zones_{theme}.svg").write_text(svg, encoding="utf-8")
        print(theme, f"{len(svg) / 1024:.0f} KB")

    # Icona: sagoma reale dei Paesi europei (senza Russia e Islanda, senza
    # territori lontani), adattata a 24 x 24 con 1 px di margine.
    rings = []
    lon_min, lat_min, lon_max, lat_max = ICON_VIEW
    for f in ne["features"]:
        p = f["properties"]
        if p.get("CONTINENT") != "Europe" or p.get("ADM0_A3") in {"RUS", "ISL", "SJM"}:
            continue
        for poly in polygons(f["geometry"]):
            ring = poly[0]
            clon = sum(x for x, _ in ring) / len(ring)
            clat = sum(y for _, y in ring) / len(ring)
            if lon_min <= clon <= lon_max and lat_min <= clat <= lat_max:
                rings.append([laea(lon, lat) for lon, lat in ring])
    xs = [x for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
    bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
    s = 22 / max(bx1 - bx0, by1 - by0)
    ox = 1 + (22 - (bx1 - bx0) * s) / 2
    oy = 1 + (22 - (by1 - by0) * s) / 2
    parts = []
    for r in rings:
        pts = dp([(ox + (x - bx0) * s, oy + (by1 - y) * s) for x, y in r], 0.12)
        if len(pts) >= 3:
            area = abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2
            if area > 0.08:
                parts.append("M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z")
    OUT_ICON.write_text(
        # contorno dello stesso colore: chiude le fessure tra Stati, laghi e fiumi → blocco unico pieno
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#000">'
        f'<path d="{"".join(parts)}" stroke="#000" stroke-width="0.45" stroke-linejoin="round"/></svg>',
        encoding="utf-8")
    print("icona", f"{OUT_ICON.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
