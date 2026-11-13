"""Home storage from USDA FoodKeeper, full version (data/raw/foodkeeper_full.json).

enrich_foodkeeper.py only used the DOP_* fields ("from the date of purchase"). FoodKeeper also has the generic fields
Pantry_/Refrigerate_/Freeze_* (e.g. culinary herbs, cereals, prickly pear) and qualitative indications:
- Pantry_Metric = "When Ripe": the fruit is kept at room temperature UNTIL RIPE (then, if stated
  in the notes, N days: "Until Ripe, then 1-2 days") and only afterwards in the fridge;
- no pantry value: FoodKeeper recommends the fridge ONLY;
- Freeze_Metric = "Not Recommended": freezing not recommended.
Fields added to estimated_shelf_life_days:
  room_temp_mode: "days" | "until_ripe" | "fridge_only" | null
  freezing_recommended: true | false | null
If room_temp_mode is "fridge_only" (or "until_ripe" without days) room_temp_days is not applicable (N/A); if
freezing is not recommended, so is in_freezer_months. Replaced draft values go to draft_legacy_values.
Usage:  python scripts/apply_foodkeeper_modes.py   (after enrich_foodkeeper; before apply_texts)
"""
import re

from common import DATA, RAW, add_discrepancy, finalize_completeness, load_json, mark_enriched, save_json
from enrich_chilling import set_na

F = {"Days": 1, "Weeks": 7, "Months": 30, "Years": 365}
P = "ripening_and_storage.postharvest_physiology.estimated_shelf_life_days"
MODE_IT = {"days": "in dispensa per {d}", "until_ripe": "fino a maturazione{d}, poi in frigorifero",
           "fridge_only": "solo in frigorifero (nessuna durata in dispensa)"}


def rng(o, pre):
    """(min, max) in giorni dal blocco <pre>_Min/_Max/_Metric, oppure None."""
    a, b, m = o.get(pre + "_Min"), o.get(pre + "_Max"), o.get(pre + "_Metric")
    if a is None or m not in F:
        return None
    return [int(a * F[m]), int((b if b is not None else a) * F[m])]


def fmt(d):
    return f"{d[0]}-{d[1]} giorni" if d[0] != d[1] else f"{d[0]} giorni"


def main():
    fk = load_json(RAW / "foodkeeper_full.json")["products"]
    fkp = load_json(RAW / "foodkeeper_produce.json")
    mapping, approx = fkp["mapping"], set(fkp.get("mapping_approx", []))
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    stats = {"days": 0, "until_ripe": 0, "fridge_only": 0, "fridge_new": 0, "freezer_new": 0, "no_freeze": 0}
    for it in db["items"]:
        sl = it["ripening_and_storage"]["postharvest_physiology"]["estimated_shelf_life_days"]
        sl.setdefault("room_temp_mode", None)
        sl.setdefault("freezing_recommended", None)
        pid = mapping.get(it["id"])
        o = fk.get(str(pid)) if pid else None
        if not o:
            finalize_completeness(it)
            continue
        name = o["Name"] + (f" ({o['Name_subtitle']})" if o.get("Name_subtitle") else "")
        src = f"USDA FoodKeeper ({name})"
        lg = legacy["items"].setdefault(it["id"], {})
        pending = set(it["data_completeness"].get("fields_pending_verification", []))
        enr, na = [f"{P}.room_temp_mode", f"{P}.freezing_recommended", f"{P}.basis"], []

        # --- temperatura ambiente
        pantry = rng(o, "DOP_Pantry") or rng(o, "Pantry")
        tips = (o.get("Pantry_tips") or "") + " " + (o.get("DOP_Pantry_tips") or "")
        old = sl["room_temp_days"]
        if pantry:
            mode, val = "days", pantry
        elif o.get("Pantry_Metric") == "When Ripe":
            m = re.search(r"Until Ripe, then (\d+)(?:-(\d+))? days", tips)
            mode, val = "until_ripe", ([int(m.group(1)), int(m.group(2) or m.group(1))] if m else None)
        else:
            mode, val = "fridge_only", None
        sl["room_temp_mode"] = mode
        if val is not None:
            if old is not None and old != val:
                add_discrepancy(it, f"{P}.room_temp_days", old, val, src)
            sl["room_temp_days"] = val
            enr.append(f"{P}.room_temp_days")
        else:
            if old is not None and f"{P}.room_temp_days" in pending:
                lg[f"{P}.room_temp_days"] = old
            sl["room_temp_days"] = None
            na.append(f"{P}.room_temp_days")
        stats[mode] += 1

        # --- fridge (generic fields if the DOP ones are missing)
        fridge = rng(o, "DOP_Refrigerate") or rng(o, "Refrigerate")
        if fridge and sl["refrigerated_days"] != fridge:
            if sl["refrigerated_days"] is not None:
                add_discrepancy(it, f"{P}.refrigerated_days", sl["refrigerated_days"], fridge, src)
            sl["refrigerated_days"] = fridge
            stats["fridge_new"] += 1
        if fridge:
            enr.append(f"{P}.refrigerated_days")

        # --- congelatore
        frz = rng(o, "DOP_Freeze") or rng(o, "Freeze")
        if (o.get("Freeze_Metric") == "Not Recommended" or o.get("DOP_Freeze_Metric") == "Not Recommended"
                or (not frz and "damage" in (o.get("Freeze_Tips") or "").lower())):
            sl["freezing_recommended"] = False
            if sl["in_freezer_months"] is not None and f"{P}.in_freezer_months" in pending:
                lg[f"{P}.in_freezer_months"] = sl["in_freezer_months"]
            sl["in_freezer_months"] = None
            na.append(f"{P}.in_freezer_months")
            stats["no_freeze"] += 1
        elif frz:
            sl["freezing_recommended"] = True
            months = round(frz[1] / 30, 1)
            if sl["in_freezer_months"] != months:
                if sl["in_freezer_months"] is not None and abs(sl["in_freezer_months"] - months) > 1:
                    add_discrepancy(it, f"{P}.in_freezer_months", sl["in_freezer_months"], months, src)
                sl["in_freezer_months"] = months
                stats["freezer_new"] += 1
            enr.append(f"{P}.in_freezer_months")

        d = f" (poi {fmt(val)})" if mode == "until_ripe" and val else ""
        room = MODE_IT[mode].format(d=fmt(val) if mode == "days" else d)
        notes = [t.strip() for t in (o.get("Pantry_tips"), o.get("DOP_Pantry_tips"), o.get("Refrigerate_tips"),
                                     o.get("DOP_Refrigerate_tips"), o.get("Freeze_Tips")) if t]
        notes = [t.rstrip(".") + "." for t in notes]
        sl["basis"] = (f"Durate domestiche: USDA FoodKeeper '{name}'"
                       + (" (voce approssimata)" if it["id"] in approx else "")
                       + f". Temperatura ambiente: {room}"
                       + ("; congelamento sconsigliato" if sl["freezing_recommended"] is False else "")
                       + "." + (f" Note FoodKeeper: {' '.join(notes)}" if notes else "")
                       + " commercial_optimal_days: USDA HB66 / UC Davis in condizioni professionali.")
        mark_enriched(it, enr)
        dc = it["data_completeness"]
        dc["not_applicable_fields"] = [p for p in dc.get("not_applicable_fields", []) if p not in enr]
        if na:
            set_na(it, na)
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print(stats)


if __name__ == "__main__":
    main()
