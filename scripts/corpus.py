"""Corpus condiviso delle descrizioni (shared_descriptions_corpus, revisione 2026-11-12).

Nel file data/database.json i testi descrittivi ripetuti tra i prodotti (consigli di conservazione, note sulle fonti,
spiegazioni di metodo...) sono scritti una volta sola in "shared_descriptions_corpus" (subito dopo "metadata") e nei
prodotti sono richiamati così:
    { "corpus_ref": "chiave" }                                         -> testo del corpus
    { "corpus_ref": "chiave", "specific_addition": { "it", "en" } }    -> testo del corpus + " " + aggiunta specifica
I testi unici restano { "it", "en" } completi.

Gli script della pipeline lavorano sempre sul testo completo: common.load_json espande i riferimenti (expand) e
common.save_json li ricompatta (compact) quando il file è database.json. La compattazione è deterministica e conserva
le chiavi esistenti: se il testo di una voce del corpus viene modificato (es. con l'editor dei testi), tutti i prodotti
che la usano cambiano insieme e la chiave resta la stessa.
Regole: un testo completo usato almeno MIN_USES volte da almeno MIN_ITEMS prodotti diversi diventa una voce; la prima frase di testi più lunghi, se
ripetuta almeno MIN_USES volte (in italiano e in inglese), diventa una voce con "specific_addition" per il resto.
Si compattano solo i campi descrittivi (FIELDS), mai etichette brevi, nomi o titoli.
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
    """Testo completo {it, en} di un riferimento al corpus (o l'oggetto stesso se non è un riferimento)."""
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
    """(contenitore, chiave, campo) di ogni testo descrittivo {it, en} nei prodotti."""
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
    """Restituisce una copia del database con corpus e riferimenti (il dizionario passato non cambia)."""
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
    for f in list(first):                                    # anche i testi che coincidono con la sola prima frase
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
