// Schede Loghi (loghi, editore e titolo delle fonti) e Link (tutti i link, generali e per prodotto).
const Src = {list: [], changes: {}, v: Date.now()};
Src.load = async () => { Src.list = (await api.get('/api/sources')).sources; Src.changes = {}; };
Src.set = (k, f, v) => { (Src.changes[k] = Src.changes[k] || {})[f] = v; refreshDirty(); };
Src.copy = async (text, what) => { try { await navigator.clipboard.writeText(text); msg('Copiato: ' + what); } catch (e) { msg('Copia non riuscita: seleziona il testo e premi Ctrl+C', true); } };
Src.status = s => s.own_logo ? '<span class="ok">Logo proprio</span>'
  : s.favicon ? `<span class="tag">Logo condiviso (${esc(s.favicon.replace('.png', ''))})</span>` : '<span class="no">Senza logo</span>';

Studio.tabs.logos = {
  placeholder: 'Cerca fonte, editore o titolo…', load: Src.load, dirty: () => Object.keys(Src.changes).length,
  render(m, q) {
    const nq = norm(q), missing = Src.list.filter((s, i, a) => !s.favicon && s.logo_search && a.findIndex(x => !x.favicon && x.logo_search === s.logo_search) === i);
    const box = document.createElement('div'); box.className = 'box';
    box.innerHTML = `<h3>Loghi da cercare (${missing.length})</h3>
      <div class="meta">Una riga per ogni logo che manca (le fonti che usano già il logo di un'altra fonte dello stesso ente non sono in elenco, ma puoi dare anche a loro un logo proprio): copia l'elenco, cerca le immagini e caricale qui sotto con "Carica Logo" (PNG, JPG o WebP; meglio grande e con sfondo trasparente). Lo sfondo chiaro uniforme viene reso trasparente da solo.</div>
      <textarea readonly rows="${Math.min(12, missing.length + 1)}" style="font-family:Consolas,monospace;font-size:12px">${esc(missing.map(s => s.logo_search).join('\n'))}</textarea>
      <button class="btn small" id="cp_all">Copia Elenco</button>`;
    m.append(box);
    $('#cp_all').onclick = () => Src.copy(missing.map(s => s.logo_search).join('\n'), missing.length + ' righe');
    Src.list.filter(s => !nq || norm([s.key, s.name, s.publisher.it, s.publisher.en, s.title.it, s.title.en].join(' ')).includes(nq)).forEach(s => {
      const ch = Src.changes[s.key] || {}, pub = ch.publisher || {...s.publisher}, tit = ch.title || {...s.title};
      const r = document.createElement('div'); r.className = 'row' + (Src.changes[s.key] ? ' changed' : '');
      r.innerHTML = `<div class="slot" style="grid-template-columns:72px minmax(0,1fr) auto">
          <div style="width:64px;height:64px;border-radius:12px;background:${s.dark ? '#cfd6cc' : '#f1f3ee'};display:flex;align-items:center;justify-content:center">
            ${s.favicon ? `<img src="/logo/${esc(s.favicon)}?v=${Src.v}" style="width:48px;height:48px;object-fit:contain" alt="">` : '<span class="material-symbols-rounded" style="color:#9aa394">image_not_supported</span>'}</div>
          <div><b>${esc(s.title.it)}</b><div class="meta" style="margin:2px 0">${esc(s.publisher.it)} · <code>${esc(s.key)}</code> · usata in ${s.uses} link · ${Src.status(s)}</div>
            <a href="${esc(s.url)}" target="_blank" rel="noopener" class="credit" style="display:block">${esc(s.url)}</a></div>
          <label class="btn small" style="cursor:pointer">Carica Logo<input type="file" accept="image/png,image/jpeg,image/webp" hidden></label></div>
        <div class="form" style="margin-top:8px">
          <div><label class="l">Editore (IT)</label><input type="text" data-f="publisher" data-l="it"></div>
          <div><label class="l">Editore (EN)</label><input type="text" data-f="publisher" data-l="en"></div>
          <div><label class="l">Titolo (IT)</label><input type="text" data-f="title" data-l="it"></div>
          <div><label class="l">Titolo (EN)</label><input type="text" data-f="title" data-l="en"></div>
          <div class="full"><label class="l">Testo da cercare per il logo</label>
            <div style="display:flex;gap:6px"><input type="text" data-f="logo_search" style="flex:1">
            <button class="btn small" data-cp>Copia</button>
            <a class="btn small" target="_blank" rel="noopener" data-g>Cerca Immagini ↗</a></div></div></div>`;
      const vals = {publisher: pub, title: tit};
      r.querySelectorAll('input[type=text]').forEach(inp => {
        const f = inp.dataset.f, l = inp.dataset.l;
        inp.value = l ? vals[f][l] : (ch.logo_search ?? s.logo_search);
        inp.oninput = () => { if (l) { vals[f][l] = inp.value; Src.set(s.key, f, vals[f]); } else { Src.set(s.key, f, inp.value); upd(); } r.classList.add('changed'); };
      });
      const sq = r.querySelector('[data-f=logo_search]'), g = r.querySelector('[data-g]');
      const upd = () => g.href = 'https://www.google.com/search?tbm=isch&q=' + encodeURIComponent(sq.value); upd();
      r.querySelector('[data-cp]').onclick = () => Src.copy(sq.value, sq.value);
      r.querySelector('input[type=file]').onchange = e => {
        const f = e.target.files[0]; if (!f) return;
        if (Src.changes[s.key] && !confirm('Questa fonte ha modifiche non salvate a editore/titolo: caricando il logo restano in sospeso. Continuare?')) return;
        const rd = new FileReader();
        rd.onload = async () => {
          msg('Carico il logo di ' + s.key + '…');
          const res = await api.post('/api/sources/logo', {key: s.key, data_url: rd.result});
          if (await afterSave(res, 'Logo di ' + s.title.it)) { const keep = Src.changes; await Src.load(); Src.changes = keep; Src.v = Date.now(); render(); }
        };
        rd.readAsDataURL(f);
      };
      m.append(r);
    });
  },
  async save() {
    const res = await api.post('/api/sources/save', {changes: Src.changes});
    if (await afterSave(res, 'Modifiche alle fonti')) { await Src.load(); render(); }
  },
};

