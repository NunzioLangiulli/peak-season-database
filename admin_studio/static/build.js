// Build & Deploy panel: sync status, asset sync and APK build with a live log.
const Build = {job: null, next: 0};

Build.refresh = async () => {
  const s = Studio.status = await api.get('/api/status');
  const row = (k, ok, v) => `<div><span>${k}</span><span class="${ok ? 'ok' : 'no'}">${esc(v)}</span></div>`;
  const st = v => ({'ok': 'up to date', 'da sincronizzare': 'needs sync', 'assente': 'missing'}[v] || v);
  $('#status').innerHTML =
    row('Database → app', s.database === 'ok', st(s.database)) +
    row('App copy', s.ui_copy === 'ok', st(s.ui_copy)) +
    row('App icons', s.ui_config === 'ok', st(s.ui_config)) +
    row('Photos without WebP', !s.images_without_webp, String(s.images_without_webp)) +
    row('APK', s.apk.exists && !s.apk.stale, s.apk.exists ? (s.apk.stale ? 'needs rebuild (' + s.apk.time + ')' : s.apk.time) : 'never built') +
    row('Flutter', !!s.flutter, s.flutter ? 'found' : 'not found');
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
    if (kind === 'apk') modal(ok ? 'APK built ✓' : 'Build failed', ok
      ? '<p>The folder <code>build/app/outputs/flutter-apk/</code> is now open: copy <b>app-release.apk</b> to the phone (cable, Drive or e-mail) and open it to install. The first time, Android asks you to allow installs from that source.</p>'
      : '<p>Read the last lines of the log on the right. Common causes: Android licences not accepted (<code>flutter doctor --android-licenses</code>), missing Android SDK (<code>flutter doctor</code>).</p>');
    else if (ok) msg('Sync completed ✓');
    return;
  }
  setTimeout(Build.poll, 700);
};

$('#sync').onclick = () => Build.start('sync');
$('#apk').onclick = () => { if (confirm('Build the Android APK in release mode? It can take a few minutes.')) Build.start('apk'); };
$('#apkdir').onclick = async () => { const r = await api.post('/api/open_apk_folder', {}); if (!r.ok) msg('The APK folder does not exist yet: build the APK first.', true); };
window.Build = Build;
Build.refresh(); setInterval(() => { if (!Build.job) Build.refresh(); }, 15000);
