# Peak Season – Database della frutta e verdura di stagione

Un database aperto, bilingue (italiano/inglese) e **interamente basato su fonti verificabili**, che descrive **153 prodotti** freschi: quando sono di stagione in Italia e in Europa, come sceglierli, come conservarli, cosa contengono e quanto pesano sull'ambiente.

È la fonte di verità dell'app **Peak Season** ([peak-season-app](https://github.com/NunzioLangiulli/peak-season-app)), ma è pensato per essere usato **anche senza l'app**: ogni regola che l'app applica è scritta dentro il database stesso.

| | |
|---|---|
| Prodotti | 153 – 72 verdure, 55 frutti, 10 erbe e spezie, 10 funghi, 6 cereali/legumi freschi |
| Fonti | 46 fonti ufficiali e scientifiche, elencate in `metadata.official_sources` |
| Stagionalità | 3 macro-aree italiane + 6 zone climatiche europee (EUFIC/EEA, 29 Paesi) |
| Lingue | ogni testo per l'utente è `{ "it": …, "en": … }` |
| File | [`data/database.json`](data/database.json) (~10 MB), regole formali in [`data/schema.json`](data/schema.json) |

---

## 1. La ratio: perché esiste questo database

Le informazioni sulla stagionalità che si trovano online sono spesso **in contraddizione tra loro**, copiate da un sito all'altro senza indicare la fonte, e non dicono quasi mai *per quale zona* valgono. Lo stesso vale per i consigli di conservazione e per i valori nutrizionali.

L'obiettivo di Peak Season è opposto: **pochi prodotti, ma ogni dato tracciabile fino alla sua fonte**. Quando le fonti non sono d'accordo, il database non sceglie in silenzio: lo dichiara, spiega come ha deciso e conserva l'alternativa.

## 2. Le regole di rigore

Queste regole valgono per ogni campo del database e sono state seguite in tutto il lavoro.

1. **Nessun dato inventato.** Ogni valore viene da una fonte citata. Se un dato non esiste, il campo resta `null` e viene elencato in `data_completeness.missing_fields`: una lacuna dichiarata è meglio di un numero plausibile.
2. **`null` ≠ "non pertinente".** Un campo che non ha senso per un prodotto (per esempio la soglia di danno da freddo per chi non soffre il freddo, o la nutrizione di un tartufo) è elencato in `data_completeness.not_applicable_fields`, così è distinguibile da una vera lacuna.
3. **La fonte ufficiale vince, ma niente viene buttato.** Il progetto è partito da una bozza di 91 prodotti con valori e link in gran parte non verificati. Ogni valore della bozza smentito da una fonte ufficiale è stato sostituito, e il vecchio valore è stato conservato come discrepanza in `data_completeness.notes`. I valori non verificabili sono stati tolti dalla scheda e archiviati in [`data/draft_legacy_values.json`](data/draft_legacy_values.json), con il motivo.
4. **I conflitti tra fonti sono documentati.** I casi in cui fonti autorevoli si contraddicono (13 tipologie) sono descritti in `metadata.source_conflicts`, con la regola usata per risolverli.
5. **Ogni scheda dice da dove viene.** I blocchi strutturati portano la fonte accanto al valore (`source`, `basis`, `source_food`, `derivation`); tutte le fonti di una scheda sono in `sources_by_topic.sources_used`, i link utili in `useful_links`.
6. **Le stime sono marcate come stime.** Dove manca il dato di una zona, il database contiene una stima copiata dalla zona climatica più simile, tenuta separata dai dati veri (`seasonality.estimates`), con il metodo in `metadata.seasonality_estimates_method`. Non si fa mai una stima a partire da un'altra stima.
7. **Banche dati, non letteratura sparsa.** Composti bioattivi, polifenoli e carotenoidi vengono solo da banche dati ufficiali (USDA, Phenol-Explorer), senza scegliere a mano singoli articoli scientifici.
8. **Il database prima dell'app.** Ogni regola usata dall'app (colori degli stati, soglie, ordine dei calendari, nomi delle famiglie botaniche, codici dei Paesi, regole dei claim…) è scritta nel database, in `metadata`. Chi usa solo il JSON ha le stesse informazioni dell'app.
9. **Tutto bilingue, senza mescolare le lingue.** I testi per l'utente sono `{it, en}`; i valori codificati (`"fridge"`, `"climacteric"`…) si traducono con `metadata.vocabulary`. I nomi propri e i nomi registrati (DOP/IGP, varietà) restano nella lingua originale. Le note interne di lavoro (`data_completeness.notes`) sono in italiano.
10. **Convenzioni di forma.** Le etichette brevi hanno l'iniziale maiuscola a ogni parola ("In Frigorifero", "Non Climaterico"); le frasi e i nomi ufficiali no. La terminologia per l'utente è "prodotto/prodotti" (EN *produce/items*).

