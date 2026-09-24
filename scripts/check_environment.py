#!/usr/bin/env python3
"""Check the actual v2 Chinese text, formula, matrix, and PNG runtime."""
import argparse
import importlib.metadata
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font-path')
    parser.add_argument('--font-bold-path')
    args = parser.parse_args()
    try:
        from layout_v2 import Fonts, formula_image, Scene
        import io
        from PIL import Image
        fonts = Fonts(args.font_path, args.font_bold_path)
        fonts.width('概念、前提、机制与边界 → √2', 48)
        formula = formula_image(r'\frac{QK^{T}}{\sqrt{d_k}}', 60, '#172B40')
        if not formula.width or not formula.height:
            raise ValueError('empty formula output')
        buffer = io.BytesIO()
        formula.save(buffer, 'PNG')
        Image.open(io.BytesIO(buffer.getvalue())).load()
        print('v2 environment ready: Python ' + sys.version.split()[0])
        print(', '.join(name + ' ' + importlib.metadata.version(name) for name in ['Pillow', 'matplotlib', 'fonttools']))
        print('CJK regular: ' + fonts.regular)
        print('CJK bold: ' + fonts.bold)
        print('Chinese glyphs, fraction, radical, superscript/subscript and PNG decoding passed.')
        return 0
    except Exception as exc:
        print('environment incomplete: ' + str(exc), file=sys.stderr)
        print('Use a virtual environment with the skill requirements.txt and a local CJK font.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
