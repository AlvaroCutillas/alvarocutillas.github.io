"""
Pruebas de kelly_sim.py (ejecutar con: python -m pytest -q).

Cubren las tres comprobaciones exigidas para la página:
  (a) el máximo numérico de g(f) coincide con la fórmula de Kelly f*;
  (b) la media simulada del log-crecimiento por ronda converge a g(f);
  (c) casos límite: p = 0,5 con b = 1 -> f* = 0; f = 0 -> capital constante.
Además verifican que el generador vectorizado coincide con mulberry32 escalar
(el que usa la página) y que las cifras precalculadas incrustadas en el HTML
coinciden con lo que calcula este código.
"""

import json
import math
import re
from pathlib import Path

import numpy as np
import pytest

import kelly_sim as ks

HTML_PATH = Path(__file__).with_name("kelly-criterion.html")

CASES = [(0.55, 1.0), (0.60, 1.0), (0.40, 2.0), (0.30, 3.5), (0.58, 0.8), (0.75, 0.5)]


# ---------------------------------------------------------------------------
# Generador compartido
# ---------------------------------------------------------------------------
def mulberry32_scalar(seed: int, n: int) -> list[float]:
    """Transcripción literal (con enteros de Python) del mulberry32 de JavaScript."""
    def imul(x, y):
        return (x * y) & 0xFFFFFFFF
    a, out = seed & 0xFFFFFFFF, []
    for _ in range(n):
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = imul(a ^ (a >> 15), 1 | a)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        out.append(((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0)
    return out


@pytest.mark.parametrize("seed", [1, 42, 999])
def test_vectorized_generator_matches_scalar_mulberry32(seed):
    assert np.array_equal(ks.uniforms(seed, 2000), np.array(mulberry32_scalar(seed, 2000)))


def test_generator_offset_and_range():
    u = ks.uniforms(7, 10_000)
    assert np.array_equal(ks.uniforms(7, 100, start=500), u[500:600])
    assert u.min() >= 0.0 and u.max() < 1.0
    assert abs(u.mean() - 0.5) < 0.01


# ---------------------------------------------------------------------------
# (a) máximo numérico de g(f) frente a f*
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("p,b", CASES)
def test_numerical_maximum_matches_kelly(p, b):
    f_star = ks.kelly_fraction(p, b)
    assert f_star == pytest.approx((b * p - (1 - p)) / b)
    # Rejilla densa y refinamiento por sección áurea (g es estrictamente cóncava).
    grid = np.linspace(0.0, 0.999, 999_001)
    f_grid = grid[np.argmax(ks.growth_rate(grid, p, b))]
    assert abs(f_grid - f_star) <= 1.5e-6
    lo, hi, phi = 0.0, 0.999, (math.sqrt(5) - 1) / 2
    for _ in range(200):
        x1, x2 = hi - phi * (hi - lo), lo + phi * (hi - lo)
        if ks.growth_rate(x1, p, b) < ks.growth_rate(x2, p, b):
            lo = x1
        else:
            hi = x2
    assert 0.5 * (lo + hi) == pytest.approx(f_star, abs=1e-7)


@pytest.mark.parametrize("p,b", CASES)
def test_first_order_condition_at_kelly(p, b):
    f = ks.kelly_fraction(p, b)
    derivative = p * b / (1 + b * f) - (1 - p) / (1 - f)
    assert abs(derivative) < 1e-12


def test_growth_root_is_zero_and_near_twice_kelly_for_small_edges():
    for p, b in [(0.55, 1.0), (0.52, 1.0), (0.51, 2.0 / 1.9)]:
        f_star, root = ks.kelly_fraction(p, b), ks.growth_root(p, b)
        assert abs(ks.growth_rate(root, p, b)) < 1e-12
        assert root == pytest.approx(2 * f_star, rel=0.03)


# ---------------------------------------------------------------------------
# (b) convergencia del log-crecimiento simulado a g(f)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("p,b,f", [(0.55, 1.0, 0.10), (0.55, 1.0, 0.30),
                                   (0.40, 2.0, 0.05), (0.60, 1.0, 0.40)])
