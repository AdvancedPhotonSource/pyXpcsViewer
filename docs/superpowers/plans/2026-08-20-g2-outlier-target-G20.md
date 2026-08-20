# G2 Outlier Target: support `G20` alongside `g2-per-pixel`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the G2→g2 outlier rejection run its statistic on the *unnormalized* correlation numerator `G20 = G2[:, 0]` instead of the normalized per-pixel g2, selected by a new `target` argument with values `["g2-per-pixel", "G20"]`, defaulting to `"G20"`.

**Requirement mapping** (from the request):

| # | Requirement | Where it lands |
|---|---|---|
| 1 | `G20` is `G2[:, 0]` | `compute_g2` / `compute_g2_debug_bundle` select `G2[:, 0]` after the `(n_delays, n_channels, -1)` reshape — a **view**, no copy |
| 2 | Dead pixels also applied | Already automatic: `dead` zeroes `sqmap_1d`, and `find_g2_pixel_outliers` only iterates bins `1..n_sq`. Task 1 adds an explicit regression test |
| 3 | Same logic, upper bound only | Unchanged — `find_g2_pixel_outliers` is already target-agnostic (`hi = center + threshold*spread`, strict `>`, no low bound) |
| 4 | Per sq bin | Unchanged — the detector already loops sq bins. Task 1 adds a test that proves per-bin scaling matters for `G20` |
| 5 | `target` arg, default `"G20"` | New module constants `OUTLIER_TARGETS` / `DEFAULT_OUTLIER_TARGET`, threaded through `compute_g2` → `regroup_G2_with_qmap_array` → `regroup_G2` → `XpcsFile.regroup_G2` (already `**kwargs`) → GUI |

**Key finding — the core change is small.** `find_g2_pixel_outliers(sqmap, g2_pixel, ...)` never assumes its value array is normalized: it excludes exact zeros as "photon-starved", computes median/MAD (or mean/std) per `(sq bin, delay)`, and applies a strict upper bound. So supporting `G20` means **choosing which array to hand it**, not branching inside it. Two facts make the swap clean:

- `g2_pixel == 0 ⟺ IP == 0 ⟺ G20 == 0` (the `normalize_g2` denominator is clamped to be non-zero), so the "photon-starved" exclusion selects the *same pixel set* under either target — no semantic change to that rule.
- `G2[:, 0]` after the reshape is `(n_delays, n_pixels)`, exactly the shape the detector wants.

**Naming note.** Channel 0 already has two names in this codebase: `normalize_g2`'s docstring calls the channels `(IP, IF, IF)` (so channel 0 = IP), while `XpcsFile.get_G2_data`'s `channel_index = {"G2": 0, "IP": 1, "IF": 2}` calls channel 0 `"G2"`. `"G20"` is unambiguous and collides with neither. It is **not** the same `target` as `plot_G2_regroup`'s display combo (`comboBox_G2_target`: `g2_per_pixel`/`G2`/`IP`/`IF`) — different code path (display vs. regroup), no runtime collision, but keep the distinction clear in docstrings.

**Tech Stack:** Python 3.10+, PySide6, pyqtgraph 0.14.0, numpy, h5py, pytest.

---

## Decisions & caveats

1. **The default flips.** Today's behaviour is `g2-per-pixel`; after this change every un-parameterized call (GUI ReGroup, debug dialog, `XpcsFile.regroup_G2`) rejects on `G20`. Different pixels will be flagged and saved `g2`/`g2_err` will change for existing workflows. This is what was asked for, but it is a user-visible behaviour change and Task 1 pins it with an explicit test.

2. **`G20` detection is intensity-driven, `g2-per-pixel` is correlation-driven.** `G20 ≈ I²·g2`, so within a q-ring `G20` outliers are dominated by *bright* pixels (hot pixels, streaks) while `g2-per-pixel` outliers are anomalously *correlated* pixels. This is exactly why per-sq-bin statistics matter more for `G20` (a q-ring is roughly iso-intensity; the detector as a whole is not). Both are legitimate; they are not interchangeable.

