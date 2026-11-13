"""Peak Season Admin Studio (revision 2026-11-12): app texts, images, icons and build in a single dashboard.

Start:  double-click admin_studio/Avvia_Admin_Studio.bat (Windows) or Avvia_Admin_Studio.sh (Mac/Linux),
        or  python admin_studio/studio.py  [--no-browser]
The browser opens at http://localhost:8765 (if the port is busy, for example because of the app's web preview, the
next free one: the address is printed in the window). The server listens on 127.0.0.1 only.

Tabs: App Copy, Shared Corpus, Product Texts, Images, Icons, Logos, Links; Build & Deploy panel always
visible. Every save writes the files, runs scripts/validate_db.py (if it fails, the files are restored) and
syncs the app assets (scripts/build_app_assets.py). The only commands that can be run are those listed in
JOBS: the browser cannot launch arbitrary commands.
Modules: studio.py (server and API), images.py (gallery and download), icons.py (icon map), sources.py (logos and links), static/ (page).
"""
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(HERE))
import icons  # noqa: E402
import images  # noqa: E402
import sources  # noqa: E402
from corpus import FIELDS, KEY  # noqa: E402

DB = ROOT / "data" / "database.json"
UI = ROOT / "data" / "ui_copy.json"
SNAP = ROOT / "data" / "_snapshots"
APP = Path(r"C:\dev\peak_season") if Path(r"C:\dev\peak_season\pubspec.yaml").exists() else ROOT / "app"  # junction: avoids a project path with non-ASCII characters
APP_DATA = ROOT / "app" / "assets" / "data"
APK_DIR = ROOT / "app" / "build" / "app" / "outputs" / "flutter-apk"
# On Windows the Dart (AOT) compiler and the Kotlin plugin fail with non-ASCII paths (e.g. "Università") even through
# the junction or a subst drive: the APK is then built in a copy of the app on a simple path, on the same drive
# as the package cache, and the APK is copied back to app/build/app/outputs/flutter-apk/.
STAGE = Path(r"C:\dev\peak_season_build")
NEEDS_STAGE = sys.platform.startswith("win") and not str(ROOT).isascii()
PORT = 8765
KEEP_BACKUPS = 30                                     # Studio backup copies kept in data/_snapshots
LOCK = threading.Lock()                               # one write at a time on the database files


def flutter_cmd():
    for c in (os.environ.get("FLUTTER"), shutil.which("flutter"), r"C:\src\flutter\bin\flutter.bat"):
        if c and Path(c).exists():
            return c
    return None


# ------------------------------------------------------------------ file e validazione
def read(p, default):
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else default


def write(p, obj):
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for attempt in range(10):                       # OneDrive may lock the file for a moment
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.5)


def run_script(name, *args):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / name), *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode, (r.stdout + r.stderr).strip()


def guarded(files, change, sync_args=("--db-only",)):
    """Backup copy of the files, change, validation; if validation fails the files are restored.
    If it succeeds it syncs the app assets (database, ui_copy, ui_config and any new images)."""
    with LOCK:
        SNAP.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        saved = {}
        for f in files:
            if f.exists():
                saved[f] = SNAP / f"_studio_backup_{stamp}_{f.name}"
                shutil.copy2(f, saved[f])
        try:
            extra = change() or {}
        except Exception as e:                       # noqa: BLE001 - mostrato all'utente
            for f, b in saved.items():
                shutil.copy2(b, f)
            return {"ok": False, "report": f"Error: {e}"}
        rc, report = run_script("validate_db.py")
        if rc != 0:
            for f, b in saved.items():
                shutil.copy2(b, f)
            for f in extra.get("new_files", []):     # files created by this operation (e.g. a downloaded photo)
                Path(f).unlink(missing_ok=True)
            return {"ok": False, "report": report}
        backups = sorted(SNAP.glob("_studio_backup_*"), key=lambda f: f.name)
        for f in backups[:-KEEP_BACKUPS]:             # only the Studio's backup copies, the oldest ones
            f.unlink(missing_ok=True)
        src, sync = run_script("build_app_assets.py", *sync_args)
        return {"ok": True, "report": report, "sync": sync, "sync_ok": src == 0, **{k: v for k, v in extra.items() if k != "new_files"}}