def test_simulated_log_growth_converges_to_g(p, b, f):
    errors, ses = [], []
    for n_paths in (200, 2000, 8000):
        r = ks.simulate(p, b, [f], n_rounds=250, n_paths=n_paths, seed=2024)[0]
        assert abs(r.mean_log_growth - r.g_theory) < 4 * r.se_log_growth
        errors.append(abs(r.mean_log_growth - r.g_theory))
        ses.append(r.se_log_growth)
    # El error estándar cae aproximadamente como 1/sqrt(n): x40 observaciones -> /6,3.
    assert ses[-1] == pytest.approx(ses[0] / math.sqrt(40), rel=0.05)
    assert errors[-1] < 4 * ses[-1]


def test_mean_log_growth_equals_mean_of_final_log_wealth():
    p, b, f, n, m = 0.55, 1.0, 0.12, 120, 600
    r = ks.simulate(p, b, [f], n, m, seed=3)[0]
    wins = ks.uniforms(3, n * m).reshape(m, n) < p
    log_wn = np.where(wins, math.log1p(b * f), math.log1p(-f)).sum(axis=1)
    assert r.mean_log_growth == pytest.approx(log_wn.mean() / n, abs=1e-13)


# ---------------------------------------------------------------------------
# (c) casos límite
# ---------------------------------------------------------------------------
def test_fair_even_money_bet_has_zero_kelly():
    assert ks.kelly_fraction(0.5, 1.0) == 0.0
    assert ks.growth_root(0.5, 1.0) is None
    assert np.all(ks.growth_rate(np.linspace(0.01, 0.9, 50), 0.5, 1.0) < 0)


@pytest.mark.parametrize("p,b", [(0.45, 1.0), (0.30, 2.0), (0.2, 3.9)])
def test_negative_edge_has_zero_kelly(p, b):
    assert b * p - (1 - p) <= 0
    assert ks.kelly_fraction(p, b) == 0.0


def test_zero_fraction_keeps_capital_constant():
    r = ks.simulate(0.55, 1.0, [0.0], n_rounds=200, n_paths=500, seed=11)[0]
    assert r.mean_log_growth == 0.0 and r.g_theory == 0.0
    assert all(v == 1.0 for v in r.percentiles.values())
    assert r.p_ruin == 0.0 and r.p_drawdown == 0.0


def test_same_seed_reproduces_and_strategies_share_outcomes():
    a = ks.simulate(0.55, 1.0, [0.1, 0.2], 100, 300, seed=5)
    b = ks.simulate(0.55, 1.0, [0.1, 0.2], 100, 300, seed=5)
    c = ks.simulate(0.55, 1.0, [0.1, 0.2], 100, 300, seed=6)
    assert a == b and a != c
    # Misma secuencia de aciertos: el SE relativo (SE / |lw - ll|) es idéntico.
    rel = [r.se_log_growth / abs(math.log1p(r.f) - math.log1p(-r.f)) for r in a]
    assert rel[0] == pytest.approx(rel[1], rel=1e-12)


# ---------------------------------------------------------------------------
# Coherencia con las cifras precalculadas de la página
# ---------------------------------------------------------------------------
def _embedded_reference() -> dict:
    html = HTML_PATH.read_text(encoding="utf-8")
    m = re.search(r'<script id="kelly-reference-data" type="application/json">(.*?)</script>',
                  html, re.S)
    assert m, "no se encuentra el bloque kelly-reference-data en el HTML"
    return json.loads(m.group(1))


@pytest.mark.skipif(not HTML_PATH.exists(), reason="la página no está junto al script")
def test_page_precomputed_numbers_match_this_code():
    page, fresh = _embedded_reference(), ks.run_all()
    for scenario in ("baseline", "misestimated"):
        for shown, computed in zip(page[scenario]["strategies"], fresh[scenario]["strategies"]):
            for key in ("f", "g_theory", "mean_log_growth", "p_ruin", "p_drawdown"):
                assert shown[key] == pytest.approx(computed[key], abs=1e-12), (scenario, key)
            for q in ("5", "50", "95"):
                assert shown["percentiles"][q] == pytest.approx(computed["percentiles"][q],
                                                                rel=1e-12)
