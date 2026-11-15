// Navigation shared by all tabs: collapsible sections (open/closed state remembered per tab) and a floating index
// for long pages, with "expand all" / "collapse all" and a filter.
const Nav = {state: {}, panel: false};
Nav.key = k => Studio.tab + '|' + k;
Nav.isOpen = (k, def) => { const v = Nav.state[Nav.key(k)]; return v === undefined ? def : v; };

// Collapsible section. title is HTML (escape it); fill(body) runs the first time the section is open (lazy pages).
Nav.sec = (parent, {key, title, count, open = true, fill, cls = '', sub = ''}) => {
  const d = document.createElement('details'); d.className = 'sec ' + cls; d.dataset.key = key;
  d.open = Nav.isOpen(key, open);
  d.innerHTML = `<summary><span class="st">${title}</span>${sub ? `<span class="ss">${sub}</span>` : ''}${count != null ? `<span class="cnt">${count}</span>` : ''}</summary>`;
  const body = document.createElement('div'); body.className = 'secb'; d.append(body);
  let filled = !fill;
  const doFill = () => { if (!filled) { filled = true; fill(body); } };
  if (d.open) doFill();
  d.addEventListener('toggle', () => { Nav.state[Nav.key(key)] = d.open; if (d.open) doFill(); });
  parent.append(d); return body;
};

// Tabs that print flat headings (.grp / .prod followed by rows) get them turned into collapsible sections.
Nav.wrapFlat = m => {
  let body = null;
  [...m.children].forEach(el => {
    if (el.matches('.grp, .prod')) {
      const tmp = document.createElement('div');
      body = Nav.sec(tmp, {key: el.textContent.trim(), title: el.innerHTML, cls: el.classList.contains('prod') ? 'lv2' : ''});
      m.insertBefore(tmp.firstChild, el); el.remove();
    } else if (body) body.append(el);
  });
};

Nav.after = m => { Nav.wrapFlat(m); Nav.toc(m); };

Nav.sections = m => [...m.querySelectorAll('details.sec')].map(d => {
  let lv = 0; for (let p = d.parentElement.closest('details.sec'); p; p = p.parentElement.closest('details.sec')) lv++;
  return {d, lv, title: d.querySelector(':scope > summary .st').textContent, count: (d.querySelector(':scope > summary .cnt') || {}).textContent || ''};
}).filter(s => s.lv < 2);

Nav.toc = m => {
  let btn = $('#navbtn');
  if (!btn) {
    btn = document.createElement('button'); btn.id = 'navbtn'; btn.className = 'btn primary'; btn.title = 'Page index';
    btn.innerHTML = '☰ Index'; document.body.append(btn);
    const p = document.createElement('div'); p.id = 'navpanel'; p.hidden = true; document.body.append(p);
    btn.onclick = () => { Nav.panel = !Nav.panel; Nav.draw(); };
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && Nav.panel) { Nav.panel = false; Nav.draw(); } });
  }
  const many = Nav.sections(m).length >= 3 || document.documentElement.scrollHeight > innerHeight * 1.6;
  btn.hidden = !many; if (!many) Nav.panel = false;
  Nav.draw();
};

Nav.draw = () => {
  const p = $('#navpanel'); p.hidden = !Nav.panel; if (!Nav.panel) return;
  const secs = Nav.sections($('#main'));
  p.innerHTML = `<div class="nh"><b>Index</b> <span class="meta" style="margin:0">${secs.filter(s => !s.lv).length} sections</span>
      <button class="btn small" data-a="top">↑ Top</button><button class="btn small" data-a="open">Expand all</button>
      <button class="btn small" data-a="close">Collapse all</button><button class="btn small" data-a="x">✕</button></div>
    <input type="search" placeholder="Filter the index…" id="navq"><div class="nl"></div>`;
  const list = p.querySelector('.nl');
  const fill = q => {
    list.innerHTML = ''; const nq = norm(q);
    secs.forEach(s => {
      if (nq && !norm(s.title).includes(nq)) return;
      const a = document.createElement('a'); a.className = 'lv' + s.lv + (s.d.open ? '' : ' shut');
      a.innerHTML = `<span>${esc(s.title)}</span><small>${esc(s.count)}</small>`;
      a.onclick = () => {
        for (let d = s.d; d; d = d.parentElement.closest('details.sec')) d.open = true;
        s.d.scrollIntoView({block: 'start'}); a.classList.remove('shut');
      };
      list.append(a);
    });
  };
  fill('');
  p.querySelector('#navq').oninput = e => fill(e.target.value);
  p.querySelectorAll('[data-a]').forEach(b => b.onclick = () => {
    const a = b.dataset.a;
    if (a === 'top') scrollTo({top: 0});
    if (a === 'x') { Nav.panel = false; Nav.draw(); return; }
    if (a === 'open' || a === 'close') { secs.filter(s => !s.lv).forEach(s => s.d.open = a === 'open'); Nav.draw(); }
  });
};
