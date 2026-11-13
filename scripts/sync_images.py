"""Synchronises assets/images/ with database.json.

For each product it looks for the files  <id>_NN.jpg  in assets/images/ and updates images.primary, images.gallery and
images.image_details. Licence metadata (author, licence, source URL, view type) live in
assets/images/_metadata.json, written by the download script: so if you delete by hand the photos you do not
like, re-running this script realigns the database.

Usage:
  python scripts/sync_images.py               # realigns the database to the files present
  python scripts/sync_images.py --renumber    # renames the remaining files in sequence _01, _02, ... (updates the metadata)
  python scripts/sync_images.py --prune       # removes from _metadata.json the entries of files no longer present
  python scripts/sync_images.py --dry-run     # shows what would change without writing anything

Rules:
  - the main photo chosen by hand in the Admin Studio (assets/images/_primary_manual.json) always wins, if the file exists;
  - otherwise the main photo is the first "full_frame" photo (product filling the frame) without flagged issues and not of a specific variety; if there is none,
    the one already chosen stays if the file still exists, otherwise the lowest-numbered photo (owner rule, 2026-11-05);
  - a photo WITHOUT licence metadata does not enter the gallery (it is only flagged): for a photo of your own
    add an entry to _metadata.json with "provider": "user", author and licence.
"""
import re
import sys

from common import DATA, IMAGES, load_json, null_paths, save_json

META = IMAGES / "_metadata.json"
MANUAL = IMAGES / "_primary_manual.json"                     # foto principali scelte a mano (admin_studio)
PAT = re.compile(r"^(?P<id>[a-z0-9_]+)_(?P<n>\d{2})\.jpg$")
DETAIL_KEYS = ["filename", "author", "license", "license_url", "source_url", "provider", "width", "height", "view_type"]
OPTIONAL_KEYS = ["flags", "variety"]


def main():
    dry = "--dry-run" in sys.argv
    IMAGES.mkdir(parents=True, exist_ok=True)
    db = load_json(DATA / "database.json")
    meta = load_json(META) if META.exists() else {}
    manual = load_json(MANUAL) if MANUAL.exists() else {}
    ids = {it["id"] for it in db["items"]}

    files = {}
    unknown = []
    for f in sorted(IMAGES.glob("*")):
        if f.name.startswith("_") or f.is_dir():
            continue
        m = PAT.match(f.name)
        if not m or m.group("id") not in ids:
            unknown.append(f.name)
            continue
        files.setdefault(m.group("id"), []).append(f.name)

    renamed = {}
    if "--renumber" in sys.argv:
        for iid, names in files.items():
            ordered = sorted(names, key=lambda x: int(PAT.match(x).group("n")))
            plan = [(old, f"{iid}_{k:02d}.jpg") for k, old in enumerate(ordered, start=1)]
            plan = [(o, n) for o, n in plan if o != n]
            renamed.update(dict(plan))
            for o, n in plan:
                print(f"rinomina {o} -> {n}")
            if not dry and plan:
                # two phases (old -> temporary -> new) to avoid name collisions
                for o, _ in plan:
                    (IMAGES / o).rename(IMAGES / (o + ".tmp"))
                moved = {o: meta.pop(o, None) for o, _ in plan}
                for o, n in plan:
                    (IMAGES / (o + ".tmp")).rename(IMAGES / n)
                    if moved[o] is not None:
                        meta[n] = dict(moved[o], filename=n)
            files[iid] = [f"{iid}_{k:02d}.jpg" for k in range(1, len(ordered) + 1)]

    if "--prune" in sys.argv:
        present = {n for v in files.values() for n in v}
        gone = [k for k in meta if k not in present]
        for k in gone:
            print("prune metadati:", k)
            if not dry:
                meta.pop(k)

    changed, unlicensed = 0, []
    for it in db["items"]:
        iid = it["id"]
        names = sorted(files.get(iid, []), key=lambda x: int(PAT.match(x).group("n")))
        licensed = [n for n in names if n in meta and meta[n].get("license") and meta[n].get("source_url")]
        unlicensed += [n for n in names if n not in licensed]
        old = it["images"]
        prev = renamed.get(old.get("primary"), old.get("primary"))   # the main photo follows any renaming
        ff = [n for n in licensed if meta[n].get("view_type") == "full_frame" and not meta[n].get("flags") and not meta[n].get("variety")]
        manual_p = renamed.get(manual.get(iid), manual.get(iid))     # chosen by hand in the Admin Studio: wins over the rule
        primary = manual_p if manual_p in licensed else (ff[0] if ff else (prev if prev in licensed else (licensed[0] if licensed else None)))
        gallery = ([primary] + [n for n in licensed if n != primary]) if primary else []
        details = [{**{k: (meta[n].get(k) if k != "filename" else n) for k in DETAIL_KEYS},
                    **{k: meta[n][k] for k in OPTIONAL_KEYS if meta[n].get(k)}} for n in gallery]
        new = {"primary": primary, "gallery": gallery, "image_details": details}
        if new != old:
            changed += 1
            it["images"] = new
            dc = it["data_completeness"]
            dc["missing_fields"] = null_paths(it)
            enr = set(dc["fields_enriched_via_scraping"])
            if gallery:
                enr |= {"images.primary", "images.gallery", "images.image_details"}
            else:
                enr -= {"images.primary", "images.gallery", "images.image_details"}
            dc["fields_enriched_via_scraping"] = sorted(enr)

    n_img = sum(len(it["images"]["gallery"]) for it in db["items"])
    with_img = sum(bool(it["images"]["gallery"]) for it in db["items"])
    print(f"Alimenti aggiornati: {changed}. Immagini in galleria: {n_img} su {with_img}/{len(db['items'])} alimenti "
          f"(media {n_img / max(with_img, 1):.1f} per alimento con foto).")
    if unlicensed:
        print(f"ATTENZIONE {len(unlicensed)} foto senza metadati di licenza (escluse dalla galleria): {unlicensed[:10]}")
    if unknown:
        print(f"ATTENZIONE {len(unknown)} file con nome non riconosciuto (atteso <id>_NN.jpg): {unknown[:10]}")
    if not dry:
        save_json(DATA / "database.json", db)
        save_json(META, meta)


if __name__ == "__main__":
    main()
