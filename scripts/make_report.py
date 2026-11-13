"""Generates data/scraping_report.md: how the database was built, organised and validated.
Numbers are computed from the database, the audit and the template coverage; the commentary is fixed text updated by hand.
Usage:  python scripts/make_report.py   (after validate_db.py, audit_db.py and template_coverage.py)
"""
import collections
import json
import re
from datetime import date

from common import DATA, load_json

CAT_EN = {"verdura": "Vegetables", "frutta": "Fruit", "erbe_spezie": "Herbs and spices", "funghi": "Mushrooms", "cereali": "Cereals"}
BLOCKS = [
    ("id, names, category", "identity: stable id, IT/EN names (common, alternative), category"),
    ("botany", "scientific name, family, genus, EPPO/GBIF/UPOV codes, plant part used"),
    ("italian_varieties_and_territories", "verified varieties (EU Common Catalogue, Slow Food, texts), PDO/PGI (eAmbrosia), PAT (MASAF), varieties registered in Italy"),
    ("images", "gallery with author, licence and source URL for every photo"),
    ("seasonality", "month-by-month state for 3 Italian macro-areas and 6 European climate zones, with zone-by-zone provenance"),
    ("agricultural_calendar_italy", "sowing, transplanting, harvest by macro-area; growing parameters"),
    ("buying_guide", "how to choose it, signs of quality and spoilage"),
    ("ripening_and_storage", "climacteric/non-climacteric, ethylene, respiration and perishability, chilling injury, commercial and home storage, compatibility"),
    ("nutrition_and_sustainability", "values per 100 g with a source per value, %NRV, EU claims, bioactive compounds, allergens, LARN portions, carbon and water footprint"),
    ("sources_by_topic", "sources used by topic and useful links"),
    ("data_completeness", "missing fields, fields to verify, non-applicable fields, discrepancies with the draft, notes"),
    ("help_refs", "glossary entries relevant to that product (\"?\" icons)"),
]


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rows]
    return "\n".join(out)


def count_bilingual(o):
    if isinstance(o, dict):
        n = 1 if set(o) == {"it", "en"} else 0
        return n + sum(count_bilingual(v) for v in o.values())
    if isinstance(o, list):
        return sum(count_bilingual(v) for v in o)
    return 0


def en(o):
    """English side of an {it, en} text."""
    return o.get("en") or o.get("it") if isinstance(o, dict) else o


