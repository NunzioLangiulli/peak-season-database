// Icons tab: picks the icon for every state, category, zone and interface element (data/ui_config.json).
const Ico = {cfg: null, cat: null, changes: {}, open: null};

Ico.load = async () => { const p = await api.get('/api/icons'); Ico.cfg = p.config; Ico.cat = p.catalog; Ico.changes = {}; };
Ico.html = ref => {
  if (!ref) return '<span class="ico">–</span>';
  if (ref.startsWith('svg:')) return `<span class="ico"><img src="/icon/${esc(ref.slice(4))}.svg" alt=""></span>`;
  return `<span class="ico"><span class="material-symbols-rounded">${esc(ref.split(':')[1])}</span></span>`;
};
const DIR_LABEL = {season: '"Growth" set (seasons)', ui: 'Icons drawn for Peak Season', zones: 'Climate zones', italy: 'Italian macro-areas'};
// group and description come from ui_config.json; the English fields are used when the app session provides them
const tr = (s, f) => s[f + '_en'] || s[f];

Studio.tabs.icons = {
  placeholder: 'Search slot or icon (e.g. fridge, category, eco)…', load: Ico.load,
  dirty: () => Object.keys(Ico.changes).length,
  render(m, q) {
    const nq = norm(q);
    m.insertAdjacentHTML('beforeend', `<div class="box"><h3>App icons</h3><div class="meta">Click "Change" on a slot and pick the icon: icons drawn for Peak Season (SVG) at the top, Material Symbols below (only the ones already included in the app).
      <span class="tag">database</span> slots are also written to the database; <span class="tag">app</span> slots are read only by the interface.</div></div>`);
    let grp = null;
    Ico.cfg.icon_slots.forEach(s => {
      const ref = Ico.changes[s.slot] || s.icon, g = tr(s, 'group');
      if (nq && !norm([s.slot, s.group, s.description, s.group_en, s.description_en, ref].join(' ')).includes(nq)) return;
      if (g !== grp) { grp = g; m.insertAdjacentHTML('beforeend', '<div class="grp">' + esc(grp) + '</div>'); }
      const r = document.createElement('div'); r.className = 'row' + (Ico.changes[s.slot] ? ' changed' : '');
      r.innerHTML = `<div class="slot">${Ico.html(ref)}<div><b>${esc(tr(s, 'description'))}</b> <span class="tag">${esc(s.target)}</span><div class="meta" style="margin:0">${esc(s.slot)} · ${esc(ref || 'none')}</div></div>
        <button class="btn small">${Ico.open === s.slot ? 'Close' : 'Change'}</button></div>`;
      r.querySelector('button').onclick = () => { Ico.open = Ico.open === s.slot ? null : s.slot; render(); };
      if (Ico.open === s.slot) r.append(Ico.picker(s, ref));
      m.append(r);
    });
    const lastSlot = Ico.open && document.querySelector('.picker'); if (lastSlot) lastSlot.scrollIntoView({block: 'nearest'});
  },
  async save() {
    const res = await api.post('/api/icons/save', {changes: Ico.changes});
    if (await afterSave(res, 'Icon changes')) { await Ico.load(); render(); }
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
  p.insertAdjacentHTML('beforeend', `<div class="meta" style="grid-column:1/-1">These are the Material icons the app can draw (${esc(Ico.cat.material_source)}). Adding one needs a line in that file and a new app build.</div>`);
  Ico.cat.material.forEach(n => {
    const b = document.createElement('button'); b.className = 'material:' + n === ref ? 'on' : '';
    b.innerHTML = `<span class="material-symbols-rounded">${esc(n)}</span>${esc(n)}`; b.onclick = () => choose('material:' + n); p.append(b);
  });
  return p;
};
