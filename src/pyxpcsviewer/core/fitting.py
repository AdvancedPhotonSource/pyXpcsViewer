# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging
import traceback

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
        except:
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
    if p0 is None:
        p0 = np.mean(bounds_fit, axis=0)
    else:
        p0 = np.array(p0)[fit_flag]

    fit_val = np.zeros((y.shape[1], 2, num_args))

    fit_line = []
    for n in range(y.shape[1]):
        flag = True
        try:
            popt, pcov = curve_fit(func, x, y[:, n], p0=p0, sigma=sigma[:, n], bounds=bounds_fit)
        except (Exception, RuntimeError, ValueError, Warning):
            msg = "Fitting failed: %s" % traceback.format_exc()
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
