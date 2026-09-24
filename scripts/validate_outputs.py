#!/usr/bin/env python3
"""Validate PNG outputs against a crash-card manifest."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        raise ValueError(f"not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        dimensions = manifest["dimensions"]
        expected = (dimensions["width"], dimensions["height"])
        for card in manifest["cards"]:
            folder = "quick-check" if card["type"] == "quick_check" else "explanation"
            path = args.output_dir / folder / f"{card['id']}.png"
            if not path.is_file() or path.stat().st_size < 100:
                raise ValueError(f"missing or empty PNG: {path}")
            if png_size(path) != expected:
                raise ValueError(f"wrong dimensions for {path}: got {png_size(path)}, expected {expected}")
        expected_paths = {
            args.output_dir / ("quick-check" if card["type"] == "quick_check" else "explanation") / f"{card['id']}.png"
            for card in manifest["cards"]
        }
        actual_paths = set(args.output_dir.glob("quick-check/*.png")) | set(args.output_dir.glob("explanation/*.png"))
        extras = actual_paths - expected_paths
        if extras:
            raise ValueError(f"unexpected PNG output(s): {', '.join(str(path) for path in sorted(extras))}")
        print(f"outputs valid: {len(manifest['cards'])} PNG(s), {expected[0]}x{expected[1]}")
        return 0
    except (OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"outputs invalid: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
