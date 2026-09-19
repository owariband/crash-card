#!/usr/bin/env python3
"""Check the local runtime needed for crash-flashcard PNG rendering."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys


def main() -> int:
    problems: list[str] = []
    if sys.version_info < (3, 9):
        problems.append(f"Python 3.9+ is required (found {platform.python_version()})")
    if platform.system() != "Darwin":
        problems.append("PNG rendering currently requires macOS because the rasterizer uses AppKit")
    swift = shutil.which("swift")
    if swift is None:
        problems.append("the `swift` command is missing; install macOS Xcode Command Line Tools")
    if problems:
        print("environment incomplete:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        print("SVG source output remains possible, but PNG rendering is unavailable.", file=sys.stderr)
        return 2
    try:
        version = subprocess.run([swift, "--version"], check=True, capture_output=True, text=True).stdout.splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError) as exc:
        print(f"environment incomplete: Swift exists but could not be queried: {exc}", file=sys.stderr)
        return 2
    print(f"environment ready: Python {platform.python_version()}, {version}")
    print("runtime packages: Python standard library only")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
