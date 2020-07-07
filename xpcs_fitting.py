import numpy as np
import scipy as sp
from scipy.optimize import curve_fit
import traceback


def single_exp(x, tau, bkg, cts):
    return cts * np.exp( -2 * x / tau) + bkg


def fit_xpcs(res, idx, tslice, qslice, b):
    """
    :param res: g2_data
    :param idx:
    :param max_q:
    :param contrast:
    :return:
    """
    t_el = res['t_el'][idx, tslice]
    q = res['ql_dyn'][idx, qslice]

    g2 = res['g2'][idx, tslice, qslice]
    g2_err = res['g2_err'][idx, tslice, qslice]

    fit_x = np.logspace(-5, 0.5, num=128)

    p0_guess = [np.sqrt(b[0][0] * b[1][0]),
                0.5 * (b[0][1] + b[1][1]),
                0.5 * (b[0][2] + b[1][2])]

    fit_val = np.zeros(shape=(q.size, 7))
    fit_result = []
    for n in range(q.size):
        err = g2_err[:, n]
        result = {'num_zero_err': np.sum(err < 1E-6)}
        avg = np.mean(err[err > 1E-6])
        err[err <= 1E-6] = avg
        fit_val[n, 0] = q[n]

        try:
            popt, pcov = curve_fit(single_exp, t_el, g2[:, n],
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
