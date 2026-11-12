"""Passo 1.3b - Estrae i dati dai PDF vettoriali in fonti_locali/ (lettura della grafica, non del testo).

1) Orto da Coltivare (odc-tabella-nord/centro/sud.pdf): per ogni riga le barre colorate
   rosso=semina in semenzaio, blu=semina diretta, verde=trapianto, arancio=raccolta, con risoluzione di mezzo mese
   (un mese è attivo se la barra ne copre almeno il 30%); icona luna (parte scura a sinistra = fase crescente,
   a destra = fase calante, calibrato sulla legenda del PDF); icona sole (giallo pieno = molto soleggiato,
   giallo chiaro = soleggiato, con nuvola = anche mezz'ombra).
   Profondità di semina e sesto d'impianto sono testo convertito in curve (non estraibile): sono trascritti a mano
   in scripts/config/odc_params_transcribed.json; lo script verifica che il disegno di quelle celle sia identico
   nelle tre tabelle (altrimenti segnala la riga da ricontrollare).
2) WWF (Calendario-della-Frutta-e-Verdura-di-Stagione.pdf): colore della cella di ogni mese
   (verde/arancio = di stagione, verde chiaro/giallo = primizie o tardive).

Output: data/raw/odc_tables.json, data/raw/wwf_calendar.json
"""
import hashlib

import pymupdf

from common import CONFIG, FONTI, RAW, load_json, save_json

BAR = {"seedbed": (0.70, 0.19, 0.20), "direct": (0.00, 0.68, 0.94), "transplant": (0.20, 0.52, 0.37), "harvest": (0.96, 0.51, 0.12)}
SUN_FULL, SUN_LIGHT, CLOUD = (1.0, 0.8, 0.02), (1.0, 0.96, 0.52), (0.53, 0.6, 0.76)
MOON_DARK, MOON_LIGHT = (0.34, 0.35, 0.36), (1.0, 0.99, 0.84)


def close(a, b, tol=0.03):
    return a is not None and all(abs(x - y) <= tol for x, y in zip(a, b))


def rf(f):
    return tuple(round(c, 2) for c in f) if f else None


def page_geometry(page):
    d = page.get_drawings()
    vl = sorted({(round(x["rect"].x0, 1), round(x["rect"].x1, 1)) for x in d
                 if x.get("fill") and x["rect"].width < 4 and x["rect"].height > 300})
    bands = sorted({round(x["rect"].y0, 1) for x in d
                    if x.get("fill") and x["rect"].width > 500 and 15 < x["rect"].height < 40})
    if len(vl) < 13 or len(bands) < 2:
        return d, [], None, None          # pagina senza tabella (es. lettera dell'autore)
    # i primi 13 separatori verticali delimitano i 12 mesi
    cols = [vl[0][1]] + [(a + b) / 2 for a, b in vl[1:13]]
    y0, pitch = bands[0], (bands[1] - bands[0]) / 2
    return d, cols, y0, pitch


def months_covered(x0, x1, cols):
    out = []
    for m in range(12):
        a, b = cols[m], cols[m + 1]
        ov = max(0.0, min(x1, b) - max(x0, a))
        if ov >= 0.3 * (b - a):
            out.append(m + 1)
    return out


def parse_odc(path, row_names):
    doc = pymupdf.open(path)
    rows, cell_hash = {}, {}
    names = iter(row_names)
    for page in doc:
        d, cols, y0, pitch = page_geometry(page)
        if len(cols) < 13:
            continue
        for k in range(27):                     # 27 righe per pagina

            try:
                name = next(names)
            except StopIteration:
                break
            ya, yb = y0 + k * pitch, y0 + (k + 1) * pitch
            rec = {b: set() for b in BAR}
            sun = {"full": 0.0, "light": 0.0, "cloud": 0.0}
            dark_cx, light_cx = [], []
            for x in d:
                r, f = x["rect"], rf(x.get("fill"))
                cy = (r.y0 + r.y1) / 2
                if not (ya <= cy < yb) or f is None:
                    continue
                if r.height < 8 and r.width > 3 and r.x0 >= cols[0] - 1 and r.x1 <= cols[12] + 1:
                    for b, c in BAR.items():
                        if close(f, c):
                            rec[b].update(months_covered(r.x0, r.x1, cols))
                if 418 <= r.x0 and r.x1 <= 442:          # colonna "Luna"
                    if close(f, MOON_DARK, 0.03):
                        dark_cx.append((r.x0 + r.x1) / 2)
                    elif close(f, MOON_LIGHT, 0.03):
                        light_cx.append((r.x0 + r.x1) / 2)
                if 521 <= r.x0 and r.x1 <= 566:
                    area = r.width * r.height
                    if close(f, SUN_FULL):
                        sun["full"] += area
                    elif close(f, SUN_LIGHT):
                        sun["light"] += area
                    elif close(f, CLOUD):
                        sun["cloud"] += area
            if dark_cx and light_cx:
                moon = "fase_crescente" if min(dark_cx) < sum(light_cx) / len(light_cx) - 0.5 else "fase_calante"
            else:
                moon = None
            if sun["cloud"] > 0:
                exp = "anche_mezzombra"
            elif sun["full"] > 0:
                exp = "molto_soleggiato"
            elif sun["light"] > 0:
                exp = "soleggiato"
            else:
                exp = None
            pix = page.get_pixmap(clip=pymupdf.Rect(477, ya + 1, 520, yb - 1), dpi=150, colorspace=pymupdf.csGRAY)
            cell_hash[name] = hashlib.md5(pix.samples).hexdigest()
            rows[name] = {**{b: sorted(v) for b, v in rec.items()}, "lunar_phase": moon, "sun_exposure": exp}
    return rows, cell_hash


