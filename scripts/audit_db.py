"""Ricontrollo sistematico di ogni voce di ogni alimento (coerenza interna, coerenza con le fonti salvate, testi vs dati).

Scrive data/audit_findings.json: lista di {item, area, field, severity (E errore | W da controllare | I informativo), msg}.
Non modifica il database.
Uso:  python scripts/audit_db.py
"""
import json
import re
from collections import Counter

from common import DATA, ROOT, load_json, save_json
from enrich_nutrition import NRV, canon, claims

STATES = {"primizie", "in_season", "peak_season", "end_of_season", "out_of_season", "not_applicable"}
IN = {"primizie", "in_season", "peak_season", "end_of_season"}
CLS = ["very_low", "low", "moderate", "high", "very_high", "extremely_high"]
IMG = ROOT / "assets" / "images"
F = []


def add(it, area, field, sev, msg):
    F.append({"item": it["id"] if isinstance(it, dict) else it, "area": area, "field": field, "severity": sev, "msg": msg})


def bil(it, path, v, area):
    if v is None:
        return
    if isinstance(v.get("it"), list) or isinstance(v.get("en"), list):
        if len(v.get("it") or []) != len(v.get("en") or []):
            add(it, area, path, "E", "liste IT/EN di lunghezza diversa")
        return
    if not isinstance(v, dict) or not v.get("it") or not v.get("en"):
        add(it, area, path, "E", "testo bilingue incompleto")
        return
    for lang in ("it", "en"):
        t = v[lang]
        if re.search(r"\bNone\b|\{|\}|nan\b|\s{2,}|\.\.(?!\.)", t):
            add(it, area, f"{path}.{lang}", "W", f"testo sospetto: {t[:80]}")
    if v["it"] == v["en"] and len(v["it"]) > 12 and re.search(r"(?i)\b(il|la|di|con|per|non|della|sono|è)\b", v["it"]):
        add(it, area, path, "W", "testo IT identico a EN")


def walk_bil(it, o, path, area):
    if isinstance(o, dict):
        if set(o) == {"it", "en"}:
            bil(it, path, o, area)
            return
        for k, v in o.items():
            walk_bil(it, v, f"{path}.{k}", area)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk_bil(it, v, f"{path}[{i}]", area)


