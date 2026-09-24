#!/usr/bin/env python3
"""Render flashcard manifests. v2: measured 1200×1600 PNG; v1: legacy adapters."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--renderer', choices=['auto', 'pillow', 'swift', 'svg'], default='auto')
    parser.add_argument('--font-path', help='Local Chinese regular font (.ttf/.otf/.ttc first face)')
    parser.add_argument('--font-bold-path', help='Optional local bold font')
    args = parser.parse_args()
    try:
        raw = args.manifest.read_bytes()
        data = json.loads(raw)
        version = data.get('schema_version', 1) if isinstance(data, dict) else None
        if type(version) is not int:
            raise ValueError('schema_version must be an integer')
        if version == 1:
            legacy = Path(__file__).parent / 'legacy/render_cards.py'
            return subprocess.run([sys.executable, str(legacy), *sys.argv[1:]], check=False).returncode
        if version != 2:
            raise ValueError(f'unsupported schema_version: {version!r}')
        if args.renderer not in ('auto', 'pillow'):
            raise ValueError('v2 supports the measured Pillow renderer; swift/svg are v1-only')
        from v2_contract import validate
        errors = validate(data)
        if errors:
            raise ValueError('\n'.join(errors))
        try:
            from render_v2 import render
        except ImportError as exc:
            raise ValueError('v2 dependencies unavailable; install the skill requirements.txt in a virtual environment: ' + str(exc)) from exc
        render(data, raw, args.output_dir, args.font_path, args.font_bold_path)
        return 0
    except (ValueError, OSError) as exc:
        print(f'render failed: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
