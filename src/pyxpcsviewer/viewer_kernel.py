import numpy as np
from .file_locator import FileLocator
from .module import saxs2d, saxs1d, intt, stability, g2mod, tauq, twotime
from .module.average_toolbox import AverageToolbox
from .helper.listmodel import TableDataModel
import pyqtgraph as pg
import os
import logging
from .xpcs_file import XpcsFile


logger = logging.getLogger(__name__)


class ViewerKernel(FileLocator):
    def __init__(self, path, statusbar=None):
        super().__init__(path)
        self.statusbar = statusbar
        self.meta = None
        self.reset_meta()
        self.path = path
        self.avg_worker = None
        self.avg_jid = 0
        self.avg_worker_active = {}
        self.current_dset = None

    def reset_meta(self):
        self.meta = {
            # saxs 1d:
            "saxs1d_bkg_fname": None,
            "saxs1d_bkg_xf": None,
            # avg
            "avg_file_list": None,
            "avg_intt_minmax": None,
            "avg_g2_avg": None,
            # g2
        }
        return

    def reset_kernel(self):
        self.clear_target()
        self.reset_meta()

    def select_bkgfile(self, fname):
        base_fname = os.path.basename(fname)
        self.meta["saxs1d_bkg_fname"] = base_fname
        self.meta["saxs1d_bkg_xf"] = XpcsFile(fname)

    def get_pg_tree(self, rows):
        xf_list = self.get_xf_list(rows)
        if xf_list:
            return xf_list[0].get_pg_tree()
        else:
            return None

    def get_fitting_tree(self, rows):
        xf_list = self.get_xf_list(rows, filter_atype="Multitau")
        result = {}
        for x in xf_list:
            result[x.label] = x.get_fitting_info(mode="g2_fitting")
        tree = pg.DataTreeWidget(data=result)
        tree.setWindowTitle("fitting summary")
        tree.resize(1024, 800)
        return tree

    def plot_g2(self, handler, q_range, t_range, y_range, rows=None, **kwargs):
        xf_list = self.get_xf_list(rows=rows, filter_atype="Multitau")
        if xf_list:
            g2mod.pg_plot(
                handler, xf_list, q_range, t_range, y_range, rows=rows, **kwargs
            )
            q, tel, *unused = g2mod.get_g2_data(xf_list)
            return q, tel
        else:
            return None, None

    def plot_g2_stability(
        self, handler, q_range, t_range, y_range, rows=None, **kwargs
    ):
        xf_obj = self.get_xf_list(rows=rows, filter_atype="Multitau")[0]
        if xf_obj and xf_obj.g2_partial is not None:
            g2mod.pg_plot_stability(
                handler, xf_obj, q_range, t_range, y_range, rows=rows, **kwargs
            )
            q, tel, *unused = g2mod.get_g2_data([xf_obj])
            return q, tel
        else:
            return None, None

    def plot_g2map(
        self, g2map_hdl, qmap_hdl, g2_hdl, rows=None, qbin=0, normalization=False
    ):
        xf_obj = self.get_xf_list(rows=rows)[0]
        if xf_obj:
            g2map_hdl.setImage(xf_obj.get_offseted_g2(normalization).T)
            qmap_hdl.setImage(xf_obj.get_cropped_qmap("dqmap"))

            g2_hdl.clear()
            color = (0, 128, 255)
            pen = pg.mkPen(color=color, width=2)

            x = xf_obj.t_el
            y = xf_obj.g2[:, qbin]
            dy = xf_obj.g2_err[:, qbin]

            line = pg.ErrorBarItem(x=np.log10(x), y=y, top=dy, bottom=dy, pen=pen)
            pen = pg.mkPen(color=color, width=1)
            g2_hdl.plot(
                x,
                y,
                pen=None,
                symbol="o",
                name=f"{qbin=}",
                symbolSize=3,
                symbolPen=pen,
                symbolBrush=pg.mkBrush(color=(*color, 0)),
            )

            g2_hdl.setLogMode(x=True, y=None)
            g2_hdl.addItem(line)
            g2_hdl.setLabel("bottom", "tau", units="s")
            g2_hdl.setLabel("left", "g2")
            return

    def plot_qmap(self, hdl, rows=None, target=None, cmap="tab20b"):
        xf_list = self.get_xf_list(rows=rows)
        if xf_list:
            if target == "scattering":
                value = np.log10(xf_list[0].saxs_2d + 1)
                vmin, vmax = np.percentile(value, (2, 98))
                hdl.setImage(value, levels=(vmin, vmax))
            elif target == "dynamic_roi_map":
                hdl.setImage(xf_list[0].dqmap)
            elif target == "static_roi_map":
                hdl.setImage(xf_list[0].sqmap)
            hdl.setColorMap(pg.colormap.getFromMatplotlib(cmap))

    def plot_tauq_pre(self, hdl=None, rows=None):
        xf_list = self.get_xf_list(rows=rows, filter_atype="Multitau")
        short_list = [xf for xf in xf_list if xf.fit_summary is not None]
        tauq.plot_pre(short_list, hdl)

    def plot_tauq(
        self,
        hdl=None,
        bounds=None,
        rows=[],
        plot_type=3,
        fit_flag=None,
        offset=None,
        q_range=None,
    ):
        xf_list = self.get_xf_list(
            rows=rows, filter_atype="Multitau", filter_fitted=True
        )
        result = {}
        for x in xf_list:
            if x.fit_summary is None:
                logger.info("g2 fitting is not available for %s", x.fname)
            else:
                x.fit_tauq(q_range, bounds, fit_flag)
                result[x.label] = x.get_fitting_info(mode="tauq_fitting")

        if len(result) > 0:
            tauq.plot(
                xf_list, hdl=hdl, q_range=q_range, offset=offset, plot_type=plot_type
            )

        return result

    def get_info_at_mouse(self, rows, x, y):
        xf = self.get_xf_list(rows)
        if xf:
            info = xf[0].get_info_at_position(x, y)
            return info

    def plot_saxs_2d(self, *args, rows=None, **kwargs):
        xf_list = self.get_xf_list(rows)[0:1]
        if xf_list:
            saxs2d.plot(xf_list[0], *args, **kwargs)

    def add_roi(self, hdl, **kwargs):
        xf_list = self.get_xf_list()
        cen = (xf_list[0].bcx, xf_list[0].bcy)
        if kwargs["sl_type"] == "Pie":
            hdl.add_roi(cen=cen, radius=100, **kwargs)
        elif kwargs["sl_type"] == "Circle":
            radius_v = min(xf_list[0].mask.shape[0] - cen[1], cen[1])
            radius_h = min(xf_list[0].mask.shape[1] - cen[0], cen[0])
            radius = min(radius_h, radius_v) * 0.8

            hdl.add_roi(cen=cen, radius=radius, label="RingA", **kwargs)
            hdl.add_roi(cen=cen, radius=0.8 * radius, label="RingB", **kwargs)

    def plot_saxs_1d(self, pg_hdl, mp_hdl, **kwargs):
        xf_list = self.get_xf_list()
        if xf_list:
            saxs1d.pg_plot(
                xf_list, mp_hdl, bkg_file=self.meta["saxs1d_bkg_xf"], **kwargs
            )

    def export_saxs_1d(self, pg_hdl, folder):
        xf_list = self.get_xf_list()
        roi_list = pg_hdl.get_roi_list()
        for xf in xf_list:
            xf.export_saxs1d(roi_list, folder)
        return

    def switch_saxs1d_line(self, mp_hdl, lb_type):
        pass
        # saxs1d.switch_line_builder(mp_hdl, lb_type)

    def plot_twotime(self, hdl, rows=None, **kwargs):
        xf_list = self.get_xf_list(rows, filter_atype="Twotime")
        if len(xf_list) == 0:
            return None
        xfile = xf_list[0]
        new_qbin_labels = None
        if self.current_dset is None or self.current_dset.fname != xfile.fname:
            self.current_dset = xfile
            new_qbin_labels = xfile.get_twotime_qbin_labels()
        twotime.plot_twotime(xfile, hdl, **kwargs)
        return new_qbin_labels

    def plot_intt(self, pg_hdl, rows=None, **kwargs):
        xf_list = self.get_xf_list(rows=rows)
        intt.plot(xf_list, pg_hdl, **kwargs)

    def plot_stability(self, mp_hdl, rows=None, **kwargs):
        xf_obj = self.get_xf_list(rows)[0]
        stability.plot(xf_obj, mp_hdl, **kwargs)

    def submit_job(self, *args, **kwargs):
        if self.avg_worker is not None:
            logger.error("average job is already running")
            return

        if len(self.target) <= 0:
            logger.error("no average target is selected")
            return

        worker = AverageToolbox(flist=self.target, jid=self.avg_jid)
        worker.setup(*args, **kwargs)
        worker.signals.finished.connect(self.avg_job_finished)
        self.avg_worker = worker
        logger.info("create average job, ID = %s", worker.jid)
        self.avg_jid += 1
        self.target.clear()
        return

    def update_avg_info(self):
        if self.avg_worker is None:
            return
        self.avg_worker.update_plot()

    def avg_job_finished(self, success):
        if success:
            self.statusbar.showMessage("average job finished", 5000)
        else:
            self.statusbar.showMessage("average job failed", 5000)
        self.avg_worker_active = {}
        self.avg_worker = None

    def update_avg_values(self, data):
        key, val = data[0], data[1]
        if self.avg_worker_active[key] is None:
            self.avg_worker_active[key] = [0, np.zeros(128, dtype=np.float32)]
        record = self.avg_worker_active[key]
        if record[0] == record[1].size:
            new_g2 = np.zeros(record[1].size * 2, dtype=np.float32)
            new_g2[0 : record[0]] = record[1]
            record[1] = new_g2
        record[1][record[0]] = val
        record[0] += 1
        return

    def export_g2(self):
        pass


if __name__ == "__main__":
    flist = os.listdir("./data")
    dv = ViewerKernel("./data", flist)
