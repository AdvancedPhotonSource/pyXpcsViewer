# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any

import numpy as np
from scipy.optimize import curve_fit
from sklearn import linear_model

logger = logging.getLogger(__name__)


def single_exp(x: float | np.ndarray, tau: float, bkg: float, cts: float) -> float | np.ndarray:
    """Evaluate a single-exponential decay function.

    Args:
        x: Independent variable (time delay).
        tau: Characteristic decay time.
        bkg: Constant background level.
        cts: Amplitude scaling factor (contrast).

    Returns:
        Computed decay values ``cts * exp(-2*x/tau) + bkg``.
    """
    return cts * np.exp(-2 * x / tau) + bkg


def single_exp_all(x, a, b, c, d):
    """Single exponential fitting model for XPCS-multitau analysis.

    Args:
        x: Delay in seconds.
        a: Contrast.
        b: Characteristic time (tau).
        c: Restriction factor.
        d: Baseline offset.

    Returns:
        Computed value of the single exponential model.
    """
    return a * np.exp(-2 * (x / b) ** c) + d


def double_exp_all(x, a, b1, c1, d, b2, c2, f):
    """Double exponential fitting model for XPCS-multitau analysis.

    Args:
        x: Delay in seconds.
        a: Contrast.
        b1: Characteristic time (tau) of the first exponential component.
        c1: Restriction factor for the first component.
        d: Baseline offset.
        b2: Characteristic time (tau) of the second exponential component.
        c2: Restriction factor for the second component.
        f: Fractional contribution of the first exponential component (0 ≤ f ≤ 1).

    Returns:
        Computed value of the double exponential model.
    """
    t1 = np.exp(-1 * (x / b1) ** c1) * f
    t2 = np.exp(-1 * (x / b2) ** c2) * (1 - f)
    return a * (t1 + t2) ** 2 + d


def power_law(x, a, b):
    """Power-law fitting model for diffusion behavior.

    Args:
        x: Independent variable, typically time delay (tau).
        a: Scaling factor.
        b: Power exponent.

    Returns:
        Computed value based on the power-law model.
    """
    return a * x**b


def fit_tau(qd: np.ndarray, tau: np.ndarray, tau_err: np.ndarray):
    """Perform linear regression on ``log(tau)`` vs ``log(q)`` to extract the diffusion exponent.

    Args:
        qd: Momentum-transfer values (Q-axis).
        tau: Characteristic times corresponding to each Q value.
        tau_err: Errors on tau for weighted fitting.

    Returns:
        Tuple of ``(slope, intercept, fit_x, fit_y)`` where *fit_x/fit_y* span the fitted line.
    """
    x = np.log(qd).reshape(-1, 1)
    y = np.log(tau).reshape(-1, 1)
    dy = tau / tau_err
    reg = linear_model.LinearRegression()
    reg.fit(x, y, sample_weight=dy)
    x2 = np.linspace(np.min(x) - 0.1, np.max(x) + 0.1, 128)
    y2 = reg.predict(x2.reshape(-1, 1))
    return reg.coef_, reg.intercept_, np.exp(x2).ravel(), np.exp(y2).ravel()


def fit_xpcs(tel, qd, g2, g2_err, b):
    """Fit G2 data with single exponential decay for each Q bin.

    Args:
        tel: Time delay values.
        qd: Dynamic Q-axis values.
        g2: G2 correlation data, shape (time, q_vals).
        g2_err: Error on G2, shape (time, q_vals).
        b: Fitting bounds.

    Returns:
        Tuple of ``(fit_result, fit_val)`` where *fit_result* is a list of
        per-Q-bin dictionaries and *fit_val* is a ``(n_q, 7)`` array.
    """

    # fit_x = np.logspace(-5, 0.5, num=128)
    fit_x = np.logspace(np.log10(np.min(tel)) - 0.5, np.log10(np.max(tel)) + 0.5, 128)

    p0_guess = [np.sqrt(b[0][0] * b[1][0]), 0.5 * (b[0][1] + b[1][1]), 0.5 * (b[0][2] + b[1][2])]

    fit_val = np.zeros(shape=(qd.size, 7))
    fit_result = []
    for n in range(qd.size):
        err = g2_err[:, n]
        result = {"num_zero_err": np.sum(err < 1e-6)}
        avg = np.mean(err[err > 1e-6])
        err[err <= 1e-6] = avg
        fit_val[n, 0] = qd[n]

        try:
            popt, pcov = curve_fit(single_exp, tel, g2[:, n], p0=p0_guess, sigma=err, bounds=b)
            fit_val[n, 1:4], fit_val[n, 4:7] = popt, np.sqrt(np.diag(pcov))
        except Exception:
            # fit_val[n, 1:4], fit_val[n, 4:7] = popt, np.sqrt(np.diag(pcov))
            result = {
                "err_msg": "q_index %2d:" + str(traceback.format_exc()),
                "fit_x": fit_x,
                "fit_y": np.ones_like(fit_x),
            }
        else:
            fit_y = single_exp(fit_x, *popt)
            result = {
                "err_msg": None,
                # result = {'err_msg': 'q_index %2d: fit ends without err' % n,
                "opt": popt,
                "err": np.sqrt(np.diag(pcov)),
                "fit_x": fit_x,
                "fit_y": fit_y,
            }
        finally:
            fit_result.append(result)

    return fit_result, fit_val


