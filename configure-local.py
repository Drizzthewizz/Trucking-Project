"""Recover the user's existing API settings from their original Netlify ZIP locally."""
import json, pathlib, re, sys, zipfile
if len(sys.argv) != 2:
    raise SystemExit('Usage: python configure-local.py /path/to/netlify-site_1.zip')
root = pathlib.Path(__file__).resolve().parent
with zipfile.ZipFile(sys.argv[1]) as z:
    html = z.read('index.html').decode()
key = re.search(r'const KEY = "([^"\n]+)";', html)
token = re.search(r'const TOK = "([^"\n]+)";', html)
if not key or not token:
    raise SystemExit('Expected API settings were not found in the original ZIP.')
out = root / 'local-settings.js'
if out.exists():
    raise SystemExit('local-settings.js already exists; preserve or remove it before configuring again.')
with out.open('x') as f:
    f.write('window.TRUCKING_CONFIG = ' + json.dumps({'fmcsaKey': key.group(1), 'socrataToken': token.group(1)}) + ';\n')
out.chmod(0o600)
print('Local configuration created. Do not commit or share local-settings.js.')
