"""Generates data/database_guide.md: an annotated guide to the database structure, with real excerpts from the tomato record.
Usage:  python scripts/make_db_guide.py
"""
import json

from common import DATA, load_json

EX = "pomodoro_tomato"


def js(o, limit=None):
    s = json.dumps(o, ensure_ascii=False, indent=2)
    if limit and len(s) > limit:
        s = s[:limit].rsplit("\n", 1)[0] + "\n  …"
    return f"```json\n{s}\n```"


def trim_months(o):
    """Shortens 12-month arrays for readability."""
    if isinstance(o, dict):
        return {k: trim_months(v) for k, v in o.items()}
    if isinstance(o, list) and len(o) == 12 and all(isinstance(x, str) for x in o):
        return " ".join({"out_of_season": "·", "in_season": "S", "peak_season": "P", "primizie": "p", "end_of_season": "f",
                         "not_applicable": "x"}[x] for x in o)
    if isinstance(o, list) and len(o) == 12 and all(isinstance(x, bool) for x in o):
        return "".join("S" if x else "·" for x in o)
    return o


def en(o):
    """English side of an {it, en} text."""
    return o.get("en") or o.get("it") if isinstance(o, dict) else o


def main():
    db = load_json(DATA / "database.json")
    it = next(i for i in db["items"] if i["id"] == EX)
    m = db["metadata"]
    r, n, b = it["ripening_and_storage"], it["nutrition_and_sustainability"], it["botany"]
    ph = r["postharvest_physiology"]
    L = []
    w = L.append
    w("# Peak Season database guide\n")
    w("This guide explains how `data/database.json` is built, block by block, using the real **tomato** record as an example. "
      "For each block: what it is for in the app, where the data come from, how to read them.\n")
    w("## 1. Files\n")
    w("| File | Content |\n|---|---|\n"
      f"| `data/database.json` | The database: `metadata` (legends, methods, sources) + `items` ({len(db['items'])} records) |\n"
      "| `data/schema.json` | The formal rules (JSON Schema): types, allowed values, required fields |\n"
      "| `data/items_index.json` | The master list: for each product, its exact codes and URLs on every source |\n"
      "| `data/draft_legacy_values.json` | Values from the initial draft that could not be verified: removed from the app but preserved |\n"
      "| `data/scraping_report.md` | The reliability and gap report |\n"
      "| `data/audit_findings.json` | Results of the item-by-item re-check |\n"
      "| `data/raw/` | Copies of the raw source data (PDF, CSV, xlsx, pages; not published) |\n"
      "| `scripts/config/` | Tables hand-curated from the sources, with quotes and page numbers |\n"
      "| `assets/images/` | Photos `<id>_01.jpg`, `_02.jpg`… (credits in `_metadata.json`) |\n")
    w("## 2. General logic\n")
    w("Every record follows the same 12-block structure. Three principles apply everywhere:\n")
    w("1. **Every value has a source.** Structured blocks carry the source next to the value (`source`, `basis`, `source_food`, `derivation`); "
      "all sources of a record are listed in `sources_by_topic.sources_used`.")
    w("2. **`null` is not the same as empty.** A `null` is either a real gap (listed in `data_completeness.missing_fields`) or a field that "
      "makes no sense for that product (listed in `not_applicable_fields`): e.g. the chilling-injury threshold for produce that is not chill-sensitive.")
    w("3. **Bilingual.** Every user-facing text is an object `{\"it\": …, \"en\": …}` (see §13).\n")
    w("Identifiers (`id`) are `italianname_englishname` without accents: they are also the keys used by cross-references between records "
      "(e.g. `keep_away_from`, `compatible_with`) and by photo file names.\n")

    w("## 3. Identity and botany\n")
    w(js({k: it[k] for k in ("id", "names", "category")}))
    w("`category` is one of the 5 template values. Synonyms come from EPPO (official IT/EN common names).\n")
    w(js(b))
    w("- `scientific_name`, `family`, `genus`: verified on EPPO and World Flora Online (`eppo_code` and `wfo_id` are the official codes).\n"
      "- `plant_part_used`: confirmed by the source texts.\n"
      "- `upov_*`: the species code of the **EU Common Catalogue of varieties**; `varieties_registered_italy.count` = varieties currently on the Italian register.\n")

    w("## 4. Varieties and territories\n")
    iv = it["italian_varieties_and_territories"]
    w(js(iv, 2200))
    w("- `notable_varieties` contains **only** verified varieties; `varieties_verification` says where (Slow Food, EU Catalogue, Orto da Coltivare…) and under which name they are registered.\n"
      "- `dop_igp_labels` and `has_dop_igp` (PDO/PGI) are verified on the EU **eAmbrosia** register (`eambrosia_verified`).\n"
      "- **Traditional Agri-food Products (PAT)** are in `nutrition_and_sustainability.traditional_products_pat` (see §9).\n")

    w("## 5. Images\n")
    w(js({"primary": it["images"]["primary"], "gallery": it["images"]["gallery"][:3] + ["…"], "image_details": it["images"]["image_details"][:1]}))
    w("Every photo has author, licence, source URL and type (`view_type`): `full_frame` (the product fills the frame: it is the "
      "main photo when available), `isolated_background` (white or coloured background), `plant_in_field` (the plant), `botanical_plate` "
      "(botanical plate), `cut_section` (cut open), `other`. `flags` reports known issues (plate, wrong subject), `variety` a "
      "specific variety (e.g. flat peach). `sync_images.py` realigns the database when photos are removed from the folder.\n")

    w("## 6. Seasonality\n")
    w("In the excerpt the 12 months (Jan→Dec) are abbreviated: `·` out of season, `p` early season, `S` in season, `P` peak, `f` end of season.\n")
    w(js(trim_months({k: it["seasonality"][k] for k in ("italy_macro_areas", "eufic_climatic_zones", "derivation_notes")})))
    w("- `italy_macro_areas` (North, Centre, South and Islands) is the seasonality for Italian users: it comes from a **vote across several sources** "
      "(WWF, Greenpeace, Altroconsumo, EUFIC for Italy, Orto da Coltivare harvest periods); the method is in `metadata.seasonality_method`. "
      "For each month the sources listing it are counted: with at least half of the votes the month is in season, with fewer it is early or end of season; "
      "the **peak** is the central months of a run of at least three months on which all sources agree.\n"
      "- `eufic_climatic_zones`: the 6 European zones, derived from the EUFIC countries (`eufic_by_country`); where EUFIC lacks the product, the Alpine zone "
      "comes from the Austrian calendar (the national source cited by EUFIC) and the Mediterranean zone is derived from the South and Islands. "
      "`eufic_zone_sources` gives the provenance of each zone.\n")

    w("## 7. Agricultural (garden) calendar\n")
    w(js(it["agricultural_calendar_italy"], 1500))
    w("Sowing, transplanting and harvest months by area, with agronomic parameters (depth, spacing, exposure, moon) "
      "from Orto da Coltivare. For fruit, herbs and cereals the draft values are still used (documented gap).\n")

    w("## 8. Buying, ripening and storage\n")
    w("This is the richest block. It reads on three levels: **user-facing texts**, **short advice**, **scientific data**.\n")
    w("### 8a. User-facing texts\n")
    w(js({"buying_guide": it["buying_guide"], "card_short_storage": r["card_short_storage"], "ripening_badge_label": r["ripening_badge_label"]}, 1800))
    w("`card_short_storage` is the short label for the card (≤ 42 characters), consistent with FoodKeeper and UC Davis data; `storage_instructions` is the long text.\n")
    w("### 8b. Short advice for the app\n")
    w(js({"home_storage": r["home_storage"], "perishability": r["perishability"]}))
    w("- `home_storage.location`: **where** to keep it at home (fridge, on the counter until ripe, room temperature, pantry). "
      "Main source: the UC Davis/Kader guide; FoodKeeper for storage times; conflicts between the two sources are written in `derivation`.\n"
      "- `perishability`: the respiration class turned into a level from 1 to 6, with label and advice. The faster a product respires, the sooner it loses freshness.\n")
    w(js({"storage_compatibility": {**r["storage_compatibility"], "compatible_with": r["storage_compatibility"]["compatible_with"][:6] + ["…"]}}))
    w("`storage_compatibility`: which products it can be stored with (same temperature and humidity, no ethylene conflict). Source: HB66, Thompson table.\n")
    w("### 8c. Postharvest scientific data\n")
    w(js(ph))
    w("- `ripening_type` (in the `ripening_and_storage` block): `climaterico` (keeps ripening after harvest, e.g. tomato, banana, pear) "
      "or `non_climaterico` (stops ripening, e.g. citrus, grape, strawberry); IT/EN labels in `metadata.vocabulary`.\n"
      "- `freezing_point_c`: HB66's \"highest freezing point\", the highest temperature at which ice starts to form; for a range "
      "the upper end (the most cautious) is used.\n"
      "- `optimal_temperature_c` and `optimal_humidity_percent`: optimal **commercial** conditions (USDA HB66, UC Davis).\n"
      "- `chilling_injury`: whether it is chill-sensitive, below which threshold (`critical_temperature_c` = upper end of the lowest safe range, "
      "`lowest_safe_range_c`) and with which symptoms. Ripe tomato is sensitive below 7-10 °C (13 °C when still green): that is why it is better kept out of the fridge.\n"
      "- `estimated_shelf_life_days`: **home** storage times from FoodKeeper (`room_temp_mode` says whether \"until ripe\" or \"fridge only\" applies); "
      "`commercial_optimal_days` is the shelf life under commercial conditions.\n")
    w(js(r["ethylene_compatibility"]))
    w("Ethylene: whether it produces it (and how much, class at 20 °C) and whether it is sensitive to it. `keep_away_from` is computed: the strong producers in the database "
      "to keep it away from, if it is sensitive.\n")

    w("## 9. Nutrition and sustainability\n")
    w(js({k: n[k] for k in ("data_basis", "edible_portion_percentage", "water_percentage", "kcal_per_100g", "macros_per_100g")}))
    w("Values per 100 g of edible portion. `data_basis` says which record is the primary source (CREA, then BDA-IEO, USDA only when the first two are missing).\n")
    w(js({"vitamins": n["vitamins"][:3] + ["…"], "nutrition_claims_eu": n["nutrition_claims_eu"]}))
    w("Every vitamin and mineral has amount, unit, `percent_nrv` (% of the Nutrient Reference Value, Regulation (EU) 1169/2011) and source. "
      "**Claims** are computed by applying the thresholds of Regulation (EC) 1924/2006 (e.g. \"High in vitamin C\" ≥ 30% NRV): "
      "they are not written by hand.\n")
    w(js({"bioactive_compounds": n["bioactive_compounds"][:3] + ["…"]}))
    w("Bioactive compounds: carotenoids (USDA FDC), flavonoid classes (USDA Flavonoid DB), total polyphenols and phenolic acids "
      "(Phenol-Explorer). `group` lets the app group them, `main_compounds` says which are the main ones.\n")
    w(js({k: n[k] for k in ("allergens_eu", "reference_portion", "protein_reference")}))
    w("- `allergens_eu`: allergens from Annex II of Regulation (EU) 1169/2011 (empty list = none).\n"
      "- `reference_portion`: the standard LARN portion (via IEO SmartFood), with a practical equivalent and per-portion values.\n"
      "- `protein_reference`: protein compared with the LARN requirement.\n")
    w(js(n["environmental_footprint"]))
    w("Sustainability (SU-EATABLE LIFE): CO2 and water per kg and per portion, with the database entry, number of studies and range. "
      "`greenhouse_comparison` shows the weight of heated greenhouses (out of season). `sustainability_rating` turns the numbers into levels and advice.\n")
    pat = n["traditional_products_pat"]
    w(js({**pat, "products": pat["products"][:4] + ["…"], "regions": pat["regions"][:6] + ["…"]}))
    w("`traditional_products_pat`: the Traditional Agri-food Products from the MASAF list linked to the product, with their region.\n")
    w(js({k: n[k] for k in ("health_benefits_and_curiosities", "culinary_waste_reduction")}))
    w("Texts: benefits (only with nutrients consistent with the claims) and anti-waste ideas.\n")

    w("## 10. Record sources\n")
    s = it["sources_by_topic"]
    w(js({"sources_used": s["sources_used"][:3] + ["…"], "useful_links": s["useful_links"][:3] + ["…"]}))
    w(f"`sources_used` lists **all** the sources used for this product ({len(s['sources_used'])} for the tomato), with topic, URL and local files. "
      f"`useful_links` are the links shown to the user ({len(s['useful_links'])}). `source_codes` holds the exact record codes (CREA, BDA, FDC…).\n")

    w("## 11. Traceability: `data_completeness`\n")
    d = it["data_completeness"]
    w(js({"is_complete": d["is_complete"], "fields_pending_verification": d["fields_pending_verification"][:4],
          "missing_fields": d["missing_fields"][:4], "not_applicable_fields": d["not_applicable_fields"][:4],
          "discrepancies": d["discrepancies"][:2], "notes": d["notes"][:400] + "…"}))
    w("This block is for maintainers, not for users: it says what came from the draft, what was verified, what is missing, what is not applicable, "
      "where the draft differed from the sources (`discrepancies`, with draft value, source value and source) and why (`notes`, an internal log written in Italian).\n")

    w("## 12. Metadata\n")
    w("`metadata` holds everything that applies to the whole database and sits at the top of the file:\n")
    for k in m:
        w(f"- `{k}`")
    w("\nThe **legends** (seasonal states, zones, perishability, storage, compatibility groups) and the **methods** "
      "(seasonality, postharvest, protein, footprints) are designed to be read directly by the app.\n")

    w("## 13. Bilingualism\n")
    w("The app can be used entirely in Italian or entirely in English:\n")
    w("- every user-facing text is `{\"it\": …, \"en\": …}`, including the rationales (`basis`, `derivation`, `method`, variety notes);\n"
      "- coded values (e.g. `climaterico`, `in_season`, `fridge`) are keys: the label to display is in `metadata.vocabulary`;\n"
      "- nutrients and compounds have `name` and `name_en`;\n"
      "- only proper names stay in their original language (varieties, PDO/PGI, PAT, scientific names, authors, licences, sources);\n"
      "- `data_completeness.notes` is a technical log in Italian, not used by the app.\n")
    voc = m["vocabulary"]
    w(js({"ripening_and_storage.ripening_type": voc["ripening_and_storage.ripening_type"]}))
    w(f"Vocabulary groups ({len(voc)}): " + ", ".join(f"`{k}`" for k in voc) + ".\n")

    w("## 14. Glossary and \"?\" icons\n")
    w("Explanations are written once, in `metadata.glossary`, and reached from several places:\n")
    w("| From | Field | Example |\n|---|---|---|\n"
      "| a field | `metadata.field_help[path]` | `ripening_and_storage.ripening_type` → `climacteric`, `non_climacteric` |\n"
      "| a value | `metadata.vocabulary[group][value].glossary` | `climaterico` → `climacteric` |\n"
      "| a product | `item.help_refs` | broad bean → `favism` on the benefits text |\n"
      "| another entry | `glossary[id].see_also` | `climacteric` → `ethylene`, `non_climacteric` |\n"
      "| a source | `official_sources[].used_for.glossary_entries` | HB66 → storage entries |\n")
    g = m["glossary"]["climacteric"]
    w(js(g, 2500))
    w("Each entry: `term`, `short` (one line for the tooltip), `text` (full explanation), `sources` (name and URL from the catalogue), `see_also`. "
      f"Entries ({len(m['glossary'])}): " + ", ".join(f"`{k}`" for k in m["glossary"]) + ".\n")
    w(js({"help_refs": it.get("help_refs", [])[:6]}))
    w(js({"field_help": dict(list(m["field_help"].items())[:6])}))

    w("## 15. Source catalogue\n")
    w("`metadata.official_sources` describes every source: what it is (`description`), why it is authoritative (`authority`), what it offers (`offers`), "
      "for which topics and which products it was consulted (`used_for`). Full list:\n")
    for s in sorted(m["official_sources"], key=lambda s: -s["used_for"]["items_count"]):
        u = s["used_for"]
        w(f"### {s.get('name', s['key'])}\n")
        w(f"`{s['key']}` · {s.get('url', '')}\n")
        w(f"- **What it is**: {en(s['description'])}")
        w(f"- **Why it is authoritative**: {en(s['authority'])}")
        w(f"- **What it offers**: {en(s['offers'])}")
        w("- **Used for**: " + (", ".join(en(t["label"]) for t in u["topics"]) or "database level"))
        if u["items"]:
            w(f"- **Products ({u['items_count']})**: " + ", ".join(u["items"]))
        elif u["database_level"]:
            w("- **Products**: used for the whole database (methods and legends), not for individual records")
        if u["glossary_entries"]:
            w("- **Glossary entries**: " + ", ".join(u["glossary_entries"]))
        w("")

    w("## 16. Conflicts between sources\n")
    w("`metadata.source_conflicts`: the general cases where sources give different values, with the decision taken.\n")
    for cf in m["source_conflicts"]:
        w(f"### {en(cf['issue'])}\n")
        w(f"- **Why**: {en(cf['why'])}\n- **Decision**: {en(cf['decision'])}\n- **Rationale**: {en(cf['rationale'])}\n")

    w("## 17. How the app uses it\n")
    w("| Screen | Fields |\n|---|---|\n"
      "| Product card | `names`, `images.primary`, month state from `seasonality.italy_macro_areas[area]`, `ripening_and_storage.card_short_storage`, `perishability.label` |\n"
      "| Shopping list | `buying_guide.shopping_list_preview`, `ripening_badge_label` |\n"
      "| Storage | `home_storage`, `storage_instructions`, `estimated_shelf_life_days`, `storage_compatibility`, `ethylene_compatibility` |\n"
      "| Nutrition | `reference_portion`, `macros_per_100g`, `nutrition_claims_eu`, `vitamins`, `minerals`, `allergens_eu` |\n"
      "| Sustainability | `environmental_footprint.sustainability_rating`, `greenhouse_comparison`, `metadata.sustainable_diet_summary` |\n"
      "| Territory | `notable_varieties`, `dop_igp_labels`, `traditional_products_pat`, `varieties_registered_italy` |\n"
      "| Garden | `agricultural_calendar_italy` |\n"
      "| Learn more | `sources_by_topic.useful_links` |\n"
      "| \"?\" help | `metadata.field_help`, `metadata.vocabulary`, `item.help_refs` → `metadata.glossary` |\n"
      "| Sources | `metadata.official_sources`, `metadata.source_conflicts` |\n")
    (DATA / "database_guide.md").write_text("\n".join(L), encoding="utf-8")
    print("wrote data/database_guide.md")


if __name__ == "__main__":
    main()
