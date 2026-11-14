"""Help Texts tab of the Admin Studio: the "?" explanations of the app (metadata.glossary).

The texts are written in scripts/config/glossary.json (the source); scripts/build_help.py copies them into the database
with the field_help map (field -> entries). Saving here edits the config file and reruns build_help.py,
ux_terminology.py and title_case_labels.py. Entries are not added or removed here: ids are used by the app code.

"Where it's used" is found by scanning app/lib for HelpButton/SubHeading/TextWithHelp calls: helpIds lists name the
entries directly, field/helpField paths name them through metadata.field_help.
"""
import json
import re
from pathlib import Path

from common import CONFIG, DATA, ROOT, load_json

GLOSSARY = CONFIG / "glossary.json"
APP_LIB = ROOT / "app" / "lib"
SCREENS = {"food_detail_screen": "Product detail", "storage_tips_screen": "Storage tips", "settings_screen": "Settings",
           "shopping_list_screen": "Shopping list", "family_screen": "Botanical family", "home_screen": "Home",
           "storage_summary": "Product detail › storage", "detail_parts": "Product detail", "help_button": "Help sheet",
           "calendar_view": "Calendar", "food_cards": "Product cards"}


def _usage(field_help):
    uses = {}
    if not APP_LIB.exists():
        return uses
    for f in APP_LIB.rglob("*.dart"):
        src = f.read_text(encoding="utf-8", errors="replace")
        base = re.search(r"\bbase\s*=\s*'([^']+)'", src)
        screen = SCREENS.get(f.stem, f.stem.replace("_", " ").capitalize())
        for n, line in enumerate(src.splitlines(), 1):
            ids = set()
            for m in re.finditer(r"helpIds:\s*(?:const\s*)?\[([^\]]*)\]", line):
                ids |= set(re.findall(r"'([a-z0-9_]+)'", m.group(1)))
            for m in re.finditer(r"\b(?:field|helpField):\s*'([^']+)'", line):
                path = m.group(1).replace("$base", base.group(1) if base else "$base")
                ids |= set(field_help.get(path) or [])
                for gid in field_help.get(path) or []:
                    uses.setdefault(gid, []).append({"screen": screen, "where": f"{f.relative_to(ROOT)}:{n}", "field": path})
            label = re.search(r"SubHeading\(\s*([^,]+),", line)
            for gid in ids:
                if not any(u["where"].endswith(f":{n}") for u in uses.get(gid, [])):
                    uses.setdefault(gid, []).append({"screen": screen, "where": f"{f.relative_to(ROOT)}:{n}",
                                                     "field": label.group(1).strip() if label else None})
    return uses


def payload():
    cfg = load_json(GLOSSARY)
    db = load_json(DATA / "database.json")
    meta = db["metadata"]
    refs = {}                                         # products whose texts link to the entry (item.help_refs)
    for it in db["items"]:
        for r in it.get("help_refs") or []:
            refs.setdefault(r["glossary_id"], set()).add(it["names"]["en"])
    fh = meta.get("field_help") or {}
    fh_ids = {k: [x if isinstance(x, str) else x.get("id") for x in (v if isinstance(v, list) else [v])] for k, v in fh.items()}
    usage = _usage(fh_ids)
    vocab = {}
    for vk, grp in (meta.get("vocabulary") or {}).items():
        if isinstance(grp, dict) and grp.get("_glossary"):
            vocab.setdefault(grp["_glossary"], []).append(vk)
    out = []
    for e in cfg["entries"]:
        fields = sorted(k for k, ids in fh_ids.items() if e["id"] in ids)
        out.append({"id": e["id"], "term": e["term"], "short": e.get("short") or {"it": "", "en": ""}, "text": e["text"],
                    "sources": e.get("sources") or [], "see_also": e.get("see_also") or [], "fields": fields,
                    "vocabulary": vocab.get(e["id"], []), "app_usage": usage.get(e["id"], []),
                    "product_refs": sorted(refs.get(e["id"], set()))})
    return {"entries": out}


def save(data, run_script):
    cfg = load_json(GLOSSARY)
    by = {e["id"]: e for e in cfg["entries"]}
    for gid, ch in (data.get("changes") or {}).items():
        if gid not in by:
            raise ValueError(f"unknown help entry: {gid}")
        for f in ("term", "short", "text"):
            if f in ch:
                v = ch[f]
                if not (v.get("it", "").strip() and v.get("en", "").strip()):
                    raise ValueError(f"{gid}: {f} needs both Italian and English")
                by[gid][f] = {"it": v["it"].strip(), "en": v["en"].strip()}
    Path(GLOSSARY).write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\r\n")
    for script in ("build_help.py", "build_app_support_metadata.py", "ux_terminology.py", "title_case_labels.py"):
        rc, out = run_script(script)
        if rc != 0:
            raise RuntimeError(f"{script}: {out[-500:]}")
