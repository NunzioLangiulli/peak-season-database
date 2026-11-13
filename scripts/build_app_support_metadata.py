"""Information and rules used by the app, written into the database so that it stays the source of truth (owner rule
"database first, app second", 2026-11-06). Idempotent.

Adds to the metadata:
1. vocabulary["botany.family"]: botanical family name in IT (Italian form of the Latin name, with the
   traditional name in brackets where it exists) and EN (common family name), plus the Latin name.
2. eufic_climatic_zones_legend: ISO 3166-1 alpha-2 country codes (countries_primary_iso, countries_partial_iso)
   and a suggested colour per zone (color_hex, Okabe-Ito palette, readable by colour-blind users too).
3. seasonality_reference_order and seasonality_display_rules: the "No Data Available" rules approved by the owner.
4. official_sources[]: site_url (website home), short_name, favicon (file in app/assets/sources/, downloaded by
   scripts/fetch_source_favicons.py; if missing, the logo of another source from the same organisation - logo_alias; null if none),
   publisher {it, en} and title {it, en} (config/source_display.json), also copied into the glossary sources.
5. icon in the vocabulary entries of the seasonal states and categories (Material Symbols names, the same
   as the app), with metadata.icon_set.
It also fixes the missing botanical family of almond (Prunus -> Rosaceae).
Usage:  python scripts/build_app_support_metadata.py   (after build_source_catalog.py, before title_case_labels.py)
"""
import urllib.parse

from common import DATA, ROOT, finalize_completeness, load_json, save_json

F = lambda la, it, en: {"latin": la, "it": it, "en": en}  # noqa: E731
FAMILIES = {f[0]: f for f in [
    ("Actinidiaceae", "Actinidiacee", "Kiwifruit Family"), ("Agaricaceae", "Agaricacee", "Agaric Family"),
    ("Amanitaceae", "Amanitacee", "Amanita Family"), ("Amaranthaceae", "Amarantacee", "Amaranth Family"),
    ("Amaryllidaceae", "Amarillidacee", "Amaryllis Family"), ("Anacardiaceae", "Anacardiacee", "Cashew Family"),
    ("Apiaceae", "Apiacee (Ombrellifere)", "Carrot Family"), ("Arecaceae", "Arecacee (Palme)", "Palm Family"),
    ("Asparagaceae", "Asparagacee", "Asparagus Family"), ("Asteraceae", "Asteracee (Composite)", "Daisy Family"),
    ("Betulaceae", "Betulacee", "Birch Family"), ("Boletaceae", "Boletacee", "Bolete Family"),
    ("Brassicaceae", "Brassicacee (Crucifere)", "Cabbage Family"), ("Bromeliaceae", "Bromeliacee", "Bromeliad Family"),
    ("Cactaceae", "Cactacee", "Cactus Family"), ("Caprifoliaceae", "Caprifogliacee", "Honeysuckle Family"),
    ("Caricaceae", "Caricacee", "Papaya Family"), ("Chenopodiaceae", "Chenopodiacee", "Goosefoot Family"),
    ("Convolvulaceae", "Convolvulacee", "Morning Glory Family"), ("Cucurbitaceae", "Cucurbitacee", "Gourd Family"),
    ("Ebenaceae", "Ebenacee", "Ebony Family"), ("Ericaceae", "Ericacee", "Heath Family"),
    ("Fabaceae", "Fabacee (Leguminose)", "Legume Family"), ("Fagaceae", "Fagacee", "Beech Family"),
    ("Grossulariaceae", "Grossulariacee", "Currant Family"), ("Hydnaceae", "Idnacee", "Tooth Fungus Family"),
    ("Iridaceae", "Iridacee", "Iris Family"), ("Juglandaceae", "Juglandacee", "Walnut Family"),
    ("Lamiaceae", "Lamiacee (Labiate)", "Mint Family"), ("Lauraceae", "Lauracee", "Laurel Family"),
    ("Lythraceae", "Litracee", "Loosestrife Family"), ("Malvaceae", "Malvacee", "Mallow Family"),
    ("Moraceae", "Moracee", "Mulberry Family"), ("Morchellaceae", "Morchellacee", "Morel Family"),
    ("Musaceae", "Musacee", "Banana Family"), ("Oleaceae", "Oleacee", "Olive Family"),
    ("Omphalotaceae", "Omfalotacee", "Omphalotus Family"), ("Passifloraceae", "Passifloracee", "Passionflower Family"),
    ("Pleurotaceae", "Pleurotacee", "Oyster Mushroom Family"), ("Poaceae", "Poacee (Graminacee)", "Grass Family"),
    ("Polygonaceae", "Poligonacee", "Knotweed Family"), ("Rhamnaceae", "Ramnacee", "Buckthorn Family"),
    ("Rosaceae", "Rosacee", "Rose Family"), ("Rutaceae", "Rutacee", "Rue Family"),
    ("Sapindaceae", "Sapindacee", "Soapberry Family"), ("Solanaceae", "Solanacee", "Nightshade Family"),
    ("Tuberaceae", "Tuberacee", "Truffle Family"), ("Viburnaceae", "Viburnacee", "Viburnum Family"),
    ("Vitaceae", "Vitacee", "Grape Family")]}
