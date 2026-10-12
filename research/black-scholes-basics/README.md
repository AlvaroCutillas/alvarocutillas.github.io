# Black–Scholes Option Pricing

Quant Basics 01. The published standalone study is [../../projects/black-scholes-basics.html](../../projects/black-scholes-basics.html). Open that HTML directly, or use the Quant Basics section in [../../index.html](../../index.html#quant-basics).

## Files

- content*.html: English textbook notes, source equations and figure placeholders.
- build.py and mathml.py: publication assembly and native MathML rendering.
- Stylesheets: the portfolio's accepted visual design.
- notebook.html, notebook.js and chart inspection files: offline interactive laboratories.
- computed.json and figures.json: reproducible computed values and embedded SVG figures.
- figures.py and numerical modules: calculations and figure generation.
- figures/: separate SVG exports of the published computed figures.
- previews/: saved visual checks of the finished page.
- Verification scripts, reference cases and JSON reports: the numerical and browser checks used during development.

Browser caches and previous styling experiments are excluded from this publication folder. The study's data conventions, assumptions and source references are documented in its HTML.

## Regenerate the HTML

From this directory in PowerShell:

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python build.py
~~~

The builder writes directly to ../../projects/black-scholes-basics.html, using the included computed data and figures. The published HTML embeds CSS, JavaScript, SVG and MathML and needs no network requests to display its notes.

To recompute the examples and figures before rebuilding, use the included numerical module where applicable:

~~~powershell
python figures.py
python build.py
~~~

## Browser checks

The browser scripts use Playwright and the installed Microsoft Edge browser. Install Playwright locally with "npm install --no-save playwright", then run:

~~~powershell
node verify.cjs
node verify_coordinates.cjs
~~~

Set PLAYWRIGHT_MODULE to another installed Playwright module path if needed. Browser scripts retain the local Windows Edge executable path; adjust it for a different operating system. Verification creates local reports and screenshots.
