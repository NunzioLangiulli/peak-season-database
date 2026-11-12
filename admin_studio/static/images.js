// Scheda Immagini: galleria di ogni prodotto, foto principale, tipo di vista, ricerca e download di nuove foto.
const VT_LABEL = {full_frame: 'Intero (riempie la foto)', isolated_background: 'Intero su sfondo', plant_in_field: 'Pianta in campo',
  botanical_plate: 'Tavola botanica', cut_section: 'Sezione / tagliato', other: 'Altro'};
const Img = {list: [], cur: null, item: null, primary: null, vt: {}};

Img.load = async () => { Img.list = await api.get('/api/images/items'); };
Img.open = async id => {
  Img.cur = id; Img.item = await api.get('/api/images/item?id=' + encodeURIComponent(id));
  Img.primary = Img.item.primary; Img.vt = {}; render();
};
Img.dirty = () => (Img.item && Img.primary !== Img.item.primary ? 1 : 0) + Object.keys(Img.vt).length;

Studio.tabs.images = {
  placeholder: 'Cerca prodotto (nome italiano, inglese o id)…', load: Img.load, dirty: Img.dirty,
  render(m, q) {
    const nq = norm(q), wrap = document.createElement('div'); wrap.className = 'imgwrap';
    const pl = document.createElement('div'); pl.className = 'plist';
    Img.list.filter(p => !nq || norm(p.name + ' ' + p.name_en + ' ' + p.id).includes(nq)).forEach(p => {
      const d = document.createElement('div'); d.className = p.id === Img.cur ? 'on' : '';
      d.innerHTML = '<span>' + esc(p.name) + '</span><small>' + p.count + ' foto</small>';
      d.onclick = () => { if (Img.dirty() && !confirm('Ci sono modifiche non salvate su questo prodotto. Cambiare prodotto?')) return; Img.open(p.id); };
      pl.append(d);
    });
    const right = document.createElement('div');
    wrap.append(pl, right); m.append(wrap);
    if (!Img.item) { right.innerHTML = '<div class="empty">Scegli un prodotto dall\'elenco a sinistra.</div>'; return; }
    const it = Img.item;
    right.insertAdjacentHTML('beforeend', `<div class="box"><h3>${esc(it.name)} · <i>${esc(it.scientific_name || '')}</i> · ${it.images.length} foto</h3>
      <div class="meta">Stella = foto principale (card e Home). Il tipo di vista decide come l'app usa la foto. Clic sulla foto = originale a piena risoluzione.</div></div>`);
    const grid = document.createElement('div'); grid.className = 'grid';
    it.images.forEach(d => {
      const f = d.filename, isP = f === Img.primary, vt = Img.vt[f] || d.view_type;
      const c = document.createElement('div'); c.className = 'ph' + (isP ? ' primary' : '') + ((Img.vt[f] || (isP && Img.primary !== it.primary)) ? ' changed' : '');
      c.innerHTML = `<img loading="lazy" src="/img/${esc(f)}" alt="${esc(f)}">
        <div class="c"><div class="meta" style="margin:0;justify-content:space-between"><b>${esc(f.replace(it.id + '_', '#').replace('.jpg', ''))}</b>
        <span class="star ${isP ? 'on' : ''}" title="Imposta come foto principale">★</span></div>
        <div class="credit" title="${esc((d.author || '') + ' · ' + (d.license || ''))}">${esc(d.author || 'autore ?')} · ${esc(d.license || 'licenza ?')}</div>
        ${(d.flags || []).length ? '<div class="no">Segnalata: ' + esc(d.flags.join(', ')) + '</div>' : ''}
        <select>${it.view_types.map(v => `<option value="${v}" ${v === vt ? 'selected' : ''}>${VT_LABEL[v] || v}</option>`).join('')}</select></div>`;
      c.querySelector('img').onclick = () => window.open('/img/' + f + '?full=1', '_blank');
      c.querySelector('.star').onclick = () => { Img.primary = f; render(); };
      c.querySelector('select').onchange = e => { if (e.target.value === d.view_type) delete Img.vt[f]; else Img.vt[f] = e.target.value; refreshDirty(); c.classList.add('changed'); };
      grid.append(c);
    });
    right.append(grid);
    // ricerca di nuove foto e download
    right.insertAdjacentHTML('beforeend', `<div class="box" style="margin-top:14px"><h3>Cerca nuove foto</h3><div class="links">${
      it.links.map(l => `<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)} ↗</a>`).join('')}</div>
      <div class="meta" style="margin-top:6px">Preferisci foto con licenza libera (CC BY, CC BY-SA, CC0, pubblico dominio). Le foto USDA ARS sono di pubblico dominio.</div></div>
      <div class="box"><h3>Scarica una foto da URL</h3>
      <div class="form">
        <input class="full" type="url" id="dl_url" placeholder="Incolla l'indirizzo: pagina Wikimedia Commons (File:…), foto upload.wikimedia.org, pagina o foto USDA ARS, oppure un'immagine qualsiasi">
        <div><label class="l">Tipo di vista</label><select id="dl_vt">${it.view_types.map(v => `<option value="${v}">${VT_LABEL[v] || v}</option>`).join('')}</select></div>
        <div><label class="l">&nbsp;</label><label><input type="checkbox" id="dl_primary"> Rendila la foto principale</label></div>
        <div><label class="l">Autore (solo se la fonte non lo indica)</label><input type="text" id="dl_author" placeholder="es. Mario Rossi / Wikimedia Commons"></div>
        <div><label class="l">Licenza (solo se la fonte non la indica)</label><input type="text" id="dl_license" placeholder="es. CC BY-SA 4.0"></div>
        <div class="full"><label class="l">URL della licenza (facoltativo)</label><input type="url" id="dl_lurl" placeholder="https://creativecommons.org/licenses/by-sa/4.0/"></div>
        <div class="full"><button class="btn primary" id="dl_go">Scarica e Aggiungi alla Galleria</button> <span id="dl_state" class="meta"></span></div>
      </div></div>`);
    $('#dl_go').onclick = async () => {
      const url = $('#dl_url').value.trim(); if (!url) return msg('Incolla prima un indirizzo.', true);
      $('#dl_go').disabled = true; $('#dl_state').textContent = 'Scarico, leggo i metadati e valido…';
      const res = await api.post('/api/images/download', {id: it.id, url, view_type: $('#dl_vt').value, make_primary: $('#dl_primary').checked,
        author: $('#dl_author').value, license: $('#dl_license').value, license_url: $('#dl_lurl').value});
      $('#dl_go').disabled = false; $('#dl_state').textContent = '';
      if (await afterSave(res, 'Nuova foto ' + (res.added ? res.added.filename : ''))) {
        msg('Aggiunta ' + res.added.filename + ' · ' + res.added.author + ' · ' + res.added.license);
        await Img.load(); await Img.open(it.id);
      }
    };
  },
  async save() {
    const res = await api.post('/api/images/save', {id: Img.cur, primary: Img.primary, view_types: Img.vt});
    if (await afterSave(res, 'Modifiche alle immagini')) { await Img.load(); await Img.open(Img.cur); }
  },
};
