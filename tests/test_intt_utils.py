# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""core.intt_utils: smoothing and the spectrum of an intensity trace."""

import numpy as np

from pyxpcsviewer.core.intt_utils import intensity_spectrum, smooth_intensity


def test_smooth_intensity_is_identity_by_default():
    y = np.arange(10.0)
    x, out = smooth_intensity(y)
    assert np.array_equal(x, np.arange(10))
    assert np.array_equal(out, y)


def test_smooth_intensity_window_and_sampling():
    y = np.arange(10.0)
    x, out = smooth_intensity(y, window=4)
    assert len(out) == 6 and x[0] == 4
    assert out[0] == np.mean(y[1:5])  # the window ends at frame x[0] = 4
    x2, out2 = smooth_intensity(y, window=4, sampling=2)
    assert np.array_equal(out2, out[::2]) and np.array_equal(x2, x[::2])


def test_intensity_spectrum_matches_xpcs_file_convention():
    rng = np.random.default_rng(1)
    y = rng.normal(size=256)
    freq, mag = intensity_spectrum(y, 0.01)
    assert freq.shape == mag.shape == (128,)
    assert mag[0] == 0
    assert freq[1] == 1 / (256 * 0.01)
    assert np.allclose(mag[1:], np.abs(np.fft.fft(y))[1:128])