def check_nutrition(it):
    n = it["nutrition_and_sustainability"]
    m = n["macros_per_100g"]
    A = "nutrizione"
    if n["kcal_per_100g"] is None:
        declared = "non disponibili" in ((n.get("data_basis") or {}).get("it") or "")
        add(it, A, "kcal_per_100g", "I" if declared else "E", "nutrizione non disponibile da fonti ufficiali (dichiarato)" if declared else "kcal mancanti")
        return
    p, c, f, fib = (m.get(k) or 0 for k in ("proteins_g", "carbs_g", "fats_g", "fiber_g"))
    est = 4 * p + 3.75 * c + 9 * f + 2 * fib
    if n["kcal_per_100g"] > 8 and abs(est - n["kcal_per_100g"]) / n["kcal_per_100g"] > 0.25 and abs(est - n["kcal_per_100g"]) > 8:
        add(it, A, "kcal_per_100g", "W", f"kcal dichiarate {n['kcal_per_100g']} vs stimate da macro {est:.0f} (4p+3,75c+9g+2fibra)")
    if n.get("kj_per_100g") and abs(n["kj_per_100g"] / 4.184 - n["kcal_per_100g"]) > max(3, 0.06 * n["kcal_per_100g"]):
        add(it, A, "kj_per_100g", "W", f"kJ {n['kj_per_100g']} incoerenti con kcal {n['kcal_per_100g']}")
    tot = (n.get("water_percentage") or 0) + p + c + f + fib
    if n.get("water_percentage") and tot > 105:
        add(it, A, "macros_per_100g", "W", f"acqua+macro = {tot:.1f} g/100 g")
    if m.get("sugars_g") and m.get("carbs_g") is not None and m["sugars_g"] > m["carbs_g"] + 0.2:
        add(it, A, "macros_per_100g.sugars_g", "E", f"zuccheri {m['sugars_g']} > carboidrati {m['carbs_g']}")
    if m.get("starch_g") and m.get("sugars_g") is not None and m.get("carbs_g") is not None and m["starch_g"] + m["sugars_g"] > m["carbs_g"] * 1.15 + 0.3:
        add(it, A, "macros_per_100g", "W", f"amido+zuccheri {m['starch_g']+m['sugars_g']:.1f} > carboidrati {m['carbs_g']}")
    ep = n.get("edible_portion_percentage")
    if ep is not None and not (5 <= ep <= 100):
        add(it, A, "edible_portion_percentage", "E", f"parte edibile {ep}%")
    vals = {"kcal": n["kcal_per_100g"], "fat": m.get("fats_g"), "sugars": m.get("sugars_g"), "fiber": m.get("fiber_g"), "protein": m.get("proteins_g")}
    for x in n["vitamins"] + n["minerals"]:
        k = canon(x["name"]) or {"vitamina a (retinolo eq.)": "vit_a"}.get(x["name"].lower())
        if k:
            vals[k] = x["amount"]
            ref = NRV.get(k)
            if ref and x.get("percent_nrv") is not None and abs(x["amount"] / ref[0] * 100 - x["percent_nrv"]) > 0.6:
                add(it, A, f"{x['name']}.percent_nrv", "E", f"%VNR {x['percent_nrv']} ≠ {x['amount']/ref[0]*100:.1f}")
            if ref and x["unit"] != ref[1]:
                add(it, A, f"{x['name']}.unit", "E", f"unità {x['unit']} diversa dal VNR ({ref[1]})")
    if "sodium" not in vals and m.get("salt_g") is not None:   # sodio non elencato (valore 0 nella fonte): dal sale
        vals["sodium"] = m["salt_g"] * 1000 / 2.5
    if "salt_g" in m and m.get("salt_g") is not None:
        sod = next((x["amount"] for x in n["minerals"] if canon(x["name"]) == "sodium"), None)
        if sod is not None and abs(sod * 2.5 / 1000 - m["salt_g"]) > 0.01:
            add(it, A, "macros_per_100g.salt_g", "E", f"sale {m['salt_g']} ≠ sodio×2,5 ({sod*2.5/1000:.3f})")
    exp = claims(vals)["it"]
    got = (n.get("nutrition_claims_eu") or {}).get("it", [])
    if sorted(x.lower() for x in exp) != sorted(x.lower() for x in got):   # le etichette hanno le iniziali maiuscole
        add(it, A, "nutrition_claims_eu", "E", f"claim non ricalcolabili: attesi {sorted(set(exp)-set(got))} / in più {sorted(set(got)-set(exp))}")
    en = (n.get("nutrition_claims_eu") or {}).get("en", [])
    if len(en) != len(got):
        add(it, A, "nutrition_claims_eu.en", "E", "claim IT/EN di numero diverso")
    rp = n.get("reference_portion") or {}
    if rp.get("grams") and rp.get("kcal") is not None and abs(rp["kcal"] - n["kcal_per_100g"] * rp["grams"] / 100) > 1:
        add(it, A, "reference_portion.kcal", "E", "kcal per porzione incoerenti")
    pr = n.get("protein_reference")
    if pr and m.get("proteins_g") is not None and abs(pr["protein_g_per_100g"] - m["proteins_g"]) > 0.01:
        add(it, A, "protein_reference", "E", "proteine del riferimento LARN diverse dalle macro")
    ef = n.get("environmental_footprint") or {}
    if ef.get("carbon_kg_co2eq_per_kg") and rp.get("grams") and ef.get("carbon_g_co2eq_per_portion") is not None:
        if abs(ef["carbon_kg_co2eq_per_kg"] * rp["grams"] - ef["carbon_g_co2eq_per_portion"]) > 2:
            add(it, "sostenibilita", "carbon_g_co2eq_per_portion", "E", "CO2 per porzione incoerente")
    for b in n.get("bioactive_compounds") or []:
        if not b.get("source"):
            add(it, A, "bioactive_compounds", "E", f"composto senza fonte: {b['name']}")
    cat = it["category"]
    gl = {"grano_duro_durum_wheat", "farro_emmer", "orzo_barley", "avena_oat"}
    has1 = any(a["annex_ii_number"] == 1 for a in n.get("allergens_eu", []))
    if (it["id"] in gl) != has1:
        add(it, "allergeni", "allergens_eu", "E", "allergene glutine incoerente")
    if cat == "cereali" and it["id"] not in gl and it["id"] not in ("riso_rice", "grano_saraceno_buckwheat", "mais_corn"):
        add(it, "allergeni", "allergens_eu", "W", "cereale non classificato")


