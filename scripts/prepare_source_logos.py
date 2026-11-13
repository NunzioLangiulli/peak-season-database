"""Prepares the source logos supplied by hand (fonti_locali/loghi_fonti/originali/).

For each source: renders the SVG at high resolution (Playwright/Edge) or opens the
raster, removes the uniform white background, crops just the symbol where the
logo with lettering would be too wide for an icon, and saves
fonti_locali/loghi_fonti/<key>.png (transparent, long side 512 px).
fetch_source_favicons.py then uses these files instead of the favicons.

Usage: python scripts/prepare_source_logos.py
"""
import base64
import io
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "fonti_locali" / "loghi_fonti" / "originali"
OUT = ROOT / "fonti_locali" / "loghi_fonti"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# key: (original file, operations). Operations, in order:
#   ("white",)              white background connected to the edges → transparent
#   ("all_white",)          ALL white/very light pixels → transparent (inside the logo too)
#   ("crop", x0,y0,x1,y1)   crop in fractions of the trimmed logo
#   ("erase", x0,y0,x1,y1)  erases a box (e.g. a subtitle)
#   ("keep_red",)           keeps only red pixels (symbol without black lettering)
#   ("white_to", "#RRGGBB") white pixels take that colour (white lettering)
#   ("circle",)             inscribed circular crop
LOGOS = {
    "crea": ("CREA_logo.png", [("erase", 0.2, 0.67, 1.0, 1.0)]),            # remove only the subtitle
    "eufic_map": ("EUFIC_logo_colour.webp", []),                          # whole logo with "eufic"
    "my_personaltrainer": ("My-PersonalTrainer logo.jpg", [("white",)]),  # the heart
    "ortodacoltivare": ("Orto da Coltivare logo.jpg", [("all_white",)]),  # no white parts
    "uc_davis": ("UCDavisUnofficialSeal_2Color_0.png", []),
    "altroconsumo": ("altroconsumo-logo-it-IT.svg", [("crop", 0.0, 0.0, 0.2, 1.0), ("keep_red",)]),  # only the square
    "slow_food": ("slow-food-logo-png-transparent.png", [("erase", 0.0, 0.86, 1.0, 1.0), ("white_to", "#C1272D")]),  # with the lettering in red, without "PORTLAND"
    "gbif": ("GBIF-Standard-logo/SVG/gbif-dot-org-green-logo.svg", []),     # original with "GBIF"
    "usda_fdc": ("usda-logo-and-lockups/USDA logo/color/usda-logo-color.svg", []),
    "usda_hb66": ("usda-logo-and-lockups/USDA logo/color/usda-logo-color.svg", []),
    "eambrosia": ("EU EC logo_MUTE/RGB/SVG/LOGO CE_RGB_MUTE_POS.svg", []),
    "eppo": ("eppo.jpg", [("circle",)]),                                 # only the circle
    "wfo": ("wfo_roundel.svg", []),
}
# Not used: "EPPO 75th logo.png" (replaced by eppo.jpg) and "wfp-logo-emblem-blue.png"
# (it is the World Food Programme, not World Flora Online).


def render_svg(path, size=1600):
    from playwright.sync_api import sync_playwright
    b64 = base64.b64encode(path.read_bytes()).decode()
    html = (f"<html><body style='margin:0;background:transparent'>"
            f"<img id='i' src='data:image/svg+xml;base64,{b64}' style='width:{size}px'></body></html>")
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=EDGE)
        pg = br.new_page(viewport={"width": size, "height": size})
        pg.set_content(html)
        pg.wait_for_timeout(400)
        png = pg.locator("#i").screenshot(omit_background=True)
        br.close()
    return Image.open(io.BytesIO(png)).convert("RGBA")


def clear_white(im, tol=30):
    """Sfondo bianco/chiaro collegato ai bordi → trasparente."""
    from collections import deque
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    q = deque([(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)])
    seen = set()
    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        r, g, b, a = px[x, y]
        if a == 0 or min(r, g, b) >= 255 - tol:
            px[x, y] = (r, g, b, 0)
            q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return im


def trim(im):
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def apply(im, op):
    kind = op[0]
    w, h = im.size
    if kind == "white":
        return clear_white(im)
    if kind == "all_white":
        px = im.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                # white and off-whites from JPEG compression (light and low-saturation)
                if min(r, g, b) >= 185 and max(r, g, b) - min(r, g, b) < 45:
                    px[x, y] = (r, g, b, 0)
        return im
    if kind == "crop":
        _, x0, y0, x1, y1 = op
        return trim(im.crop((round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h))))
    if kind == "erase":
        _, x0, y0, x1, y1 = op
        clear = Image.new("RGBA", (round((x1 - x0) * w), round((y1 - y0) * h)), (0, 0, 0, 0))
        im.paste(clear, (round(x0 * w), round(y0 * h)))
        return trim(im)
    if kind == "keep_red":
        px = im.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if not (r > 150 and r > g * 1.8 and r > b * 1.8):
                    px[x, y] = (r, g, b, 0)
        return trim(im)
    if kind == "white_to":
        c = tuple(int(op[1][i:i + 2], 16) for i in (1, 3, 5))
        px = im.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a > 0 and min(r, g, b) >= 200:
                    px[x, y] = (*c, a)
        return im
    if kind == "circle":
        from PIL import ImageDraw
        d = min(w, h)
        im = im.crop(((w - d) // 2, (h - d) // 2, (w - d) // 2 + d, (h - d) // 2 + d))
        mask = Image.new("L", (d * 4, d * 4), 0)
        ImageDraw.Draw(mask).ellipse((6, 6, d * 4 - 6, d * 4 - 6), fill=255)
        im.putalpha(mask.resize((d, d), Image.LANCZOS))
        return im
    raise ValueError(kind)


def main():
    if not SRC.exists():
        raise SystemExit(f"manca {SRC}")
    for key, (name, ops) in LOGOS.items():
        path = SRC / name
        im = render_svg(path) if path.suffix.lower() == ".svg" else Image.open(path).convert("RGBA")
        im = trim(im)
        for op in ops:
            im = apply(im, op)
        im = trim(im)
        im.thumbnail((512, 512), Image.LANCZOS)
        im.save(OUT / f"{key}.png")
        print(f"{key}: {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    main()
