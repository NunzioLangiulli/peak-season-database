"""Libreria delle icone dell'app Peak Season (SVG 24x24, monocromatiche).

Ogni icona è il contenuto di un <svg viewBox="0 0 24 24">: si colora con il
colore del tema (fill="currentColor" / ColorFilter in Flutter). Le due
tonalità di verde si ottengono con fill-opacity.

- APPROVED: icone scelte dall'utente (scritte in app/assets/icons/ui/<nome>.svg)
- ROUND2: icone da rifare o da scegliere (tavola schema_icone_5.png)
Uso: python scripts/icon_library.py   → esporta le approvate e genera tavola + ICONE.md
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEASON = ROOT / "app" / "assets" / "icons" / "season"
UI = ROOT / "app" / "assets" / "icons" / "ui"
SHEET_DIR = ROOT / "schemi_interfaccia" / "proposte_icone"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def season(name):
    s = (SEASON / f"{name}.svg").read_text(encoding="utf-8")
    return s[s.index(">") + 1: s.rindex("</svg>")]


# --- Tavola 2: da rifare / da scegliere --------------------------------------
LENS_EYE = ('<path fill-rule="evenodd" d="M10 3a7 7 0 015.6 11.2l5.1 5.1-1.4 1.4-5.1-5.1A7 7 0 1110 3zm0 2a5 5 0 100 10 5 5 0 000-10z"/>'
            '<path fill-rule="evenodd" d="M10 7.2c-2 0-3.5 1.4-4.1 2.8.6 1.4 2.1 2.8 4.1 2.8s3.5-1.4 4.1-2.8c-.6-1.4-2.1-2.8-4.1-2.8zm0 1.4a1.4 1.4 0 110 2.8 1.4 1.4 0 010-2.8z"/>')

HILLS = ('<defs><clipPath id="front"><path d="M1 20c3.6-5.4 7.4-7.6 11.2-7.2 3.7.4 7 2.6 10.8 6V20z"/></clipPath></defs>'
         '<path d="M1 20v-4c3-4.2 6.5-6.4 10.5-6.2 3.2.2 5.8 1.6 8 3.6V20z" fill-opacity=".5"/>'
         '<g clip-path="url(#front)">'
         + "".join(f'<rect x="{-6 + i * 3.2:.1f}" y="8" width="1.7" height="16" transform="rotate(32 12 16)" />' for i in range(10))
         + "".join(f'<rect x="{-4.3 + i * 3.2:.1f}" y="8" width="1.5" height="16" transform="rotate(32 12 16)" fill-opacity=".55"/>' for i in range(10))
         + '</g>'
         '<circle cx="18.5" cy="5" r="2.1"/>'
         + "".join(f'<rect x="18" y="0.6" width="1" height="1.6" rx=".5" transform="rotate({a} 18.5 5)"/>' for a in range(0, 360, 45)))

def _sustainability(stem_w=1.1, r=6.2, deg0=-205, deg1=-140, L=9.6, Wd=4.6):
    """Tre foglie con stelo ad arco (effetto frecce in cerchio) e nervatura
    centrale in un verde più chiaro: la nervatura è un taglio nella foglia
    riempito con lo stesso colore a opacità ridotta, quindi si vede su
    qualsiasi sfondo e con qualsiasi colore del tema."""
    import math
    cx = cy = 12
    a0, a1 = math.radians(deg0), math.radians(deg1)
    n = 14
    f = lambda q: f"{q[0]:.2f},{q[1]:.2f}"
    out = []
    for rot in (0, 120, 240):
        arc = lambda rr: [(cx + rr * math.cos(a0 + (a1 - a0) * i / n), cy + rr * math.sin(a0 + (a1 - a0) * i / n))
                          for i in range(n + 1)]
        stem = "M" + "L".join(f(p) for p in arc(r + stem_w / 2) + arc(r - stem_w / 2)[::-1]) + "Z"
        ex, ey = cx + r * math.cos(a1), cy + r * math.sin(a1)
        tx, ty = -math.sin(a1), math.cos(a1)
        nx, ny = math.cos(a1), math.sin(a1)
        P = lambda u, v: (ex + tx * L * u + nx * v, ey + ty * L * u + ny * v)
        tip = P(1, 1.0)
        leaf = (f"M{ex:.2f},{ey:.2f}C{f(P(.25, Wd))} {f(P(.85, Wd * .75))} {f(tip)}"
                f"C{f(P(.85, -Wd * .45))} {f(P(.25, -Wd * .7))} {ex:.2f},{ey:.2f}Z")
        # nervatura: sottile lente lungo l'asse della foglia (dalla base all'80%)
        rib = (f"M{f(P(.12, .1))}Q{f(P(.5, .95))} {f(P(.82, .85))}"
               f"Q{f(P(.5, .3))} {f(P(.12, -.25))}Z")
        out.append(f'<g transform="rotate({rot} 12 12)"><path d="{stem}"/>'
                   f'<path fill-rule="evenodd" d="{leaf}{rib}"/><path d="{rib}" fill-opacity=".45"/></g>')
    return "".join(out)


# --- Icone approvate (scelte nella tavola 1) --------------------------------
# nome file: (elemento, scelta, dove si usa, svg)
APPROVED = {
    "info": ("Informazioni Aggiuntive", "I1 · Cerchio con i (2026-11-12)", "Scheda → titolo Informazioni Aggiuntive",
                '<path d="M12 2a10 10 0 110 20 10 10 0 010-20zm-1.2 8.2v7.6h2.4v-7.6zm1.2-4a1.5 1.5 0 100 3 1.5 1.5 0 000-3z"/>'),
    "speed_up": ("Per Farlo Maturare", "M4 · Frutto al calduccio (2026-11-12)", "Scheda → Maturazione",
                '<path transform="translate(1.2 1.6) scale(.9)" d="M12 7.6c-1.2-1-2.8-1.4-4.3-1.1C4.9 7 3.4 9.6 3.4 12.7c0 4.3 2.9 8.6 5.4 8.6 1.1 0 1.7-.6 3.2-.6s2.1.6 3.2.6c2.5 0 5.4-4.3 5.4-8.6 0-3.1-1.5-5.7-4.3-6.2-1.5-.3-3.1.1-4.3 1.1z"/><circle cx="5.2" cy="5.2" r="2.6"/><g stroke="currentColor" stroke-width="1.3" stroke-linecap="round"><path d="M5.2 .6v1.1M5.2 8.7v1.1M.6 5.2h1.1M8.7 5.2h1.1M1.9 1.9l.8.8M7.7 7.7l.8.8M1.9 8.5l.8-.8M7.7 2.7l.8-.8"/></g>'),
    "pat": ("Prodotti Agroalimentari Tradizionali (PAT)", "P1 · Logo PAT in verde, senza scritta (2026-11-12)", "Scheda → Varietà e Territori → PAT",
                '<circle cx="12" cy="12" r="11.6" fill="#E3F1DC"/><circle cx="12" cy="12" r="7.9" fill="#2E7D32"/>'),
    "ripening": ("Maturazione", "A · Frutto e orologio", "Scheda → Maturazione; badge climaterico",
                 '<path d="M11 6.2C9.6 5.3 7.5 5 5.8 6 3.3 7.4 2.5 10.8 3.6 14c1.1 3.2 3.4 6 5.8 6 .9 0 1.4-.4 2.6-.4s1.7.4 2.6.4c.8 0 1.6-.3 2.3-.9A6 6 0 0111 6.2z"/><path d="M17.5 9a5.5 5.5 0 110 11 5.5 5.5 0 010-11zm-.8 2v4l3 1.8.8-1.2-2.3-1.4V11z"/><rect x="10.3" y="2" width="1.6" height="4.5" rx=".8"/>'),
    "fridge": ("In Frigorifero", "A · Frigo", "Card, lista spesa, guida conservazione",
               '<path fill-rule="evenodd" d="M7 2h10a2 2 0 012 2v16a2 2 0 01-2 2H7a2 2 0 01-2-2V4a2 2 0 012-2zm0 7v11h10V9zm0-5v3h10V4z"/><rect x="8" y="5" width="1.3" height="1.3" rx=".6"/><rect x="8" y="10.5" width="1.3" height="3" rx=".6"/>'),
    "pantry": ("In Dispensa (Fresco, Asciutto, Buio)", "B · Mensola", "Card, lista spesa, guida conservazione",
               '<rect x="2" y="11" width="20" height="2" rx="1"/><rect x="2" y="20" width="20" height="2" rx="1"/><rect x="4" y="5" width="4" height="6" rx="1"/><circle cx="12.5" cy="8.5" r="2.5"/><rect x="16" y="6" width="4" height="5" rx="2"/><rect x="5" y="15" width="5" height="5" rx="1"/><circle cx="15" cy="17.5" r="2.5"/>'),
    "nutrition": ("Nutrizione", "C · Mela con battito", "Scheda → Nutrizione",
                  '<path fill-rule="evenodd" d="M12 7.2C10.8 6.2 9.3 5.8 7.8 6 4.9 6.4 3.2 9 3.2 12.3c0 4.5 3.1 8.9 5.8 8.9 1.2 0 1.8-.6 3-.6s1.8.6 3 .6c2.7 0 5.8-4.4 5.8-8.9 0-3.3-1.7-5.9-4.6-6.3-1.5-.2-3 .3-4.2 1.4zM5 12.3h2.6l1.4-2.4 2.6 5.6 1.7-3.2H19v1.4h-4.9l-2.6 4.8-2.6-5.6-.6 1z"/>'),
    "carbon": ("Impronta di Carbonio", "A · Nuvola CO₂", "Scheda → Sostenibilità",
               '<path d="M7 19a5 5 0 01-.8-9.9A6.5 6.5 0 0118.6 8 5.5 5.5 0 0118 19z"/>'),
    "water": ("Impronta Idrica", "B · Goccia", "Scheda → Sostenibilità",
              '<path fill-rule="evenodd" d="M12 2s7 7.6 7 12.5A7 7 0 015 14.5C5 9.6 12 2 12 2zm-3 12.5a3 3 0 003 3v-1.6a1.4 1.4 0 01-1.4-1.4z"/>'),
    "cow": ("Mucca (confronto con la carne)", "A · Testa di mucca", "Scheda → Sostenibilità",
            '<path fill-rule="evenodd" d="M4 5c1.6 0 2.8.8 3.5 2h9c.7-1.2 1.9-2 3.5-2 .5 0 1 .1 1.5.3-.4 2.2-2 3.5-4 3.6V13c0 1-.3 1.9-.8 2.7A4.5 4.5 0 0118 19a3 3 0 01-3 3H9a3 3 0 01-3-3c0-1.4.6-2.6 1.5-3.4A5 5 0 016.7 13V8.9C4.6 8.8 3 7.5 2.5 5.3 3 5.1 3.5 5 4 5zm6 14.2a1 1 0 100 2 1 1 0 000-2zm4 0a1 1 0 100 2 1 1 0 000-2zM9.3 11a1.2 1.2 0 100 2.4 1.2 1.2 0 000-2.4zm5.4 0a1.2 1.2 0 100 2.4 1.2 1.2 0 000-2.4z"/>'),
    "zero_waste": ("Antispreco", "B · Due frecce a cerchio", "Scheda → Curiosità e Antispreco",
                   '<path d="M4 11a8 8 0 0114.3-4.9L20 4.5V10h-5.5l2.2-2.2A5.8 5.8 0 006.2 11zm16 2a8 8 0 01-14.3 4.9L4 19.5V14h5.5l-2.2 2.2A5.8 5.8 0 0017.8 13z"/>'),
    "perishability": ("Deperibilità", "A · Clessidra", "Scheda → Conservazione",
                      '<path fill-rule="evenodd" d="M6 2h12v2h-1v3.5c0 1.5-1.2 3.2-3 4.5 1.8 1.3 3 3 3 4.5V20h1v2H6v-2h1v-3.5c0-1.5 1.2-3.2 3-4.5-1.8-1.3-3-3-3-4.5V4H6zm3 2v3.5c0 .9 1.3 2.3 3 3.4 1.7-1.1 3-2.5 3-3.4V4zm3 10c-1.7 1.1-3 2.5-3 3.4V20h6v-2.6c0-.9-1.3-2.3-3-3.4z"/>'),
    "family": ("Famiglia Botanica", "A · Ramo con foglie", "Scheda (link famiglia), pagina Famiglia",
               '<path d="M11 22V12C11 7 8 4 3 3c0 5 2.8 8.2 7 8.9V13c-3.8.3-6.5 2.8-7 6.5 3.9-.2 6.4-2.4 7-5.7V22zm2-8.6c.5-4.7 3.3-7.2 8-7.4-.2 4.6-2.9 7.2-8 7.4z"/>'),
    "scale": ("Calcolo Peso da Comprare", "A · Bilancia", "Lista spesa → Quanto Comprarne",
              '<rect x="11" y="3" width="2" height="16" rx="1"/><rect x="6" y="19" width="12" height="2.5" rx="1.2"/><rect x="3" y="5" width="18" height="1.8" rx=".9"/><path d="M5.5 7L2 14h7zm13 0L15 14h7z" fill-opacity=".55"/><path d="M2 14a3.5 3.5 0 007 0zm13 0a3.5 3.5 0 007 0z"/>'),
    "choose": ("Come Sceglierlo al Meglio", "C2 · Lente con occhio", "Lista spesa, scheda → Come Sceglierlo", LENS_EYE),
    "calendar": ("Calendario Stagionale", "B2 · Calendario con foglia", "Scheda → Calendario Stagionale",
                 '<path fill-rule="evenodd" d="M5 4h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2zm0 5v11h14V9z"/><rect x="7" y="2" width="2" height="4" rx="1"/><rect x="15" y="2" width="2" height="4" rx="1"/><path d="M8.5 18.2c0-3.7 2.5-6.1 7-6.4-.1 4.3-2.5 6.5-5.9 6.5z"/>'),
    "varieties": ("Varietà e Territori", "B2 · Colline, filari e sole", "Scheda → Varietà e Territori", HILLS),
    "ethylene": ("Etilene", "A2 · Frutto e onde", "Avviso Da Tenere Separati, scheda → Maturazione",
                 '<path d="M8 11.3c-1-.7-2.1-.9-3.1-.7C2.6 11 1.2 13.1 1.2 15.8c0 3.6 2.5 6.9 4.7 6.9.9 0 1.4-.5 2.1-.5s1.2.5 2.1.5c2.2 0 4.7-3.3 4.7-6.9 0-2.7-1.4-4.8-3.7-5.2-1-.2-2.1 0-3.1.7z"/><rect x="7.4" y="7.6" width="1.4" height="3.6" rx=".7"/><path d="M15.8 3.5c1.4.9 1.4 2.2 0 3.1s-1.4 2.2 0 3.1M19.2 2c1.4.9 1.4 2.2 0 3.1s-1.4 2.2 0 3.1M22.6 3.5c1.2.8 1.2 2 0 2.8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>'),
    "shopping_mode": ("Modalità Spesa", "C1 · Carrello aperto con campanella (2026-11-12)", "Interruttore Sono a fare la spesa (Home, Lista Spesa), Impostazioni",
                '<g fill="none" stroke="currentColor" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 3.5H4.3L5.6 6.5L8.3 13.5H16.8L20.3 6.5"/><path d="M8.3 13.5L7 16.5H19"/></g><circle cx="8.3" cy="20.2" r="1.8"/><circle cx="17.2" cy="20.2" r="1.8"/><path transform="translate(7.00 -0.40) scale(0.5)" d="M12 2a1.5 1.5 0 011.5 1.5v.6A6.5 6.5 0 0118.5 10.5V15l2 2.5V19h-17v-1.5l2-2.5v-4.5A6.5 6.5 0 0110.5 4.1v-.6A1.5 1.5 0 0112 2zm-2.5 18h5a2.5 2.5 0 01-5 0z"/>'),
    "notifications": ("Notifiche", "B · Campanella", "Impostazioni → Notifiche",
                      '<path d="M12 2a1.5 1.5 0 011.5 1.5v.6A6.5 6.5 0 0118.5 10.5V15l2 2.5V19h-17v-1.5l2-2.5v-4.5A6.5 6.5 0 0110.5 4.1v-.6A1.5 1.5 0 0112 2zm-2.5 18h5a2.5 2.5 0 01-5 0z"/>'),
    "recipes": ("Ricette e Note", "A · Posate incrociate (verde)", "Scheda → Ricette e Note",
                '<path d="M8.1 13.34l2.83-2.83L3.91 3.5a4.008 4.008 0 000 5.66l4.19 4.18zm6.78-1.81c1.53.71 3.68.21 5.27-1.38 1.91-1.91 2.28-4.65.81-6.12-1.46-1.46-4.2-1.1-6.12.81-1.59 1.59-2.09 3.74-1.38 5.27L3.7 19.87l1.41 1.41L12 14.41l6.88 6.88 1.41-1.41L13.41 13l1.47-1.47z"/>'),
    "chilling": ("Danni da Freddo", "A · Fiocco di neve", "Guida conservazione → avviso danni da freddo",
                 '<path d="M22 11h-4.17l3.24-3.24-1.41-1.42L15 11h-2V9l4.66-4.66-1.42-1.41L13 6.17V2h-2v4.17L7.76 2.93 6.34 4.34 11 9v2H9L4.34 6.34 2.93 7.76 6.17 11H2v2h4.17l-3.24 3.24 1.41 1.42L9 13h2v2l-4.66 4.66 1.42 1.41L11 17.83V22h2v-4.17l3.24 3.24 1.42-1.41L13 15v-2h2l4.66 4.66 1.41-1.42L17.83 13H22z"/>'),
    "garden": ("Calendario dell'Orto", "C2 · Vanga simmetrica", "Scheda → Calendario dell'Orto",
               '<rect x="8.5" y="1.5" width="7" height="2.2" rx="1.1"/><rect x="11.2" y="3" width="1.6" height="8" rx=".8"/><path d="M7.8 10.5h8.4v4.3c0 2.3-1.9 4.2-4.2 4.2s-4.2-1.9-4.2-4.2z"/><path d="M2 21.2c3.2-1.5 6.6-1.9 10-1.2s6.8.4 10-.9V23H2z" fill-opacity=".55"/>'),
    "room_temp": ("Temperatura Ambiente", "A4 · Ciotola di frutta", "Card, lista spesa, guida conservazione",
                  '<circle cx="7.6" cy="9.6" r="3.9"/><circle cx="16.4" cy="9.6" r="3.9"/><circle cx="12" cy="6.4" r="3.6"/><ellipse cx="12" cy="9.8" rx="6.5" ry="3.6"/><path d="M1.8 11.4h20.4c0 4.8-3.7 8.8-8.2 8.8h-4c-4.5 0-8.2-4-8.2-8.8z"/>'),
    "sustainability": ("Sostenibilità", "C · Tre foglie in cerchio con nervatura", "Scheda → Sostenibilità",
                       _sustainability()),
}




ROUND2 = [
    ("Sostenibilità (scelta C)", "Con la nervatura centrale in un verde più chiaro.", [
        ("C · definitiva", _sustainability()),
    ]),
]


DOP_SRC = ROOT / "fonti_locali" / "loghi_fonti" / "originali" / "Logo_es_DOP_UE.svg"


def dop_green_svg():
    """Logo ufficiale DOP (livello "DOP" del file UE) senza la scritta
    circolare, rosso → verde scuro, giallo → verde chiarissimo."""
    import re
    t = DOP_SRC.read_text(encoding="utf-8")
    body = t[t.index('<g id="DOP">'): t.rindex("</svg>")]
    els = [m.group(0) for m in re.finditer(r"<(?:path|polygon)[^>]*/>", body, re.S)]
    classes = [re.search(r'class="([^"]*)"', e).group(1) for e in els]
    last_shape = max(i for i, c in enumerate(classes) if c == "st11")  # dopo: lettere della scritta
    keep = els[: last_shape + 1]
    inner = "".join(e.replace('class="st10"', 'fill="#2E7D32"').replace('class="st11"', 'fill="#E3F1DC"') for e in keep)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170.8 170.9">{inner}</svg>'


def europe_body():
    s = (SEASON / "europe.svg").read_text(encoding="utf-8")
    return s[s.index(">") + 1: s.rindex("</svg>")].replace('stroke="#000"', 'stroke="currentColor"')


def write_approved():
    UI.mkdir(parents=True, exist_ok=True)
    (UI / "dop_igp.svg").write_text(dop_green_svg(), encoding="utf-8")
    for name, (_, _, _, body) in APPROVED.items():
        (UI / f"{name}.svg").write_text(
            # currentColor: l'app passa il colore del tema senza appiattire le tonalità (fill-opacity)
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">'
            # (le maschere restano bianche/nere: servono a ritagliare, es. carrello con campanella)
            f'{body if "<mask" in body else body.replace('fill="#fff"', 'fill="currentColor"')}</svg>', encoding="utf-8")


def sheet_html():
    css = """
    body{margin:0;padding:28px 32px;width:1180px;background:#F3F5EE;font-family:Roboto,'Segoe UI',sans-serif;color:#1B1F1B}
    h1{margin:0 0 4px;font-size:26px} p.n{margin:0 0 16px;color:#555;font-size:13px}
    .row{display:flex;gap:14px;align-items:stretch;background:rgba(255,255,255,.75);border:1px solid #fff;border-radius:18px;padding:12px 16px;margin-bottom:10px}
    .head{width:330px;flex:none} .head b{font-size:14px} .head div{font-size:11.5px;color:#555;margin-top:3px}
    .opts{display:flex;gap:18px;flex-wrap:wrap}
    .o{width:200px;text-align:center;font-size:11.5px;color:#333}
    .ic{display:flex;gap:8px;justify-content:center;align-items:center;margin-bottom:6px}
    .big{width:56px;height:56px;border-radius:16px;background:#E3EEDC;display:flex;align-items:center;justify-content:center;color:#1B5E20}
    .big svg{width:38px;height:38px;fill:currentColor}
    .dark{background:#000;color:#A5D6A7}
    .sm{color:#1B5E20} .sm svg{width:18px;height:18px;fill:currentColor}
    """
    out = [f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>",
           "<h1>Icone · sostenibilità definitiva</h1>",
           "<p class='n'>Solo le icone che mi hai chiesto di rifare o che mancano. Le altre sono già approvate (vedi ICONE.md).</p>"]
    for title, note, opts in ROUND2:
        out.append(f"<div class='row'><div class='head'><b>{title}</b><div>{note}</div></div><div class='opts'>")
        for label, body in opts:
            if body is None and title.startswith("DOP"):
                svg = dop_green_svg()
            else:
                svg = f"<svg viewBox='0 0 24 24'>{body or europe_body()}</svg>"
            out.append(f"<div class='o'><div class='ic'><div class='big'>{svg}</div><div class='big dark'>{svg}</div>"
                       f"<div class='sm'>{svg}</div></div>{label}</div>")
        out.append("</div></div>")
    out.append("</body></html>")
    return "".join(out)


def write_markdown():
    rel_season = "../../app/assets/icons/season"
    rel_ui = "../../app/assets/icons/ui"
    rows = [
        ("Primizia", "Set A Crescita", f"{rel_season}/primizie.svg", "Approvata", "Pallini di stagione, calendari, legenda"),
        ("Di Stagione", "Set A Crescita", f"{rel_season}/in_season.svg", "Approvata", "Pallini di stagione, calendari, legenda"),
        ("Picco di Stagione", "Set A Crescita", f"{rel_season}/peak_season.svg", "Approvata", "Pallini, calendari, legenda, icona dell'app"),
        ("Fine Stagione", "Set A Crescita", f"{rel_season}/end_of_season.svg", "Approvata", "Pallini di stagione, calendari, legenda"),
        ("Fuori Stagione / Non Coltivato Qui", "Pallino pieno senza icona", "—", "Approvata", "Calendari (rosso / blu)"),
        ("Dati Non Disponibili", "Pallino grigio con ?", "—", "Approvata", "Calendari, legenda, sezione Senza Dati"),
        ("Frutta", "Mela intera", f"{rel_season}/apple.svg", "Approvata", "Filtro Frutta, segnaposto immagini"),
        ("DOP / IGP", "Logo ufficiale UE in verde, senza scritta", f"{rel_ui}/dop_igp.svg", "Approvata", "Scheda → Varietà e Territori (con la scritta DOP o IGP accanto)"),
        ("Zona Climatica", "Europa reale, blocco pieno", f"{rel_season}/europe.svg", "Approvata", "Impostazioni → Zona Climatica, mappa"),
    ]
    for name, (elem, choice, where, _) in APPROVED.items():
        rows.append((elem, choice, f"{rel_ui}/{name}.svg", "Approvata", where))
    for title, _, opts in ROUND2:
        rows.append((title, " / ".join(o[0] for o in opts), "anteprima", "Approvata", ""))
    lines = [
        "# Peak Season – icone dell'app",
        "",
        "Riferimento unico delle icone. Formato: SVG 24×24 monocromatico, colorato dal tema "
        "(due tonalità di verde con `fill-opacity`). Sorgente: `scripts/icon_library.py`.",
        "",
        "| Elemento | Scelta | File | Stato | Dove si usa |",
        "|---|---|---|---|---|",
    ]
    for elem, choice, path, state, where in rows:
        img = f"![]({path}) `{Path(path).name}`" if path.endswith(".svg") else path
        lines.append(f"| {elem} | {choice} | {img} | {state} | {where} |")
    (SHEET_DIR / "ICONE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    from playwright.sync_api import sync_playwright
    write_approved()
    write_markdown()
    html = sheet_html()
    (SHEET_DIR / "schema_icone_5.html").write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EDGE)
        pg = b.new_page(viewport={"width": 1244, "height": 900}, device_scale_factor=2)
        pg.set_content(html)
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(SHEET_DIR / "schema_icone_5.png"), full_page=True)
        b.close()
    print("ok")


if __name__ == "__main__":
    main()
