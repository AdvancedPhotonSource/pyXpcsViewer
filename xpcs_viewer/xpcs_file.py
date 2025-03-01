import os
import numpy as np
from .fileIO.hdf_reader import get, create_id, get_analysis_type, read_metadata_to_dict
from .module.g2mod import create_slice
from .helper.fitting import fit_with_fixed
import pyqtgraph as pg
from .fileIO.qmap_utils import get_qmap
from .module.twotime_utils import get_c2_from_hdf_fast, get_c2_stream


def single_exp_all(x, a, b, c, d):
    """
    single exponential fitting for xpcs-multitau analysis
    :param x: delay in seconds
    :param a: contrast
    :param b: tau
    :param c: restriction factor
    :param d: baseline
    :return:
    """
    return a * np.exp(-2 * (x / b) ** c) + d


def double_exp_all(x, a, b1, c1, d, b2, c2, f):
    """
    double exponential fitting for xpcs-multitau analysis
    Args:
        x: delay in seconds, float or 1d-numpy.ndarray
        a: contrast
        f: fraction for the 1st exp function; the 2nd has (1-f) weight
        b1: tau for 1st exp function
        c1: restriction factor for the 1st exp function
        b2: tau for 2nd exp function
        c2: restriction factor for the 2nd exp function
        d: baseline
    Return:
        function value
    """
    t1 = np.exp(-1 * (x / b1) ** c1) * f
    t2 = np.exp(-1 * (x / b2) ** c2) * (1 - f)
    return a * (t1 + t2) ** 2 + d


def power_law(x, a, b):
    """
    power law for fitting the diffusion factor
    :param x: tau
    :param a:
    :param b:
    :return:
    """
    return a * x ** b



