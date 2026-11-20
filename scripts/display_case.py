"""Capital first letter in the texts shown by the app (user rule, 2026-11-20).

Every user-visible text line starts with an upper-case letter, even short fragments ("Quercetina, miricetina").
Allowed exceptions:
- brands and proper names written with a lower-case initial (eAmbrosia, iNaturalist...): BRANDS;
- chemical locants such as "p-Coumaric acid" or "trans-resveratrolo" (a lower-case prefix followed by "-");
- texts that start with a digit or a symbol.
Used by capitalize_display_texts.py (fixes the data) and validate_db.py (checks it).
Internal fields are not checked: data_completeness, images (author names), sources_by_topic.source_codes,
footprint reference notes and the technical notes in metadata.
"""
import re

BRANDS = ("eAmbrosia", "iNaturalist", "iPhone")
LOCANT = re.compile(r"^(?:[a-z]|cis|trans|alfa|beta|gamma|alpha)-")
SKIP_KEYS = {"data_completeness", "images", "source_codes", "carbon_reference", "water_reference", "author", "url",
             "id", "key", "source", "source_key", "glossary_id", "fields", "favicon", "favicon_dark", "svg_dir",
             "svg_format", "_doc", "_grouping", "_used_by", "_glossary", "glossary"}
# fields with a plain string (not {it, en}) shown by the app
PLAIN_FIELDS = {"main_compounds", "main_compounds_en"}


def needs_cap(s):
    if not isinstance(s, str) or not s or not s[0].islower():
        return False
    return not (s.startswith(BRANDS) or LOCANT.match(s))


def cap(s):
    return s[0].upper() + s[1:] if needs_cap(s) else s


def walk(o, path="", fix=False, out=None):
    """Lists (or fixes, with fix=True) the user-visible strings that start with a lower-case letter."""
    out = [] if out is None else out
    if isinstance(o, dict):
        is_text = isinstance(o.get("it"), str) and isinstance(o.get("en"), str)
        for k, v in o.items():
            if k in SKIP_KEYS:
                continue
            p = f"{path}.{k}"
            if isinstance(v, str) and k in PLAIN_FIELDS:            # compound names: Title Case
                if compound_title(v) != v:
                    out.append((p, v))
                    if fix:
                        o[k] = compound_title(v)
            elif isinstance(v, str) and ((is_text and k in ("it", "en")) or (k == "name" and ".products[" in path)):
                if needs_cap(v):
                    out.append((p, v))
                    if fix:
                        o[k] = cap(v)
            else:
                walk(v, p, fix, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}[{i}]", fix, out)
    return out


def scan(db, fix=False):
    """Items, the shared corpus and the metadata shown by the app (not the technical method notes)."""
    out = []
    for it in db["items"]:
        walk(it, it["id"], fix, out)
    walk(db.get("shared_descriptions_corpus") or {}, "shared_descriptions_corpus", fix, out)
    m = db["metadata"]
    for k in ("glossary", "vocabulary", "home_storage_legend", "official_sources", "seasonality_states_legend",
              "italy_macro_areas_legend", "perishability_legend", "storage_compatibility_legend", "macros_note",
              "seasonality_estimates_method", "nutrition_claims_eu_rules"):
        if k in m:
            walk(m[k], f"metadata.{k}", fix, out)
    return out


def compound_title(s):
    """Compound names in Title Case (user rule, 2026-11-20): "acido ferulico, quercetina" -> "Acido Ferulico, Quercetina".
    Words starting with a chemical locant ("5-eneicosilresorcinolo", "p-Coumaric", "trans-resveratrolo") are left as
    they are, like the app does on display."""
    if not isinstance(s, str):
        return s
    words = s.split(" ")
    return " ".join(w if (not w or not w[0].islower() or LOCANT.match(w)) else w[0].upper() + w[1:] for w in words)


# Proper nouns that must never appear in lower case (validate_db.py warning). Italian adjectives of place ("ribollita
# toscana") are allowed, so only nouns are listed for Italian; English adjectives of place are always capitalised.
PROPER_NOUNS = """Abruzzo Basilicata Calabria Campania Emilia-Romagna Friuli Lazio Liguria Lombardia Molise Piemonte Puglia
Sardegna Sicilia Trentino Umbria Veneto Italia Europa Treviso Chioggia Verona Castelfranco Tropea Pachino Vesuvio Napoli
Etna Bronte Sorrento Amalfi Cuneo Modena Polesine Mantova Parma Trapani Ragusa Catania Lecce Foggia Salerno Pistoia
Valtellina Kader Englyst Greenpeace Altroconsumo FoodKeeper Catalogna Italy Europe Sicily Sardinia Tuscany Apulia
Italian Mediterranean Sicilian European Tuscan Ligurian Neapolitan Venetian Apulian Calabrian Sardinian Piedmontese
Roman Spanish French Greek Turkish Chinese Japanese American Asian African Mexican Peruvian""".split()
_PN = re.compile(r"(?<![\w'’/-])(" + "|".join(re.escape(n.lower()) for n in PROPER_NOUNS) + r")(?![\w-])")
PN_EXEMPT = ("data_basis", "source_food", "upov_name", "sel_name")       # official register / database entry names


def lowercase_proper_nouns(db):
    """[(path, word)] for known proper nouns written in lower case in the texts shown by the app."""
    out = []

    def check(path, s):
        for m in _PN.finditer(s):
            out.append((path, m.group(1)))

    def rec(o, path):
        if isinstance(o, dict):
            is_text = isinstance(o.get("it"), str) and isinstance(o.get("en"), str)
            for k, v in o.items():
                if k in SKIP_KEYS or k in PN_EXEMPT or k in ("products", "notable_varieties", "dop_igp_labels"):
                    continue
                if isinstance(v, str) and (is_text and k in ("it", "en")):
                    check(f"{path}.{k}", v)
                else:
                    rec(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                rec(v, f"{path}[{i}]")
    for it in db["items"]:
        rec(it, it["id"])
    rec(db["metadata"].get("glossary") or {}, "metadata.glossary")
    return out
