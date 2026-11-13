# Peak Season – Phase 1 report: building, organising and validating the database

Generated on 2026-11-13 by `scripts/make_report.py` · database v2.0.0 · 153 products · schema `data/schema.json` (JSON Schema 2020-12).

This report explains the method used to build the database, how it is organised (records, metadata, sources, glossary, bilingualism) and how it was checked. The field-by-field guide is in `data/database_guide.md`.

## 1. Summary

| Item | Value | Notes |
|---|---|---|
| Products | 153 | Vegetables 72, Fruit 55, Herbs and spices 10, Mushrooms 10, Cereals 6 |
| Catalogued sources | 46 | each with description, authority, contents and uses (§4) |
| Sources used per product | average 21.0 | `sources_by_topic.sources_used` |
| Documented source conflicts | 13 | with decision and rationale (§5) |
| Glossary entries ("?" icons) | 44 | 35 linked fields, 684 references in products |
| Bilingual {it, en} texts | 7318 | everything the user reads exists in Italian and English (§3.4) |
| Schema validation | 0 data errors | only image-file warnings remain (0) |
| Systematic re-check (data) | 1 errors, 9 to review, 23 informational | all explained (§6.3) |
| Values still to verify | 655 | almost all agricultural calendars of fruit, herbs and cereals (§7) |
| Fields without data | 2785 | real gaps, mapped in §7 |
| Non-applicable fields, with reason | 1855 | e.g. chilling injury for produce that is not sensitive |

## 2. How it was built

### 2.1 Principles

- **No invented data.** Every value comes from a catalogued source, given in the `source` field or in the `sources_by_topic` block; where no source exists the field stays empty (null) and is listed in `data_completeness.missing_fields`.
- **Official and scientific sources first**, with a declared priority order per topic (e.g. nutrition: CREA → BDA-IEO → USDA FoodData Central).
- **Per-value traceability**: for nutrients the source is given value by value; for postharvest data the HB66 chapter or table; for footprints the number of studies and the range.
- **Declared approximations**: if a source lacks the exact entry the closest one is used and flagged as approximate; estimates (e.g. respiration class from Q10) are flagged as estimated and explained in the `basis` field.
- **Not applicable ≠ missing**: a field that by definition does not apply (e.g. chilling injury for produce that does not suffer from it) is marked N/A with a reason and not counted as a gap.
- **The initial draft as a starting point, not as a source**: its 91 products were migrated into the structure; every value differing from the sources is recorded as a discrepancy, every unverifiable value is removed from the app and preserved in `data/draft_legacy_values.json` (1092 values).

### 2.2 Pipeline

The database is produced by Python scripts run in a fixed order (`scripts/README.md`). Every script has a docstring with source, method and usage.

| Phase | What it does |
|---|---|
| 1. Sources and index | downloads and caches the sources (`data/raw/`), builds the master list with each source's codes, migrates the draft |
| 2. Nutrition | CREA and BDA-IEO, USDA for missing items, recomputed %NRV and EU claims, LARN reference for protein |
| 3. Seasonality and botany | vote across Italian calendars, EUFIC map and EUFIC national sources; EPPO, WFO, GBIF; growing notes |
| 4. Varieties and territories | variety checks on texts, Slow Food and the EU Common Catalogue; PDO/PGI on eAmbrosia; UPOV codes; MASAF PAT |
| 5. Storage | USDA HB66 (tables and chapters), Kader classes, FoodKeeper and UC Davis home guide, compatibility groups |
| 6. Compounds, allergens, sustainability | USDA carotenoids and flavonoids, Phenol-Explorer, Reg. (EU) 1169/2011, LARN portions, SU-EATABLE LIFE, AGRIBALYSE |
| 7. Texts, images, sources | IT/EN texts realigned with the data, licensed images, per-product source register |
| 8. Bilingualism and help | `localize_fields.py` (last transformation step), `build_help.py` (vocabulary, glossary), `build_source_catalog.py` (source catalogue and conflicts) |
| 9. Checks and reports | JSON Schema validation, item-by-item re-check, template coverage, reports |

Choices that require judgement (quotes from HB66 chapters, mappings between entries of different sources, source descriptions, glossary, conflicts) live in hand-curated configuration files in `scripts/config/`, each with the quote or page of the source: every decision can be read and changed without touching the code.

## 3. How it is organised

`data/database.json` has two parts: `metadata` (everything that applies to the whole database) and `items` (one record per product).

### 3.1 A product record

| Block | Content |
|---|---|
| `id, names, category` | identity: stable id, IT/EN names (common, alternative), category |
| `botany` | scientific name, family, genus, EPPO/GBIF/UPOV codes, plant part used |
| `italian_varieties_and_territories` | verified varieties (EU Common Catalogue, Slow Food, texts), PDO/PGI (eAmbrosia), PAT (MASAF), varieties registered in Italy |
| `images` | gallery with author, licence and source URL for every photo |
| `seasonality` | month-by-month state for 3 Italian macro-areas and 6 European climate zones, with zone-by-zone provenance |
| `agricultural_calendar_italy` | sowing, transplanting, harvest by macro-area; growing parameters |
| `buying_guide` | how to choose it, signs of quality and spoilage |
| `ripening_and_storage` | climacteric/non-climacteric, ethylene, respiration and perishability, chilling injury, commercial and home storage, compatibility |
| `nutrition_and_sustainability` | values per 100 g with a source per value, %NRV, EU claims, bioactive compounds, allergens, LARN portions, carbon and water footprint |
| `sources_by_topic` | sources used by topic and useful links |
| `data_completeness` | missing fields, fields to verify, non-applicable fields, discrepancies with the draft, notes |
| `help_refs` | glossary entries relevant to that product ("?" icons) |

### 3.2 Metadata

| Field | Content |
|---|---|
| `official_sources` | source catalogue: what it is, why it is authoritative, what it offers, for which topics and products it was consulted |
| `source_conflicts` | general cases of disagreement between sources: why, what was decided and why |
| `glossary` | short but complete explanations of concepts, with sources, for the "?" icons |
| `vocabulary` | IT/EN labels of every coded value (e.g. `climaterico` → "Climaterico" / "Climacteric"), with the glossary link |
| `field_help` | which glossary entry explains each field |
| legends and methods | seasonal states, EUFIC zones, macro-areas, seasonality method, postharvest, perishability, storage, footprints |
| `sustainable_diet_summary` | EUFIC summary on sustainable diets |

