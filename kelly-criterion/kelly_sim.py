"""
Implementación de referencia (NumPy) del simulador del criterio de Kelly.

Modelo: apuesta binaria repetida. Con probabilidad p se gana b por unidad
apostada (cuota neta b); con probabilidad q = 1 - p se pierde lo apostado.
El apostador arriesga en cada ronda una fracción constante f de su capital.

Este script reproduce los resultados numéricos de ``kelly-criterion.html``
con la misma semilla: utiliza el mismo generador pseudoaleatorio que la
página (mulberry32 evaluado como generador de contador), por lo que la
secuencia de ganancias y pérdidas es idéntica en Python y en el navegador.

Uso:
    python kelly_sim.py                      # imprime las tablas
    python kelly_sim.py --json results.json  # además guarda los resultados

Contenido formativo: no constituye asesoramiento de inversión.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict

import numpy as np

# Umbrales de las métricas de riesgo (capital inicial normalizado a 1).
RUIN_LEVEL = 0.10       # "ruina": el capital cae por debajo del 10 % del inicial
DRAWDOWN_LEVEL = 0.50   # caída desde máximos superior al 50 %
PERCENTILES = (5, 25, 50, 75, 95)

_MULBERRY_INCREMENT = 0x6D2B79F5
_MASK32 = 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Fórmulas analíticas
# ---------------------------------------------------------------------------
def kelly_fraction(p: float, b: float) -> float:
    """Fracción de Kelly f* = (b·p - q) / b, acotada en 0 si la ventaja es <= 0."""
    q = 1.0 - p
    edge = b * p - q
    return edge / b if edge > 0 else 0.0


def growth_rate(f, p: float, b: float):
    """Crecimiento logarítmico esperado por ronda: g(f) = p·ln(1+b·f) + q·ln(1-f)."""
    f = np.asarray(f, dtype=float)
    with np.errstate(divide="ignore"):
        return p * np.log1p(b * f) + (1.0 - p) * np.log1p(-f)


def growth_root(p: float, b: float, tol: float = 1e-14) -> float | None:
    """Raíz positiva de g(f) = 0 en (f*, 1), por bisección. None si f* = 0."""
    f_star = kelly_fraction(p, b)
    if f_star <= 0 or p >= 1:
        return None
    lo, hi = f_star, 1.0 - 1e-15   # g(lo) > 0 y g(hi) < 0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if growth_rate(mid, p, b) > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Generador pseudoaleatorio compartido con la página
# ---------------------------------------------------------------------------
def uniforms(seed: int, n: int, start: int = 0) -> np.ndarray:
    """
    Devuelve las salidas start..start+n-1 de mulberry32(seed) en [0, 1).

    mulberry32 avanza su estado sumando una constante, de modo que la salida
    k-ésima depende solo de seed + (k+1)·0x6D2B79F5 (mod 2^32). Eso permite
    vectorizarlo; la página usa exactamente la misma función con índice
    k = trayectoria·N + ronda.
    """
    k = np.arange(start, start + n, dtype=np.uint64)
    a = ((np.uint64(seed) + (k + np.uint64(1)) * np.uint64(_MULBERRY_INCREMENT))
         & np.uint64(_MASK32)).astype(np.uint32)
    # Aritmética uint32 con desbordamiento modular, equivalente a Math.imul en JS.
    t = (a ^ (a >> np.uint32(15))) * (a | np.uint32(1))
    t = (t + (t ^ (t >> np.uint32(7))) * (t | np.uint32(61))) ^ t
    return (t ^ (t >> np.uint32(14))).astype(np.float64) / 4294967296.0


# ---------------------------------------------------------------------------
# Simulación Monte Carlo
# ---------------------------------------------------------------------------
@dataclass
class StrategyResult:
    f: float
    g_theory: float            # g(f) analítico con la p real
    mean_log_growth: float     # media simulada de ln(W_N)/N
    se_log_growth: float       # error estándar de esa media
    p_ruin: float              # P(min_t W_t < 0,10)
    p_drawdown: float          # P(máxima caída desde máximos > 50 %)
    percentiles: dict          # percentiles de W_N (capital final, W_0 = 1)


def simulate(p: float, b: float, fractions, n_rounds: int, n_paths: int,
             seed: int) -> list[StrategyResult]:
    """
    Simula n_paths trayectorias de n_rounds apuestas para cada fracción.

    Todas las fracciones comparten la misma secuencia de resultados, lo que
    permite comparar estrategias sin ruido adicional entre ellas.
    El capital se acumula en logaritmos (suma secuencial, igual que en la
    página) para evitar desbordamientos con fracciones extremas.
    """
    u = uniforms(seed, n_paths * n_rounds).reshape(n_paths, n_rounds)
    wins = u < p                     # misma regla que en el navegador
    n_obs = n_paths * n_rounds
    n_wins = int(wins.sum())
    p_hat = n_wins / n_obs
    results = []
    for f in fractions:
        lw, ll = math.log1p(b * f), math.log1p(-f)
        log_w = np.cumsum(np.where(wins, lw, ll), axis=1)
        # Ruina: el capital cae alguna vez por debajo del 10 % del inicial.
        p_ruin = float((log_w.min(axis=1) < math.log(RUIN_LEVEL)).mean())
        # Drawdown: el máximo previo incluye el capital inicial (log 1 = 0).
        peak = np.maximum.accumulate(np.maximum(log_w, 0.0), axis=1)
        p_dd = float(((log_w - peak) < math.log(1 - DRAWDOWN_LEVEL)).any(axis=1).mean())
        # Media del log-crecimiento por ronda a partir del número de aciertos.
        mean_lg = (n_wins * lw + (n_obs - n_wins) * ll) / n_obs
        se_lg = abs(lw - ll) * math.sqrt(p_hat * (1 - p_hat) / n_obs)
        # Percentiles calculados sobre log-capital (interpolación lineal) y exponenciados.
        pct = np.exp(np.percentile(log_w[:, -1], PERCENTILES))
        results.append(StrategyResult(
            f=float(f), g_theory=float(growth_rate(f, p, b)),
            mean_log_growth=float(mean_lg), se_log_growth=float(se_lg),
            p_ruin=p_ruin, p_drawdown=p_dd,
            percentiles={str(q): float(v) for q, v in zip(PERCENTILES, pct)},
        ))
    return results


# ---------------------------------------------------------------------------
# Escenarios publicados en la página
# ---------------------------------------------------------------------------
BASELINE = dict(p=0.55, b=1.0, n_rounds=200, n_paths=5000, seed=42)
BASELINE_FRACTIONS = (0.05, 0.10, 0.15, 0.20, 0.30)

MISESTIMATED = dict(p_true=0.53, p_believed=0.60, b=1.0, n_rounds=200,
                    n_paths=5000, seed=42)


def run_all() -> dict:
    """Calcula todos los resultados que la página muestra como precalculados."""
    p, b = BASELINE["p"], BASELINE["b"]
    base = simulate(p, b, BASELINE_FRACTIONS, BASELINE["n_rounds"],
                    BASELINE["n_paths"], BASELINE["seed"])

    m = MISESTIMATED
    f_true = kelly_fraction(m["p_true"], m["b"])
    f_full = kelly_fraction(m["p_believed"], m["b"])
    mis = simulate(m["p_true"], m["b"], (f_true, f_full, 0.5 * f_full),
                   m["n_rounds"], m["n_paths"], m["seed"])

    return {
        "baseline": {**BASELINE, "kelly": kelly_fraction(p, b),
                     "growth_root": growth_root(p, b),
                     "strategies": [asdict(r) for r in base]},
        "misestimated": {**m, "labels": ["true_kelly", "full_kelly_believed",
                                         "half_kelly_believed"],
                         "strategies": [asdict(r) for r in mis]},
        "environment": {"numpy": np.__version__},
    }


def _print_table(title: str, rows: list[dict]) -> None:
    print(f"\n{title}")
    print(f"{'f':>7} {'g(f)':>10} {'mean lg':>10} {'±1.96SE':>9} "
          f"{'median W':>11} {'P(W<0.1)':>9} {'P(DD>50%)':>10}")
    for r in rows:
        print(f"{r['f']:7.4f} {r['g_theory']:10.6f} {r['mean_log_growth']:10.6f} "
              f"{1.96 * r['se_log_growth']:9.6f} {r['percentiles']['50']:11.4f} "
              f"{r['p_ruin']:9.4f} {r['p_drawdown']:10.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--json", help="ruta opcional para guardar los resultados")
    args = parser.parse_args()

    res = run_all()
    b = res["baseline"]
    print(f"Baseline p={b['p']}, b={b['b']}, N={b['n_rounds']}, "
          f"M={b['n_paths']}, seed={b['seed']}")
    print(f"f* = {b['kelly']:.6f}   raíz g(f)=0: {b['growth_root']:.6f}")
    _print_table("Fracción constante (misma secuencia de resultados):", b["strategies"])
    m = res["misestimated"]
    _print_table(f"Ventaja mal estimada: p real={m['p_true']}, p creída={m['p_believed']} "
                 "(Kelly real, Kelly completo creído, medio Kelly creído):",
                 m["strategies"])
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2)
        print(f"\nResultados guardados en {args.json}")


if __name__ == "__main__":
    main()
