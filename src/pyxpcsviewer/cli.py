# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Console script for pyxpcsviewer."""

import argparse
import sys


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
    argparser.add_argument("--label_style", type=str, help="label style", default=None)

    args = argparser.parse_args()
    if args.positional_path is not None:
        args.path = args.positional_path

    sys.exit(main_gui(args.path, args.label_style))


if __name__ == "__main__":
    sys.exit(main())
