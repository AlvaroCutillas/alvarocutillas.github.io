from pathlib import Path
from localize import localize_page
SITE=Path(__file__).resolve().parents[2]
for path in [SITE/'index.html',*sorted((SITE/'projects').glob('*.html'))]:
    localize_page(path)
    print(path.name)
