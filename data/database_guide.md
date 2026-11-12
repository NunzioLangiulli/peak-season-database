# Peak Season database guide

This guide explains how `data/database.json` is built, block by block, using the real **tomato** record as an example. For each block: what it is for in the app, where the data come from, how to read them.

## 1. Files

| File | Content |
|---|---|
| `data/database.json` | The database: `metadata` (legends, methods, sources) + `items` (153 records) |
| `data/schema.json` | The formal rules (JSON Schema): types, allowed values, required fields |
| `data/items_index.json` | The master list: for each product, its exact codes and URLs on every source |
| `data/draft_legacy_values.json` | Values from the initial draft that could not be verified: removed from the app but preserved |
| `data/scraping_report.md` | The reliability and gap report |
| `data/audit_findings.json` | Results of the item-by-item re-check |
| `data/raw/` | Copies of the raw source data (PDF, CSV, xlsx, pages; not published) |
| `scripts/config/` | Tables hand-curated from the sources, with quotes and page numbers |
| `assets/images/` | Photos `<id>_01.jpg`, `_02.jpg`… (credits in `_metadata.json`) |

## 2. General logic

Every record follows the same 12-block structure. Three principles apply everywhere:

1. **Every value has a source.** Structured blocks carry the source next to the value (`source`, `basis`, `source_food`, `derivation`); all sources of a record are listed in `sources_by_topic.sources_used`.
2. **`null` is not the same as empty.** A `null` is either a real gap (listed in `data_completeness.missing_fields`) or a field that makes no sense for that product (listed in `not_applicable_fields`): e.g. the chilling-injury threshold for produce that is not chill-sensitive.
3. **Bilingual.** Every user-facing text is an object `{"it": …, "en": …}` (see §13).

Identifiers (`id`) are `italianname_englishname` without accents: they are also the keys used by cross-references between records (e.g. `keep_away_from`, `compatible_with`) and by photo file names.

## 3. Identity and botany

```json
{
  "id": "pomodoro_tomato",
  "names": {
    "it": "Pomodoro",
    "en": "Tomato",
    "synonyms": null
  },
  "category": "verdura"
}
```
`category` is one of the 5 template values. Synonyms come from EPPO (official IT/EN common names).

```json
{
  "scientific_name": "Solanum lycopersicum",
  "eppo_code": "LYPES",
  "eppo_preferred_name": "Solanum lycopersicum",
  "wfo_id": "wfo-0001029216",
  "gbif_key": null,
  "family": "Solanaceae",
  "genus": "Solanum",
  "plant_part_used": "frutto",
  "upov_code": "SOLAN_LYC",
  "upov_name": "Solanum lycopersicum L.",
  "upov_register": "VEG",
  "upov_match": "exact",
  "upov_note": null,
  "varieties_registered_italy": {
    "count": 621,
    "upov_code": "SOLAN_LYC",
    "status": "Registered",
    "checked": "2026-11-05",
    "source": "https://ec.europa.eu/food/plant-variety-portal/"
  }
}
```
- `scientific_name`, `family`, `genus`: verified on EPPO and World Flora Online (`eppo_code` and `wfo_id` are the official codes).
- `plant_part_used`: confirmed by the source texts.
- `upov_*`: the species code of the **EU Common Catalogue of varieties**; `varieties_registered_italy.count` = varieties currently on the Italian register.

## 4. Varieties and territories

```json
{
  "notable_varieties": [
    "Pomodoro di Pachino IGP",
    "Pomodoro San Marzano dell'Agro Sarnese-Nocerino DOP",
    "Pomodorino del Piennolo del Vesuvio DOP",
    "Cuore di Bue Ligure"
  ],
  "has_dop_igp": true,
  "dop_igp_labels": [
    "Pomodorino del Piennolo del Vesuvio DOP",
    "Pomodoro San Marzano dell'Agro Sarnese-Nocerino DOP",
    "Pomodoro di Pachino IGP"
  ],
  "eambrosia_verified": true,
  "varieties_verification": [
    {
      "name": "Pomodoro di Pachino IGP",
      "verified": true,
      "sources": [
        {
          "source_key": "eambrosia",
          "url": "https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/"
        },
        {
          "source_key": "orto_da_coltivare",
          "url": "https://www.ortodacoltivare.it/ortaggi/pomodoro/"
        }
      ]
    },
    {
      "name": "Pomodoro San Marzano dell'Agro Sarnese-Nocerino DOP",
      "verified": true,
      "sources": [
        {
          "source_key": "eambrosia",
          "url": "https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/"
        }
      ]
    },
    {
      "name": "Pomodorino del Piennolo del Vesuvio DOP",
      "verified": true,
      "sources": [
        {
          "source_key": "eambrosia",
          "url": "https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/"
        }
      ]
    },
    {
      "name": "Cuore di Bue Ligure",
      "verified": true,
      "note": {
        "it": "Catalogo comune UE: registrata come 'Cuor di bue' (specie UPOV SOLAN_LYC); iscritta in IT. registrato il tipo 'Cuor di bue', non la selezione ligure.",
        "en": "EU Common Catalogue: registered as 'Cuor di bue' (UPOV species SOLAN_LYC); registered in IT. the 'Cuor di bue' type is registered, not the Ligurian selection."
      },
      "sources": [
        {
          "source_key": "eu_plant_variety_portal",
          "url": "https://ec.europa.eu/food/plant-variety-portal/",
          "list": "common_catalogue",
          "registered_name": "Cuor di bue",
          "upov_code": "SOLAN_LYC",
          "match": "approx",
          "records": [
            {
              "country": "IT",
  …
```
- `notable_varieties` contains **only** verified varieties; `varieties_verification` says where (Slow Food, EU Catalogue, Orto da Coltivare…) and under which name they are registered.
- `dop_igp_labels` and `has_dop_igp` (PDO/PGI) are verified on the EU **eAmbrosia** register (`eambrosia_verified`).
- **Traditional Agri-food Products (PAT)** are in `nutrition_and_sustainability.traditional_products_pat` (see §9).

## 5. Images

```json
{
  "primary": "pomodoro_tomato_01.jpg",
  "gallery": [
    "pomodoro_tomato_01.jpg",
    "pomodoro_tomato_02.jpg",
    "pomodoro_tomato_03.jpg",
    "…"
  ],
  "image_details": [
    {
      "filename": "pomodoro_tomato_01.jpg",
      "author": "Engin_Akyurt / Pixabay",
      "license": "Pixabay Content License",
      "license_url": "https://pixabay.com/service/license-summary/",
      "source_url": "https://pixabay.com/photos/tomatoes-cherry-tomatoes-vegetables-8181194/",
      "provider": "pixabay",
      "width": 1280,
      "height": 853,
      "view_type": "full_frame"
    }
  ]
}
```
Every photo has author, licence, source URL and type (`view_type`): `full_frame` (the product fills the frame: it is the main photo when available), `isolated_background` (white or coloured background), `plant_in_field` (the plant), `botanical_plate` (botanical plate), `cut_section` (cut open), `other`. `flags` reports known issues (plate, wrong subject), `variety` a specific variety (e.g. flat peach). `sync_images.py` realigns the database when photos are removed from the folder.

## 6. Seasonality

In the excerpt the 12 months (Jan→Dec) are abbreviated: `·` out of season, `p` early season, `S` in season, `P` peak, `f` end of season.

```json
{
  "italy_macro_areas": {
    "nord": "· · · · · p P P P f · ·",
    "centro": "· · · · p P P P P f · ·",
    "sud_isole": "· · · p P P P P P P f ·"
  },
  "eufic_climatic_zones": {
    "mediterranean": "f f f p S S S S S S f f",
    "continental": "f f f p S S S P S S S f",
    "atlantic": "· · · p S S S S S S f f",
    "boreal": "· · · f p S S P P S S ·",
    "mountain": "· · · f p S S P S S f ·",
    "pannonian": null
  },
  "derivation_notes": {
    "it": "Fonti: EUFIC, WWF, Greenpeace, Altroconsumo, EUFIC (Italia), Orto da Coltivare (raccolta per area). Stati calcolati per voto tra fonti (metodo in metadata.seasonality_method).",
    "en": "Sources: EUFIC, WWF, Greenpeace, Altroconsumo, EUFIC (Italia), Orto da Coltivare (raccolta per area). States computed by voting across sources (method in metadata.seasonality_method)."
  }
}
```
- `italy_macro_areas` (North, Centre, South and Islands) is the seasonality for Italian users: it comes from a **vote across several sources** (WWF, Greenpeace, Altroconsumo, EUFIC for Italy, Orto da Coltivare harvest periods); the method is in `metadata.seasonality_method`. For each month the sources listing it are counted: with at least half of the votes the month is in season, with fewer it is early or end of season; the **peak** is the central months of a run of at least three months on which all sources agree.
- `eufic_climatic_zones`: the 6 European zones, derived from the EUFIC countries (`eufic_by_country`); where EUFIC lacks the product, the Alpine zone comes from the Austrian calendar (the national source cited by EUFIC) and the Mediterranean zone is derived from the South and Islands. `eufic_zone_sources` gives the provenance of each zone.

## 7. Agricultural (garden) calendar

```json
{
  "nord": {
    "sowing_or_transplant_months": [
      3,
      4,
      5,
      6
    ],
    "harvest_months": [
      6,
      7,
      8,
      9,
      10
    ],
    "seedbed_sowing_months": [
      3,
      4
    ],
    "direct_sowing_months": [
      4,
      5,
      6
    ],
    "transplant_months": [
      5,
      6
    ],
    "cultivation_notes": {
      "it": "Semina in semenzaio mar-apr, semina diretta apr-giu, trapianto mag-giu, raccolta giu-ott (Orto da Coltivare).",
      "en": "Seedbed sowing Mar-Apr, direct sowing Apr-Jun, transplanting May-Jun, harvest Jun-Oct (Orto da Coltivare)."
    }
  },
  "centro": {
    "sowing_or_transplant_months": [
      2,
      3,
      4,
      5,
      6
    ],
    "harvest_months": [
      5,
      6,
      7,
      8,
      9,
      10
    ],
    "seedbed_sowing_months": [
      2,
      3,
      4
    ],
    "direct_sowing_months": [
      3,
      4,
      5,
      6
    ],
    "transplant_months": [
      4,
      5,
      6
    ],
    "cultivation_notes": {
      "it": "Semina in semenzaio feb-apr, semina diretta mar-giu, trapianto apr-giu, raccolta mag-ott (Orto da Coltivare).",
      "en": "Seedbed sowing Feb-Apr, direct sowing Mar-Jun, transplanting Apr-Jun, harvest May-Oct (Orto da Coltivare)."
    }
  },
  "sud_isole": {
    "sowing_or_transplant_months": [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8
    ],
    "harvest_months": [
      4,
      5,
      6,
      7,
      8,
      9,
  …
```
Sowing, transplanting and harvest months by area, with agronomic parameters (depth, spacing, exposure, moon) from Orto da Coltivare. For fruit, herbs and cereals the draft values are still used (documented gap).

