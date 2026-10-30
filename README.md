# R&R Transportation Carrier Lookup

Updated website from the supplied Netlify ZIP. Uploading this repository does not deploy the website.

## Download

On this repository's GitHub page, select **Code → Download ZIP**, then extract it.

## Click-only preview (no terminal)

1. Use **Code → Download ZIP** on GitHub and extract the downloaded ZIP.
2. Double-click **preview.html** in the extracted folder. It opens in your browser.
3. Extract your ORIGINAL `netlify-site_1.zip` into a different folder.
4. In the preview's yellow setup panel, click **Choose File** and select **index.html from that original folder**.
5. Wait for **Ready!**, then use the search box. Internet access is required for live records.

The original HTML is read locally for its existing API settings, never executed or uploaded. Settings remain only in the preview tab's memory. If you close or reload the tab, choose the original file again. This is a local preview; it does not deploy to Netlify. Chrome or Edge is recommended. Clipboard/pop-up permissions can differ for local files.

The terminal instructions below are optional, for development or preparing a deployment.

## Configure locally first

API credentials are intentionally excluded from GitHub. Keep your original `netlify-site_1.zip` (the ZIP you uploaded in chat). In a terminal in this extracted repository folder, run:

```sh
python configure-local.py "/path/to/netlify-site_1.zip"
```

Replace the path with the original ZIP's location. On Windows you can use `py` instead of `python`. This copies the existing settings into a local, Git-ignored `local-settings.js` without printing them. The original ZIP is not uploaded anywhere. Do not commit that file. The site needs this configuration to run lookups.

## Preview without a Netlify deployment

Open a terminal in the extracted folder (the folder containing `index.html`) and run:

```sh
python -m http.server 8000
```

On Windows, `py -m http.server 8000` may be available instead. Open `http://localhost:8000` in your browser. Stop the server with Ctrl+C. Python and Internet access to the public data services are required.

## What changed

- Accepts pasted identifiers such as `USDOT# 294345`, `DOT: 294345`, and `MC-767467`.
- Distinguishes FMCSA lookup outages from successful empty results.
- Corrects carrier-dashboard liability/cargo filing classification and avoids inventing cancellation dates.
- Validates dates, uses calendar boundaries for the 24-month crash list, and matches crashes by report number plus state.
- Labels filing transitions accurately and warns when selected datasets reach retrieval limits.
- Updates related skill guidance. Hot leads remains included.

## Checks

Run `node tests/calculations.cjs` for 41 regression assertions and a JavaScript syntax check (Node.js required).

Before upload, browser tests exercised the modified page with live public records for USDOT 294345 and MC767467, name search, CSV export, and mobile layout. Six synthetic model checks covered filing selection, amount conversion, crash matching and filtering. Outage messages were tested with browser-only simulated failures. One carrier's OOS arithmetic and crash-window count were independently checked.

This is a first repair pass. Premium estimates, peer rankings, DataQs conclusions, inferred renewal dates, other market/service calculations, full large-fleet completeness, and concurrent-search behavior still need further validation. Public filing data does not confirm the complete current insurance program.

## Deploy later

Keep the previous deployment for rollback. Use the manual upload control in your existing Netlify site's Deploys area to upload the configured folder containing `index.html` and `local-settings.js`. The original app uses browser-visible API credentials; local configuration prevents accidental GitHub commits but does not hide them in a deployed browser app. Review provider restrictions before deployment. Deploy only when ready; local preview does not require a Netlify deployment.

The site serves `skill.md`. If you separately installed the skill in Claude, update that copy separately as well.
