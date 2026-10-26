# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""``pyxpcsviewer-web``: serve the web viewer for a result folder."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import webbrowser

from pyxpcsviewer.cli import _label_style_type


def main(argv: list[str] | None = None) -> int:
    from pyxpcsviewer import __version__

    parser = argparse.ArgumentParser(
        prog="pyxpcsviewer-web", description="pyXPCSViewer in the browser: serve a folder of XPCS result files"
    )
    parser.add_argument("--version", action="version", version=f"pyxpcsviewer: {__version__}")
    parser.add_argument("path", nargs="?", default=".", help="the result folder (default: the current directory)")
    parser.add_argument(
        "--host", default="127.0.0.1", help="address to listen on (default 127.0.0.1; 0.0.0.0 opens it to the network)"
    )
    parser.add_argument("--port", type=int, default=8070, help="port (default 8070)")
    parser.add_argument(
        "--label-style",
        type=_label_style_type,
        default=None,
        help="underscore-separated filename-segment indices for short labels, e.g. '0_2'",
    )
    parser.add_argument("--cache-size", type=int, default=8, help="open files kept in memory (default 8)")
    parser.add_argument("--open", action="store_true", help="open the page in a browser once the server is up")
    parser.add_argument("--log-level", default="info", choices=("critical", "error", "warning", "info", "debug"))
    parser.add_argument(
        "--export-openapi",
        metavar="FILE",
        help="write the API document (OpenAPI JSON) to FILE ('-' for stdout) and exit, instead of serving; "
        "the committed copy lives at src/pyxpcsviewer/web/openapi.json",
    )
    args = parser.parse_args(argv)

    if args.export_openapi:
        try:
            from .openapi import export_openapi, openapi_text
        except ModuleNotFoundError as exc:
            parser.error(f"the API export needs the web extra ({exc.name} is missing): pip install 'xpcs-viewer[web]'")
        if args.export_openapi == "-":
            sys.stdout.write(openapi_text())
        else:
            print(f"API document written to {export_openapi(args.export_openapi)}", file=sys.stderr)
        return 0

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        parser.error(f"not a directory: {root}")
    try:
        import uvicorn
    except ModuleNotFoundError:
        parser.error("the web viewer needs fastapi, uvicorn and plotly: pip install 'xpcs-viewer[web]'")

    from .app import build_app, plotly_js_path

    if plotly_js_path() is None:
        parser.error("the plotly package is missing (it provides plotly.js): pip install plotly")

    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s %(name)s: %(message)s")
    app = build_app(root, label_style=args.label_style, cache_size=args.cache_size, host=args.host)
    shown = "127.0.0.1" if args.host in ("0.0.0.0", "::", "") else args.host
    url = f"http://{shown}:{args.port}/"
    print(f"pyXPCSViewer web {__version__}: {root}\n  {url}", file=sys.stderr)
    if args.open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)
    return 0


if __name__ == "__main__":
    sys.exit(main())
