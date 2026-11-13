# Peak Season – Seasonal Fruit & Vegetable Database

An open, bilingual (Italian/English) database, **built entirely on verifiable sources**, describing **153 fresh products**: when they are in season in Italy and across Europe, how to choose them, how to store them, what they contain and what their environmental footprint is.

It is the single source of truth for the **Peak Season** app ([peak-season-app](https://github.com/NunzioLangiulli/peak-season-app)), but it is designed to be used **without the app as well**: every rule the app applies is written into the database itself.

| | |
|---|---|
| Products | 153 – 72 vegetables, 55 fruits, 10 herbs and spices, 10 mushrooms, 6 fresh cereals/pulses |
| Sources | 46 official and scientific sources, listed in `metadata.official_sources` |
| Seasonality | 3 Italian macro-areas + 6 European climate zones (EUFIC/EEA, 29 countries) |
| Languages | every user-facing text is `{ "it": …, "en": … }` |
| Files | [`data/database.json`](data/database.json) (~10 MB), formal rules in [`data/schema.json`](data/schema.json) |

---

## 1. Rationale: why this database exists

Seasonality information found online is often **contradictory**, copied from one site to another without citing a source, and almost never says *which area* it applies to. The same goes for storage advice and nutritional values.

Peak Season takes the opposite approach: **a limited number of products, but every value traceable back to its source**. When sources disagree, the database does not silently pick one: it says so, explains how the decision was made and keeps the alternative.

## 2. Rules of rigour

These rules apply to every field of the database and were followed throughout the work.

1. **No invented data.** Every value comes from a cited source. If a value does not exist, the field stays `null` and is listed in `data_completeness.missing_fields`: a declared gap is better than a plausible-looking number.
2. **`null` ≠ "not applicable".** A field that makes no sense for a product (e.g. the chilling-injury threshold for produce that is not chill-sensitive, or nutrition data for a truffle) is listed in `data_completeness.not_applicable_fields`, so it can be told apart from a real gap.
3. **The official source wins, but nothing is thrown away.** The project started from a draft of 91 products whose values and links were largely unverified. Every draft value contradicted by an official source was replaced, and the old value was kept as a discrepancy in `data_completeness.notes`. Values that could not be verified were removed from the product record and archived, with the reason, in [`data/draft_legacy_values.json`](data/draft_legacy_values.json).
4. **Conflicts between sources are documented.** Cases where authoritative sources contradict each other (13 types) are described in `metadata.source_conflicts`, together with the rule used to resolve them.
5. **Every record says where it comes from.** Structured blocks carry their source next to the value (`source`, `basis`, `source_food`, `derivation`); all sources of a record are in `sources_by_topic.sources_used`, useful links in `useful_links`.
6. **Estimates are flagged as estimates.** Where a zone has no data, the database holds an estimate copied from the most similar climate zone, kept separate from real data (`seasonality.estimates`), with the method in `metadata.seasonality_estimates_method`. An estimate is never derived from another estimate.
7. **Databases, not scattered literature.** Bioactive compounds, polyphenols and carotenoids come only from official databases (USDA, Phenol-Explorer), never from hand-picked individual papers.
8. **Database first, app second.** Every rule used by the app (state colours, thresholds, calendar order, botanical family names, country codes, claim rules…) is stored in the database under `metadata`. Anyone using the JSON alone has the same information as the app.
9. **Fully bilingual, never mixed.** User-facing texts are `{it, en}`; coded values (`"fridge"`, `"climacteric"`…) are translated through `metadata.vocabulary`. Proper names and registered names (PDO/PGI, varieties) stay in their original language. Internal working notes (`data_completeness.notes`) are in Italian.
10. **Style conventions.** Short labels use Title Case ("In the Fridge", "Non-Climacteric"); sentences and official names do not. User-facing terminology is "product/produce" (IT *prodotto/prodotti*).

### Inclusion rule

A product enters the database if it has **at least 2 seasonality or storage sources** **and** an official nutrition record (CREA or BDA-IEO). Rejected candidates and the reasons are listed in [`data/excluded_candidates_report.md`](data/excluded_candidates_report.md). A few explicit exceptions (e.g. white truffle, which has no official nutrition data) are documented in the record notes.

## 3. How the main data are computed

### Seasonality – voting across sources

For each month and each area a score `s = votes / available sources` is computed:

- vote **1** if the source marks the month as "in season" (WWF, Greenpeace, Altroconsumo, EUFIC-Italy, Orto da Coltivare harvest tables);
- vote **0.5** if the source marks it as "early" or "late".

| Score | State |
|---|---|
| `s ≥ 0.5` | **In Season** |
| `0 < s < 0.5` | **Early Season** if it precedes the season, **End of Season** if it follows it |
| `s = 0` | **Out of Season** |
| inner months of a run of at least 3 months on which **all** sources (at least 2) agree | **Peak Season** |
| exotic fruit with no Italian production | **Not Applicable** |
| no source | `null` (declared gap) |

For European zones the score is the share of the zone's countries (EUFIC, 29 countries, each assigned to its prevailing EEA biogeographical region) that report the product as in season. Zones not covered by EUFIC were completed from national sources: the Alpine zone from the Austrian Ministry of Health calendar, the Mediterranean zone from Southern Italy and the Islands.

For the **Italian macro-areas** (North, Centre, South and Islands; Abruzzo is counted in the Centre) the curve was refined using open-field harvest periods, distinguishing three cases: perishable summer produce, short gaps to be closed, and naturally stored produce, where harvest and availability differ (`seasonality.availability_note`). The full method is in `metadata.seasonality_method` and `metadata.seasonality_curve_method`; the provenance of each curve is in `seasonality.curve_basis`.

### Storage and postharvest

- **Respiration and ethylene**: Kader classes (UC Davis, USDA Agricultural Handbook 66). These drive **perishability** (6 levels, `metadata.perishability_legend`) and the list of products to **keep away from** (`keep_away_from`: strong ethylene producers, for ethylene-sensitive produce).
- **Chilling injury and freezing**: HB66, Tables 1 and 2.
- **Where to store it at home**: UC Davis/Kader guide *Storing Fresh Fruits and Vegetables for Better Taste* + USDA FoodKeeper for home storage times.
- **Compatible storage**: Thompson groups (HB66, Table 1).

### Nutrition

- Composition from **CREA** (2019 tables) and **BDA-IEO**; USDA FoodData Central only for products missing from the Italian databases.
- **% NRV** against the Nutrient Reference Values of Regulation (EU) 1169/2011 (Annex XIII).
- **Nutrition claims** computed with the exact thresholds of Regulation (EC) 1924/2006 (rules in `metadata.nutrition_claims_eu_rules`).
- **Protein**: besides the EU claim, a comparison with the Italian LARN SINU 2014 reference intakes. If 100 g covers less than 10% of the requirement, the claim stays (it is legal) but comes with a note putting it into context.
- **Allergens** (Regulation (EU) 1169/2011, Annex II) and standard **portions** (LARN / IEO SmartFood).

### Sustainability

Carbon footprint (kg CO₂eq/kg) and water footprint (L/kg) from the **SU-EATABLE LIFE** database (Petersson et al. 2021, CC BY 4.0), with AGRIBALYSE 3.1 for culinary herbs. The Low/Medium/High thresholds are a **declared project convention** (`metadata.environmental_footprint_method.levels`), not a value taken from the sources.

### Varieties, territories and botany

- **PDO and PGI** (DOP/IGP) verified against the EU eAmbrosia register.
- **Varieties** verified across several text sources and the EU Common Catalogue of varieties; UPOV species codes and the number of varieties registered in Italy.
- **Traditional Agri-food Products (PAT)**: MASAF list (26th revision, 2026); Slow Food Presidia and Ark of Taste.
- **Botany**: scientific name and family verified on EPPO, World Flora Online and GBIF (mushrooms).

### Images

Up to 5 view types per product (main photo, neutral background, plant in the field, botanical plate, cross-section). Only freely licensed photos are accepted (Wikimedia Commons, USDA ARS, Unsplash, Pixabay, iNaturalist CC0/CC BY/CC BY-SA), landscape and at least 1000 px wide, with no dishes or text, hand-picked from at least 2 candidates per type. Author, licence and source page of every photo are in [`assets/images/_metadata.json`](assets/images/_metadata.json). The image files are not in this repository: optimised versions are in the app repository.

## 4. Record structure

Every product follows the same block structure (a full block-by-block example on the tomato is in [`data/database_guide.md`](data/database_guide.md)):

| Block | Content |
|---|---|
| `id`, `names`, `category` | `italianname_englishname` identifier, IT/EN names and synonyms, category |
| `botany` | scientific name, family, plant part used, classification |
| `italian_varieties_and_territories` | verified varieties, PDO/PGI, PAT, Slow Food |
| `images` | photos with view type, author and licence |
| `seasonality` | month-by-month states for Italian macro-areas and EUFIC zones, estimates kept separate |
| `agricultural_calendar_italy` | sowing, transplanting and harvest for North/Centre/South |
| `buying_guide` | how to choose it |
| `ripening_and_storage` | climacteric behaviour, ethylene, temperatures, storage times, where to store it |
| `nutrition_and_sustainability` | composition per 100 g, NRV, claims, bioactive compounds, allergens, footprints |
| `sources_by_topic` | sources by topic and useful links |
| `data_completeness` | gaps, non-applicable fields, discrepancies with the draft, working notes |
| `help_refs` | glossary links for the "?" help icons |

The `metadata` block contains legends, methods, the glossary (44 entries), the vocabulary of coded values, field help texts, the source catalogue and the display rules used by the app.

**Shared corpus.** Descriptions repeated across several products are stored once in `shared_descriptions_corpus`, and records point to them with `{ "corpus_ref": …, "specific_addition": … }`. When reading the JSON directly, replace the reference with the corpus text (done by `scripts/common.py → load_json`).

## 5. Repository contents

```
data/
  database.json              the database
  schema.json                JSON Schema (types, allowed values, required fields)
  database_guide.md          block-by-block guide to the database
  scraping_report.md         reliability and gap report
  audit_findings.json        results of the item-by-item re-check
  seasonality_audit.json     check of the seasonal curves
  template_coverage.json     coverage of the original template fields
  items_index.json           exact codes and URLs of every product on every source
  draft_legacy_values.json   unverifiable values from the initial draft, with the reason
  merged_items_archive.json  products merged into others
  excluded_candidates_report.md  candidate products that were not admitted
  ui_copy.json, ui_config.json   app interface texts and icons
scripts/                     Python pipeline that builds and checks the database
  config/                    tables hand-curated from the sources, with quotes and page numbers
  texts/                     IT/EN descriptive texts
  README.md                  pipeline execution order (reference document)
admin_studio/                local dashboard to edit texts, images, icons and sources
assets/images/_metadata.json photo credits and licences
```

## 6. The pipeline

The database is not written by hand: it is produced by about 90 Python scripts, each with a single job and a docstring describing the sources it uses. The execution order is in [`scripts/README.md`](scripts/README.md). In short:

1. **Sources and index** – download and caching of sources, master list of products with their codes on every source.
2. **Enrichment** – nutrition, seasonality, botany, varieties, storage, compounds, allergens, sustainability, texts, images.
3. **Localisation and help** – bilingual texts, vocabulary, glossary, source catalogue, rules for the app.
4. **Checks** – JSON Schema validation (`validate_db.py`), item-by-item re-check (`audit_db.py`), template coverage (`template_coverage.py`), final reports.

Manual edits (texts, photos, icons, links) go through the **Admin Studio** ([`admin_studio/README.md`](admin_studio/README.md)), which validates the database on every save and rolls the change back if validation fails.

### Requirements

- Python 3.10+
- `python -m pip install -r admin_studio/requirements.txt` (Pillow, jsonschema, requests)
- Re-running the download scripts requires your own API keys (EPPO, Unsplash, Pixabay) in a `.env` file, which is not included.

### What is not included

To respect licences and keep the repository light, the following are not published: raw data downloaded from the sources (`data/raw/`), the original source PDFs and logos (`fonti_locali/`), high-resolution photos and the initial draft. The database still contains every extracted value and the references needed to find it again.

## 7. Using the database

```python
import json
db = json.load(open("data/database.json", encoding="utf-8"))
corpus = db.get("shared_descriptions_corpus", {})

tomato = next(i for i in db["items"] if i["id"] == "pomodoro_tomato")
print(tomato["names"]["en"], tomato["seasonality"].keys())
```

To get texts already expanded from the shared corpus:

```python
import sys; sys.path.insert(0, "scripts")
from common import load_json
db = load_json("data/database.json")
```

### Versioning

`metadata.version` is the GitHub release tag of this repository (current release: **v1.1.0**, `metadata.generated` = release date). It follows semantic versioning:
- **patch** (1.1.x): fixes to texts or data;
- **minor** (1.x.0): new fields or new content;
- **major** (x.0.0): breaking changes to the format.

`metadata.schema_version` describes the JSON format and changes independently of the data release. The version is set in `scripts/build_app_support_metadata.py` (`DB_VERSION`, `DB_RELEASE_DATE`), so pipeline reruns keep it.

## 8. Sources

The full list of the 46 sources, with URL, topics, access method and licence notes, is in `metadata.official_sources`; the description and authority of each one are in the database's source catalogue. The main ones:

- **Nutrition:** CREA Alimenti e Nutrizione, BDA-IEO, USDA FoodData Central, LARN SINU 2014, Regulation (EC) 1924/2006 and Regulation (EU) 1169/2011
- **Seasonality:** EUFIC, WWF Italia, Greenpeace Italia, Altroconsumo, Orto da Coltivare, Bio Suisse, Gesundheitsportal (AT), EEA
- **Storage:** UC Davis Postharvest Center, USDA Agricultural Handbook 66, USDA FoodKeeper
- **Varieties and territories:** eAmbrosia (EU), EU Plant Variety Portal, UPOV, MASAF (PAT), Slow Food Foundation
- **Botany:** EPPO, World Flora Online, GBIF
- **Compounds and environment:** USDA Flavonoid Database 3.3, Phenol-Explorer 3.6, SU-EATABLE LIFE, AGRIBALYSE 3.1

## 9. Licence (open source)

- **Code** (`scripts/`, `admin_studio/`): [MIT](LICENSE).
- **Database and documentation** (`data/`): [Creative Commons Attribution 4.0 (CC BY 4.0)](data/LICENSE-CC-BY-4.0.txt). You may freely reuse and adapt them, including in other projects, crediting *Peak Season – Nunzio Langiulli* and the original sources.
- **Third-party data:** the CC BY licence covers the project's original work, that is structure, selection, rules, computations and texts. Individual values taken from the sources remain subject to each source's terms, listed in `metadata.official_sources`. In particular, Phenol-Explorer data are free for non-commercial use only, and each photo carries the licence stated in `assets/images/_metadata.json`.

The project is **non-commercial**.

---

*This information is for general educational purposes and is not a substitute for advice from a doctor or nutritionist.*
