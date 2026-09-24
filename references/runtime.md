# Runtime requirements

The card workflow has platform adapters with a small, explicit dependency set. Resolve `SKILL_ROOT` and `OUTPUT_DIR` as described in SKILL.md; all paths below use those absolute directories, regardless of the current working directory.

On macOS:

- Python 3.9 or newer. `render_cards.py`, `validate_manifest.py`, and `validate_outputs.py` use only the Python standard library.
- The `swift` command with AppKit support. This is supplied by macOS Xcode Command Line Tools or Xcode and produces the PNG files without a browser or an image package.

On Windows or Linux:

- Python 3.9 or newer.
- Pillow 10 or newer: `python -m pip install -r "$SKILL_ROOT/requirements-renderer.txt"` (or `python -m pip install "Pillow>=10"`).
- A CJK-capable font. The adapter searches common Noto Sans CJK, Microsoft YaHei, and macOS font paths; use the main renderer’s `--font-path /path/to/font.ttf` option when the font is elsewhere.

Not required at runtime on macOS:

- PyYAML. It is only used by the separate Codex `quick_validate.py` development checker.
- CairoSVG, Playwright, Chromium, Node.js, npm, ImageMagick, and `sips`.
- Any network access, package installation, or third-party Skill.

Run `python3 "$SKILL_ROOT/scripts/check_environment.py"` before rendering. `render_cards.py` selects Swift/AppKit on macOS and Pillow elsewhere. You can override this with `--renderer swift|pillow|svg`; `--font-path` or `CRASH_FLASHCARD_FONT` supplies a font to Pillow. If the selected adapter or a CJK font is unavailable, the renderer can still write SVG inspection sources, but PNG delivery is incomplete. Do not present SVG-only output as finished when the user requested PNG.
