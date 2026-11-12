// Pannello Build & Deploy: stato di sincronizzazione, sincronizzazione degli asset e compilazione dell'APK con log dal vivo.
const Build = {job: null, next: 0};

Build.refresh = async () => {
  const s = Studio.status = await api.get('/api/status');
  const row = (k, ok, v) => `<div><span>${k}</span><span class="${ok ? 'ok' : 'no'}">${esc(v)}</span></div>`;
  $('#status').innerHTML =
    row('Database → app', s.database === 'ok', s.database === 'ok' ? 'aggiornato' : s.database) +
    row('Testi app', s.ui_copy === 'ok', s.ui_copy === 'ok' ? 'aggiornati' : s.ui_copy) +
    row('Icone app', s.ui_config === 'ok', s.ui_config === 'ok' ? 'aggiornate' : s.ui_config) +
    row('Foto senza WebP', !s.images_without_webp, String(s.images_without_webp)) +
    row('APK', s.apk.exists && !s.apk.stale, s.apk.exists ? (s.apk.stale ? 'da ricompilare (' + s.apk.time + ')' : s.apk.time) : 'mai compilato') +
    row('Flutter', !!s.flutter, s.flutter ? 'trovato' : 'non trovato');
  $('#howto_text').innerHTML = howtoHtml();
  $('#apk').disabled = !s.flutter || !!s.running; $('#sync').disabled = !!s.running;
  if (s.running && !Build.job) { Build.job = s.running; Build.next = 0; Build.poll(); }
};

Build.start = async kind => {
  const r = await api.post('/api/jobs', {kind});
  if (!r.ok) return msg(r.report, true);
  Build.job = r.id; Build.next = 0; $('#log').hidden = false; $('#log').textContent = '';
  $('#apk').disabled = $('#sync').disabled = true; Build.poll();
};

Build.poll = async () => {
  if (!Build.job) return;
  const r = await api.get('/api/jobs/' + Build.job + '?from=' + Build.next);
  const log = $('#log'); log.hidden = false;
  if (r.lines && r.lines.length) {
    const atEnd = log.scrollTop + log.clientHeight >= log.scrollHeight - 30;
    log.textContent += r.lines.join('\n') + '\n'; Build.next = r.next;
    if (atEnd) log.scrollTop = log.scrollHeight;
  }
  if (r.done) {
    const ok = r.rc === 0, kind = r.kind; Build.job = null; Build.refresh();
    if (kind === 'apk') modal(ok ? 'APK compilato ✓' : 'Compilazione non riuscita', ok
      ? '<p>Si è aperta la cartella <code>build/app/outputs/flutter-apk/</code>: copia <b>app-release.apk</b> sul telefono (cavo, Drive o e-mail) e aprilo per installarlo. Android chiede di consentire l\'installazione da questa fonte la prima volta.</p>'
      : '<p>Leggi le ultime righe del log a destra. Problemi frequenti: licenze Android non accettate (<code>flutter doctor --android-licenses</code>), Android SDK mancante (<code>flutter doctor</code>).</p>');
    else if (ok) msg('Sincronizzazione completata ✓');
    return;
  }
  setTimeout(Build.poll, 700);
};

$('#sync').onclick = () => Build.start('sync');
$('#apk').onclick = () => { if (confirm('Compilare l\'APK Android in versione release? Può richiedere alcuni minuti.')) Build.start('apk'); };
$('#apkdir').onclick = async () => { const r = await api.post('/api/open_apk_folder', {}); if (!r.ok) msg('La cartella dell\'APK non esiste ancora: compila prima l\'APK.', true); };
window.Build = Build;
Build.refresh(); setInterval(() => { if (!Build.job) Build.refresh(); }, 15000);