def check_season(it):
    s = it["seasonality"]
    A = "stagionalita"
    for grp in ("eufic_climatic_zones", "italy_macro_areas"):
        for z, arr in (s.get(grp) or {}).items():
            if not arr:
                continue
            if len(arr) != 12:
                add(it, A, f"{grp}.{z}", "E", f"{len(arr)} mesi invece di 12")
            bad = set(arr) - STATES
            if bad:
                add(it, A, f"{grp}.{z}", "E", f"stati non validi {bad}")
            if arr and all(x == "out_of_season" for x in arr):
                add(it, A, f"{grp}.{z}", "W", "sempre fuori stagione")
            if "peak_season" in arr and not any(x in ("in_season", "peak_season") for x in arr):
                add(it, A, f"{grp}.{z}", "W", "picco senza stagione")
    cal = it["agricultural_calendar_italy"]
    for z in ("nord", "centro", "sud_isole"):
        zc = cal.get(z) or {}
        for k in ("sowing_or_transplant_months", "harvest_months"):
            v = zc.get(k)
            if v and (any(not (1 <= x <= 12) for x in v) or len(set(v)) != len(v)):
                add(it, "calendario", f"{z}.{k}", "E", f"mesi non validi {v}")
        h = zc.get("harvest_months")
        arr = (s.get("italy_macro_areas") or {}).get(z)
        if h and arr and len(arr) == 12:
            ins = {i + 1 for i, x in enumerate(arr) if x in IN}
            if ins and not (set(h) & ins):
                add(it, "calendario", f"{z}.harvest_months", "W", f"raccolta {h} mai in stagione {sorted(ins)}")
            elif ins and len(set(h) & ins) < 0.5 * len(set(h)) and it["category"] != "erbe_spezie":
                add(it, "calendario", f"{z}.harvest_months", "I", f"raccolta {h} poco sovrapposta alla stagionalità {sorted(ins)}")