3. **Bundle key rename (`g2_pixel` → `values`).** `compute_g2_debug_bundle` returns the array the dialog histograms. Under `target="G20"` that array is `G20`, so keeping the key named `g2_pixel` would make the dialog lie about what it plots. Rename to `values` and add a `target` key. Only 6 call sites exist (`g2_utils.py:444`, `g2_debug_dialog.py:201`, `test_g2_utils.py:50,51,75,81`), and the function is 1 day old, so this is cheap now and expensive later. Keeping *both* arrays is rejected: on a 1 Mpixel detector with 60 delays each is ~240 MB.

4. **`normalize_g2` is skipped entirely in the debug bundle when `target="G20"`** — nothing else in the bundle needs it. Saves a full `(n_delays, n_pixels)` allocation plus the divide. `compute_g2` still computes it unconditionally because `error_model="per-pixel"` needs it downstream.

5. **Zero-spread clamp is scale-sensitive (Task 2, OPTIONAL).** `find_g2_pixel_outliers` clamps a degenerate `spread == 0` to `1.0`, so `hi = center + threshold`. With g2-scale data (`center ≈ 1`) that is a loose, conservative bound. With `G20`-scale data the absolute `1.0` is arbitrary: if a bin's raw magnitudes are large *and* a majority of pixels share an exact value, `hi` becomes near-degenerate and can mass-flag everything above the median. Exact ties among >50% of float32 `G20` pixels are unlikely, so this is a latent wart rather than a live bug — Task 2 fixes it properly and is separable. **Before deciding, run the empirical check in Task 2, Step 0 on a real file** (`tests/data` is not present on this machine, so this could not be measured while writing the plan).

6. **Scope.** Tasks 1 and 3 are the literal request (core API + debug bundle). Tasks 4–5 (dialog plumbing + a UI combo) are what makes the argument reachable by a user — without them the new default silently applies everywhere and cannot be inspected or overridden from the GUI. Drop 4–5 if a core-only change is wanted.

---

## Global Constraints

