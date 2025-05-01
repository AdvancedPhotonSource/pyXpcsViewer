import os
import re
import numpy as np
import pyqtgraph as pg
import warnings

from .fileIO.hdf_reader import get, get_analysis_type, read_metadata_to_dict
from .helper.fitting import fit_with_fixed
from .fileIO.qmap_utils import get_qmap
from .module.twotime_utils import get_c2_stream, get_single_c2_from_hdf
import logging

logger = logging.getLogger(__name__)


def single_exp_all(x, a, b, c, d):
    """
    Single exponential fitting for XPCS-multitau analysis.

    Parameters
    ----------
    x : float or ndarray
        Delay in seconds.
    a : float
        Contrast.
    b : float
        Characteristic time (tau).
    c : float
        Restriction factor.
    d : float
        Baseline offset.

    Returns
    -------
    float or ndarray
        Computed value of the single exponential model.
    """
    return a * np.exp(-2 * (x / b) ** c) + d


def double_exp_all(x, a, b1, c1, d, b2, c2, f):
    """
    Double exponential fitting for XPCS-multitau analysis.

    Parameters
    ----------
    x : float or ndarray
        Delay in seconds.
    a : float
        Contrast.
    b1 : float
        Characteristic time (tau) of the first exponential component.
    c1 : float
        Restriction factor for the first component.
    d : float
        Baseline offset.
    b2 : float
        Characteristic time (tau) of the second exponential component.
    c2 : float
        Restriction factor for the second component.
    f : float
        Fractional contribution of the first exponential component (0 ≤ f ≤ 1).

    Returns
    -------
    float or ndarray
        Computed value of the double exponential model.
    """
    t1 = np.exp(-1 * (x / b1) ** c1) * f
    t2 = np.exp(-1 * (x / b2) ** c2) * (1 - f)
    return a * (t1 + t2) ** 2 + d


def power_law(x, a, b):
    """
    Power-law fitting for diffusion behavior.

    Parameters
    ----------
    x : float or ndarray
        Independent variable, typically time delay (tau).
    a : float
        Scaling factor.
    b : float
        Power exponent.

    Returns
    -------
    float or ndarray
        Computed value based on the power-law model.
    """
    return a * x**b


def create_id(fname, label_style=None, simplify_flag=True):
    """
    Generate a simplified or customized ID string from a filename.

    Parameters
    ----------
    fname : str
        Input file name, possibly with path and extension.
    label_style : str or None, optional
        Comma-separated string of indices to extract specific components from the file name.
    simplify_flag : bool, optional
        Whether to simplify the file name by removing leading zeros and stripping suffixes.

    Returns
    -------
    str
        A simplified or customized ID string derived from the input filename.
    """
    fname = os.path.basename(fname)

    if simplify_flag:
        # Remove leading zeros from structured parts like '_t0600' → '_t600'
        fname = re.sub(r"_(\w)0+(\d+)", r"_\1\2", fname)
        # Remove trailing _results and file extension
        fname = re.sub(r"(_results)?\.hdf$", "", fname, flags=re.IGNORECASE)

    if len(fname) < 10 or not label_style:
        return fname

    try:
        selection = [int(x.strip()) for x in label_style.split(",")]
        if not selection:
            warnings.warn("Empty label_style selection. Returning simplified filename.")
            return fname
    except ValueError:
        warnings.warn("Invalid label_style format. Must be comma-separated integers.")
        return fname

    segments = fname.split("_")
    selected_segments = []

    for i in selection:
        if i < len(segments):
            selected_segments.append(segments[i])
        else:
            warnings.warn(f"Index {i} out of range for segments {segments}")

    if not selected_segments:
        return fname  # fallback if nothing valid was selected

    return "_".join(selected_segments)


