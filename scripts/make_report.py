"""Genera data/scraping_report.md: come il database è stato costruito, organizzato e validato.
I numeri sono calcolati dal database, dall'audit e dalla copertura del template; i commenti sono testo fisso aggiornato a mano.
Uso:  python scripts/make_report.py   (dopo validate_db.py, audit_db.py e template_coverage.py)
"""
import collections
import json
import re
from datetime import date

from common import DATA, load_json

CAT_IT = {"verdura": "Verdura", "frutta": "Frutta", "erbe_spezie": "Erbe e spezie", "funghi": "Funghi", "cereali": "Cereali"}
BLOCKS = [
    ("id, names, category", "identità: id stabile, nomi IT/EN (comune, alternativi), categoria"),
    ("botany", "nome scientifico, famiglia, genere, codici EPPO/GBIF/UPOV, parte della pianta usata"),
    ("italian_varieties_and_territories", "varietà verificate (Catalogo comune UE, Slow Food, testi), DOP/IGP (eAmbrosia), PAT (MASAF), varietà iscritte in Italia"),
    ("images", "galleria con autore, licenza e URL d'origine di ogni foto"),
    ("seasonality", "stato mese per mese per 3 macro-aree italiane e 6 zone climatiche europee, con provenienza zona per zona"),
    ("agricultural_calendar_italy", "semina, trapianto, raccolta per macro-area; parametri di coltivazione"),
    ("buying_guide", "come sceglierlo, segni di qualità e di deterioramento"),
    ("ripening_and_storage", "climaterico/non climaterico, etilene, respirazione e deperibilità, danno da freddo, conservazione professionale e domestica, compatibilità"),
    ("nutrition_and_sustainability", "valori per 100 g con fonte per valore, %VNR, claim UE, composti bioattivi, allergeni, porzioni LARN, impronta di carbonio e idrica"),
    ("sources_by_topic", "fonti usate per argomento e link utili"),
    ("data_completeness", "campi mancanti, da verificare, non pertinenti, discrepanze con la bozza, note"),
    ("help_refs", "voci del glossario pertinenti a quell'alimento (icone \"?\")"),
]


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rows]
    return "\n".join(out)


def count_bilingual(o):
    if isinstance(o, dict):
        n = 1 if set(o) == {"it", "en"} else 0
        return n + sum(count_bilingual(v) for v in o.values())
    if isinstance(o, list):
        return sum(count_bilingual(v) for v in o)
    return 0


