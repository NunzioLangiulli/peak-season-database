// Schede dei testi: Testi App (data/ui_copy.json), Corpus Condiviso e Descrizioni Prodotti (data/database.json).
const Copy = {D: null, changed: {ui: new Set(), corpus: new Set(), items: new Set()}, limit: 150};

Copy.load = async () => {
  Copy.D = await api.get('/api/copy');
  for (const k in Copy.changed) Copy.changed[k].clear();
};
Copy.resolve = v => {
  if (!v) return {it: '', en: ''};
  if (v.corpus_ref !== undefined) {
    const b = Copy.D.corpus[v.corpus_ref] || {it: '', en: ''}, a = v.specific_addition;
    return {it: (b.it + (a ? ' ' + a.it : '')).trim(), en: (b.en + (a ? ' ' + a.en : '')).trim()};
  }
  return v;
};
Copy.usage = () => {
  const u = {};
  Copy.D.items.forEach(it => it.fields.forEach(f => { const r = f.value.corpus_ref; if (r !== undefined) (u[r] = u[r] || new Set()).add(it.name); }));
  return u;
};
Copy.mark = (t, id, row) => { Copy.changed[t].add(id); if (row) row.classList.add('changed'); refreshDirty(); };
Copy.ta = (val, on) => {
  const t = document.createElement('textarea'); t.value = val ?? '';
  t.rows = Math.min(6, Math.max(1, Math.ceil((val || '').length / 70))); t.oninput = () => on(t.value); return t;
};
Copy.field = (lbl, val, on) => { const d = document.createElement('div'); d.innerHTML = '<label class="l">' + lbl + '</label>'; d.append(Copy.ta(val, on)); return d; };
Copy.pair = (obj, onchg) => {
  const p = document.createElement('div'); p.className = 'pair';
  p.append(Copy.field('Italiano', obj.it, v => { obj.it = v; onchg(); }), Copy.field('English', obj.en, v => { obj.en = v; onchg(); }));
  return p;
};
Copy.more = (m, n) => {
  if (n > Copy.limit) {
    const d = document.createElement('div'); d.className = 'more';
    d.innerHTML = 'Mostrati ' + Copy.limit + ' di ' + n + ' · <button class="btn">Mostra altri</button>';
    d.querySelector('button').onclick = () => { Copy.limit += 300; render(); }; m.append(d);
  } else if (!n) m.insertAdjacentHTML('beforeend', '<div class="empty">Nessun risultato</div>');
};
Copy.save = async () => {
  const c = Copy.changed, D = Copy.D;
  for (const k of c.corpus) { const v = D.corpus[k]; if (!v.it.trim() || !v.en.trim()) return msg('La voce del corpus "' + k + '" ha un testo vuoto: compila italiano e inglese.', true); }
  const body = {ui: c.ui.size ? D.ui : null, corpus: c.corpus.size ? D.corpus : null, item_changes: []};
  for (const id of c.items) {
    const [iid, j] = id.split('|'), f = D.items.find(x => x.id === iid).fields[+j];
    body.item_changes.push({id: iid, path: f.path, value: f.value});
  }
  const res = await api.post('/api/copy/save', body);
  if (await afterSave(res, 'Modifiche ai testi')) { await Copy.load(); render(); }
};
Copy.dirty = () => Copy.changed.ui.size + Copy.changed.corpus.size + Copy.changed.items.size;