// ---------------------------------------------------------------- Link
const Lnk = {D: null, ch: {}};
Lnk.load = async () => { Lnk.D = await api.get('/api/links'); Lnk.ch = {}; };
Lnk.c = id => Lnk.ch[id] = Lnk.ch[id] || {edit: {}, remove: [], add: []};
Lnk.count = () => Object.values(Lnk.ch).reduce((n, c) => n + Object.keys(c.edit).length + c.remove.length + c.add.length, 0);
Lnk.logo = key => { const g = Lnk.D.general.find(x => x.key === key); return g && g.favicon ? `<img src="/logo/${esc(g.favicon)}" width="22" height="22" style="object-fit:contain;vertical-align:middle" alt="">` : '<span class="material-symbols-rounded" style="font-size:20px;color:#9aa394;vertical-align:middle">link</span>'; };

Studio.tabs.links = {
  placeholder: 'Cerca prodotto, titolo, indirizzo o fonte…', load: Lnk.load, dirty: Lnk.count,
  render(m, q) {
    const nq = norm(q), D = Lnk.D;
    const gen = D.general.filter(s => !nq || norm([s.key, s.url, (s.title || {}).it, (s.publisher || {}).it].join(' ')).includes(nq));
    if (gen.length) {
      const d = document.createElement('details'); d.className = 'box'; d.open = !!nq;
      d.innerHTML = `<summary><b>Link generali: le fonti (${gen.length})</b> <span class="meta">si modificano nella scheda Loghi</span></summary>` +
        gen.map(s => `<div class="meta" style="margin:6px 0">${Lnk.logo(s.key)} <b>${esc((s.title || {}).it)}</b> · ${esc((s.publisher || {}).it)} · <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a></div>`).join('');
      m.append(d);
    }
    let shown = 0;
    D.items.forEach(it => {
      const links = it.links.map((l, j) => [l, j]).filter(([l]) => !nq || norm([it.name, it.id, l.url, l.title.it, l.title.en, l.source_key, l.topic].join(' ')).includes(nq));
      if (!links.length || shown > 40) return; shown++;
      const h = document.createElement('div'); h.className = 'prod'; h.textContent = `${it.name} · ${it.links.length} link`; m.append(h);
      links.forEach(([l]) => {
        const r = document.createElement('div'); r.className = 'row'; const orig = l._orig || l.url;
        r.innerHTML = `<div class="meta">${Lnk.logo(l.source_key)} <code>${esc(l.source_key)}</code> · ${esc(l.topic)}
            <a href="${esc(l.url)}" target="_blank" rel="noopener">apri ↗</a> <button class="btn small" style="margin-left:auto">Elimina</button></div>
          <div class="form"><div><label class="l">Titolo (IT)</label><input type="text" data-l="it"></div><div><label class="l">Titolo (EN)</label><input type="text" data-l="en"></div>
          <div class="full"><label class="l">Indirizzo</label><input type="url" data-u></div></div>`;
        const ti = r.querySelector('[data-l=it]'), te = r.querySelector('[data-l=en]'), u = r.querySelector('[data-u]');
        ti.value = l.title.it; te.value = l.title.en; u.value = l.url;
        const mark = () => {
          l._orig = orig; l.title = {it: ti.value, en: te.value}; l.url = u.value;
          if (l._new) { const a = Lnk.c(it.id).add.find(x => x === l._new); Object.assign(a, {title: l.title, url: l.url}); }
          else Lnk.c(it.id).edit[orig] = {title: l.title, url: l.url};
          r.classList.add('changed'); refreshDirty();
        };
        [ti, te, u].forEach(x => x.oninput = mark);
        r.querySelector('button').onclick = () => {
          if (!confirm('Eliminare questo link da ' + it.name + '?')) return;
          const c = Lnk.c(it.id);
          if (l._new) c.add = c.add.filter(x => x !== l._new); else { delete c.edit[orig]; c.remove.push(orig); }
          it.links = it.links.filter(x => x !== l); render();
        };
        m.append(r);
      });
      const add = document.createElement('div'); add.className = 'row';
      add.innerHTML = `<details><summary class="meta" style="cursor:pointer">+ Aggiungi un link a ${esc(it.name)}</summary><div class="form" style="margin-top:6px">
        <div><label class="l">Titolo (IT)</label><input type="text" data-a="it"></div><div><label class="l">Titolo (EN)</label><input type="text" data-a="en"></div>
        <div class="full"><label class="l">Indirizzo</label><input type="url" data-a="url" placeholder="https://…"></div>
        <div><label class="l">Fonte</label><select data-a="source_key">${D.source_keys.map(k => `<option ${k === 'user' ? 'selected' : ''}>${esc(k)}</option>`).join('')}</select></div>
        <div><label class="l">Argomento</label><select data-a="topic">${D.topics.map(k => `<option ${k === 'other' ? 'selected' : ''}>${esc(k)}</option>`).join('')}</select></div>
        <div class="full"><button class="btn small">Aggiungi</button></div></div></details>`;
      add.querySelector('button').onclick = () => {
        const g = n => add.querySelector(`[data-a=${n}]`).value.trim();
        if (!/^https?:\/\/\S+$/.test(g('url')) || !g('it') || !g('en')) return alert('Servono titolo italiano, titolo inglese e un indirizzo che inizia con https://');
        const a = {title: {it: g('it'), en: g('en')}, url: g('url'), source_key: g('source_key'), topic: g('topic')};
        Lnk.c(it.id).add.push(a); it.links.push({...a, _new: a}); refreshDirty(); render();
      };
      m.append(add);
    });
    if (shown > 40) m.insertAdjacentHTML('beforeend', '<div class="empty">Mostrati i primi 40 prodotti: cerca un prodotto per vedere gli altri.</div>');
    if (!shown && !gen.length) m.insertAdjacentHTML('beforeend', '<div class="empty">Nessun risultato</div>');
  },
  async save() {
    const res = await api.post('/api/links/save', {changes: Lnk.ch});
    if (await afterSave(res, 'Modifiche ai link')) { await Lnk.load(); render(); }
  },
};
