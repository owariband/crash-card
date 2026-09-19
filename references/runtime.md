# Runtime requirements

The card workflow intentionally has no Python package dependency.

Required on the supported target (macOS):

- Python 3.9 or newer. `render_cards.py`, `validate_manifest.py`, and `validate_outputs.py` use only the Python standard library.
- The `swift` command with AppKit support. This is supplied by macOS Xcode Command Line Tools or Xcode and produces the PNG files without a browser or an image package.

Not required at runtime:

- PyYAML. It is only used by the separate Codex `quick_validate.py` development checker.
- Pillow, CairoSVG, Playwright, Chromium, Node.js, npm, ImageMagick, and `sips`.
- Any network access, package installation, or third-party Skill.

Run `python3 scripts/check_environment.py` before rendering. If Swift/AppKit is unavailable, the renderer can still write SVG inspection sources, but PNG delivery is incomplete. Do not present SVG-only output as finished when the user requested PNG.
