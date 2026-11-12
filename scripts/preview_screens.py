"""Fase 2 - anteprime PNG delle schermate dell'app (senza telefono).

Usa la build web dell'app *vera* (stesso codice Flutter di Android/iOS) e
la fotografa con Playwright + Microsoft Edge a dimensione telefono.
Le pagine lunghe (scheda alimento, impostazioni) sono fotografate con un
"telefono altissimo", così si vede tutta la pagina come se si scorresse.

Le notifiche non esistono nel browser: per quelle si genera una
simulazione grafica di Android con i testi reali calcolati dall'app
(esportati da app/test/preview_export_test.dart).

Prerequisiti (una volta):
    pip install playwright
    cd C:\\dev\\peak_season && flutter build web --release --no-web-resources-cdn
    (in un altro terminale) python -m http.server 8765 --bind 127.0.0.1 -d C:\\dev\\peak_season\\build\\web
    cd C:\\dev\\peak_season && set PREVIEW_EXPORT=1 && flutter test test/preview_export_test.dart

Uso:  python scripts/preview_screens.py [nome_schermata ...]
Output: schemi_interfaccia/anteprime_fase2/v2/*.png
"""
import html
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "schemi_interfaccia" / "anteprime_fase2" / "v2"
URL = "http://127.0.0.1:8765/"
W, H = 390, 844  # iPhone 14 / Pixel 7 circa, in punti logici
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
NOTIF_JSON = ROOT / "app" / "build" / "notification_preview.json"

# Stato di partenza: qualche preferito e qualcosa in lista, per vedere le icone attive.
BASE_PREFS = {
    "favoriteIds": ["cavolo_nero_black_kale", "cachi_persimmon", "mela_apple"],
    "shoppingListIds": ["mela_apple", "zucca_pumpkin", "finocchio_fennel", "porro_leek", "pomodoro_tomato"],
    "dislikedIds": [],
    "inCartIds": ["finocchio_fennel"],
}


def prefs_script(prefs: dict) -> str:
    # shared_preferences_web salva in localStorage "flutter.<chiave>" = JSON
    lines = ["localStorage.clear();"]
    for k, v in prefs.items():
        lines.append(f"localStorage.setItem({json.dumps('flutter.' + k)}, {json.dumps(json.dumps(v))});")
    return "\n".join(lines)


def shot(browser, name, prefs=None, actions=(), dark=False, query="", height=H, wait_ms=4000):
    ctx = browser.new_context(
        viewport={"width": W, "height": height},
        device_scale_factor=2,
        color_scheme="dark" if dark else "light",
    )
    ctx.add_init_script(prefs_script({**BASE_PREFS, **(prefs or {})}))
    page = ctx.new_page()
    page.goto(URL + (f"?{query}" if query else ""))
    page.wait_for_selector("flutter-view", timeout=60000)
    page.wait_for_timeout(wait_ms)
    for a in actions:
        kind, *args = a
        if kind == "click":
            page.mouse.click(*args)
        elif kind == "wait":
            page.wait_for_timeout(args[0])
        elif kind == "scroll":
            page.mouse.move(W / 2, H / 2)
            page.mouse.wheel(0, args[0])
    page.wait_for_timeout(1500)
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    ctx.close()
    print("ok", path.name)


# --- Simulazione notifiche Android ------------------------------------------

def _line(s: str) -> str:
    # le righe usano <b> come in Android (htmlFormatLines); il resto va escapato
    parts = re.split(r"(</?b>)", s)
    return "".join(p if p in ("<b>", "</b>") else html.escape(p) for p in parts)


def _notif(n, expanded=True, close=None, app="Peak Season", when=""):
    title = f"<div class='t'>{html.escape(n['title'])}</div>" if n.get("title") else ""
    lines = "".join(f"<div class='l'>{_line(x)}</div>" for x in n.get("lines", [])) if expanded else ""
    body = "" if expanded and n.get("lines") else f"<div class='b'>{html.escape(n['body'])}</div>"
    action = f"<div class='act'>{html.escape(close)}</div>" if close else ""
    return f"""<div class='n'>
      <div class='h'><span class='ic'>{LEAF}</span>{app}{(' · ' + when) if when else ''}<span class='chev'>⌃</span></div>
      {title}{body}{lines}{action}</div>"""