# ------------------------------------------------------------------ testi (schede Testi App, Corpus, Descrizioni)
def is_text(v):
    return isinstance(v, dict) and (("it" in v and "en" in v and set(v) <= {"it", "en"}) or "corpus_ref" in v)


def slots(o, path, field, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "data_completeness":
                continue
            if is_text(v) and k in FIELDS:
                out.append((path + [k], v))
            else:
                slots(v, path + [k], k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if is_text(v) and field in FIELDS:
                out.append((path + [i], v))
            else:
                slots(v, path + [i], field, out)


def copy_payload():
    db = read(DB, {})
    items = []
    for it in db.get("items", []):
        out = []
        slots(it, [], None, out)
        items.append({"id": it["id"], "name": it["names"]["it"], "name_en": it["names"]["en"], "fields": [{"path": p, "value": v} for p, v in out]})
    return {"ui": read(UI, {"_meta": {}, "strings": []}), "corpus": db.get(KEY, {}), "items": items}


def copy_save(data):
    def change():
        db = read(DB, {})
        if data.get("corpus") is not None:
            rebuilt = {}
            for k, v in db.items():                  # the corpus stays between "metadata" and "items"
                if k == KEY:
                    continue
                rebuilt[k] = v
                if k == "metadata":
                    rebuilt[KEY] = data["corpus"]
            db = rebuilt
        by_id = {it["id"]: it for it in db["items"]}
        for ch in data.get("item_changes") or []:
            o = by_id[ch["id"]]
            for k in ch["path"][:-1]:
                o = o[k]
            o[ch["path"][-1]] = ch["value"]
        write(DB, db)
        if data.get("ui") is not None:
            prev = {s["key"]: s for s in read(UI, {"strings": []})["strings"]}
            new = {s["key"] for s in data["ui"]["strings"]}
            if set(prev) != new:
                raise ValueError("app copy keys cannot be added, removed or renamed from the editor")
            ph = re.compile(r"\{\w+\}")                # placeholders such as {name} or {icon}: the app replaces them
            for s in data["ui"]["strings"]:
                want = set(ph.findall(prev[s["key"]].get("it", "")) + ph.findall(prev[s["key"]].get("en", "")))
                for lang in ("it", "en"):
                    if set(ph.findall(s.get(lang, ""))) != set(ph.findall(prev[s["key"]].get(lang, ""))):
                        raise ValueError(f"{s['key']} ({lang}): the placeholders {sorted(want)} must stay in the text, written exactly the same")
            data["ui"].setdefault("_meta", {})["updated"] = date.today().isoformat()
            write(UI, data["ui"])
    return guarded([DB, UI], change)


# ------------------------------------------------------------------ build & deploy
JOBS, JOB_LOCK = {}, threading.Lock()


class Job:
    def __init__(self, kind, steps, open_dir=None):
        self.kind, self.lines, self.done, self.rc, self.started = kind, [], False, None, time.time()
        threading.Thread(target=self.run, args=(steps, open_dir), daemon=True).start()

    def run(self, steps, open_dir):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
        try:
            for title, cmd, cwd, *ok in steps:
                ok = ok[0] if ok else (0,)
                self.lines.append(f"$ {title}")
                p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                     errors="replace", env=env, bufsize=1)
                for line in p.stdout:
                    self.lines.append(line.rstrip("\n"))
                self.rc = p.wait()
                if self.rc in ok:
                    self.rc = 0
                if self.rc != 0:
                    self.lines.append(f"✗ Command ended with exit code {self.rc}")
                    return
            self.lines.append("✓ Done")
            if open_dir and Path(open_dir).exists():
                open_folder(open_dir)
                self.lines.append(f"Folder opened: {open_dir}")
        except Exception as e:                       # noqa: BLE001
            self.rc = -1
            self.lines.append(f"✗ Error: {e}")
        finally:
            self.done = True


def open_folder(p):
    if sys.platform.startswith("win"):
        os.startfile(str(p))                         # noqa: S606 - cartella locale dell'APK
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(p)])


