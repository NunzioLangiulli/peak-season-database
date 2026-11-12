"""Scarica e mette in cache il testo delle pagine web già collegate a ogni alimento (ODC, Altroconsumo,
My-PersonalTrainer, UC Davis esclusa perché protetta da Cloudflare), per verificare varietà, parti edibili ecc.
Cache: data/raw/pages/<host>/<slug>.txt (testo pulito dell'articolo).
Uso:  python scripts/fetch_text_pages.py [--hosts ortodacoltivare.it my-personaltrainer.it]
"""
import argparse
import html
import re
import urllib.parse

from common import DATA, RAW, http_get, load_json

OUT = RAW / "pages"


def clean(h):
    m = re.search(r"<article.*?</article>", h, re.S) or re.search(r"<main.*?</main>", h, re.S)
    t = m.group(0) if m else h
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<footer.*?</footer>|<aside.*?</aside>", "", t, flags=re.S)
    t = re.sub(r"<(h\d|p|li|tr|br|div)[^>]*>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


def path_for(url):
    u = urllib.parse.urlparse(url)
    host = u.netloc.replace("www.", "")
    slug = re.sub(r"[^a-z0-9]+", "_", u.path.lower()).strip("_") or "index"
    return OUT / host / f"{slug[:120]}.txt"


def urls_of(it, hosts):
    s = it["sources_by_topic"]
    cand = list(s.get("seasonality_and_storage_urls", [])) + list(s.get("agricultural_calendar_urls", [])) + list(s.get("other_urls", []))
    return [u for u in dict.fromkeys(cand) if any(h in u for h in hosts)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", nargs="*", default=["ortodacoltivare.it", "my-personaltrainer.it"])
    a = ap.parse_args()
    db = load_json(DATA / "database.json")
    n = 0
    for it in db["items"]:
        for u in urls_of(it, a.hosts):
            p = path_for(u)
            if p.exists():
                continue
            r = http_get(u, pause=1.0)
            if r.status_code != 200:
                print("HTTP", r.status_code, u)
                continue
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(u + "\n" + clean(r.text), encoding="utf-8")
            n += 1
    print("pagine scaricate:", n)


if __name__ == "__main__":
    main()