- Test/lint/type-check env: `/local/MQICHU/envs/l2604_xpcs` (has `python`, `mypy`, `ruff`, `pyside6-uic`, `pyside6-rcc`). Run from repo root `/home/beams4/MQICHU/Tools_cloud/xpcs_toolchains/pyXpcsViewer`.
- Test command pattern: `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/<file> -v`
- Lint: `ruff check <files>` and `ruff format <files>` (ruff at `~/.local/bin/ruff`).
- Type check: `/local/MQICHU/envs/l2604_xpcs/bin/mypy <files>` — strict mode repo-wide. **`src/pyxpcsviewer/core/g2_utils.py` has 19 pre-existing mypy errors** (verified 2026-08-20) — do not fix them, but the count must stay 19.
- **Never hand-edit** `src/pyxpcsviewer/gui/view/viewer_ui.py` or `icons_rc.py` — regenerate via `src/pyxpcsviewer/gui/view/convert_ui_to_py.sh` with `PATH=/local/MQICHU/envs/l2604_xpcs/bin:$PATH`.
- Working branch: `mc_dev`. Commit after each task.
- The literal strings are `"G20"` and `"g2-per-pixel"` (hyphenated, matching the `ERROR_MODELS` style — *not* `get_G2_data`'s underscored `"g2_per_pixel"`). GUI combo item text must match byte-for-byte.

---

### Task 1: Core `target` argument on `compute_g2` and the regroup wrappers

*Shipped together with Task 3 in commit `bd5c2f5` — both edit `g2_utils.py`, and the `values` key rename must land atomically with the dialog's read of it to keep the tree green.*

**Files:**
- Modify: `src/pyxpcsviewer/core/g2_utils.py`
- Test: `tests/test_g2_utils.py`

**Interfaces:**
- Produces: `OUTLIER_TARGETS = ("G20", "g2-per-pixel")`, `DEFAULT_OUTLIER_TARGET = "G20"`.
- Produces: `compute_g2(..., target: str = DEFAULT_OUTLIER_TARGET)`, same new kwarg on `regroup_G2_with_qmap_array` and `regroup_G2` (both pass-through). `XpcsFile.regroup_G2` already forwards `**kwargs` — no change needed there.
- Modifies: `find_g2_pixel_outliers`'s second parameter is renamed `g2_pixel` → `values` and its docstring generalized. No call site uses it as a keyword (verified), so this is source-compatible.

- [x] **Step 1: Write the failing tests**

Append to `tests/test_g2_utils.py`. The new fixture is the important part — the existing `make_data()` sets `IF = 1` everywhere, so `G20 == g2_pixel` there and it cannot tell the two targets apart.

```python
def make_target_data():
    """(1 delay, 3 ch, 4x4) G2 where the two outlier targets disagree.

    One sq bin (all pixels), one dq bin. Baseline pixels cycle IP over
    {0.9, 1.0, 1.1} with IF1=IF2=1, so both G20 and g2_pixel have a
    non-degenerate MAD (0.1) -- deliberately not relying on the
    spread==0 -> 1.0 clamp, so these expectations survive Task 2.

      pixel 5  "hot":     IP=10,  IF=sqrt(10) -> G20=10  (outlier), g2=1.0 (not)
      pixel 10 "corr":    IP=1,   IF=0.1      -> G20=1   (not),     g2=100 (outlier)
      pixel 0  "dead":    IP=1e6, IF1=IF2=0   -> excluded from every bin
    """
    ip = np.array([0.9, 1.0, 1.1] * 6, dtype=np.float32)[:16].reshape(4, 4)
    IP = ip[None].copy()
    IF = np.ones((1, 4, 4), dtype=np.float32)
    IP[0, 1, 1] = 10.0
    IF[0, 1, 1] = np.sqrt(10.0)          # pixel 5
    IP[0, 2, 2] = 1.0
    IF[0, 2, 2] = 0.1                    # pixel 10
    IP[0, 0, 0] = 1.0e6
    IF[0, 0, 0] = 0.0                    # pixel 0, dead
    G2 = np.stack([IP, IF, IF], axis=1).astype(np.float32)
    sqmap = np.ones((4, 4), dtype=np.uint16)
    dqmap = np.ones((4, 4), dtype=np.uint16)
    return G2, sqmap, dqmap


def _bad_mask(G2, sqmap, dqmap, **kw):
    """Outlier mask compute_g2 would use, via the debug bundle (same code path)."""
    return compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, **kw)["bad"]


def test_target_G20_flags_the_bright_pixel_not_the_correlated_one():
    G2, sqmap, dqmap = make_target_data()
    bad = _bad_mask(G2, sqmap, dqmap, target="G20")
    assert bad[0, 5]          # G20 = 10 in a bin whose median is ~1
    assert not bad[0, 10]     # G20 = 1, unremarkable


def test_target_g2_per_pixel_flags_the_correlated_pixel_not_the_bright_one():
    G2, sqmap, dqmap = make_target_data()
    bad = _bad_mask(G2, sqmap, dqmap, target="g2-per-pixel")
    assert bad[0, 10]         # g2 = 100
    assert not bad[0, 5]      # g2 = 10/10 = 1.0


def test_default_target_is_G20():
    G2, sqmap, dqmap = make_target_data()
    np.testing.assert_array_equal(
        _bad_mask(G2, sqmap, dqmap), _bad_mask(G2, sqmap, dqmap, target="G20")
    )
    assert DEFAULT_OUTLIER_TARGET == "G20"


def test_compute_g2_target_changes_the_result():
    """g2 itself differs between targets -- the argument is load-bearing, not cosmetic."""
    G2, sqmap, dqmap = make_target_data()
    g2_G20, _ = compute_g2(sqmap, dqmap, G2, outlier_threshold=3.0, target="G20")
    g2_pix, _ = compute_g2(sqmap, dqmap, G2, outlier_threshold=3.0, target="g2-per-pixel")
    assert not np.allclose(g2_G20, g2_pix)


def test_target_G20_excludes_dead_pixels():
    """Pixel 0 has IF1=IF2=0 (dead) and a huge IP; it must never be flagged,
    and it must not inflate the bin statistics."""
    G2, sqmap, dqmap = make_target_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, outlier_threshold=3.0, target="G20")
    assert b["sqmap_1d"][0] == 0
    assert b["dqmap_1d"][0] == 0
    assert b["n_dead"] == 1
    assert not b["bad"][:, 0].any()


def test_target_G20_statistics_are_per_sq_bin():
    """A G20 of 1000 is normal in a bright bin and an outlier in a dim one.
    Global (non-per-bin) statistics would flag both or neither."""
    sqmap_1d = np.array([1] * 8 + [2] * 8, dtype=np.uint16)
    values = np.concatenate([
        np.array([1.0, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0, 1000.0]),      # bin 1: dim, one spike
        np.array([1000.0, 1100.0, 900.0, 1000.0, 1100.0, 900.0, 1000.0, 1000.0]),  # bin 2: bright
    ])[None]
    bad = find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0)
    assert bad[0, 7]                 # 1000 among ~1s
    assert not bad[0, 8:].any()      # the same magnitude is normal in bin 2


def test_outlier_rejection_has_no_lower_bound():
    """Only `> center + threshold*spread` rejects; small values never do."""
    sqmap_1d = np.ones(8, dtype=np.uint16)
    values = np.array([[1.0, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0, 1e-6]])
    assert not find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0).any()


def test_compute_g2_rejects_unknown_target():
    G2, sqmap, dqmap = make_data()
    with pytest.raises(ValueError, match="target"):
        compute_g2(sqmap, dqmap, G2, target="G2")
```

Extend the existing import block with `DEFAULT_OUTLIER_TARGET` and `OUTLIER_TARGETS`.

**Fixture verified 2026-08-20** against the current implementation: under `G20` only pixel 5 is flagged, under `g2-per-pixel` only pixel 10; the per-sq-bin case flags only index 7; the low-value case flags nothing; and the resulting `g2` is `1.1340` (G20) vs `1.2273` (g2-per-pixel), so `test_compute_g2_target_changes_the_result` has real margin.

- [x] **Step 2: Run tests to verify they fail**

`/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_utils.py -v`
Expected: the new tests fail on `ImportError` / unexpected `target` kwarg; **all pre-existing tests still pass** (they use `make_data()` where `IF == 1`, so `G20 == g2_pixel` and the default flip is invisible to them — if any pre-existing test fails here, stop and re-read).

- [x] **Step 3: Write the implementation**

In `src/pyxpcsviewer/core/g2_utils.py`, after `DEFAULT_ERROR_MODEL`:

```python
#: Accepted values for the ``target`` argument -- which per-pixel quantity the
#: outlier statistic is computed on.
#:
#: ``"G20"``: the unnormalized correlation numerator ``G2[:, 0]``.  Outliers are
#: pixels whose *raw* correlation is anomalous for their sq bin, which in
#: practice means bright/hot pixels (``G20 ~ I**2 * g2``).
#: ``"g2-per-pixel"``: the normalized per-pixel g2 (``normalize_g2``).  Outliers
#: are pixels whose *correlation* is anomalous independent of their brightness.
OUTLIER_TARGETS = ("G20", "g2-per-pixel")

#: Default outlier target.
DEFAULT_OUTLIER_TARGET = "G20"
```

Rename `find_g2_pixel_outliers`'s second parameter `g2_pixel` → `values` (and the local `g2_roi`/`g2_roi_nan` may stay); update its docstring to say "per-pixel statistic (``G20`` or normalized g2), shape ``(n_delays, n_pixels)``" and to note that exact zeros are treated as photon-starved under either target because `g2_pixel == 0 ⟺ G20 == 0`.

In `compute_g2`, add `target: str = DEFAULT_OUTLIER_TARGET` as the last parameter, validate next to the `error_model` check:

```python
    if target not in OUTLIER_TARGETS:
        raise ValueError(f"target must be one of {OUTLIER_TARGETS}, got {target!r}")
```

and select the array at the rejection site:

```python
    bad = None
    if outlier_threshold >= 0:
        # G2 is already (n_delays, n_channels, n_pixels) here, so G2[:, 0] is a
        # strided view of the numerator -- no copy of a multi-hundred-MB cube.
        values = G2[:, 0] if target == "G20" else g2_pixel
        bad = find_g2_pixel_outliers(
            sqmap_1d, values, threshold=outlier_threshold, method=outlier_method, combine_outlier=combine_outlier
        )
```

Document in the `compute_g2` docstring that `target` selects only *which pixels are rejected*; the reported `g2` is always the normalized sq-bin average and `g2_err` under `error_model="per-pixel"` is still computed from the unfiltered `g2_pixel` (pre-existing behaviour, unchanged by this task).

Add the same `target` parameter + docstring entry to `regroup_G2_with_qmap_array` and `regroup_G2` and forward it.

- [x] **Step 4: Run tests to verify they pass**

`/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_utils.py -v`

- [x] **Step 5: Lint + type check**

```bash
ruff format src/pyxpcsviewer/core/g2_utils.py tests/test_g2_utils.py
ruff check src/pyxpcsviewer/core/g2_utils.py tests/test_g2_utils.py
/local/MQICHU/envs/l2604_xpcs/bin/mypy src/pyxpcsviewer/core/g2_utils.py   # must still be exactly 19 errors
```

- [x] **Step 6: Commit**

```bash
git add src/pyxpcsviewer/core/g2_utils.py tests/test_g2_utils.py
git commit -m "Add outlier target argument to compute_g2, defaulting to G20

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2 (OPTIONAL): scale-safe fallback for degenerate `spread == 0` bins

**NOT DONE (2026-08-20)** — Step 0 needs a real result file and `tests/data` is absent on this machine, so the deciding measurement could not be taken. Everything else in this plan shipped without it; the `g2-per-pixel` path is unaffected either way. Revisit if the `G20` bad-pixel map looks uniform across a ring rather than concentrated on bright pixels.

Skip this task entirely if Step 0 shows the situation does not arise. See caveat 5 above.

**Files:**
- Modify: `src/pyxpcsviewer/core/g2_utils.py`
- Test: `tests/test_g2_utils.py`

- [ ] **Step 0: Measure before deciding**

On a machine with `tests/data` present (or any real result file with `/xpcs/multitau/unnormalized_G2`), report per sq bin, for the `G20` target: the median magnitude, the MAD, and the fraction of `(sq bin, delay)` pairs whose MAD is exactly 0 among nonzero pixels. If that fraction is ~0, close this task as unnecessary and record the number in the plan. If it is non-negligible, continue.

- [ ] **Step 1: Write the failing test**

```python
def test_zero_spread_bin_rejects_nothing():
    """A bin with no measurable spread carries no information about what is
    anomalous, so nothing in it may be rejected -- regardless of magnitude."""
    sqmap_1d = np.ones(8, dtype=np.uint16)
    values = np.array([[1000.0] * 5 + [1001.0, 1002.0, 1500.0]])
    bad = find_g2_pixel_outliers(sqmap_1d, values, threshold=3.0, zero_spread_fallback=None)
    assert not bad.any()
```

- [ ] **Step 2/3: Implement**

Add `zero_spread_fallback: float | None = 1.0` to `find_g2_pixel_outliers`. `1.0` keeps today's behaviour (and keeps `test_bundle_known_outliers`, which depends on `hi = 1 + 3*1`, green). `None` means "no rejection in that bin" — set `hi = inf` where `spread == 0`:

```python
        if zero_spread_fallback is None:
            hi = np.where(spread == 0, np.inf, center + threshold * spread)
        else:
            spread[spread == 0] = zero_spread_fallback
            hi = center + threshold * spread
```

Then pass `zero_spread_fallback=None` from `compute_g2`/`compute_g2_debug_bundle` **only when `target == "G20"`**, so the `g2-per-pixel` path is bit-for-bit unchanged. Document the asymmetry and why.

- [ ] **Step 4-6: Test, lint, commit** (same commands as Task 1).

---

### Task 3: `target` in `compute_g2_debug_bundle`; bundle key `g2_pixel` → `values`

**Files:**
- Modify: `src/pyxpcsviewer/core/g2_utils.py`
- Modify: `src/pyxpcsviewer/gui/view/g2_debug_dialog.py` (line 201 only)
- Test: `tests/test_g2_utils.py`, `tests/test_g2_debug_dialog.py`

**Interfaces:**
- `compute_g2_debug_bundle(..., target: str = DEFAULT_OUTLIER_TARGET)`.
- Returned dict: key `g2_pixel` becomes `values` (the array the outlier pass actually consumed); new key `target` (str). Other keys unchanged.

- [x] **Step 1: Write the failing tests**

Update the 4 existing references in `tests/test_g2_utils.py` (lines 50, 51, 75, 81) from `b["g2_pixel"]` to `b["values"]`, and make `test_bundle_g2_pixel_matches_normalize_g2` explicit about its target:

```python
def test_bundle_values_are_normalize_g2_for_the_g2_target():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, target="g2-per-pixel")
    n_delays, n_channels, _, _ = G2.shape
    np.testing.assert_allclose(b["values"], normalize_g2(G2.reshape(n_delays, n_channels, -1)))
    assert b["target"] == "g2-per-pixel"