ISO = {"Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Croatia": "HR", "Cyprus": "CY", "Czech Republic": "CZ", "Denmark": "DK",
       "Estonia": "EE", "Finland": "FI", "France": "FR", "Germany": "DE", "Greece": "GR", "Hungary": "HU", "Ireland": "IE", "Italy": "IT",
       "Latvia": "LV", "Lithuania": "LT", "Luxembourg": "LU", "Malta": "MT", "Netherlands": "NL", "Poland": "PL", "Portugal": "PT",
       "Romania": "RO", "Slovakia": "SK", "Slovenia": "SI", "Spain": "ES", "Sweden": "SE", "Switzerland": "CH", "Turkey": "TR",
       "United Kingdom": "GB", "Norway": "NO", "Serbia": "RS"}
# colours and symbols of the EUFIC map (https://www.eufic.org/en/explore-seasonal-fruit-and-vegetables-in-europe), read from the
# owner's screenshot (2026-11-06); the Pannonian zone is not on the EUFIC map: soft terracotta and wheat ear, chosen by us
ZONE_COLOR = {"atlantic": "#3F5BA9", "boreal": "#12754A", "continental": "#5DBB8F", "mediterranean": "#F8AE1F",
              "mountain": "#9B5B9B", "pannonian": "#B86B4B"}
# regioni biogeografiche EEA 2016 (data/raw/eea_biogeo/, scripts/build_europe_map.py) -> zona dell'app
EEA_REGIONS = {"mountain": ["Alpine"], "atlantic": ["Atlantic"], "boreal": ["Boreal"], "continental": ["Continental", "BlackSea", "Steppic"],
               "mediterranean": ["Mediterranean", "Macaronesia", "Anatolian"], "pannonian": ["Pannonian"]}
EEA_APPROX = {"Macaronesia", "Anatolian", "BlackSea", "Steppic"}
ZONE_ICON = {"atlantic": "water_drop", "boreal": "fir_tree", "continental": "leaf", "mediterranean": "palm_tree",
             "mountain": "mountain", "pannonian": "wheat"}
