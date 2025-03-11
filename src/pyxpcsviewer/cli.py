"""Console script for pyxpcsviewer."""
import sys
import argparse


def main():
    from pyxpcsviewer import __version__
    from pyxpcsviewer.xpcs_viewer import main_gui

    argparser = argparse.ArgumentParser(
        description='pyXpcsViewer: a GUI tool for XPCS data analysis')

    argparser.add_argument("--version", action="version",
                           version=f"pyxpcsviewer: {__version__}")

    argparser.add_argument('--path', type=str, help='path to the result folder',
                          default='./')
    argparser.add_argument("positional_path", nargs="?", default=None,
                        help="positional path to the result folder")
    # Determine the directory to monitor
    argparser.add_argument('--label_style', type=str, help='label style',
                          default=None)

    args = argparser.parse_args()
    if args.positional_path is not None:
        args.path = args.positional_path

    sys.exit(main_gui(args.path, args.label_style))


if __name__ == "__main__":
    main()
