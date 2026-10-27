# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Synthetic result files: the datasets of a real multi-tau and two-time result, filled with a
made-up scattering pattern and correlations, for tests, demos and continuous integration.

``pyxpcsviewer-synthetic FOLDER`` writes a small set; :func:`write_synthetic_result` writes one
file. The files read back through :class:`~pyxpcsviewer.core.xpcs_file.XpcsFile` and every web
route like a beamline result, only smaller.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
from pathlib import Path

import h5py
import numpy as np

from .aps_8idi import key as hdf_key

KEYS = hdf_key["nexus"]


def _pattern(shape: tuple[int, int], center: tuple[float, float], rng: np.random.Generator) -> np.ndarray:
    """A SAXS-like intensity: a power-law decay from the beam center with a ring, a beam stop and noise."""
    rows, cols = shape
    y = np.arange(rows)[:, None] - center[1]
    x = np.arange(cols)[None, :] - center[0]
    r = np.hypot(x, y) + 1e-3
    intensity = 2.0e4 / (1 + (r / 12.0) ** 3.2) + 25.0 * np.exp(-((r - 0.42 * min(shape)) ** 2) / (2 * 9.0**2)) + 0.4
    intensity *= 1 + 0.04 * rng.standard_normal(shape)
    intensity[r < 6] = 0.0
    return intensity.astype(np.float32)


