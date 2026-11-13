"""Checks the draft's varieties (italian_varieties_and_territories.notable_varieties) against the source texts.

A variety is verified if:
- it is a PDO/PGI registered in eAmbrosia for that product, or
- all its distinctive words (excluding generic words and the product name) appear close together (within 60
  characters) in the text of at least one of the product's sources (Orto da Coltivare, Altroconsumo, My-PersonalTrainer,
  USDA HB66 for foreign cultivars).
The "Presidio Slow Food" label cannot be verified on these sources: it is removed from the name and noted.
Result in italian_varieties_and_territories.varieties_verification = [{name, verified, sources[]}];
notable_varieties keeps only the verified varieties, the others go to draft_legacy_values.json.
Usage:  python scripts/verify_varieties.py [--dry-run]
"""
import argparse
import re

from common import DATA, RAW, finalize_completeness, load_json, mark_enriched, save_json
from enrich_postharvest import MAP, load_hb66
from text_corpus import corpus, norm

STOP = set("di del della dei delle da a al alla in e il la lo le i gli d dell degli con senza tipo varieta cultivar comune dop igp "
           "presidio slow food stg pat bianco bianca rosso rossa verde nero nera giallo gialla gigante tondo tonda lungo lunga".split())
P = "italian_varieties_and_territories"


def core(name):
    n = re.sub(r"\((presidio slow food|pat)\)", "", name, flags=re.I)
    n = re.sub(r"\b(DOP|IGP|STG)\b", "", n)
    return n.strip(" ,")


def tokens(name, item_words):
    t = [w for w in norm(re.sub(r"\(.*?\)", " ", core(name))).split() if w not in STOP and w not in item_words and len(w) > 2]
    if not t:  # name made only of generic words (e.g. "Cappuccio Rosso"): use all non-empty words
        t = [w for w in norm(core(name)).split() if len(w) > 2 and w not in ("dop", "igp")]
    return t


def near(text, toks, win=60):
    if not toks:
        return False
    first = [m.start() for m in re.finditer(r"\b" + re.escape(toks[0]), text)]
    return any(all(re.search(r"\b" + re.escape(w), text[max(0, s - win):s + win + len(toks[0])]) for w in toks[1:]) for s in first)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    chap, _ = load_hb66()
    gi_all = [(r, norm(r["protectedName"])) for r in load_json(RAW / "eambrosia_it.json")["items"]
              if r.get("status") == "Registrata" and r.get("geographicalIndicatorTypeCode") in ("PDO", "PGI", "DOP", "IGP")]
    sfi = load_json(RAW / "slowfood_index.json")
    slugs = [(kind, u, set(s.split("-"))) for kind in ("presidi", "arca") for u, s in sfi[kind].items()]

    def has(w, words):  # uguaglianza o stessa radice (singolare/plurale: peperone/peperoni)
        return any(x == w or (len(w) > 4 and len(x) == len(w) and x[:-1] == w[:-1]) for x in words)

    def slow_lookup(toks, first, item_words):
        if not toks:
            return []
        # one-word names (e.g. "Kent"): the product name is also needed in the slug
        need_item = first in toks
        hits = [(k, u) for k, u, s in slugs if all(has(w, s) for w in toks)
                and (any(has(w, s) for w in item_words) or (not need_item and has(first, s)))]
        pres = [h for h in hits if h[0] == "presidi"]
        return (pres or hits)[:1]

    added_gi = []
    st = {"varieta": 0, "verificate": 0, "eambrosia": 0}
    for it in db["items"]:
        v = it[P]
        names = v.get("notable_varieties") or []
        if not names:
            continue
        m = MAP.get(it["id"])
        hb = [(m[0], chap[m[0]]["text"])] if m and m[0] in chap else None
        docs = [(k, u, norm(t)) for k, u, t in corpus(it, hb)]
        item_words = {w for w in set(norm(it["names"]["it"]).split()) | set(norm(it["names"]["en"]).split()) if len(w) > 2 and w not in STOP}
        gi = {norm(re.sub(r"\b(DOP|IGP)\b", "", l)): l for l in (v.get("dop_igp_labels") or [])}
        res = []
        for name in names:
            st["varieta"] += 1
            srcs = []
            key = norm(core(name))
            if any(key == g or key.startswith(g) or g.startswith(key) for g in gi) and re.search(r"\b(DOP|IGP)\b", name):
                srcs.append({"source_key": "eambrosia", "url": "https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/"})
                st["eambrosia"] += 1
            toks = tokens(name, item_words)
            first = norm(core(name)).split()[0] if norm(core(name)) else ""
            if not srcs and re.search(r"\b(DOP|IGP)\b", name):
                hit = next((r for r in gi_all if all(has(w, r[1].split()) for w in toks)
                            and (has(first, r[1].split()) or any(has(w, r[1].split()) for w in item_words))), None)
                if hit:
                    lab = f"{hit[0]['protectedName']} {'DOP' if hit[0]['geographicalIndicatorTypeCode'] in ('PDO', 'DOP') else 'IGP'}"
                    srcs.append({"source_key": "eambrosia", "url": "https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/",
                                 "registered_name": lab})
                    if lab not in (v.get("dop_igp_labels") or []):
                        v["dop_igp_labels"] = sorted((v.get("dop_igp_labels") or []) + [lab])
                        v["has_dop_igp"] = True
                        added_gi.append((it["id"], lab))
                    st["eambrosia"] += 1
            sf = slow_lookup(toks, first, item_words)
            for kind, u in sf:
                srcs.append({"source_key": "slow_food", "url": u, "list": "presidio" if kind == "presidi" else "arca_del_gusto"})
            for k, u, t in docs:
                if near(t, toks) and not any(s["source_key"] == k for s in srcs):
                    srcs.append({"source_key": k, "url": u})
            entry = {"name": name, "verified": bool(srcs), "sources": srcs}
            if re.search(r"presidio slow food", name, re.I):
                kinds = {k for k, _ in sf}
                if "presidi" in kinds:
                    entry["note"] = "Presidio Slow Food confermato (Fondazione Slow Food)"
                elif "arca" in kinds:
                    entry["note"] = "presente nell'Arca del Gusto Slow Food, non tra i Presìdi"
                    entry["name"] = re.sub(r"\s*\(Presidio Slow Food\)", " (Arca del Gusto Slow Food)", name)
                else:
                    entry["note"] = "qualifica 'Presidio Slow Food' non trovata sul sito della Fondazione Slow Food"
            res.append(entry)
            st["verificate"] += bool(srcs)
        if a.dry_run:
            for e in res:
                print(("OK " if e["verified"] else "-- ") + it["id"][:22].ljust(22), e["name"], [s["source_key"] for s in e["sources"]])
            continue
        v["varieties_verification"] = res
        bad = [e["name"] for e in res if not e["verified"]]
        if bad:
            legacy["items"].setdefault(it["id"], {})[f"{P}.notable_varieties_unverified"] = bad
        v["notable_varieties"] = [e["name"] for e in res if e["verified"]] or None
        mark_enriched(it, [f"{P}.notable_varieties"])
        it["data_completeness"]["notes"] += (f" Varietà: {len(res) - len(bad)}/{len(res)} verificate sulle fonti"
                                             + (f"; non verificate (in draft_legacy_values): {', '.join(bad)}." if bad else "."))
        finalize_completeness(it)
    print(st)
    print("PDO/PGI added from eAmbrosia:", added_gi)
    if not a.dry_run:
        save_json(DATA / "database.json", db)
        save_json(DATA / "draft_legacy_values.json", legacy)


if __name__ == "__main__":
    main()
