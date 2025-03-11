import numpy as np


colors = ('b', 'r', 'g', 'c', 'm', 'y', 'k')
shapes = ('o', 'v', '^', '<', '>', '8', 's', 'p', 'P', '*')


def plot(xf_list, hdl, q_range, offset, plot_type=3):

    hdl.clear()
    ax = hdl.subplots(1, 1)

    for n, xf in enumerate(xf_list):
        s = 10 ** (offset * n)
        x = xf.fit_summary['q_val']
        y = xf.fit_summary['fit_val'][:, 0, 1]
        e = xf.fit_summary['fit_val'][:, 1, 1]
        # remove failed fittings;
        valid_idx = e > 0
        x = x[valid_idx]
        y = y[valid_idx]
        e = e[valid_idx]

        color = colors[n % len(colors)]
        shape = shapes[n % len(shapes)]
        line = ax.errorbar(x, y/s,  yerr=e/s, fmt=shape, markersize=3,
                           label=xf.label, color=color, mfc='white')

        if xf.fit_summary.get('tauq_success', False):
            fit_x = xf.fit_summary['tauq_fit_line']['fit_x']
            fit_y = xf.fit_summary['tauq_fit_line']['fit_y']
            ax.plot(fit_x, fit_y / s, color=color)

    ax.set_xlabel('$q (\\AA^{-1})$')
    ax.set_ylabel('$\\tau (s)$')
    ax.legend()

    xscale = ['linear', 'log'][plot_type % 2]
    yscale = ['linear', 'log'][plot_type // 2]
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
#     hdl.fig.tight_layout()

    hdl.draw()

    return


def plot_pre(xf_list, hdl):

    hdl.clear()
    ax = hdl.subplots(2, 2, sharex=True).flatten()
    titles = ['contrast', 'tau (s)', 'stretch', 'baseline']

    for idx, xf in enumerate(xf_list):
        color = colors[idx % len(colors)]
        shape = shapes[idx % len(shapes)]
        for n in range(4):
            x = xf.fit_summary['q_val']
            y = xf.fit_summary['fit_val'][:, 0, n]
            e = xf.fit_summary['fit_val'][:, 1, n]
            ax[n].errorbar(x, y,  yerr=e, fmt=shape, markersize=3,
                           color=color, mfc='white')

        if idx == len(xf_list) - 1:
            bounds = xf.fit_summary['bounds']
            xmin, xmax = np.min(x), np.max(x)
            for n in range(4):
                ymin = bounds[0][n]
                ymax = bounds[1][n]
                ax[n].set_title(titles[n])
                ax[n].set_title(titles[n])

                if n == 1:
                    ax[n].set_yscale('log')
                    ax[n].set_ylim(ymin * 0.8, ymax * 1.2)
                else:
                    ax[n].set_ylim(ymin * 0.8, ymax * 1.2)

                if n > 1:
                    ax[n].set_xlabel('$q (\\AA^{-1})$')
                # add two lines showing the fitting ub and lb
                ax[n].hlines(ymin, xmin, xmax, color='b', label='lower bound')
                ax[n].hlines(ymax, xmin, xmax, color='g', label='upper bound')

                # only show legend in the last plot
                if n == 3:
                    ax[n].legend()

    # hdl.fig.tight_layout()
    hdl.draw()

    return