# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Console script for pyxpcsviewer."""

import argparse
import re
import sys


def _label_style_type(value: str) -> str:
    """Argparse type for ``--label-style``.

    Validates that the value is a sequence of integer indices separated by
    underscores (e.g. ``"0_2"``). Raises ``argparse.ArgumentTypeError`` so the
    CLI exits with a usage error instead of silently degrading later.

    Args:
        value: Raw string passed on the command line.

    Returns:
        The validated string unchanged.

    Raises:
        argparse.ArgumentTypeError: If ``value`` is not underscore-separated
            non-negative integers.
    """
    if not re.fullmatch(r"\d+(?:_\d+)*", value):
        raise argparse.ArgumentTypeError(
            f"invalid label_style {value!r}: must be numbers separated by "
            "underscores, e.g. '0_2'"
        )
    return value


def main() -> int:
    """Entry point for the pyxpcsviewer CLI.

    Parses command-line arguments and launches the GUI with the
    specified data directory.

    Returns:
        Exit code for sys.exit().
    """
    from pyxpcsviewer import __version__
    from pyxpcsviewer.gui.view.xpcs_viewer import main_gui

    argparser = argparse.ArgumentParser(description="pyXpcsViewer: a GUI tool for XPCS data analysis")

    argparser.add_argument("--version", action="version", version=f"pyxpcsviewer: {__version__}")

    argparser.add_argument("--path", type=str, help="path to the result folder", default="./")
    argparser.add_argument(
        "positional_path",
        nargs="?",
        default=None,
        help="positional path to the result folder",
    )
    # Determine the directory to monitor
    argparser.add_argument(
        "--label-style",
        type=_label_style_type,
        help="underscore-separated filename-segment indices for building a short label, "
        "e.g. '0_2' on 'A001_Silica_D100_att0_Rq0_00001_results.hdf' gives 'A001_D100' "
        "(default: simplified filename)",
        default=None,
    )

    args = argparser.parse_args()
    if args.positional_path is not None:
        args.path = args.positional_path

    sys.exit(main_gui(args.path, args.label_style))


if __name__ == "__main__":
    sys.exit(main())