def parse_wwf(path):
    doc = pymupdf.open(path)
    MONTHS = ["GEN", "FEB", "MAR", "APR", "MAG", "GIU", "LUG", "AGO", "SET", "OTT", "NOV", "DIC"]
    STATE = {(0.23, 0.61, 0.59): ("verdura", "in_season"), (0.99, 0.54, 0.06): ("frutta", "in_season"),
             (0.29, 0.76, 0.73): ("verdura", "primizie_o_tardive"), (1.0, 0.76, 0.12): ("frutta", "primizie_o_tardive")}
    out = {}
    names = set(load_json(RAW / "local_pdf_lists.json")["wwf"]["rows"])
    for page in doc:
        words = page.get_text("words")
        fills = [(x["rect"], rf(x["fill"])) for x in page.get_drawings()
                 if x.get("fill") and 20 < x["rect"].width < 80 and 10 < x["rect"].height < 40]
        # nomi delle righe (possono essere su due righe di testo, es. "Broccoletti di" / "Bruxelles")
        mx = min((w[0] for w in words if w[4] in MONTHS), default=0)
        labels = [w for w in words if w[4] not in MONTHS and w[2] <= mx + 1]
        lines = {}
        for w in labels:
            key = round((w[1] + w[3]) / 2)
            lines.setdefault(key, []).append(w)
        row_y = []
        for y, ws in sorted(lines.items()):
            txt = " ".join(x[4] for x in sorted(ws, key=lambda t: t[0]))
            row_y.append((y, txt))
        merged, i = [], 0
        while i < len(row_y):
            y, t = row_y[i]
            if i + 1 < len(row_y) and f"{t} {row_y[i + 1][1]}" in names and row_y[i + 1][0] - y < 30:
                merged.append(((y + row_y[i + 1][0]) / 2, f"{t} {row_y[i + 1][1]}")); i += 2
            else:
                merged.append((y, t)); i += 1
        merged = [m for m in merged if m[1] in names]
        for w in words:
            if w[4] not in MONTHS:
                continue
            cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
            cell = [k for r, f in fills if r.x0 <= cx <= r.x1 and r.y0 <= cy <= r.y1
                    for k in STATE if close(f, k, 0.02)]
            if not cell or not merged:
                continue
            name = min(merged, key=lambda m: abs(m[0] - cy))
            if abs(name[0] - cy) > 25:
                continue
            kind, state = STATE[cell[0]]
            out.setdefault(name[1], {"kind": kind, "months": {}})["months"][MONTHS.index(w[4]) + 1] = state
    return out


def main():
    rows = load_json(RAW / "local_pdf_lists.json")["odc_rows"]["rows"]
    res, hashes = {}, {}
    for area, fn in (("nord", "odc-tabella-nord.pdf"), ("centro", "odc-tabella-centro.pdf"), ("sud_isole", "odc-tabella-sud.pdf")):
        res[area], hashes[area] = parse_odc(FONTI / fn, rows)
        print(area, "righe lette:", len(res[area]))
    diff = [r for r in rows if not (hashes["nord"].get(r) == hashes["centro"].get(r) == hashes["sud_isole"].get(r))]
    params = load_json(CONFIG / "odc_params_transcribed.json")
    save_json(RAW / "odc_tables.json", {
        "_source": "fonti_locali/odc-tabella-{nord,centro,sud}.pdf (Orto da Coltivare, M. Cereda) - estrazione vettoriale",
        "areas": res, "params_transcribed": params["rows"],
        "param_cells_differ_between_areas": diff})
    print("righe con celle profondità/sesto diverse tra le tabelle:", diff)
    wwf = parse_wwf(FONTI / "Calendario-della-Frutta-e-Verdura-di-Stagione.pdf")
    save_json(RAW / "wwf_calendar.json", {"_source": "fonti_locali/Calendario-della-Frutta-e-Verdura-di-Stagione.pdf (WWF)", "rows": wwf})
    missing = sorted(set(load_json(RAW / "local_pdf_lists.json")["wwf"]["rows"]) - set(wwf))
    print("WWF righe lette:", len(wwf), "| non lette:", missing)


if __name__ == "__main__":
    main()
