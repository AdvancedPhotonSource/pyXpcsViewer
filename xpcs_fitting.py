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

    g2 = res['g2'][idx, tslice, qslice]
    g2_err = res['g2_err'][idx, tslice, qslice]

    num_q = g2.shape[1]

    fit_x = np.logspace(-5, 0.5, num=128)

    p0_guess = [np.sqrt(b[0][0] * b[1][0]),
                0.5 * (b[0][1] + b[1][1]),
                0.5 * (b[0][2] + b[1][2])]

    fit_result = []
    for n in range(g2.shape[-1]):
        err = g2_err[:, n]
        result = {'num_zero_err': np.sum(err < 1E-6)}
        avg = np.mean(err[err > 1E-6])
        err[err <= 1E-6] = avg

        try:
            popt, pcov = curve_fit(single_exp, t_el, g2[:, n],
                                   p0=p0_guess,
                                   sigma=err,
                                   bounds=b)
        except:
            result = {'err_msg': str(traceback.format_exc()),
                      'opt': None, 'err': None,
                      'fit_x': fit_x, 'fit_y': np.ones_like(fit_x)}
        else:
            fit_y = single_exp(fit_x, *popt)
            result = {'err_msg': 'q_index %2d: fit ends without err' % n,
                      'opt': popt, 'err': np.sqrt(np.diag(pcov)),
                      'fit_x': fit_x, 'fit_y': fit_y}
        finally:
            fit_result.append(result)

    return fit_result
