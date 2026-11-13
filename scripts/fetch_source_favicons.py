"""Phase 2 - favicons of the websites used as sources ("Sources and Useful Links" block).

For each source it reads the website home page, takes the declared icons
(apple-touch-icon, icon with sizes) and picks the largest; failing that
it uses /favicon.ico. It saves:
- data/raw/favicons/<key>.<ext>   original download (unchanged)
- app/assets/sources/<key>.png     128 x 128 px, ready for the app
- app/lib/data/source_logos.g.dart    which logos are dark (in the dark theme they become white)
A uniform light background (white/very light grey) is made transparent.

Better logos by hand: put a high-resolution PNG/WebP/JPG (ideally >= 256 px,
preferably already with a transparent background) in fonti_locali/loghi_fonti/<key>.png
(e.g. eufic_map.png) and re-run the script: the manual file takes precedence.
Logos belong to their respective organisations: they are used only to identify the source.

Usage: python scripts/fetch_source_favicons.py
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

# Alternative websites (parent organisation) to try if the icon is small
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
            size = -1  # SVG: Pillow cannot read it, last choice
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
        print(f"  {key}: home page not read ({e})")
    candidates.sort(key=lambda x: -x[0])
    candidates.append((16, urljoin(home, "/favicon.ico")))
    for size, url in candidates:
        if url.lower().endswith(".svg"):
            continue
        try:
            data = fetch(url).content
            im = Image.open(io.BytesIO(data))
            if getattr(im, "n_frames", 1) > 1 or im.format == "ICO":
                # multi-resolution ICO: take the largest
                sizes = im.info.get("sizes") or []
                if sizes:
                    im.size = max(sizes)
            im.load()
            return url, data, im
        except Exception:  # noqa: BLE001
            continue
    return None


def pick(key, home):
    """Best icon among the website, alternative websites and Google's favicon service."""
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
    """Makes the uniform light background touching the edges transparent."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    opaque = [c for c in corners if c[3] > 200]
    if not opaque:
        return im  # already transparent
    ref = opaque[0]
    if sum(ref[:3]) / 3 < 200 or any(max(abs(c[i] - ref[i]) for i in range(3)) > tol for c in opaque):
        return im  # coloured or non-uniform background: it is part of the logo
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
    """True if the logo would be hard to see on black: the mean HSV value
    (brightest channel) of the visible pixels is used, so a saturated red does not count
    as dark while a midnight blue does."""
    px = [p for p in im.getdata() if p[3] > 128]
    if not px:
        return False
    value = sum(max(r, g, b) for r, g, b, _ in px) / len(px) / 255
    return value < 0.5


def make_logo(im):
    """Logo ready for the app: uniform light background made transparent, margins trimmed, 128 x 128 px centred."""
    im = clear_background(im.convert("RGBA"))
    bbox = im.getbbox()  # toglie i margini trasparenti
    if bbox:
        im = im.crop(bbox)
    # scale small icons (16-48 px) up to 128 px too, so they fill the box
    scale = 128 / max(im.width, im.height)
    im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    canvas.paste(im, ((128 - im.width) // 2, (128 - im.height) // 2), im)
    return canvas


def dark_logos():
    """Keys of the dark logos among all the PNGs in app/assets/sources (including those uploaded from the Admin Studio)."""
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
    print("dark logos:", sorted(dark))


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
            print(f"{key}: no icon")
            continue
        url, data, im = res
        ext = (im.format or "img").lower()
        (RAW / f"{key}.{ext}").write_bytes(data)
        canvas = make_logo(im)
        canvas.save(OUT / f"{key}.png")
        print(f"{key}: from {url}")
    write_dart()
    if failed:
        print("without icon:", failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
