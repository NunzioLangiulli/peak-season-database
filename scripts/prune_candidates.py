"""Filters the candidate images before the owner's review. Idempotent.

1. Automatic rule (Pixabay): the product's English name must be EXACTLY one of the first two tags
   (singular or plural); e.g. discards "wild garlic" for garlic.
2. Visual discards (Claude's pre-review of the preview sheets): scripts/config/image_candidates_prescreen.json,
   {product: {type: [numbers to discard]}} or {type: {"drop": [numbers], "move": {"number": "other_type"}}}
   to move a candidate to the right type (e.g. a full-frame photo found by searching "cut").
Discarded files are deleted from assets/images/_candidates/<id>/; the remaining ones are renumbered.
Usage:  python scripts/prune_candidates.py [--pass2]   (then find_image_candidates.py --merge and make_candidates_review.py)
"""
import re

from common import CONFIG, IMAGES, load_json, save_json
from find_image_candidates import db_path
from find_image_candidates import merge

OUT = IMAGES / "_candidates"


def exact_tag(h, en):
    """en: accepted name or list of names (database name + alternative names from config/image_search_names.json)."""
    tags = [t.strip().lower() for t in h.get("title", "").split(",")][:2]
    for a in (en if isinstance(en, list) else [en]):
        base = re.sub(r"(es|s)$", "", a.lower().strip())
        if any(re.fullmatch(re.escape(base) + r"(e?s)?", t) for t in tags):
            return True
    return False


def pass2(names):
    """Second pass: acts only on candidates marked "pass": 2 (added by find_image_candidates.py --fill).
    Visual discards in config/image_candidates_prescreen2.json, with the numbers in the FILE NAME (<type>_<n>.jpg)."""
    pre = load_json(CONFIG / "image_candidates_prescreen2.json") if (CONFIG / "image_candidates_prescreen2.json").exists() else {}
    tot = drop = 0
    for f in sorted(OUT.glob("*/candidates.json")):
        iid = f.parent.name
        c = load_json(f)
        if c.get("_pruned2") or not c.get("_filled"):
            continue
        moved = {}
        for t, lst in list(c.items()):
            if t.startswith("_"):
                continue
            rule = pre.get(iid, {}).get(t, [])
            bad = set(rule if isinstance(rule, list) else rule.get("drop", []))
            mv = {} if isinstance(rule, list) else {int(k): v for k, v in rule.get("move", {}).items()}
            keep = []
            for h in lst:
                if h.get("pass") != 2:
                    keep.append(h)
                    continue
                tot += 1
                n = int(h["file"].rsplit("_", 1)[1].split(".")[0])
                auto_bad = h["provider"] == "pixabay" and not exact_tag(h, names.get(iid, ""))
                if n in mv and not auto_bad:
                    moved.setdefault(mv[n], []).append(h)
                elif n not in bad and not auto_bad:
                    keep.append(h)
                else:
                    drop += 1
                    (OUT / h["file"]).unlink(missing_ok=True)
            c[t] = keep
        for t, hs in moved.items():
            c.setdefault(t, []).extend(hs)
        renumber(iid, c)
        c["_pruned2"] = True
        save_json(f, c)
    merge()
    print(f"second pass: candidates examined {tot}, discarded {drop}")


def renumber(iid, c):
    """Renumbers <type>_<n>.jpg. First moves ALL files to unique temporary names, then assigns the final names:
    so a candidate moved from one type to another is not overwritten."""
    items = []
    for t, lst in list(c.items()):
        if t.startswith("_"):
            continue
        lst[:] = [h for h in lst if (OUT / h["file"]).exists()]   # voci senza file (anteprima persa): tolte
        items += [(t, h) for h in lst]
    for k, (t, h) in enumerate(items):
        tmp = f"{iid}/_tmp_{k}.jpg"
        (OUT / h["file"]).replace(OUT / tmp)
        h["file"] = tmp
    count = {}
    for t, h in items:
        count[t] = count.get(t, 0) + 1
        new = f"{iid}/{t}_{count[t]}.jpg"
        (OUT / h["file"]).replace(OUT / new)
        h["file"] = new


def main():
    from common import DATA
    from find_image_candidates import alt_names
    alts = alt_names()
    names = {i["id"]: [i["names"]["en"].split("(")[0].strip()] + alts.get(i["id"], []) for i in load_json(db_path())["items"]}
    import sys
    if "--pass2" in sys.argv:
        pass2(names)
        return
    pre = load_json(CONFIG / "image_candidates_prescreen.json") if (CONFIG / "image_candidates_prescreen.json").exists() else {}
    tot = drop = 0
    for f in sorted(OUT.glob("*/candidates.json")):
        iid = f.parent.name
        c = load_json(f)
        if c.get("_pruned"):
            continue
        moved = {}
        for t, lst in list(c.items()):
            if t.startswith("_"):
                continue
            rule = pre.get(iid, {}).get(t, [])
            bad = set(rule if isinstance(rule, list) else rule.get("drop", []))
            mv = {} if isinstance(rule, list) else {int(k): v for k, v in rule.get("move", {}).items()}
            keep = []
            for n, h in enumerate(lst, 1):
                tot += 1
                auto_bad = h["provider"] == "pixabay" and not exact_tag(h, names.get(iid, ""))
                if n in mv and not auto_bad:
                    moved.setdefault(mv[n], []).append(h)
                elif n not in bad and not auto_bad:
                    keep.append(h)
                else:
                    drop += 1
                    (OUT / h["file"]).unlink(missing_ok=True)
            c[t] = keep
        for t, hs in moved.items():
            c.setdefault(t, []).extend(hs)
        renumber(iid, c)
        c["_pruned"] = True
        save_json(f, c)
    merge()
    print(f"candidates examined {tot}, discarded {drop}")


if __name__ == "__main__":
    main()
