"""Measured card scenes, using local Pillow text and Mathtext formula sprites.

One scene is measured and drawn without reflow, truncation, or network access.
"""
from __future__ import annotations

import io
import math
import os
import re
import tempfile
import warnings
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "crash-card-mpl"))
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
import matplotlib
matplotlib.use("Agg")
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image


class LayoutError(ValueError):
    pass


class Fonts:
    def __init__(self, regular=None, bold=None):
        if bold and not Path(bold).is_file():
            raise LayoutError(f"bold font not found: {bold}")
        candidates = [regular] if regular else [
            os.environ.get("CRASH_CARD_FONT"),
            os.environ.get("CRASH_FLASHCARD_FONT"),
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/msyh.ttc",
        ]
        self.regular = next((str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()), None)
        if not self.regular:
            raise LayoutError("CJK font unavailable; supply --font-path with a local Chinese font")
        bold_candidates = [bold] if bold else [
            os.environ.get("CRASH_CARD_BOLD_FONT"),
            os.environ.get("CRASH_FLASHCARD_BOLD_FONT"),
            self.regular.replace("Light", "Medium").replace("Regular", "Bold"),
        ]
        self.bold = next((str(Path(p).resolve()) for p in bold_candidates if p and Path(p).is_file()), self.regular)
        font_dir = Path(matplotlib.get_data_path()) / "fonts/ttf"
        self.fallback = str(font_dir / "DejaVuSans.ttf")
        self.fallback_bold = str(font_dir / "DejaVuSans-Bold.ttf")
        self.maps = {}
        for path in {self.regular, self.bold, self.fallback, self.fallback_bold}:
            with TTFont(path, fontNumber=0, lazy=True) as font:
                self.maps[path] = set((font.getBestCmap() or {}).keys())
        self.runs("中文概念解释与条件", 48)

    @lru_cache(maxsize=128)
    def font(self, path, size):
        return ImageFont.truetype(path, size=int(size), index=0)

    @lru_cache(maxsize=4096)
    def runs(self, text, size, bold=False):
        primary = self.bold if bold else self.regular
        fallback = self.fallback_bold if bold else self.fallback
        runs = []
        for ch in text:
            if ch == "\t":
                raise LayoutError("tabs are not supported in prose; use spaces or a code block")
            path = primary if ord(ch) in self.maps[primary] else fallback
            if ord(ch) not in self.maps[path]:
                raise LayoutError(f"missing glyph {ch!r} (U+{ord(ch):04X}); choose a font that covers it")
            if runs and runs[-1][0] == path:
                runs[-1] = (path, runs[-1][1] + ch)
            else:
                runs.append((path, ch))
        return tuple(runs)

    def width(self, text, size, bold=False):
        return sum(self.font(p, size).getlength(s) for p, s in self.runs(text, size, bold))

    def wrap(self, text, width, size, bold=False):
        if width < size:
            raise LayoutError("text column is narrower than one glyph")
        lines = []
        closing = set("，。；：？！、）》】」』”’％%,.;:!?)]}")
        for paragraph in str(text).split("\n"):
            if not paragraph:
                lines.append("")
                continue
            tokens = re.findall(r"[A-Za-z0-9_][A-Za-z0-9_./:+-]*|[ \t]+|.", paragraph)
            current = ""
            for token in tokens:
                if self.width(current + token, size, bold) <= width:
                    current += token
                    continue
                if current:
                    match = re.search(r"[A-Za-z0-9_][A-Za-z0-9_./:+-]*$", current)
                    carry = match.group() if match else current[-1]
                    rest = current[:-len(carry)]
                    if token in closing and rest and self.width(carry + token, size, bold) <= width:
                        lines.append(rest.rstrip())
                        current = carry
                    else:
                        lines.append(current.rstrip())
                        current = ""
                token = token.lstrip() if not current else token
                for ch in token:
                    if current and self.width(current + ch, size, bold) > width:
                        lines.append(current.rstrip())
                        current = ""
                    current += ch
            if current:
                lines.append(current.rstrip())
        return lines

    def draw_line(self, draw, text, x, y, size, color, bold=False):
        base = y + size
        for path, run in self.runs(text, size, bold):
            font = self.font(path, size)
            draw.text((x, base), run, font=font, anchor="ls", fill=color)
            x += font.getlength(run)


