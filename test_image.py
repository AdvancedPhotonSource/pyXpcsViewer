import numpy as np

a = np.random.uniform(size=(10, 1024, 512))


def quickMinMax(data):
    """
    Estimate the min/max values of *data* by subsampling.
    """
    while data.size > 1e6:
        print('from imageview', data.shape)
        print(type(data))
        ax = np.argmax(data.shape)
        sl = [slice(None, None)] * data.ndim
        sl[ax] = slice(None, None, 2)
        sl = tuple(sl)
        data = data[sl]
    return np.nanmin(data), np.nanmax(data)


print(quickMinMax(a))