class XpcsFile(object):
    """
    XpcsFile is a class that wraps an Xpcs analysis hdf file;
    """
    def __init__(self, fname, fields=None, label_style=None):
        self.fname = fname
        self.qmap = get_qmap(self.fname)
        self.atype = get_analysis_type(self.fname)
        self.label = self.update_label(label_style)
        payload_dictionary = self.load_data(fields)
        self.__dict__.update(payload_dictionary)
        self.hdf_info = None
        self.fit_summary = None
        self.c2_all_data = None
        self.c2_kwargs = None
        # label is a short string to describe the file/filename
        # place holder for self.saxs_2d; 
        self.saxs_2d_data = None
    
    def update_label(self, label_style):
        self.label = create_id(self.fname, label_style=label_style)
        return self.label

    def __str__(self):
        ans = ["File:" + str(self.fname)]
        for key, val in self.__dict__.items():
            # omit those to avoid lengthy output
            if key == "hdf_info":
                continue
            elif isinstance(val, np.ndarray) and val.size > 1:
                val = str(val.shape)
            else:
                val = str(val)
            ans.append(f"   {key.ljust(12)}: {val.ljust(30)}")
        return "\n".join(ans)

    def __repr__(self):
        ans = str(type(self))
        ans = "\n".join([ans, self.__str__()])
        return ans

    def get_hdf_info(self, fstr=None):
        """
        get a text representation of the xpcs file; the entries are organized
        in a tree structure;
        :param fstr: list of filter strings, ["string_1", "string_2", ...]
        :return: a list strings
        """
        # cache the data because it may take long time to generate the str
        if self.hdf_info is None:
            self.hdf_info = read_metadata_to_dict(self.fname)
        return self.hdf_info

    def load_data(self, extra_fields=None):
        # default common fields for both twotime and multitau analysis;
        fields = ["saxs_1d", "Iqp", "Int_t", "t0", "t1", "start_time"]

        if "Multitau" in self.atype:
            fields = fields + ["tau", "g2", "g2_err",
                               "stride_frame", "avg_frame"]
        if "Twotime" in self.atype:
            fields = fields + ["c2_g2", "c2_g2_segments", "c2_processed_bins",
                               "c2_stride_frame", "c2_avg_frame"]

        # append other extra fields, eg "G2", "IP", "IF"
        if isinstance(extra_fields, list):
            fields += extra_fields

        # avoid duplicated keys
        fields = list(set(fields))

        ret = get(self.fname, fields, "alias", ftype='nexus')

        if "Twotime" in self.atype:
            stride_frame = ret.pop("c2_stride_frame")
            avg_frame = ret.pop("c2_avg_frame")
            ret['c2_t0'] = ret['t0'] * stride_frame * avg_frame
        if "Multitau" in self.atype:
            # correct g2_err to avoid fitting divergence
            ret['g2_err_mod'] = self.correct_g2_err(ret['g2_err'])
            stride_frame = ret.pop("stride_frame")
            avg_frame = ret.pop("avg_frame")
            t0 = ret['t0'] * stride_frame * avg_frame
            ret['g2_t0'] = t0
            ret['t_el'] = ret['tau'] * t0

        ret['saxs_1d'] = self.qmap.reshape_phi_analysis(ret['saxs_1d'],
                                                        self.label,
                                                        mode='saxs_1d')
        ret['Iqp'] = self.qmap.reshape_phi_analysis(ret['Iqp'], 
                                                    self.label,
                                                    mode='stability')

        ret["abs_cross_section_scale"] = 1.0
        return ret

    def __getattr__(self, key):
        # keys from qmap
        if key in ["sqlist", "dqlist", "dqmap", "sqmap", "mask",
                   "bcx", "bcy", "det_dist", "pixel_size", "X_energy", 
                   "sphilist", "dphilist", "static_num_pts", "dynamic_num_pts"]:
            return self.qmap.__dict__[key]
        # delayed loading of saxs_2d due to its large size
        elif key == 'saxs_2d':
            if self.saxs_2d_data is None:
                ret = get(self.fname, ['saxs_2d'], "alias", ftype='nexus')
                self.saxs_2d_data = ret['saxs_2d']
            return self.saxs_2d_data
        elif key in self.__dict__:
            return self.__dict__[key]
        else:
            raise KeyError(f"key [{key}] not found")
        
    def get_detector_extent(self):
        return self.qmap.extent

    def get_twotime_maps(self):
        dqmap, saxs = self.dqmap, self.saxs_2d
        return dqmap, saxs

    def get_twotime_c2(self, max_c2_num=-1, max_size=512):
        dq_selection = tuple(self.c2_processed_bins.tolist())
        kwargs = (dq_selection, max_c2_num, max_size)
        if self.c2_kwargs == kwargs and self.c2_all_data is not None:
            return self.c2_all_data
        else:
            self.c2_kwargs = kwargs
            c2_result = get_c2_from_hdf_fast(self.fname,
                                             dq_selection=dq_selection, 
                                             max_c2_num=max_c2_num,
                                             max_size=max_size)
            self.c2_all_data = c2_result
            return c2_result 
    
    def get_twotime_stream(self, **kwargs):
        return get_c2_stream(self.fname, **kwargs)

    def get_g2_fitting_line(self, q, tor=1E-6):
        """
        get the fitting line for q, within tor
        """
        if self.fit_summary is None:
            return None, None
        idx = np.argmin(np.abs(self.fit_summary["q_val"] - q))
        if abs(self.fit_summary["q_val"][idx] - q) > tor:
            return None, None

        fit_x = self.fit_summary["fit_line"][idx]["fit_x"]
        fit_y = self.fit_summary["fit_line"][idx]["fit_y"]
        return fit_x, fit_y

    def get_fitting_info(self, mode="g2_fitting"):
        if self.fit_summary is None:
            return "fitting is not ready for %s" % self.label

        if mode == "g2_fitting":
            result = self.fit_summary.copy()
            # fit_line is not useful to display
            result.pop("fit_line", None)
            val = result.pop("fit_val", None)
            if result["fit_func"] == "single":
                prefix = ["a", "b", "c", "d"]
            else:
                prefix = ["a", "b", "c", "d", "b2", "c2", "f"]

            msg = []
            for n in range(val.shape[0]):
                temp = []
                for m in range(len(prefix)):
                    temp.append("%s = %f ± %f" % (
                        prefix[m], val[n, 0, m], val[n, 1, m]))
                msg.append(", ".join(temp))
            result["fit_val"] = np.array(msg)

        elif mode == "tauq_fitting":
            if "tauq_fit_val" not in self.fit_summary:
                result = "tauq fitting is not available"
            else:
                v = self.fit_summary["tauq_fit_val"]
                result = "a = %e ± %e; b = %f ± %f" % (v[0, 0], v[1, 0],
                                                       v[0, 1], v[1, 1])
        else:
            raise ValueError("mode not supported.")

        return result

    def fit_g2(self, q_range=None, t_range=None, bounds=None,
               fit_flag=None, fit_func="single"):
        """
        fit the g2 values using single exponential decay function
        :param q_range: a tuple of q lower bound and upper bound
        :param t_range: a tuple of t lower bound and upper bound
        :param bounds: bounds for fitting;
        :param fit_flag: tuple of bools; True to fit and False to float
        :param fit_func: ["single" | "double"]: to fit with single exponential
            or double exponential function
        :return: dictionary with the fitting result;
        """
        assert len(bounds) == 2
        if fit_func == "single":
            assert len(bounds[0]) == 4, \
                "for single exp, the shape of bounds must be (2, 4)"
            if fit_flag is None:
                fit_flag = [True for _ in range(4)]
            func = single_exp_all
        else:
            assert len(bounds[0]) == 7, \
                "for single exp, the shape of bounds must be (2, 4)"
            if fit_flag is None:
                fit_flag = [True for _ in range(7)]
            func = double_exp_all

        if q_range is None:
            q_range = [np.min(self.dqlist) * 0.95, np.max(self.dqlist) * 1.05]

        if t_range is None:
            q_range = [np.min(self.t_el) * 0.95, np.max(self.t_el) * 1.05]

        # create a data slice for the given range;
        t_slice = create_slice(self.t_el, t_range)
        q_slice = create_slice(self.dqlist, q_range)

        t_el = self.t_el[t_slice]
        q = self.dqlist[q_slice]
        g2 = self.g2[t_slice, q_slice]
        sigma = self.g2_err_mod[t_slice, q_slice]

        # set the initial guess
        p0 = np.array(bounds).mean(axis=0)
        # tau"s bounds are in log scale, set as the geometric average
        p0[1] = np.sqrt(bounds[0][1] * bounds[1][1])
        if fit_func == "double":
            p0[4] = np.sqrt(bounds[0][4] * bounds[1][4])

        fit_x = np.logspace(np.log10(np.min(t_el)) - 0.5,
                            np.log10(np.max(t_el)) + 0.5, 128)

        fit_line, fit_val = fit_with_fixed(func, t_el, g2, sigma,
                                           bounds, fit_flag, fit_x, p0=p0)

        self.fit_summary = {
            "fit_func": fit_func,
            "fit_val": fit_val,
            "t_el": t_el,
            "q_val": q,
            "q_range": str(q_range),
            "t_range": str(t_range),
            "bounds": bounds,
            "fit_flag": str(fit_flag),
            "fit_line": fit_line
        }

        return self.fit_summary

    @staticmethod
    def correct_g2_err(g2_err=None, threshold=1E-6):
        # correct the err for some data points with really small error, which
        # may cause the fitting to blowup

        g2_err_mod = np.copy(g2_err)
        for n in range(g2_err.shape[1]):
            data = g2_err[:, n]
            idx = data > threshold
            # avoid averaging of empty slice
            if np.sum(idx) > 0:
                avg = np.mean(data[idx])
            else:
                avg = threshold
            g2_err_mod[np.logical_not(idx), n] = avg

        return g2_err_mod

    def fit_tauq(self, q_range, bounds, fit_flag):
        if self.fit_summary is None:
            return

        x = self.fit_summary["q_val"]
        q_slice = create_slice(x, q_range)
        x = x[q_slice]

        y = self.fit_summary["fit_val"][q_slice, 0, 1]
        sigma = self.fit_summary["fit_val"][q_slice, 1, 1]

        # filter out those invalid fittings; failed g2 fitting has -1 err
        valid_idx = (sigma > 0)

        if np.sum(valid_idx) == 0:
            self.fit_summary["tauq_success"] = False
            return

        x = x[valid_idx]
        y = y[valid_idx]
        sigma = sigma[valid_idx]

        # reshape to two-dimension so the fit_with_fixed function works
        y = y.reshape(-1, 1)
        sigma = sigma.reshape(-1, 1)

        # the initial value for typical gel systems
        p0 = [1.0e-7, -2.0]
        fit_x = np.logspace(np.log10(np.min(x) / 1.1),
                            np.log10(np.max(x) * 1.1), 128)

        fit_line, fit_val = fit_with_fixed(power_law, x, y, sigma, bounds,
                                           fit_flag, fit_x, p0=p0)

        # fit_line and fit_val are lists with just one element;
        self.fit_summary["tauq_success"] = fit_line[0]["success"]
        self.fit_summary["tauq_q"] = x
        self.fit_summary["tauq_tau"] = np.squeeze(y)
        self.fit_summary["tauq_tau_err"] = np.squeeze(sigma)
        self.fit_summary["tauq_fit_line"] = fit_line[0]
        self.fit_summary["tauq_fit_val"] = fit_val[0]

        return self.fit_summary
    
    def get_roi_data(self, roi_parameter, phi_num=180):
        qmap_all = self.compute_qmap()
        qmap = qmap_all["q"]
        pmap = qmap_all["phi"]
        rmap = qmap_all["r_pixel"]

        if roi_parameter["sl_type"] == "Pie":
            pmin, pmax = roi_parameter["angle_range"] 
            if pmax < pmin:
                pmax += 360.0
                pmap[pmap < pmin] += 360.0
            proi = np.logical_and(pmap >= pmin, pmap < pmax)
            proi = np.logical_and(proi, (self.mask > 0))
            qmap_idx = np.zeros_like(qmap, dtype=np.uint32)

            index = 1
            qsize = len(self.sqspan) - 1
            for n in range(qsize):
                q0, q1 = self.sqspan[n: n + 2]
                select = (qmap >= q0) * (qmap < q1)
                qmap_idx[select] = index
                index += 1
            qmap_idx = (qmap_idx * proi).ravel()

            saxs_roi = np.bincount(qmap_idx, self.saxs_2d.ravel(),
                                   minlength=qsize+1)
            saxs_nor = np.bincount(qmap_idx, minlength=qsize+1)
            saxs_nor[saxs_nor == 0] = 1.0
            saxs_roi = saxs_roi * 1.0 / saxs_nor

            # remove the 0th term
            saxs_roi = saxs_roi[1:]

            # set the qmax cutoff
            dist = roi_parameter["dist"]
            # qmax = qmap[int(self.bcy), int(self.bcx + dist)]
            wlength = 12.398 / self.X_energy
            qmax = dist * self.pix_dim_x / self.det_dist * 2 * np.pi / wlength
            saxs_roi[self.sqlist >= qmax] = 0
            saxs_roi[saxs_roi <=0] = np.nan
            return self.sqlist, saxs_roi

        elif roi_parameter["sl_type"] == "Ring":
            rmin, rmax = roi_parameter["radius"]
            if rmin > rmax:
                rmin, rmax = rmax, rmin
            rroi = np.logical_and(rmap >= rmin, rmap < rmax)
            rroi = np.logical_and(rroi, (self.mask > 0))

            phi_min, phi_max = np.min(pmap[rroi]), np.max(pmap[rroi])
            x = np.linspace(phi_min, phi_max, phi_num)
            delta = (phi_max - phi_min) / phi_num
            index = ((pmap - phi_min) / delta).astype(np.int64)
            index[index == phi_num] = phi_num - 1
            index += 1
            # q_avg = qmap[rroi].mean()
            index = (index * rroi).ravel()

            saxs_roi = np.bincount(index, self.saxs_2d.ravel(),
                                   minlength=phi_num+1)
            saxs_nor = np.bincount(index, minlength=phi_num+1)
            saxs_nor[saxs_nor == 0] = 1.0
            saxs_roi = saxs_roi * 1.0 / saxs_nor

            # remove the 0th term
            saxs_roi = saxs_roi[1:]
            return x, saxs_roi
    
    def export_saxs1d(self, roi_list, folder):
        # export ROI
        idx = 0
        for roi in roi_list:
            fname = os.path.join(folder,
                self.label + "_" + roi["sl_type"] + f"_{idx:03d}.txt")
            idx += 1
            x, y = self.get_roi_data(roi)
            if roi["sl_type"] == "Ring":
                header = "phi(degree) Intensity"
            else:
                header = "q(1/Angstron) Intensity"
            np.savetxt(fname, np.vstack([x, y]).T, header=header)

        # export all saxs1d 
        fname = os.path.join(folder, self.label + "_" + "saxs1d.txt")
        Iq, q = self.saxs_1d["Iq"], self.saxs_1d["q"]
        header = "q(1/Angstron) Intensity"
        for n in range(Iq.shape[0] - 1):
            header += f" Intensity_phi{n + 1 :03d}"
        np.savetxt(fname, np.vstack([q, Iq]).T, header=header)
    
    def get_pg_tree(self):
        data = self.load_data()
        for key, val in data.items():
            if isinstance(val, np.ndarray):
                if val.size > 4096:
                    data[key] = 'data size is too large'
                # suqeeze one-element array
                if val.size == 1:
                    data[key] = float(val)
        data['analysis_type'] = self.atype
        data['label'] = self.label
        tree = pg.DataTreeWidget(data=data)
        tree.setWindowTitle(self.fname)
        tree.resize(600, 800)
        return tree
            

def test1():
    cwd = "../../../xpcs_data"
    af = XpcsFile(fname="N077_D100_att02_0128_0001-100000.hdf", cwd=cwd)
    af.plot_saxs2d()


if __name__ == "__main__":
    test1()
