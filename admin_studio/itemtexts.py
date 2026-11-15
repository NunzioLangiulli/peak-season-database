"""Product Texts tab: every IT/EN text of each product, grouped by section, with what can be edited and where it comes from.

Three kinds of field:
- "corpus": fields that may point to a shared corpus entry (scripts/corpus.py FIELDS); editable.
- "block":  the texts written by hand per product in scripts/texts/block_*.json (shopping list preview, detailed selection,
            card storage line, benefits and curiosities, waste reduction); editable.
  scripts/apply_texts.py copies the block files into the database, so a saved edit is written to BOTH the database and the
  block file: a later apply_texts.py run keeps it. storage_instructions ("si") and, when the block has one, the chilling
  symptoms ("cn") are mirrored the same way although they are "corpus" fields.
- "generated": written by a script from other data (templates, footprint labels, claims, synonyms…): shown read-only with
  the script to change instead.
Link titles (sources_by_topic) are left to the Links tab.
"""
import json
from pathlib import Path

from common import ROOT
from corpus import FIELDS

TEXTS = ROOT / "scripts" / "texts"
# (path inside the item) -> key in the block file
BLOCK = {("buying_guide", "shopping_list_preview"): "sl", ("buying_guide", "detailed_selection"): "ds",
         ("ripening_and_storage", "card_short_storage"): "cs", ("ripening_and_storage", "storage_instructions"): "si",
         ("nutrition_and_sustainability", "health_benefits_and_curiosities"): "hb",
         ("nutrition_and_sustainability", "culinary_waste_reduction"): "wr",
         ("ripening_and_storage", "postharvest_physiology", "chilling_injury", "symptoms"): "cn"}
LIMITS = {"sl": 130, "cs": 42}                         # apply_texts.py warns above these lengths (app layout)
SECTIONS = {"names": "Names", "buying_guide": "Buying guide", "ripening_and_storage": "Ripening & storage",
            "nutrition_and_sustainability": "Nutrition & sustainability", "seasonality": "Seasonality",
            "italian_varieties_and_territories": "Varieties & territories", "agricultural_calendar_italy": "Garden calendar",
            "botany": "Botany", "images": "Images"}
SKIP = {"data_completeness", "sources_by_topic", "help_refs"}
# templates of apply_texts.py: an edit in the database is lost when apply_texts.py runs again
TEMPLATED = {"ripening_badge_label", "compatibility_notes", "speed_up", "slow_down"}
GENERATOR = {"ripening_badge_label": "scripts/apply_texts.py (template from the ripening type)",
             "carbon_label": "scripts/enrich_footprint.py", "water_label": "scripts/enrich_footprint.py",
             "boundary": "scripts/enrich_footprint.py", "nutrition_claims_eu": "scripts/build_nutrition_claims_rules.py",
             "claim_note": "scripts/enrich_protein.py", "synonyms": "scripts/enrich_botany.py / add_items.py",
             "data_basis": "the enrich_* scripts (nutrition sources)", "upov_note": "scripts/apply_upov.py",
             "group": "scripts/enrich_allergens_portions.py", "frequency": "scripts/enrich_allergens_portions.py",
             "equivalent": "scripts/enrich_allergens_portions.py", "allergens_note": "scripts/enrich_allergens_portions.py",
             "variety": "scripts/sync_images.py", "label": "the database scripts (labels of coded values)",
             "title": "the database scripts"}


def is_text(v):
    return isinstance(v, dict) and (("it" in v and "en" in v and set(v) <= {"it", "en"}) or "corpus_ref" in v)


def blocks():
    """{item_id: (file, entry)} from scripts/texts/block_*.json."""
    out = {}
    for f in sorted(TEXTS.glob("block_*.json")):
        for iid, e in json.loads(f.read_text(encoding="utf-8")).items():
            out[iid] = (f, e)
    return out


def _walk(o, path, field, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if not path and k in SKIP:
                continue
            if is_text(v):
                out.append((path + [k], k, v))
            else:
                _walk(v, path + [k], k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if is_text(v):
                out.append((path + [i], field, v))
            else:
                _walk(v, path + [i], field, out)


def fields(item, block):
    out = []
    raw = []
    _walk(item, [], None, raw)
    for path, key, v in raw:
        keys = tuple(p for p in path if isinstance(p, str))
        bk = BLOCK.get(keys)
        if bk == "cn" and not (block or {}).get("cn"):
            bk = None                                    # symptoms not written by hand for this product
        f = {"path": path, "value": v, "section": SECTIONS.get(path[0], str(path[0]).replace("_", " ").capitalize())}
        if bk:
            f["block"] = bk
            if bk in LIMITS:
                f["limit"] = LIMITS[bk]
        if key in FIELDS or bk:
            f["kind"] = "block" if bk and key not in FIELDS else "corpus"
            if key in TEMPLATED and not bk:
                f["warn"] = "Generated by scripts/apply_texts.py from a template: an edit here is lost if that script runs again."
        else:
            f["kind"] = "generated"
            if isinstance(v.get("it"), list):
                v = {"it": ", ".join(map(str, v["it"])), "en": ", ".join(map(str, v.get("en") or []))}
                f["value"] = v
            f["source"] = GENERATOR.get(key, "the database scripts")
        out.append(f)
    order = list(SECTIONS.values())
    out.sort(key=lambda f: order.index(f["section"]) if f["section"] in order else len(order))
    return out


def resolve(v, corpus):
    if "corpus_ref" in v:
        b = corpus.get(v["corpus_ref"]) or {"it": "", "en": ""}
        a = v.get("specific_addition") or {}
        return {lang: (b[lang] + (" " + a[lang] if a.get(lang) else "")).strip() for lang in ("it", "en")}
    return {"it": v.get("it", ""), "en": v.get("en", "")}


def sync_blocks(changes, corpus):
    """Write the edited block-backed texts into scripts/texts/block_*.json; returns the files changed."""
    bl = blocks()
    touched = {}
    for ch in changes:
        keys = tuple(p for p in ch["path"] if isinstance(p, str))
        bk = BLOCK.get(keys)
        if not bk or ch["id"] not in bl:
            continue
        f, _ = bl[ch["id"]]
        doc = touched.get(f) or json.loads(f.read_text(encoding="utf-8"))
        entry = doc[ch["id"]]
        if bk == "cn" and not entry.get("cn"):
            continue
        t = resolve(ch["value"], corpus)
        entry[bk] = [t["it"], t["en"]]
        touched[f] = doc
    for f, doc in touched.items():
        ends = f.read_bytes().endswith(b"\n")
        f.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + ("\n" if ends else ""), encoding="utf-8", newline="\r\n")
    return list(touched)
