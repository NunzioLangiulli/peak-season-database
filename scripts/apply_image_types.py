"""Applies the photo classification (scripts/config/image_view_types.json) to assets/images/_metadata.json:
view_type, flags (dish, wrong_item) and variety. Then run sync_images.py, which picks as main photo the first
full_frame photo without issues.
Usage:  python scripts/apply_image_types.py
"""
from common import CONFIG, IMAGES, load_json, save_json


def main():
    cfg = load_json(CONFIG / "image_view_types.json")
    meta = load_json(IMAGES / "_metadata.json")
    n = 0
    for fn, vt in cfg["view_types"].items():
        if fn not in meta:
            continue
        m = meta[fn]
        m["view_type"] = vt
        for key in ("flags", "variety"):
            val = cfg.get(key, {}).get(fn)
            if key == "flags" and val:
                val = [val] if isinstance(val, str) else val
            if val:
                m[key] = val
            else:
                m.pop(key, None)
        n += 1
    left = [k for k, v in meta.items() if v.get("view_type") not in ("full_frame", "isolated_background", "plant_in_field", "botanical_plate", "cut_section", "other")]
    save_json(IMAGES / "_metadata.json", meta)
    print(f"classificate {n} foto; senza classificazione: {left[:10]}")


if __name__ == "__main__":
    main()
