#!/usr/bin/env python3
"""Cross-platform Pillow renderer for crash-card.

This adapter is used on Windows and Linux. Pillow is intentionally optional so macOS users
can use the Swift/AppKit adapter without installing a Python image package.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print(
        "Pillow is required for PNG rendering on Windows/Linux. Install it explicitly with "
        "`python -m pip install 'Pillow>=10'`; no package is installed automatically.",
        file=sys.stderr,
    )
    raise SystemExit(2)


COLORS = {
    "background": "#F7F8FA",
    "ink": "#17202A",
    "muted": "#5C6773",
    "accent": "#246BFD",
    "accent_soft": "#E8F0FF",
    "border": "#D9E0EA",
}


def font_candidates() -> list[Path]:
    system = platform.system()
    candidates = []
    if system == "Windows":
        candidates.extend(
            Path(value)
            for value in (
                os.environ.get("WINDIR", r"C:\Windows") + r"\Fonts\msyh.ttc",
                os.environ.get("WINDIR", r"C:\Windows") + r"\Fonts\simhei.ttf",
                os.environ.get("WINDIR", r"C:\Windows") + r"\Fonts\segoeui.ttf",
            )
        )
    candidates.extend(
        Path(value)
        for value in (
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/googlefonts-noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        )
    )
    return candidates


def load_font(size: int, path: str | None, bold: bool = False):
    configured = path or os.environ.get("CRASH_CARD_FONT") or os.environ.get("CRASH_FLASHCARD_FONT")
    choices = [Path(configured)] if configured else font_candidates()
    for candidate in choices:
        if candidate.is_file():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                continue
    hint = "--font /path/to/a-cjk-font.ttf"
    raise RuntimeError(
        "No usable CJK font was found. Provide "
        f"{hint}, or install a system CJK font such as Noto Sans CJK or Microsoft YaHei."
    )


def wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in str(text or "").splitlines() or [""]:
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and draw.textlength(candidate, font=font) > width:
                lines.append(current)
                current = char
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines or [""]


def draw_wrapped(draw, text: str, xy: tuple[int, int], width: int, font, fill: str, max_lines: int | None = None, spacing: int = 10) -> int:
    lines = wrap(draw, text, font, width)
    if max_lines:
        lines = lines[:max_lines]
    x, y = xy
    bbox = draw.textbbox((0, 0), "国Ag", font=font)
    line_height = bbox[3] - bbox[1] + spacing
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def rounded(draw, box, fill: str, outline: str | None = None, width: int = 1, radius: int = 16):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def render_card(card: dict, width: int, height: int, font_path: str | None) -> Image.Image:
    image = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(image)
    margin = 72
    f_label = load_font(20, font_path, True)
    f_title = load_font(48, font_path, True)
    f_body = load_font(28, font_path)
    f_small = load_font(22, font_path)
    f_point = load_font(26, font_path)
    f_footer = load_font(18, font_path, True)
    label = "快速填空" if card["type"] == "quick_check" else "知识讲解"
    rounded(draw, (margin, margin, margin + 180, margin + 42), COLORS["accent_soft"], radius=21)
    draw.text((margin + 20, margin + 9), label, font=f_label, fill=COLORS["accent"])
    y = 166
    y = draw_wrapped(draw, card["title"], (margin, y), width - margin * 2, f_title, COLORS["ink"], max_lines=2, spacing=12) + 56

    if card["type"] == "quick_check":
        y = draw_wrapped(draw, card.get("prompt", ""), (margin, y), width - margin * 2, f_body, COLORS["ink"], max_lines=4, spacing=10) + 48
        for index, blank in enumerate(card.get("blanks", [])[:6]):
            x = margin + (index % 2) * 470
            yy = y + (index // 2) * 132
            rounded(draw, (x, yy, x + 390, yy + 84), "#FFFFFF", COLORS["accent"], width=3, radius=14)
            draw.text((x + 24, yy + 25), f"{index + 1}. {blank or '填写'}", font=f_body, fill=COLORS["muted"])
        y += ((min(len(card.get("blanks", [])), 6) + 1) // 2) * 132 + 30
        draw.text((margin, y), "先独立回忆，再对照答案。", font=f_small, fill=COLORS["muted"])
    else:
        if card.get("definition"):
            draw.text((margin, y), "定义", font=f_small, fill=COLORS["accent"])
            y = draw_wrapped(draw, card["definition"], (margin, y + 42), width - margin * 2, f_body, COLORS["ink"], max_lines=4) + 56
        for point in card.get("points", [])[:5]:
            draw.ellipse((margin + 6, y + 5, margin + 26, y + 25), fill=COLORS["accent"])
            y = draw_wrapped(draw, f"{point['label']}：{point['text']}", (margin + 48, y), width - margin * 2 - 48, f_point, COLORS["ink"], max_lines=2) + 26
        table = card.get("table")
        if table:
            draw.text((margin, y), "关系表", font=f_small, fill=COLORS["accent"])
            y += 42
            headers, rows = table["headers"], table["rows"][:5]
            columns = max(1, len(headers))
            col_width = (width - margin * 2) // columns
            for row_index, row in enumerate([headers] + rows):
                fill = COLORS["accent_soft"] if row_index == 0 else "#FFFFFF"
                draw.rectangle((margin, y, width - margin, y + 62), fill=fill, outline=COLORS["border"])
                for col_index, cell in enumerate(row):
                    draw_wrapped(draw, cell, (margin + col_index * col_width + 10, y + 16), col_width - 20, f_small, COLORS["ink"], max_lines=1, spacing=0)
                y += 62
        chart = card.get("chart")
        if chart:
            draw.text((margin, y + 18), "趋势图", font=f_small, fill=COLORS["accent"])
            y += 66
            max_value = max(chart["values"] or [1]) or 1
            for index, label in enumerate(chart["labels"][:4]):
                value = chart["values"][index]
                yy = y + index * 48
                draw.text((margin, yy), label, font=load_font(18, font_path), fill=COLORS["ink"])
                rounded(draw, (margin + 108, yy + 4, margin + 108 + int(520 * value / max_value), yy + 28), COLORS["accent"], radius=12)
            y += min(4, len(chart["labels"])) * 48
        if card.get("takeaway"):
            y += 24
            box = (margin, min(height - 180, y), width - margin, min(height - 80, y + 100))
            rounded(draw, box, COLORS["accent_soft"], radius=16)
            draw_wrapped(draw, card["takeaway"], (box[0] + 26, box[1] + 20), box[2] - box[0] - 52, f_small, COLORS["ink"], max_lines=2)

    draw.text((margin, height - 66), "CRASH FLASHCARD · 秋招速记", font=f_footer, fill=COLORS["muted"])
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--font", help="path to a CJK-capable TTF/TTC font")
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    width, height = data["dimensions"]["width"], data["dimensions"]["height"]
    try:
        for card in data["cards"]:
            folder = args.output_dir / ("quick-check" if card["type"] == "quick_check" else "explanation")
            folder.mkdir(parents=True, exist_ok=True)
            image = render_card(card, width, height, args.font)
            image.save(folder / f"{card['id']}.png", format="PNG", optimize=True)
    except RuntimeError as exc:
        print(f"Pillow rendering failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