### Regola di ammissione di un prodotto

Un prodotto entra nel database se ha **almeno 2 fonti** di stagionalità o conservazione **e** una scheda nutrizionale ufficiale (CREA o BDA-IEO). I candidati scartati e il motivo sono in [`data/excluded_candidates_report.md`](data/excluded_candidates_report.md). Alcune deroghe decise esplicitamente (per esempio il tartufo bianco, senza nutrizione ufficiale) sono documentate nelle note della scheda.

## 3. Come vengono calcolati i dati principali

### Stagionalità – voto tra fonti

Per ogni mese e ogni area si calcola un punteggio `s = voti / fonti disponibili`:

- voto **1** se la fonte indica il mese "di stagione" (WWF, Greenpeace, Altroconsumo, EUFIC-Italia, raccolta di Orto da Coltivare);
- voto **0,5** se la fonte indica "primizia" o "tardivo".

| Punteggio | Stato |
|---|---|
| `s ≥ 0,5` | **In Stagione** |
| `0 < s < 0,5` | **Primizia** se precede la stagione, **Fine Stagione** se la segue |
| `s = 0` | **Fuori Stagione** |
| mesi interni di un periodo di almeno 3 mesi su cui **tutte** le fonti (almeno 2) concordano | **Picco** |
| frutto esotico senza produzione italiana | **Non Applicabile** |
| nessuna fonte | `null` (lacuna dichiarata) |

Per le zone europee si usa la quota dei Paesi della zona (EUFIC, 29 Paesi, assegnati alla regione biogeografica EEA prevalente) che segnalano il prodotto di stagione. Le zone che EUFIC non copre sono state completate da fonti nazionali: la zona alpina dal calendario del Ministero della Salute austriaco, quella mediterranea dal Sud e Isole italiano.

