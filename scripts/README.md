# Script della Fase 1 – ordine di esecuzione

Ogni script legge e riscrive `data/database.json` (salvo dove indicato) ed è descritto nella propria docstring.
Le configurazioni curate a mano, con citazioni delle fonti, sono in `scripts/config/`; i dati grezzi scaricati in `data/raw/`.

## 1. Fonti, indice e migrazione
1. `fetch_sources.py` – scarica/mette in cache le fonti web
2. `build_index.py` – `data/items_index.json` (lista master, codici e URL per fonte)
3. `migrate_draft.py` – porta la bozza nella struttura definitiva

## 2. Nutrizione
4. `enrich_nutrition.py` – CREA + BDA-IEO, %VNR, claim UE
5. `enrich_fdc.py` – USDA FDC per gli alimenti senza CREA/BDA
6. `fill_micros_fdc.py` – vitamine/minerali FDC dove CREA/BDA non li riportano
7. `fix_corn_sweet.py` – mais = pannocchia fresca (BDA-IEO 50086)
8. `enrich_protein.py` – riferimento LARN per le proteine

## 3. Stagionalità, calendario, botanica
9. `extract_local_pdfs.py`, `enrich_seasonality.py` – PDF locali, EUFIC, voto tra fonti; `enrich_special_seasonality.py` – alimenti assenti dai calendari (pesca noce, tartufi per Legge 752/1985, ovolo); `estimate_zone_gaps.py` – stime per le zone senza dato (`seasonality.estimates`, mostrate con ≈ e disattivabili; esotici: "Non coltivato qui"); `apply_curated_seasonality.py` – stagionalità italiana da fonti specifiche lette a mano per gli alimenti aggiunti il 2026-11-05 (`config/italy_seasonality_curated.json`: Orto da Coltivare, Slow Food, Provincia di Cuneo, disciplinari); `apply_seasonality_curve.py` – curva completa primizia → picco → fine stagione per le macro-aree italiane (caso 1: deperibili estivi allineati alla raccolta in pieno campo; caso 2: buchi brevi chiusi; caso 3: prodotti da conservazione con `seasonality.availability_note`; regola in `metadata.seasonality_curve_method`, provenienza in `seasonality.curve_basis`), da lanciare dopo `apply_curated_seasonality.py` e prima di `estimate_zone_gaps.py`; `audit_seasonality_curves.py` – controllo di picchi, curve piatte, buchi e differenze raccolta/stagione (`data/seasonality_audit.json`); `enrich_zone_gaps.py` – zone EUFIC mancanti (calendario austriaco, derivazione mediterranea dal Sud Italia)
10. `enrich_botany.py`, `verify_botany.py` – EPPO, WFO, GBIF
11. `build_cultivation_notes.py` – note di coltivazione da Orto da Coltivare

## 4. Varietà e territori
12. `fetch_eambrosia.py`, `verify_dop_igp.py` – DOP/IGP sul registro UE
13. `fetch_text_pages.py`, `fetch_slowfood.py`, `verify_varieties.py` – verifica varietà sulle fonti testuali
14. `verify_varieties_eu.py` – seconda verifica sul Catalogo comune UE; `curate_varieties.py` – aggiunte e correzioni curate (pesca tabacchiera, link Slow Food errati)
15. `apply_upov.py` – codice di specie UPOV + varietà iscritte in Italia
16. `verify_plant_part.py` – parte della pianta usata
17. `enrich_pat.py` – Prodotti Agroalimentari Tradizionali (MASAF)

