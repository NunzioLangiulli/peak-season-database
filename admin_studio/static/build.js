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
  $('#apk').disabled = !s.flutter || !!s.running; $('#sync').disabled = !!s.running; $('#publish').disabled = !s.flutter || !!s.running; $('#gitpush').disabled = !!s.running;
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
    const ok = r.rc === 0, kind = r.kind; Build.job = null; Build.refresh(); if (window.Ver) Ver.refresh();
    if (kind === 'apk') modal(ok ? 'APK built ✓' : 'Build failed', ok
      ? '<p>The folder <code>build/app/outputs/flutter-apk/</code> is now open: copy <b>app-release.apk</b> to the phone (cable, Drive or e-mail) and open it to install. The first time, Android asks you to allow installs from that source.</p>'
      : '<p>Read the last lines of the log on the right. Common causes: Android licences not accepted (<code>flutter doctor --android-licenses</code>), missing Android SDK (<code>flutter doctor</code>).</p>');
    else if (kind === 'git') modal(ok ? 'Committed and pushed ✓' : 'Commit & Push stopped', ok ? '<p>Both repositories are on GitHub. Details in the log on the right.</p>' : '<p>Read the last lines of the log on the right: nothing after the failed step was done.</p>');
    else if (kind === 'publish') modal(ok ? 'Published ✓' : 'Publishing stopped', ok ? '<p>Both repositories are committed and pushed, and any missing release was created. Read the log on the right for the details.</p>' : '<p>Read the last lines of the log on the right: nothing after the failed step was done.</p>');
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

// ---------------------------------------------------------------- Build for iPhone (instructions)
$('#iphone_text').innerHTML = `<p>An iPhone app can only be compiled on a Mac with Xcode. This project uses a Mac in the cloud instead:
  <b>GitHub Actions</b> (workflow <code>app/.github/workflows/ios.yml</code>) builds an <b>unsigned .ipa</b> automatically.</p>
  <ol>
    <li><b>Automatic:</b> every time an app release is published on GitHub (for example with <b>Publish…</b> after raising the app version),
      the workflow builds <code>PeakSeason-&lt;version&gt;-unsigned.ipa</code>, attaches it to the release and adds the version to the
      SideStore source (<code>sidestore/source.json</code> in the app repository). It takes about 15-30 minutes.
      If the source update fails (the run shows an error after attaching the .ipa), in <code>app/</code> run <code>git pull</code>, then
      <code>python sidestore/update_source.py --version X --tag vX --ipa PeakSeason-X-unsigned.ipa --size &lt;ipa bytes&gt; --date &lt;release publishedAt&gt;</code>,
      then commit and push.</li>
    <li><b>By hand:</b> on github.com open <i>peak-season-app → Actions → iOS build → Run workflow</i>; the .ipa is in the run's artifacts.</li>
    <li><b>Install it on the iPhone:</b> download the .ipa and sign it with your own free Apple ID using
      <a href="https://sideloadly.io/" target="_blank" rel="noopener">Sideloadly</a> (Windows, with a cable) or AltStore/SideStore.
      With a free Apple ID the app must be re-signed every 7 days. On the iPhone, trust the profile in Settings → General → VPN & Device
      Management and enable Developer Mode (iOS 16+).</li>
    <li><b>App Store / TestFlight:</b> needs a paid Apple Developer account (99 USD/year) and signing certificates; it can be done with
      the same workflow or with Codemagic, but it is not set up.</li>
  </ol>`;

