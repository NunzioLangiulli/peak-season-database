// Scheda Icone: per ogni stato, categoria, zona ed elemento dell'interfaccia sceglie l'icona (data/ui_config.json).
const Ico = {cfg: null, cat: null, changes: {}, open: null};

Ico.load = async () => { const p = await api.get('/api/icons'); Ico.cfg = p.config; Ico.cat = p.catalog; Ico.changes = {}; };
Ico.html = ref => {
  if (!ref) return '<span class="ico">–</span>';
  if (ref.startsWith('svg:')) return `<span class="ico"><img src="/icon/${esc(ref.slice(4))}.svg" alt=""></span>`;
  return `<span class="ico"><span class="material-symbols-rounded">${esc(ref.split(':')[1])}</span></span>`;
};
const DIR_LABEL = {season: 'Set "Crescita" (stagioni)', ui: 'Icone disegnate per Peak Season', zones: 'Zone climatiche', italy: 'Macro-aree italiane'};

Studio.tabs.icons = {
  placeholder: 'Cerca voce o icona (es. frigorifero, categoria, eco)…', load: Ico.load,
  dirty: () => Object.keys(Ico.changes).length,
  render(m, q) {
    const nq = norm(q);
    m.insertAdjacentHTML('beforeend', `<div class="box"><h3>Icone dell'app</h3><div class="meta">Clicca "Cambia" su una voce e scegli l'icona: in alto quelle disegnate per Peak Season (SVG), sotto le Material Symbols (solo quelle già incluse nell'app).
      Le voci <span class="tag">database</span> vengono scritte anche nel database; le voci <span class="tag">app</span> le legge solo l'interfaccia.</div></div>`);
    let grp = null;
    Ico.cfg.icon_slots.forEach(s => {
      const ref = Ico.changes[s.slot] || s.icon;
      if (nq && !norm(s.slot + ' ' + s.group + ' ' + s.description + ' ' + ref).includes(nq)) return;
      if (s.group !== grp) { grp = s.group; m.insertAdjacentHTML('beforeend', '<div class="grp">' + esc(grp) + '</div>'); }
      const r = document.createElement('div'); r.className = 'row' + (Ico.changes[s.slot] ? ' changed' : '');
      r.innerHTML = `<div class="slot">${Ico.html(ref)}<div><b>${esc(s.description)}</b> <span class="tag">${esc(s.target)}</span><div class="meta" style="margin:0">${esc(s.slot)} · ${esc(ref || 'nessuna')}</div></div>
        <button class="btn small">${Ico.open === s.slot ? 'Chiudi' : 'Cambia'}</button></div>`;
      r.querySelector('button').onclick = () => { Ico.open = Ico.open === s.slot ? null : s.slot; render(); };
      if (Ico.open === s.slot) r.append(Ico.picker(s, ref));
      m.append(r);
    });
    const lastSlot = Ico.open && document.querySelector('.picker'); if (lastSlot) lastSlot.scrollIntoView({block: 'nearest'});
  },
  async save() {
    const res = await api.post('/api/icons/save', {changes: Ico.changes});
    if (await afterSave(res, 'Modifiche alle icone')) { await Ico.load(); render(); }
  },
};

Ico.picker = (s, ref) => {
  const p = document.createElement('div'); p.className = 'picker';
  const choose = r => { if (r === s.icon) delete Ico.changes[s.slot]; else Ico.changes[s.slot] = r; Ico.open = null; render(); };
  let dir = null;
  Ico.cat.svg.forEach(x => {
    if (x.dir !== dir) { dir = x.dir; p.insertAdjacentHTML('beforeend', '<h4>' + esc(DIR_LABEL[dir] || dir) + '</h4>'); }
    const b = document.createElement('button'); b.className = x.ref === ref ? 'on' : '';
    b.innerHTML = `<img src="${esc(x.url)}" width="24" height="24" alt="">${esc(x.name)}`; b.onclick = () => choose(x.ref); p.append(b);
  });
  p.insertAdjacentHTML('beforeend', '<h4>Material Symbols (Rounded)</h4>');
  p.insertAdjacentHTML('beforeend', `<div class="meta" style="grid-column:1/-1">Sono le icone Material che l'app sa disegnare (${esc(Ico.cat.material_source)}). Per aggiungerne una serve una riga in quel file e una nuova build dell'app.</div>`);
  Ico.cat.material.forEach(n => {
    const b = document.createElement('button'); b.className = 'material:' + n === ref ? 'on' : '';
    b.innerHTML = `<span class="material-symbols-rounded">${esc(n)}</span>${esc(n)}`; b.onclick = () => choose('material:' + n); p.append(b);
  });
  return p;
};