## 5. Conservazione e post-raccolta
18. `enrich_postharvest.py` – UC Davis / HB66
19. `enrich_foodkeeper.py`, `apply_foodkeeper_modes.py` – durate domestiche FoodKeeper
20. `enrich_chilling.py` – HB66 Tab. 1-2 (danno da freddo, gelo)
21. `apply_hb66_curated.py` – valori dei capitoli HB66 (`config/hb66_chapter_curated.json`); `apply_ethylene_curated.py` – classi di etilene a 20 °C del frutto maturo dai capitoli HB66 (`config/ethylene_curated.json`), ricalcolo di keep_away_from; va rilanciato anche dopo `apply_texts.py`, che rigenera le note
22. `apply_kader_class.py` – classe di respirazione di Kader + deperibilità
23. `mark_not_applicable.py` – campi non pertinenti (prodotti secchi, esotici)
24. `apply_home_storage.py` – dove conservarlo in casa (UC Davis + FoodKeeper)
25. `mark_structural_na.py` – altri campi vuoti per definizione
26. `fix_audit.py` – correzioni emerse dal ricontrollo
27. `apply_compat_groups.py` – gruppi di conservazione compatibile (HB66 Tab. 1)

## 6. Composti, allergeni, porzioni, sostenibilità
28. `enrich_bioactives.py`, `enrich_polyphenols.py` – carotenoidi USDA, flavonoidi USDA, Phenol-Explorer
29. `enrich_allergens_portions.py` – allergeni Reg. UE 1169/2011, porzioni LARN
30. `enrich_footprint.py` – impronta di carbonio e idrica (SU-EATABLE LIFE; AGRIBALYSE 3.1 per le erbe aromatiche)
31. `set_sustainability_summary.py` – sintesi EUFIC nei metadati

## 7. Testi, immagini, fonti
32. `sync_nutrient_mentions.py --apply` – allinea "ricco di / fonte di" ai claim (modifica `scripts/texts/`)
33. `apply_texts.py` – testi IT/EN da `scripts/texts/block_*.json`; `merge_items.py` – alimenti uniti (bietola da taglio nella bietola); `add_items.py` – alimenti aggiunti in deroga (tartufo bianco); i 44 alimenti aggiunti il 2026-11-05 sono nel catalogo (`added`) con le corrispondenze in `config/new_items_2026_11_05.json` (capitolo HB66, voce e codice USDA FDC) e `fix_new_items.py` (durate professionali, nutrizione non disponibile)
34. `download_images.py`, `sync_images.py --renumber --prune`, `make_image_review.py`; nuova revisione per tipi: `apply_image_types.py` (classificazione in `config/image_view_types.json`), `find_image_candidates.py`, `make_candidates_review.py`, `apply_image_selection.py`
35. `build_source_registry.py` – fonti usate e link utili per alimento
36. `tidy_notes.py` – pulizia delle note
37. `localize_fields.py` – **ultimo passo di trasformazione**: rende bilingui {it, en} i campi descrittivi scritti in italiano dagli script precedenti (basis, derivation, method, note). Gli script dei passi 21-36 scrivono stringhe italiane: se se ne rilancia uno, rilanciare poi anche questo e i successivi
38. `build_help.py` – vocabolario IT/EN dei valori codificati, glossario (`config/glossary.json`), `field_help` e `help_refs` per le icone "?"
39. `build_source_catalog.py` – descrizione, autorevolezza, contenuti e usi di ogni fonte (`config/source_descriptions.json`) e casi di conflitto tra fonti (`config/source_conflicts.json`)

38a. `build_app_support_metadata.py` – informazioni e regole usate dall'app, scritte nel database ("il database prima dell'app"): nomi IT/EN delle famiglie botaniche, codici ISO e colori delle zone, ordine e regole del calendario di riferimento, short_name/site_url/favicon delle fonti, icone di stati e categorie, regole dell'etilene
38b. `ux_terminology.py` – nei testi per l'utente "alimento/alimenti" e "food/foods" diventano "prodotto/prodotti" e "product/produce" (restano nomi propri delle fonti e "alimenti di origine animale"); va lanciato prima di `title_case_labels.py`
38d. `apply_storage_display_review.py` – "Dove Conservarlo" (2026-11-13): etichetta "A Temperatura Ambiente"; consiglio senza "una volta tagliato" per frigorifero e prodotti senza luogo e senza frasi che ripetono storage_instructions (regole in `apply_home_storage.py`)
38c. `title_case_labels.py` – **ultimo passo**: etichette brevi con l'iniziale maiuscola a ogni parola ("In Frigorifero", "Non Climaterico"), in IT e EN; non le frasi né i nomi ufficiali registrati. Va rilanciato dopo `build_help.py` e `build_source_catalog.py`, che rigenerano vocabolario e glossario

