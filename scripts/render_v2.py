"""v2 rendering transaction and auditable output report."""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
from pathlib import Path
from layout_v2 import Fonts, LayoutError, plan_card
from PIL import __version__ as pillow_version
import matplotlib
from v2_contract import resolve_cards, export_text

FOLDERS = {'explanation': 'explanation', 'self_check': 'self-check', 'answer': 'answer'}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def render(data, raw, output_dir, regular=None, bold=None):
    out = Path(output_dir).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if list((out / 'quick-check').glob('*.png')):
        raise LayoutError('v1 quick-check PNGs remain; render v2 into a separate output directory')
    fonts = Fonts(regular, bold)
    theme_path = Path(__file__).resolve().parents[1] / 'assets/theme.json'
    theme = json.loads(theme_path.read_text(encoding='utf-8'))
    cards = resolve_cards(data)
    plans, errors = [], []
    for card in cards:
        try:
            scene, measurements = plan_card(card, fonts, theme)
            plans.append((card, scene, measurements))
        except LayoutError as exc:
            errors.append(str(exc))
    if errors:
        raise LayoutError('\n'.join(errors))
    expected = {f"{FOLDERS[c['type']]}/{c['id']}.png" for c in cards}
    prior = {}
    if (out / 'render-report.json').is_file():
        try:
            prior = {c['path']: c['png_sha256'] for c in json.loads((out / 'render-report.json').read_text())['cards']}
        except (KeyError, TypeError, ValueError):
            pass
    obsolete = []
    for folder in FOLDERS.values():
        if (out / folder).is_symlink():
            raise LayoutError(f'output group is a symlink: {out / folder}')
        for path in (out / folder).glob('*.png'):
            rel = path.relative_to(out).as_posix()
            if rel not in expected:
                if path.is_symlink() or prior.get(rel) != sha256(path.read_bytes()):
                    raise LayoutError(f'unmanaged or modified obsolete PNG: {rel}; render to a new output directory')
                obsolete.append(path)
    report = {'schema_version': 2, 'manifest_sha256': sha256(raw), 'dimensions': data['dimensions'],
              'backend': f'Pillow {pillow_version} + Mathtext {matplotlib.__version__}',
              'theme_sha256': sha256(theme_path.read_bytes()),
              'fonts': {'regular': fonts.regular, 'bold': fonts.bold,
                        'regular_sha256': sha256(Path(fonts.regular).read_bytes()),
                        'bold_sha256': sha256(Path(fonts.bold).read_bytes())}, 'cards': []}
    with tempfile.TemporaryDirectory(prefix='.crash-cards-', dir=out.parent) as temp:
        stage = Path(temp)
        for card, scene, measure in plans:
            rel = f"{FOLDERS[card['type']]}/{card['id']}.png"
            path = stage / rel
            path.parent.mkdir(exist_ok=True)
            scene.render().save(path, 'PNG', optimize=True)
            report['cards'].append({'id': card['id'], 'type': card['type'], 'path': rel,
                                    'png_sha256': sha256(path.read_bytes()), 'width': 1200, 'height': 1600, **measure})
        (stage / 'manifest.json').write_bytes(raw)
        export_text(data, stage)
        (stage / 'render-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        out.mkdir(exist_ok=True)
        # Preflight and render all cards before replacing any final artifact.
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                target = out / path.relative_to(stage)
                target.parent.mkdir(exist_ok=True)
                if target.is_symlink():
                    raise LayoutError(f'output file is a symlink: {target}')
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                os.replace(path, out / path.relative_to(stage))
        for path in obsolete:
            path.unlink()
    print(f"Rendered {len(cards)} cards at 1200×1600 to {out}")
    print('All blocks measured; inspect final PNGs for factual and visual quality.')
