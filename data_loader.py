import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.optimize import curve_fit
import os
import h5py

hdf_dict = {
    'Iq': '/exchange/partition-mean-total',
    'ql_sta': '/xpcs/sqlist',
    'ql_dyn': '/xpcs/dqlist',
    't0': '/measurement/instrument/detector/exposure_period',
    't_el': '/exchange/tau',
    'g2': '/exchange/norm-0-g2',
    'g2_err': '/exchange/norm-0-stderr',
    'Int_2D': '/exchange/pixelSum',
    'Int_t': '/exchange/frameSum'
}


def read_file(fields, fn, prefix='./data'):
    res = []
    with h5py.File(os.path.join(prefix, fn), 'r') as HDF_Result:
        for field in fields:
            val = np.squeeze(HDF_Result.get(hdf_dict[field]))
            res.append(val)

    return res


class DataLoader(object):
    def __init__(self, prefix, file_list):
        self.size = len(file_list)
        self.prefix = prefix
        self.file_list = file_list
        # self.label = ['Iq', 'g2', 'Int_2D', 'ql_sta', 'ql_dyn', 't_el']
        # self.label = ['Iq', 'g2', 'ql_sta', 'ql_dyn', 't_el']
        # self.data = self.load_data(self.label, file_list)

    def read_data(self, labels, file_list=None, mask=None):
        if file_list is None:
            file_list = self.file_list

        if mask is None:
            mask = np.ones(shape=len(file_list), dtype=np.bool)

        data = []
        for n, fn in enumerate(file_list):
            if mask[n]:
                data.append(read_file(labels, fn, self.prefix))

        np_data = {}
        for n, label in enumerate(labels):
            temp = [x[n] for x in data]
            np_data[label] = np.array(temp)

        return np_data

    def average(self, baseline=1.03, chunk_size=256):
        labels = ['Iq', 'g2', 'g2_err', 'Int_2D']
        g2 = self.read_data(['g2'], self.file_list)['g2']
        mask = np.mean(g2[:, -10:, 1], axis=1) < baseline

        steps = (len(mask) + chunk_size - 1) // chunk_size
        result = {}
        for n in range(steps):
            beg = chunk_size * (n + 0)
            end = chunk_size * (n + 1)
            end = min(len(mask), end)
            slice0 = slice(beg, end)
            values = self.read_data(labels, file_list=self.file_list[slice0],
                                    mask=mask[slice0])
            if n == 0:
                for label in labels:
                    result[label] = np.sum(values[label], axis=0)
            else:
                for label in labels:
                    result[label] += np.sum(values[label], axis=0)

        num_points = np.sum(mask)
        for label in labels:
            result[label] = result[label] / num_points

        return result

    def plot_g2(self, ax=None):
        if ax is None:
            fig, ax = plt.subplots(1, 1)

        print(len(self.data))
        print(len(self.data[1]))
        for n in range(self.size):
            ax.plot(self.data[n][1][0, 1])

        plt.show()


if __name__ == "__main__":
    flist = os.listdir('./data')
    dv = DataViewer('./data', flist)
    dv.average()
    # dv.plot_g2()