## 8. Buying, ripening and storage

This is the richest block. It reads on three levels: **user-facing texts**, **short advice**, **scientific data**.

### 8a. User-facing texts

```json
{
  "buying_guide": {
    "shopping_list_preview": {
      "it": "Pomodoro sodo, colore uniforme e brillante, senza macchie, crepe o raggrinzimenti; profumo intenso.",
      "en": "Firm tomato with even, bright colour, no spots, cracks or wrinkles; intense aroma."
    },
    "detailed_selection": {
      "it": "Scegli pomodori sodi e turgidi, con buccia lucida di colore uniforme, senza macchie, screpolature, ammaccature o raggrinzimenti. Un profumo intenso vicino al picciolo è indice di buona maturazione. I pomodori ancora verdi o invaiati continuano a maturare dopo l'acquisto.",
      "en": "Choose firm, turgid tomatoes with glossy skin of even colour, free of spots, cracks, bruises or wrinkles. A strong aroma near the stem indicates good ripeness. Green or turning tomatoes keep ripening after purchase."
    }
  },
  "card_short_storage": {
    "it": "Ambiente se Acerbo · Frigo se Maturo",
    "en": "Room Temp If Unripe · Fridge If Ripe"
  },
  "ripening_badge_label": {
    "it": "Matura Anche Dopo l'Acquisto",
    "en": "Keeps Ripening After Purchase"
  }
}
```
`card_short_storage` is the short label for the card (≤ 42 characters), consistent with FoodKeeper and UC Davis data; `storage_instructions` is the long text.

### 8b. Short advice for the app

```json
{
  "home_storage": {
    "location": "room_temperature",
    "label": {
      "it": "A Temperatura Ambiente",
      "en": "At Room Temperature"
    },
    "tip": {
      "it": "Una volta tagliato va sempre in frigorifero.",
      "en": "Once cut, always keep it in the fridge."
    },
    "ucdavis_group": "room_temperature_only",
    "foodkeeper_mode": "until_ripe",
    "sources": [
      "uc_davis_storing_guide",
      "usda_foodkeeper"
    ],
    "derivation": {
      "it": "UC Davis / Kader, Storing Fresh Fruits and Vegetables for Better Taste",
      "en": "UC Davis / Kader, Storing Fresh Fruits and Vegetables for Better Taste"
    }
  },
  "perishability": {
    "level": 3,
    "label": {
      "it": "Deperibilità Media",
      "en": "Medium Perishability"
    },
    "tip": {
      "it": "Respira a ritmo medio: conservalo come indicato e consumalo entro pochi giorni da quando è maturo.",
      "en": "It breathes at a moderate rate: store it as advised and eat it within a few days of ripening."
    },
    "basis": {
      "it": "Classe di Kader (USDA HB66, tabella delle classi di respirazione a 5 °C, voce 'tomato')",
      "en": "Kader class (USDA HB66, table of respiration classes at 5 °C, entry 'tomato')"
    }
  }
}
```
- `home_storage.location`: **where** to keep it at home (fridge, on the counter until ripe, room temperature, pantry). Main source: the UC Davis/Kader guide; FoodKeeper for storage times; conflicts between the two sources are written in `derivation`.
- `perishability`: the respiration class turned into a level from 1 to 6, with label and advice. The faster a product respires, the sooner it loses freshness.

```json
{
  "storage_compatibility": {
    "group": "3",
    "label": {
      "it": "Prodotti da Ambiente Fresco (13-18 °C)",
      "en": "Cool Room (13-18 °C)"
    },
    "temperature_c": {
      "min": 13,
      "max": 18
    },
    "humidity_percent": {
      "min": 85,
      "max": 95
    },
    "table_entry": "Tomato, ripe, partially ripe & mature green",
    "match": "exact",
    "compatible_with": [
      "anguria_watermelon",
      "banana_banana",
      "cipolla_invernale_winter_onion",
      "papaya_papaya",
      "patata_dolce_sweet_potato",
      "patata_potato",
      "…"
    ],
    "source": "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf#page=65"
  }
}
```
`storage_compatibility`: which products it can be stored with (same temperature and humidity, no ethylene conflict). Source: HB66, Thompson table.

### 8c. Postharvest scientific data

```json
{
  "optimal_temperature_c": {
    "min": 12.5,
    "max": 15.0
  },
  "optimal_humidity_percent": {
    "min": 90,
    "max": 95
  },
  "respiration_rate_class": "moderate",
  "freezing_point_c": null,
  "chilling_injury": {
    "susceptible": true,
    "critical_temperature_c": 10,
    "symptoms": {
      "it": "Aspetto acquoso e rammollimento, marciume (pomodori verdi maturi (mature-green): 13 °C, colore scarso a maturazione e marciume da Alternaria)",
      "en": "Water soaking and softening, decay"
    },
    "lowest_safe_range_c": {
      "min": 7,
      "max": 10
    }
  },
  "estimated_shelf_life_days": {
    "room_temp_days": [
      7,
      7
    ],
    "refrigerated_days": null,
    "in_freezer_months": 2.0,
    "commercial_optimal_days": null,
    "basis": {
      "it": "Durate domestiche: USDA FoodKeeper 'Tomatoes'. Temperatura ambiente: fino a maturazione (poi 7 giorni), poi in frigorifero. Note FoodKeeper: Until Ripe, then 7 days. Ripe is when this item is tender, fully developed and ready to eat. Refrigeration may affect flavor; USDA recommends pantry storage. commercial_optimal_days: USDA HB66 / UC Davis in condizioni professionali.",
      "en": "Home storage times: USDA FoodKeeper 'Tomatoes'. Room temperature: until ripe (then 7 days), then in the fridge. FoodKeeper notes: Until Ripe, then 7 days. Ripe is when this item is tender, fully developed and ready to eat. Refrigeration may affect flavor; USDA recommends pantry storage. commercial_optimal_days: USDA HB66 / UC Davis under professional conditions."
    },
    "room_temp_mode": "until_ripe",
    "freezing_recommended": true
  },
  "freezing_susceptibility": "most"
}
```
- `ripening_type` (in the `ripening_and_storage` block): `climaterico` (keeps ripening after harvest, e.g. tomato, banana, pear) or `non_climaterico` (stops ripening, e.g. citrus, grape, strawberry); IT/EN labels in `metadata.vocabulary`.
- `freezing_point_c`: HB66's "highest freezing point", the highest temperature at which ice starts to form; for a range the upper end (the most cautious) is used.
- `optimal_temperature_c` and `optimal_humidity_percent`: optimal **commercial** conditions (USDA HB66, UC Davis).
- `chilling_injury`: whether it is chill-sensitive, below which threshold (`critical_temperature_c` = upper end of the lowest safe range, `lowest_safe_range_c`) and with which symptoms. Ripe tomato is sensitive below 7-10 °C (13 °C when still green): that is why it is better kept out of the fridge.
- `estimated_shelf_life_days`: **home** storage times from FoodKeeper (`room_temp_mode` says whether "until ripe" or "fridge only" applies); `commercial_optimal_days` is the shelf life under commercial conditions.

```json
{
  "produces_ethylene": true,
  "ethylene_production_class": "moderate",
  "sensitive_to_ethylene": true,
  "keep_away_from": [
    "melone_melon",
    "kiwi_kiwifruit",
    "lampone_raspberry",
    "mela_apple",
    "pera_pear",
    "pesca_peach",
    "susina_plum",
    "avocado_avocado",
    "pesca_noce_nectarine",
    "maracuja_passion_fruit",
    "mirabella_mirabelle_plum"
  ],
  "compatibility_notes": {
    "it": "Produzione di etilene moderata; sensibile all'etilene: tienilo lontano da melone, kiwi, lampone, mela, pera, pesca, susina, avocado, pesca noce, maracuja, mirabella.",
    "en": "Moderate ethylene production; sensitive to ethylene: keep it away from melon, kiwifruit, raspberry, apple, pear, peach, plum, avocado, nectarine, passion fruit, mirabelle plum."
  }
}
```
Ethylene: whether it produces it (and how much, class at 20 °C) and whether it is sensitive to it. `keep_away_from` is computed: the strong producers in the database to keep it away from, if it is sensitive.

## 9. Nutrition and sustainability

```json
{
  "data_basis": {
    "it": "CREA 006610, integrato con BDA-IEO 390, valori per 100 g di parte edibile",
    "en": "CREA 006610, supplemented with BDA-IEO 390, values per 100 g of edible portion"
  },
  "edible_portion_percentage": 100.0,
  "water_percentage": 94.0,
  "kcal_per_100g": 23.0,
  "macros_per_100g": {
    "carbs_g": 3.5,
    "sugars_g": 3.5,
    "starch_g": 0.0,
    "proteins_g": 1.0,
    "fats_g": 0.2,
    "fiber_g": 2.0,
    "salt_g": 0.015
  }
}
```
Values per 100 g of edible portion. `data_basis` says which record is the primary source (CREA, then BDA-IEO, USDA only when the first two are missing).

