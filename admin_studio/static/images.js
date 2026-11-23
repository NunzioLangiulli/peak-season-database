// Images tab: each product's gallery, primary photo, view type, search and download of new photos.
const VT_LABEL = {full_frame: 'Whole (fills the photo)', isolated_background: 'Whole on plain background', plant_in_field: 'Plant in the field',
  botanical_plate: 'Botanical plate', cut_section: 'Cut / section', other: 'Other'};
const Img = {list: [], cur: null, item: null, primary: null, vt: {}};

Img.load = async () => { Img.list = await api.get('/api/images/items'); };
Img.open = async id => {
  Img.cur = id;
  [Img.item, Img.list] = await Promise.all([api.get('/api/images/item?id=' + encodeURIComponent(id)), api.get('/api/images/items')]);   // counts always fresh
  Img.primary = Img.item.primary; Img.vt = {}; render();
};
Img.del = async (f, isP) => {
  if (Img.dirty()) return msg('Save or undo the pending changes of this product before deleting a photo.', true);
  if (!confirm('Delete ' + f + '?\n\nThe photo file, its author/licence record and its place in the gallery are removed' +
    (isP ? '; the primary photo is then chosen automatically (first "whole" photo)' : '') +
    '. A backup copy is kept in data/_snapshots.')) return;
  const res = await api.post('/api/images/delete', {id: Img.cur, filename: f});
  if (await afterSave(res, 'Photo ' + f + ' deleted')) { await Img.load(); await Img.open(Img.cur); }
};
// Format rules of scripts/crop_images.py, applied when a photo is added: preview before/after, and for portrait
// photos the choice between keeping them whole and a 3:2 crop at the top, centre or bottom.
Img.crop = {dl: {mode: 'keep', anchor: 0.5}, up: {mode: 'keep', anchor: 0.5}};
Img.cropBox = (k, source) => {
  const box = $('#' + k + '_crop'), st = Img.crop[k] = {mode: 'keep', anchor: 0.5};
  box.innerHTML = `<button class="btn small" id="${k}_pv">Preview crop</button> <span class="meta" style="display:inline">The photo is brought to the app format: landscape 3:2 (centred crop), botanical plates 2:3 with a margin, portrait photos kept whole unless you crop them. The uncropped original is kept in assets/images/_originals/.</span><div class="cropv"></div>`;
  const out = box.querySelector('.cropv');
  const show = async () => {
    const src = await source(); if (!src) return msg('Choose the photo first.', true);
    out.innerHTML = '<div class="meta">Preparing the preview…</div>';
    const r = await api.post('/api/images/preview', {...src, view_type: $('#' + k + '_vt').value, crop: st});
    if (!r.ok) { out.innerHTML = ''; return msg('Preview failed: ' + (r.report || ''), true); }
    out.innerHTML = `<div class="pv"><figure><img src="${r.before}"><figcaption>Before · ${r.size_before.join('×')}</figcaption></figure>
      <figure><img src="${r.after}"><figcaption>${r.changed ? 'After' : 'Unchanged'} · ${r.size_after.join('×')}</figcaption></figure></div>
      <div class="meta"><b>${esc(r.text)}</b>${r.author ? ' · ' + esc(r.author) + ' · ' + esc(r.license || '') : ''}</div>
      ${r.options ? `<div class="meta"><label><input type="radio" name="${k}_m" value="keep" ${st.mode !== 'crop' ? 'checked' : ''}> Keep it whole (portrait)</label>
        <label><input type="radio" name="${k}_m" value="crop" ${st.mode === 'crop' ? 'checked' : ''}> Crop to 3:2, keeping the</label>
        <select id="${k}_anchor">${[[0, 'top'], [0.5, 'centre'], [1, 'bottom']].map(([v, l]) => `<option value="${v}" ${+st.anchor === v ? 'selected' : ''}>${l}</option>`).join('')}</select></div>` : ''}`;
    out.querySelectorAll(`[name=${k}_m]`).forEach(x => x.onchange = () => { st.mode = x.value; show(); });
    const a = out.querySelector('#' + k + '_anchor'); if (a) a.onchange = () => { st.anchor = +a.value; st.mode = 'crop'; show(); };
  };
  box.querySelector('#' + k + '_pv').onclick = show;
  $('#' + k + '_vt').addEventListener('change', () => { if (out.innerHTML) show(); });
  Img.crop[k].reset = () => { st.mode = 'keep'; st.anchor = 0.5; out.innerHTML = ''; };
};
Img.uploadForm = it => {
  let file = null;
  const pick = f => { if (!f) return; if (!/^image\/(jpeg|png|webp)$/.test(f.type)) return msg('Choose a JPG, PNG or WebP photo.', true);
    file = f; $('#up_name').textContent = f.name + ' · ' + (f.size / 1048576).toFixed(1) + ' MB'; $('#up_drop').classList.add('on');
    Img.crop.up.reset();
    file.data = new Promise(ok => { const rd = new FileReader(); rd.onload = () => ok(rd.result); rd.readAsDataURL(f); }); };
  Img.cropBox('up', async () => file ? {data_url: await file.data} : null);
  $('#up_file').onchange = e => pick(e.target.files[0]);
  const dz = $('#up_drop');
  dz.ondragover = e => { e.preventDefault(); dz.classList.add('over'); };
  dz.ondragleave = () => dz.classList.remove('over');
  dz.ondrop = e => { e.preventDefault(); dz.classList.remove('over'); pick(e.dataTransfer.files[0]); };
  $('#up_go').onclick = () => {
    if (!file) return msg('Choose a photo first.', true);
    if (!$('#up_author').value.trim() || !$('#up_license').value.trim()) return msg('Author and licence are required: the app shows them under the photo.', true);
    (async () => {
      $('#up_go').disabled = true; $('#up_state').textContent = 'Uploading and validating…';
      const res = await api.post('/api/images/upload', {id: it.id, data_url: await file.data, file_name: file.name, view_type: $('#up_vt').value, crop: Img.crop.up,
        make_primary: $('#up_primary').checked, author: $('#up_author').value, license: $('#up_license').value, source_url: $('#up_src').value});
      $('#up_go').disabled = false; $('#up_state').textContent = '';
      if (await afterSave(res, 'New photo ' + (res.added ? res.added.filename : ''))) {
        msg('Added ' + res.added.filename + ' · ' + res.added.author + ' · ' + res.added.license + (res.crop ? '\n' + res.crop : ''));
        await Img.load(); await Img.open(it.id);
      }
    })();
  };
};
Img.dirty = () => (Img.item && Img.primary !== Img.item.primary ? 1 : 0) + Object.keys(Img.vt).length;

