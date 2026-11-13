"""Short labels with a capital initial on every word (owner decision, 2026-11-06). Idempotent.

Applies to short few-word expressions shown as labels (names, categories, states, levels, storage
locations, badges, claims, portion groups, glossary terms, vocabulary entries...), in Italian and in
English: "Cavolo Nero Toscano", "In Frigorifero", "Non Climaterico". It does NOT apply to comment sentences (storage
texts, descriptions, explanations) nor to registered official names (PDO/PGI, PAT, sources), which stay as in
the register.
Rules: linking words stay lowercase except in first position (it: di, e, a, in, con...; en: of, and,
the, in...); after an apostrophe the word is capitalised ("All'Asciutto"); acronyms, numbers, units and words with
internal capitals stay unchanged.
Usage:  python scripts/title_case_labels.py   (last step, after build_help.py and build_source_catalog.py)
"""
import re

from common import DATA, load_json, save_json

MINOR = {
    "it": {"di", "del", "dello", "della", "dei", "degli", "delle", "e", "ed", "o", "od", "a", "ad", "al", "allo", "alla", "ai", "agli", "alle",
           "da", "dal", "dallo", "dalla", "dai", "dagli", "dalle", "in", "nel", "nello", "nella", "nei", "negli", "nelle", "con", "per", "su",
           "sul", "sullo", "sulla", "sui", "sugli", "sulle", "tra", "fra", "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "che", "se", "ma"},
    "en": {"a", "an", "the", "and", "or", "nor", "of", "in", "on", "at", "to", "for", "from", "with", "by", "as", "per", "vs"},
}
APOS = re.compile(r"^(?P<pre>(?:[a-zà-ù]+)['’])(?P<rest>.+)$", re.I)


def cap_word(w, lang, first):
    lead = re.match(r"^[(\[«\"']+", w or "")
    if lead:                                       # "(bacche)" -> "(Bacche)": the bracket opens a new group
        return lead.group(0) + cap_word(w[lead.end():], lang, True)
    if not w or not w[0].isalpha() or not w[0].islower():
        return w                                   # numbers, acronyms, words already capitalised
    m = APOS.match(w)
    if m:                                          # all'asciutto -> all'Asciutto (prefix capitalised only if first word)
        pre = m.group("pre")
        pre = pre[0].upper() + pre[1:] if first else pre
        return pre + cap_word(m.group("rest"), lang, True)
    core = re.sub(r"^\W+|\W+$", "", w).lower()
    if not first and core in MINOR[lang]:
        return w
    return w[0].upper() + w[1:]


def title(s, lang):
    if not isinstance(s, str) or not s.strip():
        return s
    out, first = [], True
    for tok in re.split(r"(\s+)", s):
        if tok.isspace() or not tok:
            out.append(tok)
            continue
        out.append(cap_word(tok, lang, first))
        first = tok.endswith((":", "·", "/", "-", "–")) if tok in ("·", "/", "-", "–") else False
        if tok in ("·", "/", "–", "-", "(", ")"):
            first = True
    return "".join(out)


def bil(o):
    if isinstance(o, dict) and isinstance(o.get("it"), str):
        o["it"], o["en"] = title(o["it"], "it"), title(o.get("en"), "en")


def main():
    db = load_json(DATA / "database.json")
    n = 0
    for it in db["items"]:
        nm = it["names"]
        nm["it"], nm["en"] = title(nm["it"], "it"), title(nm["en"], "en")
        syn = nm.get("synonyms") or {}
        for lang in ("it", "en"):
            if syn.get(lang):
                syn[lang] = [title(x, lang) for x in syn[lang]]
        rs = it["ripening_and_storage"]
        for o in (rs.get("card_short_storage"), rs.get("ripening_badge_label"), (rs.get("home_storage") or {}).get("label"),
                  (rs.get("perishability") or {}).get("label"), (rs.get("storage_compatibility") or {}).get("label")):
            bil(o)
        n_ = it["nutrition_and_sustainability"]
        cl = n_.get("nutrition_claims_eu") or {}
        for lang in ("it", "en"):
            if cl.get(lang):
                cl[lang] = [title(x, lang) for x in cl[lang]]
        rp = n_.get("reference_portion") or {}
        for k in ("group", "frequency", "equivalent"):
            bil(rp.get(k))
        for a in n_.get("allergens_eu") or []:
            bil(a.get("name"))
        ef = (n_.get("environmental_footprint") or {}).get("sustainability_rating") or {}
        for v in ef.values():
            if isinstance(v, dict):
                bil(v.get("label"))
        for x in n_.get("vitamins", []) + n_.get("minerals", []) + n_.get("bioactive_compounds", []):
            if isinstance(x.get("name"), str):
                x["name"] = title(x["name"], "it")
            if isinstance(x.get("name_en"), str):
                x["name_en"] = title(x["name_en"], "en")
        iv = it["italian_varieties_and_territories"]
        iv["notable_varieties"] = [title(v, "it") for v in iv.get("notable_varieties") or []] or iv.get("notable_varieties")
        for v in iv.get("varieties_verification") or []:
            v["name"] = title(v["name"], "it")
        for d in it["images"]["image_details"]:
            bil(d.get("variety"))
        for u in it["sources_by_topic"].get("useful_links") or []:
            bil(u.get("title"))
        n += 1
    m = db["metadata"]
    for grp in (m.get("vocabulary") or {}).values():
        for k, v in grp.items():
            if not k.startswith("_"):
                bil(v)
    for g in (m.get("glossary") or {}).values():
        bil(g.get("term"))
    for v in (m.get("seasonality_states_legend") or {}).values():
        if isinstance(v, dict):
            bil(v.get("ui_label"))
    for z, v in (m.get("eufic_climatic_zones_legend") or {}).items():
        if z.startswith("_"):
            continue                               # descriptive notes (_method, _style): they are sentences
        bil(v) if isinstance(v, dict) and "it" in v else bil((v or {}).get("name") if isinstance(v, dict) else None)
    for lv in ((m.get("perishability_legend") or {}).get("levels") or []):
        bil(lv.get("label"))
    hs = m.get("home_storage_legend") or {}
    for v in (hs.get("locations") or {}).values():
        bil(v)
    for z, v in ((m.get("storage_compatibility_legend") or {}).get("groups") or {}).items():
        if z.startswith("_"):
            continue
        bil(v) if isinstance(v, dict) and "it" in v else bil((v or {}).get("label") if isinstance(v, dict) else None)
    for s in m.get("official_sources") or []:
        for t in (s.get("used_for") or {}).get("topics") or []:
            bil(t.get("label"))
    save_json(DATA / "database.json", db)
    print("short labels in Title Case:", n, "products + metadata")


if __name__ == "__main__":
    main()