```json
{
  "vitamins": [
    {
      "name": "Vitamina A (Retinolo Eq.)",
      "name_en": "Vitamin A (Retinol Eq.)",
      "amount": 610.0,
      "unit": "µg",
      "percent_nrv": 76.2,
      "source": "crea",
      "key": "vitamin_a"
    },
    {
      "name": "Vitamina E",
      "name_en": "Vitamin E",
      "amount": 1.06,
      "unit": "mg",
      "percent_nrv": 8.8,
      "source": "bda_ieo",
      "key": "vitamin_e"
    },
    {
      "name": "Vitamina C",
      "name_en": "Vitamin C",
      "amount": 25.0,
      "unit": "mg",
      "percent_nrv": 31.2,
      "source": "crea",
      "key": "vitamin_c"
    },
    "…"
  ],
  "nutrition_claims_eu": {
    "it": [
      "A Basso Contenuto Calorico",
      "Senza Grassi",
      "A Basso Contenuto di Zuccheri",
      "A Bassissimo Contenuto di Sodio/sale",
      "Ad Alto Contenuto di Fibre",
      "Fonte di Proteine",
      "Ad Alto Contenuto di Vitamina A",
      "Ad Alto Contenuto di Vitamina C"
    ],
    "en": [
      "Low Energy",
      "Fat-free",
      "Low Sugars",
      "Very Low Sodium/salt",
      "High Fibre",
      "Source of Protein",
      "High Vitamin A",
      "High Vitamin C"
    ]
  }
}
```
Every vitamin and mineral has amount, unit, `percent_nrv` (% of the Nutrient Reference Value, Regulation (EU) 1169/2011) and source. **Claims** are computed by applying the thresholds of Regulation (EC) 1924/2006 (e.g. "High in vitamin C" ≥ 30% NRV): they are not written by hand.

```json
{
  "bioactive_compounds": [
    {
      "name": "Licopene",
      "name_en": "Lycopene",
      "amount": 2573.0,
      "unit": "µg",
      "percent_nrv": null,
      "source": "usda_fdc",
      "group": "carotenoidi"
    },
    {
      "name": "Luteina + Zeaxantina",
      "name_en": "Lutein + Zeaxanthin",
      "amount": 123.0,
      "unit": "µg",
      "percent_nrv": null,
      "source": "usda_fdc",
      "group": "carotenoidi"
    },
    {
      "name": "Alfa-carotene",
      "name_en": "Alpha-carotene",
      "amount": 101.0,
      "unit": "µg",
      "percent_nrv": null,
      "source": "usda_fdc",
      "group": "carotenoidi"
    },
    "…"
  ]
}
```
Bioactive compounds: carotenoids (USDA FDC), flavonoid classes (USDA Flavonoid DB), total polyphenols and phenolic acids (Phenol-Explorer). `group` lets the app group them, `main_compounds` says which are the main ones.

```json
{
  "allergens_eu": [],
  "reference_portion": {
    "grams": 200,
    "group": {
      "it": "Verdure e Ortaggi",
      "en": "Vegetables"
    },
    "equivalent": {
      "it": "2-3 Pomodori",
      "en": "2-3 Tomatoes"
    },
    "frequency": {
      "it": "1-2 Porzioni a Pasto",
      "en": "1-2 Portions per Meal"
    },
    "kcal": 46,
    "proteins_g": 2.0,
    "fiber_g": 4.0,
    "source": "https://www.smartfood.ieo.it/media/p02bkul0/smartfood-tab-porzioni-e-frequenze-completa.pdf",
    "match": "exact"
  },
  "protein_reference": {
    "protein_g_per_100g": 1.0,
    "percent_pri_larn_adult_m": 1.6,
    "percent_pri_larn_adult_f": 1.9,
    "percent_pri_larn_over65_m": 1.3,
    "percent_pri_larn_over65_f": 1.5,
    "percent_ri_eu": 2.0,
    "energy_from_protein_percent": 17.4,
    "claim_note": {
      "it": "Claim conforme al Reg. CE 1924/2006 (il 17.4% delle calorie viene dalle proteine), ma in valore assoluto 100 g forniscono 1.0 g di proteine, circa il 1.9% del fabbisogno giornaliero raccomandato (LARN, donna adulta).",
      "en": "Claim compliant with Reg. (EC) 1924/2006 (17.4% of calories from protein), but in absolute terms 100 g provide 1.0 g of protein, about 1.9% of the recommended daily intake (Italian LARN, adult woman)."
    }
  }
}
```
- `allergens_eu`: allergens from Annex II of Regulation (EU) 1169/2011 (empty list = none).
- `reference_portion`: the standard LARN portion (via IEO SmartFood), with a practical equivalent and per-portion values.
- `protein_reference`: protein compared with the LARN requirement.

```json
{
  "carbon_kg_co2eq_per_kg": 0.45,
  "carbon_g_co2eq_per_portion": 91,
  "carbon_reference": {
    "value": 0.4541,
    "sel_name": "TOMATO",
    "level": "item",
    "uncertainty": "L",
    "sel_note": "OK item",
    "typology": "VEGETABLES OPENFIELD",
    "n_values": 68,
    "min": 0.15,
    "max": 2.29
  },
  "water_l_per_kg": 41,
  "water_l_per_portion": 8,
  "water_reference": {
    "value": 41.0,
    "sel_name": "TOMATO",
    "level": "item",
    "uncertainty": "L",
    "sel_note": "ok item",
    "typology": "VEGETABLES",
    "n_values": 6,
    "min": 5.0,
    "max": 214.0
  },
  "greenhouse_comparison": {
    "carbon_kg_co2eq_per_kg": 2.42,
    "sel_name": "TOMATO (G)",
    "heated": true,
    "times_openfield": 5.3
  },
  "match": "exact",
  "source": "https://doi.org/10.1038/s41597-021-00909-8",
  "sustainability_rating": {
    "carbon_level": "low",
    "water_level": "low",
    "carbon_label": {
      "it": "Impronta di carbonio bassa",
      "en": "Low carbon footprint"
    },
    "water_label": {
      "it": "Impronta idrica bassa",
      "en": "Low water footprint"
    },
    "times_lower_than_beef_carbon": 57,
    "times_lower_than_beef_water": 369,
    "tips": {
      "it": "Coltivato in serra riscaldata (tipico fuori stagione) ha un'impronta di carbonio 5,3 volte più alta: sceglilo di stagione e di pieno campo.",
      "en": "Grown in a heated greenhouse (typical out of season) its carbon footprint is 5.3 times higher: choose it in season and field-grown."
    },
    "basis": {
      "it": "Livelli: carbonio basso < 0,5, medio 0,5-1, alto > 1 kg CO2eq/kg; acqua bassa < 500, media 500-1500, alta > 1500 L/kg (soglie di lettura definite per l'app). Confronto con 'BEEF BONE FREE MEAT' SU-EATABLE LIFE (25.8 kg CO2eq/kg, 15139 L/kg).",
      "en": "Levels: carbon low < 0.5, medium 0.5-1, high > 1 kg CO2eq/kg; water low < 500, medium 500-1500, high > 1500 L/kg (reading thresholds defined for the app). Compared with 'BEEF BONE FREE MEAT' SU-EATABLE LIFE (25.8 kg CO2eq/kg, 15139 L/kg)."
    }
  }
}
```
Sustainability (SU-EATABLE LIFE): CO2 and water per kg and per portion, with the database entry, number of studies and range. `greenhouse_comparison` shows the weight of heated greenhouses (out of season). `sustainability_rating` turns the numbers into levels and advice.

```json
{
  "count": 78,
  "regions": [
    "Abruzzo",
    "Basilicata",
    "Calabria",
    "Campania",
    "Emilia Romagna",
    "Lazio",
    "…"
  ],
  "products": [
    {
      "name": "Conserve di pomodoro (polpa e pezzetti di pomodoro)",
      "region": "Abruzzo"
    },
    {
      "name": "Pomodoro a pera",
      "region": "Abruzzo"
    },
    {
      "name": "Passata di pomodoro di Rotonda",
      "region": "Basilicata"
    },
    {
      "name": "Pomodorino giallo costoluto di Castronuovo di Sant'Andrea",
      "region": "Basilicata"
    },
    "…"
  ],
  "source": "https://www.masaf.gov.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/24151",
  "revision": "XXVI (2026)"
}
```
`traditional_products_pat`: the Traditional Agri-food Products from the MASAF list linked to the product, with their region.

```json
{
  "health_benefits_and_curiosities": {
    "it": "Per 100 g è ricco di vitamina A (come caroteni) e di vitamina C, con pochissime calorie. Il colore rosso è dovuto al licopene, che si assorbe meglio quando il pomodoro è cotto con un po' d'olio.",
    "en": "Per 100 g it is high in vitamin A (as carotenes) and vitamin C, with very few calories. Its red colour comes from lycopene, which is better absorbed when the tomato is cooked with a little oil."
  },
  "culinary_waste_reduction": {
    "it": "Mangialo con la buccia, ricca di fibre. I pomodori troppo maturi sono perfetti per sughi veloci, passate e gazpacho; le bucce e i semi avanzati insaporiscono brodi.",
    "en": "Eat the skin, which is rich in fibre. Over-ripe tomatoes are perfect for quick sauces, passata and gazpacho; leftover skins and seeds flavour stocks."
  }
}
```
Texts: benefits (only with nutrients consistent with the claims) and anti-waste ideas.

## 10. Record sources

```json
{
  "sources_used": [
    {
      "source_key": "crea",
      "name": "CREA Alimenti e Nutrizione - Tabelle di composizione degli alimenti (rev. 2019)",
      "topics": [
        "nutrition",
        "texts"
      ],
      "urls": [
        "https://www.alimentinutrizione.it/tabelle-nutrizionali/006610"
      ],
      "local_files": []
    },
    {
      "source_key": "bda_ieo",
      "name": "BDA-IEO - Banca Dati di Composizione degli Alimenti (Istituto Europeo di Oncologia)",
      "topics": [
        "nutrition"
      ],
      "urls": [
        "https://bda.ieo.it/?page_id=87"
      ],
      "local_files": []
    },
    {
      "source_key": "usda_fdc",
      "name": "USDA FoodData Central - SR Legacy (2018-04)",
      "topics": [
        "bioactive_compounds"
      ],
      "urls": [
        "https://fdc.nal.usda.gov/food-details/170457/nutrients"
      ],
      "local_files": []
    },
    "…"
  ],
  "useful_links": [
    {
      "title": {
        "it": "Stagionalità, Scelta e Conservazione - Altroconsumo",
        "en": "Seasonality, Choosing and Storage - Altroconsumo (IT)"
      },
      "url": "https://www.altroconsumo.it/alimentazione/fare-la-spesa/consigli/calendario-frutta-verdura/pomodoro",
      "source_key": "altroconsumo",
      "topic": "seasonality"
    },
    {
      "title": {
        "it": "Come Coltivarlo nell'Orto - Orto da Coltivare",
        "en": "How to Grow It - Orto Da Coltivare (IT)"
      },
      "url": "https://www.ortodacoltivare.it/ortaggi/pomodoro/",
      "source_key": "ortodacoltivare",
      "topic": "agricultural_calendar"
    },
    {
      "title": {
        "it": "Tabella Nutrizionale - CREA Alimenti e Nutrizione",
        "en": "Nutrition Table - CREA (IT)"
      },
      "url": "https://www.alimentinutrizione.it/tabelle-nutrizionali/006610",
      "source_key": "crea",
      "topic": "nutrition"
    },
    "…"
  ]
}
```
`sources_used` lists **all** the sources used for this product (27 for the tomato), with topic, URL and local files. `useful_links` are the links shown to the user (12). `source_codes` holds the exact record codes (CREA, BDA, FDC…).

