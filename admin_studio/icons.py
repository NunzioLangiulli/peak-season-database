"""Scheda Icone dell'Admin Studio: quale icona usa l'app per ogni stato, categoria, zona ed elemento dell'interfaccia.

La mappa sta in data/ui_config.json (copia identica in app/assets/data/, letta dall'app):
    {"_meta": {...}, "icon_slots": [{"slot", "group", "description", "icon", "target"}]}
icon = "svg:<cartella>/<nome>" (file app/assets/icons/<cartella>/<nome>.svg, set disegnato per Peak Season) oppure
"material:<nome>" (Material Symbols Rounded, https://fonts.google.com/icons).
target = "database": l'icona è anche nel database ("il database prima dell'app") e build_app_support_metadata.py la
scrive in metadata.vocabulary / eufic_climatic_zones_legend; target = "app": la usa solo l'interfaccia.
Le voci dell'interfaccia sono definite dall'app (IconService.defaults): lo studio cambia solo il campo "icon", non
aggiunge, toglie o rinomina voci. Le icone Material proposte sono solo quelle di app/lib/theme/material_icon_names.dart.
"""
import json
import re
from datetime import date
from pathlib import Path

from common import DATA, ROOT, load_json, save_json

CONFIG = DATA / "ui_config.json"
ICONS = ROOT / "app" / "assets" / "icons"
SVG_DIRS = ("season", "ui", "zones", "italy")
MATERIAL = sorted(set("""eco spa grass local_florist forest grain apple nutrition restaurant kitchen soup_kitchen egg_alt bakery_dining
local_dining set_meal ramen_dining rice_bowl emoji_food_beverage park nature yard potted_plant compost agriculture energy_savings_leaf
water_drop opacity thermostat ac_unit severe_cold sunny light_mode dark_mode wb_sunny cloud partly_cloudy_day air mode_heat
calendar_month calendar_today event schedule hourglass_bottom hourglass_top timer history update today date_range
favorite favorite_border star star_border thumb_up thumb_down do_not_disturb_on block visibility visibility_off hide_source
shopping_cart shopping_basket shopping_bag add_shopping_cart remove_shopping_cart shopping_cart_checkout checklist playlist_add
playlist_add_check playlist_remove list receipt_long storefront local_grocery_store search search_off tune filter_list filter_alt
sort grid_view view_agenda view_list view_module apps settings info help question_mark public language map place explore
public_off sprout psychiatry nest_eco_leaf landscape terrain mountain_flag filter_hdr waves foggy kitchen_outline inventory_2
inventory storage door_front shelves countertops dining kebab_dining science biotech health_and_safety monitor_heart
fitness_center local_fire_department bolt recycling delete_outline delete_sweep remove add add_circle close check done
check_circle chevron_right expand_more expand_less unfold_more unfold_less open_in_new open_in_full more_vert drag_indicator
palette notifications notifications_active share bookmark bookmark_border label sell scale balance co2 water humidity_percentage
nutrition egg cookie icecream cake local_cafe wine_bar liquor emoji_nature pest_control bug_report hive pets flutter_dash""".split()))


def svg_path(rel):
    """Percorso di un SVG del catalogo (solo cartelle ammesse e nomi semplici)."""
    m = re.fullmatch(r"(season|ui|zones|italy)/([a-z0-9_]+)\.svg", rel)
    if not m:
        return None
    p = ICONS / m.group(1) / f"{m.group(2)}.svg"
    return p if p.exists() else None


APP_MATERIAL = ROOT / "app" / "lib" / "theme" / "material_icon_names.dart"   # nomi Material che l'app sa disegnare


def material_names():
    """Solo i nomi Material presenti nella mappa dell'app (righe  'nome': Icons.nome_rounded,): un nome fuori mappa
    non verrebbe disegnato e fa fallire il test ui_config_test. Per un'icona nuova serve una riga in quel file."""
    if not APP_MATERIAL.exists():
        return MATERIAL
    lines = [ln for ln in APP_MATERIAL.read_text(encoding="utf-8").splitlines() if not ln.lstrip().startswith("//")]
    return sorted(set(re.findall(r"'(\w+)': Icons\.", "\n".join(lines))))


def catalog():
    svg = [{"ref": f"svg:{d}/{p.stem}", "dir": d, "name": p.stem, "url": f"/icon/{d}/{p.stem}.svg"}
           for d in SVG_DIRS for p in sorted((ICONS / d).glob("*.svg"))]
    return {"svg": svg, "material": material_names(), "material_source": str(APP_MATERIAL.relative_to(ROOT))}


# ------------------------------------------------------------------ voci iniziali dal database
SVG_NAME = {"sprout": "svg:season/primizie", "seedling": "svg:season/in_season", "plant_large": "svg:season/peak_season",
            "plant_drooping": "svg:season/end_of_season", "apple": "svg:season/apple"}


def to_ref(name, zone=False):
    if not name or name in ("≈",):
        return None
    if name.startswith(("svg:", "material:")):
        return name
    if name in SVG_NAME:
        return SVG_NAME[name]
    if zone and (ICONS / "zones" / f"{name}.svg").exists():
        return f"svg:zones/{name}"
    return f"material:{name}"


