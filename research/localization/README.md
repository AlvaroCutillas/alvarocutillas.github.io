# Portfolio language support

The eleven public HTML pages offer an English / Español dropdown in their top navigation. The English document remains the source; the Spanish text catalogue is embedded in each HTML for offline use.

## Structure

- ../../assets/i18n/language.js: shared language rendering, language selection in the URL, internal navigation, keyboard control and dynamic laboratory text.
- ../../assets/i18n/language.css: compact control, responsive navigation and print rules.
- ../../assets/i18n/pages/*.es.json: Spanish catalogues, shared laboratory fragments and reviewed headings.
- localize.py: embeds the shared assets and the matching catalogue in a page.
- apply.py: reapplies localization to all public pages.
- manual.es.json and review scripts: reviewed financial terminology, chapter headings, introductions and laboratory messages.
- verify.cjs: English default (including old saved Spanish preferences), dropdown switching, English heading restoration, equations and code, internal navigation, mobile widths, dynamic laboratory messages, keyboard and print checks.

The study builders and the empirical portfolio research builder call localize_page after generating their English HTML. Rebuilding a project therefore retains its language control. Existing element IDs, formula notation, code samples and chart coordinate data are preserved.

## Apply changes

After editing the shared styles, runtime or a Spanish catalogue, run from this directory:

~~~powershell
python apply.py
~~~

Catalogue keys are original English text units with whitespace normalized. Values are Spanish translations. Add matching catalogue entries when adding or editing prose. Numbers and calculations are not translated by the runtime.

Bare URLs always open in English, regardless of previous stored preferences. The native dropdown supports English and Español. A selection is retained for the current page and internal navigation through the lang query parameter, including direct file URLs. Explicit lang=en or lang=es selects a link's language.

## Verification

Install Playwright locally with "npm install --no-save playwright", then run:

~~~powershell
node verify.cjs
~~~

Set PLAYWRIGHT_MODULE to an existing installed module path if needed. The browser check uses Microsoft Edge's Windows executable path; adjust it for another operating system.

## Translation provenance

The initial Spanish catalogue was generated locally with OPUS-MT en-es and CTranslate2 4.6.0, followed by financial terminology corrections and reviewed titles and interface text. Runtime switching uses the shipped catalogues and does not call an online translation service.

Model sources: https://huggingface.co/Helsinki-NLP/opus-mt-en-es and the INT8 conversion https://huggingface.co/rohanksaxena/opus-mt-en-es. The downloaded model and its Python inference dependencies remain in the development workspace and are not website assets. Its provenance is recorded in translation-model-provenance.json.
