"""Shared description corpus (shared_descriptions_corpus, revision 2026-11-12).

In data/database.json the descriptive texts repeated across products (storage tips, notes on sources,
method explanations...) are written only once in "shared_descriptions_corpus" (right after "metadata") and in the
products they are referenced like this:
    { "corpus_ref": "key" }                                            -> corpus text
    { "corpus_ref": "key", "specific_addition": { "it", "en" } }       -> corpus text + " " + specific addition
Unique texts stay complete { "it", "en" }.

Pipeline scripts always work on the full text: common.load_json expands the references (expand) and
common.save_json compacts them again (compact) when the file is database.json. Compaction is deterministic and keeps
existing keys: if the text of a corpus entry is changed (e.g. with the text editor), all the products
using it change together and the key stays the same.
Rules: a full text used at least MIN_USES times by at least MIN_ITEMS different products becomes an entry; the first sentence of longer texts, if
repeated at least MIN_USES times (in Italian and in English), becomes an entry with "specific_addition" for the rest.
Only descriptive fields (FIELDS) are compacted, never short labels, names or titles.
"""
import re
import unicodedata

KEY = "shared_descriptions_corpus"
MIN_USES = 3
MIN_ITEMS = 2                                                # testi comuni ad almeno due prodotti diversi
FIELDS = {"tip", "tips", "speed_up", "slow_down", "symptoms", "compatibility_notes", "basis", "availability_note",
          "derivation_notes", "curve_basis", "cultivation_notes", "derivation", "note", "storage_instructions", "method",
          "description", "explanation", "summary", "consumption_tip", "ideal_conditions"}
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý0-9«\"(])")


def _is_bil(o):
    return isinstance(o, dict) and isinstance(o.get("it"), str) and isinstance(o.get("en"), str) and set(o) <= {"it", "en"}


def resolve(o, corpus):
    """Full {it, en} text of a corpus reference (or the object itself if it is not a reference)."""
    if isinstance(o, dict) and "corpus_ref" in o:
        base = corpus[o["corpus_ref"]]
        add = o.get("specific_addition")
        if add:
            return {"it": f"{base['it']} {add['it']}".strip(), "en": f"{base['en']} {add['en']}".strip()}
        return {"it": base["it"], "en": base["en"]}
    return o


def expand(db):
    corpus = db.get(KEY) or {}

    def walk(o):
        if isinstance(o, dict):
            for k, v in list(o.items()):
                if isinstance(v, dict) and "corpus_ref" in v:
                    o[k] = resolve(v, corpus)
                else:
                    walk(v)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, dict) and "corpus_ref" in v:
                    o[i] = resolve(v, corpus)
                else:
                    walk(v)
    walk(db.get("items") or [])
    return db


def _slots(o, field=None):
    """(container, key, field) of every descriptive {it, en} text in the products."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "data_completeness":
                continue
            if _is_bil(v) and k in FIELDS:
                yield o, k, k
            else:
                yield from _slots(v, k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if _is_bil(v) and field in FIELDS:
                yield o, i, field
            else:
                yield from _slots(v, field)


def _first(t):
    it, en = SENT.split(t["it"]), SENT.split(t["en"])
    if len(it) >= 2 and len(it) == len(en):
        return it[0], en[0]
    return None


def _slug(field, en):
    s = unicodedata.normalize("NFKD", en).encode("ascii", "ignore").decode().lower()
    words = [w for w in re.findall(r"[a-z0-9]+", s) if w not in {"the", "a", "an", "of", "to", "and", "it", "is", "in"}][:7]
    return field + "__" + "_".join(words)


def compact(db):
    """Returns a copy of the database with corpus and references (the dictionary passed in does not change)."""
    import copy
    db = copy.deepcopy(db)
    old = db.pop(KEY, None) or {}
    slots = [(c, k, f, it.get("id")) for it in db.get("items") or [] for c, k, f in _slots(it)]
    full, first = {}, {}
    for cont, k, field, iid in slots:
        t = cont[k]
        full.setdefault((t["it"], t["en"]), []).append((field, iid))
        f = _first(t)
        if f:
            first.setdefault(f, []).append((field, iid))
    for f in list(first):                                    # also the texts that coincide with the first sentence alone
        if f in full:
            first[f] = first[f] + full[f]
    by_text = {(v["it"], v["en"]): k for k, v in old.items() if _is_bil(v)}
    cand = {}
    for src in (full, first):
        for text, uses in src.items():
            fields = [u[0] for u in uses]
            if len(uses) >= MIN_USES and len({u[1] for u in uses}) >= MIN_ITEMS and text not in cand:
                cand[text] = max(set(fields), key=fields.count)
    keys, used = {}, {}
    for text in sorted(cand, key=lambda t: (cand[t], t)):
        k = by_text.get(text)
        if not k:
            base = _slug(cand[text], text[1]) or cand[text]
            k, n = base, 2
            while k in keys.values() or (k in old and (old[k]["it"], old[k]["en"]) != text):
                k, n = f"{base}_{n}", n + 1
        keys[text] = k
    prefixes = sorted(keys, key=lambda t: -len(t[0]))
    for cont, k, field, _ in slots:
        t = cont[k]
        text = (t["it"], t["en"])
        if text in keys:
            cont[k] = {"corpus_ref": keys[text]}
            used[keys[text]] = text
            continue
        for p in prefixes:
            if t["it"].startswith(p[0] + " ") and t["en"].startswith(p[1] + " "):
                cont[k] = {"corpus_ref": keys[p], "specific_addition": {"it": t["it"][len(p[0]):].strip(), "en": t["en"][len(p[1]):].strip()}}
                used[keys[p]] = p
                break
    corpus = {k: {"it": v[0], "en": v[1]} for k, v in sorted(used.items())}
    out = {}
    for k, v in db.items():
        out[k] = v
        if k == "metadata":
            out[KEY] = corpus
    if KEY not in out:
        out = {KEY: corpus, **out}
    return out
