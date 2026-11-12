"""Schede Loghi e Link dell'Admin Studio (revisione 2026-11-13).

Loghi: per ogni fonte (metadata.official_sources) logo attuale (proprio, condiviso con un'altra fonte dello stesso ente
o assente), editore, titolo e testo da cercare. Il logo caricato dall'utente:
  - originale in fonti_locali/loghi_fonti/<chiave>.<ext> (ha la precedenza anche per scripts/fetch_source_favicons.py);
  - versione per l'app in app/assets/sources/<chiave>.png (128 px, sfondo chiaro reso trasparente, stessa funzione);
  - elenco dei loghi scuri rigenerato (app/lib/data/source_logos.g.dart e official_sources[].favicon_dark).
Editore, titolo e testo da cercare si salvano in scripts/config/source_display.json.

Link: tutti i link, generali (le fonti) e per prodotto (sources_by_topic.useful_links). Le modifiche ai link dei
prodotti si salvano in scripts/config/link_overrides.json (scripts/apply_link_overrides.py), così restano anche quando
build_source_registry.py rigenera i link.
"""
import base64
import io
import json
import re

from common import CONFIG, DATA, ROOT, load_json, save_json

DISPLAY = CONFIG / "source_display.json"
LINK_OV = CONFIG / "link_overrides.json"
LOGOS = ROOT / "app" / "assets" / "sources"
MANUAL = ROOT / "fonti_locali" / "loghi_fonti"
KEY = re.compile(r"^[a-z0-9_]+$")


def _db():
    return load_json(DATA / "database.json")


def logos_payload():
    db = _db()
    disp = load_json(DISPLAY)["sources"]
    used = {}
    for it in db["items"]:
        for l in it["sources_by_topic"].get("useful_links") or []:
            used[l["source_key"]] = used.get(l["source_key"], 0) + 1
    for g in (db["metadata"].get("glossary") or {}).values():
        for s in g.get("sources") or []:
            used[s["key"]] = used.get(s["key"], 0) + 1
    out = []
    for s in db["metadata"]["official_sources"]:
        k, d = s["key"], disp.get(s["key"], {})
        own = (LOGOS / f"{k}.png").exists()
        out.append({"key": k, "name": s.get("name"), "url": s.get("url"), "site_url": s.get("site_url"),
                    "publisher": d.get("publisher") or s.get("publisher") or {"it": "", "en": ""},
                    "title": d.get("title") or s.get("title") or {"it": "", "en": ""},
                    "logo_search": d.get("logo_search") or "", "logo_alias": d.get("logo_alias"),
                    "favicon": s.get("favicon"), "own_logo": own, "dark": s.get("favicon_dark"), "uses": used.get(k, 0)})
    out.sort(key=lambda x: (x["own_logo"], x["favicon"] is not None, x["key"]))   # prima quelle senza logo
    return {"sources": out}


def save_display(data, run_script):
    """Editore, titolo e testo da cercare di ogni fonte modificata."""
    cfg = load_json(DISPLAY)
    for k, ch in (data.get("changes") or {}).items():
        if not KEY.match(k):
            raise ValueError(f"chiave non valida: {k}")
        d = cfg["sources"].setdefault(k, {})
        for f in ("publisher", "title"):
            if f in ch:
                v = ch[f]
                if not (isinstance(v, dict) and v.get("it", "").strip() and v.get("en", "").strip()):
                    raise ValueError(f"{k}: {f} deve avere italiano e inglese")
                d[f] = {"it": v["it"].strip(), "en": v["en"].strip()}
        if "logo_search" in ch:
            d["logo_search"] = ch["logo_search"].strip()
    save_json(DISPLAY, cfg)
    _rebuild(run_script)


