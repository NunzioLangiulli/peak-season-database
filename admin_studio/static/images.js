// Images tab: each product's gallery, primary photo, view type, search and download of new photos.
const VT_LABEL = {full_frame: 'Whole (fills the photo)', isolated_background: 'Whole on plain background', plant_in_field: 'Plant in the field',
  botanical_plate: 'Botanical plate', cut_section: 'Cut / section', other: 'Other'};
const Img = {list: [], cur: null, item: null, primary: null, vt: {}};

Img.load = async () => { Img.list = await api.get('/api/images/items'); };
Img.open = async id => {
  Img.cur = id; Img.item = await api.get('/api/images/item?id=' + encodeURIComponent(id));
  Img.primary = Img.item.primary; Img.vt = {}; render();
};
Img.dirty = () => (Img.item && Img.primary !== Img.item.primary ? 1 : 0) + Object.keys(Img.vt).length;

Studio.tabs.images = {
  placeholder: 'Search product (Italian or English name, or id)…', load: Img.load, dirty: Img.dirty,
  render(m, q) {
    const nq = norm(q), wrap = document.createElement('div'); wrap.className = 'imgwrap';
    const pl = document.createElement('div'); pl.className = 'plist';
    Img.list.filter(p => !nq || norm(p.name + ' ' + p.name_en + ' ' + p.id).includes(nq)).forEach(p => {
      const d = document.createElement('div'); d.className = p.id === Img.cur ? 'on' : '';
      d.innerHTML = '<span>' + esc(p.name_en) + ' <small>(' + esc(p.name) + ')</small></span><small>' + p.count + ' photos</small>';
      d.onclick = () => { if (Img.dirty() && !confirm('This product has unsaved changes. Switch product anyway?')) return; Img.open(p.id); };
      pl.append(d);
    });
    const right = document.createElement('div');
    wrap.append(pl, right); m.append(wrap);
    if (!Img.item) { right.innerHTML = '<div class="empty">Pick a product from the list on the left.</div>'; return; }
    const it = Img.item;
    right.insertAdjacentHTML('beforeend', `<div class="box"><h3>${esc(it.name_en)} (${esc(it.name)}) · <i>${esc(it.scientific_name || '')}</i> · ${it.images.length} photos</h3>
      <div class="meta">Star = primary photo (cards and Home). The view type decides how the app uses the photo. Click a photo to open the full-resolution original.</div></div>`);
    const grid = document.createElement('div'); grid.className = 'grid';
    it.images.forEach(d => {
      const f = d.filename, isP = f === Img.primary, vt = Img.vt[f] || d.view_type;
      const c = document.createElement('div'); c.className = 'ph' + (isP ? ' primary' : '') + ((Img.vt[f] || (isP && Img.primary !== it.primary)) ? ' changed' : '');
      c.innerHTML = `<img loading="lazy" src="/img/${esc(f)}" alt="${esc(f)}">
        <div class="c"><div class="meta" style="margin:0;justify-content:space-between"><b>${esc(f.replace(it.id + '_', '#').replace('.jpg', ''))}</b>
        <span class="star ${isP ? 'on' : ''}" title="Set as primary photo">★</span></div>
        <div class="credit" title="${esc((d.author || '') + ' · ' + (d.license || ''))}">${esc(d.author || 'author ?')} · ${esc(d.license || 'licence ?')}</div>
        ${(d.flags || []).length ? '<div class="no">Flagged: ' + esc(d.flags.join(', ')) + '</div>' : ''}
        <select>${it.view_types.map(v => `<option value="${v}" ${v === vt ? 'selected' : ''}>${VT_LABEL[v] || v}</option>`).join('')}</select></div>`;
      c.querySelector('img').onclick = () => window.open('/img/' + f + '?full=1', '_blank');
      c.querySelector('.star').onclick = () => { Img.primary = f; render(); };
      c.querySelector('select').onchange = e => { if (e.target.value === d.view_type) delete Img.vt[f]; else Img.vt[f] = e.target.value; refreshDirty(); c.classList.add('changed'); };
      grid.append(c);
    });
    right.append(grid);
    // search for new photos and download
    right.insertAdjacentHTML('beforeend', `<div class="box" style="margin-top:14px"><h3>Find new photos</h3><div class="links">${
      it.links.map(l => `<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)} ↗</a>`).join('')}</div>
      <div class="meta" style="margin-top:6px">Prefer openly licensed photos (CC BY, CC BY-SA, CC0, public domain). USDA ARS photos are public domain.</div></div>
      <div class="box"><h3>Download a photo from a URL</h3>
      <div class="form">
        <input class="full" type="url" id="dl_url" placeholder="Paste the address: Wikimedia Commons page (File:…), upload.wikimedia.org photo, USDA ARS page or photo, or any image">
        <div><label class="l">View type</label><select id="dl_vt">${it.view_types.map(v => `<option value="${v}">${VT_LABEL[v] || v}</option>`).join('')}</select></div>
        <div><label class="l">&nbsp;</label><label><input type="checkbox" id="dl_primary"> Make it the primary photo</label></div>
        <div><label class="l">Author (only if the source doesn't give it)</label><input type="text" id="dl_author" placeholder="e.g. Jane Doe / Wikimedia Commons"></div>
        <div><label class="l">Licence (only if the source doesn't give it)</label><input type="text" id="dl_license" placeholder="e.g. CC BY-SA 4.0"></div>
        <div class="full"><label class="l">Licence URL (optional)</label><input type="url" id="dl_lurl" placeholder="https://creativecommons.org/licenses/by-sa/4.0/"></div>
        <div class="full"><button class="btn primary" id="dl_go">Download and Add to Gallery</button> <span id="dl_state" class="meta"></span></div>
      </div></div>`);
    $('#dl_go').onclick = async () => {
      const url = $('#dl_url').value.trim(); if (!url) return msg('Paste an address first.', true);
      $('#dl_go').disabled = true; $('#dl_state').textContent = 'Downloading, reading metadata and validating…';
      const res = await api.post('/api/images/download', {id: it.id, url, view_type: $('#dl_vt').value, make_primary: $('#dl_primary').checked,
        author: $('#dl_author').value, license: $('#dl_license').value, license_url: $('#dl_lurl').value});
      $('#dl_go').disabled = false; $('#dl_state').textContent = '';
      if (await afterSave(res, 'New photo ' + (res.added ? res.added.filename : ''))) {
        msg('Added ' + res.added.filename + ' · ' + res.added.author + ' · ' + res.added.license);
        await Img.load(); await Img.open(it.id);
      }
    };
  },
  async save() {
    const res = await api.post('/api/images/save', {id: Img.cur, primary: Img.primary, view_types: Img.vt});
    if (await afterSave(res, 'Image changes')) { await Img.load(); await Img.open(Img.cur); }
  },
};
