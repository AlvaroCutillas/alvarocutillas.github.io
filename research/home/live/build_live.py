"""Genera index.html: portada interactiva del portfolio («live research terminal»).

Fuentes:
  research/home/live/template.html  -> estructura y textos (inglés; el español sale del catálogo)
  research/home/live/live.css       -> estilos
  research/home/live/live.js        -> motores de gráficos, laboratorios y transiciones
  research/home/live/es.json        -> traducciones al español de los textos nuevos
  research/portfolio-optimization/results/*.csv -> datos reales del estudio de carteras

Uso (desde la raíz del repositorio):
  python research/home/live/build_live.py

Contratos que se conservan:
  * <a class="project-card" href="projects/portfolio-optimization.html"> sin enlaces anidados y con el
    bloque <!-- portfolio-optimization-results --> (lo reescriben analysis/page.py y lo comprueba audit.py).
  * #quant-basics contiene los ocho <a class="project-card"> (research/localization/verify.cjs).
  * El selector de idioma y el catálogo se incrustan con research/localization/localize.py.
"""
import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[2]
RES = SITE / 'research' / 'portfolio-optimization' / 'results'
CATALOG = SITE / 'assets' / 'i18n' / 'pages' / 'index.es.json'
TICKERS = ['SPY', 'IWM', 'EFA', 'EEM', 'AGG', 'TLT', 'LQD', 'VNQ', 'GLD', 'DBC']


def rows(name):
    with open(RES / name, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def r4(x):
    return round(float(x), 4)


# ---------- 1. Datos reales del estudio de carteras ----------
frontier = [[r4(r['volatility']), r4(r['return'])] for r in rows('efficient_frontier.csv')]

assets = [dict(t=r['ticker'], role=r['role'], mu=r4(r['annual_arithmetic_mean']),
               vol=r4(r['annual_volatility']), sr=round(float(r['sharpe_excess_bil']), 2),
               dd=r4(r['max_drawdown'])) for r in rows('descriptive_stats.csv')]

corr_rows = rows('training_correlations.csv')
corr = [[round(float(r[t]), 3) for t in TICKERS] for r in corr_rows]
assert [r[''] for r in corr_rows] == TICKERS

# Riqueza acumulada neta (walk-forward) a partir de los rendimientos diarios netos
daily = rows('walk_forward_daily_net.csv')
strategies = [k for k in daily[0].keys() if k != 'date']
wealth = {s: 1.0 for s in strategies}
peak = {s: 1.0 for s in strategies}
dates, series, dds = [], {s: [] for s in strategies}, {s: [] for s in strategies}
for i, r in enumerate(daily):
    for s in strategies:
        wealth[s] *= 1 + float(r[s])
        peak[s] = max(peak[s], wealth[s])
    # Una muestra cada 3 sesiones (y siempre la última) mantiene la forma sin inflar la página
    if i % 3 == 0 or i == len(daily) - 1:
        dates.append(r['date'])
        for s in strategies:
            series[s].append(round(wealth[s], 4))
            dds[s].append(round(wealth[s] / peak[s] - 1, 4))

metrics = {r['strategy']: dict(ret=r4(r['annual_return']), vol=r4(r['annual_volatility']),
                               sr=round(float(r['sharpe_excess_bil']), 2), dd=r4(r['max_drawdown']),
                               tw=round(float(r['terminal_wealth']), 2), to=round(float(r['annual_turnover']), 2),
                               ne=round(float(r['mean_effective_positions']), 2))
           for r in rows('walk_forward_metrics.csv')}
# Comprobación de coherencia: la riqueza terminal reconstruida coincide con la publicada
for s in strategies:
    assert abs(wealth[s] - metrics[s]['tw']) < 0.01, (s, wealth[s], metrics[s]['tw'])

HEADLINE = 'Max Sharpe · sample capped'
weights = [[r['date']] + [round(max(0.0, float(r[t])), 4) for t in TICKERS]
           for r in rows('walk_forward_weights.csv') if r['strategy'] == HEADLINE]

data = dict(tickers=TICKERS, frontier=frontier, assets=assets, corr=corr,
            wealth=dict(dates=dates, series=series, dd=dds, order=strategies, headline=HEADLINE),
            metrics=metrics, weights=weights, days=len(daily))

# ---------- 2. Ensamblado ----------
template = (HERE / 'template.html').read_text(encoding='utf-8')
css = (HERE / 'live.css').read_text(encoding='utf-8')
js = (HERE / 'live.js').read_text(encoding='utf-8')
payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
page = (template.replace('/*__CSS__*/', css)
                .replace('/*__JS__*/', js)
                .replace('/*__DATA__*/', payload))
assert '/*__' not in page
assert page.index('href="projects/portfolio-optimization.html"') == page.index('<a class="project-card" href="projects/portfolio-optimization.html">') + len('<a class="project-card" ')
(SITE / 'index.html').write_text(page, encoding='utf-8')

# ---------- 3. Catálogo EN/ES: se añaden los textos nuevos sin tocar los ya revisados ----------
catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
extra = json.loads((HERE / 'es.json').read_text(encoding='utf-8'))
for k, v in extra.items():
    catalog['es'].setdefault(k, v)  # no se pisan las traducciones ya revisadas
CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

sys.path.insert(0, str(SITE / 'research' / 'localization'))
from localize import localize_page  # noqa: E402

localize_page(SITE / 'index.html')
size = (SITE / 'index.html').stat().st_size
print(f'index.html generado: {size / 1024:.0f} KB · {len(daily):,} sesiones OOS · '
      f'{len(frontier)} puntos de frontera · {len(weights)} rebalanceos')
