"""Embed executed chart data and accessible controls in the standalone page."""

from html import escape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"


def attach_data(path: Path, ax, payload: dict) -> None:
    source = path.read_text(encoding="utf-8")
    root = ET.fromstring(source)
    axes = root.find(f".//{{{SVG}}}g[@id='chart-axes']")
    background = axes.find(f"{{{SVG}}}g/{{{SVG}}}path")
    coordinates = [float(value) for value in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", background.attrib["d"])]
    x, y = coordinates[::2], coordinates[1::2]
    payload = dict(payload, box=[min(x), min(y), max(x), max(y)],
                   xlim=list(map(float, ax.get_xlim())), ylim=list(map(float, ax.get_ylim())))
    encoded = escape(json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")), quote=False)
    source = source.replace("</svg>", f'<metadata data-chart="true">{encoded}</metadata>\n</svg>')
    path.write_text(source, encoding="utf-8")


def read_data(source: str) -> dict | None:
    metadata = ET.fromstring(source).find(f"{{{SVG}}}metadata[@data-chart='true']")
    return json.loads(metadata.text) if metadata is not None else None


def legend_markup(data: dict, slug: str) -> str:
    items = []
    for item in data.get("legend", []):
        items.append(
            f'<button type="button" class="chart-legend-item" data-chart-point="{item["index"]}">'
            f'<span class="chart-key" style="color:{item["color"]}">{item["symbol"]}</span>'
            f'<span><span class="chart-legend-name">{escape(item["name"])}</span>'
            f'<span class="chart-legend-values">Volatility {item["volatility"]:.2f}% · CAGR {item["return"]:.2f}%</span></span></button>'
        )
    return f'<div class="chart-legend" aria-label="Highlight a portfolio">{"".join(items)}</div>' if items else ""


def record(x: float, y: float, title: str, rows: list, **extra) -> dict:
    return {"x": float(x), "y": float(y), "title": title, "rows": rows, **extra}


def percent(value: float, digits: int = 2) -> str:
    return f"{100 * value:.{digits}f}%"


def allocation_rows(row, tickers) -> list:
    return [[ticker, percent(float(row[ticker]))] for ticker in tickers if float(row[ticker]) > .0001]
