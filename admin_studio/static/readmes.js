// READMEs tab: edit the README files published on GitHub, with a live preview close to GitHub's rendering.
const Rd = {files: [], cur: null, edits: {}, view: localStorage.getItem('readme_view') || 'both'};
Rd.load = async () => { Rd.files = (await api.get('/api/readmes')).files; Rd.edits = {}; if (!Rd.cur && Rd.files.length) Rd.cur = Rd.files[0].path; };
Rd.text = f => Rd.edits[f.path] ?? f.content;

// Small Markdown renderer (headings, paragraphs, lists, code, quotes, tables, links, images, bold/italic, rules).
function mdInline(t) {
  t = esc(t);
  const codes = [];
  t = t.replace(/`([^`]+)`/g, (m, c) => { codes.push(c); return '\u0000' + (codes.length - 1) + '\u0000'; });
  t = t.replace(/!\[([^\]]*)\]\(([^)\s]+)[^)]*\)/g, (m, alt) => `<span class="mdimg">🖼 ${alt || 'image'}</span>`)
       .replace(/\[([^\]]+)\]\(([^)\s]+)[^)]*\)/g, (m, txt, url) => `<a href="${url}" target="_blank" rel="noopener">${txt}</a>`)
       .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/__([^_]+)__/g, '<b>$1</b>')
       .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<i>$2</i>').replace(/(^|\W)_([^_\s][^_]*)_(?=\W|$)/g, '$1<i>$2</i>');
  return t.replace(/\u0000(\d+)\u0000/g, (m, i) => '<code>' + codes[+i] + '</code>');
}
function mdRender(src) {
  const L = src.replace(/\r\n/g, '\n').split('\n'), out = [];
  let i = 0;
  const isTableSep = s => /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$/.test(s);
  const cells = s => s.trim().replace(/^\||\|$/g, '').split('|').map(c => mdInline(c.trim()));
  while (i < L.length) {
    const l = L[i];
    if (/^```/.test(l)) {
      const code = []; i++;
      while (i < L.length && !/^```/.test(L[i])) code.push(L[i++]);
      i++; out.push('<pre><code>' + esc(code.join('\n')) + '</code></pre>'); continue;
    }
    let m;
    if ((m = l.match(/^(#{1,6})\s+(.*)$/))) { out.push(`<h${m[1].length}>${mdInline(m[2])}</h${m[1].length}>`); i++; continue; }
    if (/^\s*(---+|\*\*\*+)\s*$/.test(l)) { out.push('<hr>'); i++; continue; }
    if (/^\s*\|/.test(l) && i + 1 < L.length && isTableSep(L[i + 1])) {
      let h = '<table><tr>' + cells(l).map(c => '<th>' + c + '</th>').join('') + '</tr>'; i += 2;
      while (i < L.length && /^\s*\|/.test(L[i])) h += '<tr>' + cells(L[i++]).map(c => '<td>' + c + '</td>').join('') + '</tr>';
      out.push(h + '</table>'); continue;
    }
    if (/^>\s?/.test(l)) {
      const q = []; while (i < L.length && /^>\s?/.test(L[i])) q.push(L[i++].replace(/^>\s?/, ''));
      out.push('<blockquote>' + mdRender(q.join('\n')) + '</blockquote>'); continue;
    }
    if (/^\s*([-*+]|\d+\.)\s+/.test(l)) {
      const ordered = /^\s*\d+\./.test(l), items = [];
      while (i < L.length && (/^\s*([-*+]|\d+\.)\s+/.test(L[i]) || (/^\s{2,}\S/.test(L[i]) && items.length))) {
        const x = L[i++];
        if (/^\s*([-*+]|\d+\.)\s+/.test(x) && !/^\s{2,}/.test(x)) items.push(x.replace(/^\s*([-*+]|\d+\.)\s+/, ''));
        else items[items.length - 1] += '\n' + x.replace(/^\s{2,3}/, '');
      }
      const tag = ordered ? 'ol' : 'ul';
      out.push(`<${tag}>` + items.map(x => '<li>' + (x.includes('\n') ? mdRender(x) : mdInline(x)) + '</li>').join('') + `</${tag}>`); continue;
    }
    if (!l.trim()) { i++; continue; }
    const p = [];
    while (i < L.length && L[i].trim() && !/^(#{1,6}\s|```|>|\s*([-*+]|\d+\.)\s|\s*\|)/.test(L[i])) p.push(L[i++]);
    if (!p.length) p.push(L[i++]);
    out.push('<p>' + p.map(mdInline).join(' ') + '</p>');
  }
  return out.join('\n');
}