def test_bundle_values_are_the_numerator_for_the_G20_target():
    G2, sqmap, dqmap = make_data()
    b = compute_g2_debug_bundle(sqmap, dqmap, G2, target="G20")
    np.testing.assert_allclose(b["values"], G2.reshape(G2.shape[0], G2.shape[1], -1)[:, 0])
    assert b["target"] == "G20"


def test_bundle_rejects_unknown_target():
    G2, sqmap, dqmap = make_data()
    with pytest.raises(ValueError, match="target"):
        compute_g2_debug_bundle(sqmap, dqmap, G2, target="IP")
```

- [x] **Step 2: Run tests to verify they fail**

- [x] **Step 3: Write the implementation**

```python
    if target not in OUTLIER_TARGETS:
        raise ValueError(f"target must be one of {OUTLIER_TARGETS}, got {target!r}")
    ...
    # only materialize the normalized per-pixel g2 when it is the target -- on a
    # 1 Mpixel detector with 60 delays that array is ~240 MB
    values = G2[:, 0] if target == "G20" else normalize_g2(G2)
    bad = find_g2_pixel_outliers(sqmap_1d, values, threshold=outlier_threshold,
                                 method=outlier_method, combine_outlier=combine_outlier)
    return {"values": values, "target": target, "bad": bad, ...}