### 3.3 The help system ("?" icons)

An explanation is written once, in the glossary, and reached from several places:

- **from the field**: `metadata.field_help` links 35 field paths (e.g. `ripening_and_storage.ripening_type`) to the entries that explain them;
- **from the value**: every value of `metadata.vocabulary` (24 groups) can point to an entry (e.g. `climaterico` → entry *climacteric*);
- **from the product**: `item.help_refs` lists the entries relevant to that product and the fields where they are shown, computed from the content (allergens, gluten, PDO, PAT, favism for broad beans, Q10 estimates, greenhouse growing…);
- **from one entry to another**: `see_also`; and **from the source**: `official_sources[].used_for.glossary_entries`.

Every entry has `term`, `short` (one line for the tooltip) and `text` (full explanation) in IT and EN, and its sources with name and URL resolved from the catalogue. The app therefore holds no help texts of its own: it reads everything from the database.

Entries: *Climacteric Fruit*, *Non-climacteric Produce*, *Ethylene*, *Ethylene Production*, *Ethylene Sensitivity*, *Keep It Away from*, *Respiration and Kader Class*, *Perishability*, *Q10 (Respiration Estimate)*, *Chilling Injury*, *Lowest Safe Temperature*, *Freezing Point*, *Freezing Susceptibility*, *Optimal (Commercial) Conditions*, *Home Storage Time*, *Where to Store It at Home*, *Produce to Store Together*, *Seasonality States*, *Italian Macro-areas*, *European Climate Zones*, *Estimate from Neighbouring Zone (≈)*, *Sowing, Transplanting and Harvest*, *Growing Parameters*, *Edible Portion*, *NRV (Nutrient Reference Values)*, *EU Nutrition Claims*, *LARN (Italian Reference Intakes)*, *Reference Portion*, *Allergens (EU Reg. 1169/2011)*, *Gluten*, *Carotenoids*, *Polyphenols*, *Flavonoids*, *Carbon Footprint*, *Water Footprint*, *Heated Greenhouses and Seasonality*, *PDO and PGI*, *Traditional Agri-food Products (PAT)*, *Slow Food Presidia and Ark of Taste*, *UPOV Code and EU Common Catalogue*, *Verified Varieties*, *Scientific Name and Botanical Codes*, *Favism*, *Exact or Approximate*.

### 3.4 Bilingualism

The app must work entirely in Italian or entirely in English. Conventions applied and checked by the audit:

- every user-facing text is an `{it, en}` object: names, texts, labels, advice, legends, glossary, source descriptions, rationales (`basis`, `derivation`, `method`, variety notes);
- coded values (category, seasonal state, classes, storage locations…) are stable keys translated through `metadata.vocabulary`, never shown as they are;
- nutrients and compounds keep `name`/`name_en` pairs;
- only proper names stay in their original language: varieties, PDO/PGI, PAT, scientific names, authors, licences, source names, verbatim quotes from sources;
- `data_completeness.notes` is an internal technical log in Italian, not used by the app.

## 4. Sources

The full catalogue, with description, authority, contents and the list of every product for which each source was consulted, sits at the top of the database (`metadata.official_sources`) and is reproduced in the guide. Summary:

| Source | Products | Used for |
|---|---|---|
| Regolamento (UE) n. 1169/2011 - Allegato XIII, Valori Nutritivi di Riferime | 153 | Allergens, %NRV |
| IEO SmartFood - Porzioni e frequenze (porzioni standard LARN-SINU) | 153 | Portions |
| EPPO Global Database | 151 | Botany |
| Regolamento (CE) n. 1924/2006 - indicazioni nutrizionali e sulla salute | 146 | EU Claims |
| LARN - SINU (tabelle riassuntive, PDF locale) | 145 | LARN |
| World Flora Online - Plant List | 143 | Botany |
| USDA FoodData Central - SR Legacy (2018-04) | 136 | Bioactive Compounds, Nutrition, Texts |
| USDA ARS Agricultural Handbook 66 (2016) | 133 | Chilling Injury, Freezing_susceptibility, Plant_part_used, Postharvest, Compatib |
| SU-EATABLE LIFE - database delle impronte di carbonio e idrica (Petersson e | 129 | Environmental Footprint |
| Wikimedia Commons API | 124 | Images |
| Pixabay API | 124 | Images |
| BDA-IEO - Banca Dati di Composizione degli Alimenti (Istituto Europeo di On | 121 | Nutrition, Texts |
| USDA FSIS FoodKeeper | 120 | Home Storage, Texts |
| MASAF - Elenco nazionale dei Prodotti Agroalimentari Tradizionali, XXVI rev | 118 | Texts, Traditional Products |
| EUFIC - Explore seasonal fruit and vegetables in Europe | 115 | European Seasonality, Texts |
| Orto da Coltivare (Matteo Cereda) - tabelle di semina PDF + schede | 110 | Growing Calendar, Plant_part_used, Seasonality, Texts, Varieties |
| CREA Alimenti e Nutrizione - Tabelle di composizione degli alimenti (rev. 2 | 109 | Nutrition, Texts |
| My-PersonalTrainer | 109 | Plant_part_used, Varieties, Verification_texts |
| UC Davis / Kader - Storing Fresh Fruits and Vegetables for Better Taste (UC | 107 | Home Storage |
| USDA Database for the Flavonoid Content of Selected Foods, Release 3.3 (201 | 97 | Bioactive Compounds |
| Phenol-Explorer 3.6 - database del contenuto di polifenoli negli alimenti ( | 86 | Bioactive Compounds |
| UC Davis Postharvest Research and Extension Center - Produce Fact Sheets | 80 | Postharvest, Texts |
| EU Plant Variety Portal - Catalogo comune UE delle varieta' (agricole, orti | 76 | UPOV Code, Varieties |
| Bio Suisse - Calendario stagionale (Svizzera, PDF locale) | 71 | Seasonality, Texts |
| Altroconsumo - Calendario frutta e verdura | 65 | Buying_guide, Plant_part_used, Seasonality, Texts, Varieties |
| Unsplash API | 63 | Images |
| WWF Italia - Il calendario della frutta e verdura di stagione (PDF locale) | 60 | Seasonality, Texts |
| Greenpeace Italia - Guida alla frutta e verdura di stagione (PDF locale) | 54 | Seasonality, Texts |
| eAmbrosia - registro UE delle indicazioni geografiche | 48 | PDO/PGI |
| Fondazione Slow Food per la Biodiversità - Presìdi e Arca del Gusto | 34 | Seasonality, Varieties |
| GBIF Backbone Taxonomy (funghi) | 10 | Botany |
| AGRIBALYSE 3.1 (ADEME, Francia) - impatti ambientali degli alimenti | 7 | Environmental Footprint |
| Provincia di Cuneo - Schede dei funghi commestibili | 3 | Seasonality |
| Gesundheitsportal Österreichs - Saisonkalender (Ministero della salute aust | 2 | European Seasonality |
| Legge 16 dicembre 1985, n. 752 - Normativa quadro sui tartufi (art. 6, peri | 2 | Seasonality |
| iNaturalist (solo foto CC0 / CC BY / CC BY-SA) | 1 | Images |
| Istituto Superiore di Sanità - Rapporti ISTISAN 09/47 (carenza di G6PD e fa | 1 | Health Notes |
| Regione Emilia-Romagna, BUR 2012 - Disciplinare IGP Amarene Brusche di Mode | 1 | Seasonality |
| Biblioteca civica Bertoliana (Vicenza) - Scheda botanica del lampascione | 1 | Seasonality |
| NaturaSì - Frutta e verdura di stagione (schede prodotto) | 1 | Seasonality |
| ISMEA Mercati | 0 |  |
| Servizi agricoli regionali (Veneto Agricoltura, ERSA FVG, ARSIAL) | 0 |  |
| EUFIC - European national sources on seasonal fruit and vegetables | whole database |  |
| EUFIC - Are seasonal fruit and vegetables better for the environment? | whole database |  |
| USDA ARS Image Gallery | 0 |  |
| EEA - Biogeographical regions, Europe 2016 (Agenzia europea dell'ambiente) | whole database |  |

Sources assessed but not used: ISMEA and regional calendars for fruit harvest periods (no structured data by macro-area); USDA ARS Image Gallery (few relevant images); MAPA calendar (Spain), cited by EUFIC but unreachable (404 pages). My-PersonalTrainer is used only for texts and links, never for numeric values.

## 5. Conflicts between sources and decisions

The cases are in `metadata.source_conflicts` (IT/EN). In short:

- **Many values in the initial draft did not match the official sources.** The draft had been compiled without specific references and mixed different sources and contexts. → *Decision:* The official source always prevails. The draft value is recorded as a discrepancy in the record and, if unverifiable, removed from the app but kept separately. *Why:* No invented data and no information lost.
- **CREA, BDA-IEO and USDA give different values for the same product.** Different samples, varieties, countries and methods (e.g. 'available' carbohydrates in Europe and 'by difference' in the USA). → *Decision:* Order of priority: CREA, then BDA-IEO (also to fill missing nutrients), USDA only when the first two are missing. The source is given for every value. *Why:* Italian tables describe the products sold in Italy.
- **Italian calendars do not always agree on in-season months.** They consider different areas, varieties and growing methods (open field, greenhouse). → *Decision:* For each month and macro-area the sources listing it are counted: with at least half of the votes the month is in season, with fewer it is early or end of season; the peak is the central months of a period of at least three months on which all sources agree. *Why:* Voting reduces the weight of any single source and the same rule applies to every product.
- **EUFIC gives data by country, not by climate zone, and does not list every product.** Each country has its own national source and countries span several zones. → *Decision:* Each country is assigned to its main zone; missing zones are filled with national sources listed by EUFIC or, for the Mediterranean zone, with Southern Italian seasonality. The origin is given zone by zone. *Why:* A declared approximation, useful for people using the app outside Italy.
- **Some produce (truffles, Caesar's mushroom, nectarine) are missing from Italian seasonal calendars.** Calendars cover cultivated produce and do not separate forms of the same species (peach and nectarine). → *Decision:* The most authoritative source available for that product is used: the harvest-period law for truffles, an institutional mushroom sheet for Caesar's mushroom, peach seasonality for nectarine. The source is stated in seasonality.italy_source or in the notes. *Why:* A declared, product-specific source is better than a gap.
- **For cucumber, eggplant, peppers and citrus FoodKeeper says fridge, the UC Davis guide room temperature.** FoodKeeper focuses on safety and storage time, the UC Davis guide on taste: these products are chilling-sensitive and lose quality in the fridge. → *Decision:* The 'where' follows the UC Davis guide, durations follow FoodKeeper; the short label gives both options and the choice is explained in the record. *Why:* For a seasonality app keeping the flavour matters, without hiding the alternative.
- **HB66 storage times (weeks or months) are much longer than FoodKeeper's (days).** HB66 refers to commercial cold stores at optimal temperature and humidity; FoodKeeper to a home fridge. → *Decision:* They are two separate fields: home and commercial storage time. A commercial time is never used as a home time. *Why:* It avoids unrealistic promises to the user.
- **Chilling threshold and freezing point are often given as ranges.** They depend on variety, ripeness and dissolved sugars. → *Decision:* The highest end (the most cautious) is used and the range is kept when available. If damage occurs within a band (stone fruit 2-8 °C) no single threshold is given. *Why:* Cautious advice does not damage the produce.
- **HB66's summary table contains some typos (e.g. 1310 for radicchio) and many products are not measured at 5 °C.** PDF layout errors; chilling-sensitive products are not studied at low temperatures. → *Decision:* Order: Kader table class, then chapter values, then an estimate at 5 °C with HB66 Q10 values (marked as estimated). Clearly wrong values are not used. *Why:* Use the reference author's classification first.
- **Environmental footprints vary widely between studies and databases.** Different methods, countries, yields and system boundaries (field to farm gate, or up to consumption). → *Decision:* SU-EATABLE LIFE (harmonised median) is used with the number of studies and range; AGRIBALYSE only for the missing herbs, with its boundaries stated. *Why:* Values comparable between produce and transparent uncertainty.
- **Some texts written by merging several sources quoted durations or nutrients different from the structured data.** The texts drew on Italian popular sources, the data come from official databases. → *Decision:* Structured data prevail: storage labels and 'rich in / source of' lists were realigned with the data and EU claims. *Why:* The app must not say two different things about the same product.
- **For some produce a source has no exact entry.** International databases do not cover every Italian speciality (e.g. cutting chicory, turnip tops, corn salad). → *Decision:* The closest entry is used, always marked 'approximate' and stated in the record. *Why:* A declared approximate value is more useful than a gap, provided it is transparent.
- **A variety's common name may differ from its registered name.** Registers use the official denomination (e.g. 'Spadona' for Spadonino, 'Detroit 2' for Detroit). → *Decision:* The common name is shown and the registered name is given with the country of registration. *Why:* Readability for the user and verifiability on the register.

Individual product-level cases remain recorded in `data_completeness.discrepancies` (1359 discrepancies between the draft and the sources) and in the `basis` and `note` fields.

## 6. How it was validated

Four levels of checks, all re-runnable.

### 6.1 Schema

`validate_db.py` checks the database against `data/schema.json` (types, required fields, allowed values, month and bilingual-text formats) plus some consistency checks (ids, water+macronutrient sum, image files present). Result: no data errors; the only remaining warnings concern image files.

### 6.2 Cross-checks against the sources

- **Botany**: scientific name compared across EPPO, WFO and GBIF; genus consistent with scientific name and UPOV code.
- **Varieties**: shown only if found in a source (source texts, Slow Food, EU Common Catalogue, with registered name and country).
- **PDO/PGI**: every designation checked on the EU eAmbrosia register (status and category).
- **Nutrition**: energy recomputed from macronutrients, %NRV and EU claims recomputed from the values, salt = sodium × 2.5.
- **Postharvest**: HB66 chapter values transcribed with their quote in `scripts/config/hb66_chapter_curated.json`; obvious typos in the summary table excluded.

### 6.3 Systematic item-by-item re-check

`audit_db.py` checks every record: consistency of energy/macronutrients, %NRV, EU claims, portions and per-portion footprints; seasonal states and months; harvest versus seasonality; min ≤ max ranges; chilling-injury thresholds and freezing points; home storage times versus commercial ones; storage location versus text labels; ethylene (producers, "keep away from"); respiration class versus perishability; compatibility group versus temperatures; botany; varieties; PDO/PGI; images and licences; source URLs; completeness of IT/EN texts and no Italian text in English fields. It also checks the metadata: every glossary entry bilingual and with registered sources, `see_also`, `field_help` and `help_refs` pointing to existing entries, every coded value present in the vocabulary, every source described.

Remaining data warnings (explained, not errors):

| Level | Product | Field | Detail |
|---|---|---|---|
| E | cavolo_nero_black_kale | macros_per_100g.sugars_g | sugars 0.99 > carbohydrates 0.3 |
| W | cipolla_invernale_winter_onion | storage_compatibility | group 3 (13-18 °C) but optimal temperature {'min': 0.0, 'max': 0.0} |
| W | fagiolino_green_bean | chilling_injury | optimal temperature {'min': 5.0, 'max': 7.5} below the injury threshold 7 °C |
| W | pastinaca_parsnip | italy_macro_areas.sud_isole | always out of season |
| W | melone_melon | storage_compatibility | group 1B at 0-2 °C but chill-sensitive below 5 °C |
| W | lampone_raspberry | ripening_type | non-climacteric but a strong ethylene producer |
| W | avocado_avocado | storage_compatibility | group 1B at 0-2 °C but chill-sensitive below 13 °C |
| W | orzo_barley | macros_per_100g | water+macros = 105.8 g/100 g |
| W | maracuja_passion_fruit | chilling_injury | optimal temperature {'min': 7.0, 'max': 10.0} below the injury threshold 10 °C |
| W | oliva_olive | chilling_injury | optimal temperature {'min': 5.0, 'max': 7.5} below the injury threshold 7 °C |

Explanation: in cavolo nero sugars > carbohydrates because of how USDA computes carbohydrates (by difference) → noted; barley slightly exceeds 105 g/100 g when summing water and macronutrients because of rounding in the CREA table; the "below optimal temperature" thresholds come from the end of HB66's lowest safe range; dry onion in group 3 and melon/avocado in group 1B are as in the HB66 compatibility table (groups for 7-day mixed storage, not optimal temperatures); the differences between labels and FoodKeeper for chilli pepper, banana and pomegranate are intentional (UC Davis guide, optimised for taste).

### 6.4 Template coverage and reproducibility

`template_coverage.py` checks, for each of the 62 fields of the original JSON template, how many products have verified data: 16 fields are complete for all 153 products (details in `data/template_coverage.json`). Finally, the last part of the pipeline was re-run from an earlier snapshot: the result matches the delivered database (the re-run also revealed and fixed an ordering dependency in the source register).

## 7. Recovered data and remaining gaps

Data recovered in the last phase, from the proposed sources:

- **Freezing point** (HB66's "highest freezing point", the highest temperature at which ice starts to form; for a range the upper, most cautious end is used): 44 products. The others have no value in their HB66 chapter.
- **Respiration class**: 130 products; 0 estimated at 5 °C from values measured at higher temperatures using HB66 Q10 values, flagged as estimated. Still without a class: cardoon, pumpkin, chestnut, rosemary, quince (no measured value).
- **Carbon footprint of culinary herbs**: 7 from AGRIBALYSE 3.1 (ADEME), with declared system boundaries (up to consumption, so not directly comparable with SU-EATABLE LIFE). Water footprint not taken from AGRIBALYSE, because it measures scarcity, not volume.
- **Italian seasonality for products missing from the calendars**: nectarine from peach (the calendars do not separate them; confirmed by the "Pesca e Nettarina di Romagna" PGI and EUFIC); black and white truffle from Law 752/1985, art. 6 (harvest periods); Caesar's mushroom from the Province of Cuneo mushroom sheet ("summer and early autumn"). Source in `seasonality.italy_source`.
- **Scope decisions (5 November)**: chard and leaf beet merged into "Chard" (same species and same CREA record); flat peach (pesca tabacchiera) added as a peach variety (Slow Food Ark of Taste); white truffle added as an exception to the inclusion rule (no CREA/BDA record: nutrition empty and declared). After the systematic review of excluded candidates (`data/excluded_candidates_report.md`) 44 products were added (all except bergamot, caper, sorrel, strawberry tree and purslane) even with incomplete fields: they were built with the same pipeline on a test database and then merged; where official data are missing the field stays empty and declared. For 33 of them Italian seasonality comes from specific sources read by hand (`config/italy_seasonality_curated.json`): Orto da Coltivare harvest periods, Slow Food sheets, Province of Cuneo mushroom sheets, the sour cherry PGI specification; snow pea and mirabelle reuse pea and plum (same species). For 4 of them nutrition comes from a USDA entry of a related product, declared as an approximation.
- **Estimates for zones without data** (decision of 6 November): many EUFIC zones are missing (the Pannonian zone covers Hungary only). `seasonality.estimates` holds, separate from the data, estimates from the neighbouring zone with the most similar climate (e.g. Pannonian <- Continental), marked with ≈ in the app and switchable off in Settings; an estimate always starts from real data. For exotic fruit, zones without data are "Not grown here". Method in `metadata.seasonality_estimates_method`.
- **European climate zones**: Alpine zone from the Austrian Ministry of Health calendar, the national source cited by EUFIC (2 products); Mediterranean zone explicitly derived from South and Islands seasonality (23 products). Provenance in `seasonality.eufic_zone_sources`.

Not recoverable from accessible sources (documented gaps):

- **Agricultural calendars of fruit, herbs and cereals by macro-area**: neither ISMEA nor regional services publish structured data for North/Centre/South; the draft values remain "to verify".
- **Local varieties (Law 194/2015)**: there is no downloadable national list, only heterogeneous regional registers.
- **Missing Atlantic, Continental, Boreal and Pannonian zones**: they mostly concern products not grown there (citrus, persimmon, loquat, prickly pear); they stay empty.
- **Agronomic parameters of herbs and mushrooms (CREA-OF)**: not attempted in this phase.
- **Wild mushrooms and truffles**: no environmental footprint (wild harvest, no LCA study).

Gap map (fields without data):

| Field | Products | Which (first 10) |
|---|---|---|
| `ripening_and_storage.postharvest_physiology.freezing_point_c` | 99 | aglio, agretti, alchechengi, amarena, ananas, anguria, asparago, asparago, avocado, banana … |
| `seasonality.eufic_climatic_zones.pannonian` | 97 | agretti, alchechengi, amarena, ananas, anguria, arachide, arancia, asparago, avena, avocado … |
| `ripening_and_storage.postharvest_physiology.freezing_susceptibility` | 95 | aglio, agretti, alchechengi, amarena, ananas, anguria, asparago, basilico, bietola, broccolo … |
| `agricultural_calendar_italy.centro` | 93 | agretti, albicocca, alchechengi, amarena, arancia, asparago, avena, broccolo, cachi, cardoncello … |
| `agricultural_calendar_italy.sud_isole` | 93 | agretti, albicocca, alchechengi, amarena, arancia, asparago, avena, broccolo, cachi, cardoncello … |
| `agricultural_calendar_italy.nord` | 92 | agretti, albicocca, alchechengi, amarena, arancia, asparago, avena, broccolo, cachi, cardoncello … |
| `seasonality.eufic_climatic_zones.mountain` | 76 | agretti, alchechengi, amarena, ananas, arachide, arancia, asparago, avena, avocado, banana … |
| `ripening_and_storage.postharvest_physiology.estimated_shelf_life_days` | 75 | agretti, alchechengi, amarena, arachide, avena, banana, basilico, bietola, cachi, cardo … |
| `seasonality.eufic_climatic_zones.boreal` | 73 | agretti, alchechengi, amarena, ananas, arachide, asparago, avena, banana, basilico, bietola … |
| `agricultural_calendar_italy.cultivation_notes` | 72 | albicocca, amarena, arancia, asparago, avena, broccolo, cachi, cardoncello, carruba, castagna … |
| `italian_varieties_and_territories.notable_varieties` | 69 | agretti, alchechengi, amarena, ananas, arachide, asparago, avena, broccolo, cardoncello, carruba … |
| `seasonality.eufic_climatic_zones.atlantic` | 64 | agretti, alchechengi, amarena, arachide, asparago, avena, basilico, broccolo, cachi, cardo … |
| `agricultural_calendar_italy.agronomic_params` | 63 | agretti, alchechengi, amarena, asparago, broccolo, cardoncello, carruba, cavolo, cavolo, cedro … |
| `seasonality.eufic_climatic_zones.continental` | 59 | agretti, alchechengi, amarena, ananas, arachide, asparago, avena, avocado, banana, basilico … |
| `seasonality.eufic_climatic_zones.mediterranean` | 49 | agretti, amarena, arachide, asparago, avena, cardoncello, cece, cedro, chinotto, cicerchia … |
| `seasonality.italy_national` | 45 | arachide, avena, basilico, cardo, cardoncello, cavolo, cavolo, cece, cicoria, cicoria … |
| `botany.upov_note` | 44 | agretti, alchechengi, amarena, asparago, broccolo, cardoncello, carruba, cavolo, cedro, chinotto … |
| `ripening_and_storage.ethylene_compatibility.sensitive_to_ethylene` | 37 | agretti, alchechengi, ananas, carruba, cavolo, chinotto, cicerchia, cocco, crescione, erba … |
| `ripening_and_storage.postharvest_physiology.chilling_injury` | 31 | agretti, albicocca, alchechengi, asparago, cardo, carruba, castagna, cavolo, cicerchia, clementine … |
| `ripening_and_storage.ethylene_compatibility.ethylene_production_class` | 23 | agretti, alchechengi, cardo, carruba, castagna, cavolo, chinotto, cicerchia, cima, gelso … |
| `nutrition_and_sustainability.edible_portion_percentage` | 23 | alchechengi, broccolo, cardoncello, cavolo, cedro, chinotto, cicerchia, giuggiola, gombo, lampascioni … |
| `nutrition_and_sustainability.macros_per_100g.starch_g` | 22 | alchechengi, broccolo, cavolo, cavolo, cavolo, cedro, chinotto, cicerchia, giuggiola, lampascioni … |
| `ripening_and_storage.postharvest_physiology.optimal_temperature_c` | 22 | agretti, alchechengi, amarena, asparago, carruba, cavolo, cedro, chinotto, cicerchia, cocco … |
| `ripening_and_storage.postharvest_physiology.optimal_humidity_percent` | 20 | agretti, alchechengi, amarena, carruba, cedro, chinotto, cicerchia, crescione, erba, gelso … |
| `nutrition_and_sustainability.protein_reference.claim_note` | 18 | amarena, carruba, cocco, giuggiola, mandorla, mirabella, mirtillo, navone, nocciola, noce … |
| `ripening_and_storage.ethylene_compatibility.compatibility_notes` | 18 | agretti, alchechengi, carruba, chinotto, cicerchia, gelso, giuggiola, lampascioni, mela, nespola … |
| `ripening_and_storage.ethylene_compatibility.produces_ethylene` | 18 | agretti, alchechengi, carruba, chinotto, cicerchia, gelso, giuggiola, lampascioni, mela, nespola … |
| `nutrition_and_sustainability.environmental_footprint` | 16 | agretti, alchechengi, carruba, cavolo, cicerchia, crescione, erba, giuggiola, nespola, puntarelle … |
| `seasonality.italy_macro_areas` | 14 | cardoncello, cavolo, daikon, fico, indivia, indivia, mela, mirtillo, ribes, sambuco … |
| `ripening_and_storage.perishability` | 13 | agretti, alchechengi, carruba, cicerchia, cocco, erba, giuggiola, lampascioni, mela, nespola … |

## 8. Caveats for use in the app

- **Non-Italian sources**: storage (USDA HB66, FoodKeeper, UC Davis), bioactive compounds (USDA, Phenol-Explorer) and some micronutrients come from US or international sources; the main nutrition data are CREA or BDA-IEO.
- **Storage times**: home storage time (FoodKeeper) and commercial storage time (HB66) are separate fields; the app must show users the former.
- **Environmental footprints**: literature medians with high variability; the low/medium/high thresholds are an app convention, declared in `basis`.
- **Polyphenols**: indicative values per 100 g of raw product. Phenol-Explorer: non-commercial use, cite the source.
- **EU claims**: computed on raw product per 100 g (Reg. (EC) 1924/2006); the protein claim for low-energy produce is put into context with LARN.
- **PAT**: linked by keywords; also includes processed products.
- **Texts**: rewritten by merging several sources and realigned with the data; some descriptive sentences (curiosities, culinary uses) are general knowledge.

## 9. Status per product

| Product | Category | Sources | Help entries | To verify | Missing | N/A | Warnings |
|---|---|---|---|---|---|---|---|
| Barley | Cereals | 19 | 4 | 18 | 19 | 23 | 1 |
| Buckwheat | Cereals | 18 | 4 | 17 | 19 | 28 | 0 |
| Durum Wheat | Cereals | 18 | 5 | 17 | 19 | 24 | 0 |
| Emmer Wheat (Farro) | Cereals | 17 | 6 | 17 | 19 | 27 | 0 |
| Oat | Cereals | 16 | 3 | 18 | 20 | 22 | 0 |
| Rice | Cereals | 19 | 5 | 18 | 20 | 23 | 0 |
| Basil | Herbs and spices | 24 | 5 | 1 | 9 | 18 | 0 |
| Chili Pepper | Herbs and spices | 24 | 5 | 2 | 7 | 12 | 0 |
| Chives | Herbs and spices | 16 | 2 | 0 | 28 | 15 | 0 |
| Mint | Herbs and spices | 23 | 4 | 17 | 20 | 22 | 0 |
| Oregano | Herbs and spices | 18 | 3 | 20 | 18 | 37 | 0 |
| Parsley | Herbs and spices | 25 | 4 | 0 | 6 | 17 | 0 |
| Rosemary | Herbs and spices | 22 | 4 | 18 | 19 | 23 | 0 |
| Saffron | Herbs and spices | 15 | 3 | 0 | 37 | 19 | 0 |
| Sage | Herbs and spices | 21 | 4 | 19 | 21 | 24 | 0 |
| Thyme | Herbs and spices | 22 | 4 | 18 | 20 | 22 | 0 |
| Almond | Fruit | 17 | 5 | 0 | 31 | 12 | 0 |
| Apple | Fruit | 29 | 5 | 18 | 11 | 5 | 0 |
| Apricot | Fruit | 29 | 7 | 17 | 11 | 9 | 0 |
| Avocado | Fruit | 23 | 5 | 17 | 4 | 22 | 1 |
| Banana | Fruit | 22 | 4 | 6 | 6 | 22 | 0 |
| Blackberry | Fruit | 26 | 4 | 17 | 11 | 8 | 0 |
| Blackcurrant | Fruit | 19 | 2 | 0 | 25 | 13 | 0 |
| Blueberry | Fruit | 28 | 6 | 17 | 11 | 8 | 0 |
| Cape Gooseberry | Fruit | 12 | 1 | 0 | 42 | 9 | 0 |
| Carob | Fruit | 13 | 2 | 0 | 50 | 9 | 0 |
| Cherry | Fruit | 29 | 7 | 17 | 12 | 8 | 0 |
| Chestnut | Fruit | 21 | 6 | 24 | 23 | 10 | 0 |
| Chinotto | Fruit | 11 | 4 | 0 | 54 | 10 | 0 |
| Citron | Fruit | 13 | 5 | 0 | 48 | 9 | 0 |
| Clementine | Fruit | 26 | 6 | 20 | 16 | 5 | 0 |
| Coconut | Fruit | 16 | 3 | 0 | 43 | 9 | 0 |
| Elderberry | Fruit | 17 | 3 | 0 | 40 | 12 | 0 |
| Fig | Fruit | 26 | 5 | 19 | 15 | 9 | 0 |
| Gooseberry | Fruit | 16 | 2 | 0 | 38 | 13 | 0 |
| Grapefruit | Fruit | 26 | 5 | 0 | 26 | 7 | 0 |
| Hazelnut | Fruit | 18 | 6 | 0 | 33 | 11 | 0 |
| Jujube | Fruit | 15 | 2 | 0 | 48 | 9 | 0 |
| Kiwifruit | Fruit | 27 | 5 | 17 | 16 | 12 | 0 |
| Lemon | Fruit | 29 | 6 | 17 | 14 | 4 | 0 |
| Lime | Fruit | 20 | 3 | 0 | 29 | 7 | 0 |
| Lingonberry | Fruit | 17 | 4 | 0 | 36 | 12 | 0 |
| Loquat | Fruit | 21 | 5 | 0 | 31 | 17 | 0 |
| Lychee | Fruit | 19 | 3 | 0 | 29 | 13 | 0 |
| Mandarin | Fruit | 28 | 7 | 18 | 16 | 5 | 0 |
| Mango | Fruit | 23 | 5 | 17 | 18 | 10 | 0 |
| Medlar | Fruit | 9 | 2 | 0 | 56 | 9 | 0 |
| Melon (Cantaloupe) | Fruit | 27 | 7 | 0 | 2 | 3 | 1 |
| Mirabelle Plum | Fruit | 15 | 3 | 0 | 33 | 10 | 0 |
| Mulberry | Fruit | 17 | 2 | 0 | 25 | 14 | 0 |
| Nectarine | Fruit | 23 | 6 | 0 | 26 | 5 | 0 |
| Olive | Fruit | 17 | 5 | 0 | 30 | 16 | 1 |
| Orange | Fruit | 28 | 6 | 17 | 12 | 5 | 0 |
| Papaya | Fruit | 21 | 4 | 0 | 9 | 31 | 0 |
| Passion Fruit | Fruit | 19 | 3 | 0 | 9 | 31 | 1 |
| Peach | Fruit | 29 | 7 | 18 | 12 | 5 | 0 |
| Pear | Fruit | 29 | 5 | 17 | 11 | 6 | 0 |
| Persimmon | Fruit | 24 | 5 | 19 | 18 | 13 | 0 |
| Pineapple | Fruit | 21 | 4 | 0 | 8 | 31 | 0 |
| Pistachio | Fruit | 19 | 6 | 0 | 27 | 11 | 0 |
| Plum | Fruit | 29 | 6 | 17 | 11 | 4 | 0 |
| Pomegranate | Fruit | 25 | 6 | 17 | 14 | 11 | 0 |
| Prickly Pear | Fruit | 21 | 5 | 0 | 32 | 13 | 0 |
| Quince | Fruit | 23 | 2 | 0 | 43 | 8 | 0 |
| Raspberry | Fruit | 28 | 7 | 17 | 11 | 8 | 1 |
| Redcurrant | Fruit | 25 | 5 | 0 | 28 | 10 | 0 |
| Sour Cherry | Fruit | 19 | 5 | 0 | 34 | 11 | 0 |
| Strawberry | Fruit | 28 | 6 | 17 | 11 | 8 | 0 |
| Table Grape | Fruit | 27 | 6 | 17 | 11 | 12 | 0 |
| Walnut | Fruit | 18 | 6 | 0 | 32 | 11 | 0 |
| Watermelon | Fruit | 27 | 6 | 0 | 3 | 4 | 0 |
| Black Truffle | Mushrooms | 13 | 4 | 0 | 31 | 23 | 0 |
| Button Mushroom | Mushrooms | 20 | 4 | 12 | 14 | 17 | 0 |
| Caesar's Mushroom | Mushrooms | 14 | 3 | 0 | 28 | 14 | 0 |
| Chanterelle | Mushrooms | 16 | 4 | 0 | 27 | 13 | 0 |
| King Oyster Mushroom | Mushrooms | 13 | 4 | 0 | 35 | 16 | 0 |
| Morel | Mushrooms | 14 | 3 | 0 | 28 | 13 | 0 |
| Oyster Mushroom | Mushrooms | 19 | 4 | 15 | 16 | 17 | 0 |
| Porcini Mushroom | Mushrooms | 18 | 5 | 13 | 17 | 13 | 0 |
| Shiitake | Mushrooms | 13 | 3 | 0 | 34 | 16 | 0 |
| White Truffle | Mushrooms | 9 | 4 | 0 | 44 | 22 | 0 |
| Artichoke | Vegetables | 29 | 7 | 0 | 3 | 8 | 0 |
| Arugula (Rocket) | Vegetables | 21 | 5 | 0 | 6 | 12 | 0 |
| Asparagus | Vegetables | 29 | 5 | 0 | 1 | 6 | 0 |
| Beetroot | Vegetables | 26 | 4 | 0 | 1 | 9 | 0 |
| Belgian Endive | Vegetables | 19 | 3 | 0 | 29 | 9 | 0 |
| Bell Pepper | Vegetables | 29 | 7 | 0 | 2 | 3 | 0 |
| Black Kale (Lacinato) | Vegetables | 25 | 5 | 1 | 3 | 7 | 1 |
| Black Salsify | Vegetables | 13 | 5 | 0 | 23 | 12 | 0 |
| Broad Bean (Fava Bean) | Vegetables | 26 | 7 | 0 | 4 | 9 | 0 |
| Broccoli | Vegetables | 25 | 4 | 0 | 1 | 8 | 0 |
| Brussels Sprouts | Vegetables | 23 | 3 | 0 | 0 | 8 | 0 |
| Cabbage | Vegetables | 26 | 4 | 0 | 0 | 8 | 0 |
| Cardoon | Vegetables | 18 | 5 | 11 | 13 | 8 | 0 |
| Carrot | Vegetables | 29 | 7 | 0 | 0 | 8 | 0 |
| Cauliflower | Vegetables | 28 | 6 | 0 | 1 | 7 | 0 |
| Celeriac | Vegetables | 21 | 5 | 0 | 30 | 10 | 0 |
| Celery | Vegetables | 28 | 7 | 0 | 0 | 8 | 0 |
| Chard | Vegetables | 25 | 5 | 1 | 4 | 8 | 0 |
| Chayote | Vegetables | 11 | 1 | 0 | 35 | 10 | 0 |
| Chickpea | Vegetables | 17 | 4 | 0 | 9 | 29 | 0 |
| Chicory | Vegetables | 21 | 4 | 0 | 5 | 9 | 0 |
| Chinese Cabbage | Vegetables | 15 | 3 | 0 | 23 | 12 | 0 |
| Common Bean | Vegetables | 25 | 6 | 1 | 4 | 6 | 0 |
| Corn Salad (Lamb's Lettuce) | Vegetables | 17 | 3 | 0 | 5 | 9 | 0 |
| Cucumber | Vegetables | 27 | 6 | 0 | 2 | 6 | 0 |
| Curly Endive | Vegetables | 18 | 3 | 0 | 30 | 10 | 0 |
| Cutting Chicory | Vegetables | 18 | 3 | 0 | 8 | 9 | 0 |
| Daikon | Vegetables | 15 | 3 | 0 | 32 | 18 | 0 |
| Eggplant (Aubergine) | Vegetables | 29 | 8 | 0 | 0 | 2 | 0 |
| Escarole | Vegetables | 19 | 3 | 0 | 29 | 10 | 0 |
| Fennel | Vegetables | 25 | 5 | 0 | 6 | 10 | 0 |
| Garlic | Vegetables | 30 | 6 | 0 | 2 | 14 | 0 |
| Grass Pea | Vegetables | 9 | 3 | 0 | 66 | 9 | 0 |
| Green Bean (Snap Bean) | Vegetables | 27 | 6 | 0 | 0 | 6 | 1 |
| Head Lettuce | Vegetables | 28 | 7 | 0 | 0 | 7 | 0 |
| Horseradish | Vegetables | 12 | 4 | 0 | 34 | 16 | 0 |
| Jerusalem Artichoke (Sunchoke) | Vegetables | 17 | 4 | 2 | 5 | 18 | 0 |
| Kohlrabi | Vegetables | 20 | 4 | 0 | 2 | 11 | 0 |
| Leaf Lettuce | Vegetables | 28 | 6 | 0 | 2 | 7 | 0 |
| Leek | Vegetables | 24 | 5 | 0 | 3 | 9 | 0 |
| Lentil | Vegetables | 19 | 4 | 0 | 9 | 28 | 0 |
| Okra | Vegetables | 14 | 3 | 0 | 17 | 15 | 0 |
| Parsnip | Vegetables | 19 | 4 | 0 | 3 | 16 | 1 |
| Pea | Vegetables | 26 | 5 | 0 | 2 | 9 | 0 |
| Peanut | Vegetables | 19 | 2 | 0 | 9 | 22 | 0 |
| Potato | Vegetables | 29 | 5 | 0 | 0 | 4 | 0 |
| Pumpkin (Winter Squash) | Vegetables | 28 | 6 | 1 | 1 | 5 | 0 |
| Puntarelle | Vegetables | 16 | 4 | 0 | 17 | 13 | 0 |
| Radicchio | Vegetables | 23 | 5 | 0 | 6 | 7 | 0 |
| Radish | Vegetables | 27 | 4 | 0 | 1 | 10 | 0 |
| Red Cabbage | Vegetables | 23 | 4 | 0 | 22 | 8 | 0 |
| Rhubarb | Vegetables | 14 | 1 | 0 | 26 | 10 | 0 |
| Romanesco | Vegetables | 18 | 5 | 0 | 30 | 12 | 0 |
| Saltwort (Agretti) | Vegetables | 14 | 2 | 0 | 32 | 11 | 0 |
| Samphire | Vegetables | 11 | 2 | 0 | 47 | 11 | 0 |
| Savoy Cabbage | Vegetables | 24 | 4 | 0 | 1 | 8 | 0 |
| Shallot | Vegetables | 21 | 5 | 0 | 3 | 13 | 0 |
| Snow Pea | Vegetables | 16 | 3 | 0 | 35 | 11 | 0 |
| Spinach | Vegetables | 28 | 4 | 0 | 1 | 9 | 0 |
| Spring Onion | Vegetables | 20 | 5 | 0 | 26 | 13 | 0 |
| Summer Onion | Vegetables | 26 | 6 | 0 | 0 | 7 | 0 |
| Swede | Vegetables | 12 | 3 | 0 | 36 | 16 | 0 |
| Sweet Corn | Vegetables | 21 | 6 | 0 | 3 | 10 | 0 |
| Sweet Potato | Vegetables | 17 | 4 | 0 | 24 | 11 | 0 |
| Tassel Hyacinth Bulbs | Vegetables | 6 | 2 | 0 | 68 | 11 | 0 |
| Tomato | Vegetables | 27 | 7 | 0 | 4 | 3 | 0 |
| Turnip | Vegetables | 21 | 5 | 0 | 2 | 11 | 0 |
| Turnip Greens (Broccoli Rabe) | Vegetables | 23 | 4 | 1 | 9 | 13 | 0 |
| Watercress | Vegetables | 17 | 2 | 0 | 23 | 10 | 0 |
| Wild Asparagus | Vegetables | 15 | 4 | 0 | 33 | 12 | 0 |
| Winter Onion | Vegetables | 26 | 7 | 0 | 1 | 6 | 1 |
| Zucchini (Summer Squash) | Vegetables | 27 | 5 | 0 | 1 | 6 | 0 |

## 10. Reproducibility and files

- `data/database.json` – the database; `data/schema.json` – the schema; `data/database_guide.md` – the field guide.
- `data/draft_legacy_values.json` – draft values removed from the app (the original draft itself is not published).
- `data/audit_findings.json`, `data/template_coverage.json` – results of the checks.
- `data/raw/` – copies of the downloaded sources (not published); `scripts/config/` – curated configurations with quotes; `scripts/texts/` – IT/EN texts.
- `scripts/` – the pipeline, order in `scripts/README.md`.