SHORT = {"bda_ieo": "BDA-IEO", "crea": "CREA", "my_personaltrainer": "My-PersonalTrainer", "reg_1924_2006": "Reg. CE 1924/2006",
         "reg_1169_2011": "Reg. UE 1169/2011", "larn_sinu": "LARN SINU", "altroconsumo": "Altroconsumo", "greenpeace": "Greenpeace",
         "wwf": "WWF", "biosuisse": "Bio Suisse", "uc_davis": "UC Davis", "usda_hb66": "USDA HB66", "ortodacoltivare": "Orto da Coltivare",
         "ismea": "ISMEA", "regional": "Servizi Regionali", "eufic_map": "EUFIC", "eufic_national": "EUFIC", "eufic_article": "EUFIC",
         "eppo": "EPPO", "wfo": "WFO", "gbif": "GBIF", "eambrosia": "eAmbrosia", "wikimedia": "Wikimedia Commons",
         "usda_ars_images": "USDA ARS", "inaturalist": "iNaturalist", "usda_fdc": "USDA FDC", "usda_foodkeeper": "USDA FoodKeeper",
         "slow_food": "Slow Food", "unsplash": "Unsplash", "pixabay": "Pixabay", "usda_flavonoids": "USDA Flavonoidi",
         "phenol_explorer": "Phenol-Explorer", "eu_plant_variety_portal": "EU Plant Variety Portal", "ieo_smartfood_portions": "IEO SmartFood",
         "su_eatable_life": "SU-EATABLE LIFE", "masaf_pat": "MASAF PAT", "agribalyse": "AGRIBALYSE", "austria_gesundheitsportal": "Gesundheitsportal",
         "uc_davis_storing_guide": "UC Davis (Casa)", "iss_istisan_09_47": "ISS", "legge_752_1985": "Legge 752/1985",
         "provincia_cuneo_funghi": "Provincia di Cuneo", "bur_emilia_romagna_amarene": "BUR Emilia-Romagna",
         "biblioteca_bertoliana": "Biblioteca Bertoliana", "naturasi": "NaturaSì", "eea_biogeo": "EEA"}
STATE_ICON = {"primizie": "sprout", "in_season": "seedling", "peak_season": "plant_large", "end_of_season": "plant_drooping",
              "out_of_season": "remove", "not_applicable": "public"}       # set "Crescita" approvato dall'utente (2026-11-06)
CAT_ICON = {"frutta": "apple", "verdura": "grass", "erbe_spezie": "local_florist", "funghi": "forest", "cereali": "grain"}   # verdura...cereali: provvisorie
SVG = {"sprout": "primizie.svg", "seedling": "in_season.svg", "plant_large": "peak_season.svg", "plant_drooping": "end_of_season.svg",
       "apple": "apple.svg"}
EST_ICON = {"estimate": "≈", "not_grown": "public", "unknown": "question_mark"}


try:                                                  # dark logos (same rule as fetch_source_favicons.py)
    from fetch_source_favicons import dark_logos
    DARK = {f"{k}.png" for k in dark_logos()}
except ImportError:
    DARK = set()
DISPLAY = load_json(ROOT / "scripts" / "config" / "source_display.json")["sources"]   # editore, titolo, logo condiviso


def apply_ui_config_icons():
    """Icons chosen in the Admin Studio (data/ui_config.json, entries with target=database): they replace the ones above.
    Values: "svg:season/<file>" of the Growth set -> short name (sprout...), "svg:zones/<name>" -> name, "material:<name>" ->
    name; other SVGs stay "svg:<folder>/<name>"."""
    cfg = DATA / "ui_config.json"
    if not cfg.exists():
        return
    rev = {"svg:season/" + f[:-4]: k for k, f in SVG.items()}
    target = {"seasonality.state": STATE_ICON, "category": CAT_ICON, "seasonality.estimates": EST_ICON, "zone": ZONE_ICON}
    for sl in load_json(cfg).get("icon_slots", []):
        if sl.get("target") != "database" or not sl.get("icon"):
            continue
        grp, code = sl["slot"].rsplit(".", 1)
        ref = sl["icon"]
        val = rev.get(ref) or (ref.split(":", 1)[1] if ref.startswith("material:") else
                               ref.split("/", 1)[1] if grp == "zone" and ref.startswith("svg:zones/") else ref)
        if grp in target:
            target[grp][code] = val
REFERENCE_ORDER = ["italy_national", "mediterranean", "continental", "atlantic", "mountain", "pannonian", "boreal"]