```

Update the function docstring's Returns block. In `g2_debug_dialog.py` change line 201 to `self._bundle["values"]` and update the module docstring (it currently says the dialog visualizes "the per-pixel g2").

- [x] **Step 4: Run tests**

```bash
/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/test_g2_utils.py tests/test_g2_debug_dialog.py -v
```
Both files must be green: `test_g2_debug_dialog.py`'s fixtures use `IF == 1`, so its expected flagged pixels are identical under the new default target.

- [x] **Step 5: Lint + type check** — as Task 1, plus `mypy src/pyxpcsviewer/gui/view/g2_debug_dialog.py` (0 errors).

- [x] **Step 6: Commit**

---

### Task 4: Thread `target` through the debug dialog

**Files:**
- Modify: `src/pyxpcsviewer/gui/view/g2_debug_dialog.py`
- Test: `tests/test_g2_debug_dialog.py`

**Interfaces:** `G2DebugWorker(xfile, method, threshold, combine_outlier, target=DEFAULT_OUTLIER_TARGET, parent=None)`, `G2DebugDialog(xfile, method, threshold, combine_outlier, target=DEFAULT_OUTLIER_TARGET, parent=None)`, `build_debug_plots(widget, bundle, fname, method, threshold, combine_outlier, target=DEFAULT_OUTLIER_TARGET)`. Defaults keep every existing positional call site in the tests working.

- [x] **Step 1: Write the failing tests**

```python
def test_header_reports_the_outlier_target(qapp, bundle):
    host = _host()
    build_debug_plots(host, bundle, "fake.hdf", "MeanAbsoluteDeviation", 3.0, False, "G20")
    header = host.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "target=G20" in header.text()


