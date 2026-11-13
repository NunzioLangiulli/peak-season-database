"""Utilities shared by the Peak Season scripts (paths, cached HTTP, API keys)."""
import json
import os
import pathlib
import subprocess
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
CONFIG = ROOT / "scripts" / "config"
FONTI = ROOT / "fonti_locali"
IMAGES = ROOT / "assets" / "images"

UA = "PeakSeasonDataBot/0.1 (progetto universitario; python-requests)"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = UA


def load_json(path, raw=False):
    """Reads a JSON file. For database.json the references to the shared corpus are expanded into full text (corpus.py),
    unless raw=True (file as stored, for schema validation and for the text editor)."""
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    if not raw and pathlib.Path(path).name == "database.json" and isinstance(data, dict):
        import corpus
        corpus.expand(data)
    return data


def save_json(path, obj, raw=False):
    """Writes a JSON file atomically. For database.json it compacts repeated texts into the shared corpus (corpus.py),
    unless raw=True (object already in the file's form)."""
    path = pathlib.Path(path)
    if not raw and path.name == "database.json" and isinstance(obj, dict) and "items" in obj:
        import corpus
        obj = corpus.compact(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    for attempt in range(10):  # OneDrive or another process may lock the file for a moment
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 9:
                raise
            import time
            time.sleep(1 + attempt)


def env(key):
    """Reads a key from an environment variable or from the .env file at the project root."""
    if os.environ.get(key):
        return os.environ[key]
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            if line.strip().startswith(key + "="):
                return line.split("=", 1)[1].strip()
    return None


def http_get(url, *, params=None, headers=None, timeout=45, retries=3, pause=0.5):
    last = None
    for i in range(retries):
        try:
            r = SESSION.get(url, params=params, headers=headers, timeout=timeout)
            time.sleep(pause)
            return r
        except requests.RequestException as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


def http_post_json(url, payload, timeout=45, retries=3, pause=0.3):
    last = None
    for i in range(retries):
        try:
            r = SESSION.post(url, json=payload, timeout=timeout)
            time.sleep(pause)
            return r
        except requests.RequestException as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


def curl_get_json(url, timeout=45):
    """GET through the system curl.exe (uses the Windows certificate store).
    Needed for hosts such as list.worldfloraonline.org, which fail TLS verification from Python
    because an intermediate certificate is missing from Python's store."""
    out = subprocess.run(["curl.exe", "-s", "-L", "--max-time", str(timeout), "-A", UA, url],
                         capture_output=True, timeout=timeout + 10)
    if out.returncode != 0:
        raise RuntimeError(f"curl exit {out.returncode} for {url}")
    return json.loads(out.stdout.decode("utf-8"))


def null_paths(item, skip=("sources_by_topic", "data_completeness")):
    """'a.b.c' paths of a product's null leaf fields (lists of objects = a single leaf)."""
    out = []

    def walk(o, p):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{p}.{k}" if p else k)
        elif o is None:
            out.append(p)
    walk({k: v for k, v in item.items() if k not in skip}, "")
    # non-applicable fields (not counted as missing): taxonomic identifier of the other register
    b = item.get("botany", {})
    na = set(item.get("data_completeness", {}).get("not_applicable_fields", []))
    if b.get("wfo_id"):
        na.add("botany.gbif_key")
    if b.get("gbif_key"):
        na.add("botany.wfo_id")
    return sorted(p for p in out if p not in na)


def mark_enriched(item, paths):
    """Records the fields filled/verified from a source: removes them from 'pending' and adds them to 'enriched'."""
    dc = item["data_completeness"]
    paths = set(paths)
    dc["fields_enriched_via_scraping"] = sorted(set(dc["fields_enriched_via_scraping"]) | paths)
    pend = dc.get("fields_pending_verification", [])
    dc["fields_pending_verification"] = [p for p in pend if not any(p == q or p.startswith(q + ".") for q in paths)]


def add_discrepancy(item, field, draft_value, source_value, source, resolution="adottato il valore della fonte ufficiale"):
    dc = item["data_completeness"]
    dc.setdefault("discrepancies", [])
    dc["discrepancies"] = [d for d in dc["discrepancies"] if d["field"] != field]
    dc["discrepancies"].append({"field": field, "draft_value": draft_value, "source_value": source_value,
                                "source": source, "resolution": resolution})


def finalize_completeness(item):
    dc = item["data_completeness"]
    dc["missing_fields"] = null_paths(item)
    dc["is_complete"] = not dc["missing_fields"] and not dc.get("fields_pending_verification")


def iter_blocks(items, size=15):
    for i in range(0, len(items), size):
        yield i // size + 1, items[i:i + size]


def cached_json(cache_path, key, fetch):
    """Cache JSON chiave->valore su disco (salvataggio incrementale)."""
    cache_path = pathlib.Path(cache_path)
    cache = load_json(cache_path) if cache_path.exists() else {}
    if key not in cache:
        cache[key] = fetch()
        save_json(cache_path, cache)
    return cache[key]
