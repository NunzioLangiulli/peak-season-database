# Guida al database Peak Season

Questa guida spiega come è costruito `data/database.json`, blocco per blocco, usando come esempio la scheda reale del **pomodoro**. Per ogni blocco: a cosa serve nell'app, da dove vengono i dati, come leggerli.

## 1. I file

| File | Contenuto |
|---|---|
| `data/database.json` | Il database: `metadata` (legende, metodi, fonti) + `items` (153 schede) |
| `data/schema.json` | Le regole formali (JSON Schema): tipi, valori ammessi, campi obbligatori |
| `data/items_index.json` | La lista master: per ogni alimento i codici e gli URL esatti su ogni fonte |
| `data/draft_legacy_values.json` | I valori della tua bozza che non erano verificabili: tolti dall'app ma conservati |
| `data/scraping_report.md` | Il report di affidabilità e lacune |
| `data/audit_findings.json` | L'esito del ricontrollo voce per voce |
| `data/raw/` | Copie dei dati grezzi delle fonti (PDF, CSV, xlsx, pagine) |
| `scripts/config/` | Tabelle curate a mano dalle fonti, con citazioni e numeri di pagina |
| `assets/images/` | Le foto `<id>_01.jpg`, `_02.jpg`… |

## 2. La logica generale

Ogni scheda segue lo stesso schema in 12 blocchi. Tre principi valgono ovunque:

1. **Ogni dato ha una fonte.** I blocchi strutturati portano la fonte accanto al valore (`source`, `basis`, `source_food`, `derivation`); le fonti di tutta la scheda sono elencate in `sources_by_topic.sources_used`.
2. **`null` non è uguale a vuoto.** Un `null` è una lacuna vera (elencata in `data_completeness.missing_fields`), oppure un campo che non ha senso per quell'alimento (elencato in `not_applicable_fields`): ad esempio la soglia di danno da freddo per chi non soffre il freddo.
3. **Bilingue.** Tutti i testi per l'utente sono oggetti `{"it": …, "en": …}` (vedi §13).

Gli identificativi (`id`) sono `nome_it_name_en` senza accenti: sono le chiavi usate anche dai riferimenti tra schede (es. `keep_away_from`, `compatible_with`) e dai nomi delle foto.

## 3. Identità e botanica

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
`category` è uno dei 5 valori del template. I sinonimi vengono da EPPO (nomi comuni ufficiali IT/EN).

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
- `scientific_name`, `family`, `genus`: verificati su EPPO e World Flora Online (`eppo_code`, `wfo_id` sono i codici ufficiali).
- `plant_part_used`: confermata dai testi delle fonti.
- `upov_*`: il codice di specie del **Catalogo comune UE delle varietà**; `varieties_registered_italy.count` = varietà oggi iscritte nel registro italiano.

## 4. Varietà e territori

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
- `notable_varieties` contiene **solo** varietà verificate; `varieties_verification` dice dove (Slow Food, Catalogo UE, Orto da Coltivare…) e con che nome sono registrate.
- `dop_igp_labels` e `has_dop_igp` sono verificati sul registro UE **eAmbrosia** (`eambrosia_verified`).
- I **Prodotti Agroalimentari Tradizionali** stanno in `nutrition_and_sustainability.traditional_products_pat` (vedi §9).

## 5. Immagini

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
Ogni foto ha autore, licenza, URL d'origine e tipo (`view_type`): `full_frame` (il prodotto riempie l'inquadratura: è la foto principale quando c'è), `isolated_background` (sfondo bianco o colorato), `plant_in_field` (la pianta), `botanical_plate` (tavola botanica), `cut_section` (tagliato), `other`. `flags` segnala problemi noti (piatto, soggetto sbagliato), `variety` una varietà particolare (es. pesca tabacchiera). `sync_images.py` riallinea il database se togli foto dalla cartella.

## 6. Stagionalità

Nell'estratto i 12 mesi (gen→dic) sono abbreviati: `·` fuori stagione, `p` primizia, `S` di stagione, `P` picco, `f` fine stagione.

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
- `italy_macro_areas` (Nord, Centro, Sud e Isole) è la stagionalità per l'utente italiano: nasce dal **voto tra più fonti** (WWF, Greenpeace, Altroconsumo, EUFIC per l'Italia, epoche di raccolta di Orto da Coltivare); il metodo è in `metadata.seasonality_method`. Per ogni mese si contano le fonti che lo indicano: con almeno metà dei voti il mese è di stagione, con meno è inizio o fine stagione; il **picco** sono i mesi centrali di un periodo di almeno tre mesi su cui tutte le fonti concordano.
- `eufic_climatic_zones`: le 6 zone europee, derivate dai Paesi EUFIC (`eufic_by_country`); dove EUFIC non ha l'alimento, la zona alpina viene dal calendario austriaco (fonte nazionale indicata da EUFIC) e la mediterranea è derivata dal Sud e Isole. `eufic_zone_sources` dice la provenienza di ogni zona.

