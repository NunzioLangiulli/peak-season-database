// Vocabulary tab: IT/EN labels of the coded values (scripts/config/vocabulary.json -> metadata.vocabulary).
const Voc = {groups: [], changes: {}};
Voc.load = async () => { Voc.groups = (await api.get('/api/vocabulary')).groups; Voc.changes = {}; };
Voc.label = (group, code) => {                       // used by other tabs (e.g. category names)
  const g = Voc.groups.find(x => x.group === group), c = g && g.codes.find(x => x.code === code);
  return c ? c.en : code;
};
const VOC_TITLE = {category: 'Product categories', month: 'Months', 'seasonality.state': 'Seasonality states',
  'seasonality.italy_macro_areas': 'Italian macro-areas', 'seasonality.eufic_climatic_zones': 'European climate zones',
  'botany.family': 'Botanical families (generated)', class_scale: 'Class scale (respiration, ethylene)'};

Studio.tabs.vocab = {
  placeholder: 'Search group, code or label…', load: Voc.load, dirty: () => Object.keys(Voc.changes).length,
  render(m, q) {
    const nq = norm(q);
    m.insertAdjacentHTML('beforeend', `<div class="box"><h3>Value labels</h3><div class="meta" style="margin:0">
      ${Voc.groups.length} groups · source <code>scripts/config/vocabulary.json</code> · saved with build_help → build_app_support_metadata → ux_terminology → title_case_labels.
      <span class="kind generated">locked</span> groups are written by a script from other data.</div></div>`);
    let shown = 0;
    Voc.groups.forEach(g => {
      const codes = g.codes.filter(c => !nq || norm([g.group, c.code, c.it, c.en, (Voc.changes[g.group + '|' + c.code] || {}).it].join(' ')).includes(nq));
      if (!codes.length) return; shown++;
      const title = esc(VOC_TITLE[g.group] || g.group.split('.').pop().replace(/_/g, ' ').replace(/^./, c => c.toUpperCase()));
      Nav.sec(m, {key: g.group, title, sub: esc(g.group), count: codes.length, open: !!nq || g.editable, fill: body => {
        const info = [g.glossary ? `"?" entry: <code>${esc(g.glossary)}</code>` : '', g.used_by.length ? 'Fields: ' + g.used_by.map(x => '<code>' + esc(x) + '</code>').join(', ') : '',
          g.app_files.length ? 'Named in: ' + g.app_files.map(x => '<code>' + esc(x.replace('app/lib/', '')) + '</code>').join(', ') : '', g.note ? esc(g.note) : ''].filter(Boolean).join(' · ');
        if (info) body.insertAdjacentHTML('beforeend', `<div class="meta">${info}</div>`);
        codes.forEach(c => {
          const k = g.group + '|' + c.code, cur = Voc.changes[k] || c;
          const r = document.createElement('div'); r.className = 'row' + (Voc.changes[k] ? ' changed' : '') + (g.editable ? '' : ' locked');
          r.innerHTML = `<div class="meta"><span>Code: <b>${esc(c.code)}</b></span>${c.color ? `<span><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${esc(c.color)}"></span> ${esc(c.color)}</span>` : ''}${c.marker ? `<span>Marker: <b>${esc(c.marker)}</b></span>` : ''}</div>`;
          if (g.editable) {
            r.append(Copy.pair({...cur}, () => {}));
            r.querySelectorAll('textarea').forEach((t, i) => t.oninput = () => {
              const v = Voc.changes[k] || {it: c.it, en: c.en}; v[i ? 'en' : 'it'] = t.value;
              if (v.it === c.it && v.en === c.en) delete Voc.changes[k]; else Voc.changes[k] = v;
              r.classList.toggle('changed', !!Voc.changes[k]); refreshDirty();
            });
          } else r.insertAdjacentHTML('beforeend', `<div class="pair"><div class="base">${esc(c.it)}</div><div class="base">${esc(c.en)}</div></div>`);
          body.append(r);
        });
      }});
    });
    if (!shown) m.insertAdjacentHTML('beforeend', '<div class="empty">No results</div>');
  },
  async save() {
    for (const [k, v] of Object.entries(Voc.changes)) if (!v.it.trim() || !v.en.trim()) return msg(k + ': fill in both Italian and English.', true);
    const res = await api.post('/api/vocabulary/save', {changes: Voc.changes});
    if (await afterSave(res, 'Vocabulary changes')) { await Voc.load(); render(); }
  },
};
