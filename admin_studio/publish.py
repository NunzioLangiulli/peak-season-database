"""Versions, Git and one-click publishing for the Admin Studio.

The project has two GitHub repositories: the database (project root) and the app (app/). Each one gets its own commit
message, and you choose which ones to include; a repository without changes is simply skipped.

Publish (the "Publish…" button). Steps, in order; the first failure stops everything:
  1. sync the database, copy and icons into the app (scripts/build_app_assets.py)
  2. validate the database (scripts/validate_db.py)
  3. run the app tests and build the Android APK (only when the app is included or its version has no release yet)
  4. commit and push the included repositories (English messages, no co-author lines)
  5. create a GitHub release for an included repository whose version has no release yet:
     - database: tag v<metadata.version>  (DB_VERSION in scripts/build_app_support_metadata.py)
     - app: tag v<appVersion in app/lib/app_info.dart> with the APK attached as PeakSeason-<version>.apk; publishing
       the app release also starts the iOS workflow (.github/workflows/ios.yml), which attaches the unsigned .ipa.
Commit & Push (the "Commit & Push" button): steps 1, 2 and 4 only.
Versions: current version, latest GitHub release and Git state of both repositories; a new version is written
everywhere it lives (database: DB_VERSION/DB_RELEASE_DATE and README; app: app_info.dart, pubspec.yaml, README).
The two versions are independent: the app can get new versions while the database stays the same, and vice versa.

Commit messages follow the project style: English, one short line, imperative verb, optional "Area:" prefix,
no final full stop (e.g. "Admin Studio: add READMEs tab"); a new version is committed as "Peak Season 1.2.0" (app)
or "Database 1.2.0" (database). suggest_message() proposes one from the changed files.

Usage:
  python admin_studio/publish.py --preview                      JSON summary shown before publishing
  python admin_studio/publish.py [--only database,app] [--message-database "Text"] [--message-app "Text"]
                                                                publish
  python admin_studio/publish.py --git-only [same options]      Commit & Push only
  python admin_studio/publish.py --versions                     versions, releases, Git state (JSON)
  python admin_studio/publish.py --set-version app 1.2.0        write a new app (or database) version
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
OWNER = "NunzioLangiulli"
REPOS = {"database": (ROOT, f"{OWNER}/peak-season-database"), "app": (APP, f"{OWNER}/peak-season-app")}
APK = APP / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"
APP_INFO = APP / "lib" / "app_info.dart"
PUBSPEC = APP / "pubspec.yaml"
METADATA_SCRIPT = ROOT / "scripts" / "build_app_support_metadata.py"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def tool(name, *fallbacks):
    for c in (os.environ.get(name.upper()), shutil.which(name), *fallbacks):
        if c and Path(c).exists():
            return c
    return None


FLUTTER = tool("flutter", r"C:\src\flutter\bin\flutter.bat")
GH = tool("gh", r"C:\Program Files\GitHub CLI\gh.exe")
GIT = tool("git") or "git"


def cmd(exe):
    return ["cmd", "/c", exe] if exe and exe.lower().endswith(".bat") else [exe]


def out(args, cwd=ROOT):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).rstrip()


# ------------------------------------------------------------------ versions
def db_version():
    return json.loads((ROOT / "data" / "database.json").read_text(encoding="utf-8-sig"))["metadata"]["version"]


def app_version():
    """App version shown in Settings (app/lib/app_info.dart); pubspec.yaml must match (app test)."""
    if APP_INFO.exists():
        m = re.search(r"appVersion\s*=\s*'([\d.]+)'", APP_INFO.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    m = re.search(r"^version:\s*([\d.]+)", PUBSPEC.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def has_release(repo, tag):
    if not GH:
        return None
    rc, _ = out([GH, "release", "view", tag, "--repo", repo])
    return rc == 0


def latest_release(repo):
    if not GH:
        return None
    rc, o = out([GH, "release", "list", "--repo", repo, "--limit", "1", "--exclude-drafts", "--json", "tagName", "-q", ".[0].tagName"])
    return o.strip().lstrip("v") if rc == 0 and o.strip() else None


def next_versions(v):
    a, b, c = (int(x) for x in v.split("."))
    return {"patch": f"{a}.{b}.{c + 1}", "minor": f"{a}.{b + 1}.0", "major": f"{a + 1}.0.0"}


def git_state(path):
    _, st = out([GIT, "status", "--porcelain"], path)
    _, ahead = out([GIT, "rev-list", "--count", "@{u}..HEAD"], path)
    _, last = out([GIT, "log", "-1", "--format=%h %s (%cr)"], path)
    _, br = out([GIT, "rev-parse", "--abbrev-ref", "HEAD"], path)
    return {"branch": br, "changes": [l for l in st.splitlines() if l.strip()],
            "unpushed_commits": int(ahead) if ahead.isdigit() else 0, "last_commit": last}


# areas of each repository, in the order they appear in a suggested message: (path prefix, words)
AREAS = {"database": [("data/database.json", "database content"), ("data/ui_", "app texts and icons"), ("data/", "database content"),
                      ("scripts/config/", "database content"), ("scripts/", "pipeline scripts"), ("admin_studio/", "Admin Studio"),
                      ("assets/", "image metadata"), ("README", "documentation")],
         "app": [("assets/data/", "synced database"), ("assets/icons/", "icons"), ("assets/", "assets"), ("lib/", "app code"),
                 ("test/", "tests"), (".github/", "workflows"), ("android/", "Android project"), ("ios/", "iOS project"),
                 ("pubspec", "dependencies"), ("README", "documentation")]}


def suggest_message(k, git, current, released):
    """Commit message in the project style, from the changed files and the version state."""
    if current and released and current != released:
        return f"Peak Season {current}" if k == "app" else f"Database {current}"
    parts = []
    for line in git["changes"]:
        path = line[3:].strip().strip('"').split(" -> ")[-1]
        word = next((w for pre, w in AREAS[k] if path.startswith(pre)), None)
        if word and word not in parts:
            parts.append(word)
    if not parts:
        return ""
    if len(parts) > 3:
        parts = parts[:3]
    text = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return "Update " + text


def versions():
    """Current versions, latest GitHub releases, Git state and a suggested commit message for both repositories."""
    res = {}
    for k, cur in (("database", db_version()), ("app", app_version())):
        rel, git = latest_release(REPOS[k][1]), git_state(REPOS[k][0])
        res[k] = {"current": cur, "released": rel, "next": next_versions(cur) if cur else {}, "repo": REPOS[k][1], "git": git,
                  "suggested_message": suggest_message(k, git, cur, rel)}
    return res


def _sub(path, rx, rep, required=True):
    text = path.read_text(encoding="utf-8")
    new, n = re.subn(rx, rep, text, flags=re.M)
    if required and n == 0:
        raise ValueError(f"version not found in {path.relative_to(ROOT)}")
    path.write_text(new, encoding="utf-8")


def set_version(target, version):
    """Write a new version everywhere it lives. For the database the caller then reruns build_app_support_metadata.py."""
    if not SEMVER.match(version or ""):
        raise ValueError("the version must look like 1.2.3")
    if target == "database":
        _sub(METADATA_SCRIPT, r'^DB_VERSION = "[\d.]+"', f'DB_VERSION = "{version}"')
        _sub(METADATA_SCRIPT, r'^DB_RELEASE_DATE = "[\d-]+"', f'DB_RELEASE_DATE = "{datetime.date.today().isoformat()}"')
        _sub(ROOT / "README.md", r"current release: \*\*v[\d.]+\*\*", f"current release: **v{version}**", required=False)
    elif target == "app":
        _sub(APP_INFO, r"appVersion = '[\d.]+'", f"appVersion = '{version}'")
        m = re.search(r"^version:\s*[\d.]+\+(\d+)", PUBSPEC.read_text(encoding="utf-8"), re.M)
        build = int(m.group(1)) + 1 if m else 1                 # Android needs a higher build number for every update
        _sub(PUBSPEC, r"^version:\s*[\d.]+(\+\d+)?", f"version: {version}+{build}")
        _sub(APP / "README.md", r"\*\*Current version: [\d.]+\.\*\*", f"**Current version: {version}.**", required=False)
    else:
        raise ValueError("unknown target")


# ------------------------------------------------------------------ publishing
def preview():
    v = versions()
    for k in v:
        v[k]["release_exists"] = has_release(REPOS[k][1], f"v{v[k]['current']}") if v[k]["current"] else None
    return {"repos": v, "flutter": FLUTTER, "gh": GH}


def run(title, args, cwd=ROOT, ok=(0,)):
    print(f"$ {title}", flush=True)
    p = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                         errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    for line in p.stdout:
        print(line.rstrip("\n"), flush=True)
    rc = p.wait()
    if rc not in ok:
        print(f"✗ {title} failed (exit code {rc}): stopped here.", flush=True)
        sys.exit(1)


def commit_and_push(only, messages):
    for k in only:
        path = REPOS[k][0]
        _, st = out([GIT, "status", "--porcelain"], path)
        if st.strip():
            msg = messages.get(k) or suggest_message(k, git_state(path), None, None) or "Update files"
            run(f"Commit the {k} repository: {msg}", [GIT, "add", "-A"], path)
            run(f"Commit the {k} repository: {msg}", [GIT, "commit", "-m", msg], path)
        else:
            print(f"$ Commit the {k} repository", flush=True)
            print("no changes: nothing to commit", flush=True)
        run(f"Push the {k} repository", [GIT, "push"], path)
    for k in REPOS:
        if k not in only:
            print(f"$ {k} repository not included: left as it is", flush=True)


def git_only(only, messages):
    py = sys.executable
    run("Sync data to the app", [py, str(ROOT / "scripts" / "build_app_assets.py"), "--db-only"])
    run("Validate the database", [py, str(ROOT / "scripts" / "validate_db.py")])
    commit_and_push(only, messages)
    print("✓ Committed and pushed", flush=True)


def publish(only, messages):
    if not GH:
        sys.exit("✗ GitHub CLI (gh) not found.")
    py = sys.executable
    av, dv = app_version(), db_version()
    app_release = "app" in only and av and not has_release(REPOS["app"][1], f"v{av}")
    run("Sync data to the app", [py, str(ROOT / "scripts" / "build_app_assets.py")])
    run("Validate the database", [py, str(ROOT / "scripts" / "validate_db.py")])
    if "app" in only:
        if not FLUTTER:
            sys.exit("✗ Flutter not found.")
        run("Run the app tests", cmd(FLUTTER) + ["test"], APP)
        if app_release:
            run("Build the Android APK", cmd(FLUTTER) + ["build", "apk", "--release"], APP)
        else:
            print(f"$ Build the Android APK\napp v{av} is already released: no APK needed", flush=True)
    commit_and_push(only, messages)
    if "database" in only:
        if not has_release(REPOS["database"][1], f"v{dv}"):
            run(f"Create the database release v{dv}", [GH, "release", "create", f"v{dv}", "--repo", REPOS["database"][1], "--target", "main",
                                                         "--title", f"Database {dv}", "--generate-notes"])
        else:
            print(f"$ Database v{dv} is already released: no new release", flush=True)
    if app_release:
        asset = APK.with_name(f"PeakSeason-{av}.apk")
        shutil.copyfile(APK, asset)
        run(f"Create the app release v{av}", [GH, "release", "create", f"v{av}", str(asset), "--repo", REPOS["app"][1], "--target", "main",
                                               "--title", f"Peak Season {av}", "--generate-notes"])
        print("The iOS workflow now builds the unsigned .ipa and attaches it to this release (about 15-30 minutes).", flush=True)
    elif "app" in only:
        print(f"$ App v{av} is already released: no new release", flush=True)
    print("✓ Published", flush=True)


def _opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


if __name__ == "__main__":
    a = sys.argv
    only = [k for k in (_opt("--only", "database,app") or "").split(",") if k in REPOS]
    messages = {"database": _opt("--message-database", _opt("--message")), "app": _opt("--message-app", _opt("--message"))}
    if "--preview" in a:
        print(json.dumps(preview(), ensure_ascii=False))
    elif "--versions" in a:
        print(json.dumps(versions(), ensure_ascii=False))
    elif "--set-version" in a:
        i = a.index("--set-version")
        set_version(a[i + 1], a[i + 2])
        print(f"{a[i + 1]} version set to {a[i + 2]}")
    elif not only:
        sys.exit("✗ No repository selected.")
    elif "--git-only" in a:
        git_only(only, messages)
    else:
        publish(only, messages)
