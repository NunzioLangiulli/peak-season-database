"""Step 1.3c - Seasonality (EUFIC, WWF, Greenpeace, Altroconsumo, ODC) and agronomic calendar (ODC).

Merging method (also documented in metadata and in the report):
- for each month a score s = votes / available sources is computed:
    vote 1   = the source marks the month "in season" (WWF, Greenpeace, Altroconsumo, EUFIC-Italy, ODC harvest)
    vote 0.5 = the source marks it "early/late" (WWF, Altroconsumo)
- s >= 0.5 -> in_season ; 0 < s < 0.5 -> primizie (if it precedes a seasonal period) or end_of_season (if it follows it);
  s = 0 -> out_of_season; explicit early/late indications from the sources take precedence;
- peak_season = inner months (neither the first nor the last) of a run of at least 3 months on which ALL available
  sources (at least 2) agree;
- exotic fruit without any Italian production source (ODC, EUFIC-Italy, WWF, Greenpeace) -> not_applicable;
- no source -> null (missing field).
- EUFIC by zone: share of the zone's countries (prevailing EEA region) that report the product as in season;
  "(stored)" data = local stored product -> end_of_season.

Usage:  python scripts/enrich_seasonality.py
"""
import html
import re

from common import (CONFIG, DATA, RAW, add_discrepancy, finalize_completeness, http_get, iter_blocks, load_json,
                    mark_enriched, save_json)

MONTHS_IT = ["GEN", "FEB", "MAR", "APR", "MAG", "GIU", "LUG", "AGO", "SET", "OTT", "NOV", "DIC"]
MONTHS_GP = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO", "SETTEMBRE",
             "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
             "November", "December"]
ZONES = ["mediterranean", "continental", "atlantic", "boreal", "mountain", "pannonian"]
EXOTIC_IF_NO_LOCAL = {"banana_banana", "ananas_pineapple", "papaya_papaya", "maracuja_passion_fruit", "avocado_avocado",
                      "mango_mango", "litchi_lychee", "lime_lime"}


def altroconsumo_page(url):
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    p = RAW / "altroconsumo" / f"{slug}.json"
    if p.exists():
        return load_json(p)
    h = http_get(url).text
    months = {}
    i = h.find("greengrocery-calendar__table")
    for cls, m in re.findall(r'<td class="greengrocery-calendar__table__(\w+)">\s*<span[^>]*>\s*(\w+)', h[i:i + 10000]):
        if m in MONTHS_IT:
            months[MONTHS_IT.index(m) + 1] = {"season": "in_season", "early": "early", "late": "late"}.get(cls, cls)
    info = {}
    for label in ("Benefici", "Come scegliere", "Come conservare"):
        m = re.search(re.escape(label) + r"\s*<strong>\s*<p>(.*?)</p>", h, re.S)
        info[label] = html.unescape(re.sub("<.*?>", "", m.group(1))).strip() if m else None
    desc = re.search(r'<meta name="description" content="([^"]*)"', h)
    out = {"url": url, "months": months, "info": info, "description": html.unescape(desc.group(1)) if desc else None}
    save_json(p, out)
    return out


def states(score, hints, n_sources):
    """score: 12 floats (None = no source); hints: 12 of None|'early'|'late'|'stored'."""
    if n_sources == 0:
        return None
    st = []
    for m in range(12):
        s, h = score[m], hints[m]
        if h == "early":
            st.append("primizie")
        elif h == "late":
            st.append("end_of_season")
        elif s >= 0.5:
            st.append("in_season")
        elif s > 0:
            st.append("?")
        elif h == "stored":
            st.append("end_of_season")
        else:
            st.append("out_of_season")
    for m in range(12):
        if st[m] == "?":
            nxt = st[(m + 1) % 12] in ("in_season", "primizie")
            st[m] = "primizie" if nxt else "end_of_season"
    # peak: inner months of a block >= 3 months with full agreement and >= 2 sources
    if n_sources >= 2:
        full = [score[m] >= 0.999 for m in range(12)]
        if not all(full):
            for m in range(12):
                if full[m] and full[(m - 1) % 12] and full[(m + 1) % 12] and st[m] == "in_season":
                    st[m] = "peak_season"
    return st


def italy_votes(src, wwf, gp, altro, eufic_it):
    """Restituisce (voti[12], hint[12], fonti usate)."""
    votes = [0.0] * 12; hints = [None] * 12; used = []
    if src.get("wwf_row") and src["wwf_row"] in wwf:
        used.append("WWF")
        for m, s in wwf[src["wwf_row"]]["months"].items():
            m = int(m) - 1
            votes[m] += 1 if s == "in_season" else 0.5
            if s != "in_season":
                hints[m] = "edge"
    if src.get("greenpeace_name"):
        key = next((k for k in gp if k.split(":", 1)[1] == src["greenpeace_name"]), None)
        if key:
            used.append("Greenpeace")
            for mm in gp[key]:
                votes[MONTHS_GP.index(mm)] += 1
    if altro and altro["months"]:
        used.append("Altroconsumo")
        for m, s in altro["months"].items():
            m = int(m) - 1
            votes[m] += 1 if s == "in_season" else 0.5
            if s in ("early", "late"):
                hints[m] = s
    if eufic_it:
        used.append("EUFIC (Italia)")
        for m in range(12):
            votes[m] += 1 if eufic_it[m] else 0
    return votes, hints, used


