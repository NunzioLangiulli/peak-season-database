"""Review page for candidate images: assets/images/_candidates/review.html (opens in the browser, offline).

For each product it shows the current photos (with type and flagged issues) and, for each of the 5 types, the candidates
found by find_image_candidates.py. Choose with a click: candidates to add and current photos to remove.
Choices are saved in the browser; the "Esporta scelte" (export choices) button downloads image_selection.json, to put in
assets/images/_candidates/ and apply with apply_image_selection.py.
Usage:  python scripts/make_candidates_review.py
"""
import html
import json

from common import DATA, IMAGES, load_json
from find_image_candidates import db_path

OUT = IMAGES / "_candidates"
TYPES = [("full_frame", "Prodotto a tutto campo (principale)"), ("isolated_background", "Sfondo bianco o colorato"),
         ("plant_in_field", "Pianta"), ("botanical_plate", "Tavola botanica"), ("cut_section", "Tagliato / sezione")]
LABEL = dict(TYPES) | {"other": "Altro (natura morta, mercato…)"}
FLAG = {"dish": "piatto/ciotola", "wrong_item": "soggetto sbagliato"}

CSS = """
:root{--bg:#fafaf7;--fg:#1d1d1b;--mut:#6b6b66;--card:#fff;--line:#e3e2dc;--ok:#2f7d32;--no:#b3261e;--acc:#355e3b}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe6;--mut:#a3a29c;--card:#22221f;--line:#3a3934;--ok:#7cc47f;--no:#f28b82;--acc:#9fc5a3}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
header h1{font-size:16px;margin:0 12px 0 0}button,select,input{font:inherit;padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);cursor:pointer}
button.primary{background:var(--acc);color:var(--bg);border-color:var(--acc)}#stat{color:var(--mut)}
main{padding:12px 16px;max-width:1500px;margin:auto}section.item{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:14px 0;padding:10px 14px}
section.item h2{font-size:17px;margin:4px 0 8px}section.item h2 small{color:var(--mut);font-weight:400}
.row{display:flex;gap:10px;align-items:flex-start;margin:6px 0 10px;flex-wrap:wrap}.rowlab{width:170px;flex:none;color:var(--mut);font-size:13px;padding-top:4px}
.rowlab b{display:block;color:var(--fg)}.none{color:var(--mut);font-style:italic;padding-top:4px}
figure{margin:0;width:230px;flex:none;border:2px solid transparent;border-radius:8px;padding:3px;cursor:pointer;position:relative}
figure img{width:100%;height:150px;object-fit:contain;background:#00000010;border-radius:5px;display:block}
figcaption{font-size:11px;color:var(--mut);margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
figure.pick{border-color:var(--ok)}figure.pick::after{content:"✓ aggiungi";position:absolute;top:8px;left:8px;background:var(--ok);color:#fff;font-size:12px;padding:1px 6px;border-radius:4px}
figure.cur.drop{border-color:var(--no);opacity:.55}figure.cur.drop::after{content:"✕ togli";position:absolute;top:8px;left:8px;background:var(--no);color:#fff;font-size:12px;padding:1px 6px;border-radius:4px}
.tag{display:inline-block;font-size:11px;border-radius:4px;padding:0 5px;margin-right:4px;background:var(--line);color:var(--fg)}.tag.bad{background:var(--no);color:#fff}
a{color:var(--acc)}
"""

JS = """
const KEY='peakseason_image_selection_v1';
let sel={};try{sel=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){sel={}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(sel))}catch(e){};stat()}
function stat(){let a=0,r=0;for(const k in sel){a+=(sel[k].add||[]).length;r+=(sel[k].remove||[]).length}
document.getElementById('stat').textContent=`scelte: ${a} da aggiungere, ${r} da togliere`}
function toggle(el){const it=el.dataset.item,f=el.dataset.file,kind=el.classList.contains('cur')?'remove':'add';
sel[it]=sel[it]||{add:[],remove:[]};const L=sel[it][kind],i=L.indexOf(f);
if(i>=0){L.splice(i,1);el.classList.remove(kind=='add'?'pick':'drop')}else{L.push(f);el.classList.add(kind=='add'?'pick':'drop')}save()}
document.querySelectorAll('figure[data-file]').forEach(el=>{const s=sel[el.dataset.item]||{};
if(el.classList.contains('cur')&&(s.remove||[]).includes(el.dataset.file))el.classList.add('drop');
if(!el.classList.contains('cur')&&(s.add||[]).includes(el.dataset.file))el.classList.add('pick');
el.addEventListener('click',e=>{if(e.target.tagName!='A')toggle(el)})});
document.getElementById('exp').onclick=()=>{const b=new Blob([JSON.stringify({exported:new Date().toISOString(),items:sel},null,1)],{type:'application/json'});
const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='image_selection.json';a.click()};
document.getElementById('flt').onchange=e=>{const v=e.target.value;document.querySelectorAll('section.item').forEach(s=>{
s.style.display=(v=='all'||(v=='gap'&&s.dataset.gap=='1')||(v=='few'&&+s.dataset.n<3))?'':'none'})};
document.getElementById('q').oninput=e=>{const v=e.target.value.toLowerCase();document.querySelectorAll('section.item').forEach(s=>{s.style.display=s.dataset.name.includes(v)?'':'none'})};
stat();
"""


