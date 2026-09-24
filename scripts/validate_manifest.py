#!/usr/bin/env python3
"""Validate the small JSON manifest consumed by crash-card."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
ALLOWED_TYPES = {"quick_check", "explanation"}


def fail(message: str) -> None:
    raise ValueError(message)


def text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty string")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        for field in ("title", "caption"):
            text(data.get(field), field)
        topics = data.get("topics")
        if not isinstance(topics, list) or not topics or not all(isinstance(item, str) and item.strip() for item in topics):
            fail("topics must be a non-empty string array")
        dimensions = data.get("dimensions")
        if not isinstance(dimensions, dict):
            fail("dimensions must be an object")
        width, height = dimensions.get("width"), dimensions.get("height")
        if not isinstance(width, int) or not isinstance(height, int) or not (320 <= width <= 4000 and 320 <= height <= 4000):
            fail("dimensions width and height must be integers between 320 and 4000")
        cards = data.get("cards")
        if not isinstance(cards, list) or not cards:
            fail("cards must be a non-empty array")
        ids: set[str] = set()
        for index, card in enumerate(cards):
            prefix = f"cards[{index}]"
            if not isinstance(card, dict):
                fail(f"{prefix} must be an object")
            card_id = text(card.get("id"), f"{prefix}.id")
            if not SAFE_ID.fullmatch(card_id):
                fail(f"{prefix}.id contains unsafe path characters")
            if card_id in ids:
                fail(f"duplicate card id: {card_id}")
            ids.add(card_id)
            card_type = card.get("type")
            if card_type not in ALLOWED_TYPES:
                fail(f"{prefix}.type must be quick_check or explanation")
            text(card.get("title"), f"{prefix}.title")
            if card_type == "quick_check":
                text(card.get("prompt"), f"{prefix}.prompt")
                blanks, answers = card.get("blanks"), card.get("answer_key")
                if not isinstance(blanks, list) or not blanks or not all(isinstance(item, str) for item in blanks):
                    fail(f"{prefix}.blanks must be a non-empty string array")
                if len(blanks) > 6:
                    fail(f"{prefix}.blanks supports at most 6 items")
                if not isinstance(answers, list) or len(answers) != len(blanks) or not all(isinstance(item, str) and item.strip() for item in answers):
                    fail(f"{prefix}.answer_key must have one non-empty answer per blank")
                visible = " ".join(str(card.get(key, "")) for key in ("title", "prompt", "blanks"))
                for answer in answers:
                    if answer.strip() and answer.strip() in visible:
                        fail(f"{prefix} leaks answer text in visible fields: {answer!r}")
            else:
                content_fields = ("definition", "points", "table", "chart", "takeaway")
                if not any(card.get(field) for field in content_fields):
                    fail(f"{prefix} needs definition, points, table, chart, or takeaway")
                if card.get("points") is not None:
                    if not isinstance(card["points"], list) or any(not isinstance(point, dict) or not point.get("label") or not point.get("text") for point in card["points"]):
                        fail(f"{prefix}.points must contain label and text")
                    if len(card["points"]) > 5:
                        fail(f"{prefix}.points supports at most 5 items")
                table = card.get("table")
                if table is not None:
                    if not isinstance(table, dict):
                        fail(f"{prefix}.table must be an object")
                    headers, rows = table.get("headers"), table.get("rows")
                    if not isinstance(headers, list) or not headers or not all(isinstance(item, str) and item.strip() for item in headers):
                        fail(f"{prefix}.table.headers must be a non-empty string array")
                    if not isinstance(rows, list) or len(rows) > 5 or any(not isinstance(row, list) or len(row) != len(headers) for row in rows):
                        fail(f"{prefix}.table.rows must match header width")
                chart = card.get("chart")
                if chart is not None:
                    if not isinstance(chart, dict) or chart.get("kind") != "bar" or not isinstance(chart.get("labels"), list) or not isinstance(chart.get("values"), list) or len(chart["labels"]) != len(chart["values"]) or not chart["labels"] or not all(isinstance(label, str) and label.strip() for label in chart["labels"]):
                        fail(f"{prefix}.chart must be a bar chart with equal non-empty labels and values")
                    if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 for value in chart["values"]):
                        fail(f"{prefix}.chart.values must be finite non-negative numbers")
            serialized = json.dumps(card, ensure_ascii=False)
            if any(token in serialized for token in ("{{", "}}", "[TODO]")):
                fail(f"{prefix} contains an unresolved placeholder")
        print(f"manifest valid: {len(cards)} card(s), {width}x{height}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"manifest invalid: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