def test_dialog_forwards_target_to_the_bundle(qapp):
    """The dialog must compute on the target it was opened with, or it
    visualizes something other than what ReGroup will do."""
    G2, sqmap, dqmap = make_synthetic()
    fake = cast(_XpcsFileLike, types.SimpleNamespace(fname="fake.hdf", G2=G2, sqmap=sqmap, dqmap=dqmap))
    dlg = G2DebugDialog(fake, "MeanAbsoluteDeviation", 3.0, False, "g2-per-pixel")
    ...  # wait for the worker exactly as test_dialog_computes_and_populates does
    header = dlg.findChild(QtWidgets.QLabel, "g2_debug_header")
    assert "target=g2-per-pixel" in header.text()
```

`G2DebugDialog` does not retain the bundle today (`_bundle` at `g2_debug_dialog.py:122` belongs to `_BinSweepPanel`), so assert through the header text rather than adding an attribute purely for the test.

- [x] **Step 2: Run tests to verify they fail**

- [x] **Step 3: Write the implementation**

Add the parameter to all three signatures, store it on the worker/dialog, pass `target=self._target` into `compute_g2_debug_bundle`, and extend the header f-string:

```python
        f"method={method}, threshold={threshold:g}, combine={combine_outlier}, target={target}"
```

Also set an x-axis label on the bin-sweep histograms so the plotted quantity is unambiguous — `item.setLabel("bottom", bundle["target"])` in `_BinSweepPanel._render`.

- [x] **Step 4-6: Test, lint, commit.**

---

### Task 5: UI combo box + main-window wiring

**Files:**
- Modify: `src/pyxpcsviewer/gui/view/view.ui`
- Regenerate: `src/pyxpcsviewer/gui/view/viewer_ui.py` (never hand-edit)
- Modify: `src/pyxpcsviewer/gui/view/xpcs_viewer.py`
- Test: `tests/test_g2_regroup_gui_wiring.py`

- [x] **Step 1: Write the failing test**

In `tests/test_g2_regroup_gui_wiring.py`, add `self.comboBox_G2_outliertarget = _FakeCombo("G20")` to `_FakeWindow.__init__` (next to `comboBox_G2_errormodel`, ~line 134) and assert the kwarg reaches the job:

```python
def test_process_G2_regroup_forwards_the_outlier_target(qapp):
    window = _FakeWindow()
    window.checkBox_G2_removeoutlier = _FakeCheckbox(True)   # no setChecked() on the fake
    window.comboBox_G2_outliertarget = _FakeCombo("g2-per-pixel")
    XpcsViewer.process_G2_regroup(window)
    assert _pump(qapp, lambda: len(window.plots.calls) == 1)
    assert window.plots.calls[0]["target"] == "g2-per-pixel"
