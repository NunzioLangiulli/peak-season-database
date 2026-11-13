# Phase 1 scripts – execution order

Every script reads and rewrites `data/database.json` (unless stated otherwise) and is described in its own docstring.
Hand-curated configurations, with source quotes, are in `scripts/config/`; downloaded raw data in `data/raw/` (not published).

Note: `build_index.py`, `migrate_draft.py` and `fix_corn_sweet.py` read the original draft (`data/_backup_bozza_2026-11-04/`), which is not published: they document how the database was started and cannot be re-run from this repository.

## 1. Sources, index and migration
1. `fetch_sources.py` – downloads/caches the web sources
2. `build_index.py` – `data/items_index.json` (master list, codes and URLs per source)
3. `migrate_draft.py` – moves the draft into the final structure

## 2. Nutrition
4. `enrich_nutrition.py` – CREA + BDA-IEO, %NRV, EU claims
5. `enrich_fdc.py` – USDA FDC for products without CREA/BDA
6. `fill_micros_fdc.py` – FDC vitamins/minerals where CREA/BDA do not report them
7. `fix_corn_sweet.py` – maize = fresh corn on the cob (BDA-IEO 50086)
8. `enrich_protein.py` – LARN reference for protein

## 3. Seasonality, calendar, botany
9. `extract_local_pdfs.py`, `enrich_seasonality.py` – local PDFs, EUFIC, vote across sources; `enrich_special_seasonality.py` – products missing from the calendars (nectarine, truffles per Law 752/1985, Caesar's mushroom); `estimate_zone_gaps.py` – estimates for zones without data (`seasonality.estimates`, shown with ≈ and switchable off; exotic produce: "Not grown here"); `apply_curated_seasonality.py` – Italian seasonality from specific sources read by hand for the products added on 2026-11-05 (`config/italy_seasonality_curated.json`: Orto da Coltivare, Slow Food, Province of Cuneo, product specifications); `apply_seasonality_curve.py` – full early → peak → end-of-season curve for the Italian macro-areas (case 1: perishable summer produce aligned with open-field harvest; case 2: short gaps closed; case 3: stored produce with `seasonality.availability_note`; rule in `metadata.seasonality_curve_method`, provenance in `seasonality.curve_basis`), to run after `apply_curated_seasonality.py` and before `estimate_zone_gaps.py`; `audit_seasonality_curves.py` – check of peaks, flat curves, gaps and harvest/season differences (`data/seasonality_audit.json`); `enrich_zone_gaps.py` – missing EUFIC zones (Austrian calendar, Mediterranean derived from Southern Italy)
10. `enrich_botany.py`, `verify_botany.py` – EPPO, WFO, GBIF
11. `build_cultivation_notes.py` – growing notes from Orto da Coltivare

## 4. Varieties and territories
12. `fetch_eambrosia.py`, `verify_dop_igp.py` – PDO/PGI on the EU register
13. `fetch_text_pages.py`, `fetch_slowfood.py`, `verify_varieties.py` – variety checks on text sources
14. `verify_varieties_eu.py` – second check on the EU Common Catalogue; `curate_varieties.py` – curated additions and fixes (flat peach, wrong Slow Food links)
15. `apply_upov.py` – UPOV species code + varieties registered in Italy
16. `verify_plant_part.py` – plant part used
17. `enrich_pat.py` – Traditional Agri-food Products (MASAF)

## 5. Storage and postharvest
18. `enrich_postharvest.py` – UC Davis / HB66
19. `enrich_foodkeeper.py`, `apply_foodkeeper_modes.py` – FoodKeeper home storage times
20. `enrich_chilling.py` – HB66 Tab. 1-2 (chilling injury, freezing)
21. `apply_hb66_curated.py` – values from HB66 chapters (`config/hb66_chapter_curated.json`); `apply_ethylene_curated.py` – ethylene classes at 20 °C of the ripe fruit from HB66 chapters (`config/ethylene_curated.json`), recomputes keep_away_from; must also be re-run after `apply_texts.py`, which regenerates the notes
22. `apply_kader_class.py` – Kader respiration class + perishability
23. `mark_not_applicable.py` – non-applicable fields (dried products, exotic produce)
24. `apply_home_storage.py` – where to store it at home (UC Davis + FoodKeeper)
25. `mark_structural_na.py` – other fields empty by definition
26. `fix_audit.py` – fixes from the re-check
27. `apply_compat_groups.py` – compatible storage groups (HB66 Tab. 1)

## 6. Compounds, allergens, portions, sustainability
28. `enrich_bioactives.py`, `enrich_polyphenols.py` – USDA carotenoids, USDA flavonoids, Phenol-Explorer
29. `enrich_allergens_portions.py` – allergens per Reg. (EU) 1169/2011, LARN portions
30. `enrich_footprint.py` – carbon and water footprint (SU-EATABLE LIFE; AGRIBALYSE 3.1 for culinary herbs)
31. `set_sustainability_summary.py` – EUFIC summary in the metadata

## 7. Texts, images, sources
32. `sync_nutrient_mentions.py --apply` – aligns "rich in / source of" with the claims (edits `scripts/texts/`)
33. `apply_texts.py` – IT/EN texts from `scripts/texts/block_*.json`; `merge_items.py` – merged products (leaf beet into chard); `add_items.py` – products added as exceptions (white truffle); the 44 products added on 2026-11-05 are in the catalogue (`added`) with their mappings in `config/new_items_2026_11_05.json` (HB66 chapter, USDA FDC entry and code) and `fix_new_items.py` (commercial storage times, nutrition not available)
34. `download_images.py`, `sync_images.py --renumber --prune`, `make_image_review.py`; review by view type: `apply_image_types.py` (classification in `config/image_view_types.json`), `find_image_candidates.py`, `make_candidates_review.py`, `apply_image_selection.py`
35. `build_source_registry.py` – sources used and useful links per product
36. `tidy_notes.py` – note clean-up
37. `localize_fields.py` – **last transformation step**: makes the descriptive fields written in Italian by the previous scripts bilingual {it, en} (basis, derivation, method, note). Scripts in steps 21-36 write Italian strings: if one of them is re-run, re-run this one and the following ones too
38. `build_help.py` – IT/EN vocabulary of coded values, glossary (`config/glossary.json`), `field_help` and `help_refs` for the "?" icons
39. `build_source_catalog.py` – description, authority, contents and uses of every source (`config/source_descriptions.json`) and cases of conflict between sources (`config/source_conflicts.json`)

38a. `build_app_support_metadata.py` – information and rules used by the app, written into the database ("database first, app second"): IT/EN botanical family names, ISO codes and zone colours, order and rules of the reference calendar, short_name/site_url/favicon of the sources, state and category icons, ethylene rules
38b. `ux_terminology.py` – in user-facing texts "alimento/alimenti" and "food/foods" become "prodotto/prodotti" and "product/produce" (source proper names and "alimenti di origine animale" are kept); run before `title_case_labels.py`
38e. `merge_slow_down_into_storage.py` – for non-climacteric produce, adds to storage_instructions only the slow_down information it was missing (2026-11-13); the app no longer shows slow_down for them
38f. `clean_garden_notes.py` – removes area garden notes that only repeat the sowing/harvest chart and the "Calendario ricavato…" source note; keeps notes with extra information (2026-11-13)
38d. `apply_storage_display_review.py` – "Where to Store It" (2026-11-13): "At Room Temperature" label; advice without "once cut" for the fridge and for products with no location, and without sentences repeating storage_instructions (rules in `apply_home_storage.py`)
38c. `title_case_labels.py` – **last step**: short labels in Title Case ("In Frigorifero", "Non Climaterico"), in IT and EN; not sentences nor registered official names. Re-run after `build_help.py` and `build_source_catalog.py`, which regenerate vocabulary and glossary

**Shared description corpus** (`corpus.py`, automatic): `common.load_json` expands the `{corpus_ref, specific_addition}` references of `data/database.json` into full text, and `common.save_json` compacts them again into `shared_descriptions_corpus` (descriptive texts repeated in at least 2 products, with readable keys kept between saves). Scripts therefore always work on full texts; to read the file as stored: `load_json(path, raw=True)`.

**Peak Season Admin Studio** (`admin_studio/` folder, started with `admin_studio/Avvia_Admin_Studio.bat` / `.sh`, instructions in `admin_studio/README.md`): browser dashboard for texts (`data/ui_copy.json`, shared corpus, product descriptions), images (main photo, view type, download from Wikimedia/USDA ARS with licence), icons (`data/ui_config.json`, read by `build_app_support_metadata.py` for database entries), source logos (publisher, title, uploaded logo), general and per-product links (`config/link_overrides.json`, applied by `apply_link_overrides.py` and by `build_source_registry.py`) and build (asset sync, Android APK). Every save validates the database and restores the files if validation fails. `copy_editor.py` is kept only for compatibility and starts the Studio. `sync_images.py` respects hand-picked main photos (`assets/images/_primary_manual.json`).

After `title_case_labels.py`: `build_nutrition_claims_rules.py` – `metadata.nutrition_claims_eu_rules` (group, nutrient and tone of every claim, keyed by the exact IT text) and a stable `key` for vitamins and minerals. `build_app_support_metadata.py` also writes `metadata.detail_display_rules`, perishability colours (`perishability_legend.levels[].color_hex`), footprint levels and colours (`environmental_footprint_method.levels`) and source publisher/title/logo (`config/source_display.json`, also in the glossary sources).

## 8. Checks and reports
40. `validate_db.py` – JSON Schema
41. `audit_db.py` – item-by-item re-check, glossary, vocabulary and sources (`data/audit_findings.json`)
42. `template_coverage.py` – coverage of the original template (`data/template_coverage.json`)
43. `make_report.py` – `data/scraping_report.md`; `make_db_guide.py` – `data/database_guide.md`; `make_excluded_report.py` – `data/excluded_candidates_report.md` (products excluded by the inclusion rule)

## 9. Phase 2 – Flutter app (`app/`, separate repository)
44. `build_app_assets.py [--force]` – **after every change to the database or images**: copies `data/database.json` minified and without `data_completeness` (with the shared corpus: the app resolves `corpus_ref`) and `data/ui_copy.json` into `app/assets/data/`, converts images to WebP (`app/assets/images/thumb/` 600 px for cards, `full/` 1080 px for the gallery)
45. `preview_screens.py [screen_name ...]` – PNG previews of the screens (web build + Playwright/Edge) in `schemi_interfaccia/anteprime_fase2/`; instructions in the docstring
46. `fetch_source_favicons.py` – favicons of the source websites (largest icon declared by the site, then the organisation's site, then Google's favicon service) in `app/assets/sources/<key>.png`; originals in `data/raw/favicons/`