Studio.tabs.readmes = {
  placeholder: 'Search in the README files…', load: Rd.load, dirty: () => Object.keys(Rd.edits).length,
  render(m, q) {
    const nq = norm(q), files = Rd.files.filter(f => !nq || norm(f.path + ' ' + Rd.text(f)).includes(nq));
    if (nq && files.length && !files.some(f => f.path === Rd.cur)) Rd.cur = files[0].path;
    const f = Rd.files.find(x => x.path === Rd.cur);
    const bar = document.createElement('div'); bar.className = 'box';
    const group = (repo, title) => {
      const fs = files.filter(x => x.repo === repo);
      if (!fs.length) return '';
      return `<div class="rdgroup"><div class="rdgtitle">${title} <span class="meta" style="margin:0">${esc(repo)}</span></div>` +
        fs.map(x => `<button class="btn small ${x.path === Rd.cur ? 'primary' : ''}" data-p="${esc(x.path)}">${esc(x.path.replace(/^app\//, ''))}${Rd.edits[x.path] !== undefined ? ' •' : ''}</button>`).join(' ') + '</div>';
    };
    const views = [['code', 'Code'], ['preview', 'Preview'], ['both', 'Both']];
    bar.innerHTML = `<div class="rdtop"><div class="rdgroups">${group('peak-season-database', 'Database repository')}${group('peak-season-app', 'App repository')}</div>
      <div class="rdview"><span class="meta" style="margin:0">View:</span>${views.map(([v, l]) => `<button class="btn small ${Rd.view === v ? 'primary' : ''}" data-view="${v}">${l}</button>`).join('')}</div></div>` +
      (f ? `<div class="meta" style="margin-top:6px">${esc(f.description)} · published on GitHub with Commit &amp; Push or Publish. Write it in English.</div>` : '');
    bar.querySelectorAll('[data-p]').forEach(b => b.onclick = () => { Rd.cur = b.dataset.p; render(); });
    bar.querySelectorAll('[data-view]').forEach(b => b.onclick = () => { Rd.view = b.dataset.view; localStorage.setItem('readme_view', Rd.view); render(); });
    m.append(bar);
    if (!f) { m.insertAdjacentHTML('beforeend', '<div class="empty">No results</div>'); return; }
    const wrap = document.createElement('div'); wrap.className = 'mdwrap';
    const ta = document.createElement('textarea'); ta.className = 'mdedit'; ta.value = Rd.text(f); ta.spellcheck = false;
    const pv = document.createElement('div'); pv.className = 'mdprev';
    const draw = () => { pv.innerHTML = mdRender(ta.value); };
    let t; ta.oninput = () => {
      if (ta.value === f.content) delete Rd.edits[f.path]; else Rd.edits[f.path] = ta.value;
      refreshDirty(); clearTimeout(t); t = setTimeout(draw, 150);
    };
    ta.onscroll = () => { pv.scrollTop = (ta.scrollTop / Math.max(1, ta.scrollHeight - ta.clientHeight)) * (pv.scrollHeight - pv.clientHeight); };
    const left = document.createElement('div'); left.innerHTML = '<label class="l">Markdown</label>'; left.append(ta);
    const right = document.createElement('div'); right.innerHTML = '<label class="l">Preview (close to how GitHub shows it)</label>'; right.append(pv);
    wrap.classList.add('view-' + Rd.view);
    wrap.append(left, right); m.append(wrap); draw();
  },
  async save() {
    let ok = true, last = null;
    for (const [path, content] of Object.entries(Rd.edits)) {
      last = await api.post('/api/readmes/save', {path, content});
      if (!last.ok) { ok = false; msg('NOT saved: ' + last.report, true); break; }
    }
    if (ok) { msg('README files saved. They reach GitHub with Commit & Push or Publish.'); await Rd.load(); render(); if (window.Ver) Ver.refresh(); }
  },
};