def check_storage(it, ids, producers):
    r = it["ripening_and_storage"]
    ph, ec = r["postharvest_physiology"], r["ethylene_compatibility"]
    sl, ci = ph["estimated_shelf_life_days"], ph["chilling_injury"]
    A = "conservazione"
    dc = it["data_completeness"]
    na = set(dc.get("not_applicable_fields", []))
    ot = ph.get("optimal_temperature_c")
    rh = ph.get("optimal_humidity_percent")
    for nm, rg in (("optimal_temperature_c", ot), ("optimal_humidity_percent", rh)):
        if rg and rg["min"] > rg["max"]:
            add(it, A, nm, "E", f"min>max {rg}")
    if rh and not (40 <= rh["min"] <= 100 and rh["max"] <= 100):
        add(it, A, "optimal_humidity_percent", "E", f"umidità fuori scala {rh}")
    if ci.get("susceptible") is True:
        ct = ci.get("critical_temperature_c")
        if ct is not None and ct <= 0:
            add(it, A, "chilling_injury.critical_temperature_c", "E", f"sensibile al freddo con soglia {ct} °C (è un punto di congelamento?)")
        lsr = ci.get("lowest_safe_range_c")
        if ct is not None and ot and ot["min"] < ct - 0.5:
            if lsr and ot["min"] >= lsr["min"] - 0.5:
                add(it, A, "chilling_injury", "I", f"soglia {ct} °C = massimo dell'intervallo minimo sicuro {lsr}; ottimale {ot}")
            else:
                add(it, A, "chilling_injury", "W", f"temperatura ottimale {ot} sotto la soglia di danno {ct} °C")
        if not ci.get("symptoms"):
            add(it, A, "chilling_injury.symptoms", "W", "sensibile ma senza sintomi")
    if ci.get("susceptible") is False and ci.get("critical_temperature_c") is not None:
        add(it, A, "chilling_injury.critical_temperature_c", "E", "non sensibile ma con soglia di danno")
    for k in ("room_temp_days", "refrigerated_days", "commercial_optimal_days"):
        v = sl.get(k)
        if v and v[0] > v[1]:
            add(it, A, k, "E", f"intervallo invertito {v}")
    mode = sl.get("room_temp_mode")
    if mode == "fridge_only" and sl.get("room_temp_days"):
        add(it, A, "room_temp_days", "E", "solo frigo ma con giorni a temperatura ambiente")
    if sl.get("refrigerated_days") and sl.get("commercial_optimal_days") and sl["refrigerated_days"][1] > 3 * sl["commercial_optimal_days"][1] and sl["commercial_optimal_days"][1] < 300:
        add(it, A, "refrigerated_days", "W", f"durata in frigo {sl['refrigerated_days']} molto superiore a quella professionale {sl['commercial_optimal_days']}")
    if sl.get("in_freezer_months") is not None and sl.get("freezing_recommended") is False:
        add(it, A, "in_freezer_months", "E", "congelamento sconsigliato ma mesi indicati")
    hs = r.get("home_storage") or {}
    loc, prim = hs.get("location"), r.get("primary_location")
    expect = {"fridge": {"frigorifero"}, "counter_then_fridge": None, "room_temperature": {"temperatura_ambiente", "luogo_fresco_buio"},
              "cool_dry_pantry": {"luogo_fresco_buio", "temperatura_ambiente"}}
    if loc and expect.get(loc) and prim and prim not in expect[loc]:
        add(it, "testi", "primary_location", "W", f"primary_location '{prim}' vs consiglio casa '{loc}'")
    cs = (r.get("card_short_storage") or {}).get("it", "")
    if loc == "fridge" and re.search(r"(?i)^\s*(ambiente|dispensa)", cs):
        add(it, "testi", "card_short_storage", "W", f"etichetta '{cs}' ma consiglio = frigorifero")
    if loc in ("room_temperature", "cool_dry_pantry") and re.match(r"(?i)\s*frigo", cs):
        add(it, "testi", "card_short_storage", "W", f"etichetta '{cs}' ma consiglio = {loc}")
    m = re.search(r"(\d+)\s*-\s*(\d+)\s*(giorni|gg)", cs) or re.search(r"(\d+)()\s*(giorni|gg)", cs)
    rd = sl.get("refrigerated_days")
    if m and "frigo" in cs.lower() and rd:
        a = int(m.group(1)); b = int(m.group(2) or a)
        if b < rd[0] * 0.5 or a > rd[1] * 1.6:
            add(it, "testi", "card_short_storage", "W", f"'{cs}' vs FoodKeeper frigo {rd} giorni")
    si = (r.get("storage_instructions") or {}).get("it", "")
    ms = re.search(r"(?i)frigo\w*[^.]{0,60}?(?:per|fino a|entro|al massimo)\s+(\d+)(?:\s*-\s*(\d+))?\s*(giorn|settiman)", si)
    if ms and rd and sl.get("room_temp_mode") != "until_ripe":
        a = int(ms.group(1)) * (7 if ms.group(3).startswith("settiman") else 1)
        b = int(ms.group(2) or ms.group(1)) * (7 if ms.group(3).startswith("settiman") else 1)
        if b < rd[0] * 0.5 or a > rd[1] * 1.6:
            add(it, "testi", "storage_instructions", "I", f"il testo cita {a}-{b} giorni in frigo, FoodKeeper {rd}")
    ct = ci.get("critical_temperature_c")
    if ci.get("susceptible") is False and re.search(r"(?i)danni? da freddo sotto|sotto i \d+ ?°C (si )?danneggi", si):
        add(it, "testi", "storage_instructions", "W", "il testo parla di danni da freddo ma il prodotto non è sensibile")
    # etilene
    pc = ec.get("ethylene_production_class")
    if pc in ("high", "very_high", "extremely_high") and ec.get("produces_ethylene") is False:
        add(it, "etilene", "produces_ethylene", "E", f"classe {pc} ma produces_ethylene=false")
    if pc in ("very_low",) and ec.get("produces_ethylene") is True:
        add(it, "etilene", "produces_ethylene", "W", "classe very_low ma produces_ethylene=true")
    if ec.get("sensitive_to_ethylene") is True and not ec.get("keep_away_from"):
        add(it, "etilene", "keep_away_from", "W", "sensibile ma lista vuota")
    for x in ec.get("keep_away_from") or []:
        if x not in ids:
            add(it, "etilene", "keep_away_from", "E", f"id inesistente {x}")
        if x not in producers:
            add(it, "etilene", "keep_away_from", "E", f"{x} non è un forte produttore")
    cn = (ec.get("compatibility_notes") or {}).get("it", "")
    if ec.get("sensitive_to_ethylene") is False and "sensibile all'etilene:" in cn:
        add(it, "testi", "compatibility_notes", "E", "testo dice sensibile, dato dice no")
    # respirazione
    rc, pe = ph.get("respiration_rate_class"), r.get("perishability")
    if rc and pe and pe.get("level") != CLS.index(rc) + 1:
        add(it, A, "perishability", "E", "livello di deperibilità diverso dalla classe di respirazione")
    sc = r.get("storage_compatibility") or {}
    if sc and ot:
        g = sc["group"]
        if g in ("1A", "1B") and ot["min"] >= 7:
            add(it, A, "storage_compatibility", "W", f"gruppo {g} (0-2 °C) ma temperatura ottimale {ot}")
        if g == "3" and ot["max"] < 7:
            add(it, A, "storage_compatibility", "W", f"gruppo 3 (13-18 °C) ma temperatura ottimale {ot}")
        if g == "2" and ot["max"] < 4:
            add(it, A, "storage_compatibility", "W", f"gruppo 2 (7-10 °C) ma temperatura ottimale {ot}")
    if sc and ci.get("susceptible") is True and sc["group"] in ("1A", "1B") and (ct or 0) >= 5:
        add(it, A, "storage_compatibility", "W", f"gruppo {sc['group']} a 0-2 °C ma sensibile al freddo sotto {ct} °C")
    for x in sc.get("compatible_with", []):
        if x not in ids:
            add(it, A, "storage_compatibility", "E", f"id inesistente {x}")
    if r.get("ripening_type") == "non_climaterico" and ec.get("ethylene_production_class") in ("high", "very_high"):
        add(it, "etilene", "ripening_type", "W", "non climaterico ma forte produttore di etilene")


