"""Genera assets/images/_review.html: galleria locale di tutte le foto per alimento, con autore, licenza,
fonte e tipo di vista, per scegliere quali tenere. Elimina dalla cartella i file che non vuoi e poi esegui
python scripts/sync_images.py --renumber --prune
Uso:  python scripts/make_image_review.py
"""
import html

from common import DATA, IMAGES, load_json

db = load_json(DATA / "database.json")
meta = load_json(IMAGES / "_metadata.json")
rows = []
for it in db["items"]:
    files = sorted(k for k in meta if k.startswith(it["id"] + "_") and (IMAGES / k).exists())
    cells = "".join(
        f'<figure><img src="{f}" loading="lazy"><figcaption><b>{f}</b><br>{html.escape(meta[f]["view_type"])} · '
        f'{html.escape(meta[f]["provider"])}<br>{html.escape(meta[f]["author"][:60])}<br>'
        f'<a href="{html.escape(meta[f]["source_url"])}" target="_blank">{html.escape(meta[f]["license"])}</a></figcaption></figure>'
        for f in files) or "<p class=none>Nessuna immagine</p>"
    rows.append(f'<section><h2>{html.escape(it["names"]["it"])} <small>{it["id"]}</small></h2><div class=g>{cells}</div></section>')
page = f"""<!doctype html><meta charset=utf-8><title>Peak Season - revisione immagini</title>
<style>body{{font:14px system-ui;margin:16px;background:#fafafa}}h2{{font-size:16px;margin:18px 0 6px}}small{{color:#777;font-weight:400}}
.g{{display:flex;flex-wrap:wrap;gap:10px}}figure{{margin:0;width:240px;background:#fff;border:1px solid #ddd;border-radius:6px;overflow:hidden}}
img{{width:240px;height:170px;object-fit:cover;display:block}}figcaption{{padding:6px;font-size:12px;line-height:1.35}}.none{{color:#b00}}</style>
<h1>Revisione immagini ({sum(1 for k in meta if (IMAGES / k).exists())} foto)</h1>
<p>Elimina da <code>assets/images/</code> le foto che non vuoi, poi esegui <code>python scripts/sync_images.py --renumber --prune</code>.</p>
{''.join(rows)}"""
(IMAGES / "_review.html").write_text(page, encoding="utf-8")
print("scritto", IMAGES / "_review.html")
