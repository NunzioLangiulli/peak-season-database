# Alimenti non inclusi nel database

Generato il 2026-11-12 da `scripts/make_excluded_report.py`.

**Regola di ammissione** usata per i nuovi alimenti: almeno 2 fonti stagionali o di conservazione e una scheda di composizione CREA o BDA-IEO. Serve a garantire che ogni scheda abbia stagionalità e valori nutrizionali da fonte. Il tartufo bianco è stato aggiunto in deroga (nutrizione vuota, stagionalità per legge).

**Come sono stati raccolti i candidati**: tutte le voci dei calendari usati (WWF, Greenpeace, Altroconsumo, Orto da Coltivare, Bio Suisse, EUFIC per 29 Paesi) che non corrispondono a un alimento del database, più i prodotti ortofrutticoli italiani DOP/IGP del registro eAmbrosia senza alimento corrispondente, più alcuni prodotti tipici italiani assenti da tutti i calendari (es. agretti, lampascioni, cicerchia). Le colonne sulle fonti sono calcolate cercando il nome nei dati grezzi già scaricati; rilevanza e proposta sono un mio giudizio, da confermare.

**Limite**: un prodotto che non compare in nessuna di queste liste (es. molte varietà locali) non è stato considerato; per quelli si può partire dall'elenco PAT del MASAF, già collegato agli alimenti.

**Decisione dell'utente (5 novembre 2026)**: inclusi tutti i candidati tranne bergamotto, cappero, acetosa, corbezzolo e portulaca, anche con campi incompleti (colonna Stato). Per quelli inclusi le colonne mostrano le fonti disponibili al momento dell'inclusione.

## Candidati

