#!/usr/bin/env python3
"""Check every v2 PNG by full decoding and verify render accounting and hashes."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from v2_contract import TYPE_DIRS, resolve_cards


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError('v2 PNG validation requires Pillow; install the renderer requirements') from exc
    with Image.open(path) as image:
        if image.format != 'PNG':
            raise ValueError(f'not a PNG: {path}')
        image.verify()  # verify PNG chunk checksums, including IDAT
    with Image.open(path) as image:
        image.load()  # decode all pixel data, not merely IHDR
        return image.size


def validate_outputs(output_dir: Path, manifest_path: Path) -> list[str]:
    manifest_bytes = manifest_path.read_bytes()
    data = json.loads(manifest_bytes)
    cards = resolve_cards(data)
    report_path = output_dir / 'render-report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    errors = []
    if not isinstance(report, dict):
        return ['render-report.json must be an object']
    if report.get('schema_version') != 2:
        errors.append('render report schema_version must be 2')
    if report.get('manifest_sha256') != hashlib.sha256(manifest_bytes).hexdigest():
        errors.append('render report manifest_sha256 does not match exact input manifest bytes')
    if report.get('dimensions') != {'width': 1200, 'height': 1600}:
        errors.append('render report dimensions must be 1200x1600')
    rows = report.get('cards')
    if not isinstance(rows, list):
        return errors + ['render report cards must be an array']
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            errors.append('each render report card must be an object with an id')
            continue
        if row['id'] in by_id:
            errors.append(f"duplicate render report card {row['id']}")
        by_id[row['id']] = row
    expected_ids = {c['id'] for c in cards}
    if set(by_id) != expected_ids:
        errors.append(f'render report card IDs differ: missing={sorted(expected_ids-set(by_id))}, unexpected={sorted(set(by_id)-expected_ids)}')
    expected_paths = set()
    for folder in TYPE_DIRS.values():
        if not (output_dir / folder).is_dir():
            errors.append(f'missing card directory: {folder}')
    for card in cards:
        cid = card['id']
        relative = f"{TYPE_DIRS[card['type']]}/{cid}.png"
        path = output_dir / relative
        expected_paths.add(relative)
        row = by_id.get(cid)
        if row:
            if row.get('path') != relative or row.get('type') != card['type']:
                errors.append(f'{cid}: render report path/type mismatch')
            if (row.get('width'), row.get('height')) != (1200, 1600):
                errors.append(f'{cid}: render report dimensions mismatch')
            expected_blocks = [b['id'] for b in card['blocks']]
            if row.get('block_ids') != expected_blocks:
                errors.append(f'{cid}: missing, reordered or unexpected rendered blocks; expected {expected_blocks}, got {row.get("block_ids")}')
            measured = row.get('blocks')
            if not isinstance(measured, list) or len(measured) != len(card['blocks']):
                errors.append(f'{cid}: measured blocks must account for every compiled block')
            else:
                finite = lambda v: type(v) in (int, float) and math.isfinite(v)
                content_top, content_bottom = row.get('content_top'), row.get('content_bottom')
                if not finite(content_top) or not finite(content_bottom) or not 0 <= content_top <= content_bottom <= 1450:
                    errors.append(f'{cid}: content bounds must be finite and within the safe area')
                    content_top = 0
                previous_bottom = content_top
                for block, measurement in zip(card['blocks'], measured):
                    if not isinstance(measurement, dict) or measurement.get('id') != block['id'] or measurement.get('kind') != block['kind']:
                        errors.append(f'{cid}: actual measured block ID/kind/order differs from compiled content')
                        continue
                    box = measurement.get('box')
                    if not isinstance(box, list) or len(box) != 4 or not all(finite(v) for v in box):
                        errors.append(f"{cid}/{block['id']}: measured box must contain four finite numbers")
                        continue
                    x, y, width, height = box
                    if width <= 0 or height <= 0 or x < 72 or y < content_top or x + width > 1128 or y + height > 1450:
                        errors.append(f"{cid}/{block['id']}: measured block lies outside the 72px/1450px safe bounds")
                    if y < previous_bottom:
                        errors.append(f"{cid}/{block['id']}: measured content blocks overlap or are out of reading order")
                    previous_bottom = max(previous_bottom, y + height)
                if finite(content_bottom) and previous_bottom > content_bottom + 1:
                    errors.append(f'{cid}: content_bottom omits part of the measured blocks')
        try:
            size = png_size(path)
            if size != (1200, 1600):
                errors.append(f'{relative}: decoded dimensions {size}, expected 1200x1600')
            if row and row.get('png_sha256') != digest(path):
                errors.append(f'{relative}: PNG SHA256 differs from render report')
        except (OSError, ValueError, SyntaxError) as exc:
            errors.append(f'{relative}: PNG decode failed: {exc}')
    actual_paths = {str(p.relative_to(output_dir)) for folder in TYPE_DIRS.values() for p in (output_dir / folder).glob('*.png')}
    extras = actual_paths - expected_paths
    if extras:
        errors.append(f'unexpected PNG output(s): {sorted(extras)}')
    # An old quick-check directory can otherwise conceal stale v1 cards.
    stale = list((output_dir / 'quick-check').glob('*.png'))
    if stale:
        errors.append('stale v1 quick-check PNGs exist in a v2 output directory; use a fresh directory')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir', type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding='utf-8'))
        if isinstance(data, dict) and type(data.get('schema_version', 1)) is int and data.get('schema_version', 1) == 1:
            return subprocess.run([sys.executable, str(Path(__file__).parent / 'legacy' / 'validate_outputs.py'), str(args.output_dir), '--manifest', str(args.manifest)], check=False).returncode
        errors = validate_outputs(args.output_dir, args.manifest)
        if errors:
            raise ValueError('\n'.join(errors))
        print(f"outputs valid: v2, {len(data['cards'])} PNG(s), 1200x1600; full decode, hashes and block coverage checked")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'outputs invalid: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