// ---------------------------------------------------------------- Publish and Commit & Push (summary, one message per repository)
async function repoDialog(kind) {
  if (Object.values(Studio.tabs).some(t => t.dirty())) return msg('Save or discard the unsaved changes first.', true);
  const isPub = kind === 'publish';
  modal(isPub ? 'Publish — checking…' : 'Commit & Push — checking…', '<p>Reading the state of the two repositories and the versions…</p>');
  const p = isPub ? await api.get('/api/publish/preview') : {repos: await api.get('/api/versions')};
  if (p.error) { $('#modal').hidden = true; return msg('Cannot prepare the summary:\n' + p.error, true); }
  const names = {database: 'Database', app: 'App'};
  const block = k => {
    const r = p.repos[k], g = r.git, pending = g.changes.length || g.unpushed_commits;
    const unreleased = r.current && r.released !== r.current;
    const on = pending || (isPub && unreleased && !r.release_exists);
    const rel = !isPub ? '' : r.release_exists ? `<div class="meta">v${esc(r.current)} is already released: no new release.</div>`
      : `<div class="meta"><b>v${esc(r.current)} has no release yet: a GitHub release will be created${k === 'app' ? ' with the APK (and the iPhone build starts)' : ''}.</b></div>`;
    return `<div class="box" style="margin-bottom:8px">
      <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-repo="${k}" ${on ? 'checked' : ''}>
        <b>${names[k]}</b> <span class="meta" style="margin:0">${esc(r.repo)} · v${esc(r.current)}${r.released ? ' (last release v' + esc(r.released) + ')' : ''}</span></label>
      <div class="meta" style="margin:4px 0">${g.changes.length ? g.changes.length + ' changed files' : 'no changes: nothing to commit'}${g.unpushed_commits ? ' · ' + g.unpushed_commits + ' commits not pushed' : ''}</div>
      ${g.changes.length ? '<ul class="filelist">' + g.changes.map(c => '<li><code>' + esc(c) + '</code></li>').join('') + '</ul>' : ''}
      ${rel}
      <label class="l">Commit message for ${names[k].toLowerCase()} (English, one line)</label>
      <input type="text" data-msg="${k}" style="width:100%" value="${esc(r.suggested_message || '')}" placeholder="${g.changes.length ? 'e.g. Update app code' : 'no changes'}">
    </div>`;
  };
  modal(isPub ? 'Publish' : 'Commit & Push', `<div id="pubsum">
    <p>${isPub ? 'Syncs the data into the app, validates the database, runs the app tests and builds the APK (only if the app is included), commits and pushes the selected repositories and creates the missing releases.'
      : 'Syncs the data into the app, validates the database, then commits and pushes the selected repositories. No APK and no release.'} It stops at the first error.</p>
    ${block('app')}${block('database')}
    <p class="meta">Style: English, one line, verb first, optional "Area:" prefix, no full stop. The proposal comes from the changed files; edit it as you like.
      The two repositories are independent: you can publish only the app and leave the database as it is.</p>
    <div class="mactions"><button class="btn primary" id="rgo">${isPub ? 'Publish Now' : 'Commit &amp; Push Now'}</button> <button class="btn" id="rno">Cancel</button></div></div>`);
  $('#m_ok').style.display = 'none';
  const close = () => { $('#modal').hidden = true; $('#m_ok').style.display = ''; };
  $('#rno').onclick = close;
  $('#rgo').onclick = async () => {
    const only = [...document.querySelectorAll('#pubsum [data-repo]')].filter(c => c.checked).map(c => c.dataset.repo);
    if (!only.length) return alert('Select at least one repository.');
    const messages = {};
    for (const k of only) {
      const v = document.querySelector(`#pubsum [data-msg=${k}]`).value.trim();
      if (!v && p.repos[k].git.changes.length) return alert(`Write the commit message for the ${names[k].toLowerCase()} repository.`);
      messages[k] = v;
    }
    close();
    const r = await api.post('/api/jobs', {kind, only, messages});
    if (!r.ok) return msg(r.report, true);
    Build.job = r.id; Build.next = 0; $('#log').hidden = false; $('#log').textContent = '';
    $('#apk').disabled = $('#sync').disabled = $('#publish').disabled = $('#gitpush').disabled = true; Build.poll();
  };
}
$('#publish').onclick = () => repoDialog('publish');
$('#gitpush').onclick = () => repoDialog('git');

// ---------------------------------------------------------------- Versions & Git
const Ver = {data: null};
window.Ver = Ver;               // other files refresh it after a job or a save (a const is not a window property)
Ver.refresh = async () => {
  const v = Ver.data = await api.get('/api/versions');
  const box = (key, name) => {
    const x = v[key], g = x.git, rel = x.released;
    const state = !rel ? '<span class="no">never released</span>'
      : rel === x.current ? '<span class="ok">released</span>' : `<span class="no">not released yet (last release v${esc(rel)})</span>`;
    return `<div style="border-bottom:1px dashed #e4e7df;padding:6px 0">
      <div style="display:flex;justify-content:space-between"><b>${name} v${esc(x.current)}</b>${state}</div>
      <div class="meta" style="margin:2px 0">${g.changes.length ? '<span class="no">' + g.changes.length + ' files not committed</span>' : '<span class="ok">all committed</span>'}
        ${g.unpushed_commits ? ' · <span class="no">' + g.unpushed_commits + ' commits not pushed</span>' : ''} · last: ${esc(g.last_commit)}</div>
      <div style="display:flex;gap:4px;align-items:center;flex-wrap:wrap"><span class="meta" style="margin:0">New version:</span>
        ${['patch', 'minor', 'major'].map(p => `<button class="btn small" data-t="${key}" data-v="${x.next[p]}" title="${p}">${x.next[p]}</button>`).join('')}
        <input type="text" placeholder="x.y.z" style="width:70px;padding:4px" data-custom="${key}"><button class="btn small" data-set="${key}">Set</button></div></div>`;
  };
  $('#versions').innerHTML = box('app', 'App') + box('database', 'Database') +
    '<div class="meta" style="margin-top:4px">Patch = fixes, minor = new features or content, major = breaking changes. A new version gets its GitHub release with <b>Publish…</b>.</div>';
  const set = async (target, version) => {
    if (!/^\d+\.\d+\.\d+$/.test(version)) return msg('Write the version as x.y.z, e.g. 1.2.0', true);
    if (!confirm(`Set the ${target} version to ${version}? It is written in ${target === 'app' ? 'app_info.dart, pubspec.yaml and the app README' : 'the database metadata and the README'}; nothing is published yet.`)) return;
    const r = await api.post('/api/versions/set', {target, version});
    msg(r.ok ? `${target === 'app' ? 'App' : 'Database'} version set to ${version}. Use Commit & Push or Publish to send it to GitHub.` : 'Not changed: ' + r.report, !r.ok);
    Ver.refresh(); Build.refresh();
  };
  document.querySelectorAll('#versions [data-v]').forEach(b => b.onclick = () => set(b.dataset.t, b.dataset.v));
  document.querySelectorAll('#versions [data-set]').forEach(b => b.onclick = () => set(b.dataset.set, $(`#versions [data-custom=${b.dataset.set}]`).value.trim()));
};
Ver.refresh();