## 11. Traceability: `data_completeness`

```json
{
  "is_complete": false,
  "fields_pending_verification": [],
  "missing_fields": [
    "names.synonyms",
    "ripening_and_storage.postharvest_physiology.estimated_shelf_life_days.commercial_optimal_days",
    "ripening_and_storage.postharvest_physiology.freezing_point_c",
    "seasonality.eufic_climatic_zones.pannonian"
  ],
  "not_applicable_fields": [
    "botany.upov_note",
    "nutrition_and_sustainability.allergens_note",
    "ripening_and_storage.postharvest_physiology.estimated_shelf_life_days.refrigerated_days"
  ],
  "discrepancies": [
    {
      "field": "nutrition_and_sustainability.kcal_per_100g",
      "draft_value": 19.0,
      "source_value": 23.0,
      "source": "CREA 006610",
      "resolution": "adottato il valore della fonte ufficiale"
    },
    {
      "field": "nutrition_and_sustainability.macros_per_100g.sugars_g",
      "draft_value": 2.8,
      "source_value": 3.5,
      "source": "CREA 006610",
      "resolution": "adottato il valore della fonte ufficiale"
    }
  ],
  "notes": "Immagini: i file PNG indicati dalla bozza non esistono; i riferimenti Commons sono in draft_legacy_values.json come candidati per il download. Stagionalità EUFIC a 6 zone della bozza NON proveniente da EUFIC (che pubblica dati per Paese): rimossa e conservata in draft_legacy_values.json; verrà ricalcolata dai dati EUFIC reali. Voci della lista 'vitamine' della bozza riclassificate (minerali o comp…"
}
```
This block is for maintainers, not for users: it says what came from the draft, what was verified, what is missing, what is not applicable, where the draft differed from the sources (`discrepancies`, with draft value, source value and source) and why (`notes`, an internal log written in Italian).

## 12. Metadata

`metadata` holds everything that applies to the whole database and sits at the top of the file:

- `app_title`
- `version`
- `generated`
- `schema_version`
- `sustainable_diet_summary`
- `official_sources`
- `seasonality_states_legend`
- `eufic_climatic_zones_legend`
- `italy_macro_areas_legend`
- `generation_log`
- `seasonality_method`
- `postharvest_method`
- `protein_reference_method`
- `perishability_legend`
- `home_storage_legend`
- `environmental_footprint_method`
- `storage_compatibility_legend`
- `glossary`
- `vocabulary`
- `field_help`
- `source_conflicts`
- `seasonality_estimates_method`
- `icon_set`
- `seasonality_reference_order`
- `seasonality_display_rules`
- `ethylene_rules`
- `seasonality_curve_method`
- `nutrition_claims_eu_rules`
- `detail_display_rules`

The **legends** (seasonal states, zones, perishability, storage, compatibility groups) and the **methods** (seasonality, postharvest, protein, footprints) are designed to be read directly by the app.

## 13. Bilingualism

The app can be used entirely in Italian or entirely in English:

- every user-facing text is `{"it": …, "en": …}`, including the rationales (`basis`, `derivation`, `method`, variety notes);
- coded values (e.g. `climaterico`, `in_season`, `fridge`) are keys: the label to display is in `metadata.vocabulary`;
- nutrients and compounds have `name` and `name_en`;
- only proper names stay in their original language (varieties, PDO/PGI, PAT, scientific names, authors, licences, sources);
- `data_completeness.notes` is a technical log in Italian, not used by the app.

```json
{
  "ripening_and_storage.ripening_type": {
    "_glossary": null,
    "climaterico": {
      "it": "Climaterico",
      "en": "Climacteric",
      "glossary": "climacteric"
    },
    "non_climaterico": {
      "it": "Non Climaterico",
      "en": "Non-climacteric",
      "glossary": "non_climacteric"
    }
  }
}
```
Vocabulary groups (24): `category`, `botany.plant_part_used`, `seasonality.state`, `seasonality.italy_macro_areas`, `seasonality.eufic_climatic_zones`, `seasonality.estimates`, `seasonality.estimates.from`, `month`, `ripening_and_storage.ripening_type`, `ripening_and_storage.primary_location`, `class_scale`, `ripening_and_storage.postharvest_physiology.freezing_susceptibility`, `ripening_and_storage.home_storage.location`, `ripening_and_storage.postharvest_physiology.estimated_shelf_life_days.room_temp_mode`, `ripening_and_storage.storage_compatibility.group`, `agricultural_calendar_italy.agronomic_params.sun_exposure`, `agricultural_calendar_italy.agronomic_params.lunar_phase_advice`, `images.image_details.view_type`, `botany.upov_register`, `nutrition_and_sustainability.bioactive_compounds.group`, `sustainability_level`, `match`, `nutrition_and_sustainability.allergens_eu.annex_ii_number`, `botany.family`.

## 14. Glossary and "?" icons

Explanations are written once, in `metadata.glossary`, and reached from several places:

| From | Field | Example |
|---|---|---|
| a field | `metadata.field_help[path]` | `ripening_and_storage.ripening_type` → `climacteric`, `non_climacteric` |
| a value | `metadata.vocabulary[group][value].glossary` | `climaterico` → `climacteric` |
| a product | `item.help_refs` | broad bean → `favism` on the benefits text |
| another entry | `glossary[id].see_also` | `climacteric` → `ethylene`, `non_climacteric` |
| a source | `official_sources[].used_for.glossary_entries` | HB66 → storage entries |

```json
{
  "term": {
    "it": "Frutto Climaterico",
    "en": "Climacteric Fruit"
  },
  "short": {
    "it": "Continua a maturare dopo la raccolta, producendo etilene.",
    "en": "Keeps ripening after harvest, producing ethylene."
  },
  "text": {
    "it": "Un frutto climaterico, dopo la raccolta, aumenta la respirazione e produce etilene, che a sua volta ne fa produrre altro: così continua a maturare, si ammorbidisce e diventa più dolce e profumato anche in casa. Esempi: pomodoro, banana, pera, pesca, kiwi, avocado. Non tutti però producono tanto etilene: il cachi ne produce poco, il pomodoro una quantità media. Si può comprare un po' acerbo e farlo maturare fuori dal frigo, anche in un sacchetto di carta con una mela.",
    "en": "After harvest a climacteric fruit increases its respiration and produces ethylene, which in turn stimulates more ethylene: so it keeps ripening, softening and getting sweeter and more aromatic at home. Examples: tomato, banana, pear, peach, kiwifruit, avocado. Not all of them produce much ethylene, though: persimmon produces little, tomato a medium amount. It can be bought slightly unripe and ripened out of the fridge, also in a paper bag with an apple."
  },
  "sources": [
    {
      "key": "uc_davis",
      "name": "UC Davis Postharvest Research and Extension Center - Produce Fact Sheets",
      "url": "https://postharvest.ucdavis.edu/produce-facts-sheets",
      "publisher": {
        "it": "UC Davis",
        "en": "UC Davis"
      },
      "title": {
        "it": "Schede Post-Raccolta dei Prodotti",
        "en": "Produce Fact Sheets"
      },
      "favicon": "uc_davis.png"
    },
    {
      "key": "usda_hb66",
      "name": "USDA ARS Agricultural Handbook 66 (2016)",
      "url": "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf",
      "publisher": {
        "it": "USDA ARS",
        "en": "USDA ARS"
      },
      "title": {
        "it": "Agricultural Handbook 66 - Conservazione Commerciale",
        "en": "Agricultural Handbook 66 - Commercial Storage"
      },
      "favicon": "usda_hb66.png"
    },
    {
      "key": "uc_davis_storing_guide",
      "name": "UC Davis / Kader - Storing Fresh Fruits and Vegetables for Better Taste (UC ANR Pub. 21590)",
      "url": "https://homeorchard.ucanr.edu/files/115275.pdf",
      "publisher": {
        "it": "UC Davis",
        "en": "UC Davis"
      },
      "title": {
        "it": "Conservare Frutta e Verdura per un Gusto Migliore",
  …
```
Each entry: `term`, `short` (one line for the tooltip), `text` (full explanation), `sources` (name and URL from the catalogue), `see_also`. Entries (44): `climacteric`, `non_climacteric`, `ethylene`, `ethylene_production`, `ethylene_sensitivity`, `keep_away_from`, `respiration_rate`, `perishability`, `q10`, `chilling_injury`, `lowest_safe_temperature`, `freezing_point`, `freezing_susceptibility`, `optimal_storage`, `shelf_life_home`, `home_storage`, `storage_compatibility`, `seasonality_states`, `italy_macro_areas`, `eufic_zones`, `seasonality_estimate`, `sowing_transplant`, `agronomic_params`, `edible_portion`, `nrv`, `nutrition_claims`, `larn`, `reference_portion`, `allergens`, `gluten`, `carotenoids`, `polyphenols`, `flavonoids`, `carbon_footprint`, `water_footprint`, `greenhouse`, `dop_igp`, `pat`, `slow_food`, `upov_variety_register`, `varieties`, `scientific_name`, `favism`, `data_quality`.