def fit_with_fixed(base_func, x, y, sigma, bounds, fit_flag, fit_x, p0=None):
    """Fit *base_func* with per-variable bounds and optional fixed parameters.

    Args:
        base_func: Fittable function (e.g. ``single_exp``). May accept
            multiple arguments, some of which can be held constant.
        x: Independent variable (scaler input).
        y: Dependent variable (scaler output).
        sigma: Measurement error on *y*.
        bounds: Tuple of ``(lower, upper)`` arrays. When a parameter's flag
            is ``False``, the upper bound is used as the fixed value.
        fit_flag: Boolean array — ``True`` to fit, ``False`` to hold fixed.
        fit_x: X-axis values for plotting the fitted curve.
        p0: Initial parameter guess. Defaults to the midpoint of the fit
            parameter bounds.

    Returns:
        Tuple of ``(fit_line, fit_val)`` where *fit_line* is a list of
        per-Q-bin dictionaries and *fit_val* is a ``(n_q, 2, n_params)`` array.
    """
    if not isinstance(fit_flag, np.ndarray):
        fit_flag = np.array(fit_flag)

    fix_flag = np.logical_not(fit_flag)

    if not isinstance(bounds, np.ndarray):
        bounds = np.array(bounds)

    # degree of fitting
    # dof = np.sum(fit_flag)

    # number of arguments, regardless of fixed or to be fitted
    num_args = len(fit_flag)

    # create a function that takes care of the fit flag;
    def func(x1, *args):
        """Construct a callable with fixed parameters set to their upper bounds."""
        inputs = np.zeros(num_args)
        inputs[fix_flag] = bounds[1, fix_flag]
        inputs[fit_flag] = np.array(args)
        return base_func(x1, *inputs)

    # process boundaries and initial values
    bounds_fit = bounds[:, fit_flag]
    # doing a simple average to get the initial guess;
    p0 = np.mean(bounds_fit, axis=0) if p0 is None else np.array(p0)[fit_flag]

    fit_val = np.zeros((y.shape[1], 2, num_args))

    fit_line = []
    for n in range(y.shape[1]):
        flag = True
        try:
            popt, pcov = curve_fit(func, x, y[:, n], p0=p0, sigma=sigma[:, n], bounds=bounds_fit)
        except (Exception, RuntimeError, ValueError, Warning):
            msg = f"Fitting failed: {traceback.format_exc()}"
            logger.info(msg)
            flag = False
            fit_val[n, 0, fit_flag] = p0
            fit_val[n, 0, fix_flag] = bounds[1, fix_flag]
            # mark failed fitting to be negative so they can be filtered later
            fit_val[n, 1, :] = -1
            fit_y = None

        else:
            flag = True
            msg = "FittingSuccess"
            # converge values
            fit_val[n, 0, fit_flag] = popt
            fit_val[n, 0, fix_flag] = bounds[1, fix_flag]
            # errors; the fixed variables have error of 0
            fit_val[n, 1, fit_flag] = np.sqrt(np.diag(pcov))
            # fit line
            fit_y = func(fit_x, *popt)

        finally:
            fit_line.append({"fit_x": fit_x, "fit_y": fit_y, "success": flag, "msg": msg})

    return fit_line, fit_val