@lru_cache(maxsize=256)
def formula_image(latex, size, color):
    if not latex.strip() or "$" in latex:
        raise LayoutError("formula.latex must contain a math expression without $ delimiters")
    if any("\u3400" <= ch <= "\u9fff" for ch in latex):
        raise LayoutError("put Chinese explanation in formula.caption, outside the math expression")
    buffer = io.BytesIO()
    try:
        with matplotlib.rc_context({"mathtext.fontset": "stix", "text.usetex": False, "savefig.transparent": True}), warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            warnings.simplefilter("ignore", DeprecationWarning)
            math_to_image("$" + latex + "$", buffer,
                          prop=FontProperties(size=size / 2), dpi=144,
                          format="png", color=color)
        image = Image.open(buffer).convert("RGBA")
        image.load()
        return image
    except Exception as exc:
        raise LayoutError(f"unsupported or invalid Mathtext formula {latex!r}: {exc}") from exc


class Scene:
    def __init__(self, fonts, theme):
        self.fonts, self.t = fonts, theme
        self.ops = []
        self.bounds = []

    def box(self, x, y, w, h, fill, outline=None, radius=16):
        self.ops.append(("box", x, y, w, h, fill, outline, radius))

    def line(self, points, fill, width=3):
        self.ops.append(("line", points, fill, width))

    def text(self, text, x, y, width, size=None, color=None, bold=False, line_height=None, max_lines=None):
        size = size or self.t["body_size"]
        color = color or self.t["ink"]
        lh = math.ceil(size * (line_height or self.t["line_height"]))
        lines = self.fonts.wrap(text, width, size, bold)
        if max_lines and len(lines) > max_lines:
            raise LayoutError(f"text needs {len(lines)} lines, allowed {max_lines}: {text!r}")
        h = len(lines) * lh
        for i, line in enumerate(lines):
            self.ops.append(("text", line, x, y + i * lh, size, color, bold))
        return h

    def heading(self, text, x, y, width, color=None):
        if not text:
            return 0
        return self.text(text, x, y, width, 40, color or self.t["accent"], True, 1.25) + 12

    def math(self, latex, x, y, width, size=60, centered=True):
        image = formula_image(latex, size, self.t["ink"])
        if image.width > width:
            raise LayoutError(f"formula width {image.width}px exceeds {width}px; split at a meaningful equality")
        xx = x + (width - image.width) / 2 if centered else x
        self.ops.append(("image", image, xx, y))
        return image.height

    def block(self, block, x, y, width):
        start = y
        kind = block["kind"]
        heading = block.get("heading")
        if kind != "callout":
            y += self.heading(heading, x, y, width)
        if kind == "paragraph":
            y += self.text(block["text"], x, y, width)
        elif kind == "callout":
            pad = 26
            tone = block.get("tone", "key")
            color = self.t["warning"] if tone == "caution" else self.t["accent"]
            fill = self.t["warning_soft"] if tone == "caution" else self.t["accent_soft"]
            idx = len(self.ops)
            yy = y + pad
            yy += self.heading(heading, x + pad, yy, width - 2 * pad, color)
            yy += self.text(block["text"], x + pad, yy, width - 2 * pad)
            self.ops.insert(idx, ("box", x, y, width, yy - y + pad, fill, None, 16))
            y = yy + pad
        elif kind == "bullets":
            for item in block["items"]:
                self.box(x + 3, y + 22, 10, 10, self.t["accent"], radius=4)
                y += self.text(item, x + 32, y, width - 32) + 16
            y -= 16
        elif kind == "steps":
            for number, item in enumerate(block["items"], 1):
                self.box(x, y + 6, 52, 52, self.t["accent_soft"], radius=12)
                self.text(str(number), x + 10, y + 5, 38, 32, self.t["accent"], True)
                y += self.text(item["label"], x + 74, y, width - 74, 46, bold=True)
                y += self.text(item["text"], x + 74, y + 4, width - 74) + 22
            y -= 18
        elif kind == "formula":
            y += 14 + self.math(block["latex"], x, y + 14, width) + 18
            if block.get("caption"):
                y += self.text(block["caption"], x, y + 8, width, 44) + 8
        elif kind == "matrix":
            y += self.matrix(block, x, y, width)
        elif kind == "table":
            y += self.table(block, x, y, width)
        elif kind == "flow":
            y += self.flow(block, x, y, width)
        elif kind == "code":
            pad = 24
            lines = block["text"].expandtabs(4).split("\n")
            for line in lines:
                if self.fonts.width(line, 44) > width - 2 * pad:
                    raise LayoutError("code line exceeds available width; explicitly break the code")
            h = len(lines) * 62 + 2 * pad
            self.box(x, y, width, h, self.t["paper"], self.t["rule"])
            for i, line in enumerate(lines):
                self.text(line or " ", x + pad, y + pad + i * 62, width - 2 * pad, 44, line_height=1.3)
            y += h
        elif kind == "bar":
            y += self.bar(block, x, y, width)
        else:
            raise LayoutError(f"unsupported block kind: {kind}")
        self.bounds.append({"id": block["id"], "kind": kind,
                            "box": [round(x), round(start), round(width), round(y - start)]})
        return y - start

    def matrix(self, block, x, y, width):
        cells = [[formula_image(c, 56, self.t["ink"]) for c in row] for row in block["cells"]]
        ncols = len(cells[0])
        cw = [max(row[c].width for row in cells) + 38 for c in range(ncols)]
        rh = [max(image.height for image in row) + 24 for row in cells]
        left = formula_image(block["left_label"], 56, self.t["ink"]) if block.get("left_label") else None
        lw = left.width + 24 if left else 0
        w = sum(cw) + 44 + lw
        h = max(sum(rh) + 16, left.height if left else 0)
        if w > width:
            raise LayoutError(f"matrix needs {w}px, available {width}px; split the calculation")
        sx = x + (width - w) / 2
        if left:
            self.ops.append(("image", left, sx, y + (h - left.height) / 2))
        mx = sx + lw
        top = y + (h - sum(rh)) / 2
        self.line([(mx + 16, top), (mx, top), (mx, top + sum(rh)), (mx + 16, top + sum(rh))], self.t["ink"])
        right = mx + sum(cw) + 44
        self.line([(right - 16, top), (right, top), (right, top + sum(rh)), (right - 16, top + sum(rh))], self.t["ink"])
        yy = top
        for r, row in enumerate(cells):
            xx = mx + 22
            for c, image in enumerate(row):
                self.ops.append(("image", image, xx + (cw[c] - image.width) / 2, yy + (rh[r] - image.height) / 2))
                xx += cw[c]
            yy += rh[r]
        if block.get("caption"):
            h += 20 + self.text(block["caption"], x, y + h + 20, width, 44)
        return h + 12

    def table(self, block, x, y, width):
        headers, rows = block["headers"], block["rows"]
        weights = block.get("widths", [1] * len(headers))
        widths = [width * w / sum(weights) for w in weights]
        pad, size, lh = 18, 44, 60
        start = y
        for rownum, row in enumerate([headers] + rows):
            lines = [self.fonts.wrap(cell, w - 2 * pad, size, rownum == 0) for cell, w in zip(row, widths)]
            h = max(len(ls) for ls in lines) * lh + 2 * pad
            xx = x
            for colnum, (cell, w) in enumerate(zip(row, widths)):
                self.box(xx, y, w, h, self.t["accent_soft"] if rownum == 0 else self.t["paper"], self.t["rule"], 0)
                for j, line in enumerate(lines[colnum]):
                    self.ops.append(("text", line, xx + pad, y + pad + j * lh, size, self.t["ink"], rownum == 0))
                xx += w
            y += h
        return y - start

    def flow(self, block, x, y, width):
        nodes = {n["id"]: n for n in block["nodes"]}
        incoming = {n: [] for n in nodes}
        for edge in block["edges"]:
            incoming[edge["to"]].append(edge["from"])
        levels = {}
        while len(levels) < len(nodes):
            ready = [n for n in nodes if n not in levels and all(p in levels for p in incoming[n])]
            if not ready:
                raise LayoutError("flow contains a cycle; split the cycle into a narrated sequence")
            for n in ready:
                levels[n] = max((levels[p] + 1 for p in incoming[n]), default=0)
        for edge in block["edges"]:
            if levels[edge["to"]] != levels[edge["from"]] + 1:
                raise LayoutError("flow edges must join adjacent levels; add an explicit intermediate step")
        boxes = {}
        yy = y
        text_ops, boxes_ops = [], []
        for level in range(max(levels.values()) + 1):
            group = [n for n in nodes if levels[n] == level]
            if len(group) > 3:
                raise LayoutError("flow has more than 3 parallel nodes; divide into related cards")
            gap = 30
            bw = (width - gap * (len(group) - 1)) / len(group)
            height = 0
            prepared = []
            for i, node_id in enumerate(group):
                node, xx = nodes[node_id], x + i * (bw + gap)
                before = len(self.ops)
                th = self.text(node["label"], xx + 24, yy + 18, bw - 48, 46, bold=True)
                if node.get("text"):
                    th += 8 + self.text(node["text"], xx + 24, yy + 18 + th + 8, bw - 48, 44)
                text_ops.extend(self.ops[before:])
                del self.ops[before:]
                prepared.append((node_id, xx))
                height = max(height, th + 36)
            for node_id, xx in prepared:
                boxes[node_id] = (xx, yy, bw, height)
                boxes_ops.append(("box", xx, yy, bw, height, self.t["paper"], self.t["rule"], 14))
            yy += height + 100
        segments, label_boxes = [], []
        for edge in block["edges"]:
            a, b = boxes[edge["from"]], boxes[edge["to"]]
            p = (a[0] + a[2] / 2, a[1] + a[3] + 4)
            q = (b[0] + b[2] / 2, b[1] - 8)
            for old_p, old_q, old_from, old_to in segments:
                if edge['from'] == old_from or edge['to'] == old_to:
                    continue
                def cross(a, b, c):
                    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
                if cross(p, q, old_p)*cross(p, q, old_q) < 0 and cross(old_p, old_q, p)*cross(old_p, old_q, q) < 0:
                    raise LayoutError('flow arrows cross; reorder parallel nodes or split the diagram')
            segments.append((p, q, edge['from'], edge['to']))
            self.line([p, q], self.t["accent"], 4)
            angle = math.atan2(q[1] - p[1], q[0] - p[0])
            self.line([(q[0] - 15 * math.cos(angle - .45), q[1] - 15 * math.sin(angle - .45)), q,
                       (q[0] - 15 * math.cos(angle + .45), q[1] - 15 * math.sin(angle + .45))], self.t["accent"], 4)
            if edge.get("label"):
                label = edge["label"]
                tw = self.fonts.width(label, 44)
                if tw > min(width / 2, 420):
                    raise LayoutError("flow edge label is too long; put the explanation in a node")
                mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
                label_box = (mx-tw/2-12, my-30, mx+tw/2+12, my+34)
                if label_box[0] < x or label_box[2] > x + width:
                    raise LayoutError('flow edge label exceeds content width')
                for old in label_boxes:
                    if max(old[0], label_box[0]) < min(old[2], label_box[2]) and max(old[1], label_box[1]) < min(old[3], label_box[3]):
                        raise LayoutError('flow edge labels overlap; shorten labels or split the diagram')
                label_boxes.append(label_box)
                self.box(mx - tw / 2 - 12, my - 30, tw + 24, 64, self.t["background"], radius=8)
                self.text(label, mx - tw / 2, my - 30, tw + 2, 44, self.t["accent"], line_height=1.3)
        self.ops.extend(boxes_ops)
        self.ops.extend(text_ops)
        return yy - y - 100

    def bar(self, block, x, y, width):
        start = y
        peak = max(block["values"], default=0) or 1
        for label, value in zip(block["labels"], block["values"]):
            y += self.text(f"{label}  {value:g}", x, y, width, 44)
            self.box(x, y + 10, width, 22, self.t["accent_soft"], radius=6)
            self.box(x, y + 10, max(1, width * value / peak), 22, self.t["accent"], radius=6)
            y += 56
        if block.get("caption"):
            y += self.text(block["caption"], x, y, width, 44)
        return y - start

    def render(self):
        image = Image.new("RGB", (self.t["width"], self.t["height"]), self.t["background"])
        draw = ImageDraw.Draw(image)
        for op in self.ops:
            if op[0] == "box":
                _, x, y, w, h, fill, outline, radius = op
                draw.rounded_rectangle((round(x), round(y), round(x + w), round(y + h)), radius=radius, fill=fill, outline=outline, width=2)
            elif op[0] == "line":
                draw.line(op[1], fill=op[2], width=op[3], joint="curve")
            elif op[0] == "text":
                _, text, x, y, size, color, bold = op
                self.fonts.draw_line(draw, text, x, y, size, color, bold)
            elif op[0] == "image":
                _, sprite, x, y = op
                image.paste(sprite, (round(x), round(y)), sprite)
        return image


