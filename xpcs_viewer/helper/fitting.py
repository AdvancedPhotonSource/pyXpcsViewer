import numpy as np
import scipy as sp
from scipy.optimize import curve_fit
from scipy.stats import linregress as sp_stats
import traceback
from sklearn import linear_model
import joblib
import os
import time
import traceback
import logging


logger = logging.getLogger(__name__)

cache_dir = os.path.join(os.path.expanduser('~'), '.xpcs_viewer')
from joblib import Memory
memory = Memory(cache_dir, verbose=0)


@memory.cache
def fit_with_fixed(*args, **kwargs):
    # wrap the fitting function in memory so avoid re-run
    return fit_with_fixed_raw(*args, **kwargs)


def single_exp(x, tau, bkg, cts):
    return cts * np.exp( -2 * x / tau) + bkg


def fit_tau(qd, tau, tau_err):
    x = np.log(qd).reshape(-1, 1)
    y = np.log(tau).reshape(-1, 1)
    dy = tau / tau_err
    reg = linear_model.LinearRegression()
    reg.fit(x, y, sample_weight=dy)
    x2 = np.linspace(np.min(x) - 0.1, np.max(x) + 0.1, 128)
    y2 = reg.predict(x2.reshape(-1, 1))
    return reg.coef_, reg.intercept_, np.exp(x2).ravel(), np.exp(y2).ravel()


def fit_xpcs(tel, qd, g2, g2_err, b):
    """
    :param tel: t_el
    :param qd: ql_dyn
    :param g2: g2 [time, ql_dyn]
    :param g2_err: [time, ql_dyn]
    :param b: bounds
    :return:
    """

    # fit_x = np.logspace(-5, 0.5, num=128)
    fit_x = np.logspace(np.log10(np.min(tel)) - 0.5,
                        np.log10(np.max(tel)) + 0.5, 128)

    p0_guess = [np.sqrt(b[0][0] * b[1][0]),
                0.5 * (b[0][1] + b[1][1]),
                0.5 * (b[0][2] + b[1][2])]

    fit_val = np.zeros(shape=(qd.size, 7))
    fit_result = []
    for n in range(qd.size):
        err = g2_err[:, n]
        result = {'num_zero_err': np.sum(err < 1E-6)}
        avg = np.mean(err[err > 1E-6])
        err[err <= 1E-6] = avg
        fit_val[n, 0] = qd[n]

        try:
            popt, pcov = curve_fit(single_exp, tel, g2[:, n],
                                   p0=p0_guess,
                                   sigma=err,
                                   bounds=b)
            fit_val[n, 1:4], fit_val[n, 4:7] = popt, np.sqrt(np.diag(pcov))
        except:
            # fit_val[n, 1:4], fit_val[n, 4:7] = popt, np.sqrt(np.diag(pcov))
            result = {'err_msg': 'q_index %2d:' + str(traceback.format_exc()),
                      'fit_x': fit_x, 'fit_y': np.ones_like(fit_x)}
        else:
            fit_y = single_exp(fit_x, *popt)
            result = {'err_msg': None,
            # result = {'err_msg': 'q_index %2d: fit ends without err' % n,
                      'opt': popt, 'err': np.sqrt(np.diag(pcov)),
                      'fit_x': fit_x, 'fit_y': fit_y}
        finally:
            fit_result.append(result)

    return fit_result, fit_val


def fit_with_fixed_raw(base_func, x, y, sigma, bounds, fit_flag, fit_x,
                       p0=None):
    """
    :param base_func: the base function used for fitting; it can have multiple
        input variables, some of which can be fixed during the fitting;
    :param x: scaler input
    :param y: scaler output
    :param sigma: the error for y value
    :param bounds: tuple with two elements. 1st is the lower bounds and 2nd is
        the upper bounds; if the fit_flag for a variable is False, then the
        upper bound is used as the fixed value;
    :param fit_flag: tuple of bools, True/False for fit and fixed
    :param fit_x: the fitting line for x
    :param p0: the initial value for the variables; if None is provided, the
        intial value is set as the mean of lower and upper bounds
    :return: a tuple of (fit_line, fit_val)
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
            popt, pcov = curve_fit(func, x, y[:, n], p0=p0, sigma=sigma[:, n],
                                   bounds=bounds_fit)
        except (Exception, RuntimeError, ValueError, Warning) as err:
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
            msg = 'FittingSuccess'
            # converge values
            fit_val[n, 0, fit_flag] = popt
            fit_val[n, 0, fix_flag] = bounds[1, fix_flag]
            # errors; the fixed variables have error of 0
            fit_val[n, 1, fit_flag] = np.sqrt(np.diag(pcov))
            # fit line
            fit_y = func(fit_x, *popt)

        finally:
            fit_line.append({'fit_x': fit_x, 'fit_y': fit_y, 'success': flag,
                             'msg': msg})

    return fit_line, fit_val
