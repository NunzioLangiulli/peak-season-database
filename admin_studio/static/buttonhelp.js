// "?" bubbles next to the Studio buttons whose effect is not obvious: hover to read what the button does (and does not do), click to pin it.
// Rules are matched by CSS selector; new buttons drawn later by the tabs get their bubble automatically.
const BUTTON_HELP = [
  // only buttons whose effect is not obvious from the label or the page description
  ['#save', 'Saves the changes of the open tab, checks the database and updates the app files. If the check finds errors nothing is saved and the files go back as they were. It does NOT commit to Git, push to GitHub or build the APK.'],
  ['#imp', 'Loads a CSV edited in Excel into the open tab. Changes are only shown on screen: press Save Changes to keep them. Rows with unknown keys or products are skipped.'],
  // build panel
  ['#sync', 'Copies the database, texts, icons and new photos into the app folder (app/assets) and converts new photos to WebP. It does NOT build the APK, commit or publish.'],
  ['#apk', 'Syncs the app files and builds the Android APK (a few minutes), then opens its folder. It does NOT commit, push or create a GitHub release.'],
  ['#gitpush', 'Syncs the app files, checks the database, then commits and pushes both repositories to GitHub after showing you the changed files. It does NOT build the APK and does NOT create releases.'],
  ['#publish', 'Does everything in one go after a summary: sync, database check, app tests, APK build, commit and push of both repositories, and a GitHub release (with the APK) for any version that has none yet. It stops at the first error. It does NOT raise the version: choose the new version first.'],
  // tabs
  ['#nb', 'Adds an empty corpus entry with this key. It is not used by any product until you link it in Product Texts.'],
  ['#dl_go', 'Downloads the photo, reads author and licence (Wikimedia Commons, USDA ARS), adds it to the gallery and checks the database. It does not publish anything; without author and licence the photo is refused.'],
  ['.row label.btn.small', 'Uploads a logo from your computer for this source: the light background is removed and the logo is resized for the app. The app shows it after Sync App or Publish.'],
];

const HelpTip = {box: null, pinned: null};
HelpTip.show = (q, pin) => {
  if (!HelpTip.box) { HelpTip.box = document.createElement('div'); HelpTip.box.className = 'qtip'; document.body.append(HelpTip.box); }
  const b = HelpTip.box, r = q.getBoundingClientRect();
  b.textContent = q.dataset.tip; b.style.display = 'block';
  const left = Math.min(window.innerWidth - b.offsetWidth - 10, Math.max(10, r.left - 10));
  const top = r.bottom + 6 + b.offsetHeight > window.innerHeight ? r.top - b.offsetHeight - 6 : r.bottom + 6;
  b.style.left = left + 'px'; b.style.top = top + 'px'; b.classList.toggle('pinned', !!pin);
  HelpTip.pinned = pin ? q : null;
};
HelpTip.hide = force => { if (HelpTip.box && (force || !HelpTip.pinned)) { HelpTip.box.style.display = 'none'; HelpTip.pinned = null; } };

function attachButtonHelp() {
  for (const [sel, text] of BUTTON_HELP) {
    document.querySelectorAll(sel).forEach(el => {
      if (el.dataset.hasHelp) return;
      el.dataset.hasHelp = '1';
      const q = document.createElement('span'); q.className = 'qhelp'; q.textContent = '?'; q.dataset.tip = text;
      q.setAttribute('role', 'button'); q.setAttribute('aria-label', 'What this button does');
      q.onmouseenter = () => { if (!HelpTip.pinned) HelpTip.show(q); };
      q.onmouseleave = () => HelpTip.hide();
      q.onclick = e => { e.stopPropagation(); e.preventDefault(); if (HelpTip.pinned === q) HelpTip.hide(true); else HelpTip.show(q, true); };
      el.insertAdjacentElement('afterend', q);
    });
  }
}
document.addEventListener('click', () => HelpTip.hide(true));
window.addEventListener('scroll', () => HelpTip.hide(true), true);
new MutationObserver(() => attachButtonHelp()).observe(document.body, {childList: true, subtree: true});
attachButtonHelp();