Studio.tabs.images = {
  placeholder: 'Search product (Italian or English name, or id)…', load: Img.load, dirty: Img.dirty,
  render(m, q) {
    const nq = norm(q), wrap = document.createElement('div'); wrap.className = 'imgwrap';
    const pl = document.createElement('div'); pl.className = 'plist';
    Img.list.filter(p => !nq || norm(p.name + ' ' + p.name_en + ' ' + p.id).includes(nq)).forEach(p => {
      const d = document.createElement('div'); d.className = p.id === Img.cur ? 'on' : '';
      d.innerHTML = '<span>' + pname(p.name_en, p.name) + '</span><small>' + p.count + ' photos</small>';
      d.onclick = () => { if (Img.dirty() && !confirm('This product has unsaved changes. Switch product anyway?')) return; Img.open(p.id); };
      pl.append(d);
    });
    const right = document.createElement('div');
    wrap.append(pl, right); m.append(wrap);
    if (!Img.item) { right.innerHTML = '<div class="empty">Pick a product from the list on the left.</div>'; return; }
    const it = Img.item;
    right.insertAdjacentHTML('beforeend', `<div class="box"><h3>${pname(it.name_en, it.name)} · <i>${esc(it.scientific_name || '')}</i> · ${it.images.length} photos</h3>
      <div class="meta">Star = primary photo (cards and Home). The view type decides how the app uses the photo. Click a photo to open the full-resolution original.</div></div>`);
    const grid = document.createElement('div'); grid.className = 'grid';
    it.images.forEach(d => {
      const f = d.filename, isP = f === Img.primary, vt = Img.vt[f] || d.view_type;
      const c = document.createElement('div'); c.className = 'ph' + (isP ? ' primary' : '') + ((Img.vt[f] || (isP && Img.primary !== it.primary)) ? ' changed' : '');
      c.innerHTML = `<img loading="lazy" src="/img/${esc(f)}?v=${d.v || 0}" alt="${esc(f)}">
        <div class="c"><div class="meta" style="margin:0;justify-content:space-between"><b>${esc(f.replace(it.id + '_', '#').replace('.jpg', ''))}</b>
        <span><button class="btn small del" title="Delete this photo">🗑</button> <span class="star ${isP ? 'on' : ''}" title="Set as primary photo">★</span></span></div>
        <div class="credit" title="${esc((d.author || '') + ' · ' + (d.license || ''))}">${esc(d.author || 'author ?')} · ${esc(d.license || 'licence ?')}</div>
        ${(d.flags || []).length ? '<div class="no">Flagged: ' + esc(d.flags.join(', ')) + '</div>' : ''}
        <select>${it.view_types.map(v => `<option value="${v}" ${v === vt ? 'selected' : ''}>${VT_LABEL[v] || v}</option>`).join('')}</select></div>`;
      c.querySelector('img').onclick = () => window.open('/img/' + f + '?full=1&v=' + (d.v || 0), '_blank');
      c.querySelector('.star').onclick = () => { Img.primary = f; render(); };
      c.querySelector('.del').onclick = () => Img.del(f, isP);
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
        <div class="full" id="dl_crop"></div>
        <div class="full"><button class="btn primary" id="dl_go">Download and Add to Gallery</button> <span id="dl_state" class="meta"></span></div>
      </div></div>
      <div class="box"><h3>Upload a photo from this computer</h3>
      <div class="form">
        <label class="full drop" id="up_drop"><input type="file" id="up_file" accept="image/jpeg,image/png,image/webp" hidden>
          <span id="up_name">Drop a JPG, PNG or WebP photo here, or click to choose one</span></label>
        <div><label class="l">View type</label><select id="up_vt">${it.view_types.map(v => `<option value="${v}">${VT_LABEL[v] || v}</option>`).join('')}</select></div>
        <div><label class="l">&nbsp;</label><label><input type="checkbox" id="up_primary"> Make it the primary photo</label></div>
        <div><label class="l">Author (required)</label><input type="text" id="up_author" placeholder="e.g. your name, or the photographer"></div>
        <div><label class="l">Licence (required)</label><input type="text" id="up_license" list="up_lic" placeholder="e.g. CC BY 4.0">
          <datalist id="up_lic"><option>CC BY 4.0</option><option>CC BY-SA 4.0</option><option>CC0 1.0</option><option>Public domain</option><option>All rights reserved (own photo, used with permission)</option></datalist></div>
        <div class="full"><label class="l">Source page (optional)</label><input type="url" id="up_src" placeholder="Where the photo comes from, if not your own"></div>
        <div class="full" id="up_crop"></div>
        <div class="full"><button class="btn primary" id="up_go">Upload and Add to Gallery</button> <span id="up_state" class="meta"></span></div>
      </div></div>`);
    Img.uploadForm(it);
    Img.cropBox('dl', async () => { const u = $('#dl_url').value.trim(); return u ? {url: u} : null; });
    $('#dl_url').addEventListener('input', () => Img.crop.dl.reset());
    $('#dl_go').onclick = async () => {
      const url = $('#dl_url').value.trim(); if (!url) return msg('Paste an address first.', true);
      $('#dl_go').disabled = true; $('#dl_state').textContent = 'Downloading, reading metadata and validating…';
      const res = await api.post('/api/images/download', {id: it.id, url, view_type: $('#dl_vt').value, crop: Img.crop.dl, make_primary: $('#dl_primary').checked,
        author: $('#dl_author').value, license: $('#dl_license').value, license_url: $('#dl_lurl').value});
      $('#dl_go').disabled = false; $('#dl_state').textContent = '';
      if (await afterSave(res, 'New photo ' + (res.added ? res.added.filename : ''))) {
        msg('Added ' + res.added.filename + ' · ' + res.added.author + ' · ' + res.added.license + (res.crop ? '\n' + res.crop : ''));
        await Img.load(); await Img.open(it.id);
      }
    };
  },
  async save() {
    const res = await api.post('/api/images/save', {id: Img.cur, primary: Img.primary, view_types: Img.vt});
    if (await afterSave(res, 'Image changes')) { await Img.load(); await Img.open(Img.cur); }
  },
};
