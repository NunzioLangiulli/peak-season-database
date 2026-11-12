"""Fase 2 - favicon dei siti usati come fonti (blocco "Fonti e Link Utili").

Per ogni fonte legge la home page del sito, prende le icone dichiarate
(apple-touch-icon, icon con dimensioni) e sceglie la più grande; in mancanza
usa /favicon.ico. Salva:
- data/raw/favicons/<chiave>.<ext>   originale scaricato (non modificato)
- app/assets/sources/<chiave>.png     128 x 128 px, pronto per l'app
- app/lib/data/source_logos.g.dart    quali loghi sono scuri (nel tema scuro diventano bianchi)
Lo sfondo chiaro uniforme (bianco/grigio chiarissimo) viene reso trasparente.

Loghi migliori a mano: metti un PNG/WebP/JPG ad alta risoluzione (ideale >= 256 px,
meglio se già con sfondo trasparente) in fonti_locali/loghi_fonti/<chiave>.png
(es. eufic_map.png) e rilancia lo script: il file manuale ha la precedenza.
I loghi restano dei rispettivi enti: sono usati solo per identificare la fonte.

Uso: python scripts/fetch_source_favicons.py
"""
import io
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "favicons"
OUT = ROOT / "app" / "assets" / "sources"
MANUAL = ROOT / "fonti_locali" / "loghi_fonti"
DART = ROOT / "app" / "lib" / "data" / "source_logos.g.dart"
UA = {"User-Agent": "Mozilla/5.0 (PeakSeason favicon fetcher; non-commercial study app)"}

# Siti alternativi (ente di appartenenza) da provare se l'icona è piccola
ALT = {
    "crea": ["https://www.crea.gov.it/"],
    "usda_fdc": ["https://www.usda.gov/", "https://www.nal.usda.gov/"],
    "usda_hb66": ["https://www.usda.gov/"],
    "uc_davis": ["https://www.ucdavis.edu/"],
    "eppo": ["https://www.eppo.int/"],
    "eufic_map": ["https://www.eufic.org/en"],
    "wfo": ["https://www.worldfloraonline.org/"],
    "gbif": ["https://www.gbif.org/"],
}
GOOGLE = "https://www.google.com/s2/favicons?domain={}&sz=128"
MIN_GOOD = 96

SITES = {
    "altroconsumo": "https://www.altroconsumo.it/",
    "ortodacoltivare": "https://www.ortodacoltivare.it/",
    "my_personaltrainer": "https://www.my-personaltrainer.it/",
    "crea": "https://www.alimentinutrizione.it/",
    "usda_fdc": "https://fdc.nal.usda.gov/",
    "uc_davis": "https://postharvest.ucdavis.edu/",
    "usda_hb66": "https://www.ars.usda.gov/",
    "eambrosia": "https://ec.europa.eu/",
    "slow_food": "https://www.fondazioneslowfood.com/",
    "eufic_map": "https://www.eufic.org/",
    "eppo": "https://gd.eppo.int/",
    "wfo": "https://www.worldfloraonline.org/",
    "gbif": "https://www.gbif.org/",
    "eea_biogeo": "https://www.eea.europa.eu/",
}


class IconParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.icons = []  # (score, url)

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        a = dict(attrs)
        rel = (a.get("rel") or "").lower()
        href = a.get("href")
        if not href or "icon" not in rel or "mask" in rel:
            return
        size = 0
        m = re.search(r"(\d+)x(\d+)", a.get("sizes") or "")
        if m:
            size = int(m.group(1))
        elif "apple-touch-icon" in rel:
            size = 180
        elif href.lower().endswith(".svg"):
            size = -1  # SVG: Pillow non lo legge, ultima scelta
        self.icons.append((size, href))


def fetch(url):
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    return r


def best_icon(key, home):
    candidates = []
    try:
        page = fetch(home)
        p = IconParser()
        p.feed(page.text)
        candidates = [(s, urljoin(page.url, h)) for s, h in p.icons]
    except Exception as e:  # noqa: BLE001
        print(f"  {key}: home non letta ({e})")
    candidates.sort(key=lambda x: -x[0])
    candidates.append((16, urljoin(home, "/favicon.ico")))
    for size, url in candidates:
        if url.lower().endswith(".svg"):
            continue
        try:
            data = fetch(url).content
            im = Image.open(io.BytesIO(data))
            if getattr(im, "n_frames", 1) > 1 or im.format == "ICO":
                # ICO multi-risoluzione: prendi la più grande
                sizes = im.info.get("sizes") or []
                if sizes:
                    im.size = max(sizes)
            im.load()
            return url, data, im
        except Exception:  # noqa: BLE001
            continue
    return None


