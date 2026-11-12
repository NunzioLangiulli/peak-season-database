"""Genera data/database_guide.md: guida commentata alla struttura del database, con estratti reali della scheda del pomodoro.
Uso:  python scripts/make_db_guide.py
"""
import json

from common import DATA, load_json

EX = "pomodoro_tomato"


def js(o, limit=None):
    s = json.dumps(o, ensure_ascii=False, indent=2)
    if limit and len(s) > limit:
        s = s[:limit].rsplit("\n", 1)[0] + "\n  …"
    return f"```json\n{s}\n```"


def trim_months(o):
    """Abbrevia gli array di 12 mesi per leggibilità."""
    if isinstance(o, dict):
        return {k: trim_months(v) for k, v in o.items()}
    if isinstance(o, list) and len(o) == 12 and all(isinstance(x, str) for x in o):
        return " ".join({"out_of_season": "·", "in_season": "S", "peak_season": "P", "primizie": "p", "end_of_season": "f",
                         "not_applicable": "x"}[x] for x in o)
    if isinstance(o, list) and len(o) == 12 and all(isinstance(x, bool) for x in o):
        return "".join("S" if x else "·" for x in o)
    return o


def main():
    db = load_json(DATA / "database.json")
    it = next(i for i in db["items"] if i["id"] == EX)
    m = db["metadata"]
    r, n, b = it["ripening_and_storage"], it["nutrition_and_sustainability"], it["botany"]
    ph = r["postharvest_physiology"]
    L = []
    w = L.append
    w("# Guida al database Peak Season\n")
    w("Questa guida spiega come è costruito `data/database.json`, blocco per blocco, usando come esempio la scheda reale del **pomodoro**. "
      "Per ogni blocco: a cosa serve nell'app, da dove vengono i dati, come leggerli.\n")
    w("## 1. I file\n")
    w("| File | Contenuto |\n|---|---|\n"
      f"| `data/database.json` | Il database: `metadata` (legende, metodi, fonti) + `items` ({len(db['items'])} schede) |\n"
      "| `data/schema.json` | Le regole formali (JSON Schema): tipi, valori ammessi, campi obbligatori |\n"
      "| `data/items_index.json` | La lista master: per ogni alimento i codici e gli URL esatti su ogni fonte |\n"
      "| `data/draft_legacy_values.json` | I valori della tua bozza che non erano verificabili: tolti dall'app ma conservati |\n"
      "| `data/scraping_report.md` | Il report di affidabilità e lacune |\n"
      "| `data/audit_findings.json` | L'esito del ricontrollo voce per voce |\n"
      "| `data/raw/` | Copie dei dati grezzi delle fonti (PDF, CSV, xlsx, pagine) |\n"
      "| `scripts/config/` | Tabelle curate a mano dalle fonti, con citazioni e numeri di pagina |\n"
      "| `assets/images/` | Le foto `<id>_01.jpg`, `_02.jpg`… |\n")
    w("## 2. La logica generale\n")
    w("Ogni scheda segue lo stesso schema in 12 blocchi. Tre principi valgono ovunque:\n")
    w("1. **Ogni dato ha una fonte.** I blocchi strutturati portano la fonte accanto al valore (`source`, `basis`, `source_food`, `derivation`); "
      "le fonti di tutta la scheda sono elencate in `sources_by_topic.sources_used`.")
    w("2. **`null` non è uguale a vuoto.** Un `null` è una lacuna vera (elencata in `data_completeness.missing_fields`), oppure un campo che "
      "non ha senso per quell'alimento (elencato in `not_applicable_fields`): ad esempio la soglia di danno da freddo per chi non soffre il freddo.")
    w("3. **Bilingue.** Tutti i testi per l'utente sono oggetti `{\"it\": …, \"en\": …}` (vedi §13).\n")
    w("Gli identificativi (`id`) sono `nome_it_name_en` senza accenti: sono le chiavi usate anche dai riferimenti tra schede "
      "(es. `keep_away_from`, `compatible_with`) e dai nomi delle foto.\n")

    w("## 3. Identità e botanica\n")
    w(js({k: it[k] for k in ("id", "names", "category")}))
    w("`category` è uno dei 5 valori del template. I sinonimi vengono da EPPO (nomi comuni ufficiali IT/EN).\n")
    w(js(b))
    w("- `scientific_name`, `family`, `genus`: verificati su EPPO e World Flora Online (`eppo_code`, `wfo_id` sono i codici ufficiali).\n"
      "- `plant_part_used`: confermata dai testi delle fonti.\n"
      "- `upov_*`: il codice di specie del **Catalogo comune UE delle varietà**; `varieties_registered_italy.count` = varietà oggi iscritte nel registro italiano.\n")

    w("## 4. Varietà e territori\n")
    iv = it["italian_varieties_and_territories"]
    w(js(iv, 2200))
    w("- `notable_varieties` contiene **solo** varietà verificate; `varieties_verification` dice dove (Slow Food, Catalogo UE, Orto da Coltivare…) e con che nome sono registrate.\n"
      "- `dop_igp_labels` e `has_dop_igp` sono verificati sul registro UE **eAmbrosia** (`eambrosia_verified`).\n"
      "- I **Prodotti Agroalimentari Tradizionali** stanno in `nutrition_and_sustainability.traditional_products_pat` (vedi §9).\n")

    w("## 5. Immagini\n")
    w(js({"primary": it["images"]["primary"], "gallery": it["images"]["gallery"][:3] + ["…"], "image_details": it["images"]["image_details"][:1]}))
    w("Ogni foto ha autore, licenza, URL d'origine e tipo (`view_type`): `full_frame` (il prodotto riempie l'inquadratura: è la "
      "foto principale quando c'è), `isolated_background` (sfondo bianco o colorato), `plant_in_field` (la pianta), `botanical_plate` "
      "(tavola botanica), `cut_section` (tagliato), `other`. `flags` segnala problemi noti (piatto, soggetto sbagliato), `variety` una "
      "varietà particolare (es. pesca tabacchiera). `sync_images.py` riallinea il database se togli foto dalla cartella.\n")

    w("## 6. Stagionalità\n")
    w("Nell'estratto i 12 mesi (gen→dic) sono abbreviati: `·` fuori stagione, `p` primizia, `S` di stagione, `P` picco, `f` fine stagione.\n")
    w(js(trim_months({k: it["seasonality"][k] for k in ("italy_macro_areas", "eufic_climatic_zones", "derivation_notes")})))
    w("- `italy_macro_areas` (Nord, Centro, Sud e Isole) è la stagionalità per l'utente italiano: nasce dal **voto tra più fonti** "
      "(WWF, Greenpeace, Altroconsumo, EUFIC per l'Italia, epoche di raccolta di Orto da Coltivare); il metodo è in `metadata.seasonality_method`. "
      "Per ogni mese si contano le fonti che lo indicano: con almeno metà dei voti il mese è di stagione, con meno è inizio o fine stagione; "
      "il **picco** sono i mesi centrali di un periodo di almeno tre mesi su cui tutte le fonti concordano.\n"
      "- `eufic_climatic_zones`: le 6 zone europee, derivate dai Paesi EUFIC (`eufic_by_country`); dove EUFIC non ha l'alimento, la zona alpina "
      "viene dal calendario austriaco (fonte nazionale indicata da EUFIC) e la mediterranea è derivata dal Sud e Isole. "
      "`eufic_zone_sources` dice la provenienza di ogni zona.\n")

    w("## 7. Calendario agricolo (orto)\n")
    w(js(it["agricultural_calendar_italy"], 1500))
    w("Mesi di semina, trapianto e raccolta per zona, con parametri agronomici (profondità, sesto d'impianto, esposizione, luna) "
      "da Orto da Coltivare. Per frutta, erbe e cereali sono ancora i valori della bozza (lacuna documentata).\n")

    w("## 8. Acquisto, maturazione e conservazione\n")
    w("È il blocco più ricco. Va letto su tre livelli: **testi per l'utente**, **consiglio sintetico**, **dati scientifici**.\n")
    w("### 8a. Testi per l'utente\n")
    w(js({"buying_guide": it["buying_guide"], "card_short_storage": r["card_short_storage"], "ripening_badge_label": r["ripening_badge_label"]}, 1800))
    w("`card_short_storage` è l'etichetta breve per la card (≤ 42 caratteri), allineata ai dati FoodKeeper e UC Davis; `storage_instructions` è il testo lungo.\n")
    w("### 8b. Consiglio sintetico per l'app\n")
    w(js({"home_storage": r["home_storage"], "perishability": r["perishability"]}))
    w("- `home_storage.location`: **dove** tenerlo in casa (frigo, fuori dal frigo finché matura, temperatura ambiente, dispensa). "
      "Fonte principale: la guida UC Davis/Kader; FoodKeeper per le durate; i conflitti tra le due fonti sono scritti in `derivation`.\n"
      "- `perishability`: la classe di respirazione tradotta in un livello da 1 a 6, con etichetta e consiglio. Più un prodotto respira, prima perde freschezza.\n")
    w(js({"storage_compatibility": {**r["storage_compatibility"], "compatible_with": r["storage_compatibility"]["compatible_with"][:6] + ["…"]}}))
    w("`storage_compatibility`: con quali prodotti può stare (stessa temperatura e umidità, nessun conflitto di etilene). Fonte: HB66, tabella di Thompson.\n")
    w("### 8c. Dati scientifici post-raccolta\n")
    w(js(ph))
    w("- `ripening_type` (nel blocco `ripening_and_storage`): `climaterico` (continua a maturare dopo la raccolta, es. pomodoro, banana, pera) "
      "o `non_climaterico` (non matura più, es. agrumi, uva, fragola); etichette IT/EN in `metadata.vocabulary`.\n"
      "- `freezing_point_c`: il \"highest freezing point\" di HB66, la temperatura più alta a cui inizia a formarsi ghiaccio; con un intervallo "
      "si usa l'estremo più alto (il più prudente).\n"
      "- `optimal_temperature_c` e `optimal_humidity_percent`: condizioni **professionali** ottimali (USDA HB66, UC Davis).\n"
      "- `chilling_injury`: se soffre il freddo, sotto quale soglia (`critical_temperature_c` = massimo dell'intervallo minimo sicuro, "
      "`lowest_safe_range_c`) e con quali sintomi. Il pomodoro maturo è sensibile sotto i 7-10 °C (13 °C se ancora verde): per questo è meglio fuori frigo.\n"
      "- `estimated_shelf_life_days`: durate **domestiche** da FoodKeeper (`room_temp_mode` dice se si usa \"fino a maturazione\" o \"solo frigo\"); "
      "`commercial_optimal_days` è la durata in condizioni professionali.\n")
    w(js(r["ethylene_compatibility"]))
    w("Etilene: se lo produce (e quanto, classe a 20 °C) e se ne è sensibile. `keep_away_from` è calcolato: i forti produttori del database "
      "da cui tenerlo lontano, se è sensibile.\n")

    w("## 9. Nutrizione e sostenibilità\n")
    w(js({k: n[k] for k in ("data_basis", "edible_portion_percentage", "water_percentage", "kcal_per_100g", "macros_per_100g")}))
    w("Valori per 100 g di parte edibile. `data_basis` dice quale scheda è la fonte primaria (CREA, poi BDA-IEO, USDA solo se mancano le prime).\n")
    w(js({"vitamins": n["vitamins"][:3] + ["…"], "nutrition_claims_eu": n["nutrition_claims_eu"]}))
    w("Ogni vitamina e minerale ha quantità, unità, `percent_nrv` (% del Valore Nutritivo di Riferimento, Reg. UE 1169/2011) e la fonte. "
      "I **claim** sono calcolati applicando le soglie del Reg. CE 1924/2006 (es. \"Ad alto contenuto di vitamina C\" ≥ 30% VNR): "
      "non sono scritti a mano.\n")
    w(js({"bioactive_compounds": n["bioactive_compounds"][:3] + ["…"]}))
    w("Composti bioattivi: carotenoidi (USDA FDC), classi di flavonoidi (USDA Flavonoid DB), polifenoli totali e acidi fenolici "
      "(Phenol-Explorer). `group` permette di raggrupparli in app, `main_compounds` dice quali sono i principali.\n")
    w(js({k: n[k] for k in ("allergens_eu", "reference_portion", "protein_reference")}))
    w("- `allergens_eu`: allergeni dell'allegato II del Reg. UE 1169/2011 (lista vuota = nessuno).\n"
      "- `reference_portion`: la porzione standard LARN (via IEO SmartFood), con un'equivalenza pratica e i valori per porzione.\n"
      "- `protein_reference`: le proteine rapportate al fabbisogno LARN.\n")
    w(js(n["environmental_footprint"]))
    w("Sostenibilità (SU-EATABLE LIFE): CO2 e acqua per kg e per porzione, con riferimento alla voce del database, numero di studi e intervallo. "
      "`greenhouse_comparison` mostra quanto pesa la serra riscaldata (fuori stagione). `sustainability_rating` traduce i numeri in livelli e consigli.\n")
    pat = n["traditional_products_pat"]
    w(js({**pat, "products": pat["products"][:4] + ["…"], "regions": pat["regions"][:6] + ["…"]}))
    w("`traditional_products_pat`: i Prodotti Agroalimentari Tradizionali dell'elenco MASAF legati all'alimento, con la regione.\n")
    w(js({k: n[k] for k in ("health_benefits_and_curiosities", "culinary_waste_reduction")}))
    w("Testi: benefici (solo con nutrienti coerenti con i claim) e idee anti-spreco.\n")

    w("## 10. Fonti della scheda\n")
    s = it["sources_by_topic"]
    w(js({"sources_used": s["sources_used"][:3] + ["…"], "useful_links": s["useful_links"][:3] + ["…"]}))
    w(f"`sources_used` elenca **tutte** le fonti usate per questo alimento ({len(s['sources_used'])} per il pomodoro), con argomento, URL e file locali. "
      f"`useful_links` sono i link da mostrare all'utente ({len(s['useful_links'])}). `source_codes` contiene i codici esatti delle schede (CREA, BDA, FDC…).\n")

    w("## 11. Tracciabilità: `data_completeness`\n")
    d = it["data_completeness"]
    w(js({"is_complete": d["is_complete"], "fields_pending_verification": d["fields_pending_verification"][:4],
          "missing_fields": d["missing_fields"][:4], "not_applicable_fields": d["not_applicable_fields"][:4],
          "discrepancies": d["discrepancies"][:2], "notes": d["notes"][:400] + "…"}))
    w("Questo blocco serve a te, non all'utente: dice cosa veniva dalla bozza, cosa è stato verificato, cosa manca, cosa non è pertinente, "
      "dove la bozza era diversa dalle fonti (`discrepancies`, con valore della bozza, valore della fonte e fonte) e perché (`notes`).\n")

    w("## 12. I metadati\n")
    w("`metadata` contiene ciò che vale per tutto il database e sta in testa al file: \n")
    for k in m:
        w(f"- `{k}`")
    w("\nLe **legende** (stati stagionali, zone, deperibilità, conservazione, gruppi di compatibilità) e i **metodi** "
      "(stagionalità, post-raccolta, proteine, impronte) sono pensati per essere letti direttamente dall'app.\n")

    w("## 13. Bilinguismo\n")
    w("L'app può essere usata tutta in italiano o tutta in inglese:\n")
    w("- ogni testo per l'utente è `{\"it\": …, \"en\": …}`, comprese le motivazioni (`basis`, `derivation`, `method`, note delle varietà);\n"
      "- i valori codificati (es. `climaterico`, `in_season`, `fridge`) sono chiavi: l'etichetta da mostrare è in `metadata.vocabulary`;\n"
      "- nutrienti e composti hanno `name` e `name_en`;\n"
      "- restano in lingua originale solo i nomi propri (varietà, DOP/IGP, PAT, nomi scientifici, autori, licenze, fonti);\n"
      "- `data_completeness.notes` è un registro tecnico in italiano, non per l'app.\n")
    voc = m["vocabulary"]
    w(js({"ripening_and_storage.ripening_type": voc["ripening_and_storage.ripening_type"]}))
    w(f"Gruppi del vocabolario ({len(voc)}): " + ", ".join(f"`{k}`" for k in voc) + ".\n")

    w("## 14. Glossario e icone \"?\"\n")
    w("Le spiegazioni sono scritte una volta, in `metadata.glossary`, e raggiunte da più punti:\n")
    w("| Da dove | Campo | Esempio |\n|---|---|---|\n"
      "| un campo | `metadata.field_help[percorso]` | `ripening_and_storage.ripening_type` → `climacteric`, `non_climacteric` |\n"
      "| un valore | `metadata.vocabulary[gruppo][valore].glossary` | `climaterico` → `climacteric` |\n"
      "| un alimento | `item.help_refs` | fava → `favism` sul testo dei benefici |\n"
      "| un'altra voce | `glossary[id].see_also` | `climacteric` → `ethylene`, `non_climacteric` |\n"
      "| una fonte | `official_sources[].used_for.glossary_entries` | HB66 → voci di conservazione |\n")
    g = m["glossary"]["climacteric"]
    w(js(g, 2500))
    w("Ogni voce: `term`, `short` (una riga per il tooltip), `text` (spiegazione completa), `sources` (nome e URL dal catalogo), `see_also`. "
      f"Voci ({len(m['glossary'])}): " + ", ".join(f"`{k}`" for k in m["glossary"]) + ".\n")
    w(js({"help_refs": it.get("help_refs", [])[:6]}))
    w(js({"field_help": dict(list(m["field_help"].items())[:6])}))

    w("## 15. Il catalogo delle fonti\n")
    w("`metadata.official_sources` descrive ogni fonte: cos'è (`description`), perché è autorevole (`authority`), cosa offre (`offers`), "
      "per quali argomenti e per quali alimenti è stata consultata (`used_for`). Elenco completo:\n")
    for s in sorted(m["official_sources"], key=lambda s: -s["used_for"]["items_count"]):
        u = s["used_for"]
        w(f"### {s.get('name', s['key'])}\n")
        w(f"`{s['key']}` · {s.get('url', '')}\n")
        w(f"- **Cos'è**: {s['description']['it']}")
        w(f"- **Perché è autorevole**: {s['authority']['it']}")
        w(f"- **Cosa offre**: {s['offers']['it']}")
        w(f"- **Usata per**: " + (", ".join(t["label"]["it"] for t in u["topics"]) or "livello di database"))
        if u["items"]:
            w(f"- **Alimenti ({u['items_count']})**: " + ", ".join(u["items"]))
        elif u["database_level"]:
            w("- **Alimenti**: usata per l'intero database (metodi e legende), non per singole schede")
        if u["glossary_entries"]:
            w(f"- **Voci di glossario**: " + ", ".join(u["glossary_entries"]))
        w("")

    w("## 16. Conflitti tra fonti\n")
    w("`metadata.source_conflicts`: i casi generali in cui le fonti danno valori diversi, con la decisione presa.\n")
    for cf in m["source_conflicts"]:
        w(f"### {cf['issue']['it']}\n")
        w(f"- **Perché**: {cf['why']['it']}\n- **Decisione**: {cf['decision']['it']}\n- **Motivazione**: {cf['rationale']['it']}\n")

    w("## 17. Come usarlo nell'app (suggerimento)\n")
    w("| Schermata | Campi |\n|---|---|\n"
      "| Card dell'alimento | `names`, `images.primary`, stato del mese da `seasonality.italy_macro_areas[zona]`, `ripening_and_storage.card_short_storage`, `perishability.label` |\n"
      "| Lista della spesa | `buying_guide.shopping_list_preview`, `ripening_badge_label` |\n"
      "| Conservazione | `home_storage`, `storage_instructions`, `estimated_shelf_life_days`, `storage_compatibility`, `ethylene_compatibility` |\n"
      "| Nutrizione | `reference_portion`, `macros_per_100g`, `nutrition_claims_eu`, `vitamins`, `minerals`, `allergens_eu` |\n"
      "| Sostenibilità | `environmental_footprint.sustainability_rating`, `greenhouse_comparison`, `metadata.sustainable_diet_summary` |\n"
      "| Territorio | `notable_varieties`, `dop_igp_labels`, `traditional_products_pat`, `varieties_registered_italy` |\n"
      "| Orto | `agricultural_calendar_italy` |\n"
      "| Approfondimenti | `sources_by_topic.useful_links` |\n"
      "| Aiuto \"?\" | `metadata.field_help`, `metadata.vocabulary`, `item.help_refs` → `metadata.glossary` |\n"
      "| Fonti | `metadata.official_sources`, `metadata.source_conflicts` |\n")
    (DATA / "database_guide.md").write_text("\n".join(L), encoding="utf-8")
    print("scritto data/database_guide.md")


if __name__ == "__main__":
    main()
