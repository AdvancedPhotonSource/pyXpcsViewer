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

# the following functions are copied from:
# https://stackoverflow.com/questions/2892931
def long_substr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0])-i+1):
                if j > len(substr) and is_substr(data[0][i:i+j], data):
                    substr = data[0][i:i+j]
    return substr

def is_substr(find, data):
    if len(data) < 1 and len(find) < 1:
        return False
    for i in range(len(data)):
        if find not in data[i]:
            return False
    return True


def create_id(in_list, repeat=2, keep_slice=None):
    """
    :param in_list: input file name list
    :param repeat: number of repeats to remove common string
    :param keep_slice: the slice in the original string to keep, if not given,
        then use the segment before the first underscore.
    :return: label list with minimal information redundancy
    """
    if len(in_list) < 1:
        return []

    if keep_slice is None:
        idx = in_list[0].find('_')
        keep_slice = slice(0, idx + 1)

    keep_str = in_list[0][keep_slice]
    if keep_str[-1] != '_':
        keep_str = keep_str + '_'

    for n in range(repeat):
        substr = long_substr(in_list)
        in_list = [x.replace(substr, '') for x in in_list]

    in_list = [keep_str + x for x in in_list]
    return in_list


class DataLoader(object):
    def __init__(self, prefix, file_list):
        self.size = len(file_list)
        self.prefix = prefix
        self.file_list = file_list
        self.id_list = create_id(self.file_list)
        self.get_g2_data()

    def plot_saxs(self):


    def get_saxs(self):
        ans = self.read_data(['Int_2D'])['Int_2D']
        return ans

    def get_g2_data(self):
        labels = ['g2', 'g2_err']
        res = self.read_data(labels)
        labels2 = ['t0', 't_el']
        time_res = self.read_data(labels2, [self.file_list[0]])
        t_el = time_res['t0'] * time_res['t_el'][0]
        res['t_el'] = t_el

        return res

    def get_stability_data(self, max_point=128):
        labels = ['Int_t', 'Iq']
        res = self.read_data(labels)
        avg_int_t = []

        int_t = res['Int_t'][:, 1, :]
        int_t = int_t / np.mean(int_t)
        avg_size = (int_t.shape[1] + max_point - 1) // max_point
        for n in range(max_point):
            sl = slice(n * avg_size, (n + 1) * avg_size)
            temp = int_t[:, sl]
            avg, mean = np.mean(temp, axis=1), np.std(temp, axis=1)
            avg_int_t.append(np.vstack([avg, mean]).T)

        res['Int_t_statistics'] = np.array(avg_int_t).swapaxes(0, 1)
        res['Int_t'] = None
        res['avg_size'] = avg_size

        return res

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
