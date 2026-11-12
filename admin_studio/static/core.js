// Peak Season Admin Studio: funzioni comuni a tutte le schede.
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const norm = s => String(s ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
const api = {
  get: async u => (await fetch(u)).json(),
  post: async (u, body) => (await fetch(u, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)})).json(),
};

// Ogni scheda si registra con: render(main, query), dirty() -> numero, save() -> risposta del server, csv (facoltativo), placeholder
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
    <li>I file dell'app sono già sincronizzati (database, testi, icone e foto nuove in <code>app/assets</code>).</li>
    <li><b>App già aperta con <code>flutter run</code>:</b> nel terminale di Flutter premi <b>R</b> maiuscola (<i>Hot Restart</i>). I dati JSON si rileggono solo al riavvio: la <b>r</b> minuscola (Hot Reload) non basta.</li>
    <li><b>App non aperta:</b> in un terminale <code>cd ${app}</code> e poi <code>${fl} run</code> (scegli il dispositivo o il browser).</li>
    <li><b>Sul telefono senza cavo:</b> premi <b>Compila APK Android</b> qui a destra e installa <code>app-release.apk</code> dalla cartella che si apre.</li>
  </ol>`;
}

function refreshDirty() {
  const t = Studio.tabs[Studio.tab], n = t.dirty();
  $('#dirty').textContent = n ? n + ' modifiche non salvate' : '';
  $('#save').disabled = !n;
}

function render() {
  const t = Studio.tabs[Studio.tab];
  $('#q').placeholder = t.placeholder || 'Cerca…';
  $('#csv').style.display = t.csv ? '' : 'none';
  const m = $('#main'); m.innerHTML = '';
  t.render(m, Studio.q);
  refreshDirty();
}

async function afterSave(res, what) {
  if (res.ok) {
    modal(what + ' salvate e validate ✓', howtoHtml() + (res.sync_ok === false ? '<p class="no">Attenzione: la sincronizzazione con l\'app non è riuscita, premi "Sincronizza App".</p>' : ''));
    msg('Validazione:\n' + (res.report || '').split('\n').slice(0, 4).join('\n'));
  } else {
    msg('NON salvato: ' + (res.report || 'errore sconosciuto') + '\n(i file sono tornati com\'erano)', true);
  }
  if (window.Build) Build.refresh();
  return res.ok;
}

document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => {
  const cur = Studio.tabs[Studio.tab];
  if (cur.dirty() && !confirm('Ci sono modifiche non salvate in questa scheda. Cambiare scheda comunque? (restano in memoria finché non chiudi la pagina)')) return;
  document.querySelectorAll('#tabs button').forEach(x => x.classList.remove('on'));
  b.classList.add('on'); Studio.tab = b.dataset.t; Studio.q = ''; $('#q').value = ''; render();
});
let tq; $('#q').oninput = e => { clearTimeout(tq); tq = setTimeout(() => { Studio.q = e.target.value; render(); }, 120); };
$('#save').onclick = async () => {
  const t = Studio.tabs[Studio.tab];
  $('#save').disabled = true; $('#save').textContent = 'Salvataggio…';
  try { await t.save(); } finally { $('#save').textContent = 'Salva Modifiche'; refreshDirty(); }
};
window.onbeforeunload = e => { if (Object.values(Studio.tabs).some(t => t.dirty())) { e.preventDefault(); e.returnValue = ''; } };
window.addEventListener('DOMContentLoaded', async () => {
  for (const t of Object.values(Studio.tabs)) if (t.load) await t.load();
  render();
});