def start_job(kind):
    with JOB_LOCK:
        if any(not j.done for j in JOBS.values()):
            return None, "Another operation is already running: wait for it to finish."
        py = [sys.executable, str(ROOT / "scripts" / "build_app_assets.py")]
        if kind == "sync":
            steps, open_dir = [("Sync database, copy, icons and new images with the app", py, ROOT)], None
        elif kind == "apk":
            fl = flutter_cmd()
            if not fl:
                return None, "Flutter not found: install Flutter or set the FLUTTER variable to the path of flutter(.bat)."
            fcmd = ["cmd", "/c", fl] if fl.lower().endswith(".bat") else [fl]
            steps = [("Sync the app assets", py, ROOT)]
            build_dir = APP
            if NEEDS_STAGE:
                build_dir = STAGE
                STAGE.mkdir(parents=True, exist_ok=True)
                steps.append((f"Copy the app to {STAGE} (path without accents)",
                              ["robocopy", str(ROOT / "app"), str(STAGE), "/MIR", "/XD", "build", ".dart_tool", ".idea", ".gradle",
                               "/NFL", "/NDL", "/NJH", "/NP"], ROOT, range(0, 8)))      # robocopy: 0-7 = riuscito
            steps.append(("flutter build apk --release", fcmd + ["build", "apk", "--release"], build_dir))
            if NEEDS_STAGE:
                src = STAGE / "build" / "app" / "outputs" / "flutter-apk"
                steps.append(("Copy the APK to the app folder", [sys.executable, "-c",
                              "import shutil,sys,pathlib;s,d=map(pathlib.Path,sys.argv[1:]);d.mkdir(parents=True,exist_ok=True);"
                              "[print('copied',f.name) or shutil.copy2(f,d/f.name) for f in s.glob('*.apk*')]", str(src), str(APK_DIR)], ROOT))
            open_dir = APK_DIR
        else:
            return None, "Unknown operation"
        jid = str(int(time.time() * 1000))
        JOBS[jid] = Job(kind, steps, open_dir)
        return jid, None


def status():
    """Sync status between the project files and the app files."""
    def mt(p):
        return p.stat().st_mtime if p.exists() else None

    def same(a, b):
        return a.exists() and b.exists() and a.read_bytes() == b.read_bytes()
    db_src, db_app = mt(DB), mt(APP_DATA / "database.json")
    db = read(DB, {})
    out = ROOT / "app" / "assets" / "images"         # thumb/ = main photos (600 px), full/ = whole gallery (1080 px)
    full = {p.stem for p in (out / "full").glob("*.webp")}
    thumb = {p.stem for p in (out / "thumb").glob("*.webp")}
    no_webp = [f for it in db.get("items", []) for f in it["images"].get("gallery") or [] if Path(f).stem not in full]
    no_webp += [it["images"]["primary"] for it in db.get("items", []) if it["images"].get("primary") and Path(it["images"]["primary"]).stem not in thumb]
    apk = APK_DIR / "app-release.apk"
    newest = max(x for x in [db_app, mt(APP_DATA / "ui_copy.json"), mt(APP_DATA / "ui_config.json"), 0] if x)
    return {
        "database": "ok" if db_app and db_src and db_app >= db_src else "needs sync",
        "ui_copy": "ok" if same(UI, APP_DATA / "ui_copy.json") else ("missing" if not UI.exists() else "needs sync"),
        "ui_config": "ok" if same(icons.CONFIG, APP_DATA / "ui_config.json") else ("missing" if not icons.CONFIG.exists() else "needs sync"),
        "images_without_webp": len(no_webp),
        "apk": {"exists": apk.exists(), "time": time.strftime("%d/%m/%Y %H:%M", time.localtime(mt(apk))) if apk.exists() else None,
                "stale": (not apk.exists()) or mt(apk) < newest, "path": str(APK_DIR)},
        "flutter": flutter_cmd(), "app_dir": str(APP),
        "running": next((k for k, j in JOBS.items() if not j.done), None),
    }


