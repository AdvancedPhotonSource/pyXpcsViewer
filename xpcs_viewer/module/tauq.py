import numpy as np
from ..helper.fitting import fit_tau


def plot(g2_fit_val, labels=None, max_q=0.016, hdl=None, offset=None):
    if g2_fit_val is None:
        msg = 'g2 fitting not ready'
        return [msg]

    num_points = len(g2_fit_val)
    if num_points == 0:
        msg = 'g2 fitting not ready'
        return [msg]

    # prepare fit values
    fit_val = []
    for _, val in g2_fit_val.items():
        fit_val.append(val)
    fit_val = np.hstack(fit_val).swapaxes(0, 1)
    q = fit_val[::7]
    sl = q[0] <= max_q

    tau = fit_val[1::7]
    cts = fit_val[3::7]

    tau_err = fit_val[4::7]
    cts_err = fit_val[6::7]

    fit_msg = []

    hdl.clear()
    ax = hdl.subplots(1, 1)

    for n in range(tau.shape[0]):
        s = 10 ** (offset * n)
        line = ax.errorbar(q[n][sl],
                           tau[n][sl] / s,
                           yerr=tau_err[n][sl] / s,
                           fmt='o-',
                           markersize=3,
                           label=labels[n])
        slope, intercept, xf, yf = fit_tau(q[n][sl], tau[n][sl],
                                           tau_err[n][sl])
        # plot straight line
        ax.plot(xf, yf / s)
        fit_msg.append('fn: %s, slope = %.4f, intercept = %.4f' %
                       (labels[n], slope, intercept))

    ax.set_xlabel('$q (\\AA^{-1})$')
    ax.set_ylabel('$\\tau \\times 10^4$')
    ax.legend()
    ax.set_xscale('log')
    ax.set_yscale('log')
    hdl.draw()

    return fit_msg