```json
{
  "help_refs": [
    {
      "glossary_id": "carotenoids",
      "fields": [
        "nutrition_and_sustainability.health_benefits_and_curiosities"
      ]
    },
    {
      "glossary_id": "chilling_injury",
      "fields": [
        "ripening_and_storage.postharvest_physiology.chilling_injury"
      ]
    },
    {
      "glossary_id": "climacteric",
      "fields": [
        "ripening_and_storage.ripening_type"
      ]
    },
    {
      "glossary_id": "dop_igp",
      "fields": [
        "buying_guide.detailed_selection",
        "italian_varieties_and_territories.dop_igp_labels"
      ]
    },
    {
      "glossary_id": "ethylene",
      "fields": [
        "ripening_and_storage.ethylene_compatibility.compatibility_notes"
      ]
    },
    {
      "glossary_id": "greenhouse",
      "fields": [
        "nutrition_and_sustainability.environmental_footprint.greenhouse_comparison"
      ]
    }
  ]
}
```
```json
{
  "field_help": {
    "ripening_and_storage.ripening_type": [
      "climacteric",
      "non_climacteric"
    ],
    "ripening_and_storage.ripening_badge_label": [
      "climacteric",
      "non_climacteric"
    ],
    "ripening_and_storage.home_storage": [
      "home_storage"
    ],
    "ripening_and_storage.card_short_storage": [
      "home_storage",
      "shelf_life_home"
    ],
    "ripening_and_storage.perishability": [
      "perishability",
      "respiration_rate"
    ],
    "ripening_and_storage.storage_compatibility": [
      "storage_compatibility"
    ]
  }
}
```
## 15. Source catalogue

`metadata.official_sources` describes every source: what it is (`description`), why it is authoritative (`authority`), what it offers (`offers`), for which topics and which products it was consulted (`used_for`). Full list:

### Regolamento (UE) n. 1169/2011 - Allegato XIII, Valori Nutritivi di Riferimento

`reg_1169_2011` · https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32011R1169

- **What it is**: Regulation (EU) No 1169/2011 on product information to consumers.
- **Why it is authoritative**: Binding EU law on product labelling.
- **What it offers**: Nutrient Reference Values (Annex XIII) for percentages and the list of 14 allergens (Annex II).
- **Used for**: Allergens, %NRV
- **Products (153)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Glossary entries**: allergens, gluten, nrv, nutrition_claims

### IEO SmartFood - Porzioni e frequenze (porzioni standard LARN-SINU)

`ieo_smartfood_portions` · https://www.smartfood.ieo.it/media/p02bkul0/smartfood-tab-porzioni-e-frequenze-completa.pdf

- **What it is**: 'Portions and frequencies' table of the European Institute of Oncology's SmartFood programme.
- **Why it is authoritative**: It presents the LARN-SINU standard portions in practical form, with household equivalents.
- **What it offers**: Portion grams by product group, equivalents ('2-3 tomatoes') and consumption frequencies.
- **Used for**: Portions
- **Products (153)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Glossary entries**: reference_portion

### EPPO Global Database

`eppo` · https://gd.eppo.int/

- **What it is**: EPPO Global Database of the European and Mediterranean Plant Protection Organization.
- **Why it is authoritative**: An intergovernmental organisation; its codes are the standard for identifying plants in Europe.
- **What it offers**: Preferred scientific name, EPPO code and official common names in Italian and English.
- **Used for**: Botany
- **Products (151)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: scientific_name

### Regolamento (CE) n. 1924/2006 - indicazioni nutrizionali e sulla salute

`reg_1924_2006` · https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32006R1924

- **What it is**: Regulation (EC) No 1924/2006 on nutrition and health claims.
- **Why it is authoritative**: It is the binding EU law setting which nutrition claims may be used and with which thresholds.
- **What it offers**: The thresholds for 'source of', 'high in' and 'low in' claims.
- **Used for**: EU Claims
- **Products (146)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Glossary entries**: nutrition_claims

### LARN - SINU (tabelle riassuntive, PDF locale)

`larn_sinu` · https://sinu.it/tabelle-larn-2014/

- **What it is**: LARN - Italian Reference Intake Levels of Nutrients and energy, Italian Society of Human Nutrition (4th revision, 2014).
- **Why it is authoritative**: They are the official reference values for the Italian population.
- **What it offers**: Protein requirements used to put protein claims in context.
- **Used for**: LARN
- **Products (145)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Glossary entries**: larn, reference_portion

### World Flora Online - Plant List

`wfo` · https://list.worldfloraonline.org/

- **What it is**: World Flora Online, the global catalogue of plant species.
- **Why it is authoritative**: An international project of the leading botanic gardens, successor to The Plant List.
- **What it offers**: Accepted name, family and genus.
- **Used for**: Botany
- **Products (143)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, taccola_snow_pea, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Glossary entries**: scientific_name

### USDA FoodData Central - SR Legacy (2018-04)

`usda_fdc` · https://fdc.nal.usda.gov/

- **What it is**: USDA FoodData Central, SR Legacy release (2018), US Department of Agriculture.
- **Why it is authoritative**: It is the US national composition database, in the public domain and among the most used worldwide.
- **What it offers**: Carotenoids (lycopene, lutein, etc.), absent from Italian tables, and nutrients for a few produce without a CREA or BDA-IEO entry.
- **Used for**: Bioactive Compounds, Nutrition, Texts
- **Products (136)**: aglio_garlic, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Glossary entries**: carotenoids

### USDA ARS Agricultural Handbook 66 (2016)

`usda_hb66` · https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf

- **What it is**: USDA Agriculture Handbook 66 'The Commercial Storage of Fruits, Vegetables, and Florist and Nursery Stocks' (2016).
- **Why it is authoritative**: It is the international reference technical manual on fresh produce storage, with chapters written by specialists for each product.
- **What it offers**: Optimal conditions, respiration (Kader classes), ethylene, chilling injury, freezing point, compatible storage groups.
- **Used for**: Chilling Injury, Freezing_susceptibility, Plant_part_used, Postharvest, Compatible Storage, Texts, Varieties
- **Products (133)**: aglio_garlic, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gombo_okra, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Glossary entries**: chilling_injury, climacteric, ethylene, ethylene_production, ethylene_sensitivity, freezing_point, freezing_susceptibility, keep_away_from, lowest_safe_temperature, non_climacteric, optimal_storage, perishability, q10, respiration_rate, storage_compatibility

### SU-EATABLE LIFE - database delle impronte di carbonio e idrica (Petersson et al. 2021)

`su_eatable_life` · https://doi.org/10.1038/s41597-021-00909-8

- **What it is**: SU-EATABLE LIFE, database of the carbon and water footprints of produce (Petersson et al., Scientific Data, 2021).
- **Why it is authoritative**: Produced by an EU-funded LIFE project, published in a peer-reviewed journal; it harmonises over 800 studies.
- **What it offers**: Carbon and water footprint per kg, comparing open field, greenhouse and imported produce.
- **Used for**: Environmental Footprint
- **Products (129)**: aglio_garlic, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, daikon_daikon, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, gelso_mulberry, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salvia_sage, scalogno_shallot, scarola_escarole, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, susina_plum, taccola_snow_pea, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: carbon_footprint, greenhouse, water_footprint

### Wikimedia Commons API

`wikimedia` · https://commons.wikimedia.org/w/api.php

- **What it is**: Wikimedia Commons.
- **Why it is authoritative**: An archive of images with verifiable free licences.
- **What it offers**: Photos with author and licence (CC0, CC BY, CC BY-SA, public domain).
- **Used for**: Images
- **Products (124)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, broccolo_romanesco_romanesco, cachi_persimmon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pisello_pea, pistacchio_pistachio, pompelmo_grapefruit, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, rafano_horseradish, rapa_turnip, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, spinacio_spinach, spugnola_morel, susina_plum, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote

### Pixabay API

`pixabay` · https://pixabay.com/

- **What it is**: Pixabay.
- **Why it is authoritative**: An image bank under the Pixabay Content License.
- **What it offers**: High-resolution photos.
- **Used for**: Images
- **Products (124)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicerchia_grass_pea, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, erba_cipollina_chives, fagiolino_green_bean, farro_emmer, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, prezzemolo_parsley, rabarbaro_rhubarb, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, salvia_sage, sambuco_elderberry, scalogno_shallot, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, susina_plum, timo_thyme, uva_spina_gooseberry, uva_table_grape, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini

### BDA-IEO - Banca Dati di Composizione degli Alimenti (Istituto Europeo di Oncologia)

`bda_ieo` · https://bda.ieo.it/

- **What it is**: Food Composition Database for Epidemiological Studies in Italy, European Institute of Oncology.
- **Why it is authoritative**: A scientific database that brings together and harmonises Italian and international tables, citing the original source of every value.
- **What it offers**: Nutrients missing from the CREA tables and produce not in CREA (e.g. raw sweet corn).
- **Used for**: Nutrition, Texts
- **Products (121)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_rosso_red_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, salvia_sage, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, spugnola_morel, susina_plum, tartufo_nero_black_truffle, timo_thyme, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: edible_portion

### USDA FSIS FoodKeeper

`usda_foodkeeper` · https://www.foodsafety.gov/keep-food-safe/foodkeeper-app

- **What it is**: USDA FSIS FoodKeeper, a database on home product storage.
- **Why it is authoritative**: An official tool of the US Food Safety and Inspection Service, developed with Cornell University.
- **What it offers**: Pantry, fridge and freezer times from the purchase date, with practical notes.
- **Used for**: Home Storage, Texts
- **Products (120)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, carciofo_artichoke, cardoncello_king_oyster_mushroom, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, clementine_clementine, crescione_watercress, daikon_daikon, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, finferlo_chanterelle, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mango_mango, maracuja_passion_fruit, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, sambuco_elderberry, scalogno_shallot, scarola_escarole, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, timo_thyme, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: home_storage, shelf_life_home

### MASAF - Elenco nazionale dei Prodotti Agroalimentari Tradizionali, XXVI revisione (2026)

`masaf_pat` · https://www.masaf.gov.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/24151

- **What it is**: National list of Traditional Agri-food Products of the Italian Ministry of Agriculture (26th revision, 2026).
- **Why it is authoritative**: An official list updated every year on the Regions' proposals.
- **What it offers**: The regional traditional products linked to each product.
- **Used for**: Texts, Traditional Products
- **Products (118)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, anguria_watermelon, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, grano_duro_durum_wheat, grano_saraceno_buckwheat, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, mandarino_mandarin, mandorla_almond, mango_mango, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mirtillo_rosso_lingonberry, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_table_grape, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: pat