// ---------- CSV (separatore ";", BOM per Excel)
Copy.cq = v => { v = String(v ?? ''); return /[;"\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
Copy.parseCSV = t => {
  t = t.replace(/^﻿/, ''); const h = t.split('\n')[0];
  const d = h.split(';').length >= h.split(',').length ? ';' : ','; const R = []; let r = [], f = '', Q = false;
  for (let i = 0; i < t.length; i++) {
    const c = t[i];
    if (Q) { if (c === '"') { if (t[i + 1] === '"') { f += '"'; i++; } else Q = false; } else f += c; }
    else if (c === '"') Q = true; else if (c === d) { r.push(f); f = ''; }
    else if (c === '\n') { r.push(f.replace(/\r$/, '')); R.push(r); r = []; f = ''; } else f += c;
  }
  if (f || r.length) { r.push(f.replace(/\r$/, '')); R.push(r); }
  return R;
};
Copy.exportCSV = (tab, rows) => {
  const csv = '﻿' + rows.map(r => r.map(Copy.cq).join(';')).join('\r\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], {type: 'text/csv'}));
  a.download = 'peakseason_' + tab + '.csv'; a.click();
};

// ---------- Testi App
Studio.tabs.ui = {
  placeholder: 'Cerca in schermate, chiavi, descrizioni e testi…', csv: true, load: Copy.load, dirty: Copy.dirty, save: Copy.save,
  render(m, q) {
    const S = Copy.D.ui.strings || [], nq = norm(q);
    if (!S.length) { m.innerHTML = '<div class="empty">data/ui_copy.json non esiste ancora o è vuoto.</div>'; return; }
    const rows = S.map((s, i) => [s, i]).filter(([s]) => !nq || norm([s.screen, s.key, s.element_description, s.it, s.en].join(' ')).includes(nq));
    rows.slice(0, Copy.limit).forEach(([s, i]) => {
      const r = document.createElement('div'); r.className = 'row' + (Copy.changed.ui.has(i) ? ' changed' : '');
      r.innerHTML = '<div class="meta"><span>Schermata: <b>' + esc(s.screen) + '</b></span><span>Chiave: <b>' + esc(s.key) + '</b></span><span>' + esc(s.element_description) + '</span></div>';
      r.append(Copy.pair(s, () => Copy.mark('ui', i, r))); m.append(r);
    });
    Copy.more(m, rows.length);
  },
  rows: () => [['screen', 'key', 'element_description', 'it', 'en'], ...(Copy.D.ui.strings || []).map(s => [s.screen, s.key, s.element_description, s.it, s.en])],
  import(H, R) {
    const ix = n => H.indexOf(n); if (ix('key') < 0) throw 'serve la colonna "key"';
    const by = {}; (Copy.D.ui.strings || []).forEach((s, i) => by[s.key] = i); let n = 0, miss = 0;
    R.forEach(r => {
      const i = by[r[ix('key')]]; if (i === undefined) { if (r[ix('key')]) miss++; return; }
      const s = Copy.D.ui.strings[i];
      if (s.it !== r[ix('it')] || s.en !== r[ix('en')]) { s.it = r[ix('it')]; s.en = r[ix('en')]; Copy.changed.ui.add(i); n++; }
    });
    return [n, miss];
  },
};

// ---------- Corpus Condiviso
Studio.tabs.corpus = {
  placeholder: 'Cerca in chiavi, testi e prodotti collegati…', csv: true, dirty: Copy.dirty, save: Copy.save,
  render(m, q) {
    const D = Copy.D, u = Copy.usage(), nq = norm(q);
    const keys = Object.keys(D.corpus).filter(k => !nq || norm(k + ' ' + D.corpus[k].it + ' ' + D.corpus[k].en + ' ' + [...(u[k] || [])].join(' ')).includes(nq));
    const add = document.createElement('div'); add.className = 'row';
    add.innerHTML = '<b>Nuova voce del corpus</b> <input type="text" id="nk" placeholder="chiave_parlante (minuscole, numeri, _)" style="width:320px"> <button class="btn" id="nb">Aggiungi</button>';
    m.append(add);
    $('#nb').onclick = () => {
      const k = $('#nk').value.trim();
      if (!/^[a-z0-9_]+$/.test(k) || D.corpus[k]) return alert('Chiave non valida o già esistente');
      D.corpus[k] = {it: '', en: ''}; Copy.mark('corpus', k); Studio.q = k; $('#q').value = k; render();
    };
    keys.slice(0, Copy.limit).forEach(k => {
      const r = document.createElement('div'); r.className = 'row' + (Copy.changed.corpus.has(k) ? ' changed' : ''); const us = [...(u[k] || [])];
      r.innerHTML = '<div class="meta"><span>Chiave: <b>' + esc(k) + '</b></span><span>Usata da <b>' + us.length + '</b> prodotti</span></div>';
      r.append(Copy.pair(D.corpus[k], () => Copy.mark('corpus', k, r)));
      const c = document.createElement('div'); c.className = 'chips'; c.innerHTML = us.sort().map(n => '<span class="chip">' + esc(n) + '</span>').join('');
      r.append(c); m.append(r);
    });
    Copy.more(m, keys.length);
  },
  rows() { const u = Copy.usage(), D = Copy.D; return [['key', 'it', 'en', 'used_by'], ...Object.keys(D.corpus).map(k => [k, D.corpus[k].it, D.corpus[k].en, [...(u[k] || [])].join(', ')])]; },
  import(H, R) {
    const ix = n => H.indexOf(n); if (ix('key') < 0) throw 'serve la colonna "key"'; let n = 0, miss = 0;
    R.forEach(r => {
      const k = r[ix('key')]; if (!k) return; if (!/^[a-z0-9_]+$/.test(k)) { miss++; return; }
      const v = Copy.D.corpus[k] || (Copy.D.corpus[k] = {it: '', en: ''});
      if (v.it !== r[ix('it')] || v.en !== r[ix('en')]) { v.it = r[ix('it')]; v.en = r[ix('en')]; Copy.changed.corpus.add(k); n++; }
    });
    return [n, miss];
  },
};

// ---------- Descrizioni Prodotti
Studio.tabs.items = {
  placeholder: 'Cerca prodotto, campo o testo…', csv: true, dirty: Copy.dirty, save: Copy.save,
  render(m, q) {
    const D = Copy.D, nq = norm(q), opts = Object.keys(D.corpus).sort(); let shown = 0, total = 0;
    D.items.forEach(it => {
      const fs = it.fields.map((f, j) => [f, j]).filter(([f]) => {
        if (!nq) return true; const t = Copy.resolve(f.value);
        return norm(it.name + ' ' + it.id + ' ' + f.path.join('.') + ' ' + t.it + ' ' + t.en + ' ' + (f.value.corpus_ref || '')).includes(nq);
      });
      if (!fs.length) return; total += fs.length; if (shown >= Copy.limit) return;
      const h = document.createElement('div'); h.className = 'prod'; h.textContent = it.name + '  ·  ' + it.id; m.append(h);
      fs.forEach(([f, j]) => {
        if (shown++ >= Copy.limit) return;
        const id = it.id + '|' + j, r = document.createElement('div'); r.className = 'row' + (Copy.changed.items.has(id) ? ' changed' : '');
        const dirty = () => Copy.mark('items', id, r);
        const draw = () => {
          r.innerHTML = '<div class="meta"><span>Campo: <b>' + esc(f.path.filter(x => typeof x === 'string').join(' › ')) + '</b></span></div>';
          const sel = document.createElement('select');
          sel.innerHTML = '<option value="">— Testo specifico di questo prodotto —</option>' + opts.map(k => '<option' + (k === f.value.corpus_ref ? ' selected' : '') + '>' + esc(k) + '</option>').join('');
          sel.onchange = () => { const full = Copy.resolve(f.value); f.value = sel.value ? {corpus_ref: sel.value} : {it: full.it, en: full.en}; dirty(); draw(); };
          const sl = document.createElement('div'); sl.className = 'meta'; sl.append('Voce del corpus: ', sel); r.append(sl);
          if (f.value.corpus_ref !== undefined) {
            const b = D.corpus[f.value.corpus_ref] || {};
            const bd = document.createElement('div'); bd.className = 'pair'; bd.innerHTML = '<div class="base">' + esc(b.it) + '</div><div class="base">' + esc(b.en) + '</div>'; r.append(bd);
            const add = f.value.specific_addition || {it: '', en: ''};
            const lab = document.createElement('label'); lab.className = 'l'; lab.style.marginTop = '6px'; lab.textContent = 'Aggiunta specifica (facoltativa, va dopo il testo del corpus)'; r.append(lab);
            r.append(Copy.pair(add, () => { if (add.it || add.en) f.value.specific_addition = add; else delete f.value.specific_addition; dirty(); }));
          } else r.append(Copy.pair(f.value, dirty));
        };
        draw(); m.append(r);
      });
    });
    Copy.more(m, total);
  },
  rows() {
    const out = [['item_id', 'item_name', 'path', 'corpus_ref', 'it', 'en']];
    Copy.D.items.forEach(it => it.fields.forEach(f => {
      const v = f.value, a = v.corpus_ref !== undefined ? (v.specific_addition || {it: '', en: ''}) : v;
      out.push([it.id, it.name, JSON.stringify(f.path), v.corpus_ref || '', a.it, a.en]);
    }));
    return out;
  },
  import(H, R) {
    const ix = n => H.indexOf(n); if (ix('path') < 0) throw 'servono le colonne item_id e path'; let n = 0, miss = 0;
    R.forEach(r => {
      const it = Copy.D.items.find(x => x.id === r[ix('item_id')]); if (!it) { if (r[ix('item_id')]) miss++; return; }
      const j = it.fields.findIndex(f => JSON.stringify(f.path) === r[ix('path')]); if (j < 0) { miss++; return; }
      const ref = r[ix('corpus_ref')], ti = r[ix('it')], te = r[ix('en')]; let v;
      if (ref) { v = {corpus_ref: ref}; if (ti || te) v.specific_addition = {it: ti, en: te}; } else v = {it: ti, en: te};
      if (JSON.stringify(v) !== JSON.stringify(it.fields[j].value)) { it.fields[j].value = v; Copy.changed.items.add(it.id + '|' + j); n++; }
    });
    return [n, miss];
  },
};

$('#exp').onclick = () => Copy.exportCSV(Studio.tab, Studio.tabs[Studio.tab].rows());
$('#imp').onclick = () => $('#file').click();
$('#file').onchange = async e => {
  const file = e.target.files[0]; if (!file) return; e.target.value = '';
  const R = Copy.parseCSV(await file.text()), H = R.shift().map(h => h.trim());
  try {
    const [n, miss] = Studio.tabs[Studio.tab].import(H, R); render();
    msg('Importate ' + n + ' modifiche' + (miss ? ' · ' + miss + ' righe ignorate (chiave o prodotto non trovati)' : '') + '. Controlla e premi "Salva Modifiche".');
  } catch (err) { msg('CSV non valido per questa scheda: ' + err, true); }
};
