import numpy as np
import scipy as sp
from scipy.optimize import curve_fit
from scipy.stats import linregress as sp_stats
import traceback
from sklearn import linear_model

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


