"""Review of the "Where to Store It" section (2026-11-13, owner request). Idempotent.
Applies to the database the rules now written in apply_home_storage.py without regenerating the whole home_storage:
- room_temperature label: "A Temperatura Ambiente" / "At Room Temperature" (consistent with the others);
- tip: no "Once cut it always goes in the fridge" for the fridge and for products without a location;
  no sentences repeating storage_instructions (shown right above in the app). Empty tip = null.
Usage:  python scripts/apply_storage_display_review.py   (after apply_home_storage.py; then ux_terminology and title_case_labels)
"""
from apply_home_storage import LABEL, TIPS, home_tip
from enrich_chilling import set_na
from common import CONFIG, DATA, finalize_completeness, load_json, save_json


def main():
    cfg = load_json(CONFIG / "ucdavis_home_storage.json")["items"]
    db = load_json(DATA / "database.json")
    n = {"label": 0, "tip": 0, "tip_removed": 0}
    for it in db["items"]:
        hs = it["ripening_and_storage"].get("home_storage")
        if not hs:
            continue
        loc = hs.get("location")
        if loc:
            lab = {"it": LABEL[loc][0], "en": LABEL[loc][1]}
            if (hs.get("label") or {}).get("it", "").lower() != lab["it"].lower():
                hs["label"] = lab
                n["label"] += 1
        u = cfg.get(it["id"])
        new = home_tip(it["id"], loc, TIPS.get(it["id"]) or (TIPS[u[2]] if u and len(u) > 2 else None))
        if new != hs.get("tip"):
            n["tip"] += 1
            n["tip_removed"] += new is None
            hs["tip"] = new
            if new is None:                                   # field empty by choice, not missing data
                set_na(it, ["ripening_and_storage.home_storage.tip"])
        finalize_completeness(it)
    m = db["metadata"].get("home_storage_legend") or {}
    if m.get("locations"):
        m["locations"]["room_temperature"] = {"it": LABEL["room_temperature"][0], "en": LABEL["room_temperature"][1]}
    save_json(DATA / "database.json", db)
    print(n)


if __name__ == "__main__":
    main()
