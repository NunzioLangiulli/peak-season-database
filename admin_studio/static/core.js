// Peak Season Admin Studio: helpers shared by all tabs.
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const norm = s => String(s ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
const api = {
  get: async u => (await fetch(u)).json(),
  post: async (u, body) => (await fetch(u, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)})).json(),
};

// Each tab registers: render(main, query), dirty() -> count, save() -> server reply, csv (optional), placeholder
const Studio = {tabs: {}, tab: 'ui', q: '', status: null};

function msg(t, err) {
  const m = $('#msg'); m.textContent = t; m.className = err ? 'err' : ''; m.style.display = 'block';
  clearTimeout(m._t); m._t = setTimeout(() => m.style.display = 'none', err ? 40000 : 8000);
  m.onclick = () => m.style.display = 'none';
}

function modal(title, html) {
  $('#m_title').textContent = title; $('#m_body').innerHTML = html; $('#modal').hidden = false;
  $('#m_ok').onclick = () => $('#modal').hidden = true;
}

function howtoHtml() {
  const s = Studio.status || {}, app = esc(s.app_dir || 'C:\\dev\\peak_season'), fl = esc(s.flutter || 'flutter');
  return `<ol>
    <li>The app files are already synced (database, copy, icons and new photos in <code>app/assets</code>).</li>
    <li><b>App already running with <code>flutter run</code>:</b> press capital <b>R</b> in the Flutter terminal (<i>Hot Restart</i>). JSON data is only re-read on restart: lowercase <b>r</b> (Hot Reload) is not enough.</li>
    <li><b>App not running:</b> in a terminal run <code>cd ${app}</code> and then <code>${fl} run</code> (pick the device or the browser).</li>
    <li><b>On the phone without a cable:</b> press <b>Build Android APK</b> on the right and install <code>app-release.apk</code> from the folder that opens.</li>
  </ol>`;
}

function refreshDirty() {
  const t = Studio.tabs[Studio.tab], n = t.dirty();
  $('#dirty').textContent = n ? n + ' unsaved change' + (n === 1 ? '' : 's') : '';
  $('#save').disabled = !n;
}

function render() {
  const t = Studio.tabs[Studio.tab];
  $('#q').placeholder = t.placeholder || 'Search…';
  $('#csv').style.display = t.csv ? '' : 'none';
  const m = $('#main'); m.innerHTML = '';
  t.render(m, Studio.q);
  refreshDirty();
}

async function afterSave(res, what) {
  if (res.ok) {
    modal(what + ' saved and validated ✓', howtoHtml() + (res.sync_ok === false ? '<p class="no">Warning: syncing with the app failed, press "Sync App".</p>' : ''));
    msg('Validation:\n' + (res.report || '').split('\n').slice(0, 4).join('\n'));
  } else {
    msg('NOT saved: ' + (res.report || 'unknown error') + '\n(the files were restored)', true);
  }
  if (window.Build) Build.refresh();
  return res.ok;
}

document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => {
  const cur = Studio.tabs[Studio.tab];
  if (cur.dirty() && !confirm('This tab has unsaved changes. Switch tab anyway? (they stay in memory until you close the page)')) return;
  document.querySelectorAll('#tabs button').forEach(x => x.classList.remove('on'));
  b.classList.add('on'); Studio.tab = b.dataset.t; Studio.q = ''; $('#q').value = ''; render();
});
let tq; $('#q').oninput = e => { clearTimeout(tq); tq = setTimeout(() => { Studio.q = e.target.value; render(); }, 120); };
$('#save').onclick = async () => {
  const t = Studio.tabs[Studio.tab];
  $('#save').disabled = true; $('#save').textContent = 'Saving…';
  try { await t.save(); } finally { $('#save').textContent = 'Save Changes'; refreshDirty(); }
};
window.onbeforeunload = e => { if (Object.values(Studio.tabs).some(t => t.dirty())) { e.preventDefault(); e.returnValue = ''; } };
window.addEventListener('DOMContentLoaded', async () => {
  for (const t of Object.values(Studio.tabs)) if (t.load) await t.load();
  render();
});