```

Also add a smoke assertion that the real generated UI exposes the widget with the right items (mirroring `test_debug_button_wired` in `tests/test_g2_debug_dialog.py`):

```python
def test_outlier_target_combo_exists_with_both_targets(qapp, tmp_path):
    win = ...  # same construction as test_debug_button_wired
    items = [win.comboBox_G2_outliertarget.itemText(i)
             for i in range(win.comboBox_G2_outliertarget.count())]
    assert items == ["G20", "g2-per-pixel"]
```

- [x] **Step 2: Run tests to verify they fail**

- [x] **Step 3: Add the widgets to `view.ui`**

In `groupBox_23` ("Group Setting", `gridLayout_50`), rows 0 and 1 are full; buttons live at columns 6-7. Add row 2:

```xml
                <item row="2" column="0" colspan="2">
                 <widget class="QLabel" name="label_G2_outliertarget">
                  <property name="text">
                   <string>Outlier Target:</string>
                  </property>
                 </widget>
                </item>
                <item row="2" column="2" colspan="4">
                 <widget class="QComboBox" name="comboBox_G2_outliertarget">
                  <item>
                   <property name="text">
                    <string>G20</string>
                   </property>
                  </item>
                  <item>
                   <property name="text">
                    <string>g2-per-pixel</string>
                   </property>
                  </item>
                 </widget>
                </item>
