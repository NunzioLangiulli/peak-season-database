// Help Texts tab: the "?" explanations (scripts/config/glossary.json -> metadata.glossary), with where each one is used.
const Help = {list: [], changes: {}, open: null};
Help.load = async () => { Help.list = (await api.get('/api/help')).entries; Help.changes = {}; };
Help.cur = (e, f) => (Help.changes[e.id] || {})[f] || e[f];
Help.set = (e, f, lang, v, row) => {
  const c = Help.changes[e.id] = Help.changes[e.id] || {};
  c[f] = {...(c[f] || e[f]), [lang]: v}; row.classList.add('changed'); refreshDirty();
};

Studio.tabs.help = {
  placeholder: 'Search entry, text, field or screen…', load: Help.load, dirty: () => Object.keys(Help.changes).length,
  render(m, q) {
    const nq = norm(q);
    const seeAlsoFrom = {};
    Help.list.forEach(e => e.see_also.forEach(s => (seeAlsoFrom[s] = seeAlsoFrom[s] || []).push(e.id)));
    Help.list.filter(e => !nq || norm([e.id, e.term.it, e.term.en, e.short.it, e.short.en, e.text.it, e.text.en, e.fields.join(' '),
      e.app_usage.map(u => u.screen + ' ' + (u.field || '')).join(' ')].join(' ')).includes(nq)).forEach(e => {
      const r = document.createElement('div'); r.className = 'row' + (Help.changes[e.id] ? ' changed' : '');
      const term = Help.cur(e, 'term'), open = Help.open === e.id || !!nq;
      const usage = e.app_usage.map(u => `<li><b>${esc(u.screen)}</b>${u.field ? ' · ' + esc(u.field) : ''} <span class="tag">${esc(u.where)}</span></li>`).join('');
      const extra = [
        e.footnote.it ? `<li>Footnote: ${esc(e.footnote.en)}</li>` : '',
        e.fields.length ? `<li>Data fields (field_help): ${e.fields.map(f => '<code>' + esc(f) + '</code>').join(', ')}</li>` : '',
        e.vocabulary.length ? `<li>Value labels: ${e.vocabulary.map(f => '<code>' + esc(f) + '</code>').join(', ')}</li>` : '',
        e.product_refs.length ? `<li>Linked from the texts of ${e.product_refs.length} products (e.g. ${esc(e.product_refs.slice(0, 4).join(', '))})</li>` : '',
        (seeAlsoFrom[e.id] || []).length ? `<li>"See also" in: ${seeAlsoFrom[e.id].map(x => '<code>' + esc(x) + '</code>').join(', ')}</li>` : '',
      ].join('');
      r.innerHTML = `<div class="meta" style="justify-content:space-between"><span><b style="font-size:14px">${esc(term.en)}</b> (${esc(term.it)}) · <code>${esc(e.id)}</code></span>
          <button class="btn small">${open ? 'Close' : 'Edit'}</button></div>
        <div class="meta" style="margin:0">Where it's used in the app:</div>
        <ul class="uses">${usage || '<li>No direct "?" button found in the app code</li>'}${extra}</ul>`;
      r.querySelector('button').onclick = () => { Help.open = Help.open === e.id ? null : e.id; render(); };
      if (open) {
        for (const [f, lbl] of [['term', 'Title'], ['short', 'Short line (tooltip)'], ['footnote', 'Footnote on the product page, before the "?" (optional: leave both empty to use the short line)'], ['text', 'Full explanation']]) {
          const v = Help.cur(e, f);
          r.insertAdjacentHTML('beforeend', `<label class="l" style="margin-top:8px">${lbl}</label>`);
          const p = document.createElement('div'); p.className = 'pair';
          for (const [lang, name] of [['it', 'Italian (app text)'], ['en', 'English (app text)']]) {
            const d = document.createElement('div'); d.innerHTML = `<label class="l">${name}</label>`;
            const t = document.createElement('textarea'); t.value = v[lang] || '';
            t.rows = f === 'text' ? Math.min(16, Math.max(4, (v[lang] || '').split('\n').length + Math.ceil((v[lang] || '').length / 90))) : 1;
            t.oninput = () => Help.set(e, f, lang, t.value, r); d.append(t); p.append(d);
          }
          r.append(p);
        }
        r.insertAdjacentHTML('beforeend', `<div class="meta" style="margin-top:6px">Sources: ${e.sources.map(s => '<code>' + esc(s) + '</code>').join(', ') || '—'} · See also: ${e.see_also.map(s => '<code>' + esc(s) + '</code>').join(', ') || '—'}</div>`);
      }
      m.append(r);
    });
  },
  async save() {
    const res = await api.post('/api/help/save', {changes: Help.changes});
    if (await afterSave(res, 'Help text changes')) { await Help.load(); render(); }
  },
};
