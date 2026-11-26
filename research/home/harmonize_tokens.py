"""Alinea los tokens de color de las paginas de proyecto (y sus base.css fuente) con la nueva home."""
import re, sys
from pathlib import Path
SITE = Path(__file__).resolve().parents[2]
MAP = {'--bg:#0b0e0c': '--bg:#0b0e0c', '--panel:#0d0d0d': '--panel:#111512', '--panel2:#111111': '--panel2:#161b17',
       '--line:#262626': '--line:#242b26', '--line-2:#303030': '--line-2:#323a34', '--text:#f5f5f2': '--text:#e9ece5',
       '--muted:#9a9a94': '--muted:#99a199'}
files = [*SITE.glob('projects/*.html'), *SITE.glob('research/*/base.css'), SITE / 'projects/project-status.css']
for f in files:
    s = f.read_text(encoding='utf-8'); o = s
    for a, b in MAP.items(): s = re.sub(re.escape(a) + r'(?![0-9a-fA-F])', b, s)
    s = re.sub(r'(?<![\w-])background:\s*#050505', 'background:#0b0e0c', s) if f.suffix == '.css' else s
    if s != o: f.write_text(s, encoding='utf-8', newline=''); print('actualizado', f.relative_to(SITE))
