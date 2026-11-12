# Products not included in the database

Generated on 2026-11-12 by `scripts/make_excluded_report.py`.

**Inclusion rule** for new products: at least 2 seasonality or storage sources and a CREA or BDA-IEO composition record. It ensures every record has sourced seasonality and nutrition values. White truffle was added as an exception (empty nutrition, seasonality set by law).

**How candidates were collected**: every entry of the calendars used (WWF, Greenpeace, Altroconsumo, Orto da Coltivare, Bio Suisse, EUFIC for 29 countries) that does not match a product in the database, plus Italian PDO/PGI fruit and vegetable products from the eAmbrosia register with no matching product, plus some typical Italian products missing from every calendar (e.g. agretti, lampascioni, cicerchia). The source columns are computed by searching the name in the raw data already downloaded; relevance and proposal are a declared judgement, to be confirmed.

**Limitation**: a product missing from all these lists (e.g. many local varieties) was not considered; for those, the MASAF PAT list, already linked to the products, is a starting point.

**Owner decision (5 November 2026)**: all candidates included except bergamot, caper, sorrel, strawberry tree and purslane, even with incomplete fields (Status column). For included products the columns show the sources available at the time of inclusion.

## Candidates

| Candidate | Status | Italian calendars | Other calendars | Storage | CREA | BDA-IEO | PDO/PGI | Why it is out | Relevance | Proposal |
|---|---|---|---|---|---|---|---|---|---|---|
| Chanterelle (Finferlo (gallinaccio)) | included on 2026-11-05 | – | EUFIC 3 countries | – | – | – | – | 1 seasonality/storage source; no CREA/BDA record | high – wild mushroom, widely picked and sold | add if an Italian seasonal source is found |
| Hazelnut (Nocciola) | included on 2026-11-05 | Orto da Coltivare (sito) | – | – | Nocciole, secche | NOCCIOLE, secche | Nocciola Romana; Nocciola di Giffoni; Nocciola del Piemonte / Nocciola Piemonte | 1 seasonality/storage source | high – three Italian PDO/PGI (Piemonte, Giffoni, Romana) | consider extending to nuts |
| Puntarelle (catalogna chicory shoots) (Puntarelle) | included on 2026-11-05 | Orto da Coltivare (sito) | EUFIC 1 countries | – | – | – | – | no CREA/BDA record | high – typical of Lazio, winter | as a variety of head chicory (catalogna) |
| Romanesco (Broccolo romanesco) | included on 2026-11-05 | WWF | EUFIC 1 countries | – | – | – | – | no CREA/BDA record | high – typically Italian winter vegetable | add (exception, nutrition from cauliflower or broccoli as an approximation) or as a variety |
| Saltwort (agretti) (Agretti (barba di frate)) | included on 2026-11-05 | Orto da Coltivare (sito) | – | – | Agretti, cotti, bolliti; Agretti, crudi | AGRETTI | – | 1 seasonality/storage source | high – typically Italian spring vegetable | add if a second seasonal source is found |
| Spring onion (Cipollotto) | included on 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 18 countries | – | – | – | Cipollotto Nocerino | no CREA/BDA record | high – very common in Italy, Cipollotto Nocerino PGI | add (exception: nutrition from CREA 'cipolline' as a declared approximation) |
| Walnut (Noce) | included on 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse | – | Noci; Noci pecan | NOCI PECAN; NOCI, fresche | – | requirements met: was not in the initial candidate list | high – autumn nut, widely eaten | consider extending to nuts |
| Almond (Mandorla) | included on 2026-11-05 | Orto da Coltivare (sito) | – | – | Mandorle dolci, secche | MANDORLE DOLCI, fresche; MANDORLE DOLCI, secche | – | 1 seasonality/storage source | medium – nut; fresh almonds have a short summer season | consider extending to nuts |
| Bergamot orange (Bergamotto) | excluded by owner decision (2026-11-05) | Orto da Coltivare (sito) | – | – | – | – | – | 1 seasonality/storage source; no CREA/BDA record | medium – citrus typical of Calabria, used mainly for flavouring | to evaluate |
| Caper (Cappero) | excluded by owner decision (2026-11-05) | Orto da Coltivare (sito) | – | – | – | CAPPERI SOTT’ACETO | Cappero delle Isole Eolie; Cappero di Pantelleria | 1 seasonality/storage source | medium – PDO/PGI of Pantelleria and the Aeolian Islands; eaten preserved | no (preserved product) |
| Chinese cabbage / pak choi (Cavolo cinese / pak choi) | included on 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 16 countries | UC Davis, USDA HB66 | – | – | – | no CREA/BDA record | medium – increasingly common in supermarkets and gardens | to evaluate |
| Chives (Erba cipollina) | included on 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse | USDA HB66 | – | ERBA CIPOLLINA, fresca | – | requirements met: was not in the initial candidate list | medium – common garden herb | add if a second seasonal source is found |
| Citron (Cedro) | included on 2026-11-05 | Orto da Coltivare (sito) | – | – | – | CEDRO, CANDITO | Cedro di Santa Maria del Cedro | 1 seasonality/storage source | medium – Cedro di Santa Maria del Cedro PDO | to evaluate |
| Grass pea (Cicerchia) | included on 2026-11-05 | – | – | – | – | – | – | 0 seasonality/storage source; no CREA/BDA record | medium – traditional legume of Central Italy | to evaluate |
| Horseradish (Rafano (cren)) | included on 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 5 countries | USDA HB66 | – | – | – | no CREA/BDA record | medium – traditional in Basilicata (rafanata) and North-East Italy | to evaluate |
| Jujube (Giuggiola) | included on 2026-11-05 | Orto da Coltivare (sito) | EUFIC 2 countries | UC Davis | – | – | – | no CREA/BDA record | medium – traditional autumn fruit (Veneto, South) | to evaluate |
| King oyster mushroom (Cardoncello) | included on 2026-11-05 | – | – | – | – | – | – | 0 seasonality/storage source; no CREA/BDA record | medium – cultivated and wild mushroom typical of Apulia and Basilicata | to evaluate |
| Mulberry (Gelso (mora di gelso)) | included on 2026-11-05 | Orto da Coltivare (sito) | EUFIC 4 countries | – | – | – | – | no CREA/BDA record | medium – traditional fruit of Southern Italy, rarely sold | to evaluate |
| Olive (Oliva) | included on 2026-11-05 | Orto da Coltivare (sito) | EUFIC 1 countries | UC Davis, USDA HB66 | Oliva Giarraffa; Oliva Nocellara del Belice | OLIVE, DA TAVOLA, conservate; OLIVE, NERE | Olive taggiasche liguri; Oliva di Gaeta; Oliva Ascolana del Piceno | requirements met: was not in the initial candidate list | medium – many PDOs; not eaten fresh | no (processed only) |
| Pistachio (Pistacchio) | included on 2026-11-05 | Orto da Coltivare (sito) | – | UC Davis | Pistacchi; Pistacchio di Bronte DOP | PISTACCHI, freschi; PISTACCHI, secchi | Pistacchio di Raffadali; Pistacchio Verde di Bronte | requirements met: was not in the initial candidate list | medium – Pistacchio Verde di Bronte PDO | consider extending to nuts |
| Snow pea / mangetout (Taccola (pisello mangiatutto)) | included on 2026-11-05 | – | Bio Suisse; EUFIC 6 countries | UC Davis | – | – | – | no CREA/BDA record | medium – common in gardens; could be a form of pea | as a variety of pea |
| Sour cherry (Amarena / visciola) | included on 2026-11-05 | – | – | – | Amarene, fresche | AMARENE | Amarene Brusche di Modena | 0 seasonality/storage source | medium – Amarene Brusche di Modena PGI; rarely eaten fresh | to evaluate |
| Sweet potato (Patata dolce (batata)) | included on 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 3 countries | UC Davis | – | – | – | no CREA/BDA record | medium – also grown in Italy (Veneto, Apulia), growing consumption | to evaluate |
| Tassel hyacinth bulbs (Lampascioni) | included on 2026-11-05 | – | – | – | – | – | – | 0 seasonality/storage source; no CREA/BDA record | medium – traditional in Apulia and Basilicata | to evaluate |
| Wild asparagus (Asparago selvatico) | included on 2026-11-05 | Orto da Coltivare (sito) | – | – | Asparagi di bosco, crudi; Asparagi di campo, cotti, bolliti | – | – | 1 seasonality/storage source | medium – wild spring harvest, CREA has an entry | as a variety or note of asparagus |
| Blackcurrant (Ribes nero) | included on 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 14 countries | – | – | RIBES NERO | – | requirements met: was not in the initial candidate list | low – mainly a Northern European crop | no |
| Cape gooseberry (physalis) (Alchechengi) | included on 2026-11-05 | WWF, Altroconsumo, Orto da Coltivare (sito) | – | – | – | – | – | no CREA/BDA record | low – ornamental fruit, occasionally eaten | no |
| Carob (Carruba) | included on 2026-11-05 | – | EUFIC 3 countries | – | Carrube | CARRUBE | – | 1 seasonality/storage source | low – eaten mainly as flour | no |
| Chayote (Zucchina spinosa (chayote)) | included on 2026-11-05 | Orto da Coltivare (sito) | EUFIC 3 countries | – | – | – | – | no CREA/BDA record | low – niche | no |
| Chinotto (myrtle-leaved orange) (Chinotto) | included on 2026-11-05 | – | – | – | – | – | – | 0 seasonality/storage source; no CREA/BDA record | low – used processed | no |
| Coconut (Cocco) | included on 2026-11-05 | Altroconsumo, Orto da Coltivare (sito) | – | USDA HB66 | Cocco, essiccato; Cocco, fresco | – | – | requirements met: was not in the initial candidate list | low – exotic, no season in Italy | no |
| Cranberry / lingonberry (Mirtillo rosso) | included on 2026-11-05 | – | Bio Suisse; EUFIC 7 countries | USDA HB66 | – | – | – | no CREA/BDA record | low – in Italy almost only dried or as juice | no |
| Daikon / white radish (Daikon) | included on 2026-11-05 | – | EUFIC 3 countries | – | – | DAIKON | – | 1 seasonality/storage source | low – niche | no |
| Elderberry (Sambuco) | included on 2026-11-05 | – | Bio Suisse; EUFIC 5 countries | – | – | – | – | no CREA/BDA record | low – used mainly for flowers and syrups | no |
| Gooseberry (Uva spina) | included on 2026-11-05 | – | Bio Suisse; EUFIC 15 countries | USDA HB66 | – | – | – | no CREA/BDA record | low – mainly a Northern European crop | no |
| Medlar (Nespola comune (germanica)) | included on 2026-11-05 | – | EUFIC 5 countries | – | – | – | – | 1 seasonality/storage source; no CREA/BDA record | low – heritage fruit, rarely sold | no |
| Mirabelle plum (Mirabella / susina gialla) | included on 2026-11-05 | – | Bio Suisse; EUFIC 5 countries | – | – | – | – | no CREA/BDA record | low – falls under plums | as a variety of plum |
| Morel (Spugnola) | included on 2026-11-05 | – | EUFIC 2 countries | – | – | – | – | 1 seasonality/storage source; no CREA/BDA record | low – niche wild spring mushroom | no |
| Okra (Gombo (okra)) | included on 2026-11-05 | Orto da Coltivare (sito) | EUFIC 4 countries | UC Davis, USDA HB66 | – | – | – | no CREA/BDA record | low – niche | no |
| Purslane (Portulaca) | excluded by owner decision (2026-11-05) | Orto da Coltivare (sito) | Bio Suisse; EUFIC 3 countries | – | – | – | – | no CREA/BDA record | low – wild herb | no |
| Rhubarb (Rabarbaro) | included on 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 15 countries | USDA HB66 | – | – | – | no CREA/BDA record | low – rarely used in Italian cooking | no |
| Saffron (Zafferano) | included on 2026-11-05 | Orto da Coltivare (sito) | – | – | – | ZAFFERANO | Zafferano di Sardegna; Zafferano di San Gimignano; Zafferano dell'Aquila | 1 seasonality/storage source | low – spice; three Italian PDOs | no (dried spice) |
| Salsify / black salsify (Scorzonera / scorzobianca) | included on 2026-11-05 | Orto da Coltivare (sito) | Bio Suisse; EUFIC 9 countries | USDA HB66 | – | SCORZONERA | – | requirements met: was not in the initial candidate list | low – niche vegetable | no |
| Samphire (Salicornia) | included on 2026-11-05 | Orto da Coltivare (sito) | EUFIC 3 countries | – | – | – | – | no CREA/BDA record | low – niche | no |
| Shiitake (Shiitake) | included on 2026-11-05 | – | EUFIC 3 countries | – | – | – | – | 1 seasonality/storage source; no CREA/BDA record | low – cultivated, no seasonality | no |
| Sorrel (Acetosa) | excluded by owner decision (2026-11-05) | Orto da Coltivare (sito) | EUFIC 3 countries | – | – | – | – | no CREA/BDA record | low – wild herb | no |
| Strawberry tree fruit (Corbezzolo) | excluded by owner decision (2026-11-05) | Orto da Coltivare (sito) | – | – | – | – | – | 1 seasonality/storage source; no CREA/BDA record | low – wild fruit | no |
| Swede / rutabaga (Rapa / navone (rutabaga)) | included on 2026-11-05 | – | EUFIC 11 countries | USDA HB66 | – | – | – | no CREA/BDA record | low – niche in Italy | no |
| Watercress (Crescione) | included on 2026-11-05 | Orto da Coltivare (sito) | EUFIC 6 countries | USDA HB66 | – | CRESCIONE | – | requirements met: was not in the initial candidate list | low – uncommon in Italy | no |

## To evaluate first

Candidates with high relevance or that already meet the rule: Spring onion, Saltwort (agretti), Walnut, Hazelnut, Pistachio, Chives, Watercress, Blackcurrant, Salsify / black salsify, Romanesco, Puntarelle (catalogna chicory shoots), Coconut, Chanterelle, Olive.

Notes:

- **Nuts** (walnut, hazelnut, almond, pistachio): they have CREA/BDA records and PDO/PGI, but the seasonal calendars do not list them. Including them is a scope choice for the app (today: fresh fruit and vegetables).
- **Varieties or forms of products already present** (puntarelle, snow peas, mirabelles, wild asparagus): better added as varieties, as for the flat peach, without creating new records.
- **Romanesco broccoli**: no specific CREA/BDA record; cauliflower or broccoli could be used as a declared approximation.
- **Wild mushrooms** (chanterelle, morel, cardoncello): regional mushroom laws rarely give periods per species; institutional mycological sheets would be needed, as for Caesar's mushroom.
