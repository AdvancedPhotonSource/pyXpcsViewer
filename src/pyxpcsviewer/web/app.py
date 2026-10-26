# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""The web viewer's HTTP side: a JSON API over :class:`~pyxpcsviewer.web.workspace.Workspace`
and the static page that calls it.

``build_app(root)`` returns the FastAPI application; ``pyxpcsviewer-web`` serves it with uvicorn.
Routes are thin: they parse parameters, call the workspace and turn its errors into 4xx answers.
"""

from __future__ import annotations

import ipaddress
import logging
from importlib import resources
from pathlib import Path
from typing import Any

from beamline_webkit import array_response, array_responses
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from pyxpcsviewer import __version__

from . import models
from .colormaps import COLORMAPS, colorscales
from .workspace import DEFAULT_G2_BOUNDS, DEFAULT_TAUQ_BOUNDS, Workspace, WorkspaceError

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
LOOPBACK_HOSTS = ("localhost", "*.localhost", "127.0.0.1", "[::1]")
# The version of the API as the committed openapi.json (``pyxpcsviewer-web --export-openapi``) describes
# it: bump the minor for an addition, the major for a change a frontend built against the old document
# would not survive. The package version is separate: it changes with every release.
API_SCHEMA_VERSION = "0.3.0"


# ── request bodies ───────────────────────────────────────────────────────────────────────────


class FilesRequest(BaseModel):
    names: list[str] = Field(default_factory=list, description="files of the folder, in plot order")


class G2Request(FilesRequest):
    q_range: list[float] | None = None
    t_range: list[float] | None = None
    with_fit: bool = True


class G2FitRequest(FilesRequest):
    q_range: list[float] | None = None
    t_range: list[float] | None = None
    fit_func: str = "single"
    bounds: list[list[float]] | None = None
    fit_flag: list[bool] | None = None


class TauqRequest(FilesRequest):
    q_range: list[float] | None = None
    bounds: list[list[float]] | None = None
    fit_flag: list[bool] | None = None
    fit: bool = True


class Saxs1dRequest(FilesRequest):
    q_range: list[float] | None = None
    norm: str = "none"
    sampling: int = 1
    all_phi: bool = False
    background: str | None = None
    bkg_weight: float = 1.0
    absolute: bool = False


class InttRequest(FilesRequest):
    window: int = 1
    sampling: int = 1
    max_points: int = 16000


# ── hosts ────────────────────────────────────────────────────────────────────────────────────


def is_loopback(host: str) -> bool:
    """True for a name or address of this machine's loopback interface."""
    name = str(host).strip().strip("[]").lower()
    if name == "localhost" or name.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(name).is_loopback
    except ValueError:
        return False


def trusted_hosts(ip: str = "127.0.0.1") -> list[str] | None:
    """The Host headers the server answers to when bound to ``ip``: the loopback names and ``ip``
    itself, so a page that rebinds its own name to this machine (DNS rebinding) is refused. None
    (any host) when bound to every interface: it was opened to the network on purpose."""
    if ip in ("0.0.0.0", "::", ""):
        return None
    hosts = list(LOOPBACK_HOSTS)
    if not is_loopback(ip):
        hosts.append(f"[{ip}]" if ":" in ip else ip)
    return hosts


# ── the application ──────────────────────────────────────────────────────────────────────────


def plotly_js_path() -> Path | None:
    """plotly.min.js as the ``plotly`` package ships it (None when the package is missing)."""
    try:
        path = resources.files("plotly") / "package_data" / "plotly.min.js"
    except ModuleNotFoundError:
        return None
    return Path(str(path)) if path.is_file() else None