TYPE_LABELS = {"explanation": "讲解", "self_check": "自测", "answer": "解答"}
LAYOUT_LABELS = {"concept": "概念", "formula": "公式", "process": "流程", "comparison": "对比",
                 "worked_example": "例题", "misconception": "辨析", "question": "独立解释", "answer": "核对依据"}


def plan_card(card, fonts, theme):
    t = dict(theme)
    if card["type"] == "self_check":
        t["accent"], t["accent_soft"] = t["question"], t["question_soft"]
    elif card["type"] == "answer":
        t["accent"], t["accent_soft"] = t["answer"], t["answer_soft"]
    scene = Scene(fonts, t)
    x, width = t["margin"], t["width"] - 2 * t["margin"]
    scene.box(x, 64, 206, 54, t["accent_soft"], radius=12)
    scene.text(TYPE_LABELS[card["type"]], x + 18, 67, 180, 32, t["accent"], True)
    # Reader-facing series name; internal IDs remain in files and references.
    series = card.get("series_title", "")
    if series:
        sw = fonts.width(series, 26)
        if sw <= width - 250:
            scene.text(series, t["width"] - x - sw, 78, sw + 2, 26, t["muted"])
    y = 145
    y += scene.text(card["title"], x, y, width, t["title_size"], bold=True, line_height=1.2, max_lines=2)
    y += 16
    unit_title = card.get("unit_title", "")
    descriptor = LAYOUT_LABELS[card["layout"]]
    if card.get("depth") == "deep":
        descriptor += " · 深入"
    subtitle = f"{unit_title} / {descriptor}" if unit_title else descriptor
    y += scene.text(subtitle, x, y, width, 28, t["muted"], max_lines=2)
    y += 22
    scene.line([(x, y), (x + width, y)], t["rule"], 2)
    y += 30
    content_start = y
    for block in card["blocks"]:
        try:
            used = scene.block(block, x, y, width)
        except LayoutError as exc:
            raise LayoutError(f"{card['id']} / {block['id']}: {exc}") from exc
        if y + used > 1450:
            raise LayoutError(f"{card['id']} / {block['id']}: content ends at {math.ceil(y + used)}px (limit 1450px); revise layout or split this complete sub-question")
        y += used + t["block_gap"]
    scene.line([(x, 1492), (x + width, 1492)], t["rule"], 2)
    footer = "用自己的话解释 · 答后核对" if card["type"] == "self_check" else "CRASH CARD"
    if card["type"] == "answer" and card.get("explanation_titles"):
        footer = "回看：" + "、".join("《" + title + "》" for title in card["explanation_titles"])
        if fonts.width(footer, 26) > width - 260:
            footer = "回看本主题的讲解篇"
    scene.text(footer, x, 1510, width - 260, 26, t["muted"])
    page = card.get("page")
    if page and page["total"] > 1:
        suffix = f"{page['index']} / {page['total']}"
        sw = fonts.width(suffix, 26)
        scene.text(suffix, t["width"] - x - sw, 1510, sw + 2, 26, t["muted"])
    return scene, {"content_top": content_start, "content_bottom": y - t["block_gap"],
                   "blocks": scene.bounds, "block_ids": [b["id"] for b in card["blocks"]]}
