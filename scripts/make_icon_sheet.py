"""Tavola delle icone dell'app con le opzioni tra cui scegliere.

Output: schemi_interfaccia/proposte_icone/schema_icone.html e .png
Ogni icona è un SVG 24x24 monocromatico (riempimento = currentColor), lo
stesso formato delle icone delle fasi di stagione già nell'app.
Uso: python scripts/make_icon_sheet.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "schemi_interfaccia" / "proposte_icone"
SEASON = ROOT / "app" / "assets" / "icons" / "season"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

G = '<rect x="5" y="20.5" width="14" height="2" rx="1"/>'  # linea di terra del set "Crescita"


def svg_file(name):
    s = (SEASON / f"{name}.svg").read_text(encoding="utf-8")
    return s[s.index(">") + 1 : s.rindex("</svg>")]


# Ogni voce: (titolo, nota, [(etichetta opzione, svg interno, suggerita_dall_utente)])
SECTIONS = [
    ("Già approvate", [
        ("Fasi di stagione (set A \"Crescita\")", "Approvate: restano così.", [
            ("Primizia", svg_file("primizie"), False),
            ("Di Stagione", svg_file("in_season"), False),
            ("Picco di Stagione", svg_file("peak_season"), False),
            ("Fine Stagione", svg_file("end_of_season"), False),
        ]),
        ("Frutta", "Mela intera (niente marchi).", [("Mela", svg_file("apple"), False)]),
        ("Icona dell'app", "Pianta del picco in grande.", [("Logo", svg_file("peak_season"), False)]),
    ]),
    ("Scheda alimento", [
        ("Come Sceglierlo al Meglio", "Tuo suggerimento: occhio (+ lente).", [
            ("A · Occhio", '<path d="M12 5C6.5 5 2.7 9.2 1.5 12c1.2 2.8 5 7 10.5 7s9.3-4.2 10.5-7C21.3 9.2 17.5 5 12 5zm0 11.5a4.5 4.5 0 110-9 4.5 4.5 0 010 9z"/><circle cx="12" cy="12" r="2.2"/>', True),
            ("B · Lente", '<path d="M10 3a7 7 0 015.6 11.2l5.1 5.1-1.4 1.4-5.1-5.1A7 7 0 1110 3zm0 2.2a4.8 4.8 0 100 9.6 4.8 4.8 0 000-9.6z"/>', True),
            ("C · Lente con occhio", '<path d="M10 3a7 7 0 015.6 11.2l5.1 5.1-1.4 1.4-5.1-5.1A7 7 0 1110 3zm0 3.5c-2.4 0-4 1.8-4.6 3.5.6 1.7 2.2 3.5 4.6 3.5s4-1.8 4.6-3.5C14 8.3 12.4 6.5 10 6.5z"/><circle cx="10" cy="10" r="1.5" fill="#fff"/>', True),
        ]),
        ("Maturazione", "Proposte mie.", [
            ("A · Frutto e orologio", '<path d="M11 6.2C9.6 5.3 7.5 5 5.8 6 3.3 7.4 2.5 10.8 3.6 14c1.1 3.2 3.4 6 5.8 6 .9 0 1.4-.4 2.6-.4s1.7.4 2.6.4c.8 0 1.6-.3 2.3-.9A6 6 0 0111 6.2z"/><path d="M17.5 9a5.5 5.5 0 110 11 5.5 5.5 0 010-11zm-.8 2v4l3 1.8.8-1.2-2.3-1.4V11z"/><rect x="10.3" y="2" width="1.6" height="4.5" rx=".8"/>', False),
            ("B · Frutto mezzo pieno", '<path d="M12 6.5C10.6 5.4 8.9 5 7.4 5.3 4.6 5.8 3 8.4 3 11.7 3 16.2 6.2 21 9 21c1.2 0 1.8-.6 3-.6s1.8.6 3 .6c2.8 0 6-4.8 6-9.3 0-3.3-1.6-5.9-4.4-6.4-1.5-.3-3.2.1-4.6 1.2zm0 2.4c1-.9 2.3-1.3 3.4-1.1 1.6.3 3.1 1.8 3.1 4.6 0 3.3-2.4 6.6-3.5 6.6-.6 0-1.4-.6-3-.6z"/><rect x="11.2" y="1.8" width="1.6" height="4.6" rx=".8"/>', False),
            ("C · Sole e frutto", '<circle cx="17.5" cy="6.5" r="3"/><path d="M10 9.5c-1.1-.8-2.4-1-3.6-.8C4.2 9.1 3 11.1 3 13.6 3 17 5.4 21 7.5 21c.9 0 1.4-.5 2.5-.5s1.6.5 2.5.5c2.1 0 4.5-4 4.5-7.4 0-2.5-1.2-4.5-3.4-4.9-1.2-.2-2.5 0-3.6.8z"/><rect x="17" y="0.8" width="1.2" height="2" rx=".6"/><rect x="21.2" y="6" width="2" height="1.2" rx=".6"/><rect x="20" y="1.9" width="1.2" height="2" rx=".6" transform="rotate(45 20.6 2.9)"/>', False),
        ]),
        ("Temperatura Ambiente", "Tuo suggerimento: una ciotola.", [
            ("A · Ciotola di frutta", '<circle cx="8.5" cy="9" r="3"/><circle cx="14" cy="8" r="3.2"/><circle cx="11.5" cy="5" r="2.2"/><path d="M2 11.5h20c0 4.6-3.6 8.5-8 8.5h-4c-4.4 0-8-3.9-8-8.5z"/>', True),
            ("B · Ciotola vuota", '<path d="M2 10h20c0 5.2-4 9.5-9 9.5h-2c-5 0-9-4.3-9-9.5zm6 11h8v1.5H8z"/>', True),
            ("C · Cesto", '<path d="M3 10h18l-2 10.5H5zm3-1 4.2-5.5 1.3 1L8 9zm12 0-4.2-5.5-1.3 1L16 9z"/><path d="M7 12.5v6M12 12.5v6M17 12.5v6" stroke="#fff" stroke-width="1.4"/>', False),
        ]),
        ("In Frigorifero", "Proposte mie.", [
            ("A · Frigo", '<path d="M7 2h10a2 2 0 012 2v16a2 2 0 01-2 2H7a2 2 0 01-2-2V4a2 2 0 012-2zm0 7v11h10V9zm0-5v3h10V4z"/><rect x="8" y="5" width="1.3" height="1.3" rx=".6"/><rect x="8" y="10.5" width="1.3" height="3" rx=".6"/>', False),
            ("B · Fiocco", '<path d="M11 2h2v4.2l2.6-1.5 1 1.7L13 8.6v2.7l2.3-1.4 3.7-2.1 1 1.7L16.3 11.6 18.6 13l-1 1.7-3.6-2.1-1-.6v2.7l3.6 2.1-1 1.7L13 16.9V22h-2v-5.1l-2.6 1.6-1-1.7 3.6-2.1v-2.7l-1 .6-3.6 2.1-1-1.7L7.7 11.6 4 9.5l1-1.7 3.7 2.1 2.3 1.4V8.6L7.4 6.4l1-1.7L11 6.2z"/>', False),
            ("C · Termometro freddo", '<path d="M10 2a2.5 2.5 0 015 0v11a5 5 0 11-5 0zm2.5 15.5a2 2 0 100-4 2 2 0 000 4z"/><rect x="11.8" y="7" width="1.4" height="7" rx=".7" fill="#fff"/><rect x="17" y="4" width="4" height="1.6" rx=".8"/><rect x="17" y="8" width="3" height="1.6" rx=".8"/>', False),
        ]),
        ("In Dispensa (Fresco, Asciutto, Buio)", "Proposte mie.", [
            ("A · Barattolo", '<rect x="6" y="2" width="12" height="3.5" rx="1"/><path d="M7 6.5h10c1.1 0 2 .9 2 2V20a2 2 0 01-2 2H7a2 2 0 01-2-2V8.5c0-1.1.9-2 2-2zm1.5 6v5h7v-5z"/>', False),
            ("B · Mensola", '<rect x="2" y="11" width="20" height="2" rx="1"/><rect x="2" y="20" width="20" height="2" rx="1"/><rect x="4" y="5" width="4" height="6" rx="1"/><circle cx="12.5" cy="8.5" r="2.5"/><rect x="16" y="6" width="4" height="5" rx="2"/><rect x="5" y="15" width="5" height="5" rx="1"/><circle cx="15" cy="17.5" r="2.5"/>', False),
            ("C · Cassetta e luna", '<path d="M3 11h18v9a2 2 0 01-2 2H5a2 2 0 01-2-2zm3 3v1.6h12V14z"/><path d="M15.5 2.5a4.5 4.5 0 104.5 6 3.6 3.6 0 01-4.5-6z"/>', False),
        ]),
        ("Calendario Stagionale", "Tuo suggerimento: calendario stilizzato.", [
            ("A · Pagina con pallini", '<path d="M5 4h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2zm0 5v11h14V9z"/><rect x="7" y="2" width="2" height="4" rx="1"/><rect x="15" y="2" width="2" height="4" rx="1"/><circle cx="8" cy="12.5" r="1.4"/><circle cx="12" cy="12.5" r="1.4"/><circle cx="16" cy="12.5" r="1.4"/><circle cx="8" cy="16.5" r="1.4"/><circle cx="12" cy="16.5" r="2"/><circle cx="16" cy="16.5" r="1.4"/>', True),
            ("B · Calendario con foglia", '<path d="M5 4h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2zm0 5v11h14V9z"/><rect x="7" y="2" width="2" height="4" rx="1"/><rect x="15" y="2" width="2" height="4" rx="1"/><path d="M8 18.5c0-4 2.8-6.6 8-6.8-.1 4.6-2.8 7.1-6.6 7.1l-.5-.1L8 19.6z"/>', True),
            ("C · Ruota dei 12 mesi", '<circle cx="12" cy="3.5" r="1.6"/><circle cx="16.3" cy="4.6" r="1.6"/><circle cx="19.4" cy="7.7" r="1.6"/><circle cx="20.5" cy="12" r="1.6"/><circle cx="19.4" cy="16.3" r="1.6"/><circle cx="16.3" cy="19.4" r="1.6"/><circle cx="12" cy="20.5" r="2.4"/><circle cx="7.7" cy="19.4" r="1.6"/><circle cx="4.6" cy="16.3" r="1.6"/><circle cx="3.5" cy="12" r="1.6"/><circle cx="4.6" cy="7.7" r="1.6"/><circle cx="7.7" cy="4.6" r="1.6"/>', False),
        ]),
        ("Varietà e Territori", "Tuo suggerimento: colline stilizzate.", [
            ("A · Colline", '<path d="M1 20c2.5-5.5 5.5-8 9-8 2 0 3.6.8 5 2.2C16.6 11.4 18.6 10 21 10c.7 0 1.4.1 2 .3V20z"/><path d="M1 20c3-3 7-4.2 11-3.2 3.7.9 7.4.6 11-1V20z" fill-opacity=".55"/>', True),
            ("B · Colline con filari", '<path d="M1 20c2.5-5.5 5.5-8 9-8 2 0 3.6.8 5 2.2C16.6 11.4 18.6 10 21 10c.7 0 1.4.1 2 .3V20z"/><path d="M5 19.5c2-2.6 4-4 6.4-4.3M8.5 19.8c1.5-2 3.2-3 5-3.2M12.5 20c1.2-1.4 2.6-2.2 4.2-2.4" stroke="#fff" stroke-width="1.2" fill="none" stroke-linecap="round"/><circle cx="18" cy="5" r="2.5"/>', True),
            ("C · Collina con segnaposto", '<path d="M1 21c3-6 6.5-9 10.5-9S19 15 23 21z"/><path d="M12 1.5a4.5 4.5 0 014.5 4.5c0 3.2-4.5 7.5-4.5 7.5S7.5 9.2 7.5 6A4.5 4.5 0 0112 1.5zm0 2.8a1.7 1.7 0 100 3.4 1.7 1.7 0 000-3.4z"/>', False),
        ]),
        ("DOP / IGP", "Tuo suggerimento: accanto al loro logo, stilizzato. Colori dei marchi UE: DOP rosso/giallo, IGP blu/giallo.", [
            ("A · Sigillo DOP", '<circle cx="12" cy="12" r="11" fill="#C8102E"/><circle cx="12" cy="12" r="7.6" fill="#FFD100"/><circle cx="12" cy="12" r="5.6" fill="#C8102E"/><text x="12" y="13.9" font-size="4.6" font-weight="900" text-anchor="middle" fill="#FFD100" font-family="Arial">DOP</text>', True),
            ("B · Sigillo IGP", '<circle cx="12" cy="12" r="11" fill="#003399"/><circle cx="12" cy="12" r="7.6" fill="#FFD100"/><circle cx="12" cy="12" r="5.6" fill="#003399"/><text x="12" y="13.9" font-size="4.6" font-weight="900" text-anchor="middle" fill="#FFD100" font-family="Arial">IGP</text>', True),
            ("C · Coccarda monocroma", '<path d="M12 1l2.2 2 2.9-.6.9 2.8 2.8.9-.6 2.9 2 2.2-2 2.2.6 2.9-2.8.9-.9 2.8-2.9-.6L12 20l-2.2-2-2.9.6-.9-2.8-2.8-.9.6-2.9-2-2.2 2-2.2-.6-2.9 2.8-.9.9-2.8 2.9.6z"/><path d="M8 19l-2 4 3-1 1.5 2 1.5-4.5zM16 19l2 4-3-1-1.5 2-1.5-4.5z"/><path d="M8.2 10.6l2.6 2.6 5-5" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>', False),
        ]),
        ("Nutrizione", "Tuo suggerimento: pilloline.", [
            ("A · Due pillole", '<rect x="1.5" y="8" width="13" height="6" rx="3" transform="rotate(-35 8 11)"/><rect x="11" y="12" width="11" height="5" rx="2.5" transform="rotate(25 16.5 14.5)" fill-opacity=".6"/>', True),
            ("B · Pillola e foglia", '<rect x="2" y="9" width="13" height="6" rx="3" transform="rotate(-35 8.5 12)"/><path d="M13 20c0-5.5 3-8.5 9-9-.2 6-3.4 9-8 9z"/>', True),
            ("C · Mela con battito", '<path d="M12 7.2C10.8 6.2 9.3 5.8 7.8 6 4.9 6.4 3.2 9 3.2 12.3c0 4.5 3.1 8.9 5.8 8.9 1.2 0 1.8-.6 3-.6s1.8.6 3 .6c2.7 0 5.8-4.4 5.8-8.9 0-3.3-1.7-5.9-4.6-6.3-1.5-.2-3 .3-4.2 1.4z"/><path d="M5 13h3l1.5-2.5L12 16l1.8-3H19" stroke="#fff" stroke-width="1.4" fill="none" stroke-linejoin="round"/>', False),
        ]),
        ("Sostenibilità", "Proposte mie.", [
            ("A · Foglia nel cerchio", '<path d="M12 2a10 10 0 110 20 10 10 0 010-20zm0 2a8 8 0 100 16 8 8 0 000-16z"/><path d="M7.5 16.5C7.5 11 10.6 8 16.5 7.5c0 5.9-3 9-8.2 9h-.8z"/>', False),
            ("B · Pianeta con foglia", '<path d="M12 2a10 10 0 016.6 17.5L17 16.6c-.3-.9-.9-1.6-1.8-1.6h-1v-2.5c0-.6-.4-1-1-1H8.5V9.3h2c.6 0 1-.4 1-1V6.6h2a2 2 0 002-2v-.4A8 8 0 0012 4a8 8 0 00-6.8 12.2L10 21.5A10 10 0 0112 2z"/><path d="M14 22c0-4.4 2.4-6.8 7-7-.2 4.6-2.6 7-6.4 7z"/>', False),
            ("C · Impronta con foglia", '<path d="M9 22c-2.8 0-4-2.5-4-6s1.5-7 4-7 3.5 3 3.2 6.6C12 19 11.6 22 9 22z"/><circle cx="6" cy="6" r="1.4"/><circle cx="8.6" cy="4.4" r="1.4"/><circle cx="11.2" cy="5.2" r="1.3"/><path d="M14 12c0-5 3-8 8-8.5-.2 5.3-3 8.3-7.4 8.4z"/>', False),
        ]),
        ("Impronta di Carbonio / Idrica", "Proposte mie (nuove).", [
            ("A · Nuvola CO₂", '<path d="M7 19a5 5 0 01-.8-9.9A6.5 6.5 0 0118.6 8 5.5 5.5 0 0118 19z"/><text x="12.5" y="16.5" font-size="5.5" font-weight="900" text-anchor="middle" fill="#fff" font-family="Arial">CO₂</text>', False),
            ("B · Goccia", '<path d="M12 2s7 7.6 7 12.5A7 7 0 015 14.5C5 9.6 12 2 12 2zm-3 12.5a3 3 0 003 3v-1.6a1.4 1.4 0 01-1.4-1.4z"/>', False),
        ]),
        ("Mucca (confronto con la carne)", "Tuo suggerimento: mucca stilizzata.", [
            ("A · Testa di mucca", '<path d="M4 5c1.6 0 2.8.8 3.5 2h9c.7-1.2 1.9-2 3.5-2 .5 0 1 .1 1.5.3-.4 2.2-2 3.5-4 3.6V13c0 1-.3 1.9-.8 2.7A4.5 4.5 0 0118 19a3 3 0 01-3 3H9a3 3 0 01-3-3c0-1.4.6-2.6 1.5-3.4A5 5 0 016.7 13V8.9C4.6 8.8 3 7.5 2.5 5.3 3 5.1 3.5 5 4 5zm6 14.2a1 1 0 100 2 1 1 0 000-2zm4 0a1 1 0 100 2 1 1 0 000-2zM9.3 11a1.2 1.2 0 100 2.4 1.2 1.2 0 000-2.4zm5.4 0a1.2 1.2 0 100 2.4 1.2 1.2 0 000-2.4z"/>', True),
            ("B · Mucca di profilo", '<path d="M3 9.5c0-1.4 1.1-2.5 2.5-2.5H16l1-2 1.2.6-.6 1.4h1.9c1.4 0 2.5 1.1 2.5 2.5V12h-2v8h-2v-5h-2v5h-2v-5H7v5H5v-5.2A3 3 0 013 12z"/><circle cx="11" cy="10" r="1.6" fill="#fff"/><circle cx="7" cy="12" r="1.2" fill="#fff"/>', True),
        ]),
        ("Antispreco", "Tuo suggerimento: simbolo più stilizzato.", [
            ("A · Freccia circolare con foglia", '<path d="M12 3a9 9 0 018.5 6.1l1.6-.9.4 4.6-4.2-1.9 1.4-.8A6.9 6.9 0 0012 5.1 6.9 6.9 0 005.1 12H3a9 9 0 019-9zm9 9a9 9 0 01-15.6 6.1L3.5 19l.2-4.6 4 2-1.4.8A6.9 6.9 0 0018.9 12z"/><path d="M8.5 15.5c0-4 2.4-6.6 7-7-.2 4.4-2.5 7-5.8 7z"/>', True),
            ("B · Due frecce a cerchio", '<path d="M4 11a8 8 0 0114.3-4.9L20 4.5V10h-5.5l2.2-2.2A5.8 5.8 0 006.2 11zm16 2a8 8 0 01-14.3 4.9L4 19.5V14h5.5l-2.2 2.2A5.8 5.8 0 0017.8 13z"/>', True),
            ("C · Mela con foglia e cuore", '<path d="M12 21s-7.5-4.4-7.5-10A4.4 4.4 0 0112 8.4 4.4 4.4 0 0119.5 11C19.5 16.6 12 21 12 21z"/><path d="M12.5 7.5c.4-2.7 2.2-4.3 5-4.5-.4 2.7-2.2 4.3-5 4.5z"/>', False),
        ]),
        ("Ricette e Note", "Accanto al titolo del blocco.", [
            ("A · Cappello da cuoco", '<path d="M7 18h10v3H7zm12-9.5a4 4 0 01-2 3.5V17H7v-5a4 4 0 012-7.6 4 4 0 016 0A4 4 0 0119 8.5z"/>', False),
            ("B · Forchetta e coltello", '<path d="M6 2h1.4v6h1.2V2H10v6h1.2V2h1.3v7.5a2.5 2.5 0 01-2 2.4V22H8.3V11.9a2.5 2.5 0 01-2-2.4zM17.5 2c1.5 1.6 2.5 4 2.5 7.5V13h-2v9h-2V2z"/>', False),
            ("C · Quaderno con foglia", '<path d="M6 2h12a2 2 0 012 2v16a2 2 0 01-2 2H6a2 2 0 01-2-2V4a2 2 0 012-2zm1 4v1.6h3V6zm0 4v1.6h3V10zm0 4v1.6h3V14z"/><path d="M11.5 17c0-4.7 2.6-7.4 7-7.8-.2 5-2.8 7.8-6.4 7.8z" fill="#fff"/>', False),
        ]),
        ("Calendario dell'Orto", "Tuo suggerimento: terreno arato stilizzato.", [
            ("A · Solchi in prospettiva", '<path d="M2 21L9 9h6l7 12z"/><path d="M12 9v12M10 9l-3.5 12M14 9l3.5 12" stroke="#fff" stroke-width="1.2"/><circle cx="18" cy="5" r="2.5"/>', True),
            ("B · Solchi con germoglio", '<path d="M2 15.5c3-1.5 7-1.5 10 0s7 1.5 10 0v2c-3 1.5-7 1.5-10 0s-7-1.5-10 0zM2 19.5c3-1.5 7-1.5 10 0s7 1.5 10 0V22H2z"/><rect x="11.2" y="9" width="1.6" height="6" rx=".8"/><path d="M12 11c-2.4 0-4-1.6-4-4 2.4 0 4 1.6 4 4zm0-1c0-2.4 1.6-4 4-4 0 2.4-1.6 4-4 4z"/>', True),
            ("C · Vanga e terra", '<path d="M14.6 2.2l1.4-1.4 5.2 5.2-1.4 1.4-1.4-1.4-3.5 3.5 1.2 1.2-4.9 4.9-3.5-3.5 4.9-4.9 1.2 1.2 3.5-3.5z"/><path d="M2 20c3-2 6.5-2.5 10-1.5s7 .5 10-1V22H2z"/>', False),
        ]),
        ("Zona Climatica", "Tuo suggerimento: mappa stilizzata dell'Europa.", [
            ("A · Europa", '<path d="M3.5 16.5l1.6-2.2-.4-2.4 2.4-.8.8-2 2.2.3 1-2.6 1.6-2.2.4-2.6 1.8-1 1 1.6-.6 2 1.2 1.2 2-1.4 1.6 1.4-.6 2.2 1.2 2-1 2.4 1.4 2-1.8 1.2-1.2-1-1 1.6-1.6.4-.6 2.2-1.4-1-.2 2.4-1.2.4-.6-2.8-1.8-.4-.8 1.6-2-.8-1 1.8-2.2-.6z"/>', True),
            ("B · Europa con fasce", '<path d="M3.5 16.5l1.6-2.2-.4-2.4 2.4-.8.8-2 2.2.3 1-2.6 1.6-2.2.4-2.6 1.8-1 1 1.6-.6 2 1.2 1.2 2-1.4 1.6 1.4-.6 2.2 1.2 2-1 2.4 1.4 2-1.8 1.2-1.2-1-1 1.6-1.6.4-.6 2.2-1.4-1-.2 2.4-1.2.4-.6-2.8-1.8-.4-.8 1.6-2-.8-1 1.8-2.2-.6z"/><path d="M2 8h20M2 13h20" stroke="#fff" stroke-width="1.2"/>', True),
            ("C · Termometro e mappa", '<path d="M3 5l5-2 8 3 5-2v15l-5 2-8-3-5 2z" fill-opacity=".45"/><path d="M10.5 6a2 2 0 014 0v8.5a4 4 0 11-4 0z"/>', False),
        ]),
    ]),
    ("Altre icone (proposte mie, nuove)", [
        ("Etilene", "Per l'avviso incompatibilità e la sezione maturazione.", [
            ("A · Onde dal frutto", '<path d="M9 10c-1-.7-2.1-.9-3.2-.7C3.4 9.7 2 11.9 2 14.7 2 18.5 4.6 22 6.9 22c1 0 1.5-.5 2.1-.5s1.1.5 2.1.5c2.3 0 4.9-3.5 4.9-7.3 0-2.8-1.4-5-3.8-5.4-1.1-.2-2.2 0-3.2.7z"/><path d="M15 4c1.5 1 1.5 2.4 0 3.4s-1.5 2.4 0 3.4M18.5 2.5c1.5 1 1.5 2.4 0 3.4s-1.5 2.4 0 3.4M22 4c1.5 1 1.5 2.4 0 3.4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>', False),
            ("B · Molecola", '<circle cx="8" cy="12" r="3"/><circle cx="16" cy="12" r="3"/><path d="M10 10.8h4M10 13.2h4" stroke="currentColor" stroke-width="1.3"/><circle cx="4" cy="7" r="1.6"/><circle cx="4" cy="17" r="1.6"/><circle cx="20" cy="7" r="1.6"/><circle cx="20" cy="17" r="1.6"/><path d="M5 8l1.5 2M5 16l1.5-2M19 8l-1.5 2M19 16l-1.5-2" stroke="currentColor" stroke-width="1.3"/>', False),
        ]),
        ("Deperibilità", "Quanto dura.", [
            ("A · Clessidra", '<path d="M6 2h12v2h-1v3.5c0 1.5-1.2 3.2-3 4.5 1.8 1.3 3 3 3 4.5V20h1v2H6v-2h1v-3.5c0-1.5 1.2-3.2 3-4.5-1.8-1.3-3-3-3-4.5V4H6zm3 2v3.5c0 .9 1.3 2.3 3 3.4 1.7-1.1 3-2.5 3-3.4V4zm3 10c-1.7 1.1-3 2.5-3 3.4V20h6v-2.6c0-.9-1.3-2.3-3-3.4z"/>', False),
            ("B · Timer", '<rect x="9" y="1" width="6" height="2" rx="1"/><path d="M12 4a9 9 0 110 18 9 9 0 010-18zm-1 4v6l4.5 2.6 1-1.7L13 13V8z"/>', False),
        ]),
        ("Danni da Freddo", "Avviso per chi non va in frigo.", [
            ("A · Fiocco barrato", '<path d="M11 2h2v20h-2zM2 11h20v2H2zM4.9 6.3l1.4-1.4 12.8 12.8-1.4 1.4zm12.8-1.4l1.4 1.4L6.3 19.1l-1.4-1.4z" fill-opacity=".55"/><path d="M3 3l18 18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>', False),
            ("B · Termometro con avviso", '<path d="M6 2a2.5 2.5 0 015 0v11a5 5 0 11-5 0z"/><path d="M17.5 4l5 9h-10z"/><rect x="16.8" y="7" width="1.4" height="3" rx=".7" fill="#fff"/><circle cx="17.5" cy="11.2" r=".8" fill="#fff"/>', False),
        ]),
        ("Famiglia Botanica", "Link alla lista della stessa famiglia.", [
            ("A · Ramo con foglie", '<path d="M11 22V12C11 7 8 4 3 3c0 5 2.8 8.2 7 8.9V13c-3.8.3-6.5 2.8-7 6.5 3.9-.2 6.4-2.4 7-5.7V22zm2-8.6c.5-4.7 3.3-7.2 8-7.4-.2 4.6-2.9 7.2-8 7.4z"/>', False),
            ("B · Albero genealogico", '<circle cx="12" cy="4" r="2.5"/><circle cx="5" cy="19" r="2.5"/><circle cx="12" cy="19" r="2.5"/><circle cx="19" cy="19" r="2.5"/><path d="M12 6.5V16M12 11H5v5.5M12 11h7v5.5" stroke="currentColor" stroke-width="1.6" fill="none"/>', False),
        ]),
        ("Calcolo Peso da Comprare", "Lista della spesa.", [
            ("A · Bilancia", '<rect x="11" y="3" width="2" height="16" rx="1"/><rect x="6" y="19" width="12" height="2.5" rx="1.2"/><rect x="3" y="5" width="18" height="1.8" rx=".9"/><path d="M5.5 7L2 14h7zm13 0L15 14h7z" fill-opacity=".7"/><path d="M2 14a3.5 3.5 0 007 0zm13 0a3.5 3.5 0 007 0z"/>', False),
            ("B · Peso", '<path d="M9.5 6a2.5 2.5 0 115 0c0 .4-.1.7-.2 1h3.2c.9 0 1.6.6 1.8 1.4l2.4 11A2 2 0 0119.8 22H4.2a2 2 0 01-1.9-2.6l2.4-11C4.9 7.6 5.6 7 6.5 7h3.2c-.1-.3-.2-.6-.2-1z"/>', False),
        ]),
        ("Modalità Spesa / Notifiche", "Carrello e campanella.", [
            ("A · Carrello con foglia", '<path d="M1 3h3.2l2.6 11.2c.2.8.9 1.3 1.7 1.3H18c.8 0 1.5-.5 1.7-1.3L21.6 7H6.4L5.8 4.6 5.4 3zm8 15a2 2 0 110 4 2 2 0 010-4zm8 0a2 2 0 110 4 2 2 0 010-4z"/><path d="M10 13c0-3 1.7-4.6 5-4.8-.1 3.1-1.7 4.8-4.4 4.8z" fill="#fff"/>', False),
            ("B · Campanella con foglia", '<path d="M12 2a1.5 1.5 0 011.5 1.5v.6A6.5 6.5 0 0118.5 10.5V15l2 2.5V19h-17v-1.5l2-2.5v-4.5A6.5 6.5 0 0110.5 4.1v-.6A1.5 1.5 0 0112 2zm-2.5 18h5a2.5 2.5 0 01-5 0z"/><path d="M9 14c0-3 1.7-4.6 5-4.8-.1 3.1-1.7 4.8-4.4 4.8z" fill="#fff"/>', False),
        ]),
    ]),
]


def html():
    css = """
    body{margin:0;padding:28px 32px;width:1180px;background:#F3F5EE;font-family:Roboto,'Segoe UI',sans-serif;color:#1B1F1B}
    h1{margin:0 0 4px;font-size:26px} h2{margin:26px 0 10px;font-size:19px}
    p.n{margin:0 0 16px;color:#555;font-size:13px}
    .row{display:flex;gap:14px;align-items:stretch;background:rgba(255,255,255,.75);border:1px solid #fff;border-radius:18px;padding:12px 16px;margin-bottom:10px}
    .head{width:250px;flex:none} .head b{font-size:14px} .head div{font-size:11.5px;color:#666;margin-top:3px}
    .opts{display:flex;gap:14px;flex-wrap:wrap}
    .o{width:150px;text-align:center;font-size:11.5px;color:#333;position:relative}
    .ic{display:flex;gap:8px;justify-content:center;align-items:center;margin-bottom:6px}
    .big{width:52px;height:52px;border-radius:16px;background:#E3EEDC;display:flex;align-items:center;justify-content:center;color:#1B5E20}
    .big svg{width:34px;height:34px;fill:currentColor}
    .dark{background:#000;color:#A5D6A7}
    .sm svg{width:18px;height:18px;fill:#1B5E20}
    .star{position:absolute;top:-4px;right:18px;background:#FFB300;color:#fff;border-radius:8px;font-size:9.5px;padding:1px 5px;font-weight:700}
    """
    parts = [f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>",
             "<h1>Peak Season – icone dell'app</h1>",
             "<p class='n'>Per ogni elemento: anteprima grande (chiaro e scuro) e alla misura reale (18 px). "
             "<span style='background:#FFB300;color:#fff;border-radius:8px;padding:1px 6px;font-weight:700;font-size:11px'>tuo</span> "
             "= opzione che segue un tuo suggerimento. Rispondimi con la lettera scelta per ogni riga (es. \"Come Sceglierlo: A\").</p>"]
    for section, rows in SECTIONS:
        parts.append(f"<h2>{section}</h2>")
        for title, note, opts in rows:
            parts.append(f"<div class='row'><div class='head'><b>{title}</b><div>{note}</div></div><div class='opts'>")
            for label, body, mine in opts:
                svg = f"<svg viewBox='0 0 24 24'>{body}</svg>"
                star = "<span class='star'>tuo</span>" if mine else ""
                parts.append(
                    f"<div class='o'>{star}<div class='ic'><div class='big'>{svg}</div><div class='big dark'>{svg}</div>"
                    f"<div class='sm'>{svg}</div></div>{label}</div>")
            parts.append("</div></div>")
    parts.append("</body></html>")
    return "".join(parts)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    page_html = html()
    (OUT / "schema_icone.html").write_text(page_html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EDGE)
        pg = b.new_page(viewport={"width": 1244, "height": 900}, device_scale_factor=2)
        pg.set_content(page_html)
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(OUT / "schema_icone.png"), full_page=True)
        b.close()
    print("ok", OUT / "schema_icone.png")


if __name__ == "__main__":
    main()