def upload_logo(data, run_script):
    """Logo caricato dal browser (data URL in base64) per la fonte data["key"]."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from PIL import Image
    from fetch_source_favicons import make_logo, write_dart
    k = data.get("key", "")
    if not KEY.match(k) or k not in {s["key"] for s in _db()["metadata"]["official_sources"]}:
        raise ValueError("fonte sconosciuta")
    m = re.match(r"^data:image/(png|jpe?g|webp);base64,(.+)$", data.get("data_url", ""), re.S)
    if not m:
        raise ValueError("serve un'immagine PNG, JPG o WebP (gli SVG vanno prima convertiti in PNG)")
    raw = base64.b64decode(m.group(2))
    if len(raw) > 15 * 1024 * 1024:
        raise ValueError("immagine troppo grande (oltre 15 MB)")
    im = Image.open(io.BytesIO(raw))
    im.load()
    ext = {"jpeg": "jpg"}.get(m.group(1), m.group(1))
    MANUAL.mkdir(parents=True, exist_ok=True)
    for old in MANUAL.glob(f"{k}.*"):                 # un solo originale per fonte
        if old.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and old.name != f"{k}.{ext}":
            old.unlink()
    (MANUAL / f"{k}.{ext}").write_bytes(raw)
    make_logo(im).save(LOGOS / f"{k}.png")
    write_dart()
    _rebuild(run_script)


def _rebuild(run_script):
    for script in ("build_app_support_metadata.py", "ux_terminology.py", "title_case_labels.py"):
        rc, out = run_script(script)
        if rc != 0:
            raise RuntimeError(f"{script}: {out[-500:]}")


# ------------------------------------------------------------------ link
def links_payload():
    db = _db()
    general = [{"key": s["key"], "publisher": s.get("publisher"), "title": s.get("title"), "url": s.get("url"),
                "site_url": s.get("site_url"), "favicon": s.get("favicon")} for s in db["metadata"]["official_sources"]]
    items = [{"id": it["id"], "name": it["names"]["it"], "links": it["sources_by_topic"].get("useful_links") or []} for it in db["items"]]
    topics = sorted({l["topic"] for it in items for l in it["links"]} | {"other"})
    ov = load_json(LINK_OV) if LINK_OV.exists() else {"items": {}}
    return {"general": general, "items": items, "topics": topics, "overrides": ov,
            "source_keys": sorted({s["key"] for s in general} | {"user"})}


def save_links(data, run_script):
    """data["changes"]: {id: {"edit": {url_originale: {url, title}}, "remove": [...], "add": [...]}} da unire al file."""
    ov = load_json(LINK_OV) if LINK_OV.exists() else {"_note": "Modifiche ai link dei prodotti fatte con l'Admin Studio "
                                                      "(scripts/apply_link_overrides.py).", "items": {}}
    for iid, ch in (data.get("changes") or {}).items():
        o = ov["items"].setdefault(iid, {"edit": {}, "remove": [], "add": []})
        for orig, e in (ch.get("edit") or {}).items():
            _check(e)
            added = next((a for a in o["add"] if a["url"] == orig), None)
            if added:                                 # link aggiunto a mano: si modifica direttamente
                added.update(e)
            else:
                prev = next((k for k, v in o["edit"].items() if v.get("url") == orig), orig)
                o["edit"][prev] = {**o["edit"].get(prev, {}), **e}
        for url in ch.get("remove") or []:
            if any(a["url"] == url for a in o["add"]):
                o["add"] = [a for a in o["add"] if a["url"] != url]
            else:
                orig = next((k for k, v in o["edit"].items() if v.get("url") == url), url)
                o["edit"].pop(orig, None)
                if orig not in o["remove"]:
                    o["remove"].append(orig)
        for a in ch.get("add") or []:
            _check(a)
            o["add"].append({"url": a["url"], "title": a["title"], "source_key": a.get("source_key") or "user",
                             "topic": a.get("topic") or "other"})
    save_json(LINK_OV, ov)
    rc, out = run_script("apply_link_overrides.py")
    if rc != 0:
        raise RuntimeError(out[-500:])


def _check(e):
    if "url" in e and not re.match(r"^https?://\S+$", e["url"] or ""):
        raise ValueError(f"indirizzo non valido: {e['url']}")
    if "title" in e and not (e["title"].get("it", "").strip() and e["title"].get("en", "").strip()):
        raise ValueError("il titolo del link deve avere italiano e inglese")


def search_list():
    """Elenco da copiare: un testo da cercare per ogni fonte senza logo proprio."""
    out = []
    for s in logos_payload()["sources"]:
        if not s["favicon"] and s["logo_search"] and s["logo_search"] not in out:
            out.append(s["logo_search"])
    return "\n".join(out)


if __name__ == "__main__":
    print(json.dumps(logos_payload(), ensure_ascii=False)[:500])