def build_app(
    root: str,
    *,
    label_style: str | None = None,
    cache_size: int = 8,
    host: str = "127.0.0.1",
    workspace: Workspace | None = None,
) -> FastAPI:
    """The application for the result files under ``root``.

    Args:
        root: The folder to browse.
        label_style: Short-label style for the files (the CLI's ``--label-style``).
        cache_size: Open files kept in memory.
        host: The address the server binds to; it decides the Host headers accepted
            (:func:`trusted_hosts`).
        workspace: A ready workspace instead of one built from ``root`` (tests).
    """
    service = workspace or Workspace(root, label_style=label_style, cache_size=cache_size)
    app = FastAPI(
        title="pyXPCSViewer web",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    hosts = trusted_hosts(host)
    if hosts is not None:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    app.state.workspace = service
    plotly_js = plotly_js_path()

    @app.exception_handler(WorkspaceError)
    async def _workspace_error(_request: Any, exc: WorkspaceError) -> JSONResponse:
        status = 404 if str(exc).startswith("no such file") else 400
        return JSONResponse({"detail": str(exc)}, status_code=status)

    @app.exception_handler(Exception)
    async def _unexpected_error(request: Any, exc: Exception) -> JSONResponse:
        """Anything a file can throw at the reader (a missing HDF5 filter, a corrupt dataset) reaches
        the page as a message instead of a bare 500."""
        logger.exception("%s %s failed", request.method, request.url.path)
        return JSONResponse({"detail": f"{type(exc).__name__}: {exc}"}, status_code=500)

    # ── the page ─────────────────────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})

    @app.get("/vendor/plotly.min.js", include_in_schema=False)
    def plotly_bundle() -> Response:
        if plotly_js is None:
            raise HTTPException(503, "the plotly package is not installed: pip install plotly")
        return FileResponse(
            plotly_js, media_type="application/javascript", headers={"Cache-Control": "public, max-age=86400"}
        )

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.middleware("http")
    async def _revalidate_static(request: Any, call_next: Any) -> Any:
        """The page's own files are revalidated on every load (ETag / Last-Modified), so a browser
        never keeps an old stylesheet or script after the viewer is updated."""
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    # ── the folder ───────────────────────────────────────────────────────────────────────
    @app.get("/api/info")
    def info() -> models.Info:
        return {  # type: ignore[return-value]
            "root": service.root,
            "version": __version__,
            "schema_version": API_SCHEMA_VERSION,
            "label_style": service.label_style,
            "colormaps": list(COLORMAPS),
            "defaults": {
                "g2_bounds": {k: [list(v[0]), list(v[1])] for k, v in DEFAULT_G2_BOUNDS.items()},
                "tauq_bounds": [list(DEFAULT_TAUQ_BOUNDS[0]), list(DEFAULT_TAUQ_BOUNDS[1])],
            },
        }

    @app.get("/api/colormaps")
    def colormaps() -> models.Colormaps:
        return colorscales()  # type: ignore[return-value]

    @app.get("/api/files")
    def files(
        pattern: str = "",
        sort: str = Query("name", pattern="^(name|time)$"),
        reverse: bool = False,
        rescan: bool = False,
        limit: int | None = Query(None, ge=1),
    ) -> models.Files:
        rows = service.files(pattern, sort=sort, reverse=reverse, rescan=rescan, limit=limit)
        return {"files": rows, "total": service.count_files(pattern), "version": service.listing_version}

    # ── one file ─────────────────────────────────────────────────────────────────────────
    @app.get("/api/files/{name}/summary")
    def summary(name: str) -> models.Summary:
        return {  # type: ignore[return-value]
            "file": name,
            "label": service.label(name),
            "rows": service.summary(name),
            "geometry": service.geometry(name),
        }

    @app.get("/api/files/{name}/hdf")
    def hdf(name: str) -> models.HdfInfo:
        return {"file": name, "groups": service.hdf_info(name)}

    @app.get("/api/files/{name}/image")
    def image(name: str, kind: str = "saxs", scale: str = "log", max_size: int = Query(1024, ge=0)) -> models.Image:
        return service.image(name, kind=kind, scale=scale, max_size=max_size)

    @app.get("/api/files/{name}/image/meta")
    def image_meta(
        name: str, kind: str = "saxs", scale: str = "log", max_size: int = Query(1024, ge=0)
    ) -> models.ImageMeta:
        """What the binary image route sends for these parameters, without the array."""
        return service.image_array(name, kind=kind, scale=scale, max_size=max_size)[1]  # type: ignore[return-value]

    @app.get(
        "/api/files/{name}/image/data",
        response_class=Response,
        responses=array_responses(
            "the map as float32 rows (uint8 for the mask), downsampled to max_size or, with max_size=0, "
            "at full resolution; x_min … y_max cut it to a region of the detector",
            meta="ImageMeta",
        ),
    )
    def image_data(
        name: str,
        kind: str = "saxs",
        scale: str = "log",
        max_size: int = Query(1024, ge=0),
        x_min: int | None = Query(None, ge=0),
        x_max: int | None = Query(None, ge=1),
        y_min: int | None = Query(None, ge=0),
        y_max: int | None = Query(None, ge=1),
    ) -> Response:
        bounds = (x_min, x_max, y_min, y_max)
        region = None
        if any(b is not None for b in bounds):
            if any(b is None for b in bounds):
                raise HTTPException(400, "a region needs all of x_min, x_max, y_min and y_max")
            region = (x_min, x_max, y_min, y_max)
        z, meta = service.image_array(name, kind=kind, scale=scale, max_size=max_size, region=region)
        return array_response(z, meta=meta)

    @app.get("/api/files/{name}/pixel")
    def pixel(name: str, x: float, y: float) -> models.Pixel:
        return service.pixel(name, x, y)

    @app.get("/api/files/{name}/stability")
    def stability(name: str, norm: str = "none") -> models.Stability:
        return service.stability(name, norm=norm)

    @app.get("/api/files/{name}/g2_stability")
    def g2_stability(
        name: str,
        q_min: float | None = None,
        q_max: float | None = None,
        t_min: float | None = None,
        t_max: float | None = None,
    ) -> models.G2Stability:
        q_range = [q_min, q_max] if q_min is not None and q_max is not None else None
        t_range = [t_min, t_max] if t_min is not None and t_max is not None else None
        return service.g2_stability(name, q_range=q_range, t_range=t_range)

    @app.get("/api/files/{name}/g2/meta")
    def g2_meta(
        name: str,
        q_min: float | None = None,
        q_max: float | None = None,
        t_min: float | None = None,
        t_max: float | None = None,
    ) -> models.G2Meta:
        """The q values, labels and delays of the binary g2 route, without the array."""
        q_range = [q_min, q_max] if q_min is not None and q_max is not None else None
        t_range = [t_min, t_max] if t_min is not None and t_max is not None else None
        return service.g2_array(name, q_range=q_range, t_range=t_range)[1]  # type: ignore[return-value]

    @app.get(
        "/api/files/{name}/g2/data",
        response_class=Response,
        responses=array_responses("the g2 and its error as float32, shape (2, delays, q-bins)", meta="G2Meta"),
    )
    def g2_data(
        name: str,
        q_min: float | None = None,
        q_max: float | None = None,
        t_min: float | None = None,
        t_max: float | None = None,
    ) -> Response:
        q_range = [q_min, q_max] if q_min is not None and q_max is not None else None
        t_range = [t_min, t_max] if t_min is not None and t_max is not None else None
        data, meta = service.g2_array(name, q_range=q_range, t_range=t_range)
        return array_response(data, meta=meta)

    @app.get("/api/files/{name}/twotime/bins")
    def twotime_bins(name: str) -> models.TwotimeBins:
        return service.twotime_bins(name)

    @app.get("/api/files/{name}/twotime/bin_at")
    def twotime_bin_at(name: str, x: float, y: float) -> models.TwotimeBinAt:
        return service.twotime_bin_at(name, x, y)

    @app.get("/api/files/{name}/twotime/c2")
    def twotime_c2(
        name: str,
        selection: int = 0,
        correct_diag: bool = True,
        max_size: int = Query(512, ge=16),
        include_c2: bool = Query(True, description="false: leave the map out, the binary route has it"),
    ) -> models.TwotimeC2:
        return service.twotime_c2(
            name, selection=selection, correct_diag=correct_diag, max_size=max_size, include_c2=include_c2
        )

    @app.get("/api/files/{name}/twotime/c2/meta")
    def twotime_c2_meta(
        name: str, selection: int = 0, correct_diag: bool = True, max_size: int = Query(512, ge=16)
    ) -> models.C2Meta:
        """What the binary two-time route sends for these parameters, without the array."""
        return service.twotime_c2_array(name, selection=selection, correct_diag=correct_diag, max_size=max_size)[1]  # type: ignore[return-value]

    @app.get(
        "/api/files/{name}/twotime/c2/data",
        response_class=Response,
        responses=array_responses("the two-time correlation map of one q-bin as float32", meta="C2Meta"),
    )
    def twotime_c2_data(
        name: str, selection: int = 0, correct_diag: bool = True, max_size: int = Query(512, ge=16)
    ) -> Response:
        c2, meta = service.twotime_c2_array(name, selection=selection, correct_diag=correct_diag, max_size=max_size)
        return array_response(c2, meta=meta)

    # ── several files ────────────────────────────────────────────────────────────────────
    @app.post("/api/g2")
    def g2(body: G2Request) -> models.G2:
        return service.g2(body.names, body.q_range, body.t_range, with_fit=body.with_fit)

    @app.post("/api/g2/fit")
    def g2_fit(body: G2FitRequest) -> models.G2:
        return service.fit_g2(
            body.names, body.q_range, body.t_range, fit_func=body.fit_func, bounds=body.bounds, fit_flag=body.fit_flag
        )

    @app.post("/api/tauq")
    def tauq(body: TauqRequest) -> models.Tauq:
        return service.tauq(body.names, body.q_range, bounds=body.bounds, fit_flag=body.fit_flag, fit=body.fit)

    @app.post("/api/saxs1d")
    def saxs1d(body: Saxs1dRequest) -> models.Saxs1d:
        return service.saxs1d(
            body.names,
            q_range=body.q_range,
            norm=body.norm,
            sampling=body.sampling,
            all_phi=body.all_phi,
            background=body.background,
            bkg_weight=body.bkg_weight,
            absolute=body.absolute,
        )

    @app.post("/api/intt")
    def intt(body: InttRequest) -> models.Intt:
        return service.intt(body.names, window=body.window, sampling=body.sampling, max_points=body.max_points)

    return app
