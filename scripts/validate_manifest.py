#!/usr/bin/env python3
"""Validate v2 strictly; dispatch genuine v1 manifests to the preserved validator."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path
from v2_contract import validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('manifest must be an object')
        version = data.get('schema_version', 1)
        if type(version) is int and version == 1:
            return subprocess.run([sys.executable, str(Path(__file__).parent / 'legacy' / 'validate_manifest.py'), str(args.manifest)], check=False).returncode
        errors = validate(data)
        if errors:
            raise ValueError('\n'.join(errors))
        print(f"manifest valid: v2, {len(data['cards'])} card(s), 1200x1600")
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f'manifest invalid: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