**Corpus condiviso delle descrizioni** (`corpus.py`, automatico): `common.load_json` espande i riferimenti `{corpus_ref, specific_addition}` di `data/database.json` in testo completo e `common.save_json` li ricompatta in `shared_descriptions_corpus` (testi descrittivi ripetuti in almeno 2 prodotti, chiavi parlanti conservate tra un salvataggio e l'altro). Gli script lavorano quindi sempre su testi completi; per leggere il file così com'è: `load_json(path, raw=True)`.

**Peak Season Admin Studio** (cartella `admin_studio/`, avvio con `admin_studio/Avvia_Admin_Studio.bat` / `.sh`, istruzioni in `admin_studio/README.md`): dashboard nel browser per testi (`data/ui_copy.json`, corpus condiviso, descrizioni dei prodotti), immagini (foto principale, tipo di vista, download da Wikimedia/USDA ARS con licenza), icone (`data/ui_config.json`, letto da `build_app_support_metadata.py` per le voci del database), loghi delle fonti (editore, titolo, logo caricato), link generali e per prodotto (`config/link_overrides.json`, applicato da `apply_link_overrides.py` e da `build_source_registry.py`) e build (sincronizzazione asset, APK Android). Ogni salvataggio valida il database e ripristina i file se la validazione fallisce. `copy_editor.py` resta solo per compatibilità e avvia lo studio. `sync_images.py` rispetta le foto principali scelte a mano (`assets/images/_primary_manual.json`).

Dopo `title_case_labels.py`: `build_nutrition_claims_rules.py` – `metadata.nutrition_claims_eu_rules` (gruppo, nutriente e tono di ogni claim, con il testo IT esatto come chiave) e `key` stabile di vitamine e minerali. `build_app_support_metadata.py` scrive anche `metadata.detail_display_rules`, i livelli e i colori dell'impronta (`environmental_footprint_method.levels`) ed editore/titolo/logo delle fonti (`config/source_display.json`, anche nelle fonti del glossario).

## 8. Controlli e report
40. `validate_db.py` – JSON Schema
41. `audit_db.py` – ricontrollo voce per voce, glossario, vocabolario e fonti (`data/audit_findings.json`)
42. `template_coverage.py` – copertura del template originale (`data/template_coverage.json`)
43. `make_report.py` – `data/scraping_report.md`; `make_db_guide.py` – `data/database_guide.md`; `make_excluded_report.py` – `data/excluded_candidates_report.md` (alimenti esclusi dalla regola di ammissione)

## 9. Fase 2 – app Flutter (`app/`)
44. `build_app_assets.py [--force]` – **dopo ogni modifica del database o delle immagini**: copia `data/database.json` minificato e senza `data_completeness` (con il corpus condiviso: l'app risolve `corpus_ref`) e `data/ui_copy.json` in `app/assets/data/`, converte le immagini in WebP (`app/assets/images/thumb/` 600 px per le card, `full/` 1080 px per la galleria)
45. `preview_screens.py [nome_schermata ...]` – anteprime PNG delle schermate (build web + Playwright/Edge) in `schemi_interfaccia/anteprime_fase2/`; istruzioni nella docstring
46. `fetch_source_favicons.py` – favicon dei siti delle fonti (icona più grande dichiarata dal sito, poi sito dell'ente, poi servizio favicon di Google) in `app/assets/sources/<chiave>.png`; originali in `data/raw/favicons/`