### EUFIC - Explore seasonal fruit and vegetables in Europe

`eufic_map` · https://www.eufic.org/en/explore-seasonal-fruit-and-vegetables-in-europe

- **What it is**: EUFIC interactive map of seasonal fruit and vegetables in Europe.
- **Why it is authoritative**: The European Food Information Council is a non-profit organisation that communicates science-based information on product and health.
- **What it offers**: In-season months by European country, aggregated by climate zone.
- **Used for**: European Seasonality, Texts
- **Products (115)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, cicoria_da_cespo_chicory, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, crescione_watercress, daikon_daikon, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, limone_lemon, mais_corn, mandarino_mandarin, mango_mango, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, oliva_olive, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rucola_arugula, salicornia_samphire, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Glossary entries**: eufic_zones, italy_macro_areas, seasonality_estimate, seasonality_states

### Orto da Coltivare (Matteo Cereda) - tabelle di semina PDF + schede

`ortodacoltivare` · https://www.ortodacoltivare.it/calendario/calendario-delle-raccolte/

- **What it is**: Orto da Coltivare, Matteo Cereda's website and sowing tables (local PDFs for North, Centre, South).
- **Why it is authoritative**: A widely used Italian reference for home gardens, with tables by climate area.
- **What it offers**: Sowing, transplanting and harvest months by macro-area and growing parameters.
- **Used for**: Growing Calendar, Plant_part_used, Seasonality, Texts, Varieties
- **Products (110)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, crescione_watercress, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, indivia_belga_belgian_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, mais_corn, mandarino_mandarin, mandorla_almond, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, timo_thyme, topinambur_jerusalem_artichoke, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Glossary entries**: agronomic_params, italy_macro_areas, seasonality_states, sowing_transplant, varieties

### CREA Alimenti e Nutrizione - Tabelle di composizione degli alimenti (rev. 2019)

`crea` · https://www.alimentinutrizione.it/tabelle-nutrizionali/ricerca-per-alimento

- **What it is**: Food composition tables of CREA - Research Centre for Food and Nutrition (2019 revision).
- **Why it is authoritative**: It is the public research body of the Italian Ministry of Agriculture and maintains Italy's national reference product composition database.
- **What it offers**: Energy, water, macronutrients, vitamins, minerals and edible portion per 100 g of raw product.
- **Used for**: Nutrition, Texts
- **Products (109)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, litchi_lychee, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, orzo_barley, papaya_papaya, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salvia_sage, scarola_escarole, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, tartufo_nero_black_truffle, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: edible_portion

### My-PersonalTrainer

`my_personaltrainer` · https://www.my-personaltrainer.it/frutta-verdura-di-stagione.htm

- **What it is**: My-PersonalTrainer, an Italian popular-science portal on nutrition and health.
- **Why it is authoritative**: A popular-science source included in the project brief; not a primary source.
- **What it offers**: Only cues for texts and further-reading links: no numerical value is taken from it.
- **Used for**: Plant_part_used, Varieties, Verification_texts
- **Products (109)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_porcino_porcini_mushroom, grano_saraceno_buckwheat, indivia_belga_belgian_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nocciola_hazelnut, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, radicchio_radicchio, rafano_horseradish, ravanello_radish, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, taccola_snow_pea, timo_thyme, topinambur_jerusalem_artichoke, uva_table_grape, zafferano_saffron, zucca_pumpkin, zucchina_zucchini

### UC Davis / Kader - Storing Fresh Fruits and Vegetables for Better Taste (UC ANR Pub. 21590)

`uc_davis_storing_guide` · https://homeorchard.ucanr.edu/files/115275.pdf

- **What it is**: 'Storing Fresh Fruits and Vegetables for Better Taste' guide (A. Kader, J. Thompson, K. Sylva, L. Harris), UC ANR Pub. 21590.
- **Why it is authoritative**: An official University of California extension publication by leading postharvest experts.
- **What it offers**: Where to keep each product at home: fridge, ripen on the counter, room temperature only.
- **Used for**: Home Storage
- **Products (107)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardoncello_king_oyster_mushroom, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, fico_fig, finferlo_chanterelle, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, mais_corn, mandarino_mandarin, mango_mango, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, papaya_papaya, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, radicchio_radicchio, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, sedano_celery, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, timo_thyme, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: climacteric, ethylene, keep_away_from

### USDA Database for the Flavonoid Content of Selected Foods, Release 3.3 (2018)

`usda_flavonoids` · https://www.ars.usda.gov/northeast-area/beltsville-md-bhnrc/beltsville-human-nutrition-research-center/methods-and-application-of-food-composition-laboratory/mafcl-site-pages/flavonoids/

- **What it is**: USDA Database for the Flavonoid Content of Selected Foods, Release 3.3 (2018).
- **Why it is authoritative**: A database from USDA's composition laboratory, built from analytical studies selected with quality criteria.
- **What it offers**: Content of anthocyanins, flavonols, flavones, flavanones and catechins.
- **Used for**: Bioactive Compounds
- **Products (97)**: aglio_garlic, albicocca_apricot, amarena_sour_cherry, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avocado_avocado, banana_banana, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, crescione_watercress, erba_cipollina_chives, fagiolino_green_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_saraceno_buckwheat, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, mandarino_mandarin, mandorla_almond, mango_mango, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nocciola_hazelnut, noce_walnut, origano_oregano, orzo_barley, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salvia_sage, sambuco_elderberry, scarola_escarole, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, timo_thyme, uva_spina_gooseberry, uva_table_grape, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: flavonoids, polyphenols

### Phenol-Explorer 3.6 - database del contenuto di polifenoli negli alimenti (INRA)

`phenol_explorer` · http://phenol-explorer.eu/

- **What it is**: Phenol-Explorer 3.6, database of polyphenols in produce (INRA, France).
- **Why it is authoritative**: A scientific database cited in international literature, collecting data from hundreds of publications with the analytical method.
- **What it offers**: Total polyphenols (Folin assay), phenolic acids, stilbenes and other polyphenols. Non-commercial use with citation.
- **Used for**: Bioactive Compounds
- **Products (86)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, carciofo_artichoke, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, clementine_clementine, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, grano_duro_durum_wheat, grano_saraceno_buckwheat, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, litchi_lychee, mandarino_mandarin, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nespola_loquat, origano_oregano, orzo_barley, papaya_papaya, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pomodoro_tomato, pompelmo_grapefruit, prezzemolo_parsley, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salvia_sage, scalogno_shallot, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, timo_thyme, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: flavonoids, polyphenols

### UC Davis Postharvest Research and Extension Center - Produce Fact Sheets

`uc_davis` · https://postharvest.ucdavis.edu/produce-facts-sheets

- **What it is**: Postharvest fact sheets of the University of California, Davis Postharvest Research and Extension Center.
- **Why it is authoritative**: A world-leading research centre on postharvest physiology (fact sheets edited by A. Kader and colleagues).
- **What it offers**: Optimal temperature and humidity, ethylene, chilling injury, climacteric classification.
- **Used for**: Postharvest, Texts
- **Products (80)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, avocado_avocado, banana_banana, basilico_basil, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_rosso_red_cabbage, cetriolo_cucumber, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, clementine_clementine, fagiolino_green_bean, fico_d_india_prickly_pear, fico_fig, fragola_strawberry, fungo_champignon_button_mushroom, giuggiola_jujube, gombo_okra, indivia_belga_belgian_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nespola_loquat, oliva_olive, origano_oregano, papaya_papaya, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, prezzemolo_parsley, radicchio_radicchio, ravanello_radish, ribes_redcurrant, rosmarino_rosemary, salvia_sage, sedano_celery, spinacio_spinach, susina_plum, taccola_snow_pea, timo_thyme, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: chilling_injury, climacteric, ethylene, ethylene_sensitivity, home_storage, non_climacteric, optimal_storage

### EU Plant Variety Portal - Catalogo comune UE delle varieta' (agricole, ortive, frutticole)

`eu_plant_variety_portal` · https://ec.europa.eu/food/plant-variety-portal/

- **What it is**: EU Plant Variety Portal, the EU Common Catalogue of varieties of agricultural, vegetable and fruit species.
- **Why it is authoritative**: The European Commission's official database gathering the national variety registers.
- **What it offers**: UPOV species codes, variety verification and the number of varieties listed in Italy.
- **Used for**: UPOV Code, Varieties
- **Products (76)**: aglio_garlic, albicocca_apricot, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_broccoli, carciofo_artichoke, cardo_cardoon, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, clementine_clementine, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, grano_duro_durum_wheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, mais_corn, mandarino_mandarin, mela_apple, mela_cotogna_quince, melanzana_eggplant, melone_melon, mirtillo_blueberry, mora_blackberry, orzo_barley, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_redcurrant, riso_rice, scalogno_shallot, scarola_escarole, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, valerianella_corn_salad, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: upov_variety_register, varieties

### Bio Suisse - Calendario stagionale (Svizzera, PDF locale)

`biosuisse` · https://bio-suisse.ch/calendariostagionale

- **What it is**: Seasonal calendar of Bio Suisse, the federation of Swiss organic farms (local PDF).
- **Why it is authoritative**: The reference body for organic farming in Switzerland; useful as a reference for the Alpine climate.
- **What it offers**: In-season months for Alpine and mountain areas.
- **Used for**: Seasonality, Texts
- **Products (71)**: aglio_garlic, albicocca_apricot, asparago_asparagus, barbabietola_beetroot, basilico_basil, broccolo_broccoli, carciofo_artichoke, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, cicoria_da_cespo_chicory, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, erba_cipollina_chives, fagiolo_bean, finocchio_fennel, fragola_strawberry, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, mais_corn, mela_apple, mela_cotogna_quince, melanzana_eggplant, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, noce_walnut, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, porro_leek, prezzemolo_parsley, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rucola_arugula, sambuco_elderberry, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, taccola_snow_pea, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_zucchini

### Altroconsumo - Calendario frutta e verdura

`altroconsumo` · https://www.altroconsumo.it/alimentazione/fare-la-spesa/consigli/calendario-frutta-verdura

