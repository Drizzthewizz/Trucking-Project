"""Build a self-contained, double-click browser preview without API credentials."""
from pathlib import Path
import base64,json
root=Path(__file__).resolve().parents[1]
s=(root/'index.html').read_text()
s=s.replace('<script src="local-settings.js"></script>', '')
s=s.replace('const KEY = (window.TRUCKING_CONFIG || {}).fmcsaKey || "";', 'let KEY = "";')
s=s.replace('const TOK = (window.TRUCKING_CONFIG || {}).socrataToken || "";', 'let TOK = "";')
s=s.replace('src="rr-transportation-logo.png"','src="data:image/png;base64,'+base64.b64encode((root/'rr-transportation-logo.png').read_bytes()).decode()+'"')
s=s.replace('fetch("counties.json").then(r => r.json())','Promise.resolve('+json.dumps(json.loads((root/'counties.json').read_text()))+')')
s=s.replace('fetch("stfips.json").then(r => r.json())','Promise.resolve('+json.dumps(json.loads((root/'stfips.json').read_text()))+')')
s=s.replace('<main id="app"></main>', '''<section style="padding:20px;background:#fff6dd;border-bottom:2px solid #b86b00" aria-label="Preview setup">
<div class="wrap"><h2 style="margin:0 0 8px">Local preview — no Netlify deployment</h2>
<p>First, unzip your original Netlify ZIP. Choose its <b>index.html</b> below to load your existing API settings. The file is read locally, not uploaded or executed. Settings stay in this tab's memory and are sent only with the app's normal API requests.</p>
<label for="preview-config"><b>Original index.html:</b></label> <input type="file" id="preview-config" accept=".html,text/html">
<p id="preview-status" role="status">Waiting for your original file. Then use the search box above.</p>
<p>You can click around this preview. Clipboard and pop-up features may depend on browser permissions when opening a local file.</p></div></section>
<main id="app"></main>''')
s=s.replace('Local API configuration is missing. Follow the README configuration step, then reload this page.','Choose the original index.html in the preview setup panel first.')
extra=r'''
<script>
document.getElementById('preview-config').addEventListener('change', async event => {
  const statusEl = document.getElementById('preview-status');
  const file = event.target.files[0];
  if (!file) return;
  if (file.size > 5 * 1024 * 1024){ statusEl.textContent = 'Please select the original index.html file (under 5 MB).'; return; }
  try {
    const text = await file.text();
    const key = text.match(/const KEY\s*=\s*"([^"\r\n]+)"\s*;/);
    const token = text.match(/const TOK\s*=\s*"([^"\r\n]+)"\s*;/);
    if (!key || !token || /window\.|TRUCKING_CONFIG/.test(key[1])){
      statusEl.textContent = 'Settings were not found. Choose index.html from your ORIGINAL Netlify ZIP, not this updated download.';
      return;
    }
    KEY = key[1]; TOK = token[1];
    statusEl.textContent = 'Ready! Search by DOT, MC number or company name above. Your settings are loaded for this tab only.';
  } catch {
    statusEl.textContent = 'Could not read that file. Please select the original index.html again.';
  }
});
</script>
'''
s=s.replace('</body>',extra+'\n</body>')
(root/'preview.html').write_text(s)
print('Built preview.html with embedded logo and geographic data; API credentials excluded.')
