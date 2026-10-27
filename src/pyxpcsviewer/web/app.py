# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""The web viewer's HTTP side: a JSON API over :class:`~pyxpcsviewer.web.workspace.Workspace`
and the static page that calls it.

``build_app(root)`` returns the FastAPI application; ``pyxpcsviewer-web`` serves it with uvicorn.
Routes are thin: they parse parameters, call the workspace and turn its errors into 4xx answers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from beamline_webkit import (
    AppInfo,
    JobManager,
    JobState,
    Session,
    SessionStore,
    array_response,
    array_responses,
    create_app,
)
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pyxpcsviewer import __version__

from . import models
from .colormaps import COLORMAPS, colorscales
from .workspace import DEFAULT_G2_BOUNDS, DEFAULT_TAUQ_BOUNDS, Workspace, WorkspaceError

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
# The version of the API as the committed openapi.json (``pyxpcsviewer-web --export-openapi``) describes
# it: bump the minor for an addition, the major for a change a frontend built against the old document
# would not survive. The package version is separate: it changes with every release.
API_SCHEMA_VERSION = "0.4.0"


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


# ── the application ──────────────────────────────────────────────────────────────────────────


NOT_BUILT = (
    "<!doctype html><html lang=en><head><meta charset=utf-8><title>pyXPCSViewer web</title>"
    "<style>body{font:14px system-ui,sans-serif;max-width:40rem;margin:4rem auto;color:#1f1f1d;line-height:1.5}"
    "code{background:#efeeea;padding:0 .3em}</style></head><body><h1>pyXPCSViewer web</h1>"
    "<p>The API is up (<a href=api/docs>api/docs</a>), but this install carries no frontend. Release wheels do; "
    "from a checkout, build the app in the <code>beamline-web</code> repository "
    "(<code>pnpm --filter @beamline-web/app-xpcs build</code>) and copy its <code>dist/</code> into "
    "<code>src/pyxpcsviewer/web/static/</code>, or run its dev server, which proxies <code>/api</code> to this "
    "service.</p></body></html>"
)


def frontend_dir() -> Path | None:
    """The built app's folder when this install carries one (release wheels do), else None."""
    return STATIC_DIR if (STATIC_DIR / "index.html").is_file() else None


def build_app(
    root: str,
    *,
    label_style: str | None = None,
    cache_size: int = 8,
    host: str = "127.0.0.1",
    workspace: Workspace | None = None,
    session_ttl: float = 3600.0,
) -> FastAPI:
    """The application for the result files under ``root``.

    Built on :func:`beamline_webkit.create_app`: the health route, the one error shape and the
    trusted-host guard come from there. Fits run as jobs and live in the page's session.

    Args:
        root: The folder to browse.
        label_style: Short-label style for the files (the CLI's ``--label-style``).
        cache_size: Open files kept in memory.
        host: The address the server binds to; it decides the Host headers accepted
            (:func:`beamline_webkit.trusted_hosts`).
        workspace: A ready workspace instead of one built from ``root`` (tests).
        session_ttl: Seconds a page's fits are kept after its last request.
    """
    service = workspace or Workspace(root, label_style=label_style, cache_size=cache_size)
    sessions = SessionStore(ttl=session_ttl)
    jobs = JobManager(workers=2)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> Any:
        service.warm_fit_pool()
        yield
        jobs.shutdown()
        service.close()

    app = create_app(
        AppInfo(name="xpcs-viewer", title="pyXPCSViewer web", version=__version__, schema_version=API_SCHEMA_VERSION),
        host=host,
        lifespan=lifespan,
    )
    app.state.workspace = service
    app.state.sessions = sessions
    app.state.jobs = jobs
    app.include_router(jobs.router())
    current_session = sessions.dependency()

    @app.exception_handler(WorkspaceError)
    async def _workspace_error(_request: Any, exc: WorkspaceError) -> JSONResponse:
        status = 404 if str(exc).startswith("no such file") else 400
        return JSONResponse({"detail": str(exc)}, status_code=status)

    # ── the page ─────────────────────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    def index() -> Response:
        built = frontend_dir()
        if built is None:
            return HTMLResponse(NOT_BUILT, headers={"Cache-Control": "no-cache"})
        return FileResponse(built / "index.html", headers={"Cache-Control": "no-cache"})

    built = frontend_dir()
    if built is not None and (built / "assets").is_dir():
        # the bundle's hashed files, cacheable for good; index.html above is revalidated on every load
        app.mount("/assets", StaticFiles(directory=str(built / "assets")), name="assets")

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
    def fits_of(session: Session) -> dict[str, dict[str, Any]]:
        store: dict[str, dict[str, Any]] = session.setdefault("fits", dict)
        return store

    @app.post("/api/g2")
    def g2(body: G2Request, session: Session = Depends(current_session)) -> models.G2:  # noqa: B008
        return service.g2(body.names, body.q_range, body.t_range, with_fit=body.with_fit, fits=fits_of(session))

    @app.post("/api/g2/fit", summary="Fit the g2 of the files now, and answer with the result")
    def g2_fit(body: G2FitRequest, session: Session = Depends(current_session)) -> models.G2:  # noqa: B008
        return service.fit_g2(
            body.names,
            body.q_range,
            body.t_range,
            fit_func=body.fit_func,
            bounds=body.bounds,
            fit_flag=body.fit_flag,
            fits=fits_of(session),
        )

    @app.post("/api/jobs/g2-fit", status_code=202, summary="Fit the g2 of the files as a job")
    def g2_fit_job(body: G2FitRequest, session: Session = Depends(current_session)) -> JobState:  # noqa: B008
        """Starts the fit and answers with the job; follow it at /api/jobs/{id}/events, then
        fetch the fits with /api/g2 or /api/files/{name}/g2/fit. The result names the files
        fitted and those skipped."""
        # validated here, so a bad request is a 400 instead of a failed job
        service.fit_g2(
            [], body.q_range, body.t_range, fit_func=body.fit_func, bounds=body.bounds, fit_flag=body.fit_flag
        )
        store = fits_of(session)

        def run(progress: Any) -> dict[str, Any]:
            answer = service.fit_g2(
                body.names,
                body.q_range,
                body.t_range,
                fit_func=body.fit_func,
                bounds=body.bounds,
                fit_flag=body.fit_flag,
                fits=store,
                progress=progress,
            )
            return {
                "fitted": [f["file"] for f in answer["files"] if f["fit"] is not None],
                "failed": [f["file"] for f in answer["files"] if f["fit"] is None],
                "skipped": answer["skipped"],
            }

        return jobs.submit(run, name="g2 fit", session=session.id).state()

    @app.get("/api/files/{name}/g2/fit", summary="The page's fit of the file, matched to the g2 route's q values")
    def g2_fit_of_file(
        name: str,
        session: Session = Depends(current_session),  # noqa: B008
        q_min: float | None = None,
        q_max: float | None = None,
        t_min: float | None = None,
        t_max: float | None = None,
    ) -> models.G2Fit | None:
        q_range = [q_min, q_max] if q_min is not None and q_max is not None else None
        t_range = [t_min, t_max] if t_min is not None and t_max is not None else None
        return service.fit_payload(name, q_range, t_range, fits=fits_of(session))

    @app.post("/api/tauq")
    def tauq(body: TauqRequest, session: Session = Depends(current_session)) -> models.Tauq:  # noqa: B008
        return service.tauq(
            body.names, body.q_range, bounds=body.bounds, fit_flag=body.fit_flag, fit=body.fit, fits=fits_of(session)
        )

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