LEAF = ("<svg viewBox='0 0 24 24' width='14' height='14' fill='#2E7D32'><rect x='5' y='20.5' width='14' height='2' rx='1'/>"
        "<rect x='11' y='5' width='2' height='16' rx='1'/><path d='M12 18.5C7 18.5 3.5 15.5 3.5 11C8.5 11 12 14 12 18.5Z'/>"
        "<path d='M12 15C17 15 20.5 12 20.5 7.5C15.5 7.5 12 10.5 12 15Z'/><path d='M12 9.5C9.5 8 9 4.8 12 1.5C15 4.8 14.5 8 12 9.5Z'/></svg>")

CSS = """
body{margin:0;font-family:Roboto,'Segoe UI',sans-serif;width:390px}
.scr{width:390px;height:844px;position:relative;overflow:hidden;color:#fff}
.lock{background:linear-gradient(170deg,#3e5b46,#1d2b22 60%,#101712)}
.shade{background:#1c1f1c}
.clock{text-align:center;font-size:76px;font-weight:300;margin-top:70px;letter-spacing:-2px}
.date{text-align:center;font-size:15px;opacity:.85;margin-top:-4px}
.list{position:absolute;left:12px;right:12px;top:230px}
.shade .list{top:150px}
.n{background:rgba(245,247,242,.96);color:#1b1f1b;border-radius:24px;padding:14px 16px 14px;margin-bottom:8px}
.h{font-size:12px;color:#4a4f4a;display:flex;align-items:center;gap:6px}
.chev{margin-left:auto;font-size:12px;color:#777}
.t{font-weight:700;font-size:15px;margin-top:6px}
.b{font-size:13.5px;color:#3c403c;margin-top:2px}
.l{font-size:13px;color:#2f332f;margin-top:4px;line-height:1.3}
.act{display:inline-block;margin-top:10px;font-weight:700;color:#2E7D32;font-size:14px;padding:6px 14px;border-radius:16px;background:#E3EEDC}
.qs{display:flex;gap:10px;padding:52px 16px 0}
.qs div{flex:1;height:56px;border-radius:28px;background:#2b302b}
.qs div.on{background:#A5D6A7}
.top{position:absolute;top:10px;left:20px;right:20px;font-size:13px;display:flex;justify-content:space-between;opacity:.9}
.cap{position:absolute;bottom:14px;left:0;right:0;text-align:center;font-size:11px;opacity:.7}
.shade .cap{color:#ccc}
"""