## 7. Calendario agricolo (orto)

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
Mesi di semina, trapianto e raccolta per zona, con parametri agronomici (profondità, sesto d'impianto, esposizione, luna) da Orto da Coltivare. Per frutta, erbe e cereali sono ancora i valori della bozza (lacuna documentata).

## 8. Acquisto, maturazione e conservazione

È il blocco più ricco. Va letto su tre livelli: **testi per l'utente**, **consiglio sintetico**, **dati scientifici**.

### 8a. Testi per l'utente

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
`card_short_storage` è l'etichetta breve per la card (≤ 42 caratteri), allineata ai dati FoodKeeper e UC Davis; `storage_instructions` è il testo lungo.

### 8b. Consiglio sintetico per l'app

```json
{
  "home_storage": {
    "location": "room_temperature",
    "label": {
      "it": "A Temperatura Ambiente, Non in Frigo",
      "en": "At Room Temperature, Not in the Fridge"
    },
    "tip": {
      "it": "In frigo perde sapore e non si colora. Una volta tagliato va sempre in frigorifero.",
      "en": "In the fridge it loses flavour and doesn't turn red. Once cut, always keep it in the fridge."
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
- `home_storage.location`: **dove** tenerlo in casa (frigo, fuori dal frigo finché matura, temperatura ambiente, dispensa). Fonte principale: la guida UC Davis/Kader; FoodKeeper per le durate; i conflitti tra le due fonti sono scritti in `derivation`.
- `perishability`: la classe di respirazione tradotta in un livello da 1 a 6, con etichetta e consiglio. Più un prodotto respira, prima perde freschezza.

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
`storage_compatibility`: con quali prodotti può stare (stessa temperatura e umidità, nessun conflitto di etilene). Fonte: HB66, tabella di Thompson.

### 8c. Dati scientifici post-raccolta

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
- `ripening_type` (nel blocco `ripening_and_storage`): `climaterico` (continua a maturare dopo la raccolta, es. pomodoro, banana, pera) o `non_climaterico` (non matura più, es. agrumi, uva, fragola); etichette IT/EN in `metadata.vocabulary`.
- `freezing_point_c`: il "highest freezing point" di HB66, la temperatura più alta a cui inizia a formarsi ghiaccio; con un intervallo si usa l'estremo più alto (il più prudente).
- `optimal_temperature_c` e `optimal_humidity_percent`: condizioni **professionali** ottimali (USDA HB66, UC Davis).
- `chilling_injury`: se soffre il freddo, sotto quale soglia (`critical_temperature_c` = massimo dell'intervallo minimo sicuro, `lowest_safe_range_c`) e con quali sintomi. Il pomodoro maturo è sensibile sotto i 7-10 °C (13 °C se ancora verde): per questo è meglio fuori frigo.
- `estimated_shelf_life_days`: durate **domestiche** da FoodKeeper (`room_temp_mode` dice se si usa "fino a maturazione" o "solo frigo"); `commercial_optimal_days` è la durata in condizioni professionali.

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
Etilene: se lo produce (e quanto, classe a 20 °C) e se ne è sensibile. `keep_away_from` è calcolato: i forti produttori del database da cui tenerlo lontano, se è sensibile.

## 9. Nutrizione e sostenibilità

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
Valori per 100 g di parte edibile. `data_basis` dice quale scheda è la fonte primaria (CREA, poi BDA-IEO, USDA solo se mancano le prime).

```json
{
  "vitamins": [
    {
      "name": "Vitamina A (Retinolo Eq.)",
      "name_en": "Vitamin A (Retinol Eq.)",
      "amount": 610.0,
      "unit": "µg",
      "percent_nrv": 76.2,
      "source": "crea"
    },
    {
      "name": "Vitamina E",
      "name_en": "Vitamin E",
      "amount": 1.06,
      "unit": "mg",
      "percent_nrv": 8.8,
      "source": "bda_ieo"
    },
    {
      "name": "Vitamina C",
      "name_en": "Vitamin C",
      "amount": 25.0,
      "unit": "mg",
      "percent_nrv": 31.2,
      "source": "crea"
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
Ogni vitamina e minerale ha quantità, unità, `percent_nrv` (% del Valore Nutritivo di Riferimento, Reg. UE 1169/2011) e la fonte. I **claim** sono calcolati applicando le soglie del Reg. CE 1924/2006 (es. "Ad alto contenuto di vitamina C" ≥ 30% VNR): non sono scritti a mano.

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
Composti bioattivi: carotenoidi (USDA FDC), classi di flavonoidi (USDA Flavonoid DB), polifenoli totali e acidi fenolici (Phenol-Explorer). `group` permette di raggrupparli in app, `main_compounds` dice quali sono i principali.

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
- `allergens_eu`: allergeni dell'allegato II del Reg. UE 1169/2011 (lista vuota = nessuno).
- `reference_portion`: la porzione standard LARN (via IEO SmartFood), con un'equivalenza pratica e i valori per porzione.
- `protein_reference`: le proteine rapportate al fabbisogno LARN.

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
Sostenibilità (SU-EATABLE LIFE): CO2 e acqua per kg e per porzione, con riferimento alla voce del database, numero di studi e intervallo. `greenhouse_comparison` mostra quanto pesa la serra riscaldata (fuori stagione). `sustainability_rating` traduce i numeri in livelli e consigli.

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
`traditional_products_pat`: i Prodotti Agroalimentari Tradizionali dell'elenco MASAF legati all'alimento, con la regione.

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
Testi: benefici (solo con nutrienti coerenti con i claim) e idee anti-spreco.

## 10. Fonti della scheda

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
`sources_used` elenca **tutte** le fonti usate per questo alimento (27 per il pomodoro), con argomento, URL e file locali. `useful_links` sono i link da mostrare all'utente (12). `source_codes` contiene i codici esatti delle schede (CREA, BDA, FDC…).

## 11. Tracciabilità: `data_completeness`

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
Questo blocco serve a te, non all'utente: dice cosa veniva dalla bozza, cosa è stato verificato, cosa manca, cosa non è pertinente, dove la bozza era diversa dalle fonti (`discrepancies`, con valore della bozza, valore della fonte e fonte) e perché (`notes`).

## 12. I metadati

`metadata` contiene ciò che vale per tutto il database e sta in testa al file: 

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

Le **legende** (stati stagionali, zone, deperibilità, conservazione, gruppi di compatibilità) e i **metodi** (stagionalità, post-raccolta, proteine, impronte) sono pensati per essere letti direttamente dall'app.

## 13. Bilinguismo

L'app può essere usata tutta in italiano o tutta in inglese:

- ogni testo per l'utente è `{"it": …, "en": …}`, comprese le motivazioni (`basis`, `derivation`, `method`, note delle varietà);
- i valori codificati (es. `climaterico`, `in_season`, `fridge`) sono chiavi: l'etichetta da mostrare è in `metadata.vocabulary`;
- nutrienti e composti hanno `name` e `name_en`;
- restano in lingua originale solo i nomi propri (varietà, DOP/IGP, PAT, nomi scientifici, autori, licenze, fonti);
- `data_completeness.notes` è un registro tecnico in italiano, non per l'app.

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
Gruppi del vocabolario (24): `category`, `botany.plant_part_used`, `seasonality.state`, `seasonality.italy_macro_areas`, `seasonality.eufic_climatic_zones`, `seasonality.estimates`, `seasonality.estimates.from`, `month`, `ripening_and_storage.ripening_type`, `ripening_and_storage.primary_location`, `class_scale`, `ripening_and_storage.postharvest_physiology.freezing_susceptibility`, `ripening_and_storage.home_storage.location`, `ripening_and_storage.postharvest_physiology.estimated_shelf_life_days.room_temp_mode`, `ripening_and_storage.storage_compatibility.group`, `agricultural_calendar_italy.agronomic_params.sun_exposure`, `agricultural_calendar_italy.agronomic_params.lunar_phase_advice`, `images.image_details.view_type`, `botany.upov_register`, `nutrition_and_sustainability.bioactive_compounds.group`, `sustainability_level`, `match`, `nutrition_and_sustainability.allergens_eu.annex_ii_number`, `botany.family`.

## 14. Glossario e icone "?"

Le spiegazioni sono scritte una volta, in `metadata.glossary`, e raggiunte da più punti:

| Da dove | Campo | Esempio |
|---|---|---|
| un campo | `metadata.field_help[percorso]` | `ripening_and_storage.ripening_type` → `climacteric`, `non_climacteric` |
| un valore | `metadata.vocabulary[gruppo][valore].glossary` | `climaterico` → `climacteric` |
| un alimento | `item.help_refs` | fava → `favism` sul testo dei benefici |
| un'altra voce | `glossary[id].see_also` | `climacteric` → `ethylene`, `non_climacteric` |
| una fonte | `official_sources[].used_for.glossary_entries` | HB66 → voci di conservazione |

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
      "url": "https://postharvest.ucdavis.edu/produce-facts-sheets"
    },
    {
      "key": "usda_hb66",
      "name": "USDA ARS Agricultural Handbook 66 (2016)",
      "url": "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf"
    },
    {
      "key": "uc_davis_storing_guide",
      "name": "UC Davis / Kader - Storing Fresh Fruits and Vegetables for Better Taste (UC ANR Pub. 21590)",
      "url": "https://homeorchard.ucanr.edu/files/115275.pdf"
    }
  ],
  "see_also": [
    "ethylene",
    "non_climacteric"
  ]
}
```
Ogni voce: `term`, `short` (una riga per il tooltip), `text` (spiegazione completa), `sources` (nome e URL dal catalogo), `see_also`. Voci (44): `climacteric`, `non_climacteric`, `ethylene`, `ethylene_production`, `ethylene_sensitivity`, `keep_away_from`, `respiration_rate`, `perishability`, `q10`, `chilling_injury`, `lowest_safe_temperature`, `freezing_point`, `freezing_susceptibility`, `optimal_storage`, `shelf_life_home`, `home_storage`, `storage_compatibility`, `seasonality_states`, `italy_macro_areas`, `eufic_zones`, `seasonality_estimate`, `sowing_transplant`, `agronomic_params`, `edible_portion`, `nrv`, `nutrition_claims`, `larn`, `reference_portion`, `allergens`, `gluten`, `carotenoids`, `polyphenols`, `flavonoids`, `carbon_footprint`, `water_footprint`, `greenhouse`, `dop_igp`, `pat`, `slow_food`, `upov_variety_register`, `varieties`, `scientific_name`, `favism`, `data_quality`.

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
## 15. Il catalogo delle fonti

`metadata.official_sources` descrive ogni fonte: cos'è (`description`), perché è autorevole (`authority`), cosa offre (`offers`), per quali argomenti e per quali alimenti è stata consultata (`used_for`). Elenco completo:

### Regolamento (UE) n. 1169/2011 - Allegato XIII, Valori Nutritivi di Riferimento

`reg_1169_2011` · https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32011R1169

- **Cos'è**: Regolamento (UE) n. 1169/2011 sulle informazioni sui prodotti ai consumatori.
- **Perché è autorevole**: Norma europea vincolante sull'etichettatura.
- **Cosa offre**: Valori Nutritivi di Riferimento (Allegato XIII) per le percentuali e l'elenco dei 14 allergeni (Allegato II).
- **Usata per**: Allergeni, %VNR
- **Alimenti (153)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Voci di glossario**: allergens, gluten, nrv, nutrition_claims

### IEO SmartFood - Porzioni e frequenze (porzioni standard LARN-SINU)

`ieo_smartfood_portions` · https://www.smartfood.ieo.it/media/p02bkul0/smartfood-tab-porzioni-e-frequenze-completa.pdf

- **Cos'è**: Tabella 'Porzioni e frequenze' del programma SmartFood dell'Istituto Europeo di Oncologia.
- **Perché è autorevole**: Riporta le porzioni standard LARN-SINU in forma pratica, con equivalenze domestiche.
- **Cosa offre**: Grammi della porzione per gruppo di prodotti, equivalenze ('2-3 pomodori') e frequenze di consumo.
- **Usata per**: Porzioni
- **Alimenti (153)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Voci di glossario**: reference_portion

### EPPO Global Database

`eppo` · https://gd.eppo.int/

- **Cos'è**: EPPO Global Database dell'Organizzazione europea e mediterranea per la protezione delle piante.
- **Perché è autorevole**: Organizzazione intergovernativa; i suoi codici sono lo standard per identificare le piante in Europa.
- **Cosa offre**: Nome scientifico preferito, codice EPPO e nomi comuni ufficiali in italiano e inglese.
- **Usata per**: Botanica
- **Alimenti (151)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: scientific_name

### Regolamento (CE) n. 1924/2006 - indicazioni nutrizionali e sulla salute

`reg_1924_2006` · https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32006R1924

- **Cos'è**: Regolamento (CE) n. 1924/2006 sulle indicazioni nutrizionali e sulla salute.
- **Perché è autorevole**: È la norma europea vincolante che stabilisce quali diciture nutrizionali si possono usare e con quali soglie.
- **Cosa offre**: Le soglie per i claim 'fonte di', 'ad alto contenuto di', 'a basso contenuto di'.
- **Usata per**: Claim UE
- **Alimenti (146)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Voci di glossario**: nutrition_claims

### LARN - SINU (tabelle riassuntive, PDF locale)

`larn_sinu` · https://sinu.it/tabelle-larn-2014/

- **Cos'è**: LARN - Livelli di Assunzione di Riferimento di Nutrienti ed energia, Società Italiana di Nutrizione Umana (IV revisione, 2014).
- **Perché è autorevole**: Sono i valori di riferimento ufficiali per la popolazione italiana.
- **Cosa offre**: Il fabbisogno di proteine per contestualizzare i claim proteici.
- **Usata per**: LARN
- **Alimenti (145)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Voci di glossario**: larn, reference_portion

### World Flora Online - Plant List

`wfo` · https://list.worldfloraonline.org/

- **Cos'è**: World Flora Online, catalogo mondiale delle specie vegetali.
- **Perché è autorevole**: Progetto internazionale dei principali orti botanici, erede di The Plant List.
- **Cosa offre**: Nome accettato, famiglia e genere.
- **Usata per**: Botanica
- **Alimenti (143)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, taccola_snow_pea, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Voci di glossario**: scientific_name

### USDA FoodData Central - SR Legacy (2018-04)

`usda_fdc` · https://fdc.nal.usda.gov/

- **Cos'è**: USDA FoodData Central, versione SR Legacy (2018) del Dipartimento dell'Agricoltura degli Stati Uniti.
- **Perché è autorevole**: È la banca dati nazionale di composizione degli USA, in pubblico dominio e tra le più usate al mondo.
- **Cosa offre**: Carotenoidi (licopene, luteina, ecc.), assenti nelle tabelle italiane, e i nutrienti di pochi prodotti senza scheda CREA o BDA-IEO.
- **Usata per**: Composti Bioattivi, Nutrizione, Testi
- **Alimenti (136)**: aglio_garlic, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Voci di glossario**: carotenoids

### USDA ARS Agricultural Handbook 66 (2016)

`usda_hb66` · https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf

- **Cos'è**: USDA Agriculture Handbook 66 'The Commercial Storage of Fruits, Vegetables, and Florist and Nursery Stocks' (2016).
- **Perché è autorevole**: È il manuale tecnico di riferimento internazionale sulla conservazione dei prodotti freschi, con capitoli scritti da specialisti per ogni prodotto.
- **Cosa offre**: Condizioni ottimali, respirazione (classi di Kader), etilene, danno da freddo, punto di congelamento, gruppi di conservazione compatibile.
- **Usata per**: Danno da Freddo, Freezing_susceptibility, Plant_part_used, Post-raccolta, Conservazione Compatibile, Testi, Varietà
- **Alimenti (133)**: aglio_garlic, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gombo_okra, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Voci di glossario**: chilling_injury, climacteric, ethylene, ethylene_production, ethylene_sensitivity, freezing_point, freezing_susceptibility, keep_away_from, lowest_safe_temperature, non_climacteric, optimal_storage, perishability, q10, respiration_rate, storage_compatibility

### SU-EATABLE LIFE - database delle impronte di carbonio e idrica (Petersson et al. 2021)

`su_eatable_life` · https://doi.org/10.1038/s41597-021-00909-8

- **Cos'è**: SU-EATABLE LIFE, database delle impronte di carbonio e idrica dei prodotti (Petersson et al., Scientific Data, 2021).
- **Perché è autorevole**: Prodotto da un progetto LIFE finanziato dall'UE, pubblicato su rivista scientifica con revisione tra pari; armonizza oltre 800 studi.
- **Cosa offre**: Impronta di carbonio e idrica per kg, con confronto tra pieno campo, serra e prodotti importati.
- **Usata per**: Impronta Ambientale
- **Alimenti (129)**: aglio_garlic, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, daikon_daikon, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, gelso_mulberry, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salvia_sage, scalogno_shallot, scarola_escarole, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, susina_plum, taccola_snow_pea, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: carbon_footprint, greenhouse, water_footprint

### Wikimedia Commons API

`wikimedia` · https://commons.wikimedia.org/w/api.php

- **Cos'è**: Wikimedia Commons.
- **Perché è autorevole**: Archivio di immagini con licenza libera verificabile.
- **Cosa offre**: Foto con autore e licenza (CC0, CC BY, CC BY-SA, pubblico dominio).
- **Usata per**: Immagini
- **Alimenti (124)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, broccolo_romanesco_romanesco, cachi_persimmon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, cicerchia_grass_pea, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pisello_pea, pistacchio_pistachio, pompelmo_grapefruit, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, rafano_horseradish, rapa_turnip, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, spinacio_spinach, spugnola_morel, susina_plum, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote

### Pixabay API

`pixabay` · https://pixabay.com/

- **Cos'è**: Pixabay.
- **Perché è autorevole**: Banca di immagini con licenza Pixabay.
- **Cosa offre**: Foto ad alta risoluzione.
- **Usata per**: Immagini
- **Alimenti (124)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicerchia_grass_pea, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, erba_cipollina_chives, fagiolino_green_bean, farro_emmer, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, grano_saraceno_buckwheat, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, prezzemolo_parsley, rabarbaro_rhubarb, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, salvia_sage, sambuco_elderberry, scalogno_shallot, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, susina_plum, timo_thyme, uva_spina_gooseberry, uva_table_grape, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini

### BDA-IEO - Banca Dati di Composizione degli Alimenti (Istituto Europeo di Oncologia)

`bda_ieo` · https://bda.ieo.it/

- **Cos'è**: Banca Dati di Composizione degli Alimenti per studi epidemiologici in Italia, Istituto Europeo di Oncologia.
- **Perché è autorevole**: Banca dati scientifica che riunisce e armonizza tabelle italiane e internazionali indicando per ogni valore la fonte originale.
- **Cosa offre**: Nutrienti mancanti nelle tabelle CREA e prodotti non presenti in CREA (es. mais dolce crudo).
- **Usata per**: Nutrizione, Testi
- **Alimenti (121)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_rosso_red_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, papaya_papaya, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, salvia_sage, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, spugnola_morel, susina_plum, tartufo_nero_black_truffle, timo_thyme, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: edible_portion

### USDA FSIS FoodKeeper

`usda_foodkeeper` · https://www.foodsafety.gov/keep-food-safe/foodkeeper-app

- **Cos'è**: USDA FSIS FoodKeeper, banca dati sulla conservazione domestica dei prodotti.
- **Perché è autorevole**: Strumento ufficiale del Food Safety and Inspection Service degli Stati Uniti, sviluppato con la Cornell University.
- **Cosa offre**: Durate in dispensa, frigorifero e congelatore dalla data di acquisto, con note pratiche.
- **Usata per**: Conservazione in Casa, Testi
- **Alimenti (120)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, carciofo_artichoke, cardoncello_king_oyster_mushroom, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, clementine_clementine, crescione_watercress, daikon_daikon, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, finferlo_chanterelle, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mango_mango, maracuja_passion_fruit, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, sambuco_elderberry, scalogno_shallot, scarola_escarole, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, timo_thyme, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: home_storage, shelf_life_home

### MASAF - Elenco nazionale dei Prodotti Agroalimentari Tradizionali, XXVI revisione (2026)

`masaf_pat` · https://www.masaf.gov.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/24151

- **Cos'è**: Elenco nazionale dei Prodotti Agroalimentari Tradizionali del Ministero dell'Agricoltura (XXVI revisione, 2026).
- **Perché è autorevole**: Elenco ufficiale aggiornato ogni anno su segnalazione delle Regioni.
- **Cosa offre**: I prodotti tradizionali regionali legati a ciascun prodotto.
- **Usata per**: Testi, Prodotti Tradizionali
- **Alimenti (118)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, anguria_watermelon, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, cardoncello_king_oyster_mushroom, carota_carrot, carruba_carob, castagna_chestnut, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, cicoria_da_cespo_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, grano_duro_durum_wheat, grano_saraceno_buckwheat, kiwi_kiwifruit, lampascioni_tassel_hyacinth, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, mandarino_mandarin, mandorla_almond, mango_mango, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mirtillo_rosso_lingonberry, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, orzo_barley, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, timo_thyme, topinambur_jerusalem_artichoke, uva_table_grape, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: pat

### EUFIC - Explore seasonal fruit and vegetables in Europe

`eufic_map` · https://www.eufic.org/en/explore-seasonal-fruit-and-vegetables-in-europe

- **Cos'è**: Mappa interattiva EUFIC della frutta e verdura di stagione in Europa.
- **Perché è autorevole**: L'European Food Information Council è un'organizzazione senza scopo di lucro che divulga informazioni scientifiche su alimentazione e salute.
- **Cosa offre**: Mesi di stagione per Paese europeo, aggregati per zona climatica.
- **Usata per**: Stagionalità Europea, Testi
- **Alimenti (115)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, cicoria_da_cespo_chicory, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, crescione_watercress, daikon_daikon, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finferlo_chanterelle, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, giuggiola_jujube, gombo_okra, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, limone_lemon, mais_corn, mandarino_mandarin, mango_mango, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nespola_comune_medlar, nespola_loquat, oliva_olive, papaya_papaya, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rucola_arugula, salicornia_samphire, sambuco_elderberry, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, tartufo_bianco_white_truffle, tartufo_nero_black_truffle, topinambur_jerusalem_artichoke, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Voci di glossario**: eufic_zones, italy_macro_areas, seasonality_estimate, seasonality_states

### Orto da Coltivare (Matteo Cereda) - tabelle di semina PDF + schede

`ortodacoltivare` · https://www.ortodacoltivare.it/calendario/calendario-delle-raccolte/

- **Cos'è**: Orto da Coltivare, sito e tabelle di semina di Matteo Cereda (PDF locali per Nord, Centro, Sud).
- **Perché è autorevole**: Riferimento italiano molto usato per l'orto domestico, con tabelle per zona climatica.
- **Cosa offre**: Mesi di semina, trapianto e raccolta per macro-area e parametri di coltivazione.
- **Usata per**: Calendario Agricolo, Plant_part_used, Stagionalità, Testi, Varietà
- **Alimenti (110)**: aglio_garlic, agretti_saltwort, albicocca_apricot, alchechengi_cape_gooseberry, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_verza_savoy_cabbage, cece_chickpea, cedro_citron, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, crescione_watercress, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_duro_durum_wheat, indivia_belga_belgian_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, mais_corn, mandarino_mandarin, mandorla_almond, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nespola_comune_medlar, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, origano_oregano, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, scalogno_shallot, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, timo_thyme, topinambur_jerusalem_artichoke, uva_table_grape, valerianella_corn_salad, zafferano_saffron, zucca_pumpkin, zucchina_spinosa_chayote, zucchina_zucchini
- **Voci di glossario**: agronomic_params, italy_macro_areas, seasonality_states, sowing_transplant, varieties

### CREA Alimenti e Nutrizione - Tabelle di composizione degli alimenti (rev. 2019)

`crea` · https://www.alimentinutrizione.it/tabelle-nutrizionali/ricerca-per-alimento

- **Cos'è**: Tabelle di composizione dei prodotti del CREA - Centro di ricerca Alimenti e Nutrizione (revisione 2019).
- **Perché è autorevole**: È l'ente pubblico di ricerca del Ministero dell'Agricoltura e cura la banca dati nazionale di riferimento per la composizione dei prodotti in Italia.
- **Cosa offre**: Energia, acqua, macronutrienti, vitamine, minerali e parte edibile per 100 g di prodotto crudo.
- **Usata per**: Nutrizione, Testi
- **Alimenti (109)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, cocco_coconut, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, grano_duro_durum_wheat, grano_saraceno_buckwheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, litchi_lychee, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nespola_loquat, nocciola_hazelnut, noce_walnut, oliva_olive, orzo_barley, papaya_papaya, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salvia_sage, scarola_escarole, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, tartufo_nero_black_truffle, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: edible_portion

### My-PersonalTrainer

`my_personaltrainer` · https://www.my-personaltrainer.it/frutta-verdura-di-stagione.htm

- **Cos'è**: My-PersonalTrainer, portale italiano di divulgazione su alimentazione e salute.
- **Perché è autorevole**: Fonte divulgativa prevista dal progetto; non è una fonte primaria.
- **Cosa offre**: Solo spunti per i testi e link di approfondimento: nessun valore numerico viene preso da qui.
- **Usata per**: Plant_part_used, Varietà, Verification_texts
- **Alimenti (109)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, cardo_cardoon, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cece_chickpea, cetriolo_cucumber, chinotto_chinotto, cicerchia_grass_pea, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cocco_coconut, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, fungo_champignon_button_mushroom, fungo_porcino_porcini_mushroom, grano_saraceno_buckwheat, indivia_belga_belgian_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, lime_lime, limone_lemon, mais_corn, mandarino_mandarin, mandorla_almond, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nocciola_hazelnut, origano_oregano, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, radicchio_radicchio, rafano_horseradish, ravanello_radish, ribes_redcurrant, riso_rice, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, taccola_snow_pea, timo_thyme, topinambur_jerusalem_artichoke, uva_table_grape, zafferano_saffron, zucca_pumpkin, zucchina_zucchini

### UC Davis / Kader - Storing Fresh Fruits and Vegetables for Better Taste (UC ANR Pub. 21590)

`uc_davis_storing_guide` · https://homeorchard.ucanr.edu/files/115275.pdf

- **Cos'è**: Guida 'Storing Fresh Fruits and Vegetables for Better Taste' (A. Kader, J. Thompson, K. Sylva, L. Harris), UC ANR Pub. 21590.
- **Perché è autorevole**: Pubblicazione divulgativa ufficiale dell'Università della California firmata dai principali esperti di post-raccolta.
- **Cosa offre**: Dove conservare in casa ogni prodotto: frigorifero, maturazione sul bancone, solo temperatura ambiente.
- **Usata per**: Conservazione in Casa
- **Alimenti (107)**: aglio_garlic, agretti_saltwort, albicocca_apricot, amarena_sour_cherry, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cardoncello_king_oyster_mushroom, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cedro_citron, cetriolo_cucumber, chinotto_chinotto, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, crescione_watercress, daikon_daikon, erba_cipollina_chives, fagiolino_green_bean, fagiolo_bean, fico_fig, finferlo_chanterelle, fragola_strawberry, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, gelso_mulberry, indivia_belga_belgian_endive, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, mais_corn, mandarino_mandarin, mango_mango, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, papaya_papaya, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, radicchio_radicchio, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salicornia_samphire, salvia_sage, sambuco_elderberry, scalogno_shallot, scarola_escarole, sedano_celery, shiitake_shiitake, spinacio_spinach, spugnola_morel, susina_plum, taccola_snow_pea, timo_thyme, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: climacteric, ethylene, keep_away_from

### USDA Database for the Flavonoid Content of Selected Foods, Release 3.3 (2018)

`usda_flavonoids` · https://www.ars.usda.gov/northeast-area/beltsville-md-bhnrc/beltsville-human-nutrition-research-center/methods-and-application-of-food-composition-laboratory/mafcl-site-pages/flavonoids/

- **Cos'è**: USDA Database for the Flavonoid Content of Selected Foods, Release 3.3 (2018).
- **Perché è autorevole**: Banca dati del laboratorio di composizione dell'USDA, costruita da studi analitici selezionati con criteri di qualità.
- **Cosa offre**: Contenuto di antocianine, flavonoli, flavoni, flavanoni e catechine.
- **Usata per**: Composti Bioattivi
- **Alimenti (97)**: aglio_garlic, albicocca_apricot, amarena_sour_cherry, arachide_peanut, arancia_orange, asparago_asparagus, asparago_selvatico_wild_asparagus, avocado_avocado, banana_banana, bietola_da_coste_swiss_chard, broccolo_broccoli, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, crescione_watercress, erba_cipollina_chives, fagiolino_green_bean, fava_broad_bean, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fragola_strawberry, gelso_mulberry, giuggiola_jujube, gombo_okra, grano_saraceno_buckwheat, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, mandarino_mandarin, mandorla_almond, mango_mango, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, navone_swede, nocciola_hazelnut, noce_walnut, origano_oregano, orzo_barley, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, puntarelle_puntarelle, rabarbaro_rhubarb, radicchio_radicchio, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salvia_sage, sambuco_elderberry, scarola_escarole, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, timo_thyme, uva_spina_gooseberry, uva_table_grape, zafferano_saffron, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: flavonoids, polyphenols

### Phenol-Explorer 3.6 - database del contenuto di polifenoli negli alimenti (INRA)

`phenol_explorer` · http://phenol-explorer.eu/

- **Cos'è**: Phenol-Explorer 3.6, database dei polifenoli nei prodotti (INRA, Francia).
- **Perché è autorevole**: Database scientifico citato nella letteratura internazionale, che raccoglie i dati di centinaia di pubblicazioni con il metodo di analisi.
- **Cosa offre**: Polifenoli totali (saggio di Folin), acidi fenolici, stilbeni e altri polifenoli. Uso non commerciale con citazione.
- **Usata per**: Composti Bioattivi
- **Alimenti (86)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, banana_banana, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, broccolo_broccoli, carciofo_artichoke, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cima_di_rapa_turnip_greens, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, clementine_clementine, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, grano_duro_durum_wheat, grano_saraceno_buckwheat, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, litchi_lychee, mandarino_mandarin, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nespola_loquat, origano_oregano, orzo_barley, papaya_papaya, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pomodoro_tomato, pompelmo_grapefruit, prezzemolo_parsley, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_redcurrant, rosmarino_rosemary, rucola_arugula, salvia_sage, scalogno_shallot, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, timo_thyme, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: flavonoids, polyphenols

### UC Davis Postharvest Research and Extension Center - Produce Fact Sheets

`uc_davis` · https://postharvest.ucdavis.edu/produce-facts-sheets

- **Cos'è**: Schede post-raccolta del Postharvest Research and Extension Center dell'Università della California, Davis.
- **Perché è autorevole**: Centro di ricerca di riferimento mondiale sulla fisiologia post-raccolta (le schede sono curate da A. Kader e colleghi).
- **Cosa offre**: Temperatura e umidità ottimali, etilene, danno da freddo, classificazione climaterica.
- **Usata per**: Post-raccolta, Testi
- **Alimenti (80)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, avocado_avocado, banana_banana, basilico_basil, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_rosso_red_cabbage, cetriolo_cucumber, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, clementine_clementine, fagiolino_green_bean, fico_d_india_prickly_pear, fico_fig, fragola_strawberry, fungo_champignon_button_mushroom, giuggiola_jujube, gombo_okra, indivia_belga_belgian_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, mango_mango, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melanzana_eggplant, melograno_pomegranate, melone_melon, menta_mint, mirtillo_blueberry, mora_blackberry, nespola_loquat, oliva_olive, origano_oregano, papaya_papaya, patata_dolce_sweet_potato, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pistacchio_pistachio, pomodoro_tomato, pompelmo_grapefruit, prezzemolo_parsley, radicchio_radicchio, ravanello_radish, ribes_redcurrant, rosmarino_rosemary, salvia_sage, sedano_celery, spinacio_spinach, susina_plum, taccola_snow_pea, timo_thyme, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: chilling_injury, climacteric, ethylene, ethylene_sensitivity, home_storage, non_climacteric, optimal_storage

### EU Plant Variety Portal - Catalogo comune UE delle varieta' (agricole, ortive, frutticole)

`eu_plant_variety_portal` · https://ec.europa.eu/food/plant-variety-portal/

- **Cos'è**: EU Plant Variety Portal, il Catalogo comune UE delle varietà di specie agricole, ortive e da frutto.
- **Perché è autorevole**: Banca dati ufficiale della Commissione europea che riunisce i registri varietali nazionali.
- **Cosa offre**: Codici di specie UPOV, verifica delle varietà e numero di varietà iscritte in Italia.
- **Usata per**: Codice UPOV, Varietà
- **Alimenti (76)**: aglio_garlic, albicocca_apricot, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_broccoli, carciofo_artichoke, cardo_cardoon, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, cicoria_da_cespo_chicory, cicoria_da_taglio_cutting_chicory, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, clementine_clementine, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, grano_duro_durum_wheat, indivia_belga_belgian_endive, indivia_riccia_curly_endive, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, mais_corn, mandarino_mandarin, mela_apple, mela_cotogna_quince, melanzana_eggplant, melone_melon, mirtillo_blueberry, mora_blackberry, orzo_barley, patata_potato, peperoncino_chili_pepper, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, prezzemolo_parsley, radicchio_radicchio, rapa_turnip, ravanello_radish, ribes_redcurrant, riso_rice, scalogno_shallot, scarola_escarole, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, valerianella_corn_salad, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: upov_variety_register, varieties

### Bio Suisse - Calendario stagionale (Svizzera, PDF locale)

`biosuisse` · https://bio-suisse.ch/calendariostagionale

- **Cos'è**: Calendario stagionale di Bio Suisse, federazione delle aziende biologiche svizzere (PDF locale).
- **Perché è autorevole**: Ente di riferimento dell'agricoltura biologica in Svizzera; utile come riferimento per il clima alpino.
- **Cosa offre**: Mesi di stagione per le zone alpine e di montagna.
- **Usata per**: Stagionalità, Testi
- **Alimenti (71)**: aglio_garlic, albicocca_apricot, asparago_asparagus, barbabietola_beetroot, basilico_basil, broccolo_broccoli, carciofo_artichoke, carota_carrot, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_cinese_chinese_cabbage, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, cicoria_da_cespo_chicory, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, erba_cipollina_chives, fagiolo_bean, finocchio_fennel, fragola_strawberry, indivia_riccia_curly_endive, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, mais_corn, mela_apple, mela_cotogna_quince, melanzana_eggplant, mirabella_mirabelle_plum, mirtillo_blueberry, mirtillo_rosso_lingonberry, mora_blackberry, noce_walnut, pastinaca_parsnip, patata_dolce_sweet_potato, patata_potato, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pisello_pea, pomodoro_tomato, porro_leek, prezzemolo_parsley, rabarbaro_rhubarb, radicchio_radicchio, rafano_horseradish, ravanello_radish, ribes_nero_blackcurrant, ribes_redcurrant, rucola_arugula, sambuco_elderberry, scarola_escarole, scorzonera_black_salsify, sedano_celery, sedano_rapa_celeriac, spinacio_spinach, susina_plum, taccola_snow_pea, uva_spina_gooseberry, uva_table_grape, valerianella_corn_salad, zucca_pumpkin, zucchina_zucchini

### Altroconsumo - Calendario frutta e verdura

`altroconsumo` · https://www.altroconsumo.it/alimentazione/fare-la-spesa/consigli/calendario-frutta-verdura

- **Cos'è**: Calendario di frutta e verdura di Altroconsumo, associazione italiana dei consumatori.
- **Perché è autorevole**: Associazione indipendente di tutela dei consumatori con test e guide d'acquisto.
- **Cosa offre**: Mesi di stagione in Italia, consigli d'acquisto e di conservazione.
- **Usata per**: Buying_guide, Plant_part_used, Stagionalità, Testi, Varietà
- **Alimenti (65)**: aglio_garlic, albicocca_apricot, alchechengi_cape_gooseberry, ananas_pineapple, anguria_watermelon, arancia_orange, asparago_asparagus, avocado_avocado, banana_banana, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, ciliegia_cherry, cima_di_rapa_turnip_greens, clementine_clementine, cocco_coconut, fagiolino_green_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, litchi_lychee, mandarino_mandarin, mango_mango, maracuja_passion_fruit, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, mirtillo_blueberry, mora_blackberry, nespola_loquat, papaya_papaya, patata_potato, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, ravanello_radish, sedano_celery, spinacio_spinach, susina_plum, topinambur_jerusalem_artichoke, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: italy_macro_areas, seasonality_states

### Unsplash API

`unsplash` · https://unsplash.com/

- **Cos'è**: Unsplash.
- **Perché è autorevole**: Banca di immagini con licenza Unsplash.
- **Cosa offre**: Foto ad alta risoluzione.
- **Usata per**: Immagini
- **Alimenti (63)**: aglio_garlic, albicocca_apricot, ananas_pineapple, anguria_watermelon, arachide_peanut, arancia_orange, asparago_asparagus, avena_oat, avocado_avocado, barbabietola_beetroot, basilico_basil, bietola_da_coste_swiss_chard, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavolo_nero_black_kale, cavolo_rapa_kohlrabi, cetriolo_cucumber, ciliegia_cherry, cipolla_estiva_summer_onion, clementine_clementine, fagiolino_green_bean, fagiolo_bean, farro_emmer, fava_broad_bean, fragola_strawberry, fungo_champignon_button_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, lampone_raspberry, limone_lemon, litchi_lychee, mais_corn, mandarino_mandarin, maracuja_passion_fruit, mela_apple, mela_cotogna_quince, melograno_pomegranate, menta_mint, mirtillo_blueberry, mora_blackberry, orzo_barley, papaya_papaya, pastinaca_parsnip, patata_potato, peperoncino_chili_pepper, pera_pear, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, prezzemolo_parsley, rapa_turnip, ravanello_radish, ribes_redcurrant, riso_rice, rosmarino_rosemary, salvia_sage, spinacio_spinach, susina_plum, timo_thyme, zucchina_zucchini

### WWF Italia - Il calendario della frutta e verdura di stagione (PDF locale)

`wwf` · https://www.wwf.it/ecotips

- **Cos'è**: Calendario della frutta e verdura di stagione di WWF Italia (PDF locale).
- **Perché è autorevole**: Organizzazione per la conservazione della natura; calendario usato nel voto tra fonti italiane.
- **Cosa offre**: Mesi di stagione in Italia.
- **Usata per**: Stagionalità, Testi
- **Alimenti (60)**: aglio_garlic, albicocca_apricot, alchechengi_cape_gooseberry, anguria_watermelon, arancia_orange, asparago_asparagus, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_romanesco_romanesco, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavoletto_di_bruxelles_brussels_sprout, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cavolo_rosso_red_cabbage, cavolo_verza_savoy_cabbage, cetriolo_cucumber, ciliegia_cherry, cima_di_rapa_turnip_greens, clementine_clementine, fagiolino_green_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lime_lime, limone_lemon, litchi_lychee, mandarino_mandarin, mango_mango, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, mirtillo_blueberry, mora_blackberry, nespola_loquat, patata_potato, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, ravanello_radish, sedano_celery, spinacio_spinach, susina_plum, topinambur_jerusalem_artichoke, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: italy_macro_areas, seasonality_states

### Greenpeace Italia - Guida alla frutta e verdura di stagione (PDF locale)

`greenpeace` · https://www.greenpeace.org/italy/

- **Cos'è**: Guida alla frutta e verdura di stagione di Greenpeace Italia (PDF locale).
- **Perché è autorevole**: Organizzazione ambientalista; la guida è usata come una delle fonti di stagionalità italiane.
- **Cosa offre**: Mesi di stagione e consigli contro lo spreco.
- **Usata per**: Stagionalità, Testi
- **Alimenti (54)**: aglio_garlic, albicocca_apricot, anguria_watermelon, arancia_orange, asparago_asparagus, barbabietola_beetroot, bietola_da_coste_swiss_chard, broccolo_broccoli, cachi_persimmon, carciofo_artichoke, carota_carrot, castagna_chestnut, cavolfiore_cauliflower, cavolo_cappuccio_cabbage, cavolo_nero_black_kale, cetriolo_cucumber, ciliegia_cherry, cima_di_rapa_turnip_greens, clementine_clementine, fagiolino_green_bean, fagiolo_bean, fava_broad_bean, fico_fig, finocchio_fennel, fragola_strawberry, kiwi_kiwifruit, lampone_raspberry, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, limone_lemon, mandarino_mandarin, mela_apple, melanzana_eggplant, melograno_pomegranate, melone_melon, mirtillo_blueberry, mora_blackberry, nespola_loquat, patata_potato, peperone_bell_pepper, pera_pear, pesca_peach, pisello_pea, pomodoro_tomato, pompelmo_grapefruit, porro_leek, ravanello_radish, sedano_celery, spinacio_spinach, susina_plum, topinambur_jerusalem_artichoke, uva_table_grape, zucca_pumpkin, zucchina_zucchini
- **Voci di glossario**: italy_macro_areas, seasonality_states

### eAmbrosia - registro UE delle indicazioni geografiche

`eambrosia` · https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/

- **Cos'è**: eAmbrosia, registro dell'Unione europea delle indicazioni geografiche.
- **Perché è autorevole**: Registro legale ufficiale delle DOP e IGP, gestito dalla Commissione europea.
- **Cosa offre**: Verifica delle DOP e IGP e link alla scheda di ciascuna.
- **Usata per**: DOP/IGP
- **Alimenti (48)**: aglio_garlic, amarena_sour_cherry, anguria_watermelon, arancia_orange, asparago_asparagus, basilico_basil, broccolo_romanesco_romanesco, carciofo_artichoke, carota_carrot, castagna_chestnut, cavolfiore_cauliflower, cedro_citron, ciliegia_cherry, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, cipollotto_spring_onion, clementine_clementine, fagiolo_bean, farro_emmer, fico_d_india_prickly_pear, fico_fig, finocchio_fennel, fungo_porcino_porcini_mushroom, kiwi_kiwifruit, lattuga_da_cespo_head_lettuce, lattuga_da_taglio_leaf_lettuce, lenticchia_lentil, limone_lemon, mela_apple, melanzana_eggplant, melone_melon, nocciola_hazelnut, noce_walnut, oliva_olive, patata_potato, peperone_bell_pepper, pera_pear, pesca_noce_nectarine, pesca_peach, pistacchio_pistachio, pomodoro_tomato, radicchio_radicchio, riso_rice, rucola_arugula, scalogno_shallot, sedano_celery, susina_plum, uva_table_grape
- **Voci di glossario**: dop_igp, varieties

### Fondazione Slow Food per la Biodiversità - Presìdi e Arca del Gusto

`slow_food` · https://www.fondazioneslowfood.com/it/

- **Cos'è**: Fondazione Slow Food per la Biodiversità: Presìdi e Arca del Gusto.
- **Perché è autorevole**: Fondazione che cataloga e tutela le varietà locali a rischio, con schede pubbliche per ciascun prodotto.
- **Cosa offre**: Verifica delle varietà locali e della qualifica di Presidio.
- **Usata per**: Stagionalità, Varietà
- **Alimenti (34)**: aglio_garlic, albicocca_apricot, avocado_avocado, banana_banana, carciofo_artichoke, cardo_cardoon, carota_carrot, carruba_carob, cavolfiore_cauliflower, cece_chickpea, cedro_citron, chinotto_chinotto, cicerchia_grass_pea, cipolla_estiva_summer_onion, cipolla_invernale_winter_onion, fagiolo_bean, farro_emmer, fava_broad_bean, giuggiola_jujube, grano_duro_durum_wheat, grano_saraceno_buckwheat, lenticchia_lentil, limone_lemon, mandarino_mandarin, melanzana_eggplant, navone_swede, nespola_comune_medlar, peperone_bell_pepper, pesca_peach, porro_leek, rapa_turnip, riso_rice, sedano_celery, zucca_pumpkin
- **Voci di glossario**: slow_food, varieties

### GBIF Backbone Taxonomy (funghi)

`gbif` · https://www.gbif.org/

- **Cos'è**: GBIF Backbone Taxonomy, Global Biodiversity Information Facility.
- **Perché è autorevole**: Infrastruttura internazionale finanziata dai governi per i dati sulla biodiversità.
- **Cosa offre**: La tassonomia dei funghi, che EPPO e WFO coprono solo in parte.
- **Usata per**: Botanica
- **Alimenti (10)**: cardoncello_king_oyster_mushroom, finferlo_chanterelle, fungo_champignon_button_mushroom, fungo_ovolo_caesars_mushroom, fungo_pleurotus_oyster_mushroom, fungo_porcino_porcini_mushroom, shiitake_shiitake, spugnola_morel, tartufo_bianco_white_truffle, tartufo_nero_black_truffle

### AGRIBALYSE 3.1 (ADEME, Francia) - impatti ambientali degli alimenti

`agribalyse` · https://data.ademe.fr/datasets/agribalyse-31-synthese

- **Cos'è**: AGRIBALYSE 3.1, banca dati pubblica francese degli impatti ambientali dei prodotti (ADEME, INRAE).
- **Perché è autorevole**: Banca dati ufficiale dell'agenzia francese per la transizione ecologica, basata sull'analisi del ciclo di vita.
- **Cosa offre**: Impronta di carbonio delle erbe aromatiche fresche, assenti in SU-EATABLE LIFE (confini diversi: fino al consumo).
- **Usata per**: Impronta Ambientale
- **Alimenti (7)**: basilico_basil, menta_mint, origano_oregano, prezzemolo_parsley, rosmarino_rosemary, salvia_sage, timo_thyme
- **Voci di glossario**: carbon_footprint

### Provincia di Cuneo - Schede dei funghi commestibili

`provincia_cuneo_funghi` · https://natura.provincia.cuneo.it/funghi/commestibili/amanita-caesarea/

- **Cos'è**: Schede dei funghi commestibili del portale naturalistico della Provincia di Cuneo.
- **Perché è autorevole**: Fonte istituzionale locale, in una delle principali zone di raccolta di funghi in Italia.
- **Cosa offre**: Il periodo di crescita dell'ovolo buono (estate e inizio autunno).
- **Usata per**: Stagionalità
- **Alimenti (3)**: finferlo_chanterelle, fungo_ovolo_caesars_mushroom, spugnola_morel

### Gesundheitsportal Österreichs - Saisonkalender (Ministero della salute austriaco)

`austria_gesundheitsportal` · https://www.gesundheit.gv.at/leben/ernaehrung/saisonkalender.html

- **Cos'è**: Calendario stagionale del portale sanitario pubblico austriaco (Ministero federale della salute).
- **Perché è autorevole**: Fonte governativa indicata da EUFIC come riferimento nazionale per l'Austria.
- **Cosa offre**: Mesi di stagione usati per la zona alpina dove EUFIC non elenca il prodotto.
- **Usata per**: Stagionalità Europea
- **Alimenti (2)**: fungo_pleurotus_oyster_mushroom, indivia_riccia_curly_endive

### Legge 16 dicembre 1985, n. 752 - Normativa quadro sui tartufi (art. 6, periodi di raccolta)

`legge_752_1985` · https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:1985-12-16;752~art6

- **Cos'è**: Legge quadro nazionale su raccolta, coltivazione e commercio dei tartufi.
- **Perché è autorevole**: Norma dello Stato: l'art. 6 fissa i periodi in cui raccolta e commercio dei tartufi freschi sono consentiti.
- **Cosa offre**: Il calendario di raccolta per specie, usato come stagionalità del tartufo bianco e del tartufo nero.
- **Usata per**: Stagionalità
- **Alimenti (2)**: tartufo_bianco_white_truffle, tartufo_nero_black_truffle

### iNaturalist (solo foto CC0 / CC BY / CC BY-SA)

`inaturalist` · https://www.inaturalist.org/

- **Cos'è**: iNaturalist (solo foto CC0, CC BY, CC BY-SA).
- **Perché è autorevole**: Piattaforma di osservazioni naturalistiche con licenze dichiarate.
- **Cosa offre**: Foto delle piante in campo.
- **Usata per**: Immagini
- **Alimenti (1)**: fungo_pleurotus_oyster_mushroom

### Istituto Superiore di Sanità - Rapporti ISTISAN 09/47 (carenza di G6PD e favismo)

`iss_istisan_09_47` · https://www.iss.it/documents/20126/45616/0947web.pdf

- **Cos'è**: Istituto Superiore di Sanità, Rapporti ISTISAN 09/47 sulla carenza di G6PD.
- **Perché è autorevole**: L'ISS è il principale ente pubblico di ricerca e controllo in sanità pubblica in Italia.
- **Cosa offre**: La spiegazione del favismo collegata alla fava.
- **Usata per**: Note di Salute
- **Alimenti (1)**: fava_broad_bean
- **Voci di glossario**: favism

### Regione Emilia-Romagna, BUR 2012 - Disciplinare IGP Amarene Brusche di Modena (richiesta di modifica)

`bur_emilia_romagna_amarene` · https://bur.regione.emilia-romagna.it/area-bollettini/bollettini-pubblicati/2012/marzo-periodico-parte-seconda-1a-quindicina/richiesta-di-modifica-del-disciplinare-della-denominazione-amarene-brusche-di-modena/allegato.pdf

- **Cos'è**: Disciplinare di produzione dell'IGP Amarene Brusche di Modena, pubblicato nel Bollettino Ufficiale della Regione Emilia-Romagna (richiesta di modifica, 2012).
- **Perché è autorevole**: Atto ufficiale che regola una denominazione protetta: fissa il periodo in cui le amarene possono essere raccolte.
- **Cosa offre**: Il periodo di raccolta delle amarene (20 maggio - 31 luglio).
- **Usata per**: Stagionalità
- **Alimenti (1)**: amarena_sour_cherry

### Biblioteca civica Bertoliana (Vicenza) - Scheda botanica del lampascione

`biblioteca_bertoliana` · https://www.bibliotecabertoliana.it/file/4959-lampascione.pdf

- **Cos'è**: Scheda botanica del lampascione pubblicata dalla Biblioteca civica Bertoliana di Vicenza.
- **Perché è autorevole**: Fonte divulgativa di un ente pubblico; usata solo in mancanza di fonti agricole o regionali, e dichiarata come tale.
- **Cosa offre**: Il periodo di raccolta dei bulbi (gennaio-marzo).
- **Usata per**: Stagionalità
- **Alimenti (1)**: lampascioni_tassel_hyacinth

### NaturaSì - Frutta e verdura di stagione (schede prodotto)

`naturasi` · https://www.naturasi.it/frutta-verdura-di-stagione/cipollotto

- **Cos'è**: Schede di frutta e verdura di stagione di NaturaSì, catena italiana di negozi biologici.
- **Perché è autorevole**: Fonte commerciale italiana indicata dall'utente; usata solo per il cipollotto, che nessun calendario riporta.
- **Cosa offre**: La stagione del cipollotto (inizio della primavera).
- **Usata per**: Stagionalità
- **Alimenti (1)**: cipollotto_spring_onion

### ISMEA Mercati

`ismea` · https://www.ismeamercati.it/

- **Cos'è**: ISMEA Mercati, Istituto di Servizi per il Mercato Agricolo Alimentare.
- **Perché è autorevole**: Ente pubblico per i dati di mercato agroalimentare.
- **Cosa offre**: Previsto dal progetto per le epoche di raccolta della frutta: non disponibile in forma consultabile per Nord, Centro e Sud, quindi non usato.
- **Usata per**: livello di database

### Servizi agricoli regionali (Veneto Agricoltura, ERSA FVG, ARSIAL)

`regional` · https://www.arsial.it/

- **Cos'è**: Servizi agricoli regionali (Veneto Agricoltura, ERSA FVG, ARSIAL e altri).
- **Perché è autorevole**: Enti pubblici regionali di assistenza tecnica.
- **Cosa offre**: Previsti per i calendari della frutta: non usati (lacuna documentata).
- **Usata per**: livello di database

### EUFIC - European national sources on seasonal fruit and vegetables

`eufic_national` · https://www.eufic.org/en/page/european-national-sources-to-find-information-on-seasonal-fruit-and-vegetables

- **Cos'è**: Elenco EUFIC delle fonti nazionali sulla frutta e verdura di stagione.
- **Perché è autorevole**: Selezione curata da EUFIC delle fonti di ciascun Paese.
- **Cosa offre**: Le fonti nazionali usate per colmare le zone climatiche mancanti (es. il portale austriaco).
- **Usata per**: livello di database
- **Alimenti**: usata per l'intero database (metodi e legende), non per singole schede
- **Voci di glossario**: eufic_zones

### EUFIC - Are seasonal fruit and vegetables better for the environment?

`eufic_article` · https://www.eufic.org/en/healthy-living/article/are-seasonal-fruit-and-vegetables-better-for-the-environment

- **Cos'è**: Articolo EUFIC 'Are seasonal fruit and vegetables better for the environment?' (2020).
- **Perché è autorevole**: Sintesi divulgativa basata sulla letteratura scientifica sull'impatto ambientale della stagionalità.
- **Cosa offre**: La sintesi sui benefici ambientali della dieta stagionale nei metadati.
- **Usata per**: livello di database
- **Alimenti**: usata per l'intero database (metodi e legende), non per singole schede
- **Voci di glossario**: greenhouse

### USDA ARS Image Gallery

`usda_ars_images` · https://www.ars.usda.gov/oc/images/image-gallery/

- **Cos'è**: USDA ARS Image Gallery.
- **Perché è autorevole**: Immagini istituzionali di pubblico dominio.
- **Cosa offre**: Prevista dal progetto: poche immagini pertinenti, non usata.
- **Usata per**: livello di database

### EEA - Biogeographical regions, Europe 2016 (Agenzia europea dell'ambiente)

`eea_biogeo` · https://www.eea.europa.eu/

- **Cos'è**: Strato cartografico delle regioni biogeografiche d'Europa (2016) dell'Agenzia europea dell'ambiente.
- **Perché è autorevole**: Agenzia dell'Unione europea; è la stessa base delle zone climatiche usate da EUFIC.
- **Cosa offre**: I confini continui delle zone climatiche per la mappa dell'app.
- **Usata per**: livello di database
- **Alimenti**: usata per l'intero database (metodi e legende), non per singole schede

## 16. Conflitti tra fonti

`metadata.source_conflicts`: i casi generali in cui le fonti danno valori diversi, con la decisione presa.

### Molti valori della bozza iniziale non coincidevano con le fonti ufficiali.

- **Perché**: La bozza era stata compilata senza riferimenti puntuali e mescolava fonti e contesti diversi.
- **Decisione**: Vale sempre la fonte ufficiale. Il valore della bozza è registrato come discrepanza nella scheda e, se non verificabile, è tolto dall'app ma conservato a parte.
- **Motivazione**: Nessun dato inventato e nessuna informazione persa.

### CREA, BDA-IEO e USDA danno valori diversi per lo stesso prodotto.

- **Perché**: Campioni, varietà, Paesi e metodi diversi (es. carboidrati 'disponibili' in Europa e 'per differenza' negli USA).
- **Decisione**: Ordine di priorità: CREA, poi BDA-IEO (anche per completare i nutrienti mancanti), USDA solo se mancano le prime due. La fonte è indicata per ogni valore.
- **Motivazione**: Le tabelle italiane descrivono i prodotti venduti in Italia.

### I calendari italiani non sempre coincidono sui mesi di stagione.

- **Perché**: Considerano territori, varietà e coltivazioni (pieno campo, serra) diversi.
- **Decisione**: Per ogni mese e macro-area si contano le fonti che lo indicano: con almeno metà dei voti il mese è di stagione, con meno è inizio o fine stagione; il picco sono i mesi centrali di un periodo di almeno tre mesi in cui tutte le fonti concordano.
- **Motivazione**: Il voto riduce il peso di una singola fonte e la regola è la stessa per tutti i prodotti.

### EUFIC dà i dati per Paese, non per zona climatica, e non elenca tutti i prodotti.

- **Perché**: Ogni Paese ha la sua fonte nazionale e i Paesi stanno in più zone.
- **Decisione**: Ogni Paese è assegnato alla zona prevalente; le zone mancanti sono colmate con fonti nazionali indicate da EUFIC o, per la zona mediterranea, con la stagionalità del Sud Italia. La provenienza è indicata zona per zona.
- **Motivazione**: Approssimazione dichiarata, utile per chi usa l'app fuori dall'Italia.

### Alcuni prodotti (tartufi, ovolo, pesca noce) non compaiono nei calendari di stagione italiani.

- **Perché**: I calendari trattano frutta e verdura coltivate e non distinguono forme della stessa specie (pesca e pesca noce).
- **Decisione**: Si usa la fonte più autorevole disponibile per quel prodotto: la legge sui periodi di raccolta per i tartufi, una scheda micologica istituzionale per l'ovolo, la stagionalità della pesca per la pesca noce. La fonte è indicata in seasonality.italy_source o nelle note.
- **Motivazione**: Meglio una stagionalità da fonte specifica e dichiarata che un vuoto.

### Per cetriolo, melanzana, peperoni e agrumi FoodKeeper indica il frigorifero, la guida UC Davis la temperatura ambiente.

- **Perché**: FoodKeeper guarda alla sicurezza e alla durata, la guida UC Davis al gusto: questi prodotti soffrono il freddo e in frigo perdono qualità.
- **Decisione**: Il 'dove' segue la guida UC Davis, le durate seguono FoodKeeper; l'etichetta breve riporta entrambe le opzioni e la scelta è spiegata nella scheda.
- **Motivazione**: Per un'app sulla stagionalità conta mantenere il sapore, senza nascondere l'alternativa.

### Le durate di HB66 (settimane o mesi) sono molto più lunghe di quelle di FoodKeeper (giorni).

- **Perché**: HB66 si riferisce a celle professionali a temperatura e umidità ottimali; FoodKeeper a un frigorifero di casa.
- **Decisione**: Sono due campi distinti: durata domestica e durata professionale. Una durata professionale non viene mai usata come durata domestica.
- **Motivazione**: Evita promesse irrealistiche all'utente.

### Soglia di danno da freddo e punto di congelamento sono spesso dati come intervalli.

- **Perché**: Dipendono da varietà, maturazione e zuccheri disciolti.
- **Decisione**: Si usa l'estremo più alto (il più prudente) e si conserva l'intervallo quando disponibile. Se il danno avviene in una fascia (drupacee 2-8 °C) non si indica una soglia unica.
- **Motivazione**: Un consiglio prudente non danneggia il prodotto.

### La tabella riassuntiva di HB66 contiene alcuni refusi (es. 1310 per il radicchio) e molti prodotti non sono misurati a 5 °C.

- **Perché**: Errori di impaginazione del PDF; i prodotti sensibili al freddo non vengono studiati a basse temperature.
- **Decisione**: Ordine: classe della tabella di Kader, poi valori dei capitoli, poi stima a 5 °C con i Q10 di HB66 (marcata come stimata). I valori palesemente errati non sono usati.
- **Motivazione**: Usare per prima la classificazione dell'autore di riferimento.

### Le impronte ambientali variano molto tra studi e banche dati.

- **Perché**: Metodi, Paesi, rese e confini del sistema diversi (dal campo all'azienda, o fino al consumo).
- **Decisione**: Si usa SU-EATABLE LIFE (mediana armonizzata) con numero di studi e intervallo; AGRIBALYSE solo per le erbe che mancano, con i confini dichiarati.
- **Motivazione**: Valori confrontabili tra prodotti e incertezza trasparente.

### Alcuni testi scritti fondendo più fonti citavano durate o nutrienti diversi dai dati strutturati.

- **Perché**: I testi riprendevano fonti italiane divulgative, i dati vengono da banche dati ufficiali.
- **Decisione**: I dati strutturati prevalgono: le etichette di conservazione e le liste 'ricco di / fonte di' sono state riallineate ai dati e ai claim UE.
- **Motivazione**: L'app non deve dire due cose diverse sullo stesso prodotto.

### Per alcuni prodotti una fonte non ha una voce esatta.

- **Perché**: Le banche dati internazionali non coprono tutte le specialità italiane (es. cicoria da taglio, cime di rapa, valerianella).
- **Decisione**: Si usa la voce più vicina, sempre marcata 'approssimata' e indicata nella scheda.
- **Motivazione**: Un dato approssimato dichiarato è più utile di un vuoto, purché trasparente.

### Il nome d'uso di una varietà può differire da quello registrato.

- **Perché**: I registri usano la denominazione ufficiale (es. 'Spadona' per Spadonino, 'Detroit 2' per Detroit).
- **Decisione**: Si mostra il nome d'uso e si riporta il nome registrato con il Paese di iscrizione.
- **Motivazione**: Leggibilità per l'utente e verificabilità sul registro.

## 17. Come usarlo nell'app (suggerimento)

| Schermata | Campi |
|---|---|
| Card dell'alimento | `names`, `images.primary`, stato del mese da `seasonality.italy_macro_areas[zona]`, `ripening_and_storage.card_short_storage`, `perishability.label` |
| Lista della spesa | `buying_guide.shopping_list_preview`, `ripening_badge_label` |
| Conservazione | `home_storage`, `storage_instructions`, `estimated_shelf_life_days`, `storage_compatibility`, `ethylene_compatibility` |
| Nutrizione | `reference_portion`, `macros_per_100g`, `nutrition_claims_eu`, `vitamins`, `minerals`, `allergens_eu` |
| Sostenibilità | `environmental_footprint.sustainability_rating`, `greenhouse_comparison`, `metadata.sustainable_diet_summary` |
| Territorio | `notable_varieties`, `dop_igp_labels`, `traditional_products_pat`, `varieties_registered_italy` |
| Orto | `agricultural_calendar_italy` |
| Approfondimenti | `sources_by_topic.useful_links` |
| Aiuto "?" | `metadata.field_help`, `metadata.vocabulary`, `item.help_refs` → `metadata.glossary` |
| Fonti | `metadata.official_sources`, `metadata.source_conflicts` |
