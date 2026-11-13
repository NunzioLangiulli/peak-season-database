"""Full source trace per product + useful links for the app.

sources_by_topic.sources_used = [{source_key, name, topics[], urls[], local_files[]}]: every source actually
used for the product (nutrition, seasonality, calendar, postharvest, botany, PDO/PGI, varieties, texts, images).
sources_by_topic.useful_links = [{title{it,en}, url, source_key, topic}]: product-specific links, suitable to be
shown in the app (excludes generic pages shared by many products, except EUFIC and USDA HB66 with a page).
Adds to the register the sources used along the way (USDA FDC, FoodKeeper, Slow Food, Unsplash, Pixabay).
Usage:  python scripts/build_source_registry.py
"""
import collections
import glob
import json
import re
import urllib.parse

from common import CONFIG, DATA, RAW, load_json, save_json
from enrich_postharvest import MAP, load_hb66
from text_corpus import norm

NEW_SOURCES = [
    {"key": "agribalyse", "number": "agg.", "name": "AGRIBALYSE 3.1 (ADEME, Francia) - impatti ambientali degli alimenti", "url": "https://data.ademe.fr/datasets/agribalyse-31-synthese",
     "topics": ["environmental_footprint"], "access": "CSV ufficiale (data.ademe.fr)", "license_note": "Licence Ouverte / Etalab"},
    {"key": "austria_gesundheitsportal", "number": "agg.", "name": "Gesundheitsportal Österreichs - Saisonkalender (Ministero della salute austriaco)",
     "url": "https://www.gesundheit.gv.at/leben/ernaehrung/saisonkalender.html", "topics": ["seasonality_europe"], "access": "pagina web letta dal browser", "license_note": None},
    {"key": "uc_davis_storing_guide", "number": "agg.", "name": "UC Davis / Kader - Storing Fresh Fruits and Vegetables for Better Taste (UC ANR Pub. 21590)",
     "url": "https://homeorchard.ucanr.edu/files/115275.pdf", "topics": ["home_storage"], "access": "PDF (copia in data/raw/ucdavis_storing/)", "license_note": None},
    {"key": "legge_752_1985", "number": "agg.", "name": "Legge 16 dicembre 1985, n. 752 - Normativa quadro sui tartufi (art. 6, periodi di raccolta)",
     "url": "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:1985-12-16;752~art6", "topics": ["seasonality"],
     "access": "Normattiva (copia in data/raw/national_calendars/)", "license_note": "Testo normativo pubblico"},
    {"key": "provincia_cuneo_funghi", "number": "agg.", "name": "Provincia di Cuneo - Schede dei funghi commestibili",
     "url": "https://natura.provincia.cuneo.it/funghi/commestibili/amanita-caesarea/", "topics": ["seasonality"],
     "access": "pagina web (copia in data/raw/national_calendars/)", "license_note": None},
    {"key": "bur_emilia_romagna_amarene", "number": "agg.", "name": "Regione Emilia-Romagna, BUR 2012 - Disciplinare IGP Amarene Brusche di Modena (richiesta di modifica)",
     "url": "https://bur.regione.emilia-romagna.it/area-bollettini/bollettini-pubblicati/2012/marzo-periodico-parte-seconda-1a-quindicina/richiesta-di-modifica-del-disciplinare-della-denominazione-amarene-brusche-di-modena/allegato.pdf",
     "topics": ["seasonality"], "access": "PDF (copia in data/raw/seasonality_sources/)", "license_note": "Atto pubblico"},
    {"key": "eea_biogeo", "number": "agg.", "name": "EEA - Biogeographical regions, Europe 2016 (Agenzia europea dell'ambiente)",
     "url": "https://www.eea.europa.eu/", "topics": ["seasonality_europe"],
     "access": "servizio ArcGIS EEA, strato semplificato in data/raw/eea_biogeo/ (scripts/build_europe_map.py)", "license_note": "CC BY 4.0"},
    {"key": "naturasi", "number": "agg.", "name": "NaturaSì - Frutta e verdura di stagione (schede prodotto)",
     "url": "https://www.naturasi.it/frutta-verdura-di-stagione/cipollotto", "topics": ["seasonality"],
     "access": "pagina web letta col browser (estratto in data/raw/seasonality_sources/)", "license_note": None},
    {"key": "biblioteca_bertoliana", "number": "agg.", "name": "Biblioteca civica Bertoliana (Vicenza) - Scheda botanica del lampascione",
     "url": "https://www.bibliotecabertoliana.it/file/4959-lampascione.pdf", "topics": ["seasonality"],
     "access": "PDF (copia in data/raw/seasonality_sources/)", "license_note": None},
    {"key": "iss_istisan_09_47", "number": "agg.", "name": "Istituto Superiore di Sanità - Rapporti ISTISAN 09/47 (carenza di G6PD e favismo)",
     "url": "https://www.iss.it/documents/20126/45616/0947web.pdf", "topics": ["health_notes"], "access": "PDF", "license_note": None},
    {"key": "usda_fdc", "number": "agg.", "name": "USDA FoodData Central - SR Legacy (2018-04)", "url": "https://fdc.nal.usda.gov/",
     "topics": ["nutrition", "bioactive_compounds"], "access": "CSV ufficiale + API (fonte non italiana, usata solo dove mancano CREA/BDA o per i carotenoidi)",
     "license_note": "Dominio pubblico USA (CC0)"},
    {"key": "usda_flavonoids", "number": "agg.", "name": "USDA Database for the Flavonoid Content of Selected Foods, Release 3.3 (2018)",
     "url": "https://www.ars.usda.gov/northeast-area/beltsville-md-bhnrc/beltsville-human-nutrition-research-center/methods-and-application-of-food-composition-laboratory/mafcl-site-pages/flavonoids/",
     "topics": ["bioactive_compounds"], "access": "database Access Flav_R03-3.accdb esportato in CSV", "license_note": "Dominio pubblico USA"},
    {"key": "phenol_explorer", "number": "agg.", "name": "Phenol-Explorer 3.6 - database del contenuto di polifenoli negli alimenti (INRA)",
     "url": "http://phenol-explorer.eu/", "topics": ["bioactive_compounds"], "access": "composition-data.xlsx (download ufficiale)",
     "license_note": "Gratuito; uso commerciale solo con permesso degli autori e citazione (Rothwell et al., Database 2013)"},
    {"key": "ieo_smartfood_portions", "number": "agg.", "name": "IEO SmartFood - Porzioni e frequenze (porzioni standard LARN-SINU)",
     "url": "https://www.smartfood.ieo.it/media/p02bkul0/smartfood-tab-porzioni-e-frequenze-completa.pdf", "topics": ["reference_portion"],
     "access": "PDF (copia in data/raw/porzioni/)", "license_note": None},
    {"key": "su_eatable_life", "number": "agg.", "name": "SU-EATABLE LIFE - database delle impronte di carbonio e idrica (Petersson et al. 2021)",
     "url": "https://doi.org/10.1038/s41597-021-00909-8", "topics": ["environmental_footprint"],
     "access": "xlsx figshare 13271111", "license_note": "CC BY 4.0"},
    {"key": "masaf_pat", "number": "agg.", "name": "MASAF - Elenco nazionale dei Prodotti Agroalimentari Tradizionali, XXVI revisione (2026)",
     "url": "https://www.masaf.gov.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/24151", "topics": ["traditional_products"],
     "access": "tabella xlsx per Regione e categoria", "license_note": None},
    {"key": "usda_foodkeeper", "number": "agg.", "name": "USDA FSIS FoodKeeper", "url": "https://www.foodsafety.gov/keep-food-safe/foodkeeper-app",
     "topics": ["home_storage"], "access": "JSON https://www.fsis.usda.gov/shared/data/EN/foodkeeper.json letto col browser", "license_note": "Dominio pubblico USA"},
    {"key": "slow_food", "number": "agg.", "name": "Fondazione Slow Food per la Biodiversità - Presìdi e Arca del Gusto",
     "url": "https://www.fondazioneslowfood.com/it/", "topics": ["varieties"], "access": "sitemap XML dei Presìdi e dell'Arca del Gusto", "license_note": None},
    {"key": "eu_plant_variety_portal", "number": "agg.", "name": "EU Plant Variety Portal - Catalogo comune UE delle varieta' (agricole, ortive, frutticole)",
     "url": "https://ec.europa.eu/food/plant-variety-portal/", "topics": ["varieties"], "access": "ricerca per denominazione dal browser (POST del modulo)", "license_note": "Commissione europea, riuso consentito con citazione"},
    {"key": "unsplash", "number": "agg.", "name": "Unsplash API", "url": "https://unsplash.com/", "topics": ["images"], "access": "API (licenza Unsplash)", "license_note": "Unsplash License"},
    {"key": "pixabay", "number": "agg.", "name": "Pixabay API", "url": "https://pixabay.com/", "topics": ["images"], "access": "API", "license_note": "Pixabay Content License"},
]
NAMES_T = {  # titles of the useful links: source_key -> (it, en)
    "altroconsumo": ("Stagionalità, scelta e conservazione - Altroconsumo", "Seasonality, choosing and storage - Altroconsumo (IT)"),
    "ortodacoltivare": ("Come coltivarlo nell'orto - Orto da Coltivare", "How to grow it - Orto da Coltivare (IT)"),
    "my_personaltrainer": ("Proprietà e ricette - My-PersonalTrainer", "Properties and recipes - My-PersonalTrainer (IT)"),
    "crea": ("Tabella nutrizionale - CREA Alimenti e Nutrizione", "Nutrition table - CREA (IT)"),
    "bda_ieo": ("Composizione - Banca Dati IEO", "Composition - IEO food database (IT)"),
    "usda_fdc": ("Dati nutrizionali e carotenoidi - USDA FoodData Central", "Nutrients and carotenoids - USDA FoodData Central"),
    "uc_davis": ("Scheda post-raccolta - UC Davis", "Postharvest fact sheet - UC Davis"),
    "usda_hb66": ("Conservazione professionale - USDA Handbook 66", "Commercial storage - USDA Handbook 66"),
    "eufic_map": ("Stagionalità nei Paesi europei - EUFIC", "Seasonality across Europe - EUFIC"),
    "eppo": ("Scheda tassonomica - EPPO Global Database", "Taxonomy - EPPO Global Database"),
    "wfo": ("Scheda botanica - World Flora Online", "Botany - World Flora Online"),
    "gbif": ("Scheda tassonomica - GBIF", "Taxonomy - GBIF"),
}
LOCAL = {"wwf": "fonti_locali/Calendario-della-Frutta-e-Verdura-di-Stagione.pdf",
         "greenpeace": "fonti_locali/calendario-frutta-e-verdura-di-stagione_greenpeace.pdf",
         "biosuisse": "fonti_locali/BioSuisse-calendariostagionale-2026-11-01.pdf"}