def render_notifications(browser):
    if not NOTIF_JSON.exists():
        print("manca", NOTIF_JSON, "(esegui il test di export, vedi docstring)")
        return
    d = json.loads(NOTIF_JSON.read_text(encoding="utf-8"))
    cap = "Simulazione grafica Android · testi reali generati dall'app"
    pages = {
        "20_notifica_blocco_lista_evidenziata": f"""
          <div class='scr lock'><div class='top'><span>Iliad</span><span>🔋 82%</span></div>
          <div class='clock'>17:42</div><div class='date'>venerdì 6 novembre</div>
          <div class='list'>{_notif(d['highlight'], close=d['close'])}</div><div class='cap'>{cap}</div></div>""",
        "21_notifica_solo_lista": f"""
          <div class='scr lock'><div class='top'><span>Iliad</span><span>🔋 82%</span></div>
          <div class='clock'>17:42</div><div class='date'>venerdì 6 novembre</div>
          <div class='list'>{_notif(d['onlyList'], close=d['close'])}</div><div class='cap'>{cap}</div></div>""",
        "22_notifica_senza_lista": f"""
          <div class='scr lock'><div class='top'><span>Iliad</span><span>🔋 82%</span></div>
          <div class='clock'>17:42</div><div class='date'>venerdì 6 novembre</div>
          <div class='list'>{_notif(d['season'], close=d['close'])}</div><div class='cap'>{cap}</div></div>""",
        "23_notifiche_dopo_spesa_e_picco": f"""
          <div class='scr shade'><div class='qs'><div class='on'></div><div></div><div class='on'></div><div></div></div>
          <div class='list'>{_notif({'title': d['storage']['title'], 'body': d['storage']['body']}, expanded=False, when='ora')}
          {_notif(d['peak'], when='1 dic, 09:00')}</div><div class='cap'>{cap}</div></div>""",
    }
    for name, body in pages.items():
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        page.set_content(f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>")
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / f"{name}.png"))
        page.close()
        print("ok", name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    plan = [
        # nome, prefs, azioni, dark, query, altezza
        ("01_home_griglia", {}, [], False, "", H),
        ("02_home_lista_climaterico", {"homeViewMode": "list"}, [], False, "", H),
        ("03_home_calendario", {"homeViewMode": "calendar"}, [], False, "", H),
        ("04_legenda", {}, [("click", 195, 120), ("wait", 1200)], False, "", H),
        ("05_aiuto_climaterico", {"homeViewMode": "list"}, [("click", 254, 315), ("wait", 1200)], False, "", H),
        ("06_modalita_spesa_attiva", {"shoppingModeActive": True}, [], False, "", H),
        ("07_home_dark", {"themeMode": "dark"}, [], True, "", H),
        ("08_home_calendario_dark", {"homeViewMode": "calendar", "themeMode": "dark"}, [], True, "", H),
        ("10_scheda_pomodoro_completa", {}, [], False, "food=pomodoro_tomato", 3900),
        ("11_scheda_mela_completa", {}, [], False, "food=mela_apple", 3900),
        ("12_scheda_cece_stima", {"climaticZone": "pannonian"}, [], False, "food=cece_chickpea", 3400),
        ("13_scheda_dato_mancante", {"climaticZone": "pannonian", "allowApproximateSeasonality": False},
         [], False, "food=cece_chickpea", 3400),
        ("14_scheda_aglio_dark", {"themeMode": "dark"}, [], True, "food=aglio_garlic", 3900),
        ("15_lista_spesa", {}, [], False, "tab=1", 1700),
        ("16_come_conservarli", {}, [], False, "route=storage", 4200),
        ("17_impostazioni_complete", {"storageTipsDelayMinutes": 10}, [], False, "tab=2", 3000),
        ("18_sezioni_scheda", {"detailSectionModes": ["nutrition:collapsed", "garden:collapsed", "recipes:hidden"]},
         [], False, "route=sections", 1300),
        ("19_scheda_sezioni_personalizzate",
         {"detailSectionModes": ["nutrition:collapsed", "sustainability:collapsed", "garden:collapsed",
                                 "curiosities:collapsed", "recipes:hidden"],
          "detailSectionOrder": ["calendar", "buyStore", "varieties", "nutrition", "sustainability",
                                 "garden", "curiosities", "recipes", "links"]},
         [], False, "food=pomodoro_tomato", 2600),
        ("37_zone_climatiche_mappa", {}, [], False, "help=eufic_zones", 1500),
        ("39_galleria_schermo_intero", {}, [("click", 195, 150), ("wait", 1500)], False, "food=pomodoro_tomato", H),
        ("40_filtri_avanzati_dark", {"themeMode": "dark"}, [("click", 281, 160), ("wait", 1200)], True, "", 1300),
        ("41_lista_spesa_vuota", {"shoppingListIds": []}, [], False, "tab=1", H),
        ("38_zone_climatiche_mappa_dark", {"themeMode": "dark"}, [], True, "help=eufic_zones", 1500),
        ("34_famiglia_solanaceae", {}, [], False, "family=Solanaceae", H),
        ("35_mesi_gennaio_centrato", {}, [], False, "month=1", H),
        ("36_mesi_dicembre_centrato_dark", {"themeMode": "dark"}, [], True, "month=12", H),
        ("30_senza_dati_sezione_chiusa", {"climaticZone": "atlantic", "homeViewMode": "list"},
         [("scroll", 60000), ("wait", 800), ("scroll", 60000)], False, "", H),
        ("31_filtro_includi_senza_dati", {"climaticZone": "atlantic"}, [("click", 281, 160), ("wait", 1200)], False, "", 1250),
        ("32_scheda_riferimento_mediterranea", {"climaticZone": "atlantic"}, [], False, "food=cardo_cardoon", 1500),
        ("33_scheda_riferimento_italia", {"climaticZone": "atlantic"}, [], False, "food=cima_di_rapa_turnip_greens", 1500),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=EDGE, headless=True)
        for name, prefs, actions, dark, query, height in plan:
            if only and name not in only:
                continue
            shot(browser, name, prefs, actions, dark, query, height)
        if not only or any(n.startswith("2") for n in only):
            render_notifications(browser)
        browser.close()


if __name__ == "__main__":
    main()