- **What it is**: Fruit and vegetable calendar by Altroconsumo, the Italian consumers' association.
- **Why it is authoritative**: An independent consumer organisation that runs tests and buying guides.
- **What it offers**: In-season months in Italy, buying and storage tips.
- **Used for**: Buying_guide, Plant_part_used, Seasonality, Texts, Varieties
- **Products (65)**: aglio_garlic, albicocca_apricot, alchechengi_cape_gooseberry, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, ciliegia_cherry, cima_di_rapa_turnip_greens, clementine_clementine, cocco_coconut, fagiolino_green_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, litchi_lychee, mandarino_mandarin, mango_mango, maracuja_passion_fruit, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, mirtillo_blueberry, mora_blackberry, nespola_loquat, papaya_papaya, patata_potato, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, ravanello_radish, sedano_celery, spinacio_spinach, susina_plum, topinambur_jerusalem_artichoke, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: italy_macro_areas, seasonality_states

### Unsplash API

`unsplash` · https://unsplash.com/

- **What it is**: Unsplash.
- **Why it is authoritative**: An image bank under the Unsplash License.
- **What it offers**: High-resolution photos.
- **Used for**: Images
- **Products (63)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cetriolo_cucumber, ciliegia_cherry, cipolla_estiva_summer_onion, clementine_clementine, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, lampone_raspberry, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melograno_pomegranate, menta_mint, mirtillo_blueberry, mora_blackberry, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, pera_pear, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, prezzemolo_parsley, rapa_turnip, ravanello_radish, ribes_redcurrant, riso_rice, rosmarino_rosemary, salvia_sage, spinacio_spinach, susina_plum, timo_thyme, zucchina_zucchini

### WWF Italia - Il calendario della frutta e verdura di stagione (PDF locale)

`wwf` · https://www.wwf.it/ecotips

- **What it is**: WWF Italy's seasonal fruit and vegetable calendar (local PDF).
- **Why it is authoritative**: A conservation organisation; calendar used in the vote among Italian sources.
- **What it offers**: In-season months in Italy.
- **Used for**: Seasonality, Texts
- **Products (60)**: aglio_garlic, albicocca_apricot, alchechengi_cape_gooseberry, anguria_watermelon, arancia_orange, asparago_asparagus, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, ciliegia_cherry, cima_di_rapa_turnip_greens, clementine_clementine, fagiolino_green_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, litchi_lychee, mandarino_mandarin, mango_mango, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, mirtillo_blueberry, mora_blackberry, nespola_loquat, patata_potato, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, ravanello_radish, sedano_celery, spinacio_spinach, susina_plum, topinambur_jerusalem_artichoke, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: italy_macro_areas, seasonality_states

### Greenpeace Italia - Guida alla frutta e verdura di stagione (PDF locale)

`greenpeace` · https://www.greenpeace.org/italy/

- **What it is**: Greenpeace Italy's seasonal fruit and vegetable guide (local PDF).
- **Why it is authoritative**: An environmental organisation; the guide is used as one of the Italian seasonality sources.
- **What it offers**: In-season months and anti-waste tips.
- **Used for**: Seasonality, Texts
- **Products (54)**: aglio_garlic, albicocca_apricot, anguria_watermelon, arancia_orange, asparago_asparagus, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cetriolo_cucumber, ciliegia_cherry, cima_di_rapa_turnip_greens, clementine_clementine, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, limone_lemon, mandarino_mandarin, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, mirtillo_blueberry, mora_blackberry, nespola_loquat, patata_potato, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, ravanello_radish, sedano_celery, spinacio_spinach, susina_plum, topinambur_jerusalem_artichoke, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Glossary entries**: italy_macro_areas, seasonality_states

### eAmbrosia - registro UE delle indicazioni geografiche

`eambrosia` · https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/

- **What it is**: eAmbrosia, the European Union register of geographical indications.
- **Why it is authoritative**: The official legal register of PDOs and PGIs, managed by the European Commission.
- **What it offers**: Verification of PDOs and PGIs and a link to each one's record.
- **Used for**: PDO/PGI
- **Products (48)**: aglio_garlic, amarena_sour_cherry, anguria_watermelon, arancia_orange, asparago_asparagus, basilico_basil, broccolo_romanesco_romanesco, carciofo_artichoke, carota_carrot, castagna_chestnut, cavolfiore_cauliflower, cedro_citron, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, fagiolo_bean, farro_emmer, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fungo_porcino_porcini_mushroom, kiwi_kiwifruit, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, mela_apple, melanzana_eggplant, melone_melon, nocciola_hazelnut, noce_walnut, oliva_olive, patata_potato, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pistacchio_pistachio, pomodoro_tomato, radicchio_radicchio, riso_rice, rucola_arugula, scalogno_shallot, sedano_celery, susina_plum, uva_table_grape
- **Glossary entries**: dop_igp, varieties

### Fondazione Slow Food per la Biodiversità - Presìdi e Arca del Gusto

`slow_food` · https://www.fondazioneslowfood.com/it/

- **What it is**: Slow Food Foundation for Biodiversity: Presidia and Ark of Taste.
- **Why it is authoritative**: A foundation that catalogues and protects endangered local varieties, with a public record for each product.
- **What it offers**: Verification of local varieties and of Presidium status.
- **Used for**: Seasonality, Varieties
- **Products (34)**: aglio_garlic, albicocca_apricot, avocado_avocado, banana_banana, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, cavolfiore_cauliflower, cece_chickpea, cedro_citron, chinotto_chinotto, cicerchia_grass_pea, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, fagiolo_bean, farro_emmer, fava_broad_bean, giuggiola_jujube, grano_duro_durum_wheat, grano_saraceno_buckwheat, lenticchia_lentil, limone_lemon, mandarino_mandarin, melanzana_eggplant, navone_swede, nespola_comune_medlar, peperone_bell_pepper, pesca_peach, porro_leek, rapa_turnip, riso_rice, sedano_celery, zucca_pumpkin
- **Glossary entries**: slow_food, varieties

### GBIF Backbone Taxonomy (funghi)

`gbif` · https://www.gbif.org/

- **What it is**: GBIF Backbone Taxonomy, Global Biodiversity Information Facility.
- **Why it is authoritative**: A government-funded international infrastructure for biodiversity data.
- **What it offers**: The taxonomy of fungi, which EPPO and WFO cover only in part.
- **Used for**: Botany
- **Products (10)**: cardoncello_king_oyster_mushroom, finferlo_chanterelle, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, shiitake_shiitake, spugnola_morel, tartufo_bianco_white_truffle, tartufo_nero_black_truffle

### AGRIBALYSE 3.1 (ADEME, Francia) - impatti ambientali degli alimenti

`agribalyse` · https://data.ademe.fr/datasets/agribalyse-31-synthese

- **What it is**: AGRIBALYSE 3.1, the French public database of the environmental impacts of produce (ADEME, INRAE).
- **Why it is authoritative**: The official database of the French ecological transition agency, based on life-cycle assessment.
- **What it offers**: Carbon footprint of fresh herbs, absent from SU-EATABLE LIFE (different boundaries: up to consumption).
- **Used for**: Environmental Footprint
- **Products (7)**: basilico_basil, menta_mint, origano_oregano, prezzemolo_parsley, rosmarino_rosemary, salvia_sage, timo_thyme
- **Glossary entries**: carbon_footprint

### Provincia di Cuneo - Schede dei funghi commestibili

`provincia_cuneo_funghi` · https://natura.provincia.cuneo.it/funghi/commestibili/amanita-caesarea/

- **What it is**: Edible mushroom sheets on the nature portal of the Province of Cuneo.
- **Why it is authoritative**: A local institutional source in one of Italy's main mushroom-gathering areas.
- **What it offers**: The fruiting period of Caesar's mushroom (summer and early autumn).
- **Used for**: Seasonality
- **Products (3)**: finferlo_chanterelle, fungo_ovolo_caesars_mushroom, spugnola_morel

### Gesundheitsportal Österreichs - Saisonkalender (Ministero della salute austriaco)

`austria_gesundheitsportal` · https://www.gesundheit.gv.at/leben/ernaehrung/saisonkalender.html

- **What it is**: Seasonal calendar of Austria's public health portal (Federal Ministry of Health).
- **Why it is authoritative**: A government source listed by EUFIC as the national reference for Austria.
- **What it offers**: In-season months used for the Alpine zone where EUFIC does not list the product.
- **Used for**: European Seasonality
- **Products (2)**: fungo_pleurotus_oyster_mushroom, indivia_riccia_curly_endive

### Legge 16 dicembre 1985, n. 752 - Normativa quadro sui tartufi (art. 6, periodi di raccolta)

`legge_752_1985` · https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:1985-12-16;752~art6

- **What it is**: Italian national framework law on harvesting, growing and selling truffles.
- **Why it is authoritative**: State law: article 6 sets the periods in which harvesting and selling fresh truffles are allowed.
- **What it offers**: The harvest calendar by species, used as the seasonality of white and black truffles.
- **Used for**: Seasonality
- **Products (2)**: tartufo_bianco_white_truffle, tartufo_nero_black_truffle

### iNaturalist (solo foto CC0 / CC BY / CC BY-SA)

`inaturalist` · https://www.inaturalist.org/

- **What it is**: iNaturalist (CC0, CC BY, CC BY-SA photos only).
- **Why it is authoritative**: A nature observation platform with stated licences.
- **What it offers**: Photos of plants in the field.
- **Used for**: Images
- **Products (1)**: fungo_pleurotus_oyster_mushroom

### Istituto Superiore di Sanità - Rapporti ISTISAN 09/47 (carenza di G6PD e favismo)

`iss_istisan_09_47` · https://www.iss.it/documents/20126/45616/0947web.pdf

- **What it is**: Italian National Institute of Health, ISTISAN Report 09/47 on G6PD deficiency.
- **Why it is authoritative**: ISS is Italy's main public body for research and control in public health.
- **What it offers**: The explanation of favism linked to broad beans.
- **Used for**: Health Notes
- **Products (1)**: fava_broad_bean
- **Glossary entries**: favism

### Regione Emilia-Romagna, BUR 2012 - Disciplinare IGP Amarene Brusche di Modena (richiesta di modifica)

`bur_emilia_romagna_amarene` · https://bur.regione.emilia-romagna.it/area-bollettini/bollettini-pubblicati/2012/marzo-periodico-parte-seconda-1a-quindicina/richiesta-di-modifica-del-disciplinare-della-denominazione-amarene-brusche-di-modena/allegato.pdf

