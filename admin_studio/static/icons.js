// Icons tab: picks the icon for every state, category, zone and interface element (data/ui_config.json).
const Ico = {cfg: null, cat: null, changes: {}, open: null};

Ico.load = async () => { const p = await api.get('/api/icons'); Ico.cfg = p.config; Ico.cat = p.catalog; Ico.res = p.resources || []; Ico.changes = {}; };
Ico.html = ref => {
  if (!ref) return '<span class="ico">–</span>';
  if (ref.startsWith('svg:')) return `<span class="ico"><img src="/icon/${esc(ref.slice(4))}.svg" alt=""></span>`;
  return `<span class="ico"><span class="material-symbols-rounded">${esc(ref.split(':')[1])}</span></span>`;
};
const DIR_LABEL = {season: '"Growth" set (seasons)', ui: 'Icons drawn for Peak Season', zones: 'Climate zones', italy: 'Italian macro-areas (mini maps)',
  zones_map: 'European climate zones (mini maps)'};
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
    Ico.gallery(m, nq);
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

// Read-only gallery of every graphic resource in the app (all icon folders, Europe maps, launcher icon), with the slots using each.
Ico.gallery = (m, nq) => {
  const groups = Ico.res.map(g => ({...g, files: g.files.filter(f => !nq || norm([g.dir, f.name, f.ref || '', f.slots.join(' ')].join(' ')).includes(nq))}))
    .filter(g => g.files.length);
  if (!groups.length) return;
  const n = groups.reduce((a, g) => a + g.files.length, 0);
  const d = document.createElement('details'); d.className = 'box resgal'; d.open = !!nq || Ico.galOpen; d.ontoggle = () => { if (!nq) Ico.galOpen = d.open; };
  d.innerHTML = `<summary><h3 style="display:inline">All app graphic resources</h3> <span class="meta">${n} files · app/assets</span></summary>
    <div class="meta">Everything the app draws, by folder: icon sets, the Europe and Italy mini maps, the full Europe climate-zone maps and the launcher icon.
    Files under "Used by" are linked to a slot above; the others are used directly by the app code. Maps and mini maps are generated by scripts, so edit them there, not here.</div>`;
  groups.forEach(g => {
    d.insertAdjacentHTML('beforeend', `<div class="grp">${esc(g.title || DIR_LABEL[g.key] || g.dir)} <span class="meta" style="font-weight:normal">app/assets/${esc(g.dir)}/ · ${g.files.length}</span></div>
      ${g.note ? `<div class="meta">${esc(g.note)}</div>` : ''}`);
    const grid = document.createElement('div'); grid.className = 'resgrid' + (g.key === 'maps' ? ' big' : '');
    g.files.forEach(f => grid.insertAdjacentHTML('beforeend', `<a class="res" href="${esc(f.url)}" target="_blank" title="${esc(f.ref || f.url)} · ${f.kb} KB">
      <img src="${esc(f.url)}" alt="" loading="lazy"><b>${esc(f.name)}</b>
      <span class="meta">${f.slots.length ? 'Used by: ' + esc(f.slots.join(', ')) : (g.key === 'season' || g.key === 'ui' || g.key === 'zones' ? 'no slot' : 'app code')}</span></a>`));
    d.append(grid);
  });
  m.append(d);
};