def main():
    apply_ui_config_icons()
    db = load_json(DATA / "database.json")
    m = db["metadata"]
    for it in db["items"]:                              # famiglia mancante (mandorla)
        b = it["botany"]
        if not b.get("family") and (b.get("genus") == "Prunus" or b["scientific_name"].startswith("Prunus ")):
            b["family"], b["genus"] = "Rosaceae", "Prunus"
            finalize_completeness(it)
    voc = m.setdefault("vocabulary", {})
    used = sorted({it["botany"]["family"] for it in db["items"] if it["botany"].get("family")})
    missing = [f for f in used if f not in FAMILIES]
    voc["botany.family"] = {"_glossary": "scientific_name", **{f: F(*FAMILIES[f]) for f in used if f in FAMILIES}}
    for code, ico in STATE_ICON.items():
        if code in voc.get("seasonality.state", {}):
            voc["seasonality.state"][code]["icon"] = ico
    for code, ico in CAT_ICON.items():
        if code in voc.get("category", {}):
            voc["category"][code]["icon"] = ico
    for code, ico in EST_ICON.items():
        if code in voc.get("seasonality.estimates", {}):
            voc["seasonality.estimates"][code]["icon"] = ico
    m["icon_set"] = {
        "name": "Crescita (disegnato per Peak Season) + Material Symbols (Rounded)",
        "svg_dir": "app/assets/icons/season/", "svg_files": SVG, "svg_format": "viewBox 24, monocromatici",
        "material_url": "https://fonts.google.com/icons",
        "note": {"it": "Le icone del set \"Crescita\" (sprout, seedling, plant_large, plant_drooping, apple) sono SVG in svg_dir; le altre sono nomi "
                       "Material Symbols. out_of_season e not_applicable si disegnano come pallino pieno senza icona, unknown come pallino grigio "
                       "con \"?\"; \"≈\" è un simbolo di testo. Le icone di verdura, erbe, funghi e cereali sono provvisorie.",
                 "en": "Icons of the \"Crescita\" (Growth) set (sprout, seedling, plant_large, plant_drooping, apple) are SVG files in svg_dir; the "
                       "others are Material Symbols names. out_of_season and not_applicable are drawn as a solid dot without icon, unknown as a "
                       "grey dot with \"?\"; \"≈\" is a text symbol. Vegetable, herb, mushroom and grain icons are provisional."}}
    unknown_iso = set()
    for z, v in (m.get("eufic_climatic_zones_legend") or {}).items():
        if not isinstance(v, dict) or z.startswith("_"):
            continue
        for k in ("countries_primary", "countries_partial"):
            v[k + "_iso"] = [ISO[c] for c in v.get(k) or [] if c in ISO]
            unknown_iso |= {c for c in v.get(k) or [] if c not in ISO}
        v["color_hex"] = ZONE_COLOR.get(z)
        v["icon"] = ZONE_ICON.get(z)
        v["eea_regions"] = EEA_REGIONS.get(z, [])
        v["eea_regions_approx"] = [r for r in EEA_REGIONS.get(z, []) if r in EEA_APPROX]
        v["style_source"] = "eufic_map" if z != "pannonian" else "peak_season"
    m["eufic_climatic_zones_legend"]["_style"] = {
        "it": "Colori e simboli delle zone come nella mappa EUFIC (goccia atlantica, abete boreale, foglia continentale, palma mediterranea, "
              "montagna alpina). La zona pannonica non compare sulla mappa EUFIC: per l'app è stata scelta una terracotta tenue (#B86B4B) "
              "con una spiga, simbolo delle pianure cerealicole ungheresi, ben distinguibile dagli altri cinque colori.",
        "en": "Zone colours and symbols as on the EUFIC map (Atlantic drop, Boreal fir, Continental leaf, Mediterranean palm, Alpine mountain). "
              "The Pannonian zone is not on the EUFIC map: for the app a soft terracotta (#B86B4B) with an ear of wheat was chosen, a symbol of "
              "Hungary's grain plains, clearly distinct from the other five colours."}
    m["eufic_climatic_zones_legend"]["_eea_regions"] = {
        "it": "La mappa dell'app disegna le zone come regioni continue usando lo strato EEA \"Biogeographical regions, Europe 2016\" (Agenzia europea "
              "dell'ambiente, CC BY 4.0). Corrispondenza: Alpina -> alpina (mountain), Atlantica, Boreale, Continentale, Mediterranea e Pannonica -> "
              "zona omonima. Approssimazioni nostre, perché EUFIC non usa queste regioni: Macaronesia e Anatolica -> mediterranea; Mar Nero e Steppica "
              "-> continentale. La regione Artica è disegnata in grigio (#5B6670) con un fiocco, come su EUFIC, ma non è una zona dell'app.",
        "en": "The app map draws the zones as continuous regions using the EEA layer \"Biogeographical regions, Europe 2016\" (European Environment "
              "Agency, CC BY 4.0). Mapping: Alpine -> mountain, Atlantic, Boreal, Continental, Mediterranean and Pannonian -> the zone with the same "
              "name. Our own approximations, since EUFIC does not use these regions: Macaronesia and Anatolian -> Mediterranean; Black Sea and "
              "Steppic -> Continental. The Arctic region is drawn in grey (#5B6670) with a snowflake, as on EUFIC, but is not an app zone.",
        "arctic": {"color_hex": "#5B6670", "icon": "snowflake", "app_zone": None}}
    m["seasonality_reference_order"] = REFERENCE_ORDER
    m["seasonality_display_rules"] = {
        "it": "Se per la zona scelta un alimento non ha né dati né stima, l'app mostra \"Dati Non Disponibili\" (pallini grigi) e non lo indica mai "
              "come di stagione. Nel catalogo e nella ricerca l'alimento resta sempre visibile. Nelle liste del mese va in una sezione separata e "
              "chiusa, \"Senza Dati per Questa Zona (n)\", che non compare se è vuota; l'interruttore \"Includi Alimenti Senza Dati\" (spento di "
              "default) li riporta in fondo alla lista principale. Nella scheda dell'alimento compare un \"Calendario di Riferimento\" preso dalla "
              "prima zona con dati veri nell'ordine di seasonality_reference_order (prima l'Italia), con la nota \"Non è la tua zona: indicazione "
              "generale.\"; mai da una stima, e solo se la zona scelta non ha un dato o una stima ≈ attiva.",
        "en": "If a food has neither data nor an estimate for the chosen zone, the app shows \"No Data\" (grey dots) and never marks it as in season. "
              "In the catalogue and in search the food always stays visible. In monthly lists it goes into a separate, collapsed section, "
              "\"No Data for This Zone (n)\", which is hidden when empty; the \"Include Foods Without Data\" switch (off by default) puts them back "
              "at the end of the main list. The food page shows a \"Reference Calendar\" taken from the first zone with real data in "
              "seasonality_reference_order (Italy first), with the note \"Not your zone: general guidance.\"; never from an estimate, and only "
              "when the chosen zone has no data and no active ≈ estimate."}
    m["ethylene_rules"] = {
        "it": "Classe di produzione di etilene da USDA HB66 (µL/kg·h a 20 °C): <0,1 molto bassa, 0,1-1 bassa, 1-10 moderata, 10-100 alta, >100 "
              "molto alta; un valore \"<x\" è letto come x/2. produces_ethylene = classe almeno moderata. keep_away_from = solo i produttori con "
              "classe alta o superiore, per gli alimenti sensibili all'etilene. L'avviso \"incompatibilità nella spesa\" usa keep_away_from: "
              "segnala la coppia A-B quando B è nella lista di A.",
        "en": "Ethylene production class from USDA HB66 (µL/kg·h at 20 °C): <0.1 very low, 0.1-1 low, 1-10 moderate, 10-100 high, >100 very "
              "high; a value \"<x\" is read as x/2. produces_ethylene = class moderate or above. keep_away_from = only producers of high class "
              "or above, for ethylene-sensitive foods. The \"incompatibility in your shopping\" warning uses keep_away_from: it flags the pair "
              "A-B when B is in A's list."}
    fav_dir = ROOT / "app" / "assets" / "sources"
    for s in m.get("official_sources") or []:
        u = urllib.parse.urlparse(s.get("url") or "")
        s["site_url"] = f"{u.scheme}://{u.netloc}/" if u.netloc else None
        s["short_name"] = SHORT.get(s["key"], s.get("name", s["key"]).split(" - ")[0][:30])
        disp = DISPLAY.get(s["key"]) or {}
        own, alias = fav_dir / f"{s['key']}.png", disp.get("logo_alias")
        s["favicon"] = own.name if own.exists() else (f"{alias}.png" if alias and (fav_dir / f"{alias}.png").exists() else None)
        s["favicon_dark"] = s["favicon"] in DARK if s["favicon"] else None   # in the dark theme the app inverts the lightness
        s["publisher"] = disp.get("publisher") or {"it": s["short_name"], "en": s["short_name"]}
        s["title"] = disp.get("title") or {"it": s.get("name"), "en": s.get("name")}
    # Italian macro-areas: Abruzzo in the Centre by owner choice (2026-11-13), unlike the ISTAT grouping
    ima = m.setdefault("italy_macro_areas_legend", {})
    ima.update({
        "nord": {"it": "Nord Italia (Valle d'Aosta, Piemonte, Liguria, Lombardia, Trentino-Alto Adige, Veneto, Friuli-Venezia Giulia, Emilia-Romagna)",
                 "en": "Northern Italy (Aosta Valley, Piedmont, Liguria, Lombardy, Trentino-Alto Adige, Veneto, Friuli-Venezia Giulia, Emilia-Romagna)",
                 "regions": ["Valle d'Aosta", "Piemonte", "Liguria", "Lombardia", "Trentino-Alto Adige", "Veneto", "Friuli-Venezia Giulia", "Emilia-Romagna"]},
        "centro": {"it": "Centro Italia (Toscana, Umbria, Marche, Lazio, Abruzzo)",
                   "en": "Central Italy (Tuscany, Umbria, Marche, Lazio, Abruzzo)",
                   "regions": ["Toscana", "Umbria", "Marche", "Lazio", "Abruzzo"]},
        "sud_isole": {"it": "Sud e Isole (Molise, Campania, Puglia, Basilicata, Calabria, Sicilia, Sardegna)",
                      "en": "Southern Italy and Islands (Molise, Campania, Apulia, Basilicata, Calabria, Sicily, Sardinia)",
                      "regions": ["Molise", "Campania", "Puglia", "Basilicata", "Calabria", "Sicilia", "Sardegna"]},
        "_grouping": {
            "it": "Raggruppamento scelto per Peak Season: l'Abruzzo è nel Centro, mentre per l'ISTAT appartiene al Sud. Riguarda la legenda e le "
                  "mappe dell'app; i calendari non cambiano, perché le fonti (WWF, Greenpeace, Altroconsumo, EUFIC, Orto da Coltivare) danno già "
                  "i mesi per Nord, Centro e Sud secondo la propria suddivisione e nessun dato è ricavato da calendari regionali abruzzesi.",
            "en": "Grouping chosen for Peak Season: Abruzzo is in the Centre, while ISTAT places it in the South. It affects the app's legend and "
                  "maps; the calendars do not change, because the sources (WWF, Greenpeace, Altroconsumo, EUFIC, Orto da Coltivare) already give "
                  "the months for North, Centre and South by their own split, and no data comes from regional calendars of Abruzzo."}})
    # display rules of the product page (revision 2026-11-13: the app applies them, the database documents them)
    m["detail_display_rules"] = {
        "ripening": {
            "non_climacteric": {"hide": ["ripening_and_storage.ripening_management.speed_up"],
                                "move_to_storage": {"field": "ripening_and_storage.ripening_management.slow_down",
                                                    "label": {"it": "Per Conservarlo più a Lungo", "en": "To Keep It Longer"}}},
            "badge_behaviour_text": "help_only",
            "badge_help_glossary": ["climacteric", "non_climacteric"]},
        "storage_order": ["ripening_and_storage.home_storage.label", "ripening_and_storage.storage_instructions",
                          "ripening_and_storage.home_storage.tip", "ripening_and_storage.ethylene_compatibility.keep_away_from",
                          "ripening_and_storage.postharvest_physiology.estimated_shelf_life_days", "ripening_and_storage.perishability"],
        "footprint_filters": ["nutrition_and_sustainability.environmental_footprint.sustainability_rating.carbon_level",
                              "nutrition_and_sustainability.environmental_footprint.sustainability_rating.water_level"],
        "note": {
            "it": "Prodotti non climaterici: non si mostra \"come accelerare la maturazione\" (speed_up); il consiglio slow_down compare nella "
                  "parte di conservazione con l'etichetta \"Per Conservarlo più a Lungo\". Il testo del comportamento di maturazione non compare "
                  "sotto il badge (Climaterico / Non Climaterico) ma nell'aiuto \"?\" (glossario climacteric / non_climacteric). Ordine della "
                  "conservazione: dove conservarlo, istruzioni, consiglio, cosa tenere lontano, quanto dura in casa, deperibilità. Filtri della Home "
                  "per impronta di carbonio e idrica con i livelli e i colori di environmental_footprint_method.levels.",
            "en": "Non-climacteric produce: \"how to speed up ripening\" (speed_up) is not shown; the slow_down tip appears in the storage part "
                  "under the label \"To Keep It Longer\". The ripening behaviour text is not shown under the badge (Climacteric / Non-climacteric) "
                  "but in the \"?\" help (glossary climacteric / non_climacteric). Storage order: where to store it, instructions, tip, what to "
                  "keep away, how long it lasts at home, perishability. Home filters for carbon and water footprint use the levels and colours of "
                  "environmental_footprint_method.levels."}}
    efm = m.get("environmental_footprint_method")
    if isinstance(efm, dict):                         # sustainability_rating thresholds (enrich_footprint.py) and colours for the filters
        efm["levels"] = {
            "low": {"label": {"it": "Bassa", "en": "Low"}, "color_hex": "#2E7D32", "carbon_kg_co2eq_per_kg": [None, 0.5], "water_l_per_kg": [None, 500]},
            "medium": {"label": {"it": "Media", "en": "Medium"}, "color_hex": "#F9A825", "carbon_kg_co2eq_per_kg": [0.5, 1], "water_l_per_kg": [500, 1500]},
            "high": {"label": {"it": "Alta", "en": "High"}, "color_hex": "#C62828", "carbon_kg_co2eq_per_kg": [1, None], "water_l_per_kg": [1500, None]}}
    # sources of the help sheets (glossary.*.sources) and of other {key, name, url} lists: same fields as the box
    by_key = {s["key"]: s for s in m.get("official_sources") or []}

    def dress(o):
        if isinstance(o, dict):
            for v in o.values():
                dress(v)
        elif isinstance(o, list):
            for x in o:
                if isinstance(x, dict) and "url" in x and x.get("key") in by_key and "topics" not in x:
                    src = by_key[x["key"]]
                    x.update({"publisher": src["publisher"], "title": src["title"], "favicon": src["favicon"]})
                else:
                    dress(x)
    dress(m.get("glossary") or {})
    save_json(DATA / "database.json", db)
    print(f"famiglie: {len(used)} (senza nome: {missing}); paesi senza ISO: {sorted(unknown_iso)}; "
          f"fonti con favicon: {sum(1 for s in m['official_sources'] if s['favicon'])}/{len(m['official_sources'])}")


if __name__ == "__main__":
    main()
