"""Modifiche a mano ai link utili dei prodotti (sources_by_topic.useful_links), fatte con l'Admin Studio (scheda Link).
Idempotente. Le modifiche stanno in config/link_overrides.json, così restano anche quando build_source_registry.py
rigenera i link:
    {"items": {"<id>": {"edit":   {"<url originale>": {"url": "...", "title": {"it", "en"}}},
                        "remove": ["<url>", ...],
                        "add":    [{"url", "title": {"it", "en"}, "source_key", "topic"}]}}}
Uso:  python scripts/apply_link_overrides.py   (dopo build_source_registry.py; lo studio lo esegue da solo)
"""
from common import CONFIG, DATA, load_json, save_json

FILE = CONFIG / "link_overrides.json"


def apply(db, ov):
    n = 0
    by = {it["id"]: it for it in db["items"]}
    for iid, o in (ov.get("items") or {}).items():
        it = by.get(iid)
        if not it:
            continue
        links = it["sources_by_topic"].setdefault("useful_links", [])
        for orig, e in (o.get("edit") or {}).items():
            for l in links:
                if l["url"] in (orig, e.get("url")):
                    for k in ("url", "title"):
                        if e.get(k) and l.get(k) != e[k]:
                            l[k] = e[k]
                            n += 1
        rm = set(o.get("remove") or [])
        before = len(links)
        links[:] = [l for l in links if l["url"] not in rm]
        n += before - len(links)
        have = {l["url"] for l in links}
        for a in o.get("add") or []:
            if a["url"] not in have:
                links.append({"title": a["title"], "url": a["url"], "source_key": a.get("source_key") or "user", "topic": a.get("topic") or "other"})
                n += 1
    return n


def main():
    if not FILE.exists():
        print("nessuna modifica ai link")
        return
    db = load_json(DATA / "database.json")
    n = apply(db, load_json(FILE))
    save_json(DATA / "database.json", db)
    print("modifiche ai link applicate:", n)


if __name__ == "__main__":
    main()
