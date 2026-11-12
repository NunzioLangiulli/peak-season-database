# Peak Season – Report Fase 1: costruzione, organizzazione e validazione del database

Generato il 2026-11-12 da `scripts/make_report.py` · database v2.0.0 · 153 alimenti · schema `data/schema.json` (JSON Schema 2020-12).

Il report spiega con quale metodo è stato costruito il database, come è organizzato (schede, metadati, fonti, glossario, bilinguismo) e come è stato controllato. Le immagini hanno un report a parte, dopo la tua revisione. La guida campo per campo è in `data/database_guide.md`.

## 1. In sintesi

| Voce | Valore | Note |
|---|---|---|
| Alimenti | 153 | Verdura 72, Frutta 55, Erbe e spezie 10, Funghi 10, Cereali 6 |
| Fonti catalogate | 46 | ognuna con descrizione, autorevolezza, contenuti e usi (§4) |
| Fonti usate per alimento | media 21.0 | `sources_by_topic.sources_used` |
| Casi di conflitto tra fonti documentati | 13 | con decisione e motivazione (§5) |
| Voci di glossario (icone "?") | 44 | 35 campi collegati, 684 rimandi negli alimenti |
| Testi bilingui {it, en} | 7105 | tutto ciò che l'utente legge esiste in italiano e in inglese (§3.4) |
| Validazione schema | 0 errori sui dati | restano solo i file immagine eliminati durante la tua revisione (0 segnalazioni) |
| Ricontrollo sistematico (dati) | 1 errori, 9 da controllare, 23 informativi | tutti spiegati (§6.3) |
| Valori ancora da verificare | 655 | quasi tutti calendari agricoli di frutta, erbe e cereali (§7) |
| Campi senza dato | 2785 | lacune vere, mappate in §7 |
| Campi non pertinenti, motivati | 1749 | es. danno da freddo per chi non è sensibile |

## 2. Come è stato costruito

### 2.1 Principi

- **Nessun dato inventato.** Ogni valore viene da una fonte catalogata, indicata nel campo `source` o nel blocco `sources_by_topic`; dove una fonte manca il campo resta vuoto (null) ed è elencato in `data_completeness.missing_fields`.
- **Fonti ufficiali e scientifiche prima di tutto**, con un ordine di priorità dichiarato per argomento (es. nutrizione: CREA → BDA-IEO → USDA FoodData Central).
- **Tracciabilità per valore**: per i nutrienti la fonte è indicata valore per valore; per i dati post-raccolta il capitolo o la tabella HB66; per le impronte il numero di studi e l'intervallo.
- **Approssimazioni dichiarate**: se una fonte non ha la voce esatta si usa la più vicina, marcata come approssimata; le stime (es. classe di respirazione da Q10) sono marcate come stimate e spiegate nel campo `basis`.
- **Non pertinente ≠ mancante**: un campo che per definizione non si applica (es. danno da freddo per chi non lo soffre) è marcato N/A con motivazione, non conteggiato come lacuna.
- **La bozza iniziale come punto di partenza, non come fonte**: i suoi 91 alimenti sono stati migrati nella struttura; ogni valore diverso dalle fonti è registrato come discrepanza, ogni valore non verificabile è tolto dall'app e conservato in `data/draft_legacy_values.json` (1092 valori). Copia della bozza in `data/_backup_bozza_2026-11-04/`.

### 2.2 Pipeline

Il database è prodotto da script Python eseguiti in un ordine fisso (`scripts/README.md`). Ogni script ha una docstring con fonte, metodo e uso.

| Fase | Cosa fa |
|---|---|
| 1. Fonti e indice | scarica e mette in cache le fonti (`data/raw/`), costruisce la lista master con i codici di ogni fonte, migra la bozza |
| 2. Nutrizione | CREA e BDA-IEO, USDA per i mancanti, %VNR e claim UE ricalcolati, riferimento LARN per le proteine |
| 3. Stagionalità e botanica | voto tra i calendari italiani, mappa EUFIC e fonti nazionali EUFIC; EPPO, WFO, GBIF; note di coltivazione |
| 4. Varietà e territori | verifica delle varietà su testi, Slow Food e Catalogo comune UE; DOP/IGP su eAmbrosia; codici UPOV; PAT MASAF |
| 5. Conservazione | USDA HB66 (tabelle e capitoli), classi di Kader, FoodKeeper e guida UC Davis per la casa, gruppi di compatibilità |
| 6. Composti, allergeni, sostenibilità | USDA carotenoidi e flavonoidi, Phenol-Explorer, Reg. UE 1169/2011, porzioni LARN, SU-EATABLE LIFE, AGRIBALYSE |
| 7. Testi, immagini, fonti | testi IT/EN riallineati ai dati, immagini con licenza, registro delle fonti per alimento |
| 8. Bilinguismo e aiuto | `localize_fields.py` (ultimo passo di trasformazione), `build_help.py` (vocabolario, glossario), `build_source_catalog.py` (catalogo fonti e conflitti) |
| 9. Controlli e report | validazione JSON Schema, ricontrollo voce per voce, copertura del template, report |

Le scelte che richiedono giudizio (citazioni dai capitoli HB66, mappature tra voci di fonti diverse, descrizioni delle fonti, glossario, conflitti) sono in file di configurazione curati a mano in `scripts/config/`, ciascuno con la citazione o la pagina della fonte: così ogni decisione è leggibile e modificabile senza toccare il codice.

## 3. Come è organizzato

