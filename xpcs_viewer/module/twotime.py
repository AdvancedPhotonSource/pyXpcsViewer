import numpy as np
import os
import matplotlib.pyplot as plt


def plot_twotime_map(xfile, hdl, meta=None, group='xpcs', cmap='jet', scale='log',
                     auto_crop=True):

    if xfile.full_path == meta['twotime_fname'] and \
            group == meta['twotime_group']:
        return

    dqmap, saxs, rpath, idlist = xfile.get_twotime_maps(group)
    time_scale = xfile.get_time_scale(group)

    meta['twotime_key'] = rpath
    meta['twotime_group'] = group
    meta['twotime_scale'] = time_scale
    meta['twotime_idlist'] = idlist

    if auto_crop:
        idx = np.nonzero(dqmap >= 1)
        sl_v = slice(np.min(idx[0]), np.max(idx[0]))
        sl_h = slice(np.min(idx[1]), np.max(idx[1]))
        dqmap = dqmap[sl_v, sl_h]
        saxs = saxs[sl_v, sl_h]

    if dqmap.shape[0] > dqmap.shape[1]:
        dqmap = np.swapaxes(dqmap, 0, 1)
        saxs = np.swapaxes(saxs, 0, 1)

    meta['twotime_dqmap'] = dqmap
    meta['twotime_fname'] = xfile.full_path
    meta['twotime_saxs'] = saxs
    meta['twotime_ready'] = True

    if scale == 'log':
        saxs = np.log10(saxs + 1)

    hdl.clear()
    ax = hdl.subplots(1, 2, sharex=True, sharey=True)
    im0 = ax[0].imshow(saxs, cmap=plt.get_cmap(cmap))
    im1 = ax[1].imshow(dqmap, cmap=plt.get_cmap('hot'))
    ax[0].set_title('SAXS-2D')
    ax[1].set_title('dqmap')
    plt.colorbar(im0, ax=ax[0])
    plt.colorbar(im1, ax=ax[1])
    hdl.draw()


def plot_twotime(xfile, hdl, meta, plot_index=1, cmap='jet'):

    if plot_index not in meta['twotime_idlist']:
        msg = 'plot_index is not found.'
        return msg

    # check if a twotime selected point is already there;
    if 'twotime_pos' not in meta or meta['twotime_dqmap'][
            meta['twotime_pos']] != plot_index:
        v, h = np.where(meta['twotime_dqmap'] == plot_index)
        ret = (np.mean(v), np.mean(h))
    else:
        ret = None
    
    if xfile.type != 'Twotime':
        return ret

    c2 = xfile.get_twotime_c2(plot_index=plot_index,
                              twotime_key=meta['twotime_key'])

    t = meta['twotime_scale'] * np.arange(len(c2))
    t_min = np.min(t)
    t_max = np.max(t)

    hdl.clear()
    ax = hdl.subplots(1, 2)
    im = ax[0].imshow(c2,
                      interpolation='none',
                      origin='lower',
                      extent=([t_min, t_max, t_min, t_max]),
                      cmap=plt.get_cmap(cmap))
    plt.colorbar(im, ax=ax[0])
    ax[0].set_ylabel('t1 (s)')
    ax[0].set_xlabel('t2 (s)')

    # the first element in the list seems to deviate from the rest a lot
    g2f = xfile.g2_full[:, plot_index - 1][1:]
    g2p = xfile.g2_partials[:, :, plot_index - 1].T
    g2p = g2p[:, 1:]

    t = meta['twotime_scale'] * np.arange(g2f.size)
    ax[1].plot(t, g2f, lw=3, color='blue', alpha=0.5)
    for n in range(g2p.shape[0]):
        t = meta['twotime_scale'] * np.arange(g2p[n].size)
        ax[1].plot(t, g2p[n], label='partial%d' % n, alpha=0.5)
    ax[1].set_xscale('log')
    ax[1].set_ylabel('g2')
    ax[1].set_xlabel('t (s)')
    hdl.fig.tight_layout()

    hdl.draw()

    return ret