def check_botany(it):
    b = it["botany"]
    A = "botanica"
    sn = b.get("scientific_name") or ""
    if b.get("genus") and not sn.startswith(b["genus"]):
        add(it, A, "genus", "E", f"genere {b['genus']} ≠ nome scientifico {sn}")
    up = b.get("upov_name") or ""
    if up and b.get("genus") and not up.startswith(b["genus"]):
        add(it, A, "upov_name", "W", f"specie UPOV {up} di genere diverso da {b['genus']}")
    iv = it["italian_varieties_and_territories"]
    names = {v["name"] for v in iv.get("varieties_verification") or []}
    for v in iv.get("notable_varieties") or []:
        if v not in names:
            add(it, "varieta", "notable_varieties", "E", f"varietà senza verifica: {v}")
    shown = set(iv.get("notable_varieties") or [])
    for v in iv.get("varieties_verification") or []:
        if v["name"] in shown and (not v.get("verified") or not v.get("sources")):
            add(it, "varieta", "varieties_verification", "E", f"varietà mostrata ma non verificata: {v['name']}")
    if iv.get("has_dop_igp") and not iv.get("dop_igp_labels"):
        add(it, "varieta", "dop_igp_labels", "E", "has_dop_igp true senza etichette")
    if iv.get("dop_igp_labels") and not iv.get("has_dop_igp"):
        add(it, "varieta", "has_dop_igp", "E", "etichette DOP/IGP ma has_dop_igp false")


def check_images(it):
    im = it["images"]
    A = "immagini"
    for f in im.get("gallery") or []:
        if not (IMG / f).exists():
            add(it, A, "gallery", "E", f"file mancante {f}")
    det = {d["filename"]: d for d in im.get("image_details") or []}
    for f in im.get("gallery") or []:
        d = det.get(f)
        if not d or not d.get("license") or not d.get("source_url") or not d.get("author"):
            add(it, A, "image_details", "E", f"metadati licenza incompleti per {f}")
    if im.get("primary") and im["primary"] not in (im.get("gallery") or []):
        add(it, A, "primary", "E", "primaria non in galleria")


def check_sources(it):
    s = it["sources_by_topic"]
    A = "fonti"
    used = s.get("sources_used") or []
    if len(used) < 5:
        add(it, A, "sources_used", "W", f"solo {len(used)} fonti")
    urls = [u for x in used for u in x.get("urls", [])] + [l["url"] for l in s.get("useful_links") or []]
    for u in urls:
        if u and not re.match(r"^https?://", u):
            add(it, A, "urls", "E", f"URL non valido {u}")
    if not s.get("useful_links"):
        add(it, A, "useful_links", "W", "nessun link utile")