Il file `data/database.json` ha due parti: `metadata` (tutto ciò che vale per l'intero database) e `items` (una scheda per alimento).

### 3.1 La scheda di un alimento

| Blocco | Contenuto |
|---|---|
| `id, names, category` | identità: id stabile, nomi IT/EN (comune, alternativi), categoria |
| `botany` | nome scientifico, famiglia, genere, codici EPPO/GBIF/UPOV, parte della pianta usata |
| `italian_varieties_and_territories` | varietà verificate (Catalogo comune UE, Slow Food, testi), DOP/IGP (eAmbrosia), PAT (MASAF), varietà iscritte in Italia |
| `images` | galleria con autore, licenza e URL d'origine di ogni foto |
| `seasonality` | stato mese per mese per 3 macro-aree italiane e 6 zone climatiche europee, con provenienza zona per zona |
| `agricultural_calendar_italy` | semina, trapianto, raccolta per macro-area; parametri di coltivazione |
| `buying_guide` | come sceglierlo, segni di qualità e di deterioramento |
| `ripening_and_storage` | climaterico/non climaterico, etilene, respirazione e deperibilità, danno da freddo, conservazione professionale e domestica, compatibilità |
| `nutrition_and_sustainability` | valori per 100 g con fonte per valore, %VNR, claim UE, composti bioattivi, allergeni, porzioni LARN, impronta di carbonio e idrica |
| `sources_by_topic` | fonti usate per argomento e link utili |
| `data_completeness` | campi mancanti, da verificare, non pertinenti, discrepanze con la bozza, note |
| `help_refs` | voci del glossario pertinenti a quell'alimento (icone "?") |

### 3.2 I metadati

| Campo | Contenuto |
|---|---|
| `official_sources` | catalogo delle fonti: cos'è, perché è autorevole, cosa offre, per quali argomenti e alimenti è stata consultata |
| `source_conflicts` | casi generali di valori discordanti tra fonti: perché, cosa si è deciso e perché |
| `glossary` | spiegazioni brevi ma complete dei concetti, con fonti, per le icone "?" |
| `vocabulary` | etichette IT/EN di tutti i valori codificati (es. `climaterico` → "Climaterico" / "Climacteric"), con il rimando al glossario |
| `field_help` | quale voce del glossario spiega ogni campo |
| legende e metodi | stati stagionali, zone EUFIC, macro-aree, metodo di stagionalità, post-raccolta, deperibilità, conservazione, impronte |
| `sustainable_diet_summary` | sintesi EUFIC sulla dieta sostenibile |

### 3.3 Il sistema di aiuto (icone "?")

Una spiegazione è scritta una volta sola, nel glossario, e raggiunta da più punti:

- **dal campo**: `metadata.field_help` collega 35 percorsi di campo (es. `ripening_and_storage.ripening_type`) alle voci che li spiegano;
- **dal valore**: ogni valore di `metadata.vocabulary` (24 gruppi) può puntare a una voce (es. `climaterico` → voce *climacteric*);
- **dall'alimento**: `item.help_refs` elenca le voci pertinenti per quell'alimento e i campi dove mostrarle, calcolate dal contenuto (allergeni, glutine, DOP, PAT, favismo per la fava, stime Q10, coltura in serra…);
- **da una voce all'altra**: `see_also`; e **dalla fonte**: `official_sources[].used_for.glossary_entries`.

Ogni voce ha `term`, `short` (una riga per il tooltip) e `text` (spiegazione completa) in IT e EN, e le fonti con nome e URL risolti dal catalogo. L'app quindi non contiene testi di aiuto propri: legge tutto dal database.

Voci: *Frutto Climaterico*, *Prodotto Non Climaterico*, *Etilene*, *Produzione di Etilene*, *Sensibilità all'Etilene*, *Tienilo Lontano da*, *Respirazione e Classe di Kader*, *Deperibilità*, *Q10 (Stima della Respirazione)*, *Danno da Freddo*, *Temperatura Minima Sicura*, *Punto di Congelamento*, *Sensibilità al Gelo*, *Condizioni Ottimali (Professionali)*, *Durata in Casa*, *Dove Conservarlo in Casa*, *Prodotti da Conservare Insieme*, *Stati della Stagionalità*, *Macro-aree Italiane*, *Zone Climatiche Europee*, *Stima dalla Zona Vicina (≈)*, *Semina, Trapianto e Raccolta*, *Parametri di Coltivazione*, *Parte Edibile*, *VNR (Valori Nutritivi di Riferimento)*, *Claim Nutrizionali UE*, *LARN*, *Porzione di Riferimento*, *Allergeni (Reg. UE 1169/2011)*, *Glutine*, *Carotenoidi*, *Polifenoli*, *Flavonoidi*, *Impronta di Carbonio*, *Impronta Idrica*, *Serra Riscaldata e Stagionalità*, *DOP e IGP*, *Prodotti Agroalimentari Tradizionali (PAT)*, *Presìdi Slow Food e Arca del Gusto*, *Codice UPOV e Catalogo Comune UE*, *Varietà Verificate*, *Nome Scientifico e Codici Botanici*, *Favismo*, *Esatto o Approssimato*.

### 3.4 Bilinguismo

L'app deve funzionare interamente in italiano o interamente in inglese. Convenzioni applicate e verificate dall'audit:

- ogni testo per l'utente è un oggetto `{it, en}`: nomi, testi, etichette, consigli, legende, glossario, descrizioni delle fonti, motivazioni (`basis`, `derivation`, `method`, note delle varietà);
- i valori codificati (categoria, stato stagionale, classi, luoghi di conservazione…) sono chiavi stabili tradotte da `metadata.vocabulary`, mai mostrate così come sono;
- per nutrienti e composti restano le coppie `name`/`name_en`;
- restano nella lingua originale solo i nomi propri: varietà, DOP/IGP, PAT, nomi scientifici, autori, licenze, nomi delle fonti, citazioni testuali delle fonti;
- `data_completeness.notes` è un registro tecnico interno in italiano, non destinato all'app.

## 4. Fonti

Il catalogo completo, con descrizione, autorevolezza, contenuti e l'elenco di tutti gli alimenti per cui ogni fonte è stata consultata, è in testa al database (`metadata.official_sources`) ed è riportato nella guida. Riepilogo:

| Fonte | Alimenti | Usata per |
|---|---|---|
| Regolamento (UE) n. 1169/2011 - Allegato XIII, Valori Nutritivi di Riferime | 153 | Allergeni, %VNR |
| IEO SmartFood - Porzioni e frequenze (porzioni standard LARN-SINU) | 153 | Porzioni |
| EPPO Global Database | 151 | Botanica |
| Regolamento (CE) n. 1924/2006 - indicazioni nutrizionali e sulla salute | 146 | Claim UE |
| LARN - SINU (tabelle riassuntive, PDF locale) | 145 | LARN |
| World Flora Online - Plant List | 143 | Botanica |
| USDA FoodData Central - SR Legacy (2018-04) | 136 | Composti Bioattivi, Nutrizione, Testi |
| USDA ARS Agricultural Handbook 66 (2016) | 133 | Danno da Freddo, Freezing_susceptibility, Plant_part_used, Post-raccolta, Conser |
| SU-EATABLE LIFE - database delle impronte di carbonio e idrica (Petersson e | 129 | Impronta Ambientale |
| Wikimedia Commons API | 124 | Immagini |
| Pixabay API | 124 | Immagini |
| BDA-IEO - Banca Dati di Composizione degli Alimenti (Istituto Europeo di On | 121 | Nutrizione, Testi |
| USDA FSIS FoodKeeper | 120 | Conservazione in Casa, Testi |
| MASAF - Elenco nazionale dei Prodotti Agroalimentari Tradizionali, XXVI rev | 118 | Testi, Prodotti Tradizionali |
| EUFIC - Explore seasonal fruit and vegetables in Europe | 115 | Stagionalità Europea, Testi |
| Orto da Coltivare (Matteo Cereda) - tabelle di semina PDF + schede | 110 | Calendario Agricolo, Plant_part_used, Stagionalità, Testi, Varietà |
| CREA Alimenti e Nutrizione - Tabelle di composizione degli alimenti (rev. 2 | 109 | Nutrizione, Testi |
| My-PersonalTrainer | 109 | Plant_part_used, Varietà, Verification_texts |
| UC Davis / Kader - Storing Fresh Fruits and Vegetables for Better Taste (UC | 107 | Conservazione in Casa |
| USDA Database for the Flavonoid Content of Selected Foods, Release 3.3 (201 | 97 | Composti Bioattivi |
| Phenol-Explorer 3.6 - database del contenuto di polifenoli negli alimenti ( | 86 | Composti Bioattivi |
| UC Davis Postharvest Research and Extension Center - Produce Fact Sheets | 80 | Post-raccolta, Testi |
| EU Plant Variety Portal - Catalogo comune UE delle varieta' (agricole, orti | 76 | Codice UPOV, Varietà |
| Bio Suisse - Calendario stagionale (Svizzera, PDF locale) | 71 | Stagionalità, Testi |
| Altroconsumo - Calendario frutta e verdura | 65 | Buying_guide, Plant_part_used, Stagionalità, Testi, Varietà |
| Unsplash API | 63 | Immagini |
| WWF Italia - Il calendario della frutta e verdura di stagione (PDF locale) | 60 | Stagionalità, Testi |
| Greenpeace Italia - Guida alla frutta e verdura di stagione (PDF locale) | 54 | Stagionalità, Testi |
| eAmbrosia - registro UE delle indicazioni geografiche | 48 | DOP/IGP |
| Fondazione Slow Food per la Biodiversità - Presìdi e Arca del Gusto | 34 | Stagionalità, Varietà |
| GBIF Backbone Taxonomy (funghi) | 10 | Botanica |
| AGRIBALYSE 3.1 (ADEME, Francia) - impatti ambientali degli alimenti | 7 | Impronta Ambientale |
| Provincia di Cuneo - Schede dei funghi commestibili | 3 | Stagionalità |
| Gesundheitsportal Österreichs - Saisonkalender (Ministero della salute aust | 2 | Stagionalità Europea |
| Legge 16 dicembre 1985, n. 752 - Normativa quadro sui tartufi (art. 6, peri | 2 | Stagionalità |
| iNaturalist (solo foto CC0 / CC BY / CC BY-SA) | 1 | Immagini |
| Istituto Superiore di Sanità - Rapporti ISTISAN 09/47 (carenza di G6PD e fa | 1 | Note di Salute |
| Regione Emilia-Romagna, BUR 2012 - Disciplinare IGP Amarene Brusche di Mode | 1 | Stagionalità |
| Biblioteca civica Bertoliana (Vicenza) - Scheda botanica del lampascione | 1 | Stagionalità |
| NaturaSì - Frutta e verdura di stagione (schede prodotto) | 1 | Stagionalità |
| ISMEA Mercati | 0 |  |
| Servizi agricoli regionali (Veneto Agricoltura, ERSA FVG, ARSIAL) | 0 |  |
| EUFIC - European national sources on seasonal fruit and vegetables | tutto il database |  |
| EUFIC - Are seasonal fruit and vegetables better for the environment? | tutto il database |  |
| USDA ARS Image Gallery | 0 |  |
| EEA - Biogeographical regions, Europe 2016 (Agenzia europea dell'ambiente) | tutto il database |  |

Fonti valutate e non usate: ISMEA e calendari regionali per le epoche di raccolta della frutta (nessun dato strutturato per macro-area); USDA ARS Image Gallery (poche immagini pertinenti); calendario MAPA (Spagna), indicato da EUFIC ma non raggiungibile (pagine 404). My-PersonalTrainer è usato solo per testi e link, nessun valore numerico.

## 5. Conflitti tra fonti e decisioni

I casi sono in `metadata.source_conflicts` (IT/EN). In breve:

- **Molti valori della bozza iniziale non coincidevano con le fonti ufficiali.** La bozza era stata compilata senza riferimenti puntuali e mescolava fonti e contesti diversi. → *Decisione:* Vale sempre la fonte ufficiale. Il valore della bozza è registrato come discrepanza nella scheda e, se non verificabile, è tolto dall'app ma conservato a parte. *Perché:* Nessun dato inventato e nessuna informazione persa.
- **CREA, BDA-IEO e USDA danno valori diversi per lo stesso prodotto.** Campioni, varietà, Paesi e metodi diversi (es. carboidrati 'disponibili' in Europa e 'per differenza' negli USA). → *Decisione:* Ordine di priorità: CREA, poi BDA-IEO (anche per completare i nutrienti mancanti), USDA solo se mancano le prime due. La fonte è indicata per ogni valore. *Perché:* Le tabelle italiane descrivono i prodotti venduti in Italia.
- **I calendari italiani non sempre coincidono sui mesi di stagione.** Considerano territori, varietà e coltivazioni (pieno campo, serra) diversi. → *Decisione:* Per ogni mese e macro-area si contano le fonti che lo indicano: con almeno metà dei voti il mese è di stagione, con meno è inizio o fine stagione; il picco sono i mesi centrali di un periodo di almeno tre mesi in cui tutte le fonti concordano. *Perché:* Il voto riduce il peso di una singola fonte e la regola è la stessa per tutti i prodotti.
- **EUFIC dà i dati per Paese, non per zona climatica, e non elenca tutti i prodotti.** Ogni Paese ha la sua fonte nazionale e i Paesi stanno in più zone. → *Decisione:* Ogni Paese è assegnato alla zona prevalente; le zone mancanti sono colmate con fonti nazionali indicate da EUFIC o, per la zona mediterranea, con la stagionalità del Sud Italia. La provenienza è indicata zona per zona. *Perché:* Approssimazione dichiarata, utile per chi usa l'app fuori dall'Italia.
- **Alcuni prodotti (tartufi, ovolo, pesca noce) non compaiono nei calendari di stagione italiani.** I calendari trattano frutta e verdura coltivate e non distinguono forme della stessa specie (pesca e pesca noce). → *Decisione:* Si usa la fonte più autorevole disponibile per quel prodotto: la legge sui periodi di raccolta per i tartufi, una scheda micologica istituzionale per l'ovolo, la stagionalità della pesca per la pesca noce. La fonte è indicata in seasonality.italy_source o nelle note. *Perché:* Meglio una stagionalità da fonte specifica e dichiarata che un vuoto.
- **Per cetriolo, melanzana, peperoni e agrumi FoodKeeper indica il frigorifero, la guida UC Davis la temperatura ambiente.** FoodKeeper guarda alla sicurezza e alla durata, la guida UC Davis al gusto: questi prodotti soffrono il freddo e in frigo perdono qualità. → *Decisione:* Il 'dove' segue la guida UC Davis, le durate seguono FoodKeeper; l'etichetta breve riporta entrambe le opzioni e la scelta è spiegata nella scheda. *Perché:* Per un'app sulla stagionalità conta mantenere il sapore, senza nascondere l'alternativa.
- **Le durate di HB66 (settimane o mesi) sono molto più lunghe di quelle di FoodKeeper (giorni).** HB66 si riferisce a celle professionali a temperatura e umidità ottimali; FoodKeeper a un frigorifero di casa. → *Decisione:* Sono due campi distinti: durata domestica e durata professionale. Una durata professionale non viene mai usata come durata domestica. *Perché:* Evita promesse irrealistiche all'utente.
- **Soglia di danno da freddo e punto di congelamento sono spesso dati come intervalli.** Dipendono da varietà, maturazione e zuccheri disciolti. → *Decisione:* Si usa l'estremo più alto (il più prudente) e si conserva l'intervallo quando disponibile. Se il danno avviene in una fascia (drupacee 2-8 °C) non si indica una soglia unica. *Perché:* Un consiglio prudente non danneggia il prodotto.
- **La tabella riassuntiva di HB66 contiene alcuni refusi (es. 1310 per il radicchio) e molti prodotti non sono misurati a 5 °C.** Errori di impaginazione del PDF; i prodotti sensibili al freddo non vengono studiati a basse temperature. → *Decisione:* Ordine: classe della tabella di Kader, poi valori dei capitoli, poi stima a 5 °C con i Q10 di HB66 (marcata come stimata). I valori palesemente errati non sono usati. *Perché:* Usare per prima la classificazione dell'autore di riferimento.
- **Le impronte ambientali variano molto tra studi e banche dati.** Metodi, Paesi, rese e confini del sistema diversi (dal campo all'azienda, o fino al consumo). → *Decisione:* Si usa SU-EATABLE LIFE (mediana armonizzata) con numero di studi e intervallo; AGRIBALYSE solo per le erbe che mancano, con i confini dichiarati. *Perché:* Valori confrontabili tra prodotti e incertezza trasparente.
- **Alcuni testi scritti fondendo più fonti citavano durate o nutrienti diversi dai dati strutturati.** I testi riprendevano fonti italiane divulgative, i dati vengono da banche dati ufficiali. → *Decisione:* I dati strutturati prevalgono: le etichette di conservazione e le liste 'ricco di / fonte di' sono state riallineate ai dati e ai claim UE. *Perché:* L'app non deve dire due cose diverse sullo stesso prodotto.
- **Per alcuni prodotti una fonte non ha una voce esatta.** Le banche dati internazionali non coprono tutte le specialità italiane (es. cicoria da taglio, cime di rapa, valerianella). → *Decisione:* Si usa la voce più vicina, sempre marcata 'approssimata' e indicata nella scheda. *Perché:* Un dato approssimato dichiarato è più utile di un vuoto, purché trasparente.
- **Il nome d'uso di una varietà può differire da quello registrato.** I registri usano la denominazione ufficiale (es. 'Spadona' per Spadonino, 'Detroit 2' per Detroit). → *Decisione:* Si mostra il nome d'uso e si riporta il nome registrato con il Paese di iscrizione. *Perché:* Leggibilità per l'utente e verificabilità sul registro.

I singoli casi alimento per alimento restano registrati in `data_completeness.discrepancies` (1359 discrepanze tra la bozza e le fonti) e nei campi `basis` e `note`.

## 6. Come è stato validato

Quattro livelli di controllo, tutti rieseguibili.

### 6.1 Schema

`validate_db.py` verifica il database contro `data/schema.json` (tipi, campi obbligatori, valori ammessi, formato dei mesi e dei testi bilingui) e alcuni controlli di coerenza (id, somma acqua+macronutrienti, file immagine presenti). Esito: nessun errore sui dati; gli unici errori sono le immagini che stai eliminando, che spariranno con la sincronizzazione finale.

### 6.2 Verifiche incrociate sulle fonti

- **Botanica**: nome scientifico confrontato tra EPPO, WFO e GBIF; genere coerente con nome scientifico e codice UPOV.
- **Varietà**: mostrate solo se trovate in una fonte (testi delle fonti, Slow Food, Catalogo comune UE, con nome registrato e Paese).
- **DOP/IGP**: ogni denominazione controllata sul registro UE eAmbrosia (stato e categoria).
- **Nutrizione**: calorie ricalcolate dai macronutrienti, %VNR e claim UE ricalcolati dai valori, sale = sodio × 2,5.
- **Post-raccolta**: valori dei capitoli HB66 trascritti con la citazione in `scripts/config/hb66_chapter_curated.json`; refusi evidenti della tabella riassuntiva esclusi.

### 6.3 Ricontrollo sistematico voce per voce

`audit_db.py` controlla ogni scheda: coerenza calorie/macronutrienti, %VNR, claim UE, porzioni e impronte per porzione; stati stagionali e mesi; raccolta rispetto alla stagionalità; intervalli min ≤ max; soglie di danno da freddo e punti di congelamento; durate domestiche rispetto a quelle professionali; luogo di conservazione rispetto alle etichette dei testi; etilene (produttori, "tenere lontano da"); classe di respirazione rispetto alla deperibilità; gruppo di compatibilità rispetto alle temperature; botanica; varietà; DOP/IGP; immagini e licenze; URL delle fonti; completezza dei testi IT/EN e assenza di testo italiano nei campi inglesi. Controlla inoltre i metadati: ogni voce del glossario bilingue e con fonti registrate, rimandi `see_also`, `field_help` e `help_refs` verso voci esistenti, ogni valore codificato presente nel vocabolario, ogni fonte descritta.

Segnalazioni residue sui dati (spiegate, non sono errori):

| Livello | Alimento | Campo | Dettaglio |
|---|---|---|---|
| E | cavolo_nero_black_kale | macros_per_100g.sugars_g | zuccheri 0.99 > carboidrati 0.3 |
| W | cipolla_invernale_winter_onion | storage_compatibility | gruppo 3 (13-18 °C) ma temperatura ottimale {'min': 0.0, 'max': 0.0} |
| W | fagiolino_green_bean | chilling_injury | temperatura ottimale {'min': 5.0, 'max': 7.5} sotto la soglia di danno 7 °C |
| W | pastinaca_parsnip | italy_macro_areas.sud_isole | sempre fuori stagione |
| W | melone_melon | storage_compatibility | gruppo 1B a 0-2 °C ma sensibile al freddo sotto 5 °C |
| W | lampone_raspberry | ripening_type | non climaterico ma forte produttore di etilene |
| W | avocado_avocado | storage_compatibility | gruppo 1B a 0-2 °C ma sensibile al freddo sotto 13 °C |
| W | orzo_barley | macros_per_100g | acqua+macro = 105.8 g/100 g |
| W | maracuja_passion_fruit | chilling_injury | temperatura ottimale {'min': 7.0, 'max': 10.0} sotto la soglia di danno 10 °C |
| W | oliva_olive | chilling_injury | temperatura ottimale {'min': 5.0, 'max': 7.5} sotto la soglia di danno 7 °C |

Spiegazione: il cavolo nero ha zuccheri > carboidrati per come USDA calcola i carboidrati (per differenza) → annotato; l'orzo supera di poco 105 g/100 g sommando acqua e macronutrienti per arrotondamenti della tabella CREA; le soglie "sotto la temperatura ottimale" derivano dall'estremo dell'intervallo minimo sicuro HB66; cipolla secca nel gruppo 3 e melone/avocado nel gruppo 1B sono come nella tabella di compatibilità HB66 (gruppi per lo stoccaggio misto di 7 giorni, non temperature ottimali); le differenze tra etichette e FoodKeeper per peperoncino, banana e melograno sono volute (guida UC Davis per il gusto).

### 6.4 Copertura del template e riproducibilità

`template_coverage.py` verifica, per ognuno dei 62 campi del modello JSON del prompt, quanti alimenti hanno un dato verificato: 16 campi sono completi per tutti i 153 alimenti (dettaglio in `data/template_coverage.json`). Infine il tratto finale della pipeline è stato rieseguito da un'istantanea precedente: il risultato coincide con il database consegnato (la riesecuzione ha anche fatto emergere e correggere una dipendenza d'ordine nel registro delle fonti).

## 7. Dati recuperati e lacune residue

Recuperi dell'ultima fase, dalle fonti proposte:

- **Punto di congelamento** ("highest freezing point" di HB66, cioè la temperatura più alta a cui inizia a formarsi ghiaccio; se la fonte dà un intervallo si usa l'estremo più alto, il più prudente): 44 alimenti. Gli altri non hanno il valore nel capitolo HB66.
- **Classe di respirazione**: 130 alimenti; 0 stimate a 5 °C dai valori misurati a temperatura più alta con i Q10 di HB66, marcate come stimate. Restano senza classe: cardo, zucca, castagna, rosmarino, mela cotogna (nessun valore misurato).
- **Impronta di carbonio delle erbe aromatiche**: 7 da AGRIBALYSE 3.1 (ADEME), con confini del sistema dichiarati (fino al consumo, quindi non confrontabile 1:1 con SU-EATABLE LIFE). Impronta idrica non presa da AGRIBALYSE, perché misura la scarsità e non il volume.
- **Stagionalità italiana per alimenti assenti dai calendari**: pesca noce dalla pesca (i calendari non le distinguono; lo confermano l'IGP "Pesca e Nettarina di Romagna" ed EUFIC); tartufo nero e bianco dalla Legge 752/1985, art. 6 (periodi di raccolta); ovolo dalla scheda della Provincia di Cuneo ("estate e inizio autunno"). Fonte in `seasonality.italy_source`.
- **Decisioni sul perimetro (5 novembre)**: bietola da coste e da taglio unite in "Bietola" (stessa specie e stessa scheda CREA); pesca tabacchiera aggiunta come varietà della pesca (Arca del Gusto Slow Food); tartufo bianco aggiunto in deroga alla regola di ammissione (nessuna scheda CREA/BDA: nutrizione vuota e dichiarata). Dalla revisione sistematica degli esclusi (`data/excluded_candidates_report.md`) l'utente ha poi deciso di includere 44 alimenti (tutti tranne bergamotto, cappero, acetosa, corbezzolo e portulaca) anche con campi incompleti: sono stati costruiti con la stessa pipeline, su un database di prova, e poi uniti; dove mancano dati ufficiali il campo resta vuoto e dichiarato. Per 33 di loro la stagionalità italiana viene da fonti specifiche lette a mano (`config/italy_seasonality_curated.json`): periodi di raccolta di Orto da Coltivare, schede Slow Food, schede funghi della Provincia di Cuneo, disciplinare IGP delle amarene; taccola e mirabella riprendono pisello e susina (stessa specie). Per 4 la nutrizione viene da una voce USDA di un prodotto affine, dichiarata come approssimazione.
- **Stime per le zone senza dato** (decisione del 6 novembre): molte zone EUFIC mancano (la pannonica comprende solo l'Ungheria). `seasonality.estimates` contiene, separate dai dati, le stime dalla zona vicina con il clima più simile (es. pannonica <- continentale), marcate nell'app con ≈ e disattivabili dalle Impostazioni; la stima parte sempre da un dato vero. Per i frutti esotici le zone senza dato sono "Non coltivato qui". Metodo in `metadata.seasonality_estimates_method`.
- **Zone climatiche europee**: zona alpina da calendario del Ministero della salute austriaco, fonte nazionale indicata da EUFIC (2 alimenti); zona mediterranea derivata, dichiaratamente, dalla stagionalità di Sud e Isole (23 alimenti). Provenienza in `seasonality.eufic_zone_sources`.

Non recuperabili con fonti accessibili (lacune documentate):

- **Calendari agricoli di frutta, erbe e cereali per macro-area**: né ISMEA né i servizi regionali pubblicano dati strutturati per Nord/Centro/Sud; i valori della bozza restano "da verificare".
- **Varietà locali (L. 194/2015)**: non esiste un elenco nazionale scaricabile, solo registri regionali eterogenei.
- **Zone atlantica, continentale, boreale e pannonica mancanti**: riguardano soprattutto prodotti che lì non si coltivano (agrumi, cachi, nespola, fico d'India); restano vuote.
- **Parametri agronomici di erbe e funghi (CREA-OF)**: non tentato in questa fase.
- **Funghi spontanei e tartufo**: nessuna impronta ambientale (raccolta spontanea, nessuno studio LCA).

Mappa delle lacune (campi senza dato):

| Campo | Alimenti | Quali (primi 10) |
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

## 8. Avvertenze per l'uso nell'app

- **Fonti non italiane**: conservazione (USDA HB66, FoodKeeper, UC Davis), composti bioattivi (USDA, Phenol-Explorer) e alcuni micronutrienti vengono da fonti USA o internazionali; la nutrizione principale è CREA o BDA-IEO.
- **Durate**: la durata domestica (FoodKeeper) e quella professionale (HB66) sono campi distinti; l'app deve mostrare all'utente la prima.
- **Impronte ambientali**: mediane di letteratura con alta variabilità; le soglie basso/medio/alto sono una convenzione dell'app, dichiarata in `basis`.
- **Polifenoli**: valori indicativi per 100 g di prodotto crudo. Phenol-Explorer: uso non commerciale, citare la fonte.
- **Claim UE**: calcolati sul crudo per 100 g (Reg. CE 1924/2006); il claim "proteine" nei prodotti poco calorici è contestualizzato con i LARN.
- **PAT**: collegamento per parole chiave; include anche prodotti trasformati.
- **Testi**: riscritti fondendo più fonti e riallineati ai dati; alcune frasi descrittive (curiosità, usi in cucina) sono di conoscenza generale.

## 9. Stato per alimento

| Alimento | Categoria | Fonti | Voci di aiuto | Da verificare | Mancanti | N/A | Segnalazioni |
|---|---|---|---|---|---|---|---|
| Avena | Cereali | 16 | 3 | 18 | 20 | 22 | 0 |
| Farro | Cereali | 17 | 6 | 17 | 19 | 27 | 0 |
| Grano Duro | Cereali | 18 | 5 | 17 | 19 | 24 | 0 |
| Grano Saraceno | Cereali | 18 | 4 | 17 | 19 | 28 | 0 |
| Orzo | Cereali | 19 | 4 | 18 | 19 | 23 | 1 |
| Riso | Cereali | 19 | 5 | 18 | 20 | 23 | 0 |
| Basilico | Erbe e spezie | 24 | 5 | 1 | 9 | 17 | 0 |
| Erba Cipollina | Erbe e spezie | 16 | 2 | 0 | 28 | 14 | 0 |
| Menta | Erbe e spezie | 23 | 4 | 17 | 20 | 21 | 0 |
| Origano | Erbe e spezie | 18 | 3 | 20 | 18 | 37 | 0 |
| Peperoncino Piccante | Erbe e spezie | 24 | 5 | 2 | 7 | 12 | 0 |
| Prezzemolo | Erbe e spezie | 25 | 4 | 0 | 6 | 16 | 0 |
| Rosmarino | Erbe e spezie | 22 | 4 | 18 | 19 | 22 | 0 |
| Salvia | Erbe e spezie | 21 | 4 | 19 | 21 | 23 | 0 |
| Timo | Erbe e spezie | 22 | 4 | 18 | 20 | 21 | 0 |
| Zafferano | Erbe e spezie | 15 | 3 | 0 | 37 | 18 | 0 |
| Albicocca | Frutta | 29 | 7 | 17 | 11 | 8 | 0 |
| Alchechengi | Frutta | 12 | 1 | 0 | 42 | 8 | 0 |
| Amarena | Frutta | 19 | 5 | 0 | 34 | 10 | 0 |
| Ananas | Frutta | 21 | 4 | 0 | 8 | 31 | 0 |
| Anguria (Cocomero) | Frutta | 27 | 6 | 0 | 3 | 4 | 0 |
| Arancia | Frutta | 28 | 6 | 17 | 12 | 5 | 0 |
| Avocado | Frutta | 23 | 5 | 17 | 4 | 22 | 1 |
| Banana | Frutta | 22 | 4 | 6 | 6 | 22 | 0 |
| Caco (Kaki) | Frutta | 24 | 5 | 19 | 18 | 13 | 0 |
| Carruba | Frutta | 13 | 2 | 0 | 50 | 8 | 0 |
| Castagna | Frutta | 21 | 6 | 24 | 23 | 9 | 0 |
| Cedro | Frutta | 13 | 5 | 0 | 48 | 9 | 0 |
| Chinotto | Frutta | 11 | 4 | 0 | 54 | 10 | 0 |
| Ciliegia | Frutta | 29 | 7 | 17 | 12 | 7 | 0 |
| Clementine | Frutta | 26 | 6 | 20 | 16 | 5 | 0 |
| Cocco | Frutta | 16 | 3 | 0 | 43 | 8 | 0 |
| Fico | Frutta | 26 | 5 | 19 | 15 | 8 | 0 |
| Fico d'India | Frutta | 21 | 5 | 0 | 32 | 12 | 0 |
| Fragola | Frutta | 28 | 6 | 17 | 11 | 7 | 0 |
| Gelso (Mora di Gelso) | Frutta | 17 | 2 | 0 | 25 | 13 | 0 |
| Giuggiola | Frutta | 15 | 2 | 0 | 48 | 8 | 0 |
| Kiwi | Frutta | 27 | 5 | 17 | 16 | 12 | 0 |
| Lampone | Frutta | 28 | 7 | 17 | 11 | 7 | 1 |
| Lime | Frutta | 20 | 3 | 0 | 29 | 7 | 0 |
| Limone | Frutta | 29 | 6 | 17 | 14 | 4 | 0 |
| Litchi | Frutta | 19 | 3 | 0 | 29 | 12 | 0 |
| Mandarino | Frutta | 28 | 7 | 18 | 16 | 5 | 0 |
| Mandorla | Frutta | 17 | 5 | 0 | 31 | 11 | 0 |
| Mango | Frutta | 23 | 5 | 17 | 18 | 10 | 0 |
| Maracuja (Frutto della Passione) | Frutta | 19 | 3 | 0 | 9 | 30 | 1 |
| Mela | Frutta | 29 | 5 | 18 | 11 | 5 | 0 |
| Mela Cotogna | Frutta | 23 | 2 | 0 | 43 | 8 | 0 |
| Melograno | Frutta | 25 | 6 | 17 | 14 | 11 | 0 |
| Melone | Frutta | 27 | 7 | 0 | 2 | 3 | 1 |
| Mirabella | Frutta | 15 | 3 | 0 | 33 | 10 | 0 |
| Mirtillo | Frutta | 28 | 6 | 17 | 11 | 7 | 0 |
| Mirtillo Rosso | Frutta | 17 | 4 | 0 | 36 | 11 | 0 |
| Mora | Frutta | 26 | 4 | 17 | 11 | 7 | 0 |
| Nespola | Frutta | 21 | 5 | 0 | 31 | 16 | 0 |
| Nespola Comune | Frutta | 9 | 2 | 0 | 56 | 8 | 0 |
| Nocciola | Frutta | 18 | 6 | 0 | 33 | 10 | 0 |
| Noce | Frutta | 18 | 6 | 0 | 32 | 10 | 0 |
| Oliva | Frutta | 17 | 5 | 0 | 30 | 15 | 1 |
| Papaya | Frutta | 21 | 4 | 0 | 9 | 31 | 0 |
| Pera | Frutta | 29 | 5 | 17 | 11 | 6 | 0 |
| Pesca | Frutta | 29 | 7 | 18 | 12 | 5 | 0 |
| Pesca Noce | Frutta | 23 | 6 | 0 | 26 | 5 | 0 |
| Pistacchio | Frutta | 19 | 6 | 0 | 27 | 10 | 0 |
| Pompelmo | Frutta | 26 | 5 | 0 | 26 | 7 | 0 |
| Ribes Nero | Frutta | 19 | 2 | 0 | 25 | 12 | 0 |
| Ribes Rosso | Frutta | 25 | 5 | 0 | 28 | 9 | 0 |
| Sambuco (Bacche) | Frutta | 17 | 3 | 0 | 40 | 11 | 0 |
| Susina (Prugna) | Frutta | 29 | 6 | 17 | 11 | 4 | 0 |
| Uva Spina | Frutta | 16 | 2 | 0 | 38 | 12 | 0 |
| Uva da Tavola | Frutta | 27 | 6 | 17 | 11 | 11 | 0 |
| Cardoncello | Funghi | 13 | 4 | 0 | 35 | 15 | 0 |
| Finferlo (Gallinaccio) | Funghi | 16 | 4 | 0 | 27 | 12 | 0 |
| Fungo Champignon (Prataiolo) | Funghi | 20 | 4 | 12 | 14 | 16 | 0 |
| Fungo Pleurotus (Orecchione) | Funghi | 19 | 4 | 15 | 16 | 16 | 0 |
| Fungo Porcino | Funghi | 18 | 5 | 13 | 17 | 12 | 0 |
| Ovolo Buono | Funghi | 14 | 3 | 0 | 28 | 13 | 0 |
| Shiitake | Funghi | 13 | 3 | 0 | 34 | 15 | 0 |
| Spugnola | Funghi | 14 | 3 | 0 | 28 | 12 | 0 |
| Tartufo Bianco | Funghi | 9 | 4 | 0 | 44 | 21 | 0 |
| Tartufo Nero | Funghi | 13 | 4 | 0 | 31 | 22 | 0 |
| Aglio | Verdura | 30 | 6 | 0 | 2 | 14 | 0 |
| Agretti (Barba di Frate) | Verdura | 14 | 2 | 0 | 32 | 10 | 0 |
| Arachide | Verdura | 19 | 2 | 0 | 9 | 22 | 0 |
| Asparago | Verdura | 29 | 5 | 0 | 1 | 5 | 0 |
| Asparago Selvatico | Verdura | 15 | 4 | 0 | 33 | 11 | 0 |
| Barbabietola Rossa | Verdura | 26 | 4 | 0 | 1 | 8 | 0 |
| Bietola | Verdura | 25 | 5 | 1 | 4 | 7 | 0 |
| Broccolo Romanesco | Verdura | 18 | 5 | 0 | 30 | 11 | 0 |
| Carciofo | Verdura | 29 | 7 | 0 | 3 | 7 | 0 |
| Cardo | Verdura | 18 | 5 | 11 | 13 | 7 | 0 |
| Carota | Verdura | 29 | 7 | 0 | 0 | 7 | 0 |
| Cavoletti di Bruxelles | Verdura | 23 | 3 | 0 | 0 | 7 | 0 |
| Cavolfiore | Verdura | 28 | 6 | 0 | 1 | 6 | 0 |
| Cavolo Broccolo | Verdura | 25 | 4 | 0 | 1 | 7 | 0 |
| Cavolo Cappuccio | Verdura | 26 | 4 | 0 | 0 | 7 | 0 |
| Cavolo Cinese (Pak Choi) | Verdura | 15 | 3 | 0 | 23 | 11 | 0 |
| Cavolo Nero Toscano | Verdura | 25 | 5 | 1 | 3 | 6 | 1 |
| Cavolo Rapa | Verdura | 20 | 4 | 0 | 2 | 10 | 0 |
| Cavolo Rosso | Verdura | 23 | 4 | 0 | 22 | 7 | 0 |
| Cavolo Verza | Verdura | 24 | 4 | 0 | 1 | 7 | 0 |
| Cece | Verdura | 17 | 4 | 0 | 9 | 29 | 0 |
| Cetriolo | Verdura | 27 | 6 | 0 | 2 | 6 | 0 |
| Cicerchia | Verdura | 9 | 3 | 0 | 66 | 8 | 0 |
| Cicoria da Cespo (Catalogna / Pan di Zucchero) | Verdura | 21 | 4 | 0 | 5 | 8 | 0 |
| Cicoria da Taglio (Spadonino) | Verdura | 18 | 3 | 0 | 8 | 8 | 0 |
| Cime di Rapa | Verdura | 23 | 4 | 1 | 9 | 12 | 0 |
| Cipolla Estiva (Bianca/dorata) | Verdura | 26 | 6 | 0 | 0 | 7 | 0 |
| Cipolla Invernale (Rossa/conservazione) | Verdura | 26 | 7 | 0 | 1 | 6 | 1 |
| Cipollotto | Verdura | 20 | 5 | 0 | 26 | 12 | 0 |
| Crescione | Verdura | 17 | 2 | 0 | 23 | 9 | 0 |
| Daikon | Verdura | 15 | 3 | 0 | 32 | 17 | 0 |
| Fagiolino (Tegolina / Cornetto) | Verdura | 27 | 6 | 0 | 0 | 5 | 1 |
| Fagiolo | Verdura | 25 | 6 | 1 | 4 | 5 | 0 |
| Fava | Verdura | 26 | 7 | 0 | 4 | 8 | 0 |
| Finocchio | Verdura | 25 | 5 | 0 | 6 | 9 | 0 |
| Gombo (Okra) | Verdura | 14 | 3 | 0 | 17 | 14 | 0 |
| Indivia Belga | Verdura | 19 | 3 | 0 | 29 | 8 | 0 |
| Indivia Riccia | Verdura | 18 | 3 | 0 | 30 | 9 | 0 |
| Lampascioni | Verdura | 6 | 2 | 0 | 68 | 10 | 0 |
| Lattuga da Cespo | Verdura | 28 | 7 | 0 | 0 | 6 | 0 |
| Lattuga da Taglio | Verdura | 28 | 6 | 0 | 2 | 6 | 0 |
| Lenticchia | Verdura | 19 | 4 | 0 | 9 | 28 | 0 |
| Mais Dolce | Verdura | 21 | 6 | 0 | 3 | 9 | 0 |
| Melanzana | Verdura | 29 | 8 | 0 | 0 | 2 | 0 |
| Navone (Rutabaga) | Verdura | 12 | 3 | 0 | 36 | 15 | 0 |
| Pastinaca | Verdura | 19 | 4 | 0 | 3 | 15 | 1 |
| Patata | Verdura | 29 | 5 | 0 | 0 | 4 | 0 |
| Patata Dolce (Batata) | Verdura | 17 | 4 | 0 | 24 | 11 | 0 |
| Peperone Dolce | Verdura | 29 | 7 | 0 | 2 | 3 | 0 |
| Pisello | Verdura | 26 | 5 | 0 | 2 | 8 | 0 |
| Pomodoro | Verdura | 27 | 7 | 0 | 4 | 3 | 0 |
| Porro | Verdura | 24 | 5 | 0 | 3 | 8 | 0 |
| Puntarelle | Verdura | 16 | 4 | 0 | 17 | 12 | 0 |
| Rabarbaro | Verdura | 14 | 1 | 0 | 26 | 9 | 0 |
| Radicchio (Rosso di Treviso / Chioggia) | Verdura | 23 | 5 | 0 | 6 | 6 | 0 |
| Rafano (Cren) | Verdura | 12 | 4 | 0 | 34 | 15 | 0 |
| Rapa | Verdura | 21 | 5 | 0 | 2 | 10 | 0 |
| Ravanello | Verdura | 27 | 4 | 0 | 1 | 9 | 0 |
| Rucola | Verdura | 21 | 5 | 0 | 6 | 11 | 0 |
| Salicornia | Verdura | 11 | 2 | 0 | 47 | 10 | 0 |
| Scalogno | Verdura | 21 | 5 | 0 | 3 | 13 | 0 |
| Scarola | Verdura | 19 | 3 | 0 | 29 | 9 | 0 |
| Scorzonera | Verdura | 13 | 5 | 0 | 23 | 11 | 0 |
| Sedano | Verdura | 28 | 7 | 0 | 0 | 7 | 0 |
| Sedano Rapa | Verdura | 21 | 5 | 0 | 30 | 9 | 0 |
| Spinacio | Verdura | 28 | 4 | 0 | 1 | 8 | 0 |
| Taccola (Pisello Mangiatutto) | Verdura | 16 | 3 | 0 | 35 | 10 | 0 |
| Topinambur (Carciofo di Gerusalemme) | Verdura | 17 | 4 | 2 | 5 | 17 | 0 |
| Valerianella (Songino) | Verdura | 17 | 3 | 0 | 5 | 8 | 0 |
| Zucca | Verdura | 28 | 6 | 1 | 1 | 5 | 0 |
| Zucchina | Verdura | 27 | 5 | 0 | 1 | 5 | 0 |
| Zucchina Spinosa (Chayote) | Verdura | 11 | 1 | 0 | 35 | 9 | 0 |

## 10. Riproducibilità e file

- `data/database.json` – il database; `data/schema.json` – lo schema; `data/database_guide.md` – la guida ai campi.
- `data/draft_legacy_values.json` – valori della bozza tolti dall'app; `data/_backup_bozza_2026-11-04/` – la bozza originale.
- `data/audit_findings.json`, `data/template_coverage.json` – esiti dei controlli.
- `data/raw/` – copie delle fonti scaricate; `scripts/config/` – configurazioni curate con citazioni; `scripts/texts/` – testi IT/EN.
- `scripts/` – la pipeline, ordine in `scripts/README.md`.