class XpcsFile(object):
    """
    XpcsFile is a class that wraps an Xpcs analysis hdf file;
    """

    def __init__(self, fname, fields=None, label_style=None, qmap_manager=None):
        self.fname = fname
        if qmap_manager is None:
            self.qmap = get_qmap(self.fname)
        else:
            self.qmap = qmap_manager.get_qmap(self.fname)
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
        self.saxs_2d_log_data = None

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
            fields = fields + ["tau", "g2", "g2_err", "stride_frame", "avg_frame"]
        if "Twotime" in self.atype:
            fields = fields + [
                "c2_g2",
                "c2_g2_segments",
                "c2_processed_bins",
                "c2_stride_frame",
                "c2_avg_frame",
            ]

        # append other extra fields, eg "G2", "IP", "IF"
        if isinstance(extra_fields, list):
            fields += extra_fields

        # avoid duplicated keys
        fields = list(set(fields))

        ret = get(self.fname, fields, "alias", ftype="nexus")

        if "Twotime" in self.atype:
            stride_frame = ret.pop("c2_stride_frame")
            avg_frame = ret.pop("c2_avg_frame")
            ret["c2_t0"] = ret["t0"] * stride_frame * avg_frame
        if "Multitau" in self.atype:
            # correct g2_err to avoid fitting divergence
            # ret['g2_err_mod'] = self.correct_g2_err(ret['g2_err'])
            ret["g2_err"] = self.correct_g2_err(ret["g2_err"])
            stride_frame = ret.pop("stride_frame")
            avg_frame = ret.pop("avg_frame")
            ret["t0"] = ret["t0"] * stride_frame * avg_frame
            ret["t_el"] = ret["tau"] * ret["t0"]
            ret["g2_t0"] = ret["t0"]

        ret["saxs_1d"] = self.qmap.reshape_phi_analysis(
            ret["saxs_1d"], self.label, mode="saxs_1d"
        )
        ret["Iqp"] = self.qmap.reshape_phi_analysis(
            ret["Iqp"], self.label, mode="stability"
        )

        ret["abs_cross_section_scale"] = 1.0
        return ret

    def __getattr__(self, key):
        # keys from qmap
        if key in [
            "sqlist",
            "dqlist",
            "dqmap",
            "sqmap",
            "mask",
            "bcx",
            "bcy",
            "det_dist",
            "pixel_size",
            "X_energy",
            "splist",
            "dplist",
            "static_num_pts",
            "dynamic_num_pts",
            "map_names",
            "map_units",
            "get_qbin_label",
        ]:
            return self.qmap.__dict__[key]
        # delayed loading of saxs_2d due to its large size
        elif key == "saxs_2d":
            if self.saxs_2d_data is None:
                ret = get(self.fname, ["saxs_2d"], "alias", ftype="nexus")
                self.saxs_2d_data = ret["saxs_2d"]
            return self.saxs_2d_data
        elif key == "saxs_2d_log":
            if self.saxs_2d_log_data is None:
                saxs = np.copy(self.saxs_2d)
                roi = saxs > 0
                if np.sum(roi) == 0:
                    self.saxs_2d_log_data = np.zeros_like(saxs, dtype=np.uint8)
                else:
                    min_val = np.min(saxs[roi])
                    saxs[~roi] = min_val
                    self.saxs_2d_log_data = np.log10(saxs).astype(np.float32)
            return self.saxs_2d_log_data
        elif key == "Int_t_fft":
            y = np.abs(np.fft.fft(self.Int_t[1]))
            x = np.arange(y.size) / (y.size * self.t0)
            x = x[0 : y.size // 2]
            y = y[0 : y.size // 2]
            y[0] = 0
            return np.stack((x, y), axis=1).astype(np.float32).T
        elif key in self.__dict__:
            return self.__dict__[key]
        else:
            raise KeyError(f"key [{key}] not found")

    def get_info_at_position(self, x, y):
        x, y = int(x), int(y)
        shape = self.saxs_2d.shape
        if x < 0 or x >= shape[1] or y < 0 or y >= shape[0]:
            return None
        else:
            scat_intensity = self.saxs_2d[y, x]
            qmap_info = self.qmap.get_qmap_at_pos(x, y)
            return f"I={scat_intensity:.4e} {qmap_info}"

    def get_detector_extent(self):
        return self.qmap.extent

    def get_qbin_label(self, qbin: int, append_qbin: bool = False):
        return self.qmap.get_qbin_label(qbin, append_qbin=append_qbin)

    def get_qbinlist_at_qindex(self, qindex, zero_based=True):
        return self.qmap.get_qbinlist_at_qindex(qindex, zero_based=zero_based)

    def get_g2_data(self, qrange=None, trange=None):
        assert "Multitau" in self.atype, "only multitau is supported"
        # qrange can be None
        qindex_selected, qvalues = self.qmap.get_qbin_in_qrange(qrange, zero_based=True)
        g2 = self.g2[:, qindex_selected]
        g2_err = self.g2_err[:, qindex_selected]
        labels = [self.qmap.get_qbin_label(qbin + 1) for qbin in qindex_selected]

        if trange is not None:
            t_roi = (self.t_el >= trange[0]) * (self.t_el <= trange[1])
            g2 = g2[t_roi]
            g2_err = g2_err[t_roi]
            t_el = self.t_el[t_roi]
        else:
            t_el = self.t_el

        return qvalues, t_el, g2, g2_err, labels

    def get_saxs1d_data(
        self,
        bkg_xf=None,
        bkg_weight=1.0,
        qrange=None,
        sampling=1,
        use_absolute_crosssection=False,
        norm_method=None,
        target="saxs1d",
    ):
        assert target in ["saxs1d", "saxs1d_partial"]
        if target == "saxs1d":
            q, Iq = self.saxs_1d["q"], self.saxs_1d["Iq"]
        else:
            q, Iq = self.saxs_1d["q"], self.Iqp
        if bkg_xf is not None:
            if np.allclose(q, bkg_xf.saxs_1d["q"]):
                Iq = Iq - bkg_weight * bkg_xf.saxs_1d["Iq"]
                Iq[Iq < 0] = np.nan
            else:
                logger.warning(
                    "background subtraction is not applied because q is not matched"
                )
        if qrange is not None:
            q_roi = (q >= qrange[0]) * (q <= qrange[1])
            if q_roi.sum() > 0:
                q = q[q_roi]
                Iq = Iq[:, q_roi]
            else:
                logger.warning("qrange is not applied because it is out of range")
        if use_absolute_crosssection and self.abs_cross_section_scale is not None:
            Iq *= self.abs_cross_section_scale

        # apply sampling
        if sampling > 1:
            q, Iq = q[::sampling], Iq[::sampling]
        # apply normalization
        q, Iq, xlabel, ylabel = self.norm_saxs_data(q, Iq, norm_method=norm_method)
        return q, Iq, xlabel, ylabel

    def norm_saxs_data(self, q, Iq, norm_method=None):
        assert norm_method in (None, "q2", "q4", "I0")
        if norm_method is None:
            return q, Iq, "q (Å⁻¹)", "Intensity"
        ylabel = "Intensity"
        if norm_method == "q2":
            Iq = Iq * np.square(q)
            ylabel = ylabel + " * q^2"
        elif norm_method == "q4":
            Iq = Iq * np.square(np.square(q))
            ylabel = ylabel + " * q^4"
        elif norm_method == "I0":
            baseline = Iq[0]
            Iq = Iq / baseline
            ylabel = ylabel + " / I_0"
        xlabel = "q (Å⁻¹)"
        return q, Iq, xlabel, ylabel

    def get_twotime_qbin_labels(self):
        qbin_labels = []
        for qbin in self.c2_processed_bins.tolist():
            qbin_labels.append(self.get_qbin_label(qbin, append_qbin=True))
        return qbin_labels

    def get_twotime_maps(
        self, scale="log", auto_crop=True, highlight_xy=None, selection=None
    ):
        # emphasize the beamstop region which has qindex = 0;
        dqmap = np.copy(self.dqmap)
        if scale == "log":
            saxs = self.saxs_2d_log
        else:
            saxs = self.saxs_2d

        if auto_crop:
            idx = np.nonzero(dqmap >= 1)
            sl_v = slice(np.min(idx[0]), np.max(idx[0]) + 1)
            sl_h = slice(np.min(idx[1]), np.max(idx[1]) + 1)
            dqmap = dqmap[sl_v, sl_h]
            saxs = saxs[sl_v, sl_h]

        qindex_max = np.max(dqmap)
        dqlist = np.unique(dqmap)[1:]
        dqmap = dqmap.astype(np.float32)
        dqmap[dqmap == 0] = np.nan

        dqmap_disp = np.flipud(np.copy(dqmap))

        dq_bin = None
        if highlight_xy is not None:
            x, y = highlight_xy
            if x >= 0 and y >= 0 and x < dqmap.shape[1] and y < dqmap.shape[0]:
                dq_bin = dqmap_disp[y, x]
        elif selection is not None:
            dq_bin = dqlist[selection]

        if dq_bin is not None and dq_bin != np.nan and dq_bin > 0:
            # highlight the selected qbin if it's valid
            dqmap_disp[dqmap_disp == dq_bin] = qindex_max + 1
            selection = np.where(dqlist == dq_bin)[0][0]
        else:
            selection = None
        return dqmap_disp, saxs, selection

    def get_twotime_c2(self, selection=0, correct_diag=True, max_size=32678):
        dq_processed = tuple(self.c2_processed_bins.tolist())
        assert selection >= 0 and selection < len(
            dq_processed
        ), f"selection {selection} out of range {dq_processed}"  # noqa: E501
        config = (selection, correct_diag, max_size)
        if self.c2_kwargs == config:
            return self.c2_all_data
        else:
            c2_result = get_single_c2_from_hdf(
                self.fname,
                selection=selection,
                max_size=max_size,
                t0=self.t0,
                correct_diag=correct_diag,
            )
            self.c2_all_data = c2_result
            self.c2_kwargs = config
        return c2_result

    def get_twotime_stream(self, **kwargs):
        return get_c2_stream(self.fname, **kwargs)

    # def get_g2_fitting_line(self, q, tor=1e-6):
    #     """
    #     get the fitting line for q, within tor
    #     """
    #     if self.fit_summary is None:
    #         return None, None
    #     idx = np.argmin(np.abs(self.fit_summary["q_val"] - q))
    #     if abs(self.fit_summary["q_val"][idx] - q) > tor:
    #         return None, None

    #     fit_x = self.fit_summary["fit_line"][idx]["fit_x"]
    #     fit_y = self.fit_summary["fit_line"][idx]["fit_y"]
    #     return fit_x, fit_y

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
                    temp.append(
                        "%s = %f ± %f" % (prefix[m], val[n, 0, m], val[n, 1, m])
                    )
                msg.append(", ".join(temp))
            result["fit_val"] = np.array(msg)

        elif mode == "tauq_fitting":
            if "tauq_fit_val" not in self.fit_summary:
                result = "tauq fitting is not available"
            else:
                v = self.fit_summary["tauq_fit_val"]
                result = "a = %e ± %e; b = %f ± %f" % (
                    v[0, 0],
                    v[1, 0],
                    v[0, 1],
                    v[1, 1],
                )
        else:
            raise ValueError("mode not supported.")

        return result

    def fit_g2(
        self, q_range=None, t_range=None, bounds=None, fit_flag=None, fit_func="single"
    ):
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
            assert (
                len(bounds[0]) == 4
            ), "for single exp, the shape of bounds must be (2, 4)"
            if fit_flag is None:
                fit_flag = [True for _ in range(4)]
            func = single_exp_all
        else:
            assert (
                len(bounds[0]) == 7
            ), "for single exp, the shape of bounds must be (2, 4)"
            if fit_flag is None:
                fit_flag = [True for _ in range(7)]
            func = double_exp_all

        q_val, t_el, g2, sigma, label = self.get_g2_data(qrange=q_range, trange=t_range)

        # set the initial guess
        p0 = np.array(bounds).mean(axis=0)
        # tau"s bounds are in log scale, set as the geometric average
        p0[1] = np.sqrt(bounds[0][1] * bounds[1][1])
        if fit_func == "double":
            p0[4] = np.sqrt(bounds[0][4] * bounds[1][4])

        fit_x = np.logspace(
            np.log10(np.min(t_el)) - 0.5, np.log10(np.max(t_el)) + 0.5, 128
        )

        fit_line, fit_val = fit_with_fixed(
            func, t_el, g2, sigma, bounds, fit_flag, fit_x, p0=p0
        )

        self.fit_summary = {
            "fit_func": fit_func,
            "fit_val": fit_val,
            "t_el": t_el,
            "q_val": q_val,
            "q_range": str(q_range),
            "t_range": str(t_range),
            "bounds": bounds,
            "fit_flag": str(fit_flag),
            "fit_line": fit_line,
            "label": label,
        }

        return self.fit_summary

    @staticmethod
    def correct_g2_err(g2_err=None, threshold=1e-6):
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
        q_slice = (x >= q_range[0]) * (x <= q_range[1])
        x = x[q_slice]

        y = self.fit_summary["fit_val"][q_slice, 0, 1]
        sigma = self.fit_summary["fit_val"][q_slice, 1, 1]

        # filter out those invalid fittings; failed g2 fitting has -1 err
        valid_idx = sigma > 0

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
        fit_x = np.logspace(np.log10(np.min(x) / 1.1), np.log10(np.max(x) * 1.1), 128)

        fit_line, fit_val = fit_with_fixed(
            power_law, x, y, sigma, bounds, fit_flag, fit_x, p0=p0
        )

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
                q0, q1 = self.sqspan[n : n + 2]
                select = (qmap >= q0) * (qmap < q1)
                qmap_idx[select] = index
                index += 1
            qmap_idx = (qmap_idx * proi).ravel()

            saxs_roi = np.bincount(qmap_idx, self.saxs_2d.ravel(), minlength=qsize + 1)
            saxs_nor = np.bincount(qmap_idx, minlength=qsize + 1)
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
            saxs_roi[saxs_roi <= 0] = np.nan
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

            saxs_roi = np.bincount(index, self.saxs_2d.ravel(), minlength=phi_num + 1)
            saxs_nor = np.bincount(index, minlength=phi_num + 1)
            saxs_nor[saxs_nor == 0] = 1.0
            saxs_roi = saxs_roi * 1.0 / saxs_nor

            # remove the 0th term
            saxs_roi = saxs_roi[1:]
            return x, saxs_roi

    def export_saxs1d(self, roi_list, folder):
        # export ROI
        idx = 0
        for roi in roi_list:
            fname = os.path.join(
                folder, self.label + "_" + roi["sl_type"] + f"_{idx:03d}.txt"
            )
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
                    data[key] = "data size is too large"
                # suqeeze one-element array
                if val.size == 1:
                    data[key] = float(val)
        data["analysis_type"] = self.atype
        data["label"] = self.label
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
