#!/usr/bin/env python3
"""Normalize all layout margin properties in a Qt .ui file to a target value.

Usage:
    python fix_layout_margins.py <ui_file> [target_value]

Target value defaults to 1.
"""

import re
import sys
from pathlib import Path


# Match any of the four layout margin property blocks
MARGIN_RE = re.compile(
    r'<property name="(leftMargin|topMargin|rightMargin|bottomMargin)">\s*\n\s*<number>(\d+)</number>',
    re.MULTILINE | re.DOTALL,
)


def fix_layout_margins(ui_path: str, target: int = 1) -> int:
    """Rewrite *ui_path* so that every layout margin property is set to *target*.

    Returns:
        Number of margins changed.
    """
    text = Path(ui_path).read_text(encoding="utf-8")
    count = 0

    def replacer(m: re.Match) -> str:
        nonlocal count
        count += 1
        return f'<property name="{m.group(1)}">\n        <number>{target}</number>'

    text = MARGIN_RE.sub(replacer, text)
    Path(ui_path).write_text(text, encoding="utf-8")
    return count


if __name__ == "__main__":
    path = sys.argv[1]
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    n = fix_layout_margins(path, target)
    print(f"{n} margin properties set to {target}")