def resolve_edges(votes, hints, n):
    score = [v / n for v in votes] if n else [0] * 12
    h2 = []
    for m in range(12):
        h = hints[m]
        if h == "edge":   # WWF "primizie/tardive": decide dalla posizione rispetto al periodo pieno
            nxt = score[(m + 1) % 12] >= 0.5
            prv = score[(m - 1) % 12] >= 0.5
            h = "early" if nxt and not prv else ("late" if prv and not nxt else None)
        h2.append(h)
    return score, h2


def eufic_country_table(keys, eufic):
    fresh, stored = {}, {}
    for k in keys:
        cat = "Fruit" if k in eufic["Fruit"] else "Vegetable"
        tgt = stored if "(stored)" in k else fresh
        for month, country in eufic[cat][k]:
            c, mo = country.strip(), month.strip().capitalize()
            if mo not in MONTHS_EN:          # valori anomali nei dati EUFIC (es. refusi): ignorati
                continue
            tgt.setdefault(c, [False] * 12)[MONTHS_EN.index(mo)] = True
    return fresh, stored


def main():
    db = load_json(DATA / "database.json")
    idx = {i["id"]: i for i in load_json(DATA / "items_index.json")["items"]}
    eufic = load_json(RAW / "eufic_fvlist.json")
    zmap = load_json(CONFIG / "eufic_zone_map.json")["countries"]
    wwf = load_json(RAW / "wwf_calendar.json")["rows"]
    gp = load_json(RAW / "greenpeace_months.json")
    odc = load_json(RAW / "odc_tables.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    stats = {"eufic": 0, "italy": 0, "odc": 0, "na": 0}

    for b, block in iter_blocks(db["items"], 15):
        for it in block:
            iid, src = it["id"], idx[it["id"]]["sources"]
            sea, agri, dc = it["seasonality"], it["agricultural_calendar_italy"], it["data_completeness"]
            enriched, used_all = [], []
            # ---------------- EUFIC
            fresh, stored = eufic_country_table(src.get("eufic_keys", []), eufic)
            if fresh or stored:
                sea["eufic_by_country"] = {c: fresh.get(c, [False] * 12) for c in sorted(set(fresh) | set(stored))}
                for z in ZONES:
                    cs = [c for c, v in zmap.items() if v["zone"] == z and (c in fresh or c in stored)]
                    if not cs:
                        sea["eufic_climatic_zones"][z] = None
                        continue
                    sc = [sum(fresh.get(c, [False] * 12)[m] for c in cs) / len(cs) for m in range(12)]
                    st = [sum(stored.get(c, [False] * 12)[m] for c in cs) / len(cs) for m in range(12)]
                    hints = ["stored" if sc[m] < 0.5 and st[m] >= 0.5 else None for m in range(12)]
                    sea["eufic_climatic_zones"][z] = states(sc, hints, 2 if len(cs) >= 2 else 1)
                enriched += ["seasonality.eufic_by_country", "seasonality.eufic_climatic_zones"]
                stats["eufic"] += 1
                used_all.append("EUFIC")
            # ---------------- Italia
            altro = altroconsumo_page(src["altroconsumo_url"]) if src.get("altroconsumo_url") else None
            eufic_it = fresh.get("Italy")
            votes, hints, used = italy_votes(src, wwf, gp, altro, eufic_it)
            n_nat = len(used)
            nat = None
            if n_nat:
                score, h2 = resolve_edges(votes, hints, n_nat)
                nat = states(score, h2, n_nat)
            local_prod = bool(src.get("odc_pdf_row") or eufic_it or src.get("wwf_row") or src.get("greenpeace_name"))
            if iid in EXOTIC_IF_NO_LOCAL and not local_prod:
                nat = ["not_applicable"] * 12
                stats["na"] += 1
                dc["notes"] += " Stagionalità Italia: frutto esotico senza produzione italiana nelle fonti -> not_applicable (Altroconsumo ne indica solo la disponibilità d'importazione)."
            sea["italy_national"] = nat
            if nat:
                enriched.append("seasonality.italy_national")
            draft_areas = {a: sea["italy_macro_areas"][a] for a in ("nord", "centro", "sud_isole")}
            odc_row = src.get("odc_pdf_row")
            for a in ("nord", "centro", "sud_isole"):
                v2, h2, n2 = list(votes), list(hints), n_nat
                if odc_row:
                    for m in odc["areas"][a][odc_row]["harvest"]:
                        v2[m - 1] += 1
                    n2 += 1
                if nat == ["not_applicable"] * 12:
                    new = nat
                elif n2:
                    score, hh = resolve_edges(v2, h2, n2)
                    new = states(score, hh, n2)
                else:
                    new = None
                if new is not None:
                    if draft_areas[a] and draft_areas[a] != new:
                        add_discrepancy(it, f"seasonality.italy_macro_areas.{a}", draft_areas[a], new,
                                        " + ".join(used + (["ODC raccolta " + a] if odc_row else [])))
                    sea["italy_macro_areas"][a] = new
                    enriched.append(f"seasonality.italy_macro_areas.{a}")
            if any(sea["italy_macro_areas"][a] for a in ("nord", "centro", "sud_isole")):
                stats["italy"] += 1
            used_all += used + (["Orto da Coltivare (raccolta per area)"] if odc_row else [])
            if used_all:
                sea["derivation_notes"] = {
                    "it": "Fonti: " + ", ".join(dict.fromkeys(used_all)) + ". Stati calcolati per voto tra fonti (metodo in metadata.seasonality_method).",
                    "en": "Sources: " + ", ".join(dict.fromkeys(used_all)) + ". States computed by voting across sources (method in metadata.seasonality_method)."}
                enriched.append("seasonality.derivation_notes")
            # ---------------- calendario agronomico ODC
            if odc_row:
                prm = odc["params_transcribed"][odc_row]
                for a in ("nord", "centro", "sud_isole"):
                    r = odc["areas"][a][odc_row]
                    z = agri[a] or {}
                    sow = sorted(set(r["seedbed"]) | set(r["direct"]) | set(r["transplant"]))
                    for f, val in (("sowing_or_transplant_months", sow), ("harvest_months", r["harvest"])):
                        if z.get(f) and sorted(z[f]) != val:
                            add_discrepancy(it, f"agricultural_calendar_italy.{a}.{f}", z[f], val, f"Orto da Coltivare tabella {a}")
                    # empty lists = the ODC table does not include that operation (data present, not missing)
                    agri[a] = {"sowing_or_transplant_months": sow, "harvest_months": r["harvest"],
                               "seedbed_sowing_months": r["seedbed"], "direct_sowing_months": r["direct"],
                               "transplant_months": r["transplant"], "cultivation_notes": z.get("cultivation_notes")}
                    enriched += [f"agricultural_calendar_italy.{a}.{k}" for k in
                                 ("sowing_or_transplant_months", "harvest_months", "seedbed_sowing_months",
                                  "direct_sowing_months", "transplant_months")]
                rn = odc["areas"]["nord"][odc_row]
                new_p = {"sowing_depth_cm": prm["depth_cm"],
                         "plant_spacing_cm": {"between_rows": prm["rows_cm"], "between_plants": prm["plants_cm"]},
                         "sun_exposure": rn["sun_exposure"], "lunar_phase_advice": rn["lunar_phase"]}
                old_p = agri["agronomic_params"] or {}
                for k, v in new_p.items():
                    if old_p.get(k) is not None and old_p.get(k) != v:
                        add_discrepancy(it, f"agricultural_calendar_italy.agronomic_params.{k}", old_p.get(k), v, "Orto da Coltivare")
                agri["agronomic_params"] = new_p
                enriched.append("agricultural_calendar_italy.agronomic_params")
                extra = [prm.get("depth_note"), prm.get("note")]
                if prm.get("by_area"):
                    extra.append(f"parametri diversi per area: {prm['by_area']}")
                if any(extra):
                    dc["notes"] += " ODC: " + "; ".join(x for x in extra if x) + "."
                for a in ("centro", "sud_isole"):
                    ra = odc["areas"][a][odc_row]
                    if (ra["sun_exposure"], ra["lunar_phase"]) != (rn["sun_exposure"], rn["lunar_phase"]):
                        dc["notes"] += f" ODC {a}: esposizione {ra['sun_exposure']}, luna {ra['lunar_phase']}."
                for f in ("fonti_locali/odc-tabella-nord.pdf", "fonti_locali/odc-tabella-centro.pdf", "fonti_locali/odc-tabella-sud.pdf"):
                    if f not in it["sources_by_topic"]["local_files_used"]:
                        it["sources_by_topic"]["local_files_used"].append(f)
                stats["odc"] += 1
            # legacy: keep the replaced draft values
            legacy["items"].setdefault(iid, {})["seasonality.italy_macro_areas"] = draft_areas
            mark_enriched(it, enriched)
            finalize_completeness(it)
        save_json(DATA / "database.json", db)
        save_json(DATA / "draft_legacy_values.json", legacy)
        print(f"blocco {b} salvato")
    db["metadata"]["seasonality_method"] = {"it": __doc__.split("Metodo di fusione")[1].split("Uso:")[0].strip(),
                                            "en": "Per-month score = votes / available sources (1 = in season, 0.5 = early/late); >=0.5 in season; "
                                                  "edges = early/end of season; peak = interior months of >=3-month runs where all (>=2) sources agree; "
                                                  "EUFIC zones = share of zone countries (dominant EEA region) reporting the item in season; stored -> end of season."}
    save_json(DATA / "database.json", db)
    print(stats)


if __name__ == "__main__":
    main()