def fig(item, file, src, cap, cur=False, extra=""):
    return (f'<figure class="{"cur" if cur else "cand"}" data-item="{item}" data-file="{html.escape(file)}">'
            f'<img loading="lazy" src="{html.escape(src)}" alt=""><figcaption>{extra}{cap}</figcaption></figure>')


def main():
    db = load_json(db_path())
    cand = load_json(OUT / "candidates.json")["items"]
    parts = []
    for it in db["items"]:
        iid = it["id"]
        cur = it["images"]["image_details"]
        have = {d["view_type"] for d in cur if not d.get("flags")}
        gap = any(t not in have and not cand.get(iid, {}).get(t) for t, _ in TYPES[:3])
        rows = []
        cf = []
        for d in cur:
            tags = f'<span class="tag">{LABEL.get(d["view_type"], d["view_type"])}</span>' + "".join(
                f'<span class="tag bad">{FLAG[f]}</span>' for f in d.get("flags", []))
            if d.get("variety"):
                tags += f'<span class="tag">{html.escape(d["variety"]["it"])}</span>'
            prim = " · principale" if d["filename"] == it["images"]["primary"] else ""
            cf.append(fig(iid, d["filename"], "../" + d["filename"], f'{d["filename"]}{prim} · {d.get("width")}×{d.get("height")}', True, tags + "<br>"))
        rows.append(f'<div class="row"><div class="rowlab"><b>Foto attuali</b>clic = togli</div>{"".join(cf) or "<div class=none>nessuna</div>"}</div>')
        for t, lab in TYPES:
            lst = cand.get(iid, {}).get(t, [])
            figs = "".join(fig(iid, h["file"], h["file"],
                               f'<a href="{html.escape(h["source_url"])}" target="_blank" rel="noopener">{h["provider"].replace("wikimedia_commons", "Commons").replace("pixabay", "Pixabay")}</a>'
                               f' · {h["w"]}×{h["h"]} · {html.escape(h["license"])}') for h in lst)
            n_have = sum(1 for d in cur if d["view_type"] == t and not d.get("flags"))
            rows.append(f'<div class="row"><div class="rowlab"><b>{lab}</b>attuali: {n_have} · candidate: {len(lst)}</div>'
                        f'{figs or "<div class=none>nessuna candidata trovata</div>"}</div>')
        name = f'{it["names"]["it"]} {it["names"]["en"]} {iid}'.lower()
        parts.append(f'<section class="item" id="{iid}" data-gap="{int(gap)}" data-n="{len(cur)}" data-name="{html.escape(name)}">'
                     f'<h2>{html.escape(it["names"]["it"])} <small>{html.escape(it["names"]["en"])} · {html.escape(it["botany"]["scientific_name"] or "")}</small></h2>'
                     + "".join(rows) + "</section>")
    page = (f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Revisione immagini</title><style>{CSS}</style></head><body>'
            '<header><h1>Peak Season · revisione immagini</h1>'
            '<input id="q" placeholder="cerca alimento"><select id="flt"><option value="all">tutti</option>'
            '<option value="few">meno di 3 foto attuali</option><option value="gap">con tipi senza candidate</option></select>'
            '<span id="stat"></span><button class="primary" id="exp">Esporta scelte</button></header><main>'
            '<p>Clic su una candidata per aggiungerla (bordo verde), clic su una foto attuale per toglierla (bordo rosso). '
            'Le scelte restano salvate in questo browser. Alla fine premi <b>Esporta scelte</b> e metti il file '
            '<code>image_selection.json</code> nella cartella <code>assets/images/_candidates/</code>.</p>'
            + "".join(parts) + f"</main><script>{JS}</script></body></html>")
    (OUT / "review.html").write_text(page, encoding="utf-8")
    print("wrote", OUT / "review.html", "|", len(parts), "products")


if __name__ == "__main__":
    main()