def build_g2_fit_summary(
    q_val: np.ndarray,
    t_el: np.ndarray,
    g2: np.ndarray,
    sigma: np.ndarray,
    label: list[str],
    bounds,
    fit_flag=None,
    fit_func: str = "single",
    q_range=None,
    t_range=None,
) -> dict[str, Any]:
    """Fit every q-bin of one file's g2 data and return a fit_summary dict.

    Pure and picklable (only numpy arrays/primitives in and out), so it can
    run standalone or inside a worker process via :func:`fit_g2_batch`.

    Args:
        q_val: Q-values for each fitted bin.
        t_el: Elapsed-time axis.
        g2: G2 correlation data, shape (time, q_bins).
        sigma: Error on *g2*, same shape.
        label: Per-Q-bin label strings.
        bounds: Fitting bounds as ``(lower, upper)``.
        fit_flag: Tuple of bools — ``True`` to fit, ``False`` to hold fixed.
        fit_func: Either ``"single"`` or ``"double"`` exponential model.
        q_range: Original Q-range filter, recorded for display only.
        t_range: Original time-range filter, recorded for display only.

    Returns:
        Dictionary with the fitting results.
    """
    assert len(bounds) == 2
    if fit_func == "single":
        assert len(bounds[0]) == 4, "for single exp, the shape of bounds must be (2, 4)"
        if fit_flag is None:
            fit_flag = [True for _ in range(4)]
        func = single_exp_all
    else:
        assert len(bounds[0]) == 7, "for double exp, the shape of bounds must be (2, 7)"
        if fit_flag is None:
            fit_flag = [True for _ in range(7)]
        func = double_exp_all

    # set the initial guess
    p0 = np.array(bounds).mean(axis=0)
    # tau"s bounds are in log scale, set as the geometric average
    p0[1] = np.sqrt(bounds[0][1] * bounds[1][1])
    if fit_func == "double":
        p0[4] = np.sqrt(bounds[0][4] * bounds[1][4])

    fit_x = np.logspace(np.log10(np.min(t_el)) - 0.5, np.log10(np.max(t_el)) + 0.5, 128)

    fit_line, fit_val = fit_with_fixed(func, t_el, g2, sigma, bounds, fit_flag, fit_x, p0=p0)

    return {
        "fit_func": fit_func,
        "fit_val": fit_val,
        "t_el": t_el,
        "q_val": q_val,
        "q_range": str(q_range),
        "t_range": str(t_range),
        "bounds": bounds,
        "fit_flag": str(fit_flag),
        "fit_line": fit_line,
        "label": label,
    }


def fit_g2_batch(
    file_inputs: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]],
    bounds,
    fit_flag=None,
    fit_func: str = "single",
    q_range=None,
    t_range=None,
    max_workers: int | None = None,
    progress_callback=None,
) -> list[dict[str, Any] | None]:
    """Fit g2 data for multiple files in parallel using a process pool.

    Args:
        file_inputs: List of ``(q_val, t_el, g2, sigma, label)`` tuples, one
            per file — i.e. each file's ``XpcsFile.get_g2_data()`` return value.
        bounds: Fitting bounds as ``(lower, upper)``, shared across all files.
        fit_flag: Tuple of bools — ``True`` to fit, ``False`` to hold fixed.
        fit_func: Either ``"single"`` or ``"double"`` exponential model.
        q_range: Original Q-range filter, recorded for display only.
        t_range: Original time-range filter, recorded for display only.
        max_workers: Forwarded to ``ProcessPoolExecutor`` (``None`` picks a default).
        progress_callback: Optional ``callable(done, total)`` invoked as each
            file's fit completes.

    Returns:
        List of fit_summary dicts (``None`` for any file whose fit raised),
        in the same order as *file_inputs*.
    """
    results: list[dict[str, Any] | None] = [None] * len(file_inputs)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(build_g2_fit_summary, *args, bounds, fit_flag, fit_func, q_range, t_range): idx
            for idx, args in enumerate(file_inputs)
        }
        for done, future in enumerate(as_completed(futures), start=1):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception:
                logger.exception("g2 fit failed for file index %d", idx)
            if progress_callback is not None:
                progress_callback(done, len(file_inputs))
    return results