IMG_HOST = {"commons.wikimedia.org": "wikimedia", "upload.wikimedia.org": "wikimedia", "unsplash.com": "unsplash",
            "pixabay.com": "pixabay", "inaturalist.org": "inaturalist", "ars.usda.gov": "usda_ars_images"}


def main():
    reg = load_json(CONFIG / "sources_registry.json")
    have = {s["key"] for s in reg["sources"]}
    reg["sources"] += [s for s in NEW_SOURCES if s["key"] not in have]
    save_json(CONFIG / "sources_registry.json", reg)
    rname = {s["key"]: s["name"] for s in reg["sources"]}
    db = load_json(DATA / "database.json")
    db["metadata"]["official_sources"] = reg["sources"]
    chap, _ = load_hb66()
    hb_cur = load_json(CONFIG / "hb66_chapter_curated.json")["items"]
    cf = load_json(CONFIG / "hb66_chilling_freezing.json")
    hb_chill = set(cf["chilling"]) | set(cf["chilling_cultivar_dependent"])
    hb_frz = {i for g in cf["freezing"].values() for i in g["items"]}
    fk_map = load_json(RAW / "foodkeeper_produce.json")["mapping"]
    texts = {}
    for f in sorted(glob.glob(str(CONFIG.parent / "texts" / "block_*.json"))):
        texts.update(load_json(f))
    gi = {}
    for r in load_json(RAW / "eambrosia_it.json")["items"]:
        gi[norm(r["protectedName"])] = r
    # URLs shared by many products = generic pages
    url_count = collections.Counter(u for it in db["items"] for u in set(it["sources_by_topic"]["seasonality_and_storage_urls"]
                                                                          + it["sources_by_topic"]["agricultural_calendar_urls"]))
    tot = collections.Counter()
    for it in db["items"]:
        s = it["sources_by_topic"]
        sc = s.get("source_codes", {})
        used = collections.OrderedDict()

        def add(key, topic, url=None, local=None):
            e = used.setdefault(key, {"source_key": key, "name": rname.get(key, key), "topics": [], "urls": [], "local_files": []})
            if topic not in e["topics"]:
                e["topics"].append(topic)
            if url and url not in e["urls"]:
                e["urls"].append(url)
            if local and local not in e["local_files"]:
                e["local_files"].append(local)

        n = it["nutrition_and_sustainability"]
        if s.get("nutrition_crea_url"):
            add("crea", "nutrition", s["nutrition_crea_url"])
        if sc.get("bda_ieo") and s.get("nutrition_bda_ieo_url"):
            add("bda_ieo", "nutrition", s["nutrition_bda_ieo_url"])
        fdc = [u for u in s.get("other_urls", []) if "fdc.nal.usda.gov" in u]
        for u in fdc:
            dbs = n.get("data_basis") or ""
            dbs = dbs.get("it", "") if isinstance(dbs, dict) else dbs
            add("usda_fdc", "nutrition" if dbs.startswith("USDA") else "bioactive_compounds", u)
            if n.get("bioactive_compounds"):
                add("usda_fdc", "bioactive_compounds", u)
        bsrc = {c.get("source") for c in (n.get("bioactive_compounds") or [])}
        if "usda_flavonoids" in bsrc:
            add("usda_flavonoids", "bioactive_compounds", "https://www.ars.usda.gov/ARSUserFiles/80400535/Data/Flav/Flav3.3.pdf")
        if it["botany"].get("upov_code"):
            add("eu_plant_variety_portal", "botany_upov_code", "https://ec.europa.eu/food/plant-variety-portal/")
        if n.get("reference_portion"):
            add("ieo_smartfood_portions", "reference_portion", n["reference_portion"]["source"])
        if n.get("environmental_footprint"):
            add("su_eatable_life", "environmental_footprint", "https://doi.org/10.1038/s41597-021-00909-8")
        if (n.get("traditional_products_pat") or {}).get("count"):
            add("masaf_pat", "traditional_products", "https://www.masaf.gov.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/24151")
        if "allergens_eu" in n:
            add("reg_1169_2011", "allergens", "https://eur-lex.europa.eu/legal-content/IT/TXT/HTML/?uri=CELEX:02011R1169-20180101")
        if it["ripening_and_storage"].get("storage_compatibility"):
            add("usda_hb66", "storage_compatibility", "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf#page=65")
        hs = (it["ripening_and_storage"].get("home_storage") or {}).get("sources", [])
        if any(x.startswith("uc_davis_storing_guide") for x in hs):
            add("uc_davis_storing_guide", "home_storage", "https://homeorchard.ucanr.edu/files/115275.pdf")
        cref = ((n.get("environmental_footprint") or {}).get("carbon_reference") or {})
        if cref.get("source") == "agribalyse":
            add("agribalyse", "environmental_footprint", "https://data.ademe.fr/datasets/agribalyse-31-synthese")
        if any(z.get("source") == "austria_gesundheitsportal" for z in (it["seasonality"].get("eufic_zone_sources") or {}).values()):
            add("austria_gesundheitsportal", "seasonality_europe", "https://www.gesundheit.gv.at/leben/ernaehrung/saisonkalender.html")
        isrc = (it["seasonality"].get("italy_source") or {})
        if isrc.get("source") in ("legge_752_1985", "provincia_cuneo_funghi", "ortodacoltivare", "slow_food", "bur_emilia_romagna_amarene", "biblioteca_bertoliana", "naturasi"):
            add(isrc["source"], "seasonality", isrc["url"])
        if "G6PD" in json.dumps(it, ensure_ascii=False):  # favism warning
            add("iss_istisan_09_47", "health_notes", "https://www.iss.it/documents/20126/45616/0947web.pdf")
        if "phenol_explorer" in bsrc:
            add("phenol_explorer", "bioactive_compounds", "http://phenol-explorer.eu/")
        if n.get("nutrition_claims_eu"):
            add("reg_1924_2006", "nutrition_claims", "https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32006R1924")
        if any(v.get("percent_nrv") is not None for v in (n.get("vitamins") or []) + (n.get("minerals") or [])):
            add("reg_1169_2011", "percent_nrv", "https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32011R1169")
        if n.get("protein_reference"):
            add("larn_sinu", "reference_intakes", "https://sinu.it/tabelle-larn-2014/", "fonti_locali/Tabelle-riassuntive_SINU.pdf")
        for u in s.get("seasonality_and_storage_urls", []):
            if "altroconsumo" in u:
                add("altroconsumo", "seasonality", u)
                add("altroconsumo", "buying_guide")
            elif "my-personaltrainer" in u and url_count[u] <= 3:   # the shared generic page was not used
                add("my_personaltrainer", "verification_texts", u)
        mp = re.search(r"Parte usata '[^']+' confermata dai testi di: ([^.]+)\.", it["data_completeness"]["notes"])
        for k in (mp.group(1).split(", ") if mp else []):
            key = {"orto_da_coltivare": "ortodacoltivare"}.get(k, k)
            add(key, "plant_part_used", None)
        for key, row in (("wwf", sc.get("wwf_row")), ("greenpeace", sc.get("greenpeace_name")), ("biosuisse", sc.get("biosuisse_row"))):
            if row:
                add(key, "seasonality", local=LOCAL[key])
        if sc.get("eufic_keys"):
            add("eufic_map", "seasonality_europe", s.get("eufic_url"))
        if sc.get("odc_pdf_row"):
            for f in s.get("local_files_used", []):
                if "odc-tabella" in f:
                    add("ortodacoltivare", "agricultural_calendar", local=f)
        for u in s.get("agricultural_calendar_urls", []):
            if "ortodacoltivare" in u:
                add("ortodacoltivare", "agricultural_calendar", u)
        if sc.get("uc_davis"):
            add("uc_davis", "postharvest", f"https://postharvest.ucdavis.edu/produce-facts-sheets/{sc['uc_davis']}")
        m = MAP.get(it["id"])
        hb = "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf"
        if m and m[0] in chap:
            add("usda_hb66", "postharvest", f"{hb}#page={chap[m[0]]['page']}")
        elif m and m[1]:
            add("usda_hb66", "postharvest", f"{hb}#page=17")   # Table 1 only (respiration/ethylene)
        if it["id"] in hb_cur:
            add("usda_hb66", "postharvest", f"{hb}#page={hb_cur[it['id']]['page']}" if hb_cur[it["id"]].get("page") else hb)
        if it["id"] in hb_chill:
            add("usda_hb66", "chilling_injury", f"{hb}#page=73")
        if it["id"] in hb_frz:
            add("usda_hb66", "freezing_susceptibility", f"{hb}#page=75")
        if it["id"] in fk_map:
            add("usda_foodkeeper", "home_storage", "https://www.fsis.usda.gov/shared/data/EN/foodkeeper.json")
        b = it["botany"]
        if b.get("eppo_code"):
            add("eppo", "botany", f"https://gd.eppo.int/taxon/{b['eppo_code']}")
        if b.get("wfo_id"):
            add("wfo", "botany", f"https://www.worldfloraonline.org/taxon/{b['wfo_id']}")
        if b.get("gbif_key"):
            add("gbif", "botany", f"https://www.gbif.org/species/{b['gbif_key']}")
        v = it["italian_varieties_and_territories"]
        gi_links = []
        for lab in v.get("dop_igp_labels") or []:
            r = gi.get(norm(re.sub(r"\s+(DOP|IGP)$", "", lab)))
            url = f"https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/details/{r['appUniqueId']}" if r else None
            add("eambrosia", "dop_igp", url)
            if url:
                gi_links.append((lab, url))
        sf_links = []
        for e in v.get("varieties_verification") or []:
            for src in e["sources"]:
                if src["source_key"] in ("slow_food", "orto_da_coltivare", "altroconsumo", "my_personaltrainer", "usda_hb66", "eu_plant_variety_portal"):
                    key = {"orto_da_coltivare": "ortodacoltivare"}.get(src["source_key"], src["source_key"])
                    add(key, "varieties", None if key == "usda_hb66" else src.get("url"))
                    if key == "slow_food" and src.get("url"):
                        sf_links.append((e["name"], src["url"], src.get("list")))
        t = texts.get(it["id"], {})
        for k in t.get("src", []):
            add({"orto_da_coltivare": "ortodacoltivare", "odc": "ortodacoltivare"}.get(k, k), "texts")
        for d in it["images"].get("image_details") or []:
            host = urllib.parse.urlparse(d.get("source_url") or "").netloc.replace("www.", "")
            key = next((v2 for h, v2 in IMG_HOST.items() if host.endswith(h)), None)
            if key:
                add(key, "images", d.get("source_url"))
        for e in used.values():
            e["urls"] = [u for u in e["urls"] if u]
        s["sources_used"] = list(used.values())
        # historical URL fields consistent with the sources actually used (the draft cited HB66/FoodKeeper for all)
        phu = s.get("postharvest_ucdavis_usda_url")
        phu = [phu] if isinstance(phu, str) else (phu or [])
        if "usda_hb66" not in used:
            phu = [u for u in phu if "commercialstorage" not in u]
        s["postharvest_ucdavis_usda_url"] = phu or None
        if "usda_foodkeeper" not in used:
            s["other_urls"] = [u for u in s.get("other_urls", []) if "foodkeeper" not in u]
        if True:  # generic My-PersonalTrainer page cited by the draft, not used
            s["seasonality_and_storage_urls"] = [u for u in s["seasonality_and_storage_urls"] if "frutta-conservazione-stagionalita" not in u]
        tot.update(used.keys())
        # --- useful links for the app
        links = []

        def link(key, url, topic, title=None):
            if url and not any(x["url"] == url for x in links):
                ti, te = title or NAMES_T[key]
                links.append({"title": {"it": ti, "en": te}, "url": url, "source_key": key, "topic": topic})
        for u in s.get("seasonality_and_storage_urls", []):
            if "altroconsumo" in u:
                link("altroconsumo", u, "seasonality")
        for u in s.get("agricultural_calendar_urls", []):
            if "ortodacoltivare" in u and url_count[u] <= 3:
                link("ortodacoltivare", u, "agricultural_calendar")
        for u in s.get("seasonality_and_storage_urls", []):
            if "my-personaltrainer" in u and url_count[u] <= 3:
                link("my_personaltrainer", u, "health_benefits")
        if s.get("nutrition_crea_url"):
            link("crea", s["nutrition_crea_url"], "nutrition")
        for u in fdc[:1]:
            link("usda_fdc", u, "nutrition")
        if "uc_davis" in used:
            link("uc_davis", used["uc_davis"]["urls"][0], "postharvest")
        if "usda_hb66" in used and used["usda_hb66"]["urls"] and "#page=" in used["usda_hb66"]["urls"][0]:
            link("usda_hb66", used["usda_hb66"]["urls"][0], "postharvest")
        for lab, url in gi_links:
            link("eambrosia", url, "dop_igp", (f"{lab} - registro UE delle DOP/IGP", f"{lab} - EU register of PDO/PGI"))
        for name, url, lst in sf_links:
            nm = re.sub(r"\s*\(.*?\)", "", name)
            lab = ("Presidio Slow Food", "Slow Food Presidium") if lst == "presidio" else ("Arca del Gusto Slow Food", "Slow Food Ark of Taste")
            link("slow_food", url, "varieties", (f"{nm} - {lab[0]}", f"{nm} - {lab[1]}"))
        if s.get("eufic_url") and sc.get("eufic_keys"):
            link("eufic_map", s["eufic_url"], "seasonality_europe")
        for key in ("eppo", "wfo", "gbif"):
            if key in used and used[key]["urls"]:
                link(key, used[key]["urls"][0], "botany")
        s["useful_links"] = links
    from apply_link_overrides import FILE as LINK_OV, apply as apply_link_ov   # modifiche a mano (Admin Studio)
    if LINK_OV.exists():
        apply_link_ov(db, load_json(LINK_OV))
    save_json(DATA / "database.json", db)
    nl = [len(i["sources_by_topic"]["useful_links"]) for i in db["items"]]
    ns = [len(i["sources_by_topic"]["sources_used"]) for i in db["items"]]
    print(f"fonti per alimento: media {sum(ns) / len(ns):.1f} (min {min(ns)}, max {max(ns)}); link utili: media {sum(nl) / len(nl):.1f} (min {min(nl)})")
    print("alimenti per fonte:", dict(tot.most_common()))


if __name__ == "__main__":
    main()