| Candidato | Stato | Calendari italiani | Altri calendari | Conservazione | CREA | BDA-IEO | DOP/IGP | Perché è fuori | Rilevanza | Proposta |
|---|---|---|---|---|---|---|---|---|---|---|
| Agretti (barba di frate) | incluso il 2026-11-05 | Orto da Coltivare (sito) | – | – | Agretti, cotti, bolliti; Agretti, crudi | AGRETTI | – | 1 fonte stagionale/conservazione | alta – ortaggio primaverile tipicamente italiano | aggiungere se si trova una seconda fonte stagionale |
| Broccolo romanesco | incluso il 2026-11-05 | WWF | EUFIC 1 Paesi | – | – | – | – | nessuna scheda CREA/BDA | alta – ortaggio invernale tipicamente italiano | aggiungere (deroga, nutrizione da cavolfiore o broccolo come approssimata) o come varietà |
| Cipollotto | incluso il 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 18 Paesi | – | – | – | Cipollotto Nocerino | nessuna scheda CREA/BDA | alta – molto comune in Italia, IGP Cipollotto Nocerino | aggiungere (deroga: nutrizione dalle 'cipolline' CREA come approssimazione dichiarata) |
| Finferlo (gallinaccio) | incluso il 2026-11-05 | – | EUFIC 3 Paesi | – | – | – | – | 1 fonte stagionale/conservazione; nessuna scheda CREA/BDA | alta – fungo spontaneo molto raccolto e venduto | aggiungere se si trova una fonte stagionale italiana |
| Nocciola | incluso il 2026-11-05 | Orto da Coltivare (sito) | – | – | Nocciole, secche | NOCCIOLE, secche | Nocciola Romana; Nocciola di Giffoni; Nocciola del Piemonte / Nocciola Piemonte | 1 fonte stagionale/conservazione | alta – tre DOP/IGP italiane (Piemonte, Giffoni, Romana) | valutare l'estensione alla frutta secca |
| Noce | incluso il 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse | – | Noci; Noci pecan | NOCI PECAN; NOCI, fresche | – | requisiti soddisfatti: non era nella lista iniziale dei candidati | alta – frutta secca di stagione autunnale, molto consumata | valutare l'estensione alla frutta secca |
| Puntarelle | incluso il 2026-11-05 | Orto da Coltivare (sito) | EUFIC 1 Paesi | – | – | – | – | nessuna scheda CREA/BDA | alta – tipiche del Lazio, inverno | come varietà della cicoria da cespo (catalogna) |
| Amarena / visciola | incluso il 2026-11-05 | – | – | – | Amarene, fresche | AMARENE | Amarene Brusche di Modena | 0 fonte stagionale/conservazione | media – IGP Amarene Brusche di Modena; frutto da consumo fresco poco diffuso | valutare |
| Asparago selvatico | incluso il 2026-11-05 | Orto da Coltivare (sito) | – | – | Asparagi di bosco, crudi; Asparagi di campo, cotti, bolliti | – | – | 1 fonte stagionale/conservazione | media – raccolta spontanea primaverile, CREA ha la voce | come varietà o nota dell'asparago |
| Bergamotto | escluso su decisione dell'utente (2026-11-05) | Orto da Coltivare (sito) | – | – | – | – | – | 1 fonte stagionale/conservazione; nessuna scheda CREA/BDA | media – agrume tipico della Calabria, uso soprattutto aromatico | valutare |
| Cappero | escluso su decisione dell'utente (2026-11-05) | Orto da Coltivare (sito) | – | – | – | CAPPERI SOTT’ACETO | Cappero delle Isole Eolie; Cappero di Pantelleria | 1 fonte stagionale/conservazione | media – DOP/IGP di Pantelleria e delle Eolie; consumo conservato | no (prodotto conservato) |
| Cardoncello | incluso il 2026-11-05 | – | – | – | – | – | – | 0 fonte stagionale/conservazione; nessuna scheda CREA/BDA | media – fungo coltivato e spontaneo tipico della Puglia e Basilicata | valutare |
| Cavolo cinese / pak choi | incluso il 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 16 Paesi | UC Davis, USDA HB66 | – | – | – | nessuna scheda CREA/BDA | media – sempre più presente nei supermercati e negli orti | valutare |
| Cedro | incluso il 2026-11-05 | Orto da Coltivare (sito) | – | – | – | CEDRO, CANDITO | Cedro di Santa Maria del Cedro | 1 fonte stagionale/conservazione | media – DOP Cedro di Santa Maria del Cedro | valutare |
| Cicerchia | incluso il 2026-11-05 | – | – | – | – | – | – | 0 fonte stagionale/conservazione; nessuna scheda CREA/BDA | media – legume tradizionale del Centro Italia | valutare |
| Erba cipollina | incluso il 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse | USDA HB66 | – | ERBA CIPOLLINA, fresca | – | requisiti soddisfatti: non era nella lista iniziale dei candidati | media – erba aromatica comune nell'orto | aggiungere se si trova una seconda fonte stagionale |
| Gelso (mora di gelso) | incluso il 2026-11-05 | Orto da Coltivare (sito) | EUFIC 4 Paesi | – | – | – | – | nessuna scheda CREA/BDA | media – frutto tradizionale del Sud, poco commercializzato | valutare |
| Giuggiola | incluso il 2026-11-05 | Orto da Coltivare (sito) | EUFIC 2 Paesi | UC Davis | – | – | – | nessuna scheda CREA/BDA | media – frutto tradizionale autunnale (Veneto, Sud) | valutare |
| Lampascioni | incluso il 2026-11-05 | – | – | – | – | – | – | 0 fonte stagionale/conservazione; nessuna scheda CREA/BDA | media – tradizionali in Puglia e Basilicata | valutare |
| Mandorla | incluso il 2026-11-05 | Orto da Coltivare (sito) | – | – | Mandorle dolci, secche | MANDORLE DOLCI, fresche; MANDORLE DOLCI, secche | – | 1 fonte stagionale/conservazione | media – frutta secca; la mandorla fresca ha una breve stagione estiva | valutare l'estensione alla frutta secca |
| Oliva | incluso il 2026-11-05 | Orto da Coltivare (sito) | EUFIC 1 Paesi | UC Davis, USDA HB66 | Oliva Giarraffa; Oliva Nocellara del Belice | OLIVE, DA TAVOLA, conservate; OLIVE, NERE | Olive taggiasche liguri; Oliva di Gaeta; Oliva Ascolana del Piceno | requisiti soddisfatti: non era nella lista iniziale dei candidati | media – molte DOP; non si consuma fresca | no (solo trasformata) |
| Patata dolce (batata) | incluso il 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 3 Paesi | UC Davis | – | – | – | nessuna scheda CREA/BDA | media – coltivata anche in Italia (Veneto, Puglia), consumo in crescita | valutare |
| Pistacchio | incluso il 2026-11-05 | Orto da Coltivare (sito) | – | UC Davis | Pistacchi; Pistacchio di Bronte DOP | PISTACCHI, freschi; PISTACCHI, secchi | Pistacchio di Raffadali; Pistacchio Verde di Bronte | requisiti soddisfatti: non era nella lista iniziale dei candidati | media – DOP Pistacchio Verde di Bronte | valutare l'estensione alla frutta secca |
| Rafano (cren) | incluso il 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 5 Paesi | USDA HB66 | – | – | – | nessuna scheda CREA/BDA | media – tradizionale in Basilicata (rafanata) e nel Nord-Est | valutare |
| Taccola (pisello mangiatutto) | incluso il 2026-11-05 | – | Bio Suisse; EUFIC 6 Paesi | UC Davis | – | – | – | nessuna scheda CREA/BDA | media – comune negli orti; potrebbe stare come forma del pisello | come varietà del pisello |
| Acetosa | escluso su decisione dell'utente (2026-11-05) | Orto da Coltivare (sito) | EUFIC 3 Paesi | – | – | – | – | nessuna scheda CREA/BDA | bassa – erba spontanea | no |
| Alchechengi | incluso il 2026-11-05 | WWF, Altroconsumo, Orto da Coltivare (sito) | – | – | – | – | – | nessuna scheda CREA/BDA | bassa – frutto decorativo, consumo occasionale | no |
| Carruba | incluso il 2026-11-05 | – | EUFIC 3 Paesi | – | Carrube | CARRUBE | – | 1 fonte stagionale/conservazione | bassa – consumo soprattutto come farina | no |
| Chinotto | incluso il 2026-11-05 | – | – | – | – | – | – | 0 fonte stagionale/conservazione; nessuna scheda CREA/BDA | bassa – uso trasformato | no |
| Cocco | incluso il 2026-11-05 | Altroconsumo, Orto da Coltivare (sito) | – | USDA HB66 | Cocco, essiccato; Cocco, fresco | – | – | requisiti soddisfatti: non era nella lista iniziale dei candidati | bassa – esotico, senza stagione in Italia | no |
| Corbezzolo | escluso su decisione dell'utente (2026-11-05) | Orto da Coltivare (sito) | – | – | – | – | – | 1 fonte stagionale/conservazione; nessuna scheda CREA/BDA | bassa – frutto spontaneo | no |
| Crescione | incluso il 2026-11-05 | Orto da Coltivare (sito) | EUFIC 6 Paesi | USDA HB66 | – | CRESCIONE | – | requisiti soddisfatti: non era nella lista iniziale dei candidati | bassa – poco diffuso in Italia | no |
| Daikon | incluso il 2026-11-05 | – | EUFIC 3 Paesi | – | – | DAIKON | – | 1 fonte stagionale/conservazione | bassa – di nicchia | no |
| Gombo (okra) | incluso il 2026-11-05 | Orto da Coltivare (sito) | EUFIC 4 Paesi | UC Davis, USDA HB66 | – | – | – | nessuna scheda CREA/BDA | bassa – di nicchia | no |
| Mirabella / susina gialla | incluso il 2026-11-05 | – | Bio Suisse; EUFIC 5 Paesi | – | – | – | – | nessuna scheda CREA/BDA | bassa – rientra nelle susine | come varietà della susina |
| Mirtillo rosso | incluso il 2026-11-05 | – | Bio Suisse; EUFIC 7 Paesi | USDA HB66 | – | – | – | nessuna scheda CREA/BDA | bassa – in Italia quasi solo essiccato o in succo | no |
| Nespola comune (germanica) | incluso il 2026-11-05 | – | EUFIC 5 Paesi | – | – | – | – | 1 fonte stagionale/conservazione; nessuna scheda CREA/BDA | bassa – frutto antico, raro in commercio | no |
| Portulaca | escluso su decisione dell'utente (2026-11-05) | Orto da Coltivare (sito) | Bio Suisse; EUFIC 3 Paesi | – | – | – | – | nessuna scheda CREA/BDA | bassa – erba spontanea | no |
| Rabarbaro | incluso il 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 15 Paesi | USDA HB66 | – | – | – | nessuna scheda CREA/BDA | bassa – poco usato in cucina italiana | no |
| Rapa / navone (rutabaga) | incluso il 2026-11-05 | – | EUFIC 11 Paesi | USDA HB66 | – | – | – | nessuna scheda CREA/BDA | bassa – di nicchia in Italia | no |
| Ribes nero | incluso il 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 14 Paesi | – | – | RIBES NERO | – | requisiti soddisfatti: non era nella lista iniziale dei candidati | bassa – coltura soprattutto nordeuropea | no |
| Salicornia | incluso il 2026-11-05 | Orto da Coltivare (sito) | EUFIC 3 Paesi | – | – | – | – | nessuna scheda CREA/BDA | bassa – di nicchia | no |
| Sambuco | incluso il 2026-11-05 | – | Bio Suisse; EUFIC 5 Paesi | – | – | – | – | nessuna scheda CREA/BDA | bassa – uso soprattutto per fiori e sciroppi | no |
| Scorzonera / scorzobianca | incluso il 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 9 Paesi | USDA HB66 | – | SCORZONERA | – | requisiti soddisfatti: non era nella lista iniziale dei candidati | bassa – ortaggio di nicchia | no |
| Shiitake | incluso il 2026-11-05 | – | EUFIC 3 Paesi | – | – | – | – | 1 fonte stagionale/conservazione; nessuna scheda CREA/BDA | bassa – coltivato, senza stagionalità | no |
| Spugnola | incluso il 2026-11-05 | – | EUFIC 2 Paesi | – | – | – | – | 1 fonte stagionale/conservazione; nessuna scheda CREA/BDA | bassa – fungo spontaneo primaverile di nicchia | no |
| Uva spina | incluso il 2026-11-05 | – | Bio Suisse; EUFIC 15 Paesi | USDA HB66 | – | – | – | nessuna scheda CREA/BDA | bassa – coltura soprattutto nordeuropea | no |
| Zafferano | incluso il 2026-11-05 | Orto da Coltivare (sito) | – | – | – | ZAFFERANO | Zafferano di Sardegna; Zafferano di San Gimignano; Zafferano dell'Aquila | 1 fonte stagionale/conservazione | bassa – spezia; tre DOP italiane | no (spezia secca) |
| Zucchina spinosa (chayote) | incluso il 2026-11-05 | Orto da Coltivare (sito) | EUFIC 3 Paesi | – | – | – | – | nessuna scheda CREA/BDA | bassa – di nicchia | no |

## Da valutare per primi

Candidati con rilevanza alta o che soddisfano già la regola: Cipollotto, Agretti (barba di frate), Noce, Nocciola, Pistacchio, Erba cipollina, Crescione, Ribes nero, Scorzonera / scorzobianca, Broccolo romanesco, Puntarelle, Cocco, Finferlo (gallinaccio), Oliva.

Note:

- **Frutta secca** (noce, nocciola, mandorla, pistacchio): hanno schede CREA/BDA e DOP/IGP, ma i calendari stagionali non li riportano. Includerli è una scelta di perimetro dell'app (oggi: frutta e verdura fresca).
- **Varietà o forme di alimenti già presenti** (puntarelle, taccole, mirabelle, asparago selvatico): conviene aggiungerle come varietà, come per la pesca tabacchiera, senza creare nuove schede.
- **Broccolo romanesco**: nessuna scheda CREA/BDA specifica; si potrebbe usare cavolfiore o broccolo come approssimazione dichiarata.
- **Funghi spontanei** (finferlo, spugnola, cardoncello): le leggi regionali sui funghi raramente danno periodi per specie; servirebbero schede micologiche istituzionali come per l'ovolo.