```

and two `<connection>` entries in the `<connections>` block (copy the shape of the existing `checkBox_G2_removeoutlier → comboBox_G2_outliermethod` connection at ~line 5600): `checkBox_G2_removeoutlier.toggled(bool) → label_G2_outliertarget.setEnabled(bool)` and `→ comboBox_G2_outliertarget.setEnabled(bool)`.

- [x] **Step 4: Regenerate the UI python**

```bash
PATH=/local/MQICHU/envs/l2604_xpcs/bin:$PATH src/pyxpcsviewer/gui/view/convert_ui_to_py.sh
git diff --stat src/pyxpcsviewer/gui/view/viewer_ui.py
```
Confirm the diff only adds the new widgets/connections.

- [x] **Step 5: Wire `xpcs_viewer.py`**

In `process_G2_regroup` (~line 447), alongside `error_model`, and *outside* the `if self.checkBox_G2_removeoutlier.isChecked()` branch — when rejection is off `outlier_threshold=-1.0` makes `target` moot, so setting it unconditionally keeps the kwargs dict shape stable:

```python
        kwargs["target"] = self.comboBox_G2_outliertarget.currentText()
```

In `debug_G2_regroup` (~line 403), pass it to the dialog after `combine_outlier`:

```python
            self.checkBox_G2_combineoutlier.isChecked(),
            self.comboBox_G2_outliertarget.currentText(),
            parent=self,
```

- [x] **Step 6: Run the full suite**

```bash
/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/ -v
```

- [x] **Step 7: Lint + type check**

```bash
ruff format src/pyxpcsviewer/gui/view/xpcs_viewer.py tests/test_g2_regroup_gui_wiring.py
ruff check src/pyxpcsviewer/gui/view/xpcs_viewer.py tests/test_g2_regroup_gui_wiring.py
/local/MQICHU/envs/l2604_xpcs/bin/mypy src/pyxpcsviewer/gui/view/xpcs_viewer.py
```

- [x] **Step 8: Commit**

---

## Final verification

- [x] `/local/MQICHU/envs/l2604_xpcs/bin/python -m pytest tests/ -v` — green.
- [x] `/local/MQICHU/envs/l2604_xpcs/bin/mypy src/pyxpcsviewer/core/g2_utils.py` — still exactly 19 errors.
- [x] `ruff check .` — no new findings.
- [x] Manual: launch `pyxpcsviewer <dir>`, G2_regroup tab → Group Setting shows "Outlier Target" defaulting to `G20`, greyed out when "Remove Outlier" is unchecked. **Debug** shows `target=G20` in the header and histograms on the `G20` scale (raw magnitudes, not centred on 1). Switch to `g2-per-pixel`, reopen Debug, confirm the histograms move back to the g2 scale and a different bad-pixel map appears. **ReGroup** under each target and confirm the plotted g2 curves differ.
- [x] Sanity on real data: with `target="G20"`, the bad-pixel map should concentrate on bright/hot pixels rather than scattering uniformly across each ring. If it looks uniform, revisit caveat 5 (Task 2).