Per le **macro-aree italiane** (Nord, Centro, Sud e Isole; l'Abruzzo è nel Centro) la curva è stata rifinita con la raccolta in pieno campo, distinguendo tre casi: prodotti deperibili estivi, buchi brevi da chiudere e prodotti da conservazione naturale, per i quali raccolta e disponibilità sono diverse (`seasonality.availability_note`). Il metodo completo è in `metadata.seasonality_method` e `metadata.seasonality_curve_method`; la provenienza di ogni curva è in `seasonality.curve_basis`.

### Conservazione e post-raccolta

- **Respirazione ed etilene**: classi di Kader (UC Davis, USDA Agricultural Handbook 66). Da qui vengono la **deperibilità** (6 livelli, `metadata.perishability_legend`) e l'elenco dei prodotti da **tenere lontani** (`keep_away_from`: produttori forti di etilene per i prodotti sensibili).
- **Danno da freddo e gelo**: HB66, tabelle 1 e 2.
- **Dove conservarlo in casa**: guida UC Davis/Kader *Storing Fresh Fruits and Vegetables for Better Taste* + USDA FoodKeeper per le durate domestiche.
- **Conservazione compatibile**: gruppi di Thompson (HB66, tabella 1).

### Nutrizione

- Composizione da **CREA** (tabelle 2019) e **BDA-IEO**; USDA FoodData Central solo per i prodotti che non compaiono nelle banche dati italiane.
- **% VNR** sui Valori Nutritivi di Riferimento del Reg. UE 1169/2011 (Allegato XIII).
- **Claim nutrizionali** calcolati con le soglie esatte del Reg. CE 1924/2006 (regole in `metadata.nutrition_claims_eu_rules`).
- **Proteine**: oltre al claim UE, confronto con i LARN SINU 2014. Se 100 g coprono meno del 10% del fabbisogno, il claim resta (è legale) ma viene affiancato da una nota che lo contestualizza.
- **Allergeni** (Reg. UE 1169/2011, Allegato II) e **porzioni** standard (LARN / IEO SmartFood).

### Sostenibilità

Impronta di carbonio (kg CO₂eq/kg) e impronta idrica (L/kg) dal database **SU-EATABLE LIFE** (Petersson et al. 2021, CC BY 4.0), AGRIBALYSE 3.1 per le erbe aromatiche. Le soglie Bassa/Media/Alta sono una **convenzione dichiarata** del progetto (`metadata.environmental_footprint_method.levels`), non un dato delle fonti.

### Varietà, territori e botanica

- **DOP e IGP** verificate sul registro UE eAmbrosia.
- **Varietà** verificate su più fonti testuali e sul Catalogo comune UE delle varietà; codici di specie UPOV e numero di varietà iscritte in Italia.
- **Prodotti Agroalimentari Tradizionali**: elenco MASAF (XXVI revisione, 2026); Presìdi e Arca del Gusto Slow Food.
- **Botanica**: nome scientifico e famiglia verificati su EPPO, World Flora Online e GBIF (funghi).

### Immagini

Fino a 5 tipi di vista per prodotto (foto principale, sfondo neutro, pianta in campo, tavola botanica, sezione). Sono ammesse solo foto con licenza libera (Wikimedia Commons, USDA ARS, Unsplash, Pixabay, iNaturalist CC0/CC BY/CC BY-SA), orizzontali e di almeno 1000 px, senza piatti né scritte, scelte a mano tra almeno 2 candidate per tipo. Autore, licenza e pagina di origine di ogni foto sono in [`assets/images/_metadata.json`](assets/images/_metadata.json). I file delle foto non sono in questo repository: le versioni ottimizzate sono nel repository dell'app.

## 4. Struttura di una scheda

Ogni prodotto segue lo stesso schema a blocchi (esempio completo, blocco per blocco, sul pomodoro in [`data/database_guide.md`](data/database_guide.md)):

| Blocco | Contenuto |
|---|---|
| `id`, `names`, `category` | identificativo `nome_it_name_en`, nomi IT/EN e sinonimi, categoria |
| `botany` | nome scientifico, famiglia, parte della pianta, classificazione |
| `italian_varieties_and_territories` | varietà verificate, DOP/IGP, PAT, Slow Food |
| `images` | foto con tipo di vista, autore e licenza |
| `seasonality` | stati mese per mese per macro-aree italiane e zone EUFIC, stime separate |
| `agricultural_calendar_italy` | semina, trapianto e raccolta per Nord/Centro/Sud |
| `buying_guide` | come sceglierlo |
| `ripening_and_storage` | climaterico, etilene, temperature, durate, dove conservarlo |
| `nutrition_and_sustainability` | composizione per 100 g, VNR, claim, composti bioattivi, allergeni, impronte |
| `sources_by_topic` | fonti per argomento e link utili |
| `data_completeness` | lacune, campi non pertinenti, discrepanze con la bozza, note di lavoro |
| `help_refs` | collegamenti al glossario per le icone "?" |

Il blocco `metadata` contiene legende, metodi, glossario (44 voci), vocabolario dei valori codificati, testi di aiuto dei campi, catalogo delle fonti e le regole di visualizzazione usate dall'app.

**Corpus condiviso.** Le descrizioni ripetute in più prodotti sono salvate una volta sola in `shared_descriptions_corpus`, e le schede vi puntano con `{ "corpus_ref": …, "specific_addition": … }`. Chi legge il JSON direttamente deve sostituire il riferimento con il testo del corpus (lo fa `scripts/common.py → load_json`).

## 5. Contenuto del repository

```
data/
  database.json              il database
  schema.json                JSON Schema (tipi, valori ammessi, campi obbligatori)
  database_guide.md          guida al database, blocco per blocco
  scraping_report.md         report di affidabilità e lacune
  audit_findings.json        esito del ricontrollo voce per voce
  seasonality_audit.json     controllo delle curve stagionali
  template_coverage.json     copertura dei campi del modello iniziale
  items_index.json           codici e URL esatti di ogni prodotto su ogni fonte
  draft_legacy_values.json   valori della bozza iniziale non verificabili, con il motivo
  merged_items_archive.json  prodotti uniti ad altri
  excluded_candidates_report.md  prodotti candidati non ammessi
  ui_copy.json, ui_config.json   testi e icone dell'interfaccia dell'app
scripts/                     pipeline Python che costruisce e verifica il database
  config/                    tabelle curate a mano dalle fonti, con citazioni e pagine
  texts/                     testi descrittivi IT/EN
  README.md                  ordine di esecuzione della pipeline (fonte di verità)
admin_studio/                dashboard locale per modificare testi, immagini, icone e fonti
assets/images/_metadata.json crediti e licenze delle foto
```

## 6. La pipeline

Il database non è scritto a mano: è prodotto da circa 90 script Python, ognuno con un solo compito e una docstring che spiega le fonti usate. L'ordine di esecuzione è in [`scripts/README.md`](scripts/README.md). In sintesi:

1. **Fonti e indice** – download e cache delle fonti, lista master dei prodotti con i codici su ogni fonte.
2. **Arricchimento** – nutrizione, stagionalità, botanica, varietà, conservazione, composti, allergeni, sostenibilità, testi, immagini.
3. **Localizzazione e aiuto** – testi bilingui, vocabolario, glossario, catalogo delle fonti, regole per l'app.
4. **Controlli** – validazione con JSON Schema (`validate_db.py`), ricontrollo voce per voce (`audit_db.py`), copertura del modello (`template_coverage.py`), report finali.

Le modifiche manuali (testi, foto, icone, link) passano dall'**Admin Studio** ([`admin_studio/README.md`](admin_studio/README.md)), che valida il database a ogni salvataggio e annulla la modifica se la validazione fallisce.

### Requisiti

- Python 3.10+
- `python -m pip install -r admin_studio/requirements.txt` (Pillow, jsonschema, requests)
- Per rieseguire gli script di download servono chiavi API proprie (EPPO, Unsplash, Pixabay) in un file `.env`, che non è incluso.

### Cosa non è incluso

Per rispetto delle licenze e per tenere leggero il repository, non sono pubblicati i dati grezzi scaricati dalle fonti (`data/raw/`), i PDF originali delle fonti e i loghi (`fonti_locali/`), le foto in alta risoluzione e la bozza iniziale. Il database contiene comunque tutti i valori estratti e i riferimenti per ritrovarli.

## 7. Usare il database

```python
import json
db = json.load(open("data/database.json", encoding="utf-8"))
corpus = db.get("shared_descriptions_corpus", {})

pomodoro = next(i for i in db["items"] if i["id"] == "pomodoro_tomato")
print(pomodoro["names"]["it"], pomodoro["seasonality"].keys())
```

Per avere i testi già espansi dal corpus condiviso:

```python
import sys; sys.path.insert(0, "scripts")
from common import load_json
db = load_json("data/database.json")
```

## 8. Fonti e licenze

L'elenco completo delle 46 fonti, con URL, argomenti, modalità di accesso e note di licenza, è in `metadata.official_sources`; descrizione e autorevolezza di ciascuna sono nel catalogo delle fonti del database. Tra le principali:

- **Nutrizione:** CREA Alimenti e Nutrizione, BDA-IEO, USDA FoodData Central, LARN SINU 2014, Reg. CE 1924/2006 e Reg. UE 1169/2011
- **Stagionalità:** EUFIC, WWF Italia, Greenpeace Italia, Altroconsumo, Orto da Coltivare, Bio Suisse, Gesundheitsportal (AT), EEA
- **Conservazione:** UC Davis Postharvest Center, USDA Agricultural Handbook 66, USDA FoodKeeper
- **Varietà e territori:** eAmbrosia (UE), EU Plant Variety Portal, UPOV, MASAF (PAT), Fondazione Slow Food
- **Botanica:** EPPO, World Flora Online, GBIF
- **Composti e ambiente:** USDA Flavonoid Database 3.3, Phenol-Explorer 3.6, SU-EATABLE LIFE, AGRIBALYSE 3.1

## 9. Licenza (open source)

- **Codice** (`scripts/`, `admin_studio/`): licenza [MIT](LICENSE).
- **Database e documentazione** (`data/`): [Creative Commons Attribuzione 4.0 (CC BY 4.0)](data/LICENSE-CC-BY-4.0.txt). Puoi riusarli e modificarli liberamente, anche in altri progetti, citando *Peak Season – Nunzio Langiulli* e le fonti originali.
- **Dati di terzi:** la licenza CC BY copre il lavoro originale del progetto, cioè struttura, selezione, regole, calcoli e testi. I singoli valori presi dalle fonti restano soggetti ai termini di ciascuna fonte, indicati in `metadata.official_sources`. In particolare i dati di Phenol-Explorer sono liberi solo per usi non commerciali, e le foto hanno la licenza indicata in `assets/images/_metadata.json`.

Il progetto nasce **senza scopo commerciale**.

---

*Le informazioni hanno scopo divulgativo e non sostituiscono il parere di un medico o di un nutrizionista.*