- **What it is**: Production specification of the PGI Amarene Brusche di Modena, published in the Official Bulletin of the Emilia-Romagna Region (amendment request, 2012).
- **Why it is authoritative**: An official act regulating a protected name: it sets the period in which sour cherries may be harvested.
- **What it offers**: The sour cherry harvest period (20 May - 31 July).
- **Used for**: Seasonality
- **Products (1)**: amarena_sour_cherry

### Biblioteca civica Bertoliana (Vicenza) - Scheda botanica del lampascione

`biblioteca_bertoliana` · https://www.bibliotecabertoliana.it/file/4959-lampascione.pdf

- **What it is**: Botanical sheet on tassel hyacinth bulbs published by the Bertoliana public library in Vicenza.
- **Why it is authoritative**: A popular source from a public body; used only for lack of agricultural or regional sources, and stated as such.
- **What it offers**: The bulb harvest period (January-March).
- **Used for**: Seasonality
- **Products (1)**: lampascioni_tassel_hyacinth

### NaturaSì - Frutta e verdura di stagione (schede prodotto)

`naturasi` · https://www.naturasi.it/frutta-verdura-di-stagione/cipollotto

- **What it is**: Seasonal fruit and vegetable sheets by NaturaSì, an Italian organic product retailer.
- **Why it is authoritative**: An Italian commercial source suggested by the user; used only for spring onion, which no calendar lists.
- **What it offers**: The spring onion season (early spring).
- **Used for**: Seasonality
- **Products (1)**: cipollotto_spring_onion

### ISMEA Mercati

`ismea` · https://www.ismeamercati.it/

- **What it is**: ISMEA Mercati, Institute of Services for the Agricultural Food Market.
- **Why it is authoritative**: A public body for agri-food market data.
- **What it offers**: Planned for fruit harvest periods: not available in usable form for North, Centre and South, so not used.
- **Used for**: database level

### Servizi agricoli regionali (Veneto Agricoltura, ERSA FVG, ARSIAL)

`regional` · https://www.arsial.it/

- **What it is**: Regional agricultural services (Veneto Agricoltura, ERSA FVG, ARSIAL and others).
- **Why it is authoritative**: Regional public technical-advice bodies.
- **What it offers**: Planned for fruit calendars: not used (documented gap).
- **Used for**: database level

### EUFIC - European national sources on seasonal fruit and vegetables

`eufic_national` · https://www.eufic.org/en/page/european-national-sources-to-find-information-on-seasonal-fruit-and-vegetables

- **What it is**: EUFIC list of national sources on seasonal fruit and vegetables.
- **Why it is authoritative**: EUFIC's curated selection of sources for each country.
- **What it offers**: The national sources used to fill missing climate zones (e.g. the Austrian portal).
- **Used for**: database level
- **Products**: used for the whole database (methods and legends), not for individual records
- **Glossary entries**: eufic_zones

### EUFIC - Are seasonal fruit and vegetables better for the environment?

`eufic_article` · https://www.eufic.org/en/healthy-living/article/are-seasonal-fruit-and-vegetables-better-for-the-environment

- **What it is**: EUFIC article 'Are seasonal fruit and vegetables better for the environment?' (2020).
- **Why it is authoritative**: A science-based summary of the literature on the environmental impact of seasonality.
- **What it offers**: The summary on the environmental benefits of a seasonal diet in the metadata.
- **Used for**: database level
- **Products**: used for the whole database (methods and legends), not for individual records
- **Glossary entries**: greenhouse

### USDA ARS Image Gallery

`usda_ars_images` · https://www.ars.usda.gov/oc/images/image-gallery/

- **What it is**: USDA ARS Image Gallery.
- **Why it is authoritative**: Public-domain institutional images.
- **What it offers**: Planned: few relevant images, not used.
- **Used for**: database level

### EEA - Biogeographical regions, Europe 2016 (Agenzia europea dell'ambiente)

`eea_biogeo` · https://www.eea.europa.eu/

- **What it is**: Map layer of Europe's biogeographical regions (2016) by the European Environment Agency.
- **Why it is authoritative**: An EU agency; it is the same basis as the climate zones used by EUFIC.
- **What it offers**: The continuous boundaries of the climate zones for the app map.
- **Used for**: database level
- **Products**: used for the whole database (methods and legends), not for individual records

## 16. Conflicts between sources

`metadata.source_conflicts`: the general cases where sources give different values, with the decision taken.

### Many values in the initial draft did not match the official sources.

- **Why**: The draft had been compiled without specific references and mixed different sources and contexts.
- **Decision**: The official source always prevails. The draft value is recorded as a discrepancy in the record and, if unverifiable, removed from the app but kept separately.
- **Rationale**: No invented data and no information lost.

### CREA, BDA-IEO and USDA give different values for the same product.

- **Why**: Different samples, varieties, countries and methods (e.g. 'available' carbohydrates in Europe and 'by difference' in the USA).
- **Decision**: Order of priority: CREA, then BDA-IEO (also to fill missing nutrients), USDA only when the first two are missing. The source is given for every value.
- **Rationale**: Italian tables describe the products sold in Italy.

### Italian calendars do not always agree on in-season months.

- **Why**: They consider different areas, varieties and growing methods (open field, greenhouse).
- **Decision**: For each month and macro-area the sources listing it are counted: with at least half of the votes the month is in season, with fewer it is early or end of season; the peak is the central months of a period of at least three months on which all sources agree.
- **Rationale**: Voting reduces the weight of any single source and the same rule applies to every product.

### EUFIC gives data by country, not by climate zone, and does not list every product.

- **Why**: Each country has its own national source and countries span several zones.
- **Decision**: Each country is assigned to its main zone; missing zones are filled with national sources listed by EUFIC or, for the Mediterranean zone, with Southern Italian seasonality. The origin is given zone by zone.
- **Rationale**: A declared approximation, useful for people using the app outside Italy.

### Some produce (truffles, Caesar's mushroom, nectarine) are missing from Italian seasonal calendars.

- **Why**: Calendars cover cultivated produce and do not separate forms of the same species (peach and nectarine).
- **Decision**: The most authoritative source available for that product is used: the harvest-period law for truffles, an institutional mushroom sheet for Caesar's mushroom, peach seasonality for nectarine. The source is stated in seasonality.italy_source or in the notes.
- **Rationale**: A declared, product-specific source is better than a gap.

### For cucumber, eggplant, peppers and citrus FoodKeeper says fridge, the UC Davis guide room temperature.

- **Why**: FoodKeeper focuses on safety and storage time, the UC Davis guide on taste: these products are chilling-sensitive and lose quality in the fridge.
- **Decision**: The 'where' follows the UC Davis guide, durations follow FoodKeeper; the short label gives both options and the choice is explained in the record.
- **Rationale**: For a seasonality app keeping the flavour matters, without hiding the alternative.

### HB66 storage times (weeks or months) are much longer than FoodKeeper's (days).

- **Why**: HB66 refers to commercial cold stores at optimal temperature and humidity; FoodKeeper to a home fridge.
- **Decision**: They are two separate fields: home and commercial storage time. A commercial time is never used as a home time.
- **Rationale**: It avoids unrealistic promises to the user.

### Chilling threshold and freezing point are often given as ranges.

- **Why**: They depend on variety, ripeness and dissolved sugars.
- **Decision**: The highest end (the most cautious) is used and the range is kept when available. If damage occurs within a band (stone fruit 2-8 °C) no single threshold is given.
- **Rationale**: Cautious advice does not damage the produce.

### HB66's summary table contains some typos (e.g. 1310 for radicchio) and many products are not measured at 5 °C.

- **Why**: PDF layout errors; chilling-sensitive products are not studied at low temperatures.
- **Decision**: Order: Kader table class, then chapter values, then an estimate at 5 °C with HB66 Q10 values (marked as estimated). Clearly wrong values are not used.
- **Rationale**: Use the reference author's classification first.

### Environmental footprints vary widely between studies and databases.

- **Why**: Different methods, countries, yields and system boundaries (field to farm gate, or up to consumption).
- **Decision**: SU-EATABLE LIFE (harmonised median) is used with the number of studies and range; AGRIBALYSE only for the missing herbs, with its boundaries stated.
- **Rationale**: Values comparable between produce and transparent uncertainty.

### Some texts written by merging several sources quoted durations or nutrients different from the structured data.

- **Why**: The texts drew on Italian popular sources, the data come from official databases.
- **Decision**: Structured data prevail: storage labels and 'rich in / source of' lists were realigned with the data and EU claims.
- **Rationale**: The app must not say two different things about the same product.

### For some produce a source has no exact entry.

- **Why**: International databases do not cover every Italian speciality (e.g. cutting chicory, turnip tops, corn salad).
- **Decision**: The closest entry is used, always marked 'approximate' and stated in the record.
- **Rationale**: A declared approximate value is more useful than a gap, provided it is transparent.

### A variety's common name may differ from its registered name.

- **Why**: Registers use the official denomination (e.g. 'Spadona' for Spadonino, 'Detroit 2' for Detroit).
- **Decision**: The common name is shown and the registered name is given with the country of registration.
- **Rationale**: Readability for the user and verifiability on the register.

## 17. How the app uses it

| Screen | Fields |
|---|---|
| Product card | `names`, `images.primary`, month state from `seasonality.italy_macro_areas[area]`, `ripening_and_storage.card_short_storage`, `perishability.label` |
| Shopping list | `buying_guide.shopping_list_preview`, `ripening_badge_label` |
| Storage | `home_storage`, `storage_instructions`, `estimated_shelf_life_days`, `storage_compatibility`, `ethylene_compatibility` |
| Nutrition | `reference_portion`, `macros_per_100g`, `nutrition_claims_eu`, `vitamins`, `minerals`, `allergens_eu` |
| Sustainability | `environmental_footprint.sustainability_rating`, `greenhouse_comparison`, `metadata.sustainable_diet_summary` |
| Territory | `notable_varieties`, `dop_igp_labels`, `traditional_products_pat`, `varieties_registered_italy` |
| Garden | `agricultural_calendar_italy` |
| Learn more | `sources_by_topic.useful_links` |
| "?" help | `metadata.field_help`, `metadata.vocabulary`, `item.help_refs` → `metadata.glossary` |
| Sources | `metadata.official_sources`, `metadata.source_conflicts` |