def to_db(ref, zone=False):
    """Valore da scrivere nel database, nel formato che il database usa già (nomi brevi)."""
    rev = {v: k for k, v in SVG_NAME.items()}
    if ref in rev:
        return rev[ref]
    if ref.startswith("material:"):
        return ref.split(":", 1)[1]
    if zone and ref.startswith("svg:zones/"):
        return ref.split("/", 1)[1]
    return ref                                        # altri SVG: "svg:cartella/nome"


def defaults():
    db = load_json(DATA / "database.json")
    m = db["metadata"]
    voc = m.get("vocabulary") or {}
    slots = []
    lab = lambda v: v.get("it") if isinstance(v, dict) else str(v)  # noqa: E731
    for code, v in (voc.get("seasonality.state") or {}).items():
        if code.startswith("_") or not isinstance(v, dict):
            continue
        slots.append({"slot": f"seasonality.state.{code}", "group": "Stati stagionali (indicatore a 3 punti e calendario)",
                      "description": f"Stato \"{lab(v)}\"", "icon": to_ref(v.get("icon")), "target": "database"})
    for code, v in (voc.get("category") or {}).items():
        if code.startswith("_") or not isinstance(v, dict):
            continue
        slots.append({"slot": f"category.{code}", "group": "Categorie (filtri)", "description": f"Categoria \"{lab(v)}\"",
                      "icon": to_ref(v.get("icon")), "target": "database"})
    for code, v in (voc.get("seasonality.estimates") or {}).items():
        if code.startswith("_") or not isinstance(v, dict) or v.get("icon") in (None, "≈"):
            continue
        slots.append({"slot": f"seasonality.estimates.{code}", "group": "Stime e dati mancanti", "description": f"\"{lab(v)}\"",
                      "icon": to_ref(v.get("icon")), "target": "database"})
    for z, v in (m.get("eufic_climatic_zones_legend") or {}).items():
        if z.startswith("_") or not isinstance(v, dict):
            continue
        slots.append({"slot": f"zone.{z}", "group": "Zone climatiche (mappa e filtri)", "description": f"Zona {v.get('it')}",
                      "icon": to_ref(v.get("icon"), zone=True), "target": "database"})
    app = [("storage.frigorifero", "Conservazione", "Dove conservarlo: frigorifero", "svg:ui/fridge"),
           ("storage.temperatura_ambiente", "Conservazione", "Dove conservarlo: temperatura ambiente", "svg:ui/room_temp"),
           ("storage.dispensa", "Conservazione", "Dove conservarlo: dispensa", "svg:ui/pantry"),
           ("nav.home", "Barra di navigazione", "Scheda Home (non selezionata)", "material:eco"),
           ("nav.shopping", "Barra di navigazione", "Scheda Lista Spesa", "material:checklist"),
           ("nav.settings", "Barra di navigazione", "Scheda Impostazioni", "material:settings")]
    slots += [{"slot": s, "group": g, "description": d, "icon": i, "target": "app"} for s, g, d, i in app]
    return {"_meta": {"description": "Mappa delle icone dell'app, modificabile con l'Admin Studio (scheda Icone). icon = svg:<cartella>/<nome> "
                                     "(app/assets/icons) oppure material:<nome> (Material Symbols Rounded). target database = scritta anche nel "
                                     "database da build_app_support_metadata.py.", "updated": date.today().isoformat()},
            "icon_slots": slots}


def load():
    if CONFIG.exists():
        return load_json(CONFIG)
    cfg = defaults()
    save_json(CONFIG, cfg)
    return cfg


def payload():
    return {"config": load(), "catalog": catalog()}


def valid_ref(ref):
    if ref.startswith("svg:"):
        return svg_path(ref[4:] + ".svg") is not None
    return ref.startswith("material:") and ref.split(":", 1)[1] in material_names()


def save(data, run_script):
    cfg = load()
    by = {s["slot"]: s for s in cfg["icon_slots"]}
    for slot, ref in (data.get("changes") or {}).items():
        if slot not in by:
            raise ValueError(f"voce sconosciuta: {slot}")
        if not valid_ref(ref):
            raise ValueError(f"icona non valida: {ref}")
        by[slot]["icon"] = ref
    cfg["_meta"]["updated"] = date.today().isoformat()
    save_json(CONFIG, cfg)
    for script in ("build_app_support_metadata.py", "ux_terminology.py", "title_case_labels.py"):   # icone "database" scritte nel database
        rc, out = run_script(script)
        if rc != 0:
            raise RuntimeError(f"{script}: {out[-500:]}")


def overrides():
    """Per build_app_support_metadata.py: {gruppo: {codice: valore per il database}} dalle voci target=database."""
    if not CONFIG.exists():
        return {}
    out = {}
    for s in json.loads(Path(CONFIG).read_text(encoding="utf-8-sig")).get("icon_slots", []):
        if s.get("target") != "database" or not s.get("icon"):
            continue
        grp, code = s["slot"].rsplit(".", 1)
        out.setdefault(grp, {})[code] = to_db(s["icon"], zone=grp == "zone")
    return out