# ------------------------------------------------------------------ server
SAFE_IMG = re.compile(r"^[a-z0-9_]+_\d{2}\.jpg$")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8", cache=False):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "max-age=3600" if cache else "no-store")
        self.end_headers()
        self.wfile.write(b)

    def js(self, obj, code=200):
        self.send(code, json.dumps(obj, ensure_ascii=False))

    def file(self, p, cache=False):
        if not p.exists() or not p.is_file():
            return self.send(404, "{}")
        self.send(200, p.read_bytes(), mimetypes.guess_type(p.name)[0] or "application/octet-stream", cache)

    def do_GET(self):
        u = urlparse(self.path)
        p, q = u.path, parse_qs(u.query)
        if p == "/":
            return self.file(HERE / "static" / "index.html")
        if p.startswith("/static/") and re.fullmatch(r"/static/[a-z_]+\.(js|css)", p):
            return self.file(HERE / "static" / p.split("/")[-1])
        if p == "/api/copy":
            return self.js(copy_payload())
        if p == "/api/images/items":
            return self.js(images.item_list())
        if p == "/api/images/item":
            return self.js(images.item_detail(q.get("id", [""])[0]))
        if p.startswith("/img/"):                    # the app's WebP thumbnail if present, otherwise the original photo
            name = p[5:]
            if not SAFE_IMG.match(name):
                return self.send(404, "{}")
            webp = [ROOT / "app" / "assets" / "images" / d / (name[:-4] + ".webp") for d in ("thumb", "full")]
            small = next((w for w in webp if w.exists()), None)
            return self.file(small if small and "full" not in q else ROOT / "assets" / "images" / name, cache=True)
        if p == "/api/icons":
            return self.js(icons.payload())
        if p.startswith("/icon/"):
            f = icons.svg_path(p[6:])
            return self.file(f, cache=True) if f else self.send(404, "{}")
        if p == "/api/sources":
            return self.js(sources.logos_payload())
        if p == "/api/links":
            return self.js(sources.links_payload())
        if p.startswith("/logo/"):                   # source logos for the app (app/assets/sources)
            name = p[6:]
            if not re.fullmatch(r"[a-z0-9_]+\.png", name):
                return self.send(404, "{}")
            return self.file(sources.LOGOS / name)
        if p == "/api/status":
            return self.js(status())
        if p.startswith("/api/jobs/"):
            j = JOBS.get(p.split("/")[-1])
            if not j:
                return self.js({"error": "job non trovato"}, 404)
            start = int(q.get("from", ["0"])[0])
            return self.js({"lines": j.lines[start:], "next": len(j.lines), "done": j.done, "rc": j.rc, "kind": j.kind})
        self.send(404, "{}")

    def do_POST(self):
        origin = self.headers.get("Origin", "").split("//")[-1]
        if origin not in ("", f"localhost:{PORT}", f"127.0.0.1:{PORT}"):
            return self.send(403, "{}")
        n = int(self.headers.get("Content-Length", 0))
        if n > 25 * 1024 * 1024:
            return self.send(413, "{}")
        try:
            data = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            p = self.path
            if p == "/api/copy/save":
                res = copy_save(data)
            elif p == "/api/images/save":
                res = guarded([DB, images.META, images.MANUAL], lambda: images.save(data), sync_args=())  # nuova miniatura principale
            elif p == "/api/images/download":
                res = guarded([DB, images.META, images.MANUAL], lambda: images.download(data), sync_args=())
            elif p == "/api/icons/save":
                res = guarded([DB, icons.CONFIG], lambda: icons.save(data, run_script))
            elif p == "/api/sources/save":
                res = guarded([DB, sources.DISPLAY], lambda: sources.save_display(data, run_script))
            elif p == "/api/sources/logo":
                res = guarded([DB, sources.DISPLAY], lambda: sources.upload_logo(data, run_script))
            elif p == "/api/links/save":
                res = guarded([DB, sources.LINK_OV], lambda: sources.save_links(data, run_script))
            elif p == "/api/jobs":
                jid, err = start_job(data.get("kind"))
                res = {"ok": bool(jid), "id": jid, "report": err}
            elif p == "/api/open_apk_folder":
                if APK_DIR.exists():
                    open_folder(APK_DIR)
                res = {"ok": APK_DIR.exists()}
            else:
                return self.send(404, "{}")
        except Exception as e:                       # noqa: BLE001 - l'errore va mostrato all'utente
            res = {"ok": False, "report": f"Error: {e}"}
        self.js(res)


class Server(ThreadingHTTPServer):
    allow_reuse_address = False                      # on Windows, reuse would allow "sharing" a busy port

    def server_bind(self):
        import socket
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main():
    global PORT
    for port in range(PORT, PORT + 15):              # 8765; if it is busy, the next free one
        try:
            srv = Server(("127.0.0.1", port), Handler)
            PORT = port
            break
        except OSError:
            continue
    else:
        sys.exit(f"No free port between {PORT} and {PORT + 14}")
    url = f"http://localhost:{PORT}"
    print(f"Peak Season Admin Studio running at {url}\n(close this window or press Ctrl+C to stop it)", flush=True)
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
