#!/usr/bin/env python3
"""Render a validated flashcard manifest to PNG using the local macOS Swift/AppKit rasterizer.

The wrapper also writes a small SVG source beside each PNG for inspection. It never installs
dependencies or contacts the network. Run validate_manifest.py first for clearer errors.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def safe_id(value: str) -> str:
    if not SAFE_ID.fullmatch(value):
        raise ValueError(f"unsafe card id: {value!r}")
    return value


def wrap(text: str, width: int) -> list[str]:
    text = str(text or "")
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for char in text:
        current += char
        if len(current) >= width:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_text(lines: list[str], x: int, y: int, size: int, color: str, weight: int = 400) -> str:
    out = []
    for index, line in enumerate(lines):
        out.append(
            f'<text x="{x}" y="{y + index * int(size * 1.55)}" '
            f'font-family="PingFang SC, Hiragino Sans GB, Arial, sans-serif" '
            f'font-size="{size}px" font-weight="{weight}" fill="{color}">{esc(line)}</text>'
        )
    return "\n".join(out)


def make_svg(card: dict, width: int, height: int, theme: dict) -> str:
    bg, ink, muted = theme["background"], theme["ink"], theme["muted"]
    accent, soft = theme["accent"], theme["accent_soft"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{bg}"/>',
        f'<rect x="72" y="72" width="180" height="42" rx="21" fill="{soft}"/>',
        svg_text(["快速填空" if card["type"] == "quick_check" else "知识讲解"], 94, 101, 20, accent, 700),
        svg_text(wrap(card["title"], 20)[:2], 72, 190, 48, ink, 700),
    ]
    y = 320
    if card["type"] == "quick_check":
        parts.append(svg_text(wrap(card.get("prompt", ""), 28)[:4], 72, y, 30, ink))
        y += 220
        blanks = card.get("blanks", [])
        for i, blank in enumerate(blanks[:5]):
            x = 72 + (i % 2) * 470
            yy = y + (i // 2) * 130
            parts.append(f'<rect x="{x}" y="{yy}" width="390" height="84" rx="14" fill="#FFFFFF" stroke="{accent}" stroke-width="3"/>')
            parts.append(svg_text([f"{i + 1}. {blank or '填写'}"], x + 24, yy + 53, 26, muted))
        y += ((min(len(blanks), 5) + 1) // 2) * 130 + 50
        parts.append(svg_text(["先独立回忆，再对照答案。"], 72, y, 24, muted))
    else:
        if card.get("definition"):
            parts.append(svg_text(["定义"], 72, y, 22, accent, 700))
            y += 42
            parts.append(svg_text(wrap(card["definition"], 30)[:4], 72, y, 28, ink))
            y += 190
        for point in (card.get("points") or [])[:4]:
            parts.append(f'<circle cx="88" cy="{y - 10}" r="10" fill="{accent}"/>')
            parts.append(svg_text(wrap(f"{point.get('label', '')}：{point.get('text', '')}", 31)[:2], 120, y, 26, ink))
            y += 100
        table = card.get("table")
        if table:
            parts.append(svg_text(["关系表"], 72, y, 22, accent, 700))
            y += 42
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            cols = max(1, len(headers))
            colw = 936 // cols
            for row_i, row in enumerate([headers] + rows[:5]):
                fill = soft if row_i == 0 else "#FFFFFF"
                parts.append(f'<rect x="72" y="{y}" width="{colw * cols}" height="62" fill="{fill}" stroke="#D9E0EA"/>')
                for col_i, cell in enumerate(row[:cols]):
                    parts.append(svg_text(wrap(cell, max(8, int(colw / 22)))[:1], 84 + col_i * colw, y + 39, 19, ink, 700 if row_i == 0 else 400))
                y += 62
        if card.get("takeaway"):
            y += 28
            parts.append(f'<rect x="72" y="{y}" width="936" height="100" rx="16" fill="{soft}"/>')
            parts.append(svg_text(wrap(card["takeaway"], 38)[:2], 98, y + 40, 24, ink, 700))
        chart = card.get("chart")
        if chart:
            y += 120
            parts.append(svg_text(["趋势图"], 72, y, 22, accent, 700))
            max_value = max(chart.get("values", [1])) or 1
            for i, (label, value) in enumerate(zip(chart.get("labels", [])[:4], chart.get("values", [])[:4])):
                yy = y + 28 + i * 48
                bar_width = int(520 * float(value) / max_value)
                parts.append(f'<rect x="180" y="{yy - 20}" width="{bar_width}" height="24" rx="12" fill="{accent}"/>')
                parts.append(svg_text([str(label)], 72, yy, 18, ink))
    parts.append(svg_text(["CRASH FLASHCARD · 秋招速记"], 72, height - 66, 18, muted, 700))
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    output_dir = args.output_dir.resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    dimensions = data.get("dimensions", {})
    width, height = int(dimensions.get("width", 1080)), int(dimensions.get("height", 1350))
    theme_path = Path(__file__).resolve().parents[1] / "assets" / "theme.json"
    theme = json.loads(theme_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    for card in data["cards"]:
        card_id = safe_id(card["id"])
        folder = output_dir / ("quick-check" if card["type"] == "quick_check" else "explanation")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{card_id}.svg").write_text(make_svg(card, width, height, theme), encoding="utf-8")

    swift = shutil.which("swift")
    if not swift:
        print("Swift is unavailable; SVG sources were written, but PNG rendering cannot run on this machine.", file=sys.stderr)
        return 2
    rasterizer = Path(__file__).with_name("render_cards.swift")
    result = subprocess.run([swift, str(rasterizer), str(manifest_path), str(output_dir)], text=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