def check_meta(db):
    m = db["metadata"]
    gl, voc, fh = m.get("glossary", {}), m.get("vocabulary", {}), m.get("field_help", {})
    srcs = {s["key"]: s for s in m["official_sources"]}
    for gid, g in gl.items():
        for k in ("term", "short", "text"):
            if not (g.get(k) or {}).get("it") or not (g.get(k) or {}).get("en"):
                add("*", "glossario", gid, "E", f"{k} non bilingue")
        for s in g["sources"]:
            if s["key"] not in srcs:
                add("*", "glossario", gid, "E", f"fonte {s['key']} non registrata")
        for x in g.get("see_also", []):
            if x not in gl:
                add("*", "glossario", gid, "E", f"see_also inesistente {x}")
    for path, ids in fh.items():
        if get(db["items"][0], path) is None and not any(get(i, path) is not None for i in db["items"]):
            add("*", "glossario", path, "W", "campo con aiuto inesistente nelle schede")
        for g in ids:
            if g not in gl:
                add("*", "glossario", path, "E", f"voce {g} inesistente")
    for s in m["official_sources"]:
        for k in ("description", "authority", "offers"):
            if not isinstance(s.get(k), dict):
                add("*", "fonti", s["key"], "E", f"{k} mancante")
    checks = {"category": ["category"], "botany.plant_part_used": ["botany.plant_part_used"],
              "ripening_and_storage.ripening_type": ["ripening_and_storage.ripening_type"],
              "ripening_and_storage.primary_location": ["ripening_and_storage.primary_location"],
              "ripening_and_storage.home_storage.location": ["ripening_and_storage.home_storage.location"],
              "class_scale": ["ripening_and_storage.postharvest_physiology.respiration_rate_class", "ripening_and_storage.ethylene_compatibility.ethylene_production_class"],
              "ripening_and_storage.storage_compatibility.group": ["ripening_and_storage.storage_compatibility.group"],
              "agricultural_calendar_italy.agronomic_params.sun_exposure": ["agricultural_calendar_italy.agronomic_params.sun_exposure"],
              "agricultural_calendar_italy.agronomic_params.lunar_phase_advice": ["agricultural_calendar_italy.agronomic_params.lunar_phase_advice"]}
    for vk, paths in checks.items():
        for it in db["items"]:
            for p in paths:
                v = get(it, p)
                if v is not None and str(v) not in voc.get(vk, {}):
                    add(it, "vocabolario", p, "E", f"valore '{v}' senza etichetta IT/EN")
    for it in db["items"]:
        for h in it.get("help_refs", []):
            if h["glossary_id"] not in gl:
                add(it, "glossario", "help_refs", "E", f"voce {h['glossary_id']} inesistente")
        for zone in (it["seasonality"].get("eufic_climatic_zones") or {}).values():
            for st in zone or []:
                if st not in voc.get("seasonality.state", {}):
                    add(it, "vocabolario", "seasonality", "E", f"stato {st} senza etichetta")


def get(o, path):
    for k in path.split("."):
        o = o.get(k) if isinstance(o, dict) else None
    return o


def main():
    db = load_json(DATA / "database.json")
    ids = {it["id"] for it in db["items"]}
    producers = {i["id"] for i in db["items"] if i["ripening_and_storage"]["ethylene_compatibility"].get("ethylene_production_class") in ("high", "very_high")}
    names = Counter(it["names"]["it"].lower() for it in db["items"])
    for nm, c in names.items():
        if c > 1:
            add("*", "nomi", "names.it", "E", f"nome IT duplicato: {nm}")
    check_meta(db)
    for it in db["items"]:
        check_nutrition(it)
        check_season(it)
        check_storage(it, ids, producers)
        check_botany(it)
        check_images(it)
        check_sources(it)
        walk_bil(it, {k: it[k] for k in ("buying_guide", "ripening_and_storage", "nutrition_and_sustainability", "agricultural_calendar_italy")}, "", "testi")
        dc = it["data_completeness"]
        for p in set(dc.get("missing_fields", [])) & set(dc.get("not_applicable_fields", [])):
            add(it, "completezza", p, "E", "campo sia mancante sia non pertinente")
    save_json(DATA / "audit_findings.json", F)
    c = Counter((f["severity"], f["area"]) for f in F)
    print(f"totale segnalazioni: {len(F)}")
    for (sv, ar), k in sorted(c.items()):
        print(f"  {sv} {ar:14} {k}")


if __name__ == "__main__":
    main()
