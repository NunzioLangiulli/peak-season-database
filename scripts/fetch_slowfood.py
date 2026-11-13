"""List of the Slow Food Presidia and Ark of Taste from the sitemaps of the Slow Food Foundation for Biodiversity
(source added to verify the draft's varieties and "Slow Food Presidium" labels).
Cache: data/raw/slowfood_index.json = {"presidi": {url: slug}, "arca": {url: slug}}; titles of the opened pages in
data/raw/slowfood_titles.json.
Usage:  python scripts/fetch_slowfood.py
"""
import re

from common import RAW, http_get, save_json

BASE = "https://www.fondazioneslowfood.com/"
MAPS = {"presidi": ["presidi-sitemap.xml", "presidi-sitemap2.xml"],
        "arca": [f"arca-sitemap{n}.xml" for n in [""] + list(range(2, 15))]}


def main():
    out = {}
    for kind, files in MAPS.items():
        out[kind] = {}
        for f in files:
            r = http_get(BASE + f, pause=1.0)
            if r.status_code != 200:
                print("HTTP", r.status_code, f)
                continue
            for u in re.findall(r"<loc>(.*?)</loc>", r.text):
                if "/it/" in u:
                    out[kind][u] = u.rstrip("/").rsplit("/", 1)[-1]
        print(kind, len(out[kind]))
    save_json(RAW / "slowfood_index.json", out)


if __name__ == "__main__":
    main()
