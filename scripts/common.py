"""Utility condivise dagli script Peak Season (percorsi, HTTP con cache, chiavi API)."""
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
    """Legge un JSON. Per database.json i riferimenti al corpus condiviso sono espansi in testo completo (corpus.py),
    salvo raw=True (file così com'è, per la validazione dello schema e per l'editor dei testi)."""
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    if not raw and pathlib.Path(path).name == "database.json" and isinstance(data, dict):
        import corpus
        corpus.expand(data)
    return data


def save_json(path, obj, raw=False):
    """Scrive un JSON in modo atomico. Per database.json ricompatta i testi ripetuti nel corpus condiviso (corpus.py),
    salvo raw=True (oggetto già nella forma del file)."""
    path = pathlib.Path(path)
    if not raw and path.name == "database.json" and isinstance(obj, dict) and "items" in obj:
        import corpus
        obj = corpus.compact(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    for attempt in range(10):  # OneDrive o un altro processo possono bloccare il file per qualche istante
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 9:
                raise
            import time
            time.sleep(1 + attempt)


def env(key):
    """Legge una chiave da variabile d'ambiente o dal file .env nella radice del progetto."""
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
    """GET tramite curl.exe di sistema (usa l'archivio certificati di Windows).
    Serve per host come list.worldfloraonline.org, che da Python fallisce la verifica TLS
    perché manca un certificato intermedio nell'archivio di Python."""
    out = subprocess.run(["curl.exe", "-s", "-L", "--max-time", str(timeout), "-A", UA, url],
                         capture_output=True, timeout=timeout + 10)
    if out.returncode != 0:
        raise RuntimeError(f"curl exit {out.returncode} for {url}")
    return json.loads(out.stdout.decode("utf-8"))


def null_paths(item, skip=("sources_by_topic", "data_completeness")):
    """Percorsi 'a.b.c' dei campi foglia nulli di un alimento (liste di oggetti = foglia unica)."""
    out = []

    def walk(o, p):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{p}.{k}" if p else k)
        elif o is None:
            out.append(p)
    walk({k: v for k, v in item.items() if k not in skip}, "")
    # campi non applicabili (non contano come mancanti): identificativo tassonomico dell'altro registro
    b = item.get("botany", {})
    na = set(item.get("data_completeness", {}).get("not_applicable_fields", []))
    if b.get("wfo_id"):
        na.add("botany.gbif_key")
    if b.get("gbif_key"):
        na.add("botany.wfo_id")
    return sorted(p for p in out if p not in na)


def mark_enriched(item, paths):
    """Registra i campi compilati/verificati da fonte: li toglie da 'pending' e li aggiunge a 'enriched'."""
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