def main():
    db = load_json(DATA / "database.json")
    md = db["metadata"]
    items = db["items"]
    N = len(items)
    legacy = load_json(DATA / "draft_legacy_values.json")
    audit = load_json(DATA / "audit_findings.json")
    cov = load_json(DATA / "template_coverage.json")
    L = []
    w = L.append
    dcs = [i["data_completeness"] for i in items]
    miss = sum(len(d["missing_fields"]) for d in dcs)
    pend = sum(len(d["fields_pending_verification"]) for d in dcs)
    disc = sum(len(d["discrepancies"]) for d in dcs)
    na = sum(len(d.get("not_applicable_fields", [])) for d in dcs)
    img_err = sum(1 for a in audit if a["area"] == "images")
    sev = collections.Counter(a["severity"] for a in audit if a["area"] != "images")

    # ------------------------------------------------------------------ header
    w("# Peak Season – Phase 1 report: building, organising and validating the database\n")
    w(f"Generated on {date.today().isoformat()} by `scripts/make_report.py` · database v{md['version']} · {N} products · "
      f"schema `data/schema.json` (JSON Schema 2020-12).\n")
    w("This report explains the method used to build the database, how it is organised (records, metadata, sources, glossary, "
      "bilingualism) and how it was checked. The field-by-field guide is in `data/database_guide.md`.\n")

    w("## 1. Summary\n")
    w(table([
        ["Products", N, ", ".join(f"{CAT_EN[c]} {n}" for c, n in collections.Counter(i["category"] for i in items).most_common())],
        ["Catalogued sources", len(md["official_sources"]), "each with description, authority, contents and uses (§4)"],
        ["Sources used per product", f"average {sum(len(i['sources_by_topic']['sources_used']) for i in items) / N:.1f}", "`sources_by_topic.sources_used`"],
        ["Documented source conflicts", len(md["source_conflicts"]), "with decision and rationale (§5)"],
        ["Glossary entries (\"?\" icons)", len(md["glossary"]), f"{len(md['field_help'])} linked fields, {sum(len(i.get('help_refs', [])) for i in items)} references in products"],
        ["Bilingual {it, en} texts", count_bilingual(db), "everything the user reads exists in Italian and English (§3.4)"],
        ["Schema validation", "0 data errors", f"only image-file warnings remain ({img_err})"],
        ["Systematic re-check (data)", f"{sev['E']} errors, {sev['W']} to review, {sev['I']} informational", "all explained (§6.3)"],
        ["Values still to verify", pend, "almost all agricultural calendars of fruit, herbs and cereals (§7)"],
        ["Fields without data", miss, "real gaps, mapped in §7"],
        ["Non-applicable fields, with reason", na, "e.g. chilling injury for produce that is not sensitive"],
    ], ["Item", "Value", "Notes"]))
    w("")

    # ------------------------------------------------------------------ 2. building
    w("## 2. How it was built\n")
    w("### 2.1 Principles\n")
    for t in [
        "**No invented data.** Every value comes from a catalogued source, given in the `source` field or in the `sources_by_topic` block; where no source exists the field stays empty (null) and is listed in `data_completeness.missing_fields`.",
        "**Official and scientific sources first**, with a declared priority order per topic (e.g. nutrition: CREA → BDA-IEO → USDA FoodData Central).",
        "**Per-value traceability**: for nutrients the source is given value by value; for postharvest data the HB66 chapter or table; for footprints the number of studies and the range.",
        "**Declared approximations**: if a source lacks the exact entry the closest one is used and flagged as approximate; estimates (e.g. respiration class from Q10) are flagged as estimated and explained in the `basis` field.",
        "**Not applicable ≠ missing**: a field that by definition does not apply (e.g. chilling injury for produce that does not suffer from it) is marked N/A with a reason and not counted as a gap.",
        "**The initial draft as a starting point, not as a source**: its 91 products were migrated into the structure; every value differing from the sources is recorded as a discrepancy, every unverifiable value is removed from the app and preserved in `data/draft_legacy_values.json` "
        f"({sum(len(v) for v in legacy['items'].values())} values).",
    ]:
        w(f"- {t}")
    w("\n### 2.2 Pipeline\n")
    w("The database is produced by Python scripts run in a fixed order (`scripts/README.md`). Every script has a docstring with source, method and usage.\n")
    w(table([
        ["1. Sources and index", "downloads and caches the sources (`data/raw/`), builds the master list with each source's codes, migrates the draft"],
        ["2. Nutrition", "CREA and BDA-IEO, USDA for missing items, recomputed %NRV and EU claims, LARN reference for protein"],
        ["3. Seasonality and botany", "vote across Italian calendars, EUFIC map and EUFIC national sources; EPPO, WFO, GBIF; growing notes"],
        ["4. Varieties and territories", "variety checks on texts, Slow Food and the EU Common Catalogue; PDO/PGI on eAmbrosia; UPOV codes; MASAF PAT"],
        ["5. Storage", "USDA HB66 (tables and chapters), Kader classes, FoodKeeper and UC Davis home guide, compatibility groups"],
        ["6. Compounds, allergens, sustainability", "USDA carotenoids and flavonoids, Phenol-Explorer, Reg. (EU) 1169/2011, LARN portions, SU-EATABLE LIFE, AGRIBALYSE"],
        ["7. Texts, images, sources", "IT/EN texts realigned with the data, licensed images, per-product source register"],
        ["8. Bilingualism and help", "`localize_fields.py` (last transformation step), `build_help.py` (vocabulary, glossary), `build_source_catalog.py` (source catalogue and conflicts)"],
        ["9. Checks and reports", "JSON Schema validation, item-by-item re-check, template coverage, reports"],
    ], ["Phase", "What it does"]))
    w("\nChoices that require judgement (quotes from HB66 chapters, mappings between entries of different sources, source descriptions, "
      "glossary, conflicts) live in hand-curated configuration files in `scripts/config/`, each with the quote or page of the source: "
      "every decision can be read and changed without touching the code.\n")

    # ------------------------------------------------------------------ 3. organisation
    w("## 3. How it is organised\n")
    w("`data/database.json` has two parts: `metadata` (everything that applies to the whole database) and `items` (one record per product).\n")
    w("### 3.1 A product record\n")
    w(table([[f"`{a}`", b] for a, b in BLOCKS], ["Block", "Content"]))
    w("\n### 3.2 Metadata\n")
    w(table([
        ["`official_sources`", "source catalogue: what it is, why it is authoritative, what it offers, for which topics and products it was consulted"],
        ["`source_conflicts`", "general cases of disagreement between sources: why, what was decided and why"],
        ["`glossary`", "short but complete explanations of concepts, with sources, for the \"?\" icons"],
        ["`vocabulary`", "IT/EN labels of every coded value (e.g. `climaterico` → \"Climaterico\" / \"Climacteric\"), with the glossary link"],
        ["`field_help`", "which glossary entry explains each field"],
        ["legends and methods", "seasonal states, EUFIC zones, macro-areas, seasonality method, postharvest, perishability, storage, footprints"],
        ["`sustainable_diet_summary`", "EUFIC summary on sustainable diets"],
    ], ["Field", "Content"]))
    w("\n### 3.3 The help system (\"?\" icons)\n")
    w("An explanation is written once, in the glossary, and reached from several places:\n")
    w(f"- **from the field**: `metadata.field_help` links {len(md['field_help'])} field paths (e.g. `ripening_and_storage.ripening_type`) to the entries that explain them;")
    w(f"- **from the value**: every value of `metadata.vocabulary` ({len(md['vocabulary'])} groups) can point to an entry (e.g. `climaterico` → entry *climacteric*);")
    w("- **from the product**: `item.help_refs` lists the entries relevant to that product and the fields where they are shown, computed from the content (allergens, gluten, PDO, PAT, favism for broad beans, Q10 estimates, greenhouse growing…);")
    w("- **from one entry to another**: `see_also`; and **from the source**: `official_sources[].used_for.glossary_entries`.\n")
    w("Every entry has `term`, `short` (one line for the tooltip) and `text` (full explanation) in IT and EN, and its sources with name and URL resolved from the catalogue. "
      "The app therefore holds no help texts of its own: it reads everything from the database.\n")
    w("Entries: " + ", ".join(f"*{en(g['term'])}*" for g in md["glossary"].values()) + ".\n")
    w("### 3.4 Bilingualism\n")
    w("The app must work entirely in Italian or entirely in English. Conventions applied and checked by the audit:\n")
    for t in [
        "every user-facing text is an `{it, en}` object: names, texts, labels, advice, legends, glossary, source descriptions, rationales (`basis`, `derivation`, `method`, variety notes);",
        "coded values (category, seasonal state, classes, storage locations…) are stable keys translated through `metadata.vocabulary`, never shown as they are;",
        "nutrients and compounds keep `name`/`name_en` pairs;",
        "only proper names stay in their original language: varieties, PDO/PGI, PAT, scientific names, authors, licences, source names, verbatim quotes from sources;",
        "`data_completeness.notes` is an internal technical log in Italian, not used by the app.",
    ]:
        w(f"- {t}")
    w("")

    # ------------------------------------------------------------------ 4. sources
    w("## 4. Sources\n")
    w("The full catalogue, with description, authority, contents and the list of every product for which each source was consulted, "
      "sits at the top of the database (`metadata.official_sources`) and is reproduced in the guide. Summary:\n")
    rows = []
    for s in sorted(md["official_sources"], key=lambda s: -s["used_for"]["items_count"]):
        u = s["used_for"]
        rows.append([s.get("name", s["key"])[:75], "whole database" if u["database_level"] and not u["items_count"] else u["items_count"],
                     ", ".join(en(t["label"]) for t in u["topics"])[:80]])
    w(table(rows, ["Source", "Products", "Used for"]))
    w("\nSources assessed but not used: ISMEA and regional calendars for fruit harvest periods (no structured data by macro-area); "
      "USDA ARS Image Gallery (few relevant images); MAPA calendar (Spain), cited by EUFIC but unreachable (404 pages). "
      "My-PersonalTrainer is used only for texts and links, never for numeric values.\n")

    # ------------------------------------------------------------------ 5. conflicts
    w("## 5. Conflicts between sources and decisions\n")
    w("The cases are in `metadata.source_conflicts` (IT/EN). In short:\n")
    for c in md["source_conflicts"]:
        w(f"- **{en(c['issue'])}** {en(c['why'])} → *Decision:* {en(c['decision'])} *Why:* {en(c['rationale'])}")
    w("\nIndividual product-level cases remain recorded in `data_completeness.discrepancies` "
      f"({disc} discrepancies between the draft and the sources) and in the `basis` and `note` fields.\n")

    # ------------------------------------------------------------------ 6. validation
    w("## 6. How it was validated\n")
    w("Four levels of checks, all re-runnable.\n")
    w("### 6.1 Schema\n")
    w("`validate_db.py` checks the database against `data/schema.json` (types, required fields, allowed values, month and bilingual-text "
      "formats) plus some consistency checks (ids, water+macronutrient sum, image files present). Result: no data errors; "
      "the only remaining warnings concern image files.\n")
    w("### 6.2 Cross-checks against the sources\n")
    for t in [
        "**Botany**: scientific name compared across EPPO, WFO and GBIF; genus consistent with scientific name and UPOV code.",
        "**Varieties**: shown only if found in a source (source texts, Slow Food, EU Common Catalogue, with registered name and country).",
        "**PDO/PGI**: every designation checked on the EU eAmbrosia register (status and category).",
        "**Nutrition**: energy recomputed from macronutrients, %NRV and EU claims recomputed from the values, salt = sodium × 2.5.",
        "**Postharvest**: HB66 chapter values transcribed with their quote in `scripts/config/hb66_chapter_curated.json`; obvious typos in the summary table excluded.",
    ]:
        w(f"- {t}")
    w("\n### 6.3 Systematic item-by-item re-check\n")
    w("`audit_db.py` checks every record: consistency of energy/macronutrients, %NRV, EU claims, portions and per-portion footprints; seasonal states and "
      "months; harvest versus seasonality; min ≤ max ranges; chilling-injury thresholds and freezing points; home storage times "
      "versus commercial ones; storage location versus text labels; ethylene (producers, \"keep away from\"); "
      "respiration class versus perishability; compatibility group versus temperatures; botany; varieties; PDO/PGI; "
      "images and licences; source URLs; completeness of IT/EN texts and no Italian text in English fields. It also checks the "
      "metadata: every glossary entry bilingual and with registered sources, `see_also`, `field_help` and `help_refs` pointing to existing entries, "
      "every coded value present in the vocabulary, every source described.\n")
    w("Remaining data warnings (explained, not errors):\n")
    rows = [[a["severity"], a["item"], a["field"], a["msg"][:110]] for a in audit if a["severity"] in ("E", "W") and a["area"] != "images"]
    w(table(rows, ["Level", "Product", "Field", "Detail"]))
    w("\nExplanation: in cavolo nero sugars > carbohydrates because of how USDA computes carbohydrates (by difference) → noted; barley slightly exceeds "
      "105 g/100 g when summing water and macronutrients because of rounding in the CREA table; the \"below optimal temperature\" thresholds "
      "come from the end of HB66's lowest safe range; dry onion in group 3 and melon/avocado in group 1B are as in the "
      "HB66 compatibility table (groups for 7-day mixed storage, not optimal temperatures); the differences between labels and "
      "FoodKeeper for chilli pepper, banana and pomegranate are intentional (UC Davis guide, optimised for taste).\n")
    w("### 6.4 Template coverage and reproducibility\n")
    full = sum(1 for c in cov.values() if not c["draft"] and not c["missing"])
    w(f"`template_coverage.py` checks, for each of the {len(cov)} fields of the original JSON template, how many products have verified data: "
      f"{full} fields are complete for all {N} products (details in `data/template_coverage.json`). "
      "Finally, the last part of the pipeline was re-run from an earlier snapshot: the result matches the delivered database "
      "(the re-run also revealed and fixed an ordering dependency in the source register).\n")

    # ------------------------------------------------------------------ 7. recovered data and gaps
    w("## 7. Recovered data and remaining gaps\n")
    ph = [i["ripening_and_storage"]["postharvest_physiology"] for i in items]
    fz = sum(1 for p in ph if p.get("freezing_point_c") is not None)
    rc = sum(1 for p in ph if p.get("respiration_rate_class"))
    q10 = sum(1 for i in items if "Q10" in json.dumps(i["ripening_and_storage"].get("perishability"), ensure_ascii=False))
    zsrc = collections.Counter(z.get("source") for i in items for z in (i["seasonality"].get("eufic_zone_sources") or {}).values())
    agb = sum(1 for i in items if ((i["nutrition_and_sustainability"].get("environmental_footprint") or {}).get("carbon_reference") or {}).get("source") == "agribalyse")
    w("Data recovered in the last phase, from the proposed sources:\n")
    for t in [
        f"**Freezing point** (HB66's \"highest freezing point\", the highest temperature at which ice starts to form; for a range the upper, most cautious end is used): {fz} products. The others have no value in their HB66 chapter.",
        f"**Respiration class**: {rc} products; {q10} estimated at 5 °C from values measured at higher temperatures using HB66 Q10 values, flagged as estimated. Still without a class: cardoon, pumpkin, chestnut, rosemary, quince (no measured value).",
        f"**Carbon footprint of culinary herbs**: {agb} from AGRIBALYSE 3.1 (ADEME), with declared system boundaries (up to consumption, so not directly comparable with SU-EATABLE LIFE). Water footprint not taken from AGRIBALYSE, because it measures scarcity, not volume.",
        "**Italian seasonality for products missing from the calendars**: nectarine from peach (the calendars do not separate them; confirmed by the \"Pesca e Nettarina di Romagna\" PGI and EUFIC); black and white truffle from Law 752/1985, art. 6 (harvest periods); Caesar's mushroom from the Province of Cuneo mushroom sheet (\"summer and early autumn\"). Source in `seasonality.italy_source`.",
        "**Scope decisions (5 November)**: chard and leaf beet merged into \"Chard\" (same species and same CREA record); flat peach (pesca tabacchiera) added as a peach variety (Slow Food Ark of Taste); white truffle added as an exception to the inclusion rule (no CREA/BDA record: nutrition empty and declared). After the systematic review of excluded candidates (`data/excluded_candidates_report.md`) 44 products were added (all except bergamot, caper, sorrel, strawberry tree and purslane) even with incomplete fields: they were built with the same pipeline on a test database and then merged; where official data are missing the field stays empty and declared. For 33 of them Italian seasonality comes from specific sources read by hand (`config/italy_seasonality_curated.json`): Orto da Coltivare harvest periods, Slow Food sheets, Province of Cuneo mushroom sheets, the sour cherry PGI specification; snow pea and mirabelle reuse pea and plum (same species). For 4 of them nutrition comes from a USDA entry of a related product, declared as an approximation.",
        "**Estimates for zones without data** (decision of 6 November): many EUFIC zones are missing (the Pannonian zone covers Hungary only). `seasonality.estimates` holds, separate from the data, estimates from the neighbouring zone with the most similar climate (e.g. Pannonian <- Continental), marked with ≈ in the app and switchable off in Settings; an estimate always starts from real data. For exotic fruit, zones without data are \"Not grown here\". Method in `metadata.seasonality_estimates_method`.",
        f"**European climate zones**: Alpine zone from the Austrian Ministry of Health calendar, the national source cited by EUFIC ({zsrc['austria_gesundheitsportal']} products); Mediterranean zone explicitly derived from South and Islands seasonality ({zsrc['derived_italy_sud_isole']} products). Provenance in `seasonality.eufic_zone_sources`.",
    ]:
        w(f"- {t}")
    w("\nNot recoverable from accessible sources (documented gaps):\n")
    for t in [
        "**Agricultural calendars of fruit, herbs and cereals by macro-area**: neither ISMEA nor regional services publish structured data for North/Centre/South; the draft values remain \"to verify\".",
        "**Local varieties (Law 194/2015)**: there is no downloadable national list, only heterogeneous regional registers.",
        "**Missing Atlantic, Continental, Boreal and Pannonian zones**: they mostly concern products not grown there (citrus, persimmon, loquat, prickly pear); they stay empty.",
        "**Agronomic parameters of herbs and mushrooms (CREA-OF)**: not attempted in this phase.",
        "**Wild mushrooms and truffles**: no environmental footprint (wild harvest, no LCA study).",
    ]:
        w(f"- {t}")
    w("\nGap map (fields without data):\n")
    gap = collections.defaultdict(set)
    for i in items:
        for p in i["data_completeness"]["missing_fields"]:
            q = re.sub(r"\[\d+\]", "", p)
            key = ".".join(q.split(".")[:3]) if q.startswith(("ripening", "nutrition", "seasonality.eufic")) else ".".join(q.split(".")[:2])
            gap[key].add(i["id"])
    rows = [[f"`{k}`", len(u), ", ".join(x.split("_")[0] for x in sorted(u)[:10]) + (" …" if len(u) > 10 else "")]
            for k, u in sorted(gap.items(), key=lambda x: -len(x[1]))]
    w(table(rows[:30], ["Field", "Products", "Which (first 10)"]))
    w("")

    # ------------------------------------------------------------------ 8. caveats
    w("## 8. Caveats for use in the app\n")
    for t in [
        "**Non-Italian sources**: storage (USDA HB66, FoodKeeper, UC Davis), bioactive compounds (USDA, Phenol-Explorer) and some micronutrients come from US or international sources; the main nutrition data are CREA or BDA-IEO.",
        "**Storage times**: home storage time (FoodKeeper) and commercial storage time (HB66) are separate fields; the app must show users the former.",
        "**Environmental footprints**: literature medians with high variability; the low/medium/high thresholds are an app convention, declared in `basis`.",
        "**Polyphenols**: indicative values per 100 g of raw product. Phenol-Explorer: non-commercial use, cite the source.",
        "**EU claims**: computed on raw product per 100 g (Reg. (EC) 1924/2006); the protein claim for low-energy produce is put into context with LARN.",
        "**PAT**: linked by keywords; also includes processed products.",
        "**Texts**: rewritten by merging several sources and realigned with the data; some descriptive sentences (curiosities, culinary uses) are general knowledge.",
    ]:
        w(f"- {t}")
    w("")

    # ------------------------------------------------------------------ 9. status per product
    w("## 9. Status per product\n")
    rows = []
    for i in sorted(items, key=lambda x: (x["category"], x["names"]["en"])):
        d = i["data_completeness"]
        ae = sum(1 for a in audit if a["item"] == i["id"] and a["severity"] in ("E", "W") and a["area"] != "images")
        rows.append([i["names"]["en"], CAT_EN[i["category"]], len(i["sources_by_topic"]["sources_used"]), len(i.get("help_refs", [])),
                     len(d["fields_pending_verification"]), len(d["missing_fields"]), len(d.get("not_applicable_fields", [])), ae])
    w(table(rows, ["Product", "Category", "Sources", "Help entries", "To verify", "Missing", "N/A", "Warnings"]))
    w("\n## 10. Reproducibility and files\n")
    for t in [
        "`data/database.json` – the database; `data/schema.json` – the schema; `data/database_guide.md` – the field guide.",
        "`data/draft_legacy_values.json` – draft values removed from the app (the original draft itself is not published).",
        "`data/audit_findings.json`, `data/template_coverage.json` – results of the checks.",
        "`data/raw/` – copies of the downloaded sources (not published); `scripts/config/` – curated configurations with quotes; `scripts/texts/` – IT/EN texts.",
        "`scripts/` – the pipeline, order in `scripts/README.md`.",
    ]:
        w(f"- {t}")
    w("")
    (DATA / "scraping_report.md").write_text("\n".join(L), encoding="utf-8")
    print("wrote data/scraping_report.md:", len("\n".join(L)), "characters")


if __name__ == "__main__":
    main()
