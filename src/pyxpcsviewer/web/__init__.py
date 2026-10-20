# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""The web viewer: a FastAPI service over :mod:`pyxpcsviewer.core` and a browser front end.

:mod:`pyxpcsviewer.web.workspace` holds every computation (no web framework imported there);
:mod:`pyxpcsviewer.web.app` exposes it as a JSON API and serves the page in ``static/``;
``pyxpcsviewer-web`` (:mod:`pyxpcsviewer.web.cli`) starts the server.
"""