def pick(key, home):
    """Migliore icona tra sito, siti alternativi e servizio favicon di Google."""
    best = None
    for site in [home, *ALT.get(key, [])]:
        res = best_icon(key, site)
        if res and (best is None or res[2].width > best[2].width):
            best = res
        if best and best[2].width >= MIN_GOOD:
            return best
    from urllib.parse import urlparse
    for site in [home, *ALT.get(key, [])]:
        try:
            url = GOOGLE.format(urlparse(site).netloc)
            data = fetch(url).content
            im = Image.open(io.BytesIO(data))
            im.load()
            if best is None or im.width > best[2].width:
                best = (url, data, im)
        except Exception:  # noqa: BLE001
            continue
    return best


def clear_background(im, tol=28):
    """Rende trasparente lo sfondo chiaro e uniforme che tocca i bordi."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    opaque = [c for c in corners if c[3] > 200]
    if not opaque:
        return im  # già trasparente
    ref = opaque[0]
    if sum(ref[:3]) / 3 < 200 or any(max(abs(c[i] - ref[i]) for i in range(3)) > tol for c in opaque):
        return im  # sfondo colorato o non uniforme: è parte del logo
    from collections import deque
    seen = set()
    q = deque((x, y) for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)])
    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        c = px[x, y]
        if c[3] == 0 or max(abs(c[i] - ref[i]) for i in range(3)) <= tol:
            px[x, y] = (c[0], c[1], c[2], 0)
            q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return im


def is_dark(im):
    """Vero se il logo si vedrebbe male sul nero: si usa il valore HSV medio
    (canale più luminoso) dei pixel visibili, così un rosso saturo non conta
    come scuro mentre un blu notte sì."""
    px = [p for p in im.getdata() if p[3] > 128]
    if not px:
        return False
    value = sum(max(r, g, b) for r, g, b, _ in px) / len(px) / 255
    return value < 0.5


def make_logo(im):
    """Logo pronto per l'app: sfondo chiaro uniforme reso trasparente, margini tolti, 128 x 128 px centrato."""
    im = clear_background(im.convert("RGBA"))
    bbox = im.getbbox()  # toglie i margini trasparenti
    if bbox:
        im = im.crop(bbox)
    # adatta a 128 px anche le icone piccole (16-48 px), così riempiono il riquadro
    scale = 128 / max(im.width, im.height)
    im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    canvas.paste(im, ((128 - im.width) // 2, (128 - im.height) // 2), im)
    return canvas


def dark_logos():
    """Chiavi dei loghi scuri tra tutti i PNG di app/assets/sources (anche quelli caricati dall'Admin Studio)."""
    out = set()
    for f in sorted(OUT.glob("*.png")):
        with Image.open(f) as im:
            if is_dark(im.convert("RGBA")):
                out.add(f.stem)
    return out


def write_dart():
    nl = chr(10)
    dark = dark_logos()
    lines = [
        "// GENERATO da scripts/fetch_source_favicons.py (anche dall'Admin Studio): non modificare a mano.",
        "/// Loghi delle fonti scuri: nel tema scuro si invertono le luci (tinte invariate).",
        "const darkSourceLogos = <String>{",
        *[f"  '{k}'," for k in sorted(dark)],
        "};",
    ]
    DART.write_text(nl.join(lines) + nl, encoding="utf-8")
    print("loghi scuri:", sorted(dark))


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    for key, home in SITES.items():
        manual = next((f for f in MANUAL.glob(f"{key}.*") if f.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg"}), None) if MANUAL.exists() else None
        if manual:
            im = Image.open(manual)
            im.load()
            res = (str(manual), manual.read_bytes(), im)
        else:
            res = pick(key, home)
        if not res:
            failed.append(key)
            print(f"{key}: nessuna icona")
            continue
        url, data, im = res
        ext = (im.format or "img").lower()
        (RAW / f"{key}.{ext}").write_bytes(data)
        canvas = make_logo(im)
        canvas.save(OUT / f"{key}.png")
        print(f"{key}: da {url}")
    write_dart()
    if failed:
        print("senza icona:", failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
