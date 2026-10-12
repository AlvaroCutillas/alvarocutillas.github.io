"""Embed the shared language switch and offline catalogue in a generated page."""
from pathlib import Path
import json,re
SITE=Path(__file__).resolve().parents[2]
ASSETS=SITE/'assets'/'i18n'
CONTROL='<div class="language-switch"><select id="page-language" aria-label="Page language"><option value="en" lang="en" selected>English</option><option value="es" lang="es">Español</option></select></div>'
def localize_page(path):
    path=Path(path)
    catalog=ASSETS/'pages'/f'{path.stem}.es.json'
    if not catalog.exists():raise FileNotFoundError(f'Create the reviewed offline language catalogue first: {catalog}')
    page=path.read_text(encoding='utf-8')
    page=re.sub(r'<!-- portfolio-language-css -->.*?<!-- /portfolio-language-css -->','',page,flags=re.S)
    page=re.sub(r'<!-- portfolio-language-control -->.*?<!-- /portfolio-language-control -->','',page,flags=re.S)
    page=re.sub(r'<!-- portfolio-language-runtime -->.*?<!-- /portfolio-language-runtime -->','',page,flags=re.S)
    css=(ASSETS/'language.css').read_text(encoding='utf-8')
    js=(ASSETS/'language.js').read_text(encoding='utf-8')
    payload=json.dumps(json.loads(catalog.read_text(encoding='utf-8')),ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    page=page.replace('</head>','<!-- portfolio-language-css --><style>'+css+'</style><!-- /portfolio-language-css --></head>',1)
    nav=re.search(r'<nav\b.*?</nav>',page,flags=re.S)
    assert nav is not None and 'nav-inner' in nav[0]
    inner=re.search(r'<div\b[^>]*class=["\'][^"\']*\bnav-inner\b[^"\']*["\'][^>]*>',nav[0])
    assert inner is not None
    depth=0;marker=None
    for token in re.finditer(r'<div\b[^>]*>|</div>',nav[0][inner.start():]):
        depth+=-1 if token[0]=='</div>' else 1
        if depth==0:marker=inner.start()+token.start();break
    assert marker is not None
    updated=nav[0][:marker]+'<!-- portfolio-language-control -->'+CONTROL+'<!-- /portfolio-language-control -->'+nav[0][marker:]
    page=page[:nav.start()]+updated+page[nav.end():]
    runtime='<!-- portfolio-language-runtime --><script id="portfolio-language-data" type="application/json">'+payload+'</script><script>'+js+'</script><!-- /portfolio-language-runtime -->'
    page=page.replace('</body>',runtime+'</body>',1)
    path.write_text(page,encoding='utf-8')
    return path
