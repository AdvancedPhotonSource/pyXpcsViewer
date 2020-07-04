import numpy as np
import scipy as sp
from scipy.optimize import curve_fit


def single_exp(x, tau, bkg, cts):
    # print(x, tau, bkg, cts)
    # y = cts * np.exp( -2 * x / tau) + bkg
    # print(np.min(y), np.max(y))
    return cts * np.exp( -2 * x / tau) + bkg


def fit_xpcs(res, idx, max_q, contrast=None):
    """
    :param res: g2_data
    :param idx:
    :param max_q:
    :param contrast:
    :return:
    """
    t_el, g2, g2_err = res['t_el'][idx], res['g2'][idx], res['g2_err'][idx]
    ql_dyn = res['ql_dyn'][idx]

    num_q = np.sum(ql_dyn <= max_q)
    g2_fit = np.zeros([num_q, 3])
    g2_fit_err = np.zeros([num_q, 3])

    fit_x = np.logspace(-5, 0.5, num=128)

    if contrast is None:
        cts_low = -0.1
        cts_hig = 0.2
    else:
        cts_low = contrast - 0.001
        cts_hig = contrast + 0.001

    p0_guess = [1e-4, 1.0, 0.5 * (cts_low + cts_hig)]
    b_min = [1e-6, 0.99, cts_low]
    b_max = [1e-2, 1.03, cts_hig]

    fit_result = []
    for n, q_val in enumerate(ql_dyn):
        err = g2_err[:, n]
        avg = np.sum(err[err > 1E-6])
        err[err <= 1E-6] = avg

        if q_val > max_q:
            break
        popt, pcov = curve_fit(single_exp, t_el, g2[:, n],
                               p0=p0_guess,
                               sigma=err,
                               bounds=(b_min, b_max))
        g2_fit[n, :] = popt
        g2_fit_err[n, :] = np.sqrt(np.diag(pcov))

        fit_y = single_exp(fit_x, *popt)
        result = {'opt': popt, 'err': popt,
                  'fit_x': fit_x, 'fit_y': fit_y}

        fit_result.append(result)

    return fit_result