def main():
    db = load_json(DATA / "database.json")
    md = db["metadata"]
    items = db["items"]
    N = len(items)
    legacy = load_json(DATA / "draft_legacy_values.json")
    audit = load_json(DATA / "audit_findings.json")
    cov = load_json(DATA / "template_coverage.json")
    L = []
    w = L.append
    dcs = [i["data_completeness"] for i in items]
    miss = sum(len(d["missing_fields"]) for d in dcs)
    pend = sum(len(d["fields_pending_verification"]) for d in dcs)
    disc = sum(len(d["discrepancies"]) for d in dcs)
    na = sum(len(d.get("not_applicable_fields", [])) for d in dcs)
    img_err = sum(1 for a in audit if a["area"] == "immagini")
    sev = collections.Counter(a["severity"] for a in audit if a["area"] != "immagini")

    # ------------------------------------------------------------------ intestazione
    w("# Peak Season – Report Fase 1: costruzione, organizzazione e validazione del database\n")
    w(f"Generato il {date.today().isoformat()} da `scripts/make_report.py` · database v{md['version']} · {N} alimenti · "
      f"schema `data/schema.json` (JSON Schema 2020-12).\n")
    w("Il report spiega con quale metodo è stato costruito il database, come è organizzato (schede, metadati, fonti, glossario, "
      "bilinguismo) e come è stato controllato. Le immagini hanno un report a parte, dopo la tua revisione. "
      "La guida campo per campo è in `data/database_guide.md`.\n")

    w("## 1. In sintesi\n")
    w(table([
        ["Alimenti", N, ", ".join(f"{CAT_IT[c]} {n}" for c, n in collections.Counter(i["category"] for i in items).most_common())],
        ["Fonti catalogate", len(md["official_sources"]), "ognuna con descrizione, autorevolezza, contenuti e usi (§4)"],
        ["Fonti usate per alimento", f"media {sum(len(i['sources_by_topic']['sources_used']) for i in items) / N:.1f}", "`sources_by_topic.sources_used`"],
        ["Casi di conflitto tra fonti documentati", len(md["source_conflicts"]), "con decisione e motivazione (§5)"],
        ["Voci di glossario (icone \"?\")", len(md["glossary"]), f"{len(md['field_help'])} campi collegati, {sum(len(i.get('help_refs', [])) for i in items)} rimandi negli alimenti"],
        ["Testi bilingui {it, en}", count_bilingual(db), "tutto ciò che l'utente legge esiste in italiano e in inglese (§3.4)"],
        ["Validazione schema", "0 errori sui dati", f"restano solo i file immagine eliminati durante la tua revisione ({img_err} segnalazioni)"],
        ["Ricontrollo sistematico (dati)", f"{sev['E']} errori, {sev['W']} da controllare, {sev['I']} informativi", "tutti spiegati (§6.3)"],
        ["Valori ancora da verificare", pend, "quasi tutti calendari agricoli di frutta, erbe e cereali (§7)"],
        ["Campi senza dato", miss, "lacune vere, mappate in §7"],
        ["Campi non pertinenti, motivati", na, "es. danno da freddo per chi non è sensibile"],
    ], ["Voce", "Valore", "Note"]))
    w("")

    # ------------------------------------------------------------------ 2. costruzione
    w("## 2. Come è stato costruito\n")
    w("### 2.1 Principi\n")
    for t in [
        "**Nessun dato inventato.** Ogni valore viene da una fonte catalogata, indicata nel campo `source` o nel blocco `sources_by_topic`; dove una fonte manca il campo resta vuoto (null) ed è elencato in `data_completeness.missing_fields`.",
        "**Fonti ufficiali e scientifiche prima di tutto**, con un ordine di priorità dichiarato per argomento (es. nutrizione: CREA → BDA-IEO → USDA FoodData Central).",
        "**Tracciabilità per valore**: per i nutrienti la fonte è indicata valore per valore; per i dati post-raccolta il capitolo o la tabella HB66; per le impronte il numero di studi e l'intervallo.",
        "**Approssimazioni dichiarate**: se una fonte non ha la voce esatta si usa la più vicina, marcata come approssimata; le stime (es. classe di respirazione da Q10) sono marcate come stimate e spiegate nel campo `basis`.",
        "**Non pertinente ≠ mancante**: un campo che per definizione non si applica (es. danno da freddo per chi non lo soffre) è marcato N/A con motivazione, non conteggiato come lacuna.",
        "**La bozza iniziale come punto di partenza, non come fonte**: i suoi 91 alimenti sono stati migrati nella struttura; ogni valore diverso dalle fonti è registrato come discrepanza, ogni valore non verificabile è tolto dall'app e conservato in `data/draft_legacy_values.json` "
        f"({sum(len(v) for v in legacy['items'].values())} valori). Copia della bozza in `data/_backup_bozza_2026-11-04/`.",
    ]:
        w(f"- {t}")
    w("\n### 2.2 Pipeline\n")
    w("Il database è prodotto da script Python eseguiti in un ordine fisso (`scripts/README.md`). Ogni script ha una docstring con fonte, metodo e uso.\n")
    w(table([
        ["1. Fonti e indice", "scarica e mette in cache le fonti (`data/raw/`), costruisce la lista master con i codici di ogni fonte, migra la bozza"],
        ["2. Nutrizione", "CREA e BDA-IEO, USDA per i mancanti, %VNR e claim UE ricalcolati, riferimento LARN per le proteine"],
        ["3. Stagionalità e botanica", "voto tra i calendari italiani, mappa EUFIC e fonti nazionali EUFIC; EPPO, WFO, GBIF; note di coltivazione"],
        ["4. Varietà e territori", "verifica delle varietà su testi, Slow Food e Catalogo comune UE; DOP/IGP su eAmbrosia; codici UPOV; PAT MASAF"],
        ["5. Conservazione", "USDA HB66 (tabelle e capitoli), classi di Kader, FoodKeeper e guida UC Davis per la casa, gruppi di compatibilità"],
        ["6. Composti, allergeni, sostenibilità", "USDA carotenoidi e flavonoidi, Phenol-Explorer, Reg. UE 1169/2011, porzioni LARN, SU-EATABLE LIFE, AGRIBALYSE"],
        ["7. Testi, immagini, fonti", "testi IT/EN riallineati ai dati, immagini con licenza, registro delle fonti per alimento"],
        ["8. Bilinguismo e aiuto", "`localize_fields.py` (ultimo passo di trasformazione), `build_help.py` (vocabolario, glossario), `build_source_catalog.py` (catalogo fonti e conflitti)"],
        ["9. Controlli e report", "validazione JSON Schema, ricontrollo voce per voce, copertura del template, report"],
    ], ["Fase", "Cosa fa"]))
    w("\nLe scelte che richiedono giudizio (citazioni dai capitoli HB66, mappature tra voci di fonti diverse, descrizioni delle fonti, "
      "glossario, conflitti) sono in file di configurazione curati a mano in `scripts/config/`, ciascuno con la citazione o la pagina della fonte: "
      "così ogni decisione è leggibile e modificabile senza toccare il codice.\n")

    # ------------------------------------------------------------------ 3. organizzazione
    w("## 3. Come è organizzato\n")
    w("Il file `data/database.json` ha due parti: `metadata` (tutto ciò che vale per l'intero database) e `items` (una scheda per alimento).\n")
    w("### 3.1 La scheda di un alimento\n")
    w(table([[f"`{a}`", b] for a, b in BLOCKS], ["Blocco", "Contenuto"]))
    w("\n### 3.2 I metadati\n")
    w(table([
        ["`official_sources`", "catalogo delle fonti: cos'è, perché è autorevole, cosa offre, per quali argomenti e alimenti è stata consultata"],
        ["`source_conflicts`", "casi generali di valori discordanti tra fonti: perché, cosa si è deciso e perché"],
        ["`glossary`", "spiegazioni brevi ma complete dei concetti, con fonti, per le icone \"?\""],
        ["`vocabulary`", "etichette IT/EN di tutti i valori codificati (es. `climaterico` → \"Climaterico\" / \"Climacteric\"), con il rimando al glossario"],
        ["`field_help`", "quale voce del glossario spiega ogni campo"],
        ["legende e metodi", "stati stagionali, zone EUFIC, macro-aree, metodo di stagionalità, post-raccolta, deperibilità, conservazione, impronte"],
        ["`sustainable_diet_summary`", "sintesi EUFIC sulla dieta sostenibile"],
    ], ["Campo", "Contenuto"]))
    w("\n### 3.3 Il sistema di aiuto (icone \"?\")\n")
    w("Una spiegazione è scritta una volta sola, nel glossario, e raggiunta da più punti:\n")
    w(f"- **dal campo**: `metadata.field_help` collega {len(md['field_help'])} percorsi di campo (es. `ripening_and_storage.ripening_type`) alle voci che li spiegano;")
    w(f"- **dal valore**: ogni valore di `metadata.vocabulary` ({len(md['vocabulary'])} gruppi) può puntare a una voce (es. `climaterico` → voce *climacteric*);")
    w("- **dall'alimento**: `item.help_refs` elenca le voci pertinenti per quell'alimento e i campi dove mostrarle, calcolate dal contenuto (allergeni, glutine, DOP, PAT, favismo per la fava, stime Q10, coltura in serra…);")
    w("- **da una voce all'altra**: `see_also`; e **dalla fonte**: `official_sources[].used_for.glossary_entries`.\n")
    w("Ogni voce ha `term`, `short` (una riga per il tooltip) e `text` (spiegazione completa) in IT e EN, e le fonti con nome e URL risolti dal catalogo. "
      "L'app quindi non contiene testi di aiuto propri: legge tutto dal database.\n")
    w("Voci: " + ", ".join(f"*{g['term']['it']}*" for g in md["glossary"].values()) + ".\n")
    w("### 3.4 Bilinguismo\n")
    w("L'app deve funzionare interamente in italiano o interamente in inglese. Convenzioni applicate e verificate dall'audit:\n")
    for t in [
        "ogni testo per l'utente è un oggetto `{it, en}`: nomi, testi, etichette, consigli, legende, glossario, descrizioni delle fonti, motivazioni (`basis`, `derivation`, `method`, note delle varietà);",
        "i valori codificati (categoria, stato stagionale, classi, luoghi di conservazione…) sono chiavi stabili tradotte da `metadata.vocabulary`, mai mostrate così come sono;",
        "per nutrienti e composti restano le coppie `name`/`name_en`;",
        "restano nella lingua originale solo i nomi propri: varietà, DOP/IGP, PAT, nomi scientifici, autori, licenze, nomi delle fonti, citazioni testuali delle fonti;",
        "`data_completeness.notes` è un registro tecnico interno in italiano, non destinato all'app.",
    ]:
        w(f"- {t}")
    w("")

    # ------------------------------------------------------------------ 4. fonti
    w("## 4. Fonti\n")
    w("Il catalogo completo, con descrizione, autorevolezza, contenuti e l'elenco di tutti gli alimenti per cui ogni fonte è stata consultata, "
      "è in testa al database (`metadata.official_sources`) ed è riportato nella guida. Riepilogo:\n")
    rows = []
    for s in sorted(md["official_sources"], key=lambda s: -s["used_for"]["items_count"]):
        u = s["used_for"]
        rows.append([s.get("name", s["key"])[:75], "tutto il database" if u["database_level"] and not u["items_count"] else u["items_count"],
                     ", ".join(t["label"]["it"] for t in u["topics"])[:80]])
    w(table(rows, ["Fonte", "Alimenti", "Usata per"]))
    w("\nFonti valutate e non usate: ISMEA e calendari regionali per le epoche di raccolta della frutta (nessun dato strutturato per macro-area); "
      "USDA ARS Image Gallery (poche immagini pertinenti); calendario MAPA (Spagna), indicato da EUFIC ma non raggiungibile (pagine 404). "
      "My-PersonalTrainer è usato solo per testi e link, nessun valore numerico.\n")

    # ------------------------------------------------------------------ 5. conflitti
    w("## 5. Conflitti tra fonti e decisioni\n")
    w("I casi sono in `metadata.source_conflicts` (IT/EN). In breve:\n")
    for c in md["source_conflicts"]:
        w(f"- **{c['issue']['it']}** {c['why']['it']} → *Decisione:* {c['decision']['it']} *Perché:* {c['rationale']['it']}")
    w("\nI singoli casi alimento per alimento restano registrati in `data_completeness.discrepancies` "
      f"({disc} discrepanze tra la bozza e le fonti) e nei campi `basis` e `note`.\n")

    # ------------------------------------------------------------------ 6. validazione
    w("## 6. Come è stato validato\n")
    w("Quattro livelli di controllo, tutti rieseguibili.\n")
    w("### 6.1 Schema\n")
    w("`validate_db.py` verifica il database contro `data/schema.json` (tipi, campi obbligatori, valori ammessi, formato dei mesi e dei testi "
      "bilingui) e alcuni controlli di coerenza (id, somma acqua+macronutrienti, file immagine presenti). Esito: nessun errore sui dati; "
      "gli unici errori sono le immagini che stai eliminando, che spariranno con la sincronizzazione finale.\n")
    w("### 6.2 Verifiche incrociate sulle fonti\n")
    for t in [
        "**Botanica**: nome scientifico confrontato tra EPPO, WFO e GBIF; genere coerente con nome scientifico e codice UPOV.",
        "**Varietà**: mostrate solo se trovate in una fonte (testi delle fonti, Slow Food, Catalogo comune UE, con nome registrato e Paese).",
        "**DOP/IGP**: ogni denominazione controllata sul registro UE eAmbrosia (stato e categoria).",
        "**Nutrizione**: calorie ricalcolate dai macronutrienti, %VNR e claim UE ricalcolati dai valori, sale = sodio × 2,5.",
        "**Post-raccolta**: valori dei capitoli HB66 trascritti con la citazione in `scripts/config/hb66_chapter_curated.json`; refusi evidenti della tabella riassuntiva esclusi.",
    ]:
        w(f"- {t}")
    w("\n### 6.3 Ricontrollo sistematico voce per voce\n")
    w("`audit_db.py` controlla ogni scheda: coerenza calorie/macronutrienti, %VNR, claim UE, porzioni e impronte per porzione; stati stagionali e "
      "mesi; raccolta rispetto alla stagionalità; intervalli min ≤ max; soglie di danno da freddo e punti di congelamento; durate domestiche "
      "rispetto a quelle professionali; luogo di conservazione rispetto alle etichette dei testi; etilene (produttori, \"tenere lontano da\"); "
      "classe di respirazione rispetto alla deperibilità; gruppo di compatibilità rispetto alle temperature; botanica; varietà; DOP/IGP; "
      "immagini e licenze; URL delle fonti; completezza dei testi IT/EN e assenza di testo italiano nei campi inglesi. Controlla inoltre i "
      "metadati: ogni voce del glossario bilingue e con fonti registrate, rimandi `see_also`, `field_help` e `help_refs` verso voci esistenti, "
      "ogni valore codificato presente nel vocabolario, ogni fonte descritta.\n")
    w("Segnalazioni residue sui dati (spiegate, non sono errori):\n")
    rows = [[a["severity"], a["item"], a["field"], a["msg"][:110]] for a in audit if a["severity"] in ("E", "W") and a["area"] != "immagini"]
    w(table(rows, ["Livello", "Alimento", "Campo", "Dettaglio"]))
    w("\nSpiegazione: il cavolo nero ha zuccheri > carboidrati per come USDA calcola i carboidrati (per differenza) → annotato; l'orzo supera "
      "di poco 105 g/100 g sommando acqua e macronutrienti per arrotondamenti della tabella CREA; le soglie \"sotto la temperatura ottimale\" "
      "derivano dall'estremo dell'intervallo minimo sicuro HB66; cipolla secca nel gruppo 3 e melone/avocado nel gruppo 1B sono come nella "
      "tabella di compatibilità HB66 (gruppi per lo stoccaggio misto di 7 giorni, non temperature ottimali); le differenze tra etichette e "
      "FoodKeeper per peperoncino, banana e melograno sono volute (guida UC Davis per il gusto).\n")
    w("### 6.4 Copertura del template e riproducibilità\n")
    full = sum(1 for c in cov.values() if not c["draft"] and not c["missing"])
    w(f"`template_coverage.py` verifica, per ognuno dei {len(cov)} campi del modello JSON del prompt, quanti alimenti hanno un dato verificato: "
      f"{full} campi sono completi per tutti i {N} alimenti (dettaglio in `data/template_coverage.json`). "
      "Infine il tratto finale della pipeline è stato rieseguito da un'istantanea precedente: il risultato coincide con il database consegnato "
      "(la riesecuzione ha anche fatto emergere e correggere una dipendenza d'ordine nel registro delle fonti).\n")

    # ------------------------------------------------------------------ 7. recupero e lacune
    w("## 7. Dati recuperati e lacune residue\n")
    ph = [i["ripening_and_storage"]["postharvest_physiology"] for i in items]
    fz = sum(1 for p in ph if p.get("freezing_point_c") is not None)
    rc = sum(1 for p in ph if p.get("respiration_rate_class"))
    q10 = sum(1 for i in items if "Q10" in json.dumps(i["ripening_and_storage"].get("perishability"), ensure_ascii=False))
    zsrc = collections.Counter(z.get("source") for i in items for z in (i["seasonality"].get("eufic_zone_sources") or {}).values())
    agb = sum(1 for i in items if ((i["nutrition_and_sustainability"].get("environmental_footprint") or {}).get("carbon_reference") or {}).get("source") == "agribalyse")
    w("Recuperi dell'ultima fase, dalle fonti proposte:\n")
    for t in [
        f"**Punto di congelamento** (\"highest freezing point\" di HB66, cioè la temperatura più alta a cui inizia a formarsi ghiaccio; se la fonte dà un intervallo si usa l'estremo più alto, il più prudente): {fz} alimenti. Gli altri non hanno il valore nel capitolo HB66.",
        f"**Classe di respirazione**: {rc} alimenti; {q10} stimate a 5 °C dai valori misurati a temperatura più alta con i Q10 di HB66, marcate come stimate. Restano senza classe: cardo, zucca, castagna, rosmarino, mela cotogna (nessun valore misurato).",
        f"**Impronta di carbonio delle erbe aromatiche**: {agb} da AGRIBALYSE 3.1 (ADEME), con confini del sistema dichiarati (fino al consumo, quindi non confrontabile 1:1 con SU-EATABLE LIFE). Impronta idrica non presa da AGRIBALYSE, perché misura la scarsità e non il volume.",
        "**Stagionalità italiana per alimenti assenti dai calendari**: pesca noce dalla pesca (i calendari non le distinguono; lo confermano l'IGP \"Pesca e Nettarina di Romagna\" ed EUFIC); tartufo nero e bianco dalla Legge 752/1985, art. 6 (periodi di raccolta); ovolo dalla scheda della Provincia di Cuneo (\"estate e inizio autunno\"). Fonte in `seasonality.italy_source`.",
        "**Decisioni sul perimetro (5 novembre)**: bietola da coste e da taglio unite in \"Bietola\" (stessa specie e stessa scheda CREA); pesca tabacchiera aggiunta come varietà della pesca (Arca del Gusto Slow Food); tartufo bianco aggiunto in deroga alla regola di ammissione (nessuna scheda CREA/BDA: nutrizione vuota e dichiarata). Dalla revisione sistematica degli esclusi (`data/excluded_candidates_report.md`) l'utente ha poi deciso di includere 44 alimenti (tutti tranne bergamotto, cappero, acetosa, corbezzolo e portulaca) anche con campi incompleti: sono stati costruiti con la stessa pipeline, su un database di prova, e poi uniti; dove mancano dati ufficiali il campo resta vuoto e dichiarato. Per 33 di loro la stagionalità italiana viene da fonti specifiche lette a mano (`config/italy_seasonality_curated.json`): periodi di raccolta di Orto da Coltivare, schede Slow Food, schede funghi della Provincia di Cuneo, disciplinare IGP delle amarene; taccola e mirabella riprendono pisello e susina (stessa specie). Per 4 la nutrizione viene da una voce USDA di un prodotto affine, dichiarata come approssimazione.",
        "**Stime per le zone senza dato** (decisione del 6 novembre): molte zone EUFIC mancano (la pannonica comprende solo l'Ungheria). `seasonality.estimates` contiene, separate dai dati, le stime dalla zona vicina con il clima più simile (es. pannonica <- continentale), marcate nell'app con ≈ e disattivabili dalle Impostazioni; la stima parte sempre da un dato vero. Per i frutti esotici le zone senza dato sono \"Non coltivato qui\". Metodo in `metadata.seasonality_estimates_method`.",
        f"**Zone climatiche europee**: zona alpina da calendario del Ministero della salute austriaco, fonte nazionale indicata da EUFIC ({zsrc['austria_gesundheitsportal']} alimenti); zona mediterranea derivata, dichiaratamente, dalla stagionalità di Sud e Isole ({zsrc['derived_italy_sud_isole']} alimenti). Provenienza in `seasonality.eufic_zone_sources`.",
    ]:
        w(f"- {t}")
    w("\nNon recuperabili con fonti accessibili (lacune documentate):\n")
    for t in [
        "**Calendari agricoli di frutta, erbe e cereali per macro-area**: né ISMEA né i servizi regionali pubblicano dati strutturati per Nord/Centro/Sud; i valori della bozza restano \"da verificare\".",
        "**Varietà locali (L. 194/2015)**: non esiste un elenco nazionale scaricabile, solo registri regionali eterogenei.",
        "**Zone atlantica, continentale, boreale e pannonica mancanti**: riguardano soprattutto prodotti che lì non si coltivano (agrumi, cachi, nespola, fico d'India); restano vuote.",
        "**Parametri agronomici di erbe e funghi (CREA-OF)**: non tentato in questa fase.",
        "**Funghi spontanei e tartufo**: nessuna impronta ambientale (raccolta spontanea, nessuno studio LCA).",
    ]:
        w(f"- {t}")
    w("\nMappa delle lacune (campi senza dato):\n")
    gap = collections.defaultdict(set)
    for i in items:
        for p in i["data_completeness"]["missing_fields"]:
            q = re.sub(r"\[\d+\]", "", p)
            key = ".".join(q.split(".")[:3]) if q.startswith(("ripening", "nutrition", "seasonality.eufic")) else ".".join(q.split(".")[:2])
            gap[key].add(i["id"])
    rows = [[f"`{k}`", len(u), ", ".join(x.split("_")[0] for x in sorted(u)[:10]) + (" …" if len(u) > 10 else "")]
            for k, u in sorted(gap.items(), key=lambda x: -len(x[1]))]
    w(table(rows[:30], ["Campo", "Alimenti", "Quali (primi 10)"]))
    w("")

    # ------------------------------------------------------------------ 8. avvertenze
    w("## 8. Avvertenze per l'uso nell'app\n")
    for t in [
        "**Fonti non italiane**: conservazione (USDA HB66, FoodKeeper, UC Davis), composti bioattivi (USDA, Phenol-Explorer) e alcuni micronutrienti vengono da fonti USA o internazionali; la nutrizione principale è CREA o BDA-IEO.",
        "**Durate**: la durata domestica (FoodKeeper) e quella professionale (HB66) sono campi distinti; l'app deve mostrare all'utente la prima.",
        "**Impronte ambientali**: mediane di letteratura con alta variabilità; le soglie basso/medio/alto sono una convenzione dell'app, dichiarata in `basis`.",
        "**Polifenoli**: valori indicativi per 100 g di prodotto crudo. Phenol-Explorer: uso non commerciale, citare la fonte.",
        "**Claim UE**: calcolati sul crudo per 100 g (Reg. CE 1924/2006); il claim \"proteine\" nei prodotti poco calorici è contestualizzato con i LARN.",
        "**PAT**: collegamento per parole chiave; include anche prodotti trasformati.",
        "**Testi**: riscritti fondendo più fonti e riallineati ai dati; alcune frasi descrittive (curiosità, usi in cucina) sono di conoscenza generale.",
    ]:
        w(f"- {t}")
    w("")

    # ------------------------------------------------------------------ 9. stato per alimento
    w("## 9. Stato per alimento\n")
    rows = []
    for i in sorted(items, key=lambda x: (x["category"], x["names"]["it"])):
        d = i["data_completeness"]
        ae = sum(1 for a in audit if a["item"] == i["id"] and a["severity"] in ("E", "W") and a["area"] != "immagini")
        rows.append([i["names"]["it"], CAT_IT[i["category"]], len(i["sources_by_topic"]["sources_used"]), len(i.get("help_refs", [])),
                     len(d["fields_pending_verification"]), len(d["missing_fields"]), len(d.get("not_applicable_fields", [])), ae])
    w(table(rows, ["Alimento", "Categoria", "Fonti", "Voci di aiuto", "Da verificare", "Mancanti", "N/A", "Segnalazioni"]))
    w("\n## 10. Riproducibilità e file\n")
    for t in [
        "`data/database.json` – il database; `data/schema.json` – lo schema; `data/database_guide.md` – la guida ai campi.",
        "`data/draft_legacy_values.json` – valori della bozza tolti dall'app; `data/_backup_bozza_2026-11-04/` – la bozza originale.",
        "`data/audit_findings.json`, `data/template_coverage.json` – esiti dei controlli.",
        "`data/raw/` – copie delle fonti scaricate; `scripts/config/` – configurazioni curate con citazioni; `scripts/texts/` – testi IT/EN.",
        "`scripts/` – la pipeline, ordine in `scripts/README.md`.",
    ]:
        w(f"- {t}")
    w("")
    (DATA / "scraping_report.md").write_text("\n".join(L), encoding="utf-8")
    print("scritto data/scraping_report.md:", len("\n".join(L)), "caratteri")


if __name__ == "__main__":
    main()