def _g2_curves(t_el: np.ndarray, q: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Stretched exponentials whose relaxation time falls with q: g2 (delays × bins) and its error."""
    tau_q = 0.08 * (q[0] / q)
    g2 = 1.0 + 0.25 * np.exp(-2.0 * (t_el[:, None] / tau_q[None, :]) ** 0.9)
    err = 0.004 + 0.002 * (t_el[:, None] / t_el[-1])
    g2 = g2 + rng.standard_normal(g2.shape) * err * 0.5
    return g2.astype(np.float64), np.broadcast_to(err, g2.shape).astype(np.float64)


def _c2_half(frames: int, tau_frames: float, rng: np.random.Generator) -> np.ndarray:
    """The upper triangle (with the diagonal) of a two-time correlation that decays with |t1 - t2|."""
    i = np.arange(frames)
    lag = np.abs(i[:, None] - i[None, :])
    c2 = 1.0 + 0.25 * np.exp(-2.0 * (lag / tau_frames) ** 0.9) + 0.01 * rng.standard_normal((frames, frames))
    c2 = np.triu(c2)
    return c2.astype(np.float32)


def write_synthetic_result(
    path: str | os.PathLike[str],
    *,
    multitau: bool = True,
    twotime: bool = True,
    shape: tuple[int, int] = (256, 240),
    frames: int = 400,
    nq: int = 8,
    nphi: int = 1,
    segments: int = 4,
    twotime_bins: int = 3,
    frame_time: float = 0.01,
    seed: int = 0,
) -> Path:
    """Write one synthetic result file.

    Args:
        path: Where to write (``.hdf``).
        multitau: Store a multi-tau analysis (g2, partial g2, delays).
        twotime: Store a two-time analysis (C2 maps of the first ``twotime_bins`` q-bins).
        shape: Detector rows, columns.
        frames: Frames of the acquisition (the C2 maps are ``frames`` square).
        nq: Dynamic q-bins (rings around the beam center).
        nphi: Static φ slices per q-bin.
        segments: Time segments of the partial g2 and the stability curves.
        twotime_bins: How many of the q-bins carry a C2 map.
        frame_time: Seconds per frame.
        seed: Of the noise.
    """
    rng = np.random.default_rng(seed)
    rows, cols = shape
    center = (cols * 0.47, rows * 0.52)
    saxs_2d = _pattern(shape, center, rng)

    # ── the q-map: concentric rings as dynamic bins, the same rings cut in φ as static bins ──
    pixel_size = 75e-6
    det_dist = 8.0
    energy = 12.0
    k0 = 2 * np.pi / (12.398 / energy)
    y = np.arange(rows)[:, None] - center[1]
    x = np.arange(cols)[None, :] - center[0]
    r = np.hypot(x, y)
    np.sin(np.arctan(r * pixel_size / det_dist)) * k0
    phi = np.rad2deg(np.arctan2(y, x) * -1)
    r_min, r_max = 10.0, 0.45 * min(shape)
    edges = np.linspace(r_min, r_max, nq + 1)
    dqmap = np.zeros(shape, dtype=np.int32)
    for n in range(nq):
        dqmap[(r >= edges[n]) & (r < edges[n + 1])] = n + 1
    phi_edges = np.linspace(-180, 180, nphi + 1)
    phi_index = np.clip(np.digitize(phi, phi_edges) - 1, 0, nphi - 1)
    sqmap = np.where(dqmap > 0, (dqmap - 1) * nphi + phi_index + 1, 0).astype(np.int32)
    mask = np.ones(shape, dtype=np.int32)
    mask[r < 6] = 0
    mask[:, cols // 2 - 1 : cols // 2 + 1] = 0  # a module gap
    dqmap[mask == 0] = 0
    sqmap[mask == 0] = 0
    ring_r = 0.5 * (edges[:-1] + edges[1:])
    dqlist = np.sin(np.arctan(ring_r * pixel_size / det_dist)) * k0
    sqlist = dqlist.copy()
    dplist = np.array([0.0])
    splist = 0.5 * (phi_edges[:-1] + phi_edges[1:]) if nphi > 1 else np.array([0.0])
    dynamic_index_mapping = np.arange(nq)
    static_index_mapping = np.arange(nq * nphi)

    # ── 1-D: one value per static bin, the stability per segment ──
    counts = np.bincount(sqmap.ravel(), weights=saxs_2d.ravel().astype(np.float64), minlength=nq * nphi + 1)[1:]
    pixels = np.bincount(sqmap.ravel(), minlength=nq * nphi + 1)[1:]
    saxs_1d = (counts / np.maximum(pixels, 1)).astype(np.float64)
    drift = 1 + 0.03 * np.linspace(-1, 1, segments)
    iqp = (saxs_1d[None, :] * drift[:, None] * (1 + 0.01 * rng.standard_normal((segments, nq * nphi)))).astype(
        np.float64
    )

    # ── the intensity trace ──
    frame_index = np.arange(frames, dtype=np.float64)
    trace = float(saxs_2d[mask == 1].mean()) * (
        1 + 0.02 * rng.standard_normal(frames) + 0.01 * np.sin(frame_index / 25.0)
    )
    int_t = np.stack([frame_index, trace]).astype(np.float64)

    # ── multi-tau ──
    delays = np.unique(
        np.concatenate([np.arange(1, 8), np.round(np.logspace(np.log10(8), np.log10(frames // 2), 24))])
    ).astype(np.int64)
    t_el = delays * frame_time
    g2, g2_err = _g2_curves(t_el, dqlist, rng)
    g2_partial = np.stack([g2 * (1 + 0.004 * k * rng.standard_normal(g2.shape)) for k in range(segments)])
    g2_partial_err = np.broadcast_to(g2_err, g2_partial.shape).copy()

    # ── two-time ──
    tau_frames = 0.08 / frame_time * (dqlist[0] / dqlist[:twotime_bins])

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(target, "w") as f:

        def put(key: str, value: object, units: str | None = None) -> None:
            dataset = f.create_dataset(KEYS.get(key, key), data=value)
            if units:
                dataset.attrs["units"] = units

        put("mask", mask)
        # the q-map manager caches q-maps by this attribute: files of one geometry share one q-map
        f["/xpcs/qmap"].attrs["hash"] = f"synthetic-qmap-{rows}x{cols}-{nq}-{nphi}"
        put("dqmap", dqmap)
        put("sqmap", sqmap)
        put("dqlist", dqlist)
        put("sqlist", sqlist)
        put("dplist", dplist)
        put("splist", splist)
        put("bcx", float(center[0]))
        put("bcy", float(center[1]))
        put("det_dist", det_dist, "m")
        put("pixel_size", pixel_size, "m")
        put("static_index_mapping", static_index_mapping)
        put("dynamic_index_mapping", dynamic_index_mapping)
        put("static_num_pts", np.array([nq, nphi]))
        put("dynamic_num_pts", np.array([nq, 1]))
        put("map_names", np.array([b"q", b"phi"]))
        put("map_units", np.array(["Å⁻¹".encode(), b"deg"]))
        put("start_time", str(_dt.datetime(2026, 1, 1, 12, 0, 0)).encode())
        put("saxs_2d", saxs_2d)
        put("saxs_1d", saxs_1d)
        put("Iqp", iqp)
        put("Int_t", int_t)
        put("t0", frame_time, "s")
        put("t1", frame_time * 0.9, "s")
        put("X_energy", energy, "keV")
        put("pix_dim_x", pixel_size, "m")
        put("pix_dim_y", pixel_size, "m")
        f.create_dataset("/entry/instrument/detector_1/description", data=b"synthetic detector")
        f.create_dataset("/entry/instrument/detector_1/x_pixels", data=cols)
        f.create_dataset("/entry/instrument/detector_1/y_pixels", data=rows)
        f.create_dataset("/entry/sample/name", data=b"synthetic sample")
        f.create_dataset("/entry/sample/temperature", data=295.0).attrs["units"] = "K"
        f.create_dataset("/entry/user/name", data=b"pyxpcsviewer-synthetic")
        if multitau:
            put("tau", delays)
            put("g2", g2)
            put("g2_err", g2_err)
            put("g2_partial", g2_partial)
            put("g2_partial_err", g2_partial_err)
            put("g2_partial_labels", np.array([f"{k + 1}".encode() for k in range(segments)]))
            put("stride_frame", 1)
            put("avg_frame", 1)
            f.create_dataset("/xpcs/multitau/config/analysis_type", data=b"Multitau")
        if twotime:
            prefix = KEYS["c2_prefix"]
            for n in range(twotime_bins):
                f.create_dataset(f"{prefix}/C2T_all_{n + 1:04d}", data=_c2_half(frames, float(tau_frames[n]), rng))
            put("c2_processed_bins", np.arange(1, twotime_bins + 1))
            lag = np.arange(frames, dtype=np.float64)
            c2_g2 = 1.0 + 0.25 * np.exp(-2.0 * (lag[:, None] / tau_frames[None, :]) ** 0.9)
            c2_g2[0] = 1.0
            put("c2_g2", c2_g2.astype(np.float64))
            seg_len = frames // segments
            seg_lag = np.arange(seg_len, dtype=np.float64)
            c2_g2_segments = 1.0 + 0.25 * np.exp(-2.0 * (seg_lag[:, None, None] / tau_frames[None, None, :]) ** 0.9)
            c2_g2_segments = c2_g2_segments * (1 + 0.005 * rng.standard_normal((seg_len, segments, twotime_bins)))
            put("c2_g2_segments", c2_g2_segments.astype(np.float64))
            put("c2_delay", lag * frame_time)
            put("c2_stride_frame", 1)
            put("c2_avg_frame", 1)
            f.create_dataset("/xpcs/twotime/config/analysis_type", data=b"Twotime")
    return target


def write_synthetic_folder(folder: str | os.PathLike[str], *, seed: int = 0) -> list[Path]:
    """A small folder of synthetic results: a multi-tau file, a two-time file and one with both."""
    base = Path(folder)
    return [
        write_synthetic_result(base / "S0001_synthetic_a0001_f000400_r00001_multitau.hdf", twotime=False, seed=seed),
        write_synthetic_result(
            base / "S0002_synthetic_a0002_f000400_r00001_twotime.hdf", multitau=False, seed=seed + 1
        ),
        write_synthetic_result(base / "S0003_synthetic_a0003_f000400_r00001_both.hdf", seed=seed + 2),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pyxpcsviewer-synthetic", description="write synthetic XPCS result files for tests and demos"
    )
    parser.add_argument("folder", help="where to write the files (created when missing)")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    for path in write_synthetic_folder(args.folder, seed=args.seed):
        print(path, